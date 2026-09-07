# Part Packet — Cap (pillow-block top half)

_ADVISORY ONLY — machine_execution=false. No controller connection. No production authorization. Qualified machinist review required. No costs are stated in this packet (none computed). No cycle times are stated (none computed)._

## What this part is

Upper half of the pillow-block housing. Mirrors the housing saddle with
a matching Dia 40 groove so the closed assembly traps the bearing race.
Same job spec family as the housing (4140 pre-hardened context,
general tolerance ±0.1 unless noted).

## Measured geometry (programmatic, not eyeballed)

Source: `verify_pillow_block.py` run 2026-09-07 — ALL PASS.

| Attribute | Measured |
|---|---|
| Envelope (bbox) | 100.00 × 80.00 × 20.00 mm |
| Groove diameter | 40.000 mm (span X 39.988, 28 bore-surface verts) |
| Mesh | watertight=True, 500 facets |
| Mesh volume | 106,759.3 mm³ (mesh volume, not weighed) |

Files: `cap.step` (37,360 B), `cap.stl` (25,084 B).

## Meshing note (from the verifier, factual)

The groove tool center sits 0.5 below the mating face (0.5 blind cover):
a nominal R20-on-20-thick tangency is a zero-thickness kiss that cannot
triangulate watertight. Groove diameter stays exactly 40.0; only the
cover overlap changed. This is a mesh-construction fact, not a design
change — the mating interface still closes on the housing saddle.

## DFM notes (grounded in validator receipts)

- The cap groove forms the top half of the Dia 40 H6 bore: same
  0.016 mm band + Ra 0.8 hazard as the housing (see housing packet and
  rue019 receipts). Same required controls apply — multi-pass,
  tolerance-capable tooling, runout budget, hone, CMM.
- Mating faces (cap-to-housing split line) must be flat and clean or
  the assembled bore distorts: face-mill both halves' split faces in
  the same setup family where possible (shop practice, machinist to
  confirm — not validator-stated).

## Process routing (plain English)

Same saddle program family as the housing
(`programs/bore_h6_advisory.nc` pattern: rough r=19.0 → semi r=19.7 →
finish r=20.0 → spring pass → hone → CMM), mirrored to the cap's 20 mm
thickness. What that program IS: a strategy/sequence proof (see housing
packet). What it is NOT: posted, proven CAM for the cap — no separate
cap program exists in `programs/`, and none is claimed here.

## Assumptions (estimates, not verified facts)

- Cap bolt circle / bolt sizes are not modeled and not specified: the
  cap-to-housing and cap-to-base fastening scheme is open engineering.
- Feeds/speeds, if reused from the housing program, are reference
  values; prove on the machine.

## Verification

- Geometry: `verify_pillow_block.py` PASS line (groove 40.000, span
  39.988 within the 0.6 mesh tolerance).
- Tolerance planning: inherits the rue019-corrected PASS approach;
  cap-specific validator run is open work, not claimed here.
