"""One supported virgin E4/native-B3 p-only reduction check for L1 development.

This is a finite, unregistered algebra check, not an F03 assessment. The shell
is a flat Q4 strip with a fixed x=0 edge. Its top-surface trace along the
y=0 material centerline at x=.75,.875,1
is paired with two actual straight native B3 half-cells. The native root is
fixed. Only generalized resultants are stationary variables; retained cell
rotations remain physical. The actual E4 PL tangent includes its existing
drill completion, so this finite supported matrix has no asserted drill gauge
and no artificial stiffness is added here.
"""

from __future__ import annotations

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_l1_native_connection_probe import (
    SegmentedL1WeakWork, shell_trace,
)
from scripts.b3_e4_f03_plate_patch_work import raw_e4_tangent


def evaluate() -> dict[str, float | int | bool | None]:
    """Check the actual supported Hessian and all 18 L1 nodal dual actions."""
    xs = np.array((0., .25, .5, .75, .875, 1.))
    ys = np.array((-.1, 0., .1))
    cuts = xs[-3:].copy()
    shell, shell_physical = raw_e4_tangent(xs, ys, thickness=.035)
    beam = build(8, z_offset=.0675)
    state = beam.context.initial.mechanical
    ns, nb = shell.shape[0], beam.context.count
    if not np.array_equal(beam.abscissae[-3:], cuts):
        raise AssertionError("native half-cell and E4 material cuts differ")

    reference = np.column_stack((cuts, np.zeros(3), np.zeros(3)))
    def port_at(station: float) -> NativeHalfCellSpatialPort:
        element, cell, weight, _ = beam._locate(station)
        return NativeHalfCellSpatialPort(beam.context, element, cell, weight)

    line = SegmentedL1WeakWork.at_reference(
        reference, np.zeros((3, 6)), .035, cuts, port_at, state)
    for i, connection in enumerate(line.connections):
        segment = i // 2
        shell_point, shell_frame, _, _ = shell_trace(
            reference[segment:segment+2], np.zeros((2, 6)), .035,
            station=connection.station)
        high, low, beam_frame = connection.port.pose_pair(state)
        beam_point = high+low+beam_frame@np.asarray(connection.beam_offset)
        if (np.max(np.abs(shell_point-beam_point)) > 1e-14 or
                np.max(np.abs(shell_frame-beam_frame)) > 1e-14):
            raise AssertionError("L1 reference poses do not correspond")
        expected = beam._locate(line.stations[i])
        port = connection.port
        if ((port.element_index, port.cell) != expected[:2] or
                abs(port.weight-expected[2]) > 1e-14):
            raise AssertionError("L1 native station ownership differs")

    # Embed three y=0 E4 trace nodes into the actual Q4 nodal ordering.
    line_y = np.flatnonzero(ys == 0.)
    line_x = np.searchsorted(xs, cuts)
    if (len(line_y) != 1 or not np.array_equal(xs[line_x], cuts)):
        raise AssertionError("E4 top-line nodes do not match material cuts")
    line_shell = np.concatenate([
        6*(int(line_y[0])*len(xs)+int(j))+np.arange(6) for j in line_x])
    shell_free = np.array([j for j in range(ns) if (j//6) % len(xs) != 0])
    beam_free = np.asarray(beam.context.free, dtype=int)
    p_native = np.concatenate([
        beam.context.nodal_count+24*e+np.arange(6, 24)
        for e in range(len(beam.context.elements))])
    p = ns+p_native
    free = np.r_[shell_free, ns+beam_free]
    drill = np.array([j for j in shell_free if j % 6 == 5], dtype=int)
    x = np.array([j for j in free if j not in set(p)], dtype=int)
    if len(x)+len(p) != len(free):
        raise AssertionError("physical/resultant partition is incomplete")

    h = linalg.block_diag(shell, beam.tangent.toarray())
    h_symmetry = float(np.linalg.norm(h-h.T, ord=np.inf) /
                       max(1., np.linalg.norm(h, ord=np.inf)))
    if h_symmetry > 1e-10:
        raise AssertionError("actual supported E4/native tangent is asymmetric")
    dual = np.zeros((3, 6))
    b = np.zeros((18, ns+nb))
    for row in range(18):
        dual.flat[row] = 1.
        _, gaps, local, _ = line.work_tangent(np.zeros((3, 6)), state, dual)
        if np.max(np.abs(gaps)) > 1e-14:
            raise AssertionError("L1 reference gap is nonzero")
        b[row, line_shell] = local[:18]
        b[row, ns:] = local[18:]
        dual.flat[row] = 0.
    if np.max(np.abs(b[:, p])) != 0.:
        raise AssertionError("L1 work acts on native resultants")
    cell_native = np.concatenate([
        beam.context.nodal_count+24*e+np.arange(6)
        for e in range(len(beam.context.elements))])
    cell_action = float(np.linalg.norm(b[:, ns+cell_native]))
    if cell_action == 0.:
        raise AssertionError("L1 action misses retained cell rotation")

    # Actual E4 PL completion gives drill stiffness; the L1 reference action
    # still annihilates those coordinates. No thresholded eigenvalue gauge.
    drill_stiffness = np.max(np.abs(h[drill, :]))
    drill_action = np.max(np.abs(b[:, drill]))
    if drill_stiffness <= 0. or drill_action > 1e-13:
        raise AssertionError("E4 drill completion or L1 drill action differs")

    hxx = h[np.ix_(x, x)]
    hxp = h[np.ix_(x, p)]
    hpp = h[np.ix_(p, p)]
    if np.linalg.norm(hpp-hpp.T, ord=np.inf) > 1e-11*max(1., np.linalg.norm(hpp, ord=np.inf)):
        raise AssertionError("native stationary resultant block is asymmetric")
    # The generalized complementary block is negative on this virgin domain.
    negative_pp = linalg.cho_factor(-hpp, lower=True, check_finite=True)
    stationary = linalg.cho_solve(negative_pp, -hxp.T)
    stationary_residual = float(np.linalg.norm(
        hpp@stationary-hxp.T, ord=np.inf) /
        max(1., np.linalg.norm(hpp, ord=np.inf)*
            np.linalg.norm(stationary, ord=np.inf)+
            np.linalg.norm(hxp.T, ord=np.inf)))
    if stationary_residual > 1e-10:
        raise AssertionError("native resultant stationary solve is inaccurate")
    kphys = hxx-hxp@stationary
    symmetry = float(np.linalg.norm(kphys-kphys.T, ord=np.inf) /
                     max(1., np.linalg.norm(kphys, ord=np.inf)))
    if symmetry > 1e-10:
        raise AssertionError("stationary physical block is asymmetric")
    physical_factor = linalg.cho_factor(kphys, lower=True)

    bx = b[:, x]
    reduced = bx@linalg.cho_solve(physical_factor, bx.T)
    full_ids = np.r_[x, p]
    retained = h[np.ix_(full_ids, full_ids)]
    full_action = b[:, full_ids]
    full = full_action@linalg.solve(retained, full_action.T, assume_a="sym")
    reduced_norm = float(np.linalg.norm(reduced, ord=np.inf))
    if reduced_norm <= 0.:
        raise AssertionError("L1 reduced compliance is zero")
    parity = float(np.linalg.norm(full-reduced, ord=np.inf) / reduced_norm)
    if parity > 1e-8:
        raise AssertionError("full-retained and p-reduced L1 compliance differ")

    # Sensitivity only: the separately exposed E4 physical component removes
    # PL completion. Its drill coordinates are an exact algebraic gauge here;
    # no near-null eigenvectors are discarded. This is not the operative E4
    # tangent and cannot by itself certify stability of that formulation.
    physical_h = linalg.block_diag(shell_physical, beam.tangent.toarray())
    if (np.max(np.abs(physical_h[drill, :])) != 0. or
            np.max(np.abs(b[:, drill])) != 0.):
        raise AssertionError("physical-component drill quotient is not exact")
    physical_x = np.array([j for j in x if j not in set(drill)], dtype=int)
    physical_xx = physical_h[np.ix_(physical_x, physical_x)]
    physical_xp = physical_h[np.ix_(physical_x, p)]
    physical_k = physical_xx-physical_xp@linalg.cho_solve(
        negative_pp, -physical_xp.T)
    physical_symmetry = float(np.linalg.norm(
        physical_k-physical_k.T, ord=np.inf) /
        max(1., np.linalg.norm(physical_k, ord=np.inf)))
    if physical_symmetry > 1e-10:
        raise AssertionError("physical-component quotient is asymmetric")
    physical_positive = True
    physical_parity = None
    physical_sensitivity = None
    try:
        physical_factor = linalg.cho_factor(physical_k, lower=True)
    except linalg.LinAlgError:
        physical_positive = False
    if physical_positive:
        physical_bx = b[:, physical_x]
        physical_reduced = physical_bx@linalg.cho_solve(
            physical_factor, physical_bx.T)
        physical_ids = np.r_[physical_x, p]
        physical_full = b[:, physical_ids]@linalg.solve(
            physical_h[np.ix_(physical_ids, physical_ids)],
            b[:, physical_ids].T, assume_a="sym")
        physical_norm = float(np.linalg.norm(physical_reduced, ord=np.inf))
        if physical_norm <= 0.:
            raise AssertionError("physical-component L1 compliance is zero")
        physical_parity = float(np.linalg.norm(
            physical_full-physical_reduced, ord=np.inf) / physical_norm)
        # Each diagonal compares the same physical action against itself, so
        # its relative change is independent of the force/moment unit choice.
        diagonal = np.diag(physical_reduced)
        if np.any(diagonal <= 0.):
            raise AssertionError("physical-component L1 basis action lacks positive work")
        physical_sensitivity = float(np.max(
            np.abs(np.diag(physical_reduced-reduced))/diagonal))
    return {
        "shell_dofs": ns, "native_dofs": nb, "dual_rows": len(b),
        "physical_dofs": len(x), "resultant_dofs": len(p),
        "free_shell_drill_coordinates": len(drill),
        "max_resultant_action": float(np.max(np.abs(b[:, p]))),
        "retained_cell_rotation_action": cell_action,
        "max_free_shell_drill_stiffness": float(drill_stiffness),
        "max_free_shell_drill_action": float(drill_action),
        "full_hessian_symmetry_relative": h_symmetry,
        "physical_symmetry_relative": symmetry,
        "stationary_backward_residual": stationary_residual,
        "actual_compliance_inf_norm": reduced_norm,
        "compliance_parity_relative": parity,
        "physical_component_exact_drill_gauge": len(drill),
        "physical_component_symmetry_relative": physical_symmetry,
        "physical_component_quotient_positive": physical_positive,
        "physical_component_compliance_parity_relative": physical_parity,
        "max_basis_action_work_change_relative": physical_sensitivity,
    }
