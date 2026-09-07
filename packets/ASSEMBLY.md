# Pillow-Block Assembly Manifest (STAGE 3)

_ADVISORY ONLY — machine_execution=false. No controller connection. No production authorization. Qualified machinist review required. This manifest describes files; it authorizes nothing._

Assembly: two-piece pillow-block bearing housing (housing + cap,
Dia 40 H6 saddle bore) on a 120×100×12 mounting plate. Material context
per job spec: 4140 alloy steel, pre-hardened. No costs, no cycle times
anywhere in this stage (none computed).

## File manifest — what each file is + how it was verified

| File | What it is | How verified |
|---|---|---|
| `housing.step` / `housing.stl` | Housing solid + mesh (100×80×30, saddle Ø40) | `verify_pillow_block.py` PASS: watertight, 500 facets, bbox exact, bore 40.000 |
| `cap.step` / `cap.stl` | Cap solid + mesh (100×80×20, groove Ø40) | Verifier PASS: watertight, 500 facets, groove 40.000 (span 39.988 ≤ 0.6 tol); 0.5 blind-cover mesh note |
| `base_plate.step` / `base_plate.stl` | Mounting plate solid + mesh (120×100×12) | Verifier PASS: watertight, 876 facets, bbox exact (holes program-stated, not mesh-measured) |
| `verify_pillow_block.py` | Geometry checker (watertight/facets/volume/bbox/bore Ø40±0.6) | Ran 2026-09-07 via `.venv/bin/python`: ALL PASS (output quoted in packets) |
| `programs/bore_h6_advisory.nc` | 3-radius saddle program (rough 19.0 / semi 19.7 / finish 20.0 + spring) + hone/CMM notes | Header-stamped advisory-only; text-reviewed against corrected plan (multi-pass + hone + CMM present) |
| `programs/drill_9mm.nc` | 4× Dia 9 corner holes, G81 | Header-stamped advisory-only; positions explicitly assumed — confirm before cutting |
| `programs/tap_m8.nc` | 2× M8×1.25 (6.8 drill + G84 tap) | Header-stamped advisory-only; positions explicitly assumed — confirm before cutting |
| `rue019-block/job.yaml` | Naive plan input (Ø40 H6, Ra 0.8, "20mm end mill only") | Spec input to validator; drives the honest BLOCK |
| `rue019-block/tolerance-risk-validation.json` + `.md` | BLOCK receipt (`result: BLOCK`, `adequate: false`, missing tooling) | Validator-generated 2026-09-07; reason + 5 required controls quoted in housing packet |
| `rue019-corrected/job.yaml` | Corrected plan input (multi-pass, boring head/runout 0.005, reamer, hone, CMM) | Spec input to validator; drives the PASS |
| `rue019-corrected/tolerance-risk-validation.json` + `.md` | PASS receipt (`result: PASS`, `adequate: true`, `missing: []`) | Validator-generated 2026-09-07; hazard still True (correct — hazard persists, response adequate) |
| `housing_PACKET.md` / `cap_PACKET.md` / `base_plate_PACKET.md` | Per-part packets (this stage) | Numbers transcribed from verifier/validator outputs above — no invented values |
| `ASSEMBLY.md` | This manifest | Transcription of the same outputs |

All validator JSONs carry `machine_execution: false`,
`production_authorization: false`, `qualified_machinist_review_required: true`.

## Bore story: BLOCK → PASS (reads as a story)

1. **Naive plan fails honestly.** `rue019-block/job.yaml` answers a
   Ø40 H6 / 0.016-band / Ra-0.8 bore with "rough + finish with 20 mm
   end mill only." The validator finds the markers rough/finish/
   surface_finish present but the one thing that matters missing —
   tolerance-capable tooling — and BLOCKs with five required controls
   instead of waving it through.
2. **Corrected plan passes with proof.** `rue019-corrected/job.yaml`
   answers every control: rough/semi-finish/finish + spring pass, fine
   boring head with 0.005 runout budget, adjustable reamer, hone to
   size, CMM qualification with true-position check. The validator
   returns PASS with `missing: []` — while keeping `hazard: True`,
   which is the honest shape: the tolerance risk is real, and this
   plan covers it. Advisory review still required either way.

## Open work (not claimed)

- No cap-specific validator run; no cap-specific .nc program.
- Base-plate hole positions/threads are program assumptions, unapproved.
- No costs, no cycle times, no feeds/speeds proven — all open.
