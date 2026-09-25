"""Bounded G0 comparison of rigid and distributing 0.1 m footprints.

The same E4 panel and retained B3 beam supply both local tangent maps.
This is a point-station mechanics diagnostic, not a solved full line bond.
"""

from __future__ import annotations

import json
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info, threadpool_limits

from anysolver._ge_beam3_mixed_ad import Jet2, matvec, so3_exp, transpose
from anysolver._ge_beam3_pose_joint import RigidPoseJoint
from scripts._b3_e4_f03_coupled_point_work_candidate import directional_point_work
from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import SECTION_DIAGONAL, build
from scripts._b3_e4_f03_native_spatial_port import NativeNodalSpatialPort
from scripts._b3_e4_f03_shell_finite_pose_candidate import reference_nodes
from scripts._b3_e4_f03_shell_spatial_linear_port import physical_shell_stiffness
from scripts._b3_e4_f03_shell_strip_pose_candidate import (
    directional_pose_from_e4_total_strip, pose_from_e4_total_strip,
    reference_spatial_trace_strip, strip_weights,
)
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = vector
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def finite_rigid_work(shell: FlatE4TrialPanel, beam, port,
                      points: tuple[tuple[float, float, float], ...],
                      multipliers: np.ndarray) -> dict:
    """Check actual E4 interpolation/native nodal Exp-chart footprint work.

    Only the 12 corner-position rows of the declared rigid law are used.
    Shell director coordinates do not enter that law. The beam frame is the
    native nodal spatial frame, advanced from the same fixed predecessor.
    """
    base = beam.context.initial.mechanical
    shell_size = 6 * shell.panel.node_count
    q = np.zeros(shell_size)
    nodes = reference_nodes(shell.panel)
    nodal = q.reshape(-1, 6)
    nodal[:, 2] = .001 * (nodes[:, 0] + .5) * (1. + nodes[:, 1])
    nodal[:, 3] = .002 * (nodes[:, 0] + .5)
    nodal[:, 4] = -.003 * (nodes[:, 0] + .5)
    baseline = np.zeros(beam.context.count)
    start = 6 * port.node_index
    baseline[start:start+3] = (.0008, -.0005, .0004)
    baseline[start+3:start+6] = (.018, -.012, .009)
    state = beam.context.advance(base, baseline)
    beam_ref_high, beam_ref_low, beam_ref_frame = port.pose_pair(base)
    beam_ref = beam_ref_high + beam_ref_low
    offsets = [beam_ref_frame.T @ (np.asarray(point) - beam_ref)
               for point in points]
    shape_rows = [shell.panel._shape(point[0], point[1]) for point in points]

    u_shell = np.zeros_like(q)
    v_shell = np.zeros_like(q)
    u_shell.reshape(-1, 6)[:, 2] = .007 * (nodes[:, 0] + .5) * nodes[:, 1]
    v_shell.reshape(-1, 6)[:, 0] = .004 * (nodes[:, 0] + .5)
    u_beam = np.zeros(beam.context.count)
    v_beam = np.zeros(beam.context.count)
    u_beam[start:start+6] = (.003, -.002, .004, .07, -.05, .04)
    v_beam[start:start+6] = (-.002, .004, .001, -.06, .03, .05)

    def independent(a: float, b: float, *, motion=None) -> tuple[float, np.ndarray]:
        total = (q + a*u_shell + b*v_shell).reshape(-1, 6)
        changed = beam.context.advance(state, a*u_beam + b*v_beam)
        high, low, frame = port.pose_pair(changed)
        center = high + low
        gaps = []
        for (indices, weights), offset in zip(shape_rows, offsets):
            position = weights @ (nodes[indices] + total[indices, :3])
            if motion is not None:
                rotation, translation = motion
                position = rotation @ position + translation
                transformed_center = rotation @ center + translation
                transformed_frame = rotation @ frame
            else:
                transformed_center, transformed_frame = center, frame
            gaps.extend(transformed_frame.T @ (position-transformed_center) - offset)
        vector = np.asarray(gaps)
        return float(multipliers @ vector), vector

    # Two Jet directions give the complete mixed curvature of this actual
    # local chart, including multiplier-dependent beam-frame terms.
    a = Jet2.variable(0., 0, 2)
    b = Jet2.variable(0., 1, 2)
    high, low, frame = port.pose_pair(state)
    center = high + low
    frame_jets = so3_exp([a*value+b*other for value, other in
                          zip(u_beam[start+3:start+6], v_beam[start+3:start+6])])
    current_frame = [[sum(frame_jets[i][k]*frame[k, j] for k in range(3))
                      for j in range(3)] for i in range(3)]
    center_jets = [Jet2.constant(float(center[i]), 2) +
                   a*float(u_beam[start+i]) + b*float(v_beam[start+i])
                   for i in range(3)]
    work = Jet2.constant(0., 2)
    for (indices, weights), offset, row in zip(shape_rows, offsets, range(4)):
        position = weights @ (nodes[indices] + q.reshape(-1, 6)[indices, :3])
        pu = weights @ u_shell.reshape(-1, 6)[indices, :3]
        pv = weights @ v_shell.reshape(-1, 6)[indices, :3]
        distance = [Jet2.constant(float(position[i]), 2) + a*float(pu[i]) +
                    b*float(pv[i]) - center_jets[i] for i in range(3)]
        gaps = matvec(transpose(current_frame), distance)
        for axis in range(3):
            work += float(multipliers[3*row+axis]) * (gaps[axis]-float(offset[axis]))

    h = 2e-4
    f00, gap = independent(0., 0.)
    fp, _ = independent(h, 0.)
    fm, _ = independent(-h, 0.)
    gp, _ = independent(0., h)
    gm, _ = independent(0., -h)
    fpp, _ = independent(h, h)
    fpm, _ = independent(h, -h)
    fmp, _ = independent(-h, h)
    fmm, _ = independent(-h, -h)
    first_error = max(abs(work.gradient[0]-(fp-fm)/(2*h)),
                      abs(work.gradient[1]-(gp-gm)/(2*h)))
    mixed_fd = (fpp-fpm-fmp+fmm)/(4*h*h)
    mixed_error = abs(work.hessian[0, 1]-mixed_fd)
    physical_forces = (frame @ multipliers.reshape(4, 3).T).T
    shell_positions = np.array([
        weights @ (nodes[indices] + q.reshape(-1, 6)[indices, :3])
        for indices, weights in shape_rows])
    beam_force = -physical_forces.sum(axis=0)
    beam_moment = -np.cross(shell_positions-center, physical_forces).sum(axis=0)
    force_balance = float(np.linalg.norm(physical_forces.sum(axis=0)+beam_force))
    moment_balance = float(np.linalg.norm(
        np.cross(shell_positions, physical_forces).sum(axis=0) +
        np.cross(center, beam_force) + beam_moment))
    def physical_work(shell_direction, beam_direction):
        sampled = np.array([weights @ shell_direction.reshape(-1, 6)[indices, :3]
                            for indices, weights in shape_rows])
        return float(np.sum(physical_forces*sampled) +
                     beam_force@beam_direction[start:start+3] +
                     beam_moment@beam_direction[start+3:start+6])
    work_error = max(abs(work.gradient[0]-physical_work(u_shell, u_beam)),
                     abs(work.gradient[1]-physical_work(v_shell, v_beam)))
    from scipy.spatial.transform import Rotation
    motion = (Rotation.from_rotvec((.3, -.2, .4)).as_matrix(),
              np.array((2., -3., 1.)))
    moved, moved_gap = independent(0., 0., motion=motion)
    objective_error = max(abs(moved-f00), float(np.max(np.abs(moved_gap-gap))))
    if (abs(work.value-f00) > 1e-10 or first_error > 1e-6 or
            mixed_error > 1e-5 or objective_error > 1e-10 or
            abs(work.hessian[0, 1]) < 1e-3 or
            max(force_balance, moment_balance, work_error) > 1e-9):
        raise ArithmeticError("finite rigid footprint work/chart check failed")
    return {"potential_j": f00, "first_error_j": first_error,
            "mixed_hessian_j": float(work.hessian[0, 1]),
            "mixed_error_j": mixed_error,
            "objective_gap_work_error": objective_error,
            "force_balance_n": force_balance,
            "moment_balance_nm": moment_balance,
            "physical_work_error_j": work_error,
            "scope": "actual E4 position interpolation and native nodal Exp-chart, local nonzero-multiplier proof"}


