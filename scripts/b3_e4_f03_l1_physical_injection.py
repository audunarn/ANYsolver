"""Supported physical-field injection for bounded virgin L1 development grids.

This checks the entire six-channel multiplier action, not a stability quotient.
It uses the actual Q4/native B3 action assembled by the candidate comparison
fixture. Resultant coordinates remain stationary algebraic variables and are
not interpolated. No formal F03 authority is consumed by this diagnostic.
"""

from __future__ import annotations

import json

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_l1_native_connection_probe import (
    SegmentedL1WeakWork, shell_trace,
)
from scripts.b3_e4_f03_l1_space_design import (
    Macroelement, action_matrix, sampled_dual_spaces,
)
from scripts.b3_e4_f03_l1_nested_action import grid, injection


SPACES = (
    "P1_translation_twist_P0_pitch_normal",
    "P0_translation_twist_pair_P0_pitch_normal",
)


def _skew(v: np.ndarray) -> np.ndarray:
    return np.array(((0., -v[2], v[1]),
                     (v[2], 0., -v[0]),
                     (-v[1], v[0], 0.)))


def _virgin_gap_jacobian(macro: Macroelement) -> np.ndarray:
    """Independently pull the straight-reference pose Jacobian to coordinates.

    For the E4 projected material-line frame, the shell spatial spin is
    (weighted rx, weighted ry, lateral top-line displacement slope). This
    includes the top-surface lever arm and the native B3 station/offset arm.
    Only a straight virgin L1 fixture is admitted here.
    """
    state = macro.fixture.context.initial.mechanical
    nb = macro.fixture.context.count
    out = np.zeros((6*len(macro.stations), macro.coordinate_count))
    for sample, connection in enumerate(macro.connections):
        edge = sample//2
        reference = connection.reference
        span = float(reference[1, 0]-reference[0, 0])
        alpha = connection.station
        if (span <= 0. or not np.allclose(reference[:, 1:], 0.) or
                connection.thickness <= 0.):
            raise ValueError("straight, positive-span virgin trace required")
        shell, shell_frame, _, _ = shell_trace(
            reference, np.zeros((2, 6)), connection.thickness,
            station=alpha)
        high, low, beam_frame = connection.port.pose_pair(state)
        arm = beam_frame@np.asarray(connection.beam_offset)
        beam = high+low+arm
        if (np.linalg.norm(shell_frame-np.eye(3), ord=np.inf) > 1e-14 or
                np.linalg.norm(beam_frame-np.eye(3), ord=np.inf) > 1e-14):
            raise ValueError("reference triads differ from admitted straight chart")
        pose = connection.joint.evaluate(
            np.array((shell, beam)), np.array((shell_frame, beam_frame)),
            np.zeros(6))
        if np.max(np.abs(pose.constraints)) > 2e-14:
            raise AssertionError("reference connection has nonzero gap")
        spatial = np.zeros((12, 12+nb))
        half_t = .5*connection.thickness
        for node, weight in ((0, 1.-alpha), (1, alpha)):
            local = 6*node
            spatial[:3, local:local+3] += weight*np.eye(3)
            spatial[0, local+4] += weight*half_t
            spatial[1, local+3] -= weight*half_t
            spatial[3, local+3] += weight
            spatial[4, local+4] += weight
            slope_sign = (-1. if node == 0 else 1.)/span
            spatial[5, local+1] += slope_sign
            spatial[5, local+3] -= slope_sign*half_t
        port = connection.port.tangent(state)
        spatial[6:9, 12:] = port[:3]-_skew(arm)@port[3:]
        spatial[9:12, 12:] = port[3:]
        out[6*sample:6*sample+6,
            np.r_[6*edge+np.arange(12),
                  6*(macro.segments+1)+np.arange(nb)]] = (
            pose.constraint_jacobian@spatial)
    return out


