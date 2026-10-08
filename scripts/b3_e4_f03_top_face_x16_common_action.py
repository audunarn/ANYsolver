"""Replay saved top-face actions on validated F5 common virtual hats."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_factor5_common_weak_work import _native_family, _project


BASE = Path("docs/agent_plans")
F5 = Path(".qualification/b3-ge-e4-pl/f03-c1-factor5-common-weak-work-dev-20260926-v2/result.json")
CASES = (
    ("x8_m4", "B3_GE_E4_PL_F03_TOP_FACE_X8_RESOLUTION_DEV_20260927_v2.json",
     "top_face_four_intervals", 8, 4, 12),
    ("x16_m4", "B3_GE_E4_PL_F03_TOP_FACE_X16_FOUR_CONTROL_20260927.json",
     "top_face_four_intervals", 16, 4, 12),
    ("x16_m8", "B3_GE_E4_PL_F03_TOP_FACE_X16_PHYSICAL_DEV_20260927_v2.json",
     "top_face_eight_intervals", 16, 8, 12),
    ("x16_b24_m4", "B3_GE_E4_PL_F03_TOP_FACE_X16_B24_FOUR_20260927.json",
     "top_face_four_intervals", 16, 4, 24),
    ("x16_b24_m8", "B3_GE_E4_PL_F03_TOP_FACE_X16_B24_EIGHT_20260927.json",
     "top_face_eight_intervals", 16, 8, 24),
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate() -> dict:
    reference = json.loads(F5.read_text())
    if "validated saved-F5 common continuous weak-action" not in reference["classification"]:
        raise ValueError("validated F5 action required")
    for name, expected in reference["inputs_sha256"].items():
        if _sha(Path(name)) != expected:
            raise ValueError(f"protected F5 input changed: {name}")
    solid = np.asarray(reference["solid_hat_action"], dtype=float)
    if solid.shape != (2, 3):
        raise ValueError("F5 common-hat inventory changed")
    reports = {}
    sources = {str(F5): _sha(F5)}
    for label, basename, family, nx, intervals, beam_half_cells in CASES:
        path = BASE / basename
        sources[str(path)] = _sha(path)
        record = json.loads(path.read_text())
        native = record["result"]
        if ((native["bond_x_cells"], native["bond_y_cells"]) != (nx, 4) or
                native["plate_thickness_m"] != .035 or
                native["beam_half_cells"] != beam_half_cells or
                native["results"][family]["constraint_rank"] != 6*intervals):
            raise ValueError(f"native {label} physical model changed")
        # Both separate influences use the same declared +100 Nm Mx and
        # -1000 N Fz; the latter's sign is checked from the solved motion.
        if (native["results"][family]["cases"]["tip_mx"]["tip_rx_rad"] <= 0. or
                native["results"][family]["cases"]["tip_fz"]["tip_uz_m"] >= 0.):
            raise ValueError(f"native {label} load signs changed")
        x, force, wrench = _native_family(native, family)
        hats = _project(x, force, shell=True)
        common = np.array((wrench[1], wrench[2], wrench[3]+.0675*wrench[1]))
        if not np.allclose(hats.sum(axis=0), common, rtol=0., atol=1e-7):
            raise ArithmeticError(f"native {label} common work not conserved")
        first = ((hats[1, :2]-hats[0, :2])*.05)
        reports[label] = {
            "native_hat_action_N_Nm": hats.tolist(),
            "native_minus_F5_hat_action_N_Nm": (hats-solid).tolist(),
            "relative_l2_by_channel": (np.linalg.norm(hats-solid, axis=0) /
                np.maximum(np.linalg.norm(solid, axis=0), 1e-12)).tolist(),
            "native_first_x_moment_yz_Nm": first.tolist(),
            "native_shell_wrench_N_Nm": wrench.tolist(),
            "active_shell_nodes": len(x),
        }
    return {
        "classification": "saved-action common-work diagnostic, not G0B acceptance or multiplier selection",
        "question": "Does top-face row enrichment move the x16 physical action coherently toward the validated F5 common transfer fields?",
        "reference": "saved F5 bar-on-plate action, stronger shared-node bond and different continuum idealization",
        "solid_hat_action_N_Nm": solid.tolist(),
        "cases": reports,
        "input_sha256": sources,
        "source_sha256": {str(Path(__file__)): _sha(Path(__file__)),
                          "scripts/b3_e4_f03_c1_factor5_common_weak_work.py":
                          _sha(Path("scripts/b3_e4_f03_c1_factor5_common_weak_work.py"))},
        "limitations": ["two low-order hats do not detect every native retained or pointwise mode",
                        "F5 pointwise bond and continuum shell differ from the native weak law",
                        "no new solid or coupled numerical solve was run"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({key: value["relative_l2_by_channel"]
                      for key, value in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