def finite_distributing_work(shell: FlatE4TrialPanel, beam, port) -> dict:
    """Check the six-channel area-mean/polar patch through both finite charts."""
    panel = shell.panel
    shell_ref = pose_from_e4_total_strip(
        panel, .5, np.zeros(6*panel.node_count),
        half_length=.05, half_width=.05)
    base = beam.context.initial.mechanical
    beam_high, beam_low, beam_frame = port.pose_pair(base)
    joint = RigidPoseJoint(
        np.array((shell_ref[0], beam_high+beam_low)),
        np.array((shell_ref[1], beam_frame)))
    reference = joint.evaluate(
        np.array((shell_ref[0], beam_high)),
        np.array((shell_ref[1], beam_frame)), np.zeros(6),
        position_low=np.array((np.zeros(3), beam_low)))
    if np.max(np.abs(reference.constraints)) > 1e-12:
        raise ArithmeticError("distributing finite patch changed reference")
    rng = np.random.default_rng(615)
    shell_base = rng.normal(size=(panel.node_count, 6)) * .002
    first = rng.normal(size=shell_base.shape) * .025
    second = rng.normal(size=shell_base.shape) * .025
    beam_base = np.zeros(beam.context.count)
    beam_first = np.zeros_like(beam_base)
    beam_second = np.zeros_like(beam_base)
    start = 6*port.node_index
    beam_base[start:start+6] = (.0008, -.0005, .0004, .018, -.012, .009)
    beam_first[start:start+6] = (.003, -.002, .004, .07, -.05, .04)
    beam_second[start:start+6] = (-.002, .004, .001, -.06, .03, .05)
    state = beam.context.advance(base, beam_base)
    multipliers = np.array((18., -23., 31., 7., -100., 13.))
    analytic = directional_point_work(
        joint, panel, .5, shell_base.ravel(), first, second,
        port, state, beam_first, beam_second, multipliers,
        shell_port="physical_strip_005_005")

    def potential(a: float, b: float) -> float:
        shell_position, shell_frame = pose_from_e4_total_strip(
            panel, .5, (shell_base+a*first+b*second).ravel(),
            half_length=.05, half_width=.05)
        current = beam.context.advance(state, a*beam_first+b*beam_second)
        high, low, frame = port.pose_pair(current)
        return float(joint.evaluate(
            np.array((shell_position, high)),
            np.array((shell_frame, frame)), multipliers,
            position_low=np.array((np.zeros(3), low))).potential)

    h = 1e-5
    first_error = max(
        abs(analytic.first-(potential(h, 0.)-potential(-h, 0.))/(2*h)),
        abs(analytic.second-(potential(0., h)-potential(0., -h))/(2*h)))
    h = 2e-3
    mixed_fd = (potential(h, h)-potential(h, -h)-
                potential(-h, h)+potential(-h, -h))/(4*h*h)
    mixed_error = abs(analytic.mixed-mixed_fd)
    shell_position, shell_frame = pose_from_e4_total_strip(
        panel, .5, shell_base.ravel(), half_length=.05, half_width=.05)
    shell_d = directional_pose_from_e4_total_strip(
        panel, .5, shell_base.ravel(), first, second,
        half_length=.05, half_width=.05)
    high, low, beam_frame = port.pose_pair(state)
    beam_position = high + low
    evaluation = joint.evaluate(
        np.array((shell_position, high)),
        np.array((shell_frame, beam_frame)), multipliers,
        position_low=np.array((np.zeros(3), low)))
    shell_force = evaluation.residual[:3]
    shell_moment = evaluation.residual[3:6]
    beam_force = evaluation.residual[6:9]
    beam_moment = evaluation.residual[9:12]
    force_balance = float(np.linalg.norm(shell_force+beam_force))
    moment_balance = float(np.linalg.norm(
        np.cross(shell_position, shell_force)+shell_moment+
        np.cross(beam_position, beam_force)+beam_moment))

    def angular(frame_first: np.ndarray) -> np.ndarray:
        matrix = frame_first @ shell_frame.T
        return np.array((matrix[2, 1]-matrix[1, 2],
                         matrix[0, 2]-matrix[2, 0],
                         matrix[1, 0]-matrix[0, 1]))/2.

    beam_trace = port.tangent(state)
    first_trace = np.r_[shell_d.position_first,
                        angular(shell_d.frame_first),
                        beam_trace@beam_first]
    second_trace = np.r_[shell_d.position_second,
                         angular(shell_d.frame_second),
                         beam_trace@beam_second]
    physical_work_error = max(
        abs(analytic.first-evaluation.residual[:12]@first_trace),
        abs(analytic.second-evaluation.residual[:12]@second_trace))
    if (abs(analytic.potential-potential(0., 0.)) > 1e-10 or
            first_error > 1e-6 or mixed_error > 1e-5 or
            abs(analytic.mixed) < 1e-3 or
            max(force_balance, moment_balance, physical_work_error) > 1e-9):
        raise ArithmeticError("finite distributing patch pullback failed")
    return {"potential_j": analytic.potential,
            "first_error_j": first_error, "mixed_hessian_j": analytic.mixed,
            "mixed_error_j": mixed_error,
            "force_balance_n": force_balance,
            "moment_balance_nm": moment_balance,
            "physical_work_error_j": physical_work_error,
            "scope": "actual E4 area-mean/polar pose and native nodal Exp-chart, nonzero-multiplier local proof"}


