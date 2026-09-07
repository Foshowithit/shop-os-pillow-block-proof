#!/usr/bin/env python3
"""Verify pillow-block STLs: watertight, facets, volume, bbox, bore O40.

Bore check (programmatic, no eyeballing): vertices near the bore axis with
radius ~= 20 mm are bore-surface verts; fitted diameter must be 40.0 +/- 0.6
(mesh tol 0.5). Housing bore axis: (x=50, z=30) along Y; cap: (x=50, z=0).
Run from the repo root: python verifiers/verify_pillow_block.py
Needs: numpy, trimesh (pip install numpy trimesh).
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

D = Path(__file__).resolve().parent / ".." / "models"
EXPECT_BBOX = {
    "housing": (100.0, 80.0, 30.0),
    "cap": (100.0, 80.0, 20.0),
    "base_plate": (120.0, 100.0, 12.0),
}
BORE = {"housing": (50.0, 30.0), "cap": (50.0, -0.5)}  # (x0, z0), axis Y, r=20
# NOTE: cap tool center is 0.5 below the mating face (0.5 blind cover) because
# nominal R20-on-20-thick geometry is tangent (zero-thickness kiss) and cannot
# triangulate watertight. Groove dia stays exactly 40.0; envelope 100x80x20.

ok = True
for stem, exp in EXPECT_BBOX.items():
    m = trimesh.load(D / f"{stem}.stl", force="mesh")
    ext = m.bounds[1] - m.bounds[0]
    line = (f"{stem}: watertight={m.is_watertight} facets={len(m.faces)} "
            f"vol={m.volume:.1f}mm3 bbox=({ext[0]:.2f},{ext[1]:.2f},{ext[2]:.2f})")
    bok = True
    if stem in BORE:
        x0, z0 = BORE[stem]
        v = m.vertices  # groove meshed with full-length triangles: use all verts
        r = np.hypot(v[:, 0] - x0, v[:, 2] - z0)
        bv = v[np.abs(r - 20.0) < 0.5]
        dia = 2 * float(np.median(np.hypot(bv[:, 0] - x0, bv[:, 2] - z0))) if len(bv) else -1.0
        span = float(bv[:, 0].max() - bv[:, 0].min()) if len(bv) else -1.0
        bok = len(bv) > 0 and abs(dia - 40.0) <= 0.6 and abs(span - 40.0) <= 0.6
        line += f" bore_dia={dia:.3f} bore_span_x={span:.3f} n_borev={len(bv)}"
    good = (m.is_watertight and all(abs(a - b) < 0.6 for a, b in zip(ext, exp))
            and bok)
    ok &= good
    print(("PASS " if good else "FAIL ") + line)

print("ALL PASS" if ok else "FAILURES PRESENT")
sys.exit(0 if ok else 1)
