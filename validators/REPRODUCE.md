# Reproduce it yourself

From a clean clone of this repo, with any Python 3.10+ that has
`numpy`, `trimesh`, and (optional, degrades gracefully) `pyyaml`:

```bash
pip install numpy trimesh
```

## 1. Model verification (STLs)

```bash
python verifiers/verify_pillow_block.py
```

Expected output (exit 0):

```text
PASS housing: watertight=True facets=500 vol=182662.4mm3 bbox=(100.00,80.00,30.00) bore_dia=40.000 bore_span_x=40.000 n_borev=28
PASS cap: watertight=True facets=500 vol=106759.3mm3 bbox=(100.00,80.00,20.00) bore_dia=40.000 bore_span_x=39.988 n_borev=28
PASS base_plate: watertight=True facets=876 vol=138586.7mm3 bbox=(120.00,100.00,12.00)
ALL PASS
```

## 2. Tolerance validator (RUE-019)

`validators/validate_tolerance_risk.py` is a verbatim copy of the
deterministic source validator (stdlib only; `yaml` optional). It writes
`tolerance-risk-validation.json` + `.md` next to each job card:

```bash
python validators/validate_tolerance_risk.py jobs/rue019-block
echo "exit: $?"
# exit: 1  — result BLOCK (end-mill-only Ø40 H6 plan)

python validators/validate_tolerance_risk.py jobs/rue019-corrected
echo "exit: $?"
# exit: 0  — result PASS (bore + hone + CMM prescription)
```

Both receipts are checked into `jobs/` — re-running overwrites them
with identical verdicts (timestamps differ, verdicts don't).

## 3. Advisory programs

`programs/*.nc` are strategy/sequence proofs, not posted CAM (see the
packet IS/IS-NOT notes). They parse under any Fanuc-dialect reader that
accepts comments, G0/G1/G2/G3, G81/G84 cycles, and M30.
