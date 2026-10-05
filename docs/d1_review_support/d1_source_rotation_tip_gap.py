"""Check an exact source-tip normal projection from the saved rejected pose."""

import json
from pathlib import Path

import numpy as np


root = Path(__file__).resolve().parent
raw = json.loads((root / "d1_source_rotation_bound_sample_20260929.json").read_text())
geometry = raw["rejected_pose_geometry"]
source = np.asarray(geometry["physical_source_positions_m"], dtype=float)
target = np.asarray(geometry["physical_target_positions_m"], dtype=float)
source_face = source[[3, 4, 9, 8]]
target_face = target[[0, 1, 3]]
point = source_face[1]
source_normal = np.cross(source_face[1]-source_face[0],
                         source_face[2]-source_face[1])
source_normal /= np.linalg.norm(source_normal)
target_normal = np.cross(target_face[1]-target_face[0],
                         target_face[2]-target_face[0])
target_normal /= np.linalg.norm(target_normal)
normal_cosine = float(source_normal @ target_normal)
if normal_cosine <= 0.0:
    raise ValueError("source and target normals are inconsistent")
normal_gap = float((point-target_face[0]) @ target_normal / normal_cosine)
hit = point-normal_gap*source_normal
barycentric = np.linalg.solve(
    np.column_stack((target_face[1, :2]-target_face[0, :2],
                     target_face[2, :2]-target_face[0, :2])),
    hit[:2]-target_face[0, :2],
)
weights = np.asarray((1.0-sum(barycentric), *barycentric))
if min(weights) <= 0.0:
    raise ValueError("normal projection misses target triangle interior")
result = {
    "source_local_face": [3, 4, 9, 8],
    "target_local_face": [0, 1, 3],
    "source_tip_parametric_coordinate": [1.0, 0.0],
    "normal_gap_m": normal_gap,
    "normal_cosine": normal_cosine,
    "target_barycentric_at_normal_hit": weights.tolist(),
    "certified_global_lower_m": geometry["certified_global_lower_m"],
    "gap_minus_lower_m": normal_gap-geometry["certified_global_lower_m"],
}
if not 0.0 <= result["gap_minus_lower_m"] < 1e-9:
    raise AssertionError("tip projection does not corroborate the lower bound")
output = root / "d1_source_rotation_tip_gap_20260929.json"
if output.exists():
    raise FileExistsError(output)
output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
print(json.dumps(result, indent=2))