def termination_local(shell: FlatE4TrialPanel, beam) -> dict:
    """Check a declared last-0.1 m bonded patch at the native beam tip."""
    panel = shell.panel
    shell_size = 6*panel.node_count
    port = NativeNodalSpatialPort(beam.context, beam.n_half_cells)
    state = beam.context.initial.mechanical
    high, low, frame = port.pose_pair(state)
    center = high+low
    station = .95
    points = tuple((x, y, 0.) for x, y in
                   ((.9, -.05), (1., -.05), (1., .05), (.9, .05)))
    if np.max(np.abs(center - (1., 0., .085))) > 1e-14:
        raise ArithmeticError("native tip footprint geometry changed")
    total = shell_size+beam.context.count
    beam_trace = port.tangent(state)
    rigid = np.zeros((12, total))
    offsets = []
    for i, point in enumerate(points):
        indices, shape = panel._shape(point[0], point[1])
        for node, weight in zip(indices, shape):
            rigid[3*i:3*i+3, 6*node:6*node+3] += weight*np.eye(3)
        rigid[3*i:3*i+3, shell_size:] = np.column_stack((
            -np.eye(3), skew(np.asarray(point)-center)))@beam_trace
        offsets.append(frame.T@(np.asarray(point)-center))
    shell_position, shell_frame = pose_from_e4_total_strip(
        panel, station, np.zeros(shell_size),
        half_length=.05, half_width=.05)
    joint = RigidPoseJoint(
        np.array((shell_position, center)),
        np.array((shell_frame, frame)))
    evaluation = joint.evaluate(
        np.array((shell_position, high)),
        np.array((shell_frame, frame)), np.zeros(6),
        position_low=np.array((np.zeros(3), low)))
    trace = reference_spatial_trace_strip(
        panel, station, half_length=.05, half_width=.05)
    distributing = np.column_stack((
        evaluation.constraint_jacobian[:, :6]@trace,
        evaluation.constraint_jacobian[:, 6:]@beam_trace))
    fixed_shell = {6*j*(panel.x_interval_count+1)+axis
                   for j in range(panel.n_y+1) for axis in range(6)}
    fixed_beam = {shell_size+index for index in beam.context.fixed}
    free = np.array([index for index in range(total)
                     if index not in fixed_shell and index not in fixed_beam])
    ranks = (int(np.linalg.matrix_rank(distributing[:, free])),
             int(np.linalg.matrix_rank(rigid[:, free])))
    # The patch lies entirely on the plate; its mean is not the native tip.
    # A physical shell My must still be recovered about one common origin.
    dmoment = np.zeros(6)
    dmoment[4] = -100.
    dx = np.array([point[0]-station for point in points])
    rmoment = np.zeros(12)
    rmoment[2::3] = -100.*dx/(dx@dx)
    reference = reference_nodes(panel)
    def shell_my(force):
        nodal = force[:shell_size].reshape(-1, 6)
        return float(np.sum(nodal[:, 4]-reference[:, 0]*nodal[:, 2]))
    moments = (shell_my(distributing.T@dmoment),
               shell_my(rigid.T@rmoment))
    rigid_reference_gap = max(float(np.linalg.norm(
        frame.T@(np.asarray(point)-center)-offset))
        for point, offset in zip(points, offsets))
    if (ranks != (6, 12) or
            max(abs(value-100.) for value in moments) > 1e-8 or
            max(rigid_reference_gap,
                float(np.max(np.abs(evaluation.constraints)))) > 1e-12):
        raise ArithmeticError("local termination footprint admission failed")

    # The small dense system is a bounded, independent G0 assembly oracle.
    # Both laws use identical E4/native-B3 tangents, supports and tip loads.
    shell_k = shell.evaluate(np.zeros(shell_size), station).tangent
    primal = linalg.block_diag(shell_k, beam.tangent.toarray())
    force_scale = 1e6
    displacement_scale = force_scale/(210e9*.07)
    nodal_scale = np.tile(np.full(6, displacement_scale),
                          panel.node_count+beam.context.nodal_count//6)
    resultants = np.r_[np.tile(SECTION_DIAGONAL[:3]*displacement_scale, 2),
                       np.tile(SECTION_DIAGONAL[3:]*displacement_scale, 4)]
    retained_scale = np.tile(np.r_[np.full(6, displacement_scale), resultants],
                              beam.n_half_cells//2)
    primal_scale = np.r_[nodal_scale, retained_scale]
    if len(primal_scale) != total:
        raise ArithmeticError("termination retained scale layout changed")

    def loaded(constraint: np.ndarray, axis: int) -> dict:
        m = len(constraint)
        n = len(free)
        rows = constraint[:, free]
        kkt = np.block([[primal[np.ix_(free, free)], rows.T],
                        [rows, np.zeros((m, m))]])
        scale = np.r_[primal_scale[free], np.full(m, force_scale)]
        energy = force_scale*displacement_scale
        scaled = (scale[:, None]*kkt)*scale[None, :]/energy
        load = np.zeros(total)
        load[shell_size+6*beam.n_half_cells+axis] = (
            100. if axis == 3 else 1000.)
        rhs = np.r_[load[free]*scale[:n]/energy, np.zeros(m)]
        answer = linalg.solve(scaled, rhs, assume_a="gen")
        full = np.zeros(total)
        full[free] = scale[:n]*answer[:n]
        multiplier = scale[n:]*answer[n:]
        residual = primal@full + constraint.T@multiplier-load
        free_error = float(np.linalg.norm(residual[free]) /
                           max(1., np.linalg.norm(load[free])))
        gap_error = float(np.linalg.norm(constraint@full))
        work_error = float(abs(full@(primal@full)-load@full))
        shell_reactions = residual[:shell_size].reshape(-1, 6)
        beam_reactions = residual[shell_size:shell_size+beam.context.nodal_count].reshape(-1, 6)
        shell_force = shell_reactions.sum(axis=0)[:3]
        beam_force = beam_reactions.sum(axis=0)[:3]
        support_force = shell_force+beam_force
        shell_nodes = reference_nodes(panel)
        beam_nodes = np.array([(i/beam.n_half_cells, 0., .085)
                               for i in range(beam.n_half_cells+1)])
        shell_moment = (np.cross(shell_nodes,shell_reactions[:,:3]).sum(axis=0)+
                        shell_reactions[:,3:].sum(axis=0))
        beam_moment = (np.cross(beam_nodes,beam_reactions[:,:3]).sum(axis=0)+
                       beam_reactions[:,3:].sum(axis=0))
        support_moment = shell_moment+beam_moment
        applied_force = load[shell_size+6*beam.n_half_cells:
                             shell_size+6*beam.n_half_cells+3]
        applied_moment = load[shell_size+6*beam.n_half_cells+3:
                              shell_size+6*beam.n_half_cells+6]
        balance_force = float(np.linalg.norm(support_force+applied_force))
        balance_moment = float(np.linalg.norm(support_moment+
            np.cross(center, applied_force)+applied_moment))
        if (max(free_error, gap_error, work_error) > 1e-7 or
                max(balance_force, balance_moment) > 1e-7 or
                not np.isfinite(full).all()):
            raise ArithmeticError("loaded local termination solution failed")
        return {"tip_rx_rad": float(full[shell_size+6*beam.n_half_cells+3]),
                "tip_uz_m": float(full[shell_size+6*beam.n_half_cells+2]),
                "shell_support_wrench_N_Nm":[*shell_force.tolist(),
                                             *shell_moment.tolist()],
                "beam_root_wrench_N_Nm":[*beam_force.tolist(),
                                           *beam_moment.tolist()],
                "scaled_equilibrium_residual": free_error,
                "weak_gap_norm": gap_error,
                "work_error_j": work_error,
                "global_force_balance_n": balance_force,
                "global_moment_balance_nm": balance_moment}

    loaded_results = {
        family: {"torque_mx_100nm": loaded(constraint, 3),
                 "shear_fz_1000n": loaded(constraint, 2)}
        for family, constraint in (("distributing", distributing),
                                   ("rigid", rigid))}
    return {"patch_x_m": [.9, 1.], "beam_tip_x_m": 1.,
            "rows_and_supported_ranks": {"distributing": [6, ranks[0]],
                                         "rigid": [12, ranks[1]]},
            "reference_gap_max": max(
                rigid_reference_gap,
                float(np.max(np.abs(evaluation.constraints)))),
            "shell_my_nm": {"distributing": moments[0], "rigid": moments[1]},
            "loaded_linear_reference": loaded_results,
            "scope": "bounded linearized tip-patch dense oracle; no nonlinear termination qualification"}


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
        "finite_rigid_chart": finite_rigid_work(
            shell, beam, port, points, rigid_moment),
        "finite_distributing_chart": finite_distributing_work(
            shell, beam, port),
        "tip_termination_local": termination_local(shell, beam),
        "scope": "local patch work and bounded linearized tip KKT; rigid patch intentionally restrains local shear; not a true-line or production result",
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
        "question": "Do distinct finite-width laws remain consistent and give distinguishable, balanced linearized responses for the same last-0.1 m beam-tip patch?",
        "decision": "Failure of reference, rank, equilibrium, work or global balance requires map/assembly revision. Passing bounded loaded responses keeps both declared idealizations for physical-reference and nonlinear checks; it does not select a true-line multiplier space.",
        "python": platform.python_version(), "numpy": np.__version__,
        "threads": 1, "models": ["Q4", "S3-V2D"],
        "geometry": "plate [-.5,1.5]x[-.5,.5] z=0 thickness .07 m; center patch x=.5±.05 and terminal patch x=[.9,1.0], y±.05; B3 axis z=.085 m, x=[0,1]",
        "section": "square-bar Saint-Venant J; other native generalized resultants unchanged",
        "support": "full shell left edge and native B3 root fixed",
        "loads": "separate +100 Nm native tip Mx and +1000 N native tip Fz for the bounded terminal KKT",
        "scope": "local work and dense linearized terminal KKT; no nonlinear, convergence, physical-accuracy, production-footprint or true-line qualification",
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


def run_terminal_beam_resolution(output_dir: Path) -> None:
    """One-axis native beam check with the E4 panel and footprint fixed."""
    source = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"],
                               text=True).strip():
        raise RuntimeError("run requires clean source")
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "status": "EXPLORATORY_NOT_G0_ACCEPTANCE",
        "source_sha": source,
        "question": "Does native B3 half-cell resolution cause the rigid/distributing terminal response difference on one fixed E4 Q4 panel?",
        "decision": "Material drift with beam 4->8->16 requires beam/port convergence work before comparing footprint laws; roundoff agreement shifts the remaining discrepancy to shell or connection idealization. Neither selects a production law.",
        "panel": "Q4 x4/y4, t=.07 m; full left-edge clamp",
        "beam": "native B3 half-cells 4/8/16, centroid z=.085 m, square Saint-Venant J; root fixed",
        "footprint": "last 0.1 m, y +/-0.05 m; same rigid and distributing laws",
        "loads": "separate +100 Nm tip Mx and +1000 N tip Fz",
        "python": platform.python_version(), "numpy": np.__version__,
        "scope": "bounded linearized fixed-panel check; no external accuracy, mesh convergence or nonlinear qualification",
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        (output_dir/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
        shell = FlatE4TrialPanel(make_shell(4, "Q4", n_y=4))
        records=[]
        for half in (4, 8, 16):
            beam = build(half, z_offset=.085,
                         torsion_constant=square_torsion_constant())
            result=termination_local(shell, beam)
            records.append({"beam_half_cells":half, "response":result})
            print(half, json.dumps(result["loaded_linear_reference"]), flush=True)
        (output_dir/"results.json").write_text(json.dumps(records, indent=2,
                                             allow_nan=False)+"\n")


def run_terminal_shell_resolution(output_dir: Path) -> None:
    """Bounded native terminal-law response under simultaneous shell refinement."""
    source = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"],
                               text=True).strip():
        raise RuntimeError("run requires clean source")
    output_dir.mkdir(parents=True, exist_ok=False)
    levels=(2,4,8)
    manifest={
        "status":"EXPLORATORY_NOT_G0_ACCEPTANCE",
        "source_sha":source,
        "question":"Do native six-channel rigid/distributing terminal responses and plate/beam support-wrench partitions approach the section-resolved external terminal reference as the E4 shell refines?",
        "decision":"A strong native mesh trend bars a law ranking until convergence. A stable response discrepancy with different support partition points to connection transfer; a similar partition points to section, warping or shell stiffness. Neither outcome selects a footprint or true-line multiplier space.",
        "shell_formulations":["Q4","S3-V2D"],
        "shell_levels_x_half_y":list(levels),
        "beam_half_cells":8,
        "geometry":"plate [-.5,1.5]x[-.5,.5] m, thickness .07 m; B3 straight x=[0,1] m, centroid z=.085 m; patch x=[.9,1], y=+/- .05 m",
        "supports":"full E4 left edge and B3 root fixed",
        "loads":"separate +100 N m tip Mx and +1000 N tip Fz",
        "external_context":"C3D20R solid terminal patch has a declared 2 micrometre clearance outside the patch; native straight beam does not",
        "limits":{"max_dense_kkt_rows":2300,"blas_threads":1},
        "scope":"linearized dense G0 native response screen; no production assembly, nonlinear qualification, exact solid geometry parity or true-line selection",
        "python":platform.python_version(),"numpy":np.__version__,
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"]=threadpool_info()
        (output_dir/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        beam=build(8,z_offset=.085,torsion_constant=square_torsion_constant())
        records=[]
        for topology in manifest["shell_formulations"]:
            for level in levels:
                started=time.perf_counter()
                shell=FlatE4TrialPanel(make_shell(level,topology,n_y=level))
                rows=6*shell.panel.node_count+beam.context.count+12
                if rows>manifest["limits"]["max_dense_kkt_rows"]:
                    raise ValueError("terminal shell-resolution dense row cap exceeded")
                result=termination_local(shell,beam)
                record={"topology":topology,"shell_level":level,
                        "shell_nodes":shell.panel.node_count,
                        "dense_kkt_rows_bound":rows,
                        "seconds":time.perf_counter()-started,
                        "response":result}
                records.append(record)
                (output_dir/"results.json").write_text(json.dumps(
                    records,indent=2,allow_nan=False)+"\n")
                print(topology,level,json.dumps(result["loaded_linear_reference"]),
                      flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--terminal-beam-resolution", action="store_true")
    parser.add_argument("--terminal-shell-resolution", action="store_true")
    args = parser.parse_args()
    if args.terminal_beam_resolution and args.terminal_shell_resolution:
        parser.error("select one terminal resolution screen")
    if args.terminal_beam_resolution:
        run_terminal_beam_resolution(args.output_dir)
    elif args.terminal_shell_resolution:
        run_terminal_shell_resolution(args.output_dir)
    else:
        run(args.output_dir)
