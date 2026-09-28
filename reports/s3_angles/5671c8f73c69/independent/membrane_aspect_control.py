"""Control for the membrane per-DOF efficiency criterion.

Runs the campaign's "right, narrow x" membrane family at 45 (regular),
30 (historical floor), 20 and 15 deg and reports the finest-level resultant
L2 error relative to the 45 deg family at equal DOF count, i.e. the quantity
the frozen criterion ``membrane_resultant_ratio_to_regular`` bounds by 1.5.

Usage: python reports/s3_angles/5671c8f73c69/independent/membrane_aspect_control.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
import qualify_s3_angles as q  # noqa: E402


def series(family, angle, narrow, levels=4):
    rows = []
    for level in range(levels):
        mesh = q.s3_family_mesh(family, angle, level, target=(4.0, 1.0), base_count=8 if narrow == "y" else 2, narrow=narrow)
        row = {"stats": q.mesh_statistics(mesh)}
        row.update(q.run_membrane(mesh))
        rows.append(row)
    return {"levels": rows}


regular = series("regular", 45.0, "y")
print("angle  family            aspect  N_L2(finest)  ratio_to_45deg_at_equal_dofs")
for angle in (30.0, 20.0, 15.0):
    for family in ("right", "right_alternating"):
        s = series(family, angle, "x")
        finest = s["levels"][-1]
        ratio = finest["resultant_l2_error"] / q.regular_error_at(regular, finest["stats"]["dofs"], "resultant_l2_error")
        aspect = 1.0 / q.math.tan(q.math.radians(angle))
        print(f"{angle:5.1f}  {family:17s} {aspect:6.2f}  {finest['resultant_l2_error']:.4e}    {ratio:.3f}", flush=True)
