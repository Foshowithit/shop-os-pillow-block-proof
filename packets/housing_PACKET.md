# Part Packet — Housing (pillow-block saddle)

_ADVISORY ONLY — machine_execution=false. No controller connection. No production authorization. Qualified machinist review required. No costs are stated in this packet (none computed). No cycle times are stated (none computed)._

## What this part is

Lower half of a two-piece pillow-block bearing housing. A semicircular
saddle groove (nominal Dia 40 along the Y axis) cradles the bearing outer
race; the cap closes it from above. Material per job spec: 4140 alloy
steel, pre-hardened. General tolerance ±0.1 unless noted.

## Measured geometry (programmatic, not eyeballed)

Source: `verify_pillow_block.py` run 2026-09-07 — ALL PASS.

| Attribute | Measured |
|---|---|
| Envelope (bbox) | 100.00 × 80.00 × 30.00 mm |
| Saddle groove diameter | 40.000 mm (span X 40.000, 28 bore-surface verts) |
| Groove axis | X=50, Z=30, along Y, length 0–80 |
| Mesh | watertight=True, 500 facets |
| Mesh volume | 182,662.4 mm³ (mesh volume, not weighed) |

Files: `housing.step` (37,242 B), `housing.stl` (25,084 B).

## Critical feature — Dia 40 H6 bore

Spec (both rue019 job.yamls): diameter 40.0, +0.016/−0.000 (H6),
surface finish Ra 0.8. Tolerance band 0.016 mm — under the validator's
0.050 mm tight-band threshold — so this bore is the assembly's
tolerance hazard. See `rue019-block/` vs `rue019-corrected/` receipts
and the bore story in `ASSEMBLY.md`.

## DFM notes (grounded in validator receipts)

- A standard drill/ream cycle cannot hold H6 at 0.016 mm band + Ra 0.8
  (rue019-block BLOCK: "the card lacks a complete process response").
- Required, per receipt: multi-pass plan (rough → semi-finish → finish,
  spring pass optional), tolerance-capable tooling (fine boring head /
  adjustable reamer / honing — never a standard reamer without a
  capability check), runout budgeted against the 0.016 band, finish
  passes planned to Ra 0.8, CMM qualification.
- Saddle is an open half-round milled from above (not a closed bore):
  the corrected plan answers with profile passes + hone to size.

## Process routing (plain English)

Program `programs/bore_h6_advisory.nc` (advisory reference only):
 datum is the housing base (Z0) with the X0Y0 corner; tools T1 D12 flat
 rougher and T2 D6 ball finisher. Four lanes across Y (10/30/50/70) cut
 the groove in three radii — rough r=19.0, semi r=19.7, finish r=20.0 —
 then a slow spring pass repeats the finish lane at Y40. To size means
 hone Dia 40 holding the 0.016 band, then CMM-qualify bore diameter
 (true position: none on this job).

## Assumptions (estimates, not verified facts)

- Stock 100×80×30 and 4140 pre-hardened come from the job spec, not from
  measurement of bar stock.
- Feeds/speeds in the .nc (F240/F120, S3000) are reference values from
  the advisory program; prove them on the machine, do not trust them.

## Verification

- Geometry: `verify_pillow_block.py` PASS line quoted above.
- Tolerance planning: rue019-corrected PASS (`response.adequate: true`,
  `missing: []`); the naive variant honestly BLOCKs (see ASSEMBLY.md).
