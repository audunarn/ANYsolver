"""Bounded G0 comparison of rigid and distributing 0.1 m footprints.

The same E4 panel and retained B3 beam supply both local tangent maps.
This is a point-station mechanics diagnostic, not a solved full line bond.
"""

from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits

from anysolver._ge_beam3_pose_joint import RigidPoseJoint
from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeNodalSpatialPort
from scripts._b3_e4_f03_shell_finite_pose_candidate import reference_nodes
from scripts._b3_e4_f03_shell_spatial_linear_port import physical_shell_stiffness
from scripts._b3_e4_f03_shell_strip_pose_candidate import (
    pose_from_e4_total_strip, reference_spatial_trace_strip, strip_weights,
)
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = vector
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def case(topology: str) -> dict:
    """Compare actual linearized local maps and their virtual work."""
    shell = FlatE4TrialPanel(make_shell(4, topology, n_y=4))
    beam = build(4, z_offset=.085,
                 torsion_constant=square_torsion_constant())
    port = NativeNodalSpatialPort(beam.context, 2)
    shell_size = 6 * shell.panel.node_count
    count = shell_size + beam.context.count
    points = tuple((.5+dx, dy, 0.) for dx, dy in
                   ((-.05, -.05), (.05, -.05), (.05, .05), (-.05, .05)))
    beam_high, beam_low, beam_frame = port.pose_pair(
        beam.context.initial.mechanical)
    beam_center = beam_high + beam_low
    if not np.allclose(beam_center, (.5, 0., .085), atol=1e-14):
        raise ArithmeticError("native patch center changed")
    beam_trace = port.tangent(beam.context.initial.mechanical)
    rigid = np.zeros((12, count))
    for i, point in enumerate(points):
        indices, shape = shell.panel._shape(point[0], point[1])
        for node, weight in zip(indices, shape):
            rigid[3*i:3*i+3, 6*node:6*node+3] += weight * np.eye(3)
        rigid[3*i:3*i+3, shell_size:] = np.column_stack((
            -np.eye(3), skew(np.asarray(point)-beam_center))) @ beam_trace

    shell_position, shell_frame = pose_from_e4_total_strip(
        shell.panel, .5, np.zeros(shell_size),
        half_length=.05, half_width=.05)
    joint = RigidPoseJoint(
        np.array((shell_position, beam_center)),
        np.array((shell_frame, beam_frame)))
    evaluation = joint.evaluate(
        np.array((shell_position, beam_high)),
        np.array((shell_frame, beam_frame)), np.zeros(6),
        position_low=np.array((np.zeros(3), beam_low)))
    if np.linalg.norm(evaluation.constraints) > 1e-12:
        raise ArithmeticError("distributing patch is not stress free")
    trace = reference_spatial_trace_strip(
        shell.panel, .5, half_length=.05, half_width=.05)
    distributing = np.column_stack((
        evaluation.constraint_jacobian[:, :6] @ trace,
        evaluation.constraint_jacobian[:, 6:] @ beam_trace))

    nx = shell.panel.x_interval_count
    fixed_shell = {6*j*(nx+1)+axis
                   for j in range(shell.panel.n_y+1)
                   for axis in range(6)}
    fixed_beam = {shell_size+index for index in beam.context.fixed}
    free = np.array([index for index in range(count)
                     if index not in fixed_shell and index not in fixed_beam])
    ranks = (int(np.linalg.matrix_rank(distributing[:, free])),
             int(np.linalg.matrix_rank(rigid[:, free])))
    if ranks != (6, 12):
        raise ArithmeticError(f"local footprint rows lost rank: {ranks}")

    reference = reference_nodes(shell.panel)
    translation = np.array((.003, -.002, .004))
    rotation = np.array((.008, -.006, .01))
    common = np.zeros(count)
    shell_nodal = common[:shell_size].reshape(-1, 6)
    shell_nodal[:, :3] = translation + np.cross(rotation, reference)
    shell_nodal[:, 3:] = rotation
    for node in range(beam.n_half_cells+1):
        origin = np.array((node/beam.n_half_cells, 0., .085))
        start = shell_size + 6*node
        common[start:start+3] = translation + np.cross(rotation, origin)
        common[start+3:start+6] = rotation
    rigid_gap = float(np.max(np.abs(rigid @ common)))
    distributing_gap = float(np.max(np.abs(distributing @ common)))
    if max(rigid_gap, distributing_gap) > 2e-12:
        raise ArithmeticError("local footprint lost rigid-motion invariance")

    # This field vanishes at the fixed left edge and has zero strip mean.
    # Its geometric z slope is nonzero while independent shell rotations stay zero.
    mean, _ = strip_weights(shell.panel, .5,
                            half_length=.05, half_width=.05)
    x = reference[:, 0]
    a = (x-.5)*(x+.5)
    b = x+.5
    shear = np.zeros(count)
    shear[:shell_size].reshape(-1, 6)[:, 2] = .01 * (
        a - (mean@a)/(mean@b)*b)
    energy = float(shear[:shell_size] @ (
        physical_shell_stiffness(shell.panel) @ shear[:shell_size]))
    distribution_shear_gap = float(np.max(np.abs(distributing @ shear)))
    rigid_shear_gap = float(np.linalg.norm(rigid @ shear))
    if (energy <= 0. or distribution_shear_gap > 2e-12 or
            rigid_shear_gap <= 1e-5):
        raise ArithmeticError("physical transverse-shear distinction failed")

    # Paired +My multipliers act on the same shell patch and beam station.
    distributing_moment = np.zeros(6)
    # c_R = Log(R_shell^T R_beam), so a negative multiplier gives +My
    # on the shell. The corner-force construction below gives that same
    # physical shell moment through its eccentric Fz resultants.
    distributing_moment[4] = -100.
    dx = np.array([point[0]-.5 for point in points])
    rigid_moment = np.zeros(12)
    rigid_moment[2::3] = -100.*dx/(dx@dx)
    distributed_force = distributing.T @ distributing_moment
    rigid_force = rigid.T @ rigid_moment
    def shell_my(force: np.ndarray) -> float:
        nodal = force[:shell_size].reshape(-1, 6)
        return float(np.sum(nodal[:, 4] - reference[:, 0]*nodal[:, 2]))
    shell_moments = (shell_my(distributed_force), shell_my(rigid_force))
    if max(abs(value-100.) for value in shell_moments) > 1e-8:
        raise ArithmeticError(f"paired shell moments differ: {shell_moments}")
    distributed_shear_work = float(distributed_force @ shear)
    rigid_shear_work = float(rigid_force @ shear)
    if (abs(distributed_shear_work) > 1e-9 or
            abs(rigid_shear_work) < 1e-3 or
            max(abs(distributed_force @ common),
                abs(rigid_force @ common)) > 1e-9):
        raise ArithmeticError("local moment work distinction failed")
    return {
        "topology": topology, "patch_half_widths_m": [.05, .05],
        "beam_axis_z_m": .085, "native_half_cells": 4,
        "rows_and_supported_ranks": {"distributing": [6, ranks[0]],
                                     "rigid": [12, ranks[1]]},
        "common_rigid_gap_max_m_rad": {
            "distributing": distributing_gap, "rigid": rigid_gap},
        "supported_shell_transverse_shear_mode": {
            "physical_energy_twice_j": energy,
            "distributing_gap_max_m_rad": distribution_shear_gap,
            "rigid_gap_l2_m": rigid_shear_gap,
            "distributing_my_work_j": distributed_shear_work,
            "rigid_my_work_j": rigid_shear_work},
        "shell_drilling_force_max": {
            "distributing": float(np.max(np.abs(
                distributed_force[:shell_size][5::6]))),
            "rigid": float(np.max(np.abs(
                rigid_force[:shell_size][5::6])))},
        "paired_shell_my_nm": {"distributing": shell_moments[0],
                               "rigid": shell_moments[1]},
        "scope": "local linearized patch row-space/work proof; rigid patch intentionally restrains local shear; not a full line solve or space selection",
    }


