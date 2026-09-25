"""Bounded G0B screen of an exact six-resultant physical-surface line.

This is a new *candidate*, not a selected mortar space. Each P0 interval
enforces mean top-surface/bottom-beam position and its first spatial moment
with exact multipliers. The Q4 plate, retained native B3 chain, supports and
loads stay fixed while interval resolution changes. The positive-compliance
mode uses a declared H^(-1/2) force-density norm; it is not a continuum
inf-sup constant or an external accuracy comparison.
"""

from __future__ import annotations

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_p0_dual_norm import p0_dual_gram
from scripts.b3_e4_f03_local_footprint_work import distributed_surface_patch_trace
from scripts.b3_e4_f03_plate_patch_work import raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def bounded_surface_line_screen(*, shell_x: int = 8, shell_y: int = 8,
                                beam_half_cells: int = 8,
                                intervals: tuple[int, ...] = (2, 4, 8)
                                ) -> list[dict]:
    """Solve identical torque/shear loads for several exact line row counts."""
    if (shell_x not in (8, 16) or shell_y not in (8, 16) or
            beam_half_cells not in (4, 8, 16) or
            not intervals or any(n not in (2, 4, 8) for n in intervals)):
        raise ValueError("bounded shell, beam and line resolutions required")
    xs = np.linspace(-.5, 1.5, shell_x+1)
    ys = np.linspace(-.5, .5, shell_y+1)
    shell_k, shell_physical = raw_e4_tangent(xs, ys, thickness=.035)
    beam = build(beam_half_cells, z_offset=.0675,
                 torsion_constant=square_torsion_constant())
    beam_k = beam.tangent.toarray()
    shell_size = shell_k.shape[0]
    total = shell_size+beam.context.count
    if total > 1900:
        raise ValueError("dense G0 reference oracle exceeds 1900 primal rows")
    primal = linalg.block_diag(shell_k, beam_k)
    fixed_shell = {6*j*(shell_x+1)+axis for j in range(shell_y+1)
                   for axis in range(6)}
    fixed_beam = {shell_size+i for i in beam.context.fixed}
    free = np.array([i for i in range(total)
                     if i not in fixed_shell and i not in fixed_beam])
    factor = linalg.lu_factor(primal[np.ix_(free, free)])
    tip = shell_size+6*beam_half_cells
    loads = {"torque_mx_100nm": (tip+3, 100.),
             "shear_fz_1000n": (tip+2, 1000.)}
    shell_nodes = np.array([(x, y, 0.) for y in ys for x in xs])
    beam_root = np.array((0., 0., .0675))
    results = []
    action_scales = np.array((1000., 1000., 1000., 100., 100., 100.))
    for n in intervals:
        parts = [distributed_surface_patch_trace(
            xs, ys, beam, plate_thickness=.035,
            x_interval=(k/n, (k+1)/n)) for k in range(n)]
        rows = np.vstack([part[0] for part in parts])
        reference_gap = max(part[1]["reference_gap_m"] for part in parts)
        constrained = rows[:, free]
        rank = int(np.linalg.matrix_rank(constrained))
        if reference_gap > 1e-11:
            raise ArithmeticError("exact surface-line reference gap changed")
        if rank != 6*n:
            left, singular, _ = np.linalg.svd(constrained, full_matrices=False)
            null = left[:, rank:]
            results.append({
                "status": "RANK_DEFICIENT_NO_SOLVE",
                "shell_elements_xy": [shell_x, shell_y],
                "beam_half_cells": beam_half_cells,
                "line_intervals": n,
                "primal_rows": total,
                "constraint_rank": rank,
                "constraint_rows": 6*n,
                "max_reference_gap_m": reference_gap,
                "smallest_singular_value_raw_mixed_units": float(singular[-1]),
                "null_projector_channel_weights_raw_mixed_units": (
                    np.sum(null.reshape(n, 6, -1)**2, axis=(0, 2))).tolist(),
                "interpretation": "exact row dependence; no KKT solve or physical stability claim",
            })
            continue
        inverse_rows = linalg.lu_solve(factor, constrained.T)
        compliance = constrained@inverse_rows
        skew = float(np.linalg.norm(compliance-compliance.T)/max(
            np.linalg.norm(compliance), 1e-30))
        if skew > 1e-8:
            raise ArithmeticError("reference line compliance is nonsymmetric")

        # Each multiplier is a cell resultant. Divide by its cell length to
        # recover the physical line-density coefficients for the dual norm.
        lower, upper = p0_dual_gram(n, 1., 2048)
        dual = np.zeros((6*n, 6*n))
        density_gram = lower*n*n
        for channel in range(6):
            indices = np.arange(channel, 6*n, 6)
            dual[np.ix_(indices, indices)] = (
                density_gram/action_scales[channel]**2)
        eigenvalues, eigenvectors = linalg.eigh(compliance, dual)
        if eigenvalues[0] <= 0.:
            raise ArithmeticError("nonpositive physical line-compliance mode")
        weak = eigenvectors[:, 0]
        channel_fractions = []
        for channel in range(6):
            values = weak[channel::6]*n/action_scales[channel]
            channel_fractions.append(float(values@lower@values))
        weak_response = inverse_rows@weak
        shell_mode = np.zeros(shell_size)
        shell_mode[free[free<shell_size]] = weak_response[free<shell_size]
        physical_shell_action = float(shell_mode@shell_physical@shell_mode)
        shell_action = float(shell_mode@shell_k@shell_mode)
        beam_mode = weak_response[free>=shell_size]
        beam_free = free[free>=shell_size]-shell_size
        beam_action = float(beam_mode@beam_k[np.ix_(beam_free, beam_free)]@beam_mode)

        loaded = {}
        for name, (dof, amplitude) in loads.items():
            force = np.zeros(total)
            force[dof] = amplitude
            free_unconstrained = linalg.lu_solve(factor, force[free])
            multiplier = linalg.solve(
                compliance, constrained@free_unconstrained,
                assume_a="gen")
            displacement_free = free_unconstrained-inverse_rows@multiplier
            displacement = np.zeros(total)
            displacement[free] = displacement_free
            residual = primal@displacement+rows.T@multiplier-force
            equilibrium = float(np.linalg.norm(residual[free])/max(amplitude, 1.))
            gap = rows@displacement
            work = float(force@displacement)
            stiffness_work = float(displacement@primal@displacement)
            shell_work = float(displacement[:shell_size]@shell_k@displacement[:shell_size])
            physical_shell_work = float(
                displacement[:shell_size]@shell_physical@displacement[:shell_size])
            shell_reactions = residual[:shell_size].reshape(-1, 6)
            root_reaction = residual[shell_size:shell_size+6]
            support_force = shell_reactions[:, :3].sum(axis=0)+root_reaction[:3]
            support_moment = (
                (np.cross(shell_nodes, shell_reactions[:, :3])+
                 shell_reactions[:, 3:]).sum(axis=0)+
                np.cross(beam_root, root_reaction[:3])+root_reaction[3:])
            tip_position = np.array((1., 0., .0675))
            external_force = np.zeros(3)
            external_moment = np.zeros(3)
            if name.startswith("torque"):
                external_moment[0] = amplitude
            else:
                external_force[2] = amplitude
                external_moment = np.cross(tip_position, external_force)
            balance = max(float(np.linalg.norm(support_force+external_force)),
                          float(np.linalg.norm(support_moment+external_moment)))
            if (equilibrium > 1e-8 or np.max(np.abs(gap)) > 1e-8 or
                    abs(work-stiffness_work) > 1e-7 or
                    work <= 0. or physical_shell_work <= 0. or
                    balance > 1e-6):
                raise ArithmeticError(f"exact surface-line mechanics failed: {n}, {name}")
            loaded[name] = {
                "tip_rx_rad": float(displacement[tip+3]),
                "tip_uz_m": float(displacement[tip+2]),
                "shell_support_fz_n": float(shell_reactions[:, 2].sum()),
                "shell_support_mx_nm": float((
                    shell_reactions[:, 3]+shell_nodes[:, 1]*shell_reactions[:, 2]
                    -shell_nodes[:, 2]*shell_reactions[:, 1]).sum()),
                "total_external_work_j": work,
                "physical_shell_work_j": physical_shell_work,
                "numerical_shell_work_j": shell_work-physical_shell_work,
                "scaled_equilibrium_error": equilibrium,
                "max_weak_gap_m_rad": float(np.max(np.abs(gap))),
                "global_balance_n_nm": balance,
            }
        results.append({
            "status": "SOLVED_BOUNDED_DIAGNOSTIC",
            "shell_elements_xy": [shell_x, shell_y],
            "beam_half_cells": beam_half_cells,
            "line_intervals": n,
            "primal_rows": total,
            "constraint_rank": rank,
            "max_reference_gap_m": reference_gap,
            "action_scales_n_nm": action_scales.tolist(),
            "h_minus_half_gram_relative_tail": float(
                np.linalg.norm(upper-lower)/np.linalg.norm(lower)),
            "finite_physical_mode_action_j": float(eigenvalues[0]),
            "weakest_mode_channel_norm_fractions": channel_fractions,
            "weakest_mode_shell_physical_action_j": physical_shell_action,
            "weakest_mode_shell_numerical_action_j": shell_action-physical_shell_action,
            "weakest_mode_beam_action_j": beam_action,
            "compliance_relative_skew": skew,
            "loaded": loaded,
            "interpretation": "fixed-mesh exact P0 surface-resultant line screen; not inf-sup or external qualification",
        })
    return results
