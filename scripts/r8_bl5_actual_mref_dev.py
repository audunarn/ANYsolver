"""Independent flat P0 BL5 reference action for an actual mixed-shell owner.

The load functional is integrated from physical force/couple densities, not
from candidate C rows. This is development evidence, not an F03 quotient or
uniform-stability assessment.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy import linalg
from scipy.sparse.linalg import splu

from scripts.b3_e4_bl5_modal_reference_dev import p0_shell_bracket
from scripts.b3_e4_bl5_reference_accuracy_dev import beam_bracket
from scripts.b3_e4_bl5_reference_actions_dev import physical_loads, spatial_action
from scripts.b3_e4_bl5_riesz_controls_dev import beam_norm, shell_scalar
from scripts.r8_bl5_actual_primal_work_dev import actual_flat_primal_work


def _candidate_rhs(owner, shell_x, shell_y, beam_rhs, shell_rhs):
    """Scatter independently integrated physical loads to owner coordinates."""
    shell_count = owner._shell_count
    shell_nodes = len(owner._shell_ids)
    beam_nodes = len(owner._beam_ids)
    result = np.zeros(owner._K.shape[0])
    for node, position in enumerate(owner._shell_xyz):
        ix = int(np.argmin(np.abs(shell_x-position[0])))
        iy = int(np.argmin(np.abs(shell_y-position[1])))
        if (abs(shell_x[ix]-position[0]) > 2e-13 or
                abs(shell_y[iy]-position[1]) > 2e-13):
            raise ValueError("flat structured shell coordinates required")
        scalar = iy*len(shell_x)+ix
        for component in range(5):
            result[6*node+component] = shell_rhs[component*shell_nodes+scalar]
    for node in range(beam_nodes):
        result[shell_count+6*node:shell_count+6*node+3] = beam_rhs[3*node:3*node+3]
    retained = shell_count+6*beam_nodes
    for cell in range(beam_nodes-1):
        slot = retained+24*(cell//2)+3*(cell%2)
        start = 3*beam_nodes+3*cell
        result[slot:slot+3] = beam_rhs[start:start+3]
    return result


def _complete_rectangular_partition(owner, shell_x, shell_y):
    """Admit exactly one Q4 or two complementary S3s per reference cell."""
    invalid = "complete nonoverlapping Q4/S3 rectangular partition required"
    grid = {}
    for node_id, point in zip(owner._shell_ids, owner._shell_xyz):
        ix = int(np.argmin(np.abs(shell_x-point[0])))
        iy = int(np.argmin(np.abs(shell_y-point[1])))
        if (abs(shell_x[ix]-point[0]) > 2e-13 or
                abs(shell_y[iy]-point[1]) > 2e-13 or
                (ix, iy) in grid.values()):
            raise ValueError(invalid)
        grid[node_id] = (ix, iy)
    nx, ny = len(shell_x)-1, len(shell_y)-1
    if set(grid.values()) != {(i, j) for i in range(nx+1)
                              for j in range(ny+1)}:
        raise ValueError(invalid)
    buckets = {(i, j): {"q4": [], "s3": []}
               for i in range(nx) for j in range(ny)}
    panel = owner._definition.shell
    for family, elements in (("q4", panel.q4_elements),
                             ("s3", panel.s3_elements)):
        for element in elements:
            points = tuple(grid[node] for node in element)
            left = min(p[0] for p in points)
            bottom = min(p[1] for p in points)
            corners = {(left, bottom), (left+1, bottom),
                       (left+1, bottom+1), (left, bottom+1)}
            if ((left, bottom) not in buckets or
                    len(set(points)) != len(points) or
                    not set(points) <= corners):
                raise ValueError(invalid)
            buckets[left, bottom][family].append(set(points))
    for (left, bottom), bucket in buckets.items():
        corners = {(left, bottom), (left+1, bottom),
                   (left+1, bottom+1), (left, bottom+1)}
        quads, triangles = bucket["q4"], bucket["s3"]
        diagonal_a = {(left, bottom), (left+1, bottom+1)}
        diagonal_b = {(left+1, bottom), (left, bottom+1)}
        if not ((len(quads) == 1 and not triangles and quads[0] == corners) or
                (not quads and len(triangles) == 2 and
                 triangles[0] | triangles[1] == corners and
                 triangles[0] & triangles[1] in (diagonal_a, diagonal_b))):
            raise ValueError(invalid)


def flat_p0_reference_dual(owner, ell=.4, beam_width=.1,
                           refinements=(1, 2, 4)):
    """Return candidate action parity and independent refined M_ref records.

    Scope is the L=1 m, W=0.2 m flat structured, uniform native half-cell family
    with a complete P0 line and the root coordinate-selection supports.
    The five-channel multiplier basis uses force-equivalent mu, so physical
    lambda = diag(1,1,1,ell,ell) mu for each support interval.
    """
    _, embedding, work = actual_flat_primal_work(owner, ell, beam_width)
    shell_xyz = np.asarray(owner._shell_xyz)
    shell_x = np.unique(shell_xyz[:, 0])
    shell_y = np.unique(shell_xyz[:, 1])
    nx, ny = len(shell_x)-1, len(shell_y)-1
    beam_nodes = len(owner._beam_ids)
    cells = beam_nodes-1
    line = owner._definition.lines[0]
    span = line.multiplier_span
    if (line.basis != "p0" or nx < 1 or ny < 1 or
            len(shell_xyz) != len(shell_x)*len(shell_y) or
            not np.allclose(shell_x, np.linspace(0., 1., nx+1),
                            rtol=0., atol=2e-13) or
            not np.allclose(shell_y, np.linspace(0., .2, ny+1),
                            rtol=0., atol=2e-13) or
            cells % span or owner._C.shape[0] != 5*(cells//span)):
        raise ValueError("complete flat uniform P0 density family required")
    _complete_rectangular_partition(owner, shell_x, shell_y)
    trace_rows = {6*node+component
                  for node in range(len(owner._shell_ids))
                  for component in range(5)}
    trace_rows.update(owner._shell_count+6*node+component
                      for node in range(beam_nodes) for component in range(3))
    retained = owner._shell_count+6*beam_nodes
    trace_rows.update(retained+24*(cell//2)+3*(cell%2)+component
                      for cell in range(cells) for component in range(3))
    expected_fixed = {6*node+component
                      for node, position in enumerate(shell_xyz)
                      if abs(position[0]) < 2e-13 for component in range(5)}
    expected_fixed.update(owner._shell_count+component for component in range(3))
    if set(owner._fixed).intersection(trace_rows) != expected_fixed:
        raise ValueError("declared M2 root-only physical trace supports required")
    local = owner._line_samples[0][0]
    frame = np.asarray(local.port.frame)
    director = frame@local.reference_director
    arm_b = frame@local.reference_arm
    arm_s = .5*owner._definition.shell.thickness_m*director
    supports = cells//span
    qscale = np.repeat((1., 1., 1., ell, ell), supports)
    lambdas = np.diag(qscale)
    densities = [column.reshape(5, supports).T for column in lambdas.T]
    common = (frame, director, local.director_basis, arm_b, arm_s)

    candidate_loads = [physical_loads(density, *common,
                       np.linspace(0., 1., beam_nodes), shell_x, ny,
                       cells, span) for density in densities]
    physical = np.column_stack([
        embedding.T@_candidate_rhs(owner, shell_x, shell_y, b, s)
        for b, s, _ in candidate_loads])
    native = -np.asarray(work.T@lambdas)
    pairing_error = float(np.max(np.abs(native-physical)))
    if not np.allclose(native, physical, rtol=1e-11, atol=2e-12):
        raise ArithmeticError("independent physical density work differs from actual BL5 rows")

    records = []
    previous = None
    for refinement in refinements:
        if type(refinement) is not int or refinement <= 0:
            raise ValueError("positive nested reference refinements required")
        ref_nx, ref_ny = nx*refinement, ny*refinement
        ref_x, _, hs, sa = shell_scalar(1., .2, ell, ref_nx, ref_ny)
        ref_knots, hb, ba, _ = beam_norm(1., ell, cells, refinement,
                                        arm_b, beam_width)
        hs5 = sparse.block_diag((hs, hs, hs, ell**2*hs, ell**2*hs),
                                format="csc")
        shell_active = np.concatenate([
            component*((ref_ny+1)*(ref_nx+1))+sa for component in range(5)])
        loads = [physical_loads(density, *common, ref_knots, ref_x, ref_ny,
                                cells, span) for density in densities]
        shell_action = np.column_stack([s[shell_active] for _, s, _ in loads])
        beam_action = np.column_stack([b[ba] for b, _, _ in loads])
        zs = splu(hs5).solve(shell_action)
        zb = splu(hb).solve(beam_action)
        residual = max(
            float(np.linalg.norm(hs5@zs-shell_action)/
                  max(np.linalg.norm(shell_action), 1e-30)),
            float(np.linalg.norm(hb@zb-beam_action)/
                  max(np.linalg.norm(beam_action), 1e-30)))
        matrix = shell_action.T@zs+beam_action.T@zb
        skew = float(np.max(np.abs(matrix-matrix.T)))
        if residual > 1e-10 or skew > 1e-10 or not np.isfinite(matrix).all():
            raise ArithmeticError("positive reference inverse action failed")
        eigenvalues = np.linalg.eigvalsh((matrix+matrix.T)/2)
        if eigenvalues[0] <= 0.:
            raise ArithmeticError("independent multiplier reference has a null action")
        if previous is not None:
            difference = (matrix-previous+matrix.T-previous.T)/2
            if np.linalg.eigvalsh(difference)[0] < -1e-10*np.linalg.norm(matrix):
                raise ArithmeticError("nested reference dual lost monotonicity")
        records.append(dict(refinement=refinement, matrix=matrix,
                            minimum_eigenvalue=float(eigenvalues[0]),
                            inverse_residual=residual, skew=skew))
        previous = matrix
    return pairing_error, records


def flat_p0_reference_bracket(owner, ell=.4, beam_width=.1,
                              modes=1024, subdivisions=32):
    """Bound exact flat P0 physical dual via existing modal/beam majorants.

    This bounds M_ref only. It supplies no candidate inf-sup floor or beta.
    """
    # The complete supported actual-owner work and P0 reference identity are
    # checked before applying independent continuous-space bounds.
    flat_p0_reference_dual(owner, ell, beam_width, refinements=(1,))
    line = owner._definition.lines[0]
    cells = len(owner._beam_ids)-1
    supports = cells//line.multiplier_span
    local = owner._line_samples[0][0]
    frame = np.asarray(local.port.frame)
    director = frame@local.reference_director
    arm_b = frame@local.reference_arm
    arm_s = .5*owner._definition.shell.thickness_m*director
    basis = local.director_basis
    qscale = np.repeat((1., 1., 1., ell, ell), supports)
    columns = np.diag(qscale).T
    densities = [column.reshape(5, supports).T for column in columns]
    actions = [[spatial_action(row, frame, director, basis, arm_b, arm_s)
                for row in density] for density in densities]

    lower_scalar, upper_scalar, shell_info = p0_shell_bracket(
        np.linspace(0., 1., supports+1), 1., .2, ell, modes)
    shell_lower = np.zeros((len(columns), len(columns)))
    shell_upper = np.zeros_like(shell_lower)
    for component in range(5):
        block = np.array([[action[group][2 if component < 3 else 3]
                           [component if component < 3 else component-3]
                           for action in actions]
                          for group in range(supports)])
        factor = 1. if component < 3 else ell**2
        shell_lower += block.T@lower_scalar@block/factor
        shell_upper += block.T@upper_scalar@block/factor

    force = np.empty((cells, 3, len(columns)))
    moments = np.empty_like(force)
    for cell in range(cells):
        group = cell//line.multiplier_span
        for column, action in enumerate(actions):
            force[cell, :, column] = action[group][0]
            moments[cell, :, column] = action[group][1]/cells
    beam_lower, beam_upper, beam_info = beam_bracket(
        force, moments, length=1., ell=ell, arm=arm_b,
        width=beam_width, subdivisions=subdivisions)
    lower = shell_lower+beam_lower
    upper = shell_upper+beam_upper
    if (np.linalg.eigvalsh((lower+lower.T)/2)[0] <= 0. or
            np.linalg.eigvalsh((upper-lower+upper.T-lower.T)/2)[0] <
            -1e-10*np.linalg.norm(upper)):
        raise ArithmeticError("positive ordered independent dual bounds required")
    relative = float(linalg.eigvalsh((upper+upper.T)/2,
                                    (lower+lower.T)/2)[-1]-1.)
    return lower, upper, dict(relative_loewner_bound=relative,
                              shell=shell_info, beam=beam_info)
