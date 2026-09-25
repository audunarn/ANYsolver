"""Unregistered small-system F03 multiplier-resolution diagnostic.

This reuses the bounded native B3/E4 reference KKT oracle. It compares
multiplier spaces on identical physical meshes; its pointwise gaps and
linearized responses are descriptive, not a stability or accuracy gate.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
from scipy import linalg

from anysolver._ge_beam3_pose_joint import RigidPoseJoint

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts._b3_e4_f03_shell_finite_pose_candidate import (
    pose_from_e4_total, reference_nodes)
from scripts._b3_e4_f03_shell_local_translation_candidate import (
    pose_from_e4_total_local_translation,
    pose_from_e4_total_local_director,
    pose_from_e4_total_local_frame)
from scripts._b3_e4_f03_shell_strip_pose_candidate import pose_from_e4_total_strip
from scripts._b3_e4_f03_shell_chord_pose_candidate import pose_from_e4_total_chord
from scripts._b3_e4_f03_shell_spatial_linear_port import physical_shell_stiffness
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_reference_kkt)


def sinusoidal_axial_density_load(beam, *, amplitude_n_per_m=1e5):
    """Integrate one fixed physical line density through native station work."""
    if (isinstance(amplitude_n_per_m, (bool, str)) or
            not isinstance(amplitude_n_per_m,
                           (int, float, np.integer, np.floating)) or
            not np.isfinite(amplitude_n_per_m) or
            amplitude_n_per_m <= 0.):
        raise ValueError("positive finite axial line-load amplitude required")
    points, weights = np.polynomial.legendre.leggauss(8)
    load = np.zeros(beam.context.count)
    for half_cell in range(beam.n_half_cells):
        left = half_cell/beam.n_half_cells
        right = (half_cell+1)/beam.n_half_cells
        for point, weight in zip(points, weights):
            station = (left+right)/2+(right-left)*point/2
            element, cell, fraction, _ = beam._locate(float(station))
            port = NativeHalfCellSpatialPort(
                beam.context, element, cell, fraction)
            wrench = np.array((amplitude_n_per_m*np.sin(2*np.pi*station),
                               0., 0., 0., 0., 0.))
            load += (right-left)*weight/2*port.pullback(
                beam.context.initial.mechanical, wrench)
    return load


def one_case(topology: str, intervals: int, kind: str, *,
             shell_port: str = "rail",
             load_kind: str = "torsion", n_s: int = 4,
             native_half_cells: int = 16,
             n_y: int = 2,
             thickness: float = .07,
             shell_support_policy: str = "legacy_three_left_nodes") -> dict:
    """Solve one bounded six-channel load at fixed reference resolution."""
    shell = FlatE4TrialPanel(make_shell(n_s, topology, n_y=n_y,
                                       thickness=thickness))
    beam = build(native_half_cells)
    space = LineMultiplierSpace(
        kind, tuple(np.linspace(0., 1., intervals+1)))
    kkt = assemble_reference_kkt(
        shell, beam, space, shell_port=shell_port,
        shell_support_policy=shell_support_policy)
    pose_map = {"rail": pose_from_e4_total,
                "local_translation": pose_from_e4_total_local_translation,
                "local_director": pose_from_e4_total_local_director,
                "local_frame": pose_from_e4_total_local_frame,
                "physical_strip_020_023": lambda p, s, u: (
                    pose_from_e4_total_strip(
                        p, s, u, half_length=.2, half_width=.23)),
                "line_chord_020": pose_from_e4_total_chord}[shell_port]
    shell_size = 6*shell.panel.node_count
    tip_rx = shell_size+6*beam.n_half_cells+3
    tip_rz = shell_size+6*beam.n_half_cells+5
    tip_uz = shell_size+6*beam.n_half_cells+2
    load = np.zeros(shell_size+beam.context.count)
    if load_kind == "torsion":
        load[tip_rx] = 100.
    elif load_kind == "yaw_torque_z":
        load[tip_rz] = 100.
    elif load_kind == "shell_force_couple_x":
        sample = shell.panel.sample_weights(1.)
        y = np.array([-.23, -.23, .23, .23])
        load[:shell_size].reshape(-1, 6)[:, 2] += (
            100.*(y/(y@y))@sample)
    elif load_kind == "transverse_force_z":
        load[tip_uz] = 1000.
    elif load_kind == "axial_wave":
        positions = (beam.context.initial.mechanical.positions+
                     beam.context.initial.mechanical.position_low)
        axial = 1e5*np.sin(8*np.pi*positions[:, 0])
        axial[np.abs(axial) < 1e-8] = 0.
        load[shell_size:shell_size+beam.context.nodal_count:6] = axial
    elif load_kind == "sinusoidal_axial_density":
        load[shell_size:] = sinusoidal_axial_density_load(beam)
    else:
        raise ValueError("unknown bounded line load kind")
    free_count = len(kkt.free_primal)
    rhs = np.r_[load[kkt.free_primal]*
                kkt.coordinate_scale[:free_count]/kkt.energy_scale,
                np.zeros(6*space.count)]
    scaled_solution = np.linalg.solve(kkt.scaled_system, rhs)
    scaled_residual = kkt.scaled_system@scaled_solution-rhs
    physical_solution = kkt.coordinate_scale*scaled_solution
    full = np.zeros(len(load))
    full[kkt.free_primal] = physical_solution[:free_count]
    multipliers = physical_solution[free_count:]
    physical_residual = (kkt.primal_tangent@full+
                         kkt.constraint_jacobian.T@multipliers-load)
    shell_fixed = np.ones(shell_size, dtype=bool)
    shell_fixed[kkt.free_primal[kkt.free_primal < shell_size]] = False
    shell_reaction_fx = float(np.sum(
        physical_residual[:shell_size:6][shell_fixed[0::6]]))
    beam_root_reaction_fx = float(physical_residual[shell_size])
    shell_support = physical_residual[:shell_size].copy()
    shell_support[~shell_fixed] = 0.
    shell_support = shell_support.reshape(-1, 6)
    shell_reference_nodes = reference_nodes(shell.panel)
    shell_interface = (kkt.constraint_jacobian[:, :shell_size].T@
                       multipliers).reshape(-1, 6)
    shell_interface_torque_x = float(np.sum(
        shell_interface[:, 3]+shell_reference_nodes[:, 1]*shell_interface[:, 2]
        -shell_reference_nodes[:, 2]*shell_interface[:, 1]))
    shell_interface_force_z = float(np.sum(shell_interface[:, 2]))
    shell_interface_mz = float(np.sum(
        shell_interface[:, 5]+shell_reference_nodes[:, 0]*shell_interface[:, 1]
        -shell_reference_nodes[:, 1]*shell_interface[:, 0]))
    shell_reaction_mx = float(np.sum(
        shell_support[:, 3]+shell_reference_nodes[:, 1]*shell_support[:, 2]
        -shell_reference_nodes[:, 2]*shell_support[:, 1]))
    shell_reaction_fz = float(np.sum(shell_support[:, 2]))
    shell_reaction_my = float(np.sum(
        shell_support[:, 4]+shell_reference_nodes[:, 2]*shell_support[:, 0]
        -shell_reference_nodes[:, 0]*shell_support[:, 2]))
    shell_reaction_mz = float(np.sum(
        shell_support[:, 5]+shell_reference_nodes[:, 0]*shell_support[:, 1]
        -shell_reference_nodes[:, 1]*shell_support[:, 0]))
    beam_root_reaction_mx = float(physical_residual[shell_size+3])
    beam_root_reaction_fz = float(physical_residual[shell_size+2])
    beam_root_reaction_my = float(physical_residual[shell_size+4])
    beam_root_reaction_mz = float(physical_residual[shell_size+5])
    shell_load = load[:shell_size].reshape(-1, 6)
    applied_torque_x = float(load[tip_rx]+np.sum(
        shell_load[:, 3]+shell_reference_nodes[:, 1]*shell_load[:, 2]
        -shell_reference_nodes[:, 2]*shell_load[:, 1]))
    applied_force_z = float(load[tip_uz]+np.sum(shell_load[:, 2]))
    applied_moment_y = float(-load[tip_uz]+np.sum(
        shell_load[:, 4]+shell_reference_nodes[:, 2]*shell_load[:, 0]
        -shell_reference_nodes[:, 0]*shell_load[:, 2]))
    applied_moment_z = float(load[tip_rz]+np.sum(
        shell_load[:, 5]+shell_reference_nodes[:, 0]*shell_load[:, 1]
        -shell_reference_nodes[:, 1]*shell_load[:, 0]))
    shell_total = full[:shell_size]
    sample_z = shell.panel.sample_weights(1.)@shell_total.reshape(-1, 6)[:, 2]
    sample_y = np.array([-.23, -.23, .23, .23])
    shell_tip_z_slope = float(sample_y@sample_z/(sample_y@sample_y))
    shell_inplane = shell_total.reshape(-1, 6)[:, :2].ravel()
    shell_physical_inplane_energy = float(
        .5*shell_inplane@(shell.panel.stiffness@ shell_inplane))
    shell_full_energy = float(.5*shell_total@kkt.primal_tangent[
        :shell_size, :shell_size]@shell_total)
    shell_physical_energy = float(
        .5*shell_total@(physical_shell_stiffness(shell.panel)@shell_total))
    shell_component_physical_energy = 0.
    shell_numerical_energy = 0.
    for _, nodes, element in shell.elements:
        components = element.compute_stiffness_components(
            shell.model.mesh, shell.model.get_material("steel"))
        local = shell_total.reshape(-1, 6)[np.asarray(nodes)-1].ravel()
        shell_component_physical_energy += float(
            .5*local@components["physical"]@local)
        shell_numerical_energy += float(
            .5*local@components["numerical"]@local)
    beam_energy = float(.5*full[shell_size:]@
                        kkt.primal_tangent[shell_size:, shell_size:]@
                        full[shell_size:])
    beam_state = beam.context.advance(
        beam.context.initial.mechanical, full[shell_size:])
    shell_reference = np.zeros(shell_size)
    gap_norms = []
    axial_gaps = []
    for station in np.linspace(0., 1., 129):
        element, cell, fraction, _ = beam._locate(float(station))
        port = NativeHalfCellSpatialPort(
            beam.context, element, cell, fraction)
        shell_ref_position, shell_ref_frame = pose_map(
            shell.panel, float(station), shell_reference)
        beam_ref_high, beam_ref_low, beam_ref_frame = port.pose_pair(
            beam.context.initial.mechanical)
        joint = RigidPoseJoint(
            np.array((shell_ref_position, beam_ref_high+beam_ref_low)),
            np.array((shell_ref_frame, beam_ref_frame)))
        shell_position, shell_frame = pose_map(
            shell.panel, float(station), shell_total)
        beam_high, beam_low, beam_frame = port.pose_pair(beam_state)
        gap = joint.evaluate(
            np.array((shell_position, beam_high)),
            np.array((shell_frame, beam_frame)), np.zeros(6),
            position_low=np.array((np.zeros(3), beam_low))).constraints
        gap_norms.append(float(np.linalg.norm(np.r_[gap[:3], gap[3:]*1.])))
        axial_gaps.append(float(gap[0]))
    gaps = np.asarray(gap_norms)
    axial_gap = np.asarray(axial_gaps)
    beam_nodal = full[
        shell_size:shell_size+beam.context.nodal_count].reshape(-1, 6)
    return {
        "topology": topology,
        "kind": kind,
        "shell_port": shell_port,
        "shell_support_policy": shell_support_policy,
        "load_kind": load_kind,
        "intervals": intervals,
        "shell_host_intervals": n_s,
        "shell_transverse_intervals": n_y,
        "shell_thickness_m": shell.panel.thickness,
        "native_half_cells": native_half_cells,
        "shell_elements": shell.panel.element_count,
        "native_elements": beam.n_half_cells//2,
        "tip_rx_rad": float(full[tip_rx]),
        "tip_rz_rad": float(full[tip_rz]),
        "shell_tip_z_antisymmetric_slope_rad": shell_tip_z_slope,
        "beam_tip_uz_m": float(full[tip_uz]),
        "beam_tip_ux_m": float(beam_nodal[-1, 0]),
        "beam_max_abs_ux_m": float(np.max(np.abs(beam_nodal[:, 0]))),
        "shell_max_abs_ux_m": float(np.max(np.abs(
            full[:shell_size].reshape(-1, 6)[:, 0]))),
        "applied_axial_force_n": float(np.sum(
            load[shell_size:shell_size+beam.context.nodal_count:6])),
        "applied_axial_first_moment_n_m": float(np.dot(
            np.arange(native_half_cells+1)/native_half_cells,
            load[shell_size:shell_size+beam.context.nodal_count:6])),
        "shell_energy_j": shell_full_energy,
        "shell_physical_energy_j": shell_physical_energy,
        "shell_component_physical_energy_j": shell_component_physical_energy,
        "shell_numerical_energy_j": shell_numerical_energy,
        "shell_component_closure_error_j": float(
            shell_full_energy-shell_component_physical_energy-
            shell_numerical_energy),
        "shell_numerical_energy_fraction": (
            shell_numerical_energy/shell_full_energy
            if shell_full_energy != 0. else None),
        "shell_physical_inplane_energy_j": shell_physical_inplane_energy,
        "shell_full_minus_physical_inplane_energy_j": float(
            shell_full_energy-shell_physical_inplane_energy),
        "beam_energy_j": beam_energy,
        "global_work_error_j": float(
            2*(shell_full_energy+beam_energy)-full@load),
        "shell_reaction_fx_n": shell_reaction_fx,
        "beam_root_reaction_fx_n": beam_root_reaction_fx,
        "global_axial_balance_n": float(
            shell_reaction_fx+beam_root_reaction_fx+
            np.sum(load[shell_size:shell_size+beam.context.nodal_count:6])),
        "applied_torque_x_n_m": applied_torque_x,
        "shell_support_reaction_torque_x_n_m": shell_reaction_mx,
        "shell_interface_torque_x_n_m": shell_interface_torque_x,
        "shell_support_minus_interface_torque_x_n_m": float(
            shell_reaction_mx-shell_interface_torque_x),
        "beam_root_reaction_torque_x_n_m": beam_root_reaction_mx,
        "global_torque_x_balance_n_m": float(
            shell_reaction_mx+beam_root_reaction_mx+applied_torque_x),
        "applied_force_z_n": applied_force_z,
        "shell_support_reaction_fz_n": shell_reaction_fz,
        "shell_interface_fz_n": shell_interface_force_z,
        "shell_support_minus_interface_fz_n": float(
            shell_reaction_fz-shell_interface_force_z),
        "beam_root_reaction_fz_n": beam_root_reaction_fz,
        "global_force_z_balance_n": float(
            shell_reaction_fz+beam_root_reaction_fz+applied_force_z),
        "applied_moment_y_about_origin_n_m": applied_moment_y,
        "shell_support_reaction_my_about_origin_n_m": shell_reaction_my,
        "beam_root_reaction_my_about_origin_n_m": beam_root_reaction_my,
        "global_moment_y_balance_n_m": float(
            shell_reaction_my+beam_root_reaction_my+applied_moment_y),
        "applied_moment_z_about_origin_n_m": applied_moment_z,
        "shell_support_reaction_mz_about_origin_n_m": shell_reaction_mz,
        "shell_interface_mz_about_origin_n_m": shell_interface_mz,
        "beam_root_reaction_mz_about_origin_n_m": beam_root_reaction_mz,
        "global_moment_z_balance_n_m": float(
            shell_reaction_mz+beam_root_reaction_mz+applied_moment_z),
        "gap_l2_m": float(np.sqrt(np.trapezoid(gaps*gaps, dx=1./128))),
        "gap_max_m": float(np.max(gaps)),
        "gap_axial_l2_m": float(np.sqrt(np.trapezoid(
            axial_gap*axial_gap, dx=1./128))),
        "gap_axial_max_m": float(np.max(np.abs(axial_gap))),
        "scaled_equilibrium_residual": float(np.linalg.norm(scaled_residual)),
        "free_primal_residual_mixed_l2": float(np.linalg.norm(
            physical_residual[kkt.free_primal])),
    }


def chord_reference_modes(topology: str, intervals: int, kind: str, *,
                          n_s: int = 4, n_y: int = 4,
                          native_half_cells: int = 8,
                          characteristic_length: float = .46) -> dict:
    """Bounded six-channel, work-scaled line-chord interface diagnostic.

    Exact elimination of the indefinite native retained block separates a
    positive physical stiffness from signed local retained work. The norm
    uses physical energy plus the absolute retained quadratic form; it is
    an algorithmic finite-mesh diagnostic, not a physical continuum inf-sup
    proof or multiplier-space selection. E4 numerical completion remains in
    the stiffness and must be assessed separately.
    """
    if not np.isfinite(characteristic_length) or characteristic_length <= 0.:
        raise ValueError("positive physical characteristic length required")
    shell = FlatE4TrialPanel(make_shell(n_s, topology, n_y=n_y))
    beam = build(native_half_cells)
    space = LineMultiplierSpace(
        kind, tuple(np.linspace(0., 1., intervals+1)))
    kkt = assemble_reference_kkt(
        shell, beam, space, shell_port="line_chord_020",
        shell_support_policy="full_left_edge")
    free = kkt.free_primal
    rows = kkt.constraint_jacobian[:, free]
    n = len(free)
    if n+len(rows) > 1200:
        raise ValueError("bounded dense interface diagnostic exceeds 1200 rows")
    n_physical = int(np.count_nonzero(
        free < 6*shell.panel.node_count+beam.context.nodal_count))
    displacement_scale = 1e6/(210e9*.07)
    if not np.isclose(kkt.energy_scale, 1e6*displacement_scale,
                      rtol=1e-14, atol=0.):
        raise ValueError("reference KKT work scale changed")
    scales = kkt.coordinate_scale[:n]
    k = kkt.primal_tangent[np.ix_(free, free)]
    kbar = (scales[:, None]*k)*scales[None, :]/kkt.energy_scale
    if np.linalg.norm(kbar-kbar.T) > 1e-10*np.linalg.norm(kbar):
        raise ValueError("nonsymmetric reference tangent cannot use energy norm")
    kpp = kbar[:n_physical, :n_physical]
    kpr = kbar[:n_physical, n_physical:]
    krp = kbar[n_physical:, :n_physical]
    krr = kbar[n_physical:, n_physical:]
    retained_action = linalg.solve(krr, krp, assume_a="sym")
    physical_k = kpp-kpr@retained_action
    ep, up = linalg.eigh(physical_k)
    er, ur = linalg.eigh(krr)
    if (ep[0] <= 1e-10*ep[-1] or
            np.min(np.abs(er)) <= 1e-12*np.max(np.abs(er))):
        raise ValueError("positive physical/regular retained split unavailable")

    # C integrates each physical gap against a dimensionless line basis.
    # Divide by a fixed translation scale and line length (1 m); convert
    # rotations into lengths with the declared characteristic length.
    row_scale = np.tile(np.r_[np.ones(3),
                              np.full(3, characteristic_length)],
                        space.count)/displacement_scale
    cbar = (row_scale[:, None]*rows)*scales[None, :]
    cp, cr = cbar[:, :n_physical], cbar[:, n_physical:]
    cl = cp-cr@retained_action
    bp = cl@(up/np.sqrt(ep)[None, :])
    br = cr@(ur/np.sqrt(np.abs(er))[None, :])
    signed = bp@bp.T+(br*np.sign(er)[None, :])@br.T
    direct = cbar@linalg.solve(kbar, cbar.T, assume_a="sym")
    decomposition_error = float(np.linalg.norm(signed-direct)/
                                max(np.linalg.norm(direct), 1e-30))
    if decomposition_error > 1e-9:
        raise ArithmeticError("retained interface decomposition inconsistent")

    scalar_mass = np.zeros((space.count, space.count))
    points, weights = np.polynomial.legendre.leggauss(3)
    for left, right in zip(space.knots[:-1], space.knots[1:]):
        half, center = .5*(right-left), .5*(right+left)
        for point, weight in zip(points, weights):
            phi = space.values(float(center+half*point))
            scalar_mass += half*weight*np.outer(phi, phi)
    mass = np.kron(scalar_mass, np.eye(6))
    em, um = linalg.eigh(mass)
    if em[0] <= 1e-12*em[-1]:
        raise ValueError("multiplier L2 Gram is deficient")
    inv_sqrt = (um/np.sqrt(em)[None, :])@um.T
    bpw, brw = inv_sqrt@bp, inv_sqrt@br
    left, singular, _ = linalg.svd(
        np.column_stack((bpw, brw)), full_matrices=False)
    mode = inv_sqrt@left[:, -1]
    mode = mode.reshape(space.count, 6)
    channel_shares = [float(mode[:, axis]@scalar_mass@mode[:, axis])
                      for axis in range(6)]
    physical_share = float(np.linalg.norm(left[:, -1]@bpw)**2/
                           singular[-1]**2)
    if not -1e-10 <= physical_share <= 1.+1e-10:
        raise ArithmeticError("invalid weakest-mode work decomposition")
    physical_share = float(np.clip(physical_share, 0., 1.))
    weighted = np.column_stack((bpw, brw))
    channel_beta = []
    for axis in range(6):
        selected = np.arange(axis, len(rows), 6)
        channel_beta.append(float(linalg.svdvals(weighted[selected, :])[-1]))
    transverse_rows = np.array([6*i+axis for i in range(space.count)
                                for axis in (2, 3, 4)])
    transverse_left, transverse_singular, _ = linalg.svd(
        weighted[transverse_rows, :], full_matrices=False)
    transverse_mode = transverse_left[:, -1]
    transverse_shares = [float(np.linalg.norm(transverse_mode[axis::3])**2)
                         for axis in range(3)]
    transverse_physical = float(np.linalg.norm(
        transverse_mode@bpw[transverse_rows, :])**2/
        transverse_singular[-1]**2)
    if not -1e-10 <= transverse_physical <= 1.+1e-10:
        raise ArithmeticError("invalid transverse work decomposition")
    transverse_physical = float(np.clip(transverse_physical, 0., 1.))
    return {
        "topology": topology, "shell_x_intervals": 2*n_s,
        "shell_y_intervals": n_y,
        "native_half_cells": native_half_cells,
        "line_intervals": intervals, "space": kind,
        "row_count": len(rows),
        "row_rank": int(np.linalg.matrix_rank(rows)),
        "physical_stiffness_min_eigen": float(ep[0]),
        "retained_negative_modes": int(np.count_nonzero(er < 0.)),
        "decomposition_relative_error": decomposition_error,
        "characteristic_length_m": characteristic_length,
        "minimum_algorithmic_beta": float(singular[-1]),
        "weakest_mode_channel_l2_shares": channel_shares,
        "weakest_mode_physical_work_share": physical_share,
        "weakest_mode_retained_work_share": 1.-physical_share,
        "single_channel_beta_fx_fy_fz_mx_my_mz": channel_beta,
        "transverse_fz_mx_my_beta": float(transverse_singular[-1]),
        "transverse_mode_fz_mx_my_l2_shares": transverse_shares,
        "transverse_mode_physical_work_share": transverse_physical,
        "transverse_mode_retained_work_share": 1.-transverse_physical,
        "scope": "finite native six-channel algorithmic norm; not physical inf-sup acceptance",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-translation", action="store_true")
    parser.add_argument("--axial-wave", action="store_true")
    parser.add_argument("--include-dual", action="store_true")
    parser.add_argument("--paired-refinement", action="store_true")
    parser.add_argument("--paired-shell-intervals", type=int,
                        choices=(1, 2, 4, 8), nargs="+")
    parser.add_argument("--shell-transverse-intervals", type=int,
                        choices=(2, 4, 8), default=2)
    parser.add_argument("--kind", choices=("piecewise_constant",
                                           "continuous_linear", "dual_linear"))
    parser.add_argument("--shell-support-policy",
                        choices=("legacy_three_left_nodes", "full_left_edge",
                                 "both_xy_edges"),
                        default="legacy_three_left_nodes")
    parser.add_argument("--sinusoidal-axial-density", action="store_true")
    parser.add_argument("--transverse-force-z", action="store_true")
    arguments = parser.parse_args()
    if sum((arguments.axial_wave, arguments.sinusoidal_axial_density,
            arguments.transverse_force_z)) > 1:
        parser.error("select only one diagnostic load")
    if arguments.paired_shell_intervals and not arguments.paired_refinement:
        parser.error("paired shell intervals require paired refinement")
    shell_port = ("local_translation" if arguments.local_translation
                  else "rail")
    load_kind = ("transverse_force_z" if arguments.transverse_force_z else
                 "sinusoidal_axial_density" if arguments.sinusoidal_axial_density
                 else "axial_wave" if arguments.axial_wave else "torsion")
    kinds = ("piecewise_constant", "continuous_linear")
    if arguments.include_dual:
        kinds += ("dual_linear",)
    if arguments.kind is not None:
        kinds = (arguments.kind,)
    paired_sizes = arguments.paired_shell_intervals or (1, 2, 4)
    grids = ((n_s, 4*n_s, n_s) for n_s in paired_sizes) if (
        arguments.paired_refinement) else ((4, 16, intervals)
                                          for intervals in (2, 4, 8))
    grids = tuple(grids)
    rows = [one_case(topology, intervals, kind, shell_port=shell_port,
                     load_kind=load_kind, n_s=n_s,
                     native_half_cells=native_half_cells,
                     n_y=arguments.shell_transverse_intervals,
                     shell_support_policy=arguments.shell_support_policy)
            for topology in ("Q4", "S3-V2D")
            for kind in kinds
            for n_s, native_half_cells, intervals in grids]
    print(json.dumps({"status": "UNREGISTERED_DIAGNOSTIC",
                      "screen": "paired_refinement" if arguments.paired_refinement
                      else "fixed_primal",
                      "shell_transverse_intervals": arguments.shell_transverse_intervals,
                      "shell_support_policy": arguments.shell_support_policy,
                      "shell_port": shell_port, "load_kind": load_kind,
                      "cases": rows},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
