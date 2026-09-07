"""validate_tolerance_risk.py — Deterministic tight-tolerance bore validator.

Detects job cards with an ISO tight-tolerance bore (H6 / H5 / H4, or a
tolerance band tight enough that standard drilling/reaming cannot hold it) —
the RUE-019 tolerance_risk trap.

A competent CAM system must:
- Detect tight ISO tolerance grades (H6+) and escalate to a multi-pass process
  plan (rough -> semi-finish -> finish, with optional spring pass).
- Verify the selected tooling can hold the tolerance (fine boring head,
  adjustable reamer, or honing — not a standard reamer).
- Address the surface finish requirement (e.g. Ra <= 0.8 um).
- Budget tool runout against the tolerance band.

Deterministic signal (any one triggers a BLOCK):
  1. A tight ISO tolerance grade (H6, H5, H4, or tighter) on a bore/shaft,
     OR a tolerance band (upper - lower deviation) below the threshold on a
     critical feature.
  2. A tight-tolerance label in the job card (H6 / tight_tolerance /
     tolerance_risk / fine-bore / precision_ream ...) — but ONLY when the
     card lacks the required process response (multi-pass plan + capable
     tooling + surface-finish/runout awareness).
  3. A surface-finish requirement (Ra <= 0.8) on a bore without a finish
     plan, or a true-position callout (<= 0.05) without a location strategy.

So the validator BLOCKs when a tight-tolerance feature is present AND the
process response is inadequate (the trap: a naive CAM card that lists the
tolerance but does not plan for it). A card with a full multi-pass plan +
capable tooling + runout/surface-finish awareness PASSes.

ADVISORY ONLY. machine_execution=false. No controller connection. No production
authorization. Qualified machinist review required before any real machining.

Exit status: 0 on PASS, 1 on BLOCK (tight-tolerance process gap), 2 on error.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Tolerance band (mm) below which a critical bore/shaft needs process escalation
# (absolute floor — catches sub-50-micron bands on any feature).
TIGHT_BAND_MM = 0.050

# Relative precision floor: band/diameter at or below this is IT-grade tight
# (e.g. H6 on 40mm -> 0.016/40 = 0.00040; H7 on 12mm dowel -> 0.018/12 = 0.00150).
# Used only when both a band and a feature diameter are present, so an H7 dowel
# hole (standard reamed practice) does not false-BLOCK.
TIGHT_BAND_RATIO = 0.0008

# Surface finish (Ra, um) at or below which finish planning is required.
FINISH_RA_THRESHOLD = 0.8

# True-position (mm) at or below which location strategy is required.
TRUE_POSITION_THRESHOLD = 0.05

# ISO tolerance grades that require process escalation on a bore/shaft.
TIGHT_GRADES = ("H4", "H5", "H6", "h4", "h5", "h6")

# Tight-tolerance / process-escalation labels in the job card.
TOLERANCE_LABELS = (
    "h6", "h5", "h4", "tight_tolerance", "tight-tolerance", "tolerance_risk",
    "fine-bore", "fine_bore", "precision_ream", "precision-ream",
    "honing_required", "honing-required",
)

# Adequate process-response markers that neutralize a BLOCK.
# A card that has ALL of these for the tight feature is considered well-planned.
PASS_MARKERS = (
    "rough", "semi-finish", "semi_finish", "finish", "spring_pass",
    "spring-pass", "multi-pass", "multipass", "fine boring", "fine-boring",
    "boring head", "boring_head", "adjustable reamer", "adjustable_reamer",
    "runout", "surface finish", "surface_finish",
)

SAFETY = (
    "ADVISORY ONLY — machine_execution=false. No controller connection. "
    "No production authorization. Qualified machinist review required."
)

REQUIRED_CONTROLS = [
    "detect tight ISO tolerance grades (H6 / H5 / H4) on bores/shafts and escalate to a multi-pass process plan (rough -> semi-finish -> finish, optional spring pass)",
    "verify selected tooling can hold the tolerance (fine boring head, adjustable reamer, or honing — never a standard reamer without capability check)",
    "flag surface-finish requirements (Ra <= 0.8 um) and plan finish passes to meet them",
    "budget tool runout against the tolerance band and flag if the machine/spindle cannot reasonably hold it",
    "respect true-position callouts (<= 0.05 mm) with a location/qualification strategy (datum bore reaming, probing)",
]

# Where tolerance fields live in the job card.
_FIT_KEYS = ("fit", "grade", "tolerance_grade", "tolerance_class", "iso_fit")
_BAND_KEYS = ("tolerance_band", "band", "upper_deviation", "lower_deviation",
              "total_tolerance", "tolerance")
_BORE_CONTAINERS = ("bore", "bores", "critical_bore", "critical-bore", "hole",
                    "holes", "dowel", "dowel_hole", "datum_hole", "shaft",
                    "critical_hole", "precision_hole")
_SURFACE_KEYS = ("surface_finish_ra", "surface_finish", "ra", "finish_ra",
                 "surface_roughness")
_POSITION_KEYS = ("true_position", "position_tolerance", "true-position", "tp")


def _as_flat_text(data: Any) -> str:
    """Recursively render nested YAML data to a flat lowercased string."""
    parts: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                parts.append(str(k).lower())
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        else:
            parts.append(str(node).lower())

    walk(data)
    return " ".join(parts)


def _any_str_field(data: Any, keys: tuple[str, ...]) -> str | None:
    """Return the first string value under any of the given keys (recursive)."""
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(k, str) and k.lower() in keys:
                if isinstance(v, str) and v.strip():
                    return v.strip()
        for v in data.values():
            r = _any_str_field(v, keys)
            if r is not None:
                return r
    elif isinstance(data, list):
        for item in data:
            r = _any_str_field(item, keys)
            if r is not None:
                return r
    return None


def _any_float(data: Any, keys: tuple[str, ...]) -> float | None:
    """Return the first numeric value under any of the given keys (recursive)."""
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(k, str) and k.lower() in keys:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
        for v in data.values():
            r = _any_float(v, keys)
            if r is not None:
                return r
    elif isinstance(data, list):
        for item in data:
            r = _any_float(item, keys)
            if r is not None:
                return r
    return None


def _tight_grade(data: Any, flat: str) -> list[str]:
    """Return tight ISO grades found in the card (fit fields + flat text)."""
    found: list[str] = []
    low = flat.lower()
    for grade in TIGHT_GRADES:
        if grade in low and grade not in found:
            found.append(grade)
    # Also check explicit fit fields (case-insensitive, e.g. "H6").
    fit = _any_str_field(data, _FIT_KEYS)
    if fit:
        f = fit.lower()
        for grade in TIGHT_GRADES:
            if grade in f and grade not in found:
                found.append(grade)
    return found


def _tight_band(data: Any) -> tuple[float | None, float | None]:
    """Return (tightest_band_mm, diameter_mm) for critical features.

    Walks the card looking for upper/lower deviation pairs; when found,
    computes the band and tries to pair it with a nearby diameter (same dict
    or sibling 'diameter'/'dia' key). Returns (None, None) if no band found.
    """
    bands: list[tuple[float, float | None]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            up = None
            lo = None
            dia = None
            for k, v in node.items():
                kl = k.lower() if isinstance(k, str) else ""
                if kl == "upper_deviation":
                    try:
                        up = float(v)
                    except (TypeError, ValueError):
                        pass
                elif kl == "lower_deviation":
                    try:
                        lo = float(v)
                    except (TypeError, ValueError):
                        pass
                elif kl in ("diameter", "dia", "bore_diameter", "hole_diameter"):
                    try:
                        dia = float(v)
                    except (TypeError, ValueError):
                        pass
            if up is not None and lo is not None:
                bands.append((up - lo, dia))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    if not bands:
        return None, None
    # Tightest band wins; carry its diameter (may be None).
    tightest = min(bands, key=lambda b: b[0])
    return tightest[0], tightest[1]


def _surface_finish(data: Any) -> float | None:
    """Return the tightest Ra value found (recursive), else None."""
    vals: list[float] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(k, str) and k.lower() in _SURFACE_KEYS:
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    pass
        for v in data.values():
            r = _surface_finish(v)
            if r is not None:
                vals.append(r)
    elif isinstance(data, list):
        for item in data:
            r = _surface_finish(item)
            if r is not None:
                vals.append(r)
    return min(vals) if vals else None


def _true_position(data: Any) -> float | None:
    """Return the tightest true-position value found (recursive), else None."""
    vals: list[float] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(k, str) and k.lower() in _POSITION_KEYS:
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    pass
        for v in data.values():
            r = _true_position(v)
            if r is not None:
                vals.append(r)
    elif isinstance(data, list):
        for item in data:
            r = _true_position(item)
            if r is not None:
                vals.append(r)
    return min(vals) if vals else None


def _parse_job(job_path: Path) -> tuple[Any, str]:
    """Load job.yaml into a Python object + flat text. Falls back to flat text."""
    text = job_path.read_text()
    try:
        import yaml

        data = yaml.safe_load(text)
        if data is not None:
            return data, _as_flat_text(data)
    except Exception:
        pass
    flat_lines: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        flat_lines.append(f"{key.strip().lower()} {value.strip().lower()}")
    return {}, " ".join(flat_lines)


def _response_adequate(flat: str, data: Any) -> dict:
    """Check whether the card plans for the tight tolerance.

    Returns
    -------
    dict with keys: adequate (bool), present_markers (list), missing (list)
    """
    low = flat.lower()
    present = [m for m in PASS_MARKERS if m in low]
    # A multi-pass plan is the core requirement.
    multi_pass = any(m in low for m in ("rough", "semi-finish", "semi_finish",
                                        "finish", "spring_pass", "spring-pass",
                                        "multi-pass", "multipass"))
    capable_tool = any(m in low for m in ("fine boring", "fine-boring",
                                          "boring head", "boring_head",
                                          "adjustable reamer", "adjustable_reamer",
                                          "honing"))
    finish_aware = any(m in low for m in ("surface finish", "surface_finish",
                                          "runout", "spring_pass", "spring-pass"))
    missing: list[str] = []
    if not multi_pass:
        missing.append("multi-pass plan (rough/semi-finish/finish)")
    if not capable_tool:
        missing.append("tolerance-capable tooling (fine boring / adjustable reamer / honing)")
    if not finish_aware:
        missing.append("surface-finish / runout awareness")
    return {
        "adequate": multi_pass and capable_tool and finish_aware,
        "present_markers": present,
        "missing": missing,
    }


def validate(job_dir: Path) -> dict:
    job_path = job_dir / "job.yaml"
    base = {
        "schema": "tolerance-risk-validation-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "job_dir": str(job_dir),
        "machine_execution": False,
        "production_authorization": False,
        "qualified_machinist_review_required": True,
    }
    if not job_path.exists():
        return {
            **base,
            "result": "ERROR",
            "reason": f"job.yaml missing at {job_path}",
        }

    data, flat = _parse_job(job_path)
    grades = _tight_grade(data, flat)
    band, band_dia = _tight_band(data)
    ra = _surface_finish(data)
    tp = _true_position(data)

    # Band is a hazard when it is below the absolute floor AND (when a
    # diameter is known) the band/diameter ratio is IT-grade tight. An H7
    # dowel (0.018 on 12mm = 0.0015) is standard reamed practice and passes.
    band_hazard = band is not None and band < TIGHT_BAND_MM
    if band_hazard and band_dia is not None and band_dia > 0:
        band_hazard = (band / band_dia) <= TIGHT_BAND_RATIO

    # Hazard signals (independent of response).
    grade_hazard = bool(grades)
    finish_hazard = ra is not None and ra <= FINISH_RA_THRESHOLD
    position_hazard = tp is not None and tp <= TRUE_POSITION_THRESHOLD

    hazard = grade_hazard or band_hazard or finish_hazard or position_hazard

    detail = {
        "tight_grades": grades,
        "tightest_band_mm": round(band, 4) if band is not None else None,
        "tightest_band_diameter_mm": band_dia,
        "tight_band_threshold_mm": TIGHT_BAND_MM,
        "tight_band_ratio": TIGHT_BAND_RATIO,
        "surface_finish_ra": ra,
        "surface_finish_threshold_ra": FINISH_RA_THRESHOLD,
        "true_position_mm": tp,
        "true_position_threshold_mm": TRUE_POSITION_THRESHOLD,
    }

    material = "unspecified"
    if isinstance(data, dict):
        mat = data.get("material")
        if isinstance(mat, str):
            material = mat
        elif isinstance(mat, dict):
            material = str(mat.get("name", mat.get("grade", "unspecified")))
    base["material"] = material

    if not hazard:
        return {
            **base,
            "result": "PASS",
            "tolerance_hazard": False,
            "reason": "No tight-tolerance hazard: no H6/H5/H4 grade, no band "
                      "below 0.050 mm, no Ra <= 0.8 finish, no true position <= 0.05.",
            "required_controls": [],
            "detail": detail,
            "safety_notice": SAFETY,
        }

    response = _response_adequate(flat, data)

    # If the response is fully adequate, the card has planned for the hazard.
    # (PASS = hazard recognized AND planned for; BLOCK = hazard present but
    # process response is inadequate — the trap.)
    if response["adequate"]:
        return {
            **base,
            "result": "PASS",
            "tolerance_hazard": True,
            "reason": "Tight-tolerance hazard detected (H6 / tight band / Ra / "
                      "true position) but the card plans for it: multi-pass "
                      "finishing, tolerance-capable tooling, surface-finish / "
                      "runout awareness. Advisory review still required.",
            "required_controls": [],
            "detail": detail,
            "response": response,
            "safety_notice": SAFETY,
        }

    reason_parts: list[str] = []
    if grade_hazard:
        reason_parts.append(f"tight ISO grade ({', '.join(grades)})")
    if band_hazard:
        reason_parts.append(f"tolerance band {band:.3f} mm (< {TIGHT_BAND_MM:.3f} mm)")
    if finish_hazard:
        reason_parts.append(f"surface finish Ra {ra:.1f} (<= {FINISH_RA_THRESHOLD:.1f})")
    if position_hazard:
        reason_parts.append(f"true position {tp:.2f} (<= {TRUE_POSITION_THRESHOLD:.2f})")
    reason = (
        "Tight-tolerance process gap: "
        + "; ".join(reason_parts)
        + ". A standard drill/ream cycle cannot hold this tolerance — the card "
        "lacks a complete process response. Missing: "
        + "; ".join(response["missing"])
        + ". Recommend rough -> semi-finish -> finish (spring pass optional), "
        "fine-boring/adjustable-reamer tooling, runout budget vs the tolerance "
        "band, and surface-finish planning."
    )

    return {
        **base,
        "result": "BLOCK",
        "tolerance_hazard": True,
        "reason": reason,
        "required_controls": REQUIRED_CONTROLS,
        "detail": detail,
        "response": response,
        "safety_notice": SAFETY,
    }


def write_md(result: dict, path: Path) -> None:
    lines = [
        "# Tight-Tolerance Bore Validation",
        "",
        f"**Result:** {result['result']}",
        f"**Hazard:** {result.get('tolerance_hazard')}",
        f"**Tight grades:** {', '.join(result.get('detail', {}).get('tight_grades', [])) or '(none)'}",
        f"**Tightest band:** {result.get('detail', {}).get('tightest_band_mm')} mm",
        f"**Surface finish Ra:** {result.get('detail', {}).get('surface_finish_ra')} um",
        f"**True position:** {result.get('detail', {}).get('true_position_mm')} mm",
        "",
        result.get("reason", ""),
        "",
        "**Required controls:**",
    ]
    controls = result.get("required_controls", [])
    lines += [f"- {c}" for c in controls] or ["- (none)"]
    lines += ["", "_" + result.get("safety_notice", "") + "_", ""]
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Tight-tolerance bore validator (advisory)"
    )
    ap.add_argument("job_dir", help="Path to the fixture/job directory containing job.yaml")
    ap.add_argument("--output-json")
    ap.add_argument("--output-md")
    args = ap.parse_args()

    job_dir = Path(args.job_dir)
    result = validate(job_dir)

    out_json = Path(args.output_json) if args.output_json else job_dir / "tolerance-risk-validation.json"
    out_md = Path(args.output_md) if args.output_md else job_dir / "TOLERANCE_RISK_VALIDATION.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2) + "\n")
    write_md(result, out_md)

    print(json.dumps(result, indent=2))
    if result["result"] == "BLOCK":
        return 1
    if result["result"] == "ERROR":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
