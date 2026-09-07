# Part Packet — Base Plate (pillow-block mounting plate)

_ADVISORY ONLY — machine_execution=false. No controller connection. No production authorization. Qualified machinist review required. No costs are stated in this packet (none computed). No cycle times are stated (none computed)._

## What this part is

Flat mounting plate the housed bearing bolts to: 120 × 100 × 12 slab
with four Dia 9 corner mounting holes and two M8×1.25 tapped holes.
No tight-tolerance bore on this part — general tolerance ±0.1 governs.

## Measured geometry (programmatic, not eyeballed)

Source: `verify_pillow_block.py` run 2026-09-07 — ALL PASS.

| Attribute | Measured |
|---|---|
| Envelope (bbox) | 120.00 × 100.00 × 12.00 mm |
| Mesh | watertight=True, 876 facets |
| Mesh volume | 138,586.7 mm³ (mesh volume, not weighed) |

Files: `base_plate.step` (44,473 B), `base_plate.stl` (43,884 B).

Note: the verifier checks envelope/watertight only for this part (no
bore feature). Hole diameters and positions below are program-stated,
not mesh-measured.

## DFM notes

- Straightforward 2.5D plate work: face, drill, tap. No validator
  hazard on this part (the H6/Ra-0.8 hazard lives on the housing/cap
  bore, not here).
- 12 mm plate in pre-hardened 4140 (job-spec material context): clamp
  flat, watch for movement after breaking the skin — shop practice,
  machinist to confirm.
- Tapped M8×1.25 in 12 mm plate gives ~9–10 mm thread engagement:
  adequate for a mounting plate, verify against the actual bolt loads
  (engineering check, not computed here).

## Process routing (plain English)

- `programs/drill_9mm.nc`: four Dia 9 corner holes at 15 mm insets
  (15,15 / 105,15 / 15,85 / 105,85), canned G81 cycle, Z−2 through,
  R14 retract. Positions are stated in the program header as an
  engineering assumption — confirm against the mating footprint.
- `programs/tap_m8.nc`: two M8×1.25 holes at (30,50) and (90,50) —
  Dia 6.8 drill (G81) then G84 tap at S800. Positions likewise assumed;
  confirm before cutting.

## Assumptions (estimates, not verified facts)

- All six hole positions are program-header assumptions, explicitly
  marked "(positions assumed - engineering assumption)" in the .nc
  files. They are not measured from the mesh and not approved.
- What the drill/tap programs IS: strategy/sequence proofs (hole order,
  canned cycles, tap pitch consistency), verified in sim (holes clear,
  lands kept, in-envelope SHIP). What they are NOT: posted, proven CAM
  — no post-processor ran and no machine kinematics were checked.
- Feeds/speeds (F180/F150/F1000, S800/S1200/S1500) are reference values;
  prove on the machine.

## Verification

- Geometry: `verify_pillow_block.py` PASS (watertight, bbox exact).
- Holes: program text reviewed only; hole callouts are NOT mesh-verified.
