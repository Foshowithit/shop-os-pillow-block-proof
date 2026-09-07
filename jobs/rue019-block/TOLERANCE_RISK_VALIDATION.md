# Tight-Tolerance Bore Validation

**Result:** BLOCK
**Hazard:** True
**Tight grades:** h6
**Tightest band:** 0.016 mm
**Surface finish Ra:** 0.8 um
**True position:** None mm

Tight-tolerance process gap: tight ISO grade (h6); tolerance band 0.016 mm (< 0.050 mm); surface finish Ra 0.8 (<= 0.8). A standard drill/ream cycle cannot hold this tolerance — the card lacks a complete process response. Missing: tolerance-capable tooling (fine boring / adjustable reamer / honing). Recommend rough -> semi-finish -> finish (spring pass optional), fine-boring/adjustable-reamer tooling, runout budget vs the tolerance band, and surface-finish planning.

**Required controls:**
- detect tight ISO tolerance grades (H6 / H5 / H4) on bores/shafts and escalate to a multi-pass process plan (rough -> semi-finish -> finish, optional spring pass)
- verify selected tooling can hold the tolerance (fine boring head, adjustable reamer, or honing — never a standard reamer without capability check)
- flag surface-finish requirements (Ra <= 0.8 um) and plan finish passes to meet them
- budget tool runout against the tolerance band and flag if the machine/spindle cannot reasonably hold it
- respect true-position callouts (<= 0.05 mm) with a location/qualification strategy (datum bore reaming, probing)

_ADVISORY ONLY — machine_execution=false. No controller connection. No production authorization. Qualified machinist review required._