def _kinematic_problem(segments: int) -> tuple[Macroelement, dict]:
    """Build the exact candidate action without any material tangent assembly."""
    if segments not in (2, 4, 8):
        raise ValueError("bounded 2/4/8-edge kinematic fixture required")
    fixture = build(2*segments, z_offset=.0675, assemble=False)
    cuts = fixture.abscissae[segments:].copy()
    reference = np.column_stack((cuts, np.zeros(segments+1),
                                 np.zeros(segments+1)))
    total = np.zeros((segments+1, 6))
    state = fixture.context.initial.mechanical

    def port_at(station):
        element, cell, weight, _ = fixture._locate(station)
        return NativeHalfCellSpatialPort(fixture.context, element, cell, weight)

    blocks = tuple(SegmentedL1WeakWork.at_reference(
        reference[i:i+3], total[i:i+3], .035, cuts[i:i+3], port_at, state)
        for i in range(0, segments, 2))
    stations = np.array([s for block in blocks for s in block.stations])
    weights = np.array([w for block in blocks for w in block.weights])
    macro = Macroelement(fixture, blocks, cuts, stations, weights)
    xs = np.linspace(0., 1., 2*segments+1)
    ys = np.linspace(-.1, .1, segments+1)
    ns = 6*len(xs)*len(ys)
    nb = fixture.context.count
    line_x = np.searchsorted(xs, cuts)
    line_y = int(np.argmin(np.abs(ys)))
    if not np.array_equal(xs[line_x], cuts) or abs(ys[line_y]) > 1e-15:
        raise AssertionError("reference line is not nested in Q4 grid")
    line_shell = np.concatenate([
        6*(line_y*len(xs)+int(j))+np.arange(6) for j in line_x])
    shell_free = np.array([j for j in range(ns) if (j//6) % len(xs) != 0])
    p_native = np.concatenate([
        fixture.context.nodal_count+24*element+np.arange(6, 24)
        for element in range(len(fixture.context.elements))])
    free = np.r_[shell_free, ns+np.asarray(fixture.context.free, dtype=int)]
    p_set = set(ns+p_native)
    x = np.array([j for j in free if j not in p_set], dtype=int)
    gap = _virgin_gap_jacobian(macro)
    spaces = sampled_dual_spaces(macro)
    action = {}
    for name in SPACES:
        local = action_matrix(macro, spaces[name], gap)
        global_action = np.zeros((local.shape[0], ns+nb))
        global_action[:, line_shell] = local[:, :6*(segments+1)]
        global_action[:, ns:] = local[:, 6*(segments+1):]
        if np.max(np.abs(global_action[:, ns+p_native])) != 0.:
            raise AssertionError("native generalized resultants entered L1 work")
        action[name] = global_action
    return macro, {"xs": xs, "ys": ys, "ns": ns, "nb": nb,
                   "x": x, "p": ns+p_native, "action": action}


def _linear_weights(nodes: np.ndarray, coordinate: float) -> tuple[int, float]:
    left = min(int(np.searchsorted(nodes, coordinate, side="right"))-1,
               len(nodes)-2)
    if left < 0 or coordinate < nodes[0] or coordinate > nodes[-1]:
        raise ValueError("fine coordinate lies outside coarse reference")
    fraction = (coordinate-nodes[left])/(nodes[left+1]-nodes[left])
    return left, float(fraction)


def physical_injection(coarse: dict, fine: dict,
                       coarse_macro, fine_macro) -> np.ndarray:
    """Interpolate shell/nodal fields and copy native half-cell rotations.

    Rows and columns use the full global coordinate layouts. Resultant rows
    and columns are zero; the supported physical submatrix is extracted by
    the caller. This makes support preservation and forbidden p-action
    directly checkable rather than assumed.
    """
    xc, yc = coarse["xs"], coarse["ys"]
    xf, yf = fine["xs"], fine["ys"]
    if (not np.array_equal(xf[::2], xc) or
            not np.array_equal(yf[::2], yc) or
            not np.array_equal(fine_macro.fixture.abscissae[::2],
                               coarse_macro.fixture.abscissae)):
        raise ValueError("nested straight shell/native reference required")
    out = np.zeros((fine["ns"]+fine["nb"],
                    coarse["ns"]+coarse["nb"]))

    # All six Q4 nodal coordinates share the same bilinear reference map.
    for jy, y in enumerate(yf):
        iy, ty = _linear_weights(yc, float(y))
        for jx, x in enumerate(xf):
            ix, tx = _linear_weights(xc, float(x))
            target = 6*(jy*len(xf)+jx)
            for dy, wy in ((0, 1.-ty), (1, ty)):
                for dx, wx in ((0, 1.-tx), (1, tx)):
                    source = 6*((iy+dy)*len(xc)+ix+dx)
                    out[target:target+6, source:source+6] += (
                        wx*wy*np.eye(6))

    # Native nodal coordinates have six entries per reference station. The
    # attachment acts on translations and retained cell rotations, while
    # nodal rotation interpolation supplies a coherent physical-field map.
    sc = coarse_macro.fixture.abscissae
    sf = fine_macro.fixture.abscissae
    for node, station in enumerate(sf):
        parent, fraction = _linear_weights(sc, float(station))
        target = fine["ns"]+6*node
        for side, weight in ((0, 1.-fraction), (1, fraction)):
            source = coarse["ns"]+6*(parent+side)
            out[target:target+6, source:source+6] += weight*np.eye(6)

    # Each fine half-cell inherits the physical spatial rotation of its
    # containing coarse half-cell. The 18 generalized resultants per element
    # are intentionally absent from this physical injection.
    coarse_base = coarse["ns"]+coarse_macro.fixture.context.nodal_count
    fine_base = fine["ns"]+fine_macro.fixture.context.nodal_count
    for child in range(fine_macro.fixture.n_half_cells):
        parent = child//2
        child_element, child_cell = divmod(child, 2)
        parent_element, parent_cell = divmod(parent, 2)
        target = fine_base+24*child_element+3*child_cell
        source = coarse_base+24*parent_element+3*parent_cell
        out[target:target+3, source:source+3] = np.eye(3)
    return out


def report(coarse_segments: int = 2) -> dict:
    if coarse_segments not in (2, 4):
        raise ValueError("only bounded nested 2:4 or 4:8 grids admitted")
    cm, cp = _kinematic_problem(coarse_segments)
    fm, fp = _kinematic_problem(2*coarse_segments)
    t = physical_injection(cp, fp, cm, fm)
    xc, xf = cp["x"], fp["x"]
    excluded_fine = np.setdiff1d(np.arange(t.shape[0]), xf)
    fixed_leak = float(np.max(np.abs(t[np.ix_(excluded_fine, xc)])))
    p_column_action = float(np.max(np.abs(t[:, cp["p"]])))
    out = {"coarse_edges": coarse_segments,
           "fine_edges": 2*coarse_segments,
           "coarse_physical_dofs": len(xc), "fine_physical_dofs": len(xf),
           "supported_to_fixed_or_resultant_leak": fixed_leak,
           "resultant_column_action": p_column_action,
           "spaces": {}}
    for space in SPACES:
        j = injection(grid(coarse_segments), grid(2*coarse_segments),
                      space)
        bc = cp["action"][space][:, xc]
        bf = fp["action"][space][:, xf]
        difference = j.T@bf@t[np.ix_(xf, xc)]-bc
        denominator = max(1., float(np.max(np.abs(bc))),
                          float(np.max(np.abs(j.T@bf@t[np.ix_(xf, xc)]))))
        out["spaces"][space] = {
            "multiplier_rows": [bc.shape[0], bf.shape[0]],
            "max_abs_work_map_difference": float(np.max(np.abs(difference))),
            "relative_work_map_difference": float(
                np.max(np.abs(difference))/denominator),
        }
    return out


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