def run(output_dir: Path) -> None:
    source = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"],
                               text=True).strip():
        raise RuntimeError("run requires clean source")
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "status": "EXPLORATORY_NOT_G0_ACCEPTANCE", "source_sha": source,
        "question": "On the same physical 0.1 m E4/B3 patch, do exact rigid and distributing laws admit different transverse-shear work and moment paths?",
        "decision": "If the local modes/work differ, preserve distinct rigid and distributing footprints and assess termination idealization; do not treat one as a penalty approximation of the other. A rank or rigid-motion failure requires mechanics revision.",
        "python": platform.python_version(), "numpy": np.__version__,
        "threads": 1, "models": ["Q4", "S3-V2D"],
        "geometry": "plate [-.5,1.5]x[-.5,.5] z=0 thickness .07 m; square patch at x=.5 half-width .05/.05 m; B3 axis z=.085 m",
        "section": "square-bar Saint-Venant J; other native generalized resultants unchanged",
        "support": "full shell left edge and native B3 root fixed",
        "scope": "local exact linearization, not a nonlinear/global footprint or line qualification",
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n")
        with (output_dir / "results.jsonl").open("w") as stream:
            for topology in ("Q4", "S3-V2D"):
                result = case(topology)
                stream.write(json.dumps(result, allow_nan=False) + "\n")
                stream.flush()
                print(topology, result["supported_shell_transverse_shear_mode"],
                      flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    run(parser.parse_args().output_dir)
