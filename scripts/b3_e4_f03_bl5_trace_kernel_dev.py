"""Bounded BL5 beam-trace kernel feasibility check; not F03 assessment.

The physical feature is a broken H1-like surface-pose trace. Its pose map is
assembled independently of the BL5 gap Jacobian on the same native retained
coordinates. The result only tests whether this proposed trace norm observes
every actual beam-side BL5 row; it says nothing about mixed-system stability.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import anysolver
from anysolver import stiffened_shell
from anysolver._stiffened_shell_l1_local_experimental import NativeHalfCellPort
import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info, threadpool_limits

from test_stiffened_shell_l1_assembly_experimental import _bl5_joint_mesh_definition


ROOT = Path(__file__).resolve().parents[1]
LENGTH_M = 1.
WIDTH_M = .1
SURFACE_Z_M = -.05
KNOTS = (0., .19, .45, .76, 1.)


def _skew(a):
    x, y, z = a
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def _pose_map(owner, element_index, cell, fraction, y):
    element = owner._beam_parts[element_index][0]
    reference = element.operator.reference
    node_rows = tuple(owner._beam_index[node] for node in element.node_ids)
    port = NativeHalfCellPort.from_reference(
        reference, node_rows, element_index, cell, float(fraction),
        6*len(owner._beam_ids), owner._beam_count)
    result = np.zeros((6, owner._beam_count))
    left, right = port.nodes
    result[:3, 6*left:6*left+3] = (1.-fraction)*np.eye(3)
    result[:3, 6*right:6*right+3] = fraction*np.eye(3)
    slots = port.active_beam_slots()[-3:]
    result[:3, slots] = -_skew(port.lift+port.frame@np.array((0., y, SURFACE_Z_M)))
    result[3:, slots] = np.eye(3)
    return result


def _feature(owner):
    roots, weights = np.polynomial.legendre.leggauss(3)
    vandermonde = np.vander(roots, N=3, increasing=True)
    derivative = np.column_stack((np.zeros(3), np.ones(3), 2*roots))
    differentiation = derivative@np.linalg.inv(vandermonde)
    features = []
    for edge, (element_index, cell) in enumerate(owner._definition.lines[0].beam_halfcells):
        left, right = edge/8, (edge+1)/8
        half_length = (right-left)/2
        for transverse, transverse_weight in zip(roots, weights):
            y = WIDTH_M*float(transverse)/2
            maps = np.stack([_pose_map(owner, element_index, cell,
                                     (float(xi)+1)/2, y) for xi in roots])
            derivative_maps = np.einsum("ij,jkn->ikn", differentiation, maps)/half_length
            for i, wx in enumerate(weights):
                root = np.sqrt(half_length*float(wx)*float(transverse_weight)/2)
                features.append(root*maps[i]/LENGTH_M)
                features.append(root*derivative_maps[i])
    return np.vstack(features)


def analyze():
    expected = (ROOT/"src"/"anysolver"/"__init__.py").resolve()
    if Path(anysolver.__file__).resolve() != expected:
        raise RuntimeError("trace-kernel diagnostic imported another ANYsolver")
    base = _bl5_joint_mesh_definition(4, 8, 1)
    coordinates = tuple((KNOTS[i % 5], xyz[1], xyz[2])
                        for i, xyz in enumerate(base.shell.coordinates_m))
    definition = replace(base,
        shell=replace(base.shell, coordinates_m=coordinates),
        lines=(replace(base.lines[0], basis="continuous_p1_coarse"),))
    with threadpool_limits(limits=1):
        pools = threadpool_info()
        if any(pool.get("num_threads", 1) != 1 for pool in pools):
            raise RuntimeError("one numerical thread was not effective")
        owner = stiffened_shell.create_analysis(definition=definition)
        try:
            beam_free = owner._free[owner._free >= owner._shell_count]-owner._shell_count
            scale = owner._coordinate_scale[owner._shell_count+beam_free]
            feature = _feature(owner)[:, beam_free]*scale
            rows = owner._C[:, owner._shell_count+beam_free].toarray()*scale
            # The kernel is insensitive to nonzero row units; normalize only
            # for the numerical rank/SVD diagnostic, not as an F03 norm.
            row_scale = np.maximum(np.linalg.norm(rows, axis=1), np.finfo(float).tiny)
            rows /= row_scale[:, None]
            feature_scale = np.maximum(np.linalg.norm(feature, axis=1), np.finfo(float).tiny)
            feature /= feature_scale[:, None]
            _, singular, vt = linalg.svd(feature, full_matrices=True,
                                         check_finite=True)
            tolerance = singular[0]*max(feature.shape)*np.finfo(float).eps
            rank = int(np.count_nonzero(singular > tolerance))
            kernel = vt[rank:].T
            leakage = rows@kernel
            combined_rank = int(np.linalg.matrix_rank(
                np.vstack((feature, rows)), tol=tolerance))
            # Native nodal rotation slots are deliberately absent from this
            # retained half-cell pose. The checker must detect such a row.
            invisible = np.flatnonzero(np.linalg.norm(feature, axis=0) < 1e-13)
            if not len(invisible):
                raise ArithmeticError("negative control needs an unobserved coordinate")
            synthetic = np.zeros((1, feature.shape[1]))
            synthetic[0, invisible[0]] = 1.
            negative_rank = int(np.linalg.matrix_rank(
                np.vstack((feature, synthetic)), tol=tolerance))
            negative_leakage = float(np.linalg.norm(synthetic@kernel))
            if negative_rank != rank+1 or negative_leakage < .9:
                raise ArithmeticError("trace-kernel negative control was not detected")
            return {
                "status": "BL5_TRACE_KERNEL_FEASIBILITY_ONLY",
                "source_git": subprocess.check_output(
                    ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip(),
                "runner_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                "product_sha256": sha256((ROOT/"src"/"anysolver"/
                    "_stiffened_shell_l1_assembly_experimental.py").read_bytes()).hexdigest(),
                "imported_anysolver": str(expected),
                "threadpools": pools,
                "fixture": {"shell_knots_m": KNOTS, "beam_halfcells": 8,
                            "surface_width_m": WIDTH_M,
                            "surface_z_from_axis_m": SURFACE_Z_M,
                            "feature": "broken H1-like full spatial pose; three Gauss x/y"},
                "feature_shape": feature.shape, "beam_rows_shape": rows.shape,
                "feature_rank": rank, "combined_rank": combined_rank,
                "kernel_dimension": kernel.shape[1],
                "rank_tolerance": float(tolerance),
                "last_nonzero_singular": float(singular[rank-1]),
                "first_discarded_singular": (float(singular[rank])
                                              if rank < len(singular) else None),
                "relative_kernel_leakage": float(np.linalg.norm(leakage)/
                                                   np.linalg.norm(rows)),
                "max_kernel_row_leakage": float(np.max(np.abs(leakage), initial=0.)),
                "negative_control": {
                    "kind": "synthetic unobserved native nodal-rotation row",
                    "combined_rank": negative_rank,
                    "kernel_leakage": negative_leakage,
                },
                "limitations": "One supported nonuniform small fixture only; chosen physical surface trace needs mechanics review. No quotient, inf-sup, KKT, locking, accuracy or F03 acceptance.",
            }
        finally:
            owner.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = analyze()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "status", "feature_rank", "combined_rank", "kernel_dimension",
        "relative_kernel_leakage", "max_kernel_row_leakage")}))
