"""Correct the native image dimension in the bounded F5 cut comparison.

The V1 full-cut rank is the rank of *formal* independent rigid-section
coordinates. Actual native B3 endpoint positions share three coordinates;
only the two retained rotation triplets are independent at this station.
Neither calculation supplies an admissible intact-solid virtual field.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts import b3_e4_f03_c1_port_trace_compatibility as prior
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


V1 = Path("docs/agent_plans/B3_GE_E4_PL_F03_C1_PORT_TRACE_COMPAT_DEV_V1.json")
V3 = Path("docs/agent_plans/B3_GE_E4_PL_F03_C1_F5_SIDED_PORT_DEV_V3.json")


def evaluate() -> dict:
    old = json.loads(V1.read_text())
    if old != prior.evaluate():
        raise ArithmeticError("source-bound V1 cut audit changed")
    validated = json.loads(V3.read_text())
    if validated.get("status") != "PASSED_BOUNDED_STRESS_AND_SAMPLED_GAP_GUARDS":
        raise ValueError("bounded F5 sided-cut validation required")
    for path, digest in old["inputs_sha256"].items():
        if validated["inputs_sha256"].get(path) != digest:
            raise ValueError("V1 cut input differs from bounded F5 validation")
    native = build(12, z_offset=.0675,
                   torsion_constant=square_torsion_constant(),
                   reference_profile="c1_tangent_2um")
    state = native.context.initial.mechanical
    ports = (NativeHalfCellSpatialPort(native.context, 5, 0, 1.),
             NativeHalfCellSpatialPort(native.context, 5, 1, 0.))
    left, right = (port.tangent(state) for port in ports)
    pair_rank = int(np.linalg.matrix_rank(np.vstack((left, right)), tol=1e-10))
    translation_difference = float(np.max(np.abs(left[:3] - right[:3])))
    relative_rotation_rank = int(np.linalg.matrix_rank(
        left[3:] - right[3:], tol=1e-10))
    if pair_rank != 9 or translation_difference != 0 or relative_rotation_rank != 3:
        raise ArithmeticError("native endpoint image is not shared-translation/independent-rotation")

    inp = prior.ROOT / "solid-5-sided-port.inp"
    model = json.loads((prior.ROOT / "model.json").read_text())
    xyz, elements = read_deck(inp)
    cut = np.intersect1d(np.flatnonzero(np.isclose(
        xyz[:, 0], prior.AXIS[0], rtol=0, atol=1e-12)),
        np.unique(elements["Stiffener"].ravel()))
    shared = np.intersect1d(cut, np.asarray(
        model["shared_interface_node_ids"], dtype=int))
    full_rotation_rank = int(np.linalg.matrix_rank(
        prior._trace_matrix(xyz[cut])[:, 3:], tol=1e-10))
    seam_rotation_rank = int(np.linalg.matrix_rank(
        prior._trace_matrix(xyz[shared])[:, 3:], tol=1e-10))
    if (len(cut), len(shared), full_rotation_rank, seam_rotation_rank) != (341, 21, 3, 3):
        raise ArithmeticError("declared cut/rotation trace changed")
    return {
        "classification": "bounded actual-native image and assumed rigid-section cut algebra, not connection qualification",
        "decision": "Do the two actual native endpoint poses have 12 independent rigid coordinates on the intact solid cut?",
        "v1_sha256": prior.sha(V1),
        "v1_runner_sha256": prior.sha(Path(prior.__file__)),
        "bounded_f5_validation_sha256": prior.sha(V3),
        "native": {
            "formal_two_pose_coordinate_dimension": 12,
            "actual_pair_tangent_image_dimension": pair_rank,
            "shared_translation_jacobian_max_difference": translation_difference,
            "independent_relative_rotation_rank": relative_rotation_rank,
            "actual_full_cut_compatible_image_dimension": pair_rank - full_rotation_rank,
        },
        "assumed_rigid_section_extension": {
            "cut_nodes": len(cut), "bonded_cut_nodes": len(shared),
            "full_relative_rotation_trace_rank": full_rotation_rank,
            "bonded_seam_relative_rotation_trace_rank": seam_rotation_rank,
            "full_formal_pose_difference_rank": old["solid"]["left_minus_right_trace_rank"],
            "bonded_seam_formal_pose_rank": old["solid"]["normalized_rigid_trace_rank_bonded_seam"],
        },
        "conclusion": "The actual B3 endpoint image has shared translation and three independent relative rotations. Under an assumed rigid-section extension to the intact solid cut, continuity removes those three relative rotations and leaves a six-dimensional compatible native image. This blocks direct independent-sided rigid scoring without a separately justified conforming extension and companion seam work; it does not establish a connection defect.",
        "limits": [
            "the spatial port defines position and frame, not a unique solid-section displacement extension",
            "the rank result is kinematic and cannot select the physical shell trace or multiplier space",
            "the V1 bar-only broken-field work remains projection-dependent and is not an intact-system error",
        ],
        "runner_sha256": prior.sha(Path(__file__)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"native_image": result["native"]["actual_pair_tangent_image_dimension"],
                      "compatible_image": result["native"]["actual_full_cut_compatible_image_dimension"],
                      "relative_rotation_rank": result["native"]["independent_relative_rotation_rank"]}))


if __name__ == "__main__":
    main()
