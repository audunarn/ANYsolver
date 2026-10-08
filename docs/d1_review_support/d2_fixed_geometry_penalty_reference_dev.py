"""Independent fixed-geometry fine-Q1 penalty reference for the saved D2 pilot.

Only the accepted structural q=0 stiffness is imported as an explicit oracle
input. No production contact function or pilot runner is called. On the fixed
rectangle Omega=[.1,1]^2, S_i=int N_i and M_ij=int N_i N_j are exact tensor
polynomial moments. With q=(u2z,u3z,u5z,u6z), G=M[:,free], c=1e-4:
  g=c+Gq/S, p=k[-g]+, R=Kff q-G.T p-F.
For each active subset A solve
  (Kff+k G_A.T diag(1/S_A)G_A)q=F-k*c G_A.T 1.
This has a convex potential ONLY with fixed geometry/support. Comparison with
the moving-projection/von-Karman pilot is a small-motion model comparison, not
a production kernel correctness verdict or continuum accuracy certificate.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import itertools
import json
from pathlib import Path
import sys
import time

import numpy as np
import anysolver
from anysolver import BoundaryCondition, create_shell_element
from anysolver.fe_core import FEModel
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.nonlinear_restart import model_configuration_fingerprint

ROOT = Path(__file__).resolve().parents[2]
FREE = np.array([1, 2, 4, 5])
ELEMENTS = ((0, 1, 4, 3), (1, 2, 5, 4))
SOURCE_XY = np.array([[.1, .1], [.6, .1], [1.1, .1],
                      [.1, 1.1], [.6, 1.1], [1.1, 1.1]])
TARGET_XY = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])
CLEARANCE = 1e-4


def identity(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def structural_fixture():
    # Literal neutral copy of the pilot's physical shells and BCs; no contact.
    model = FEModel("d2_projected_penalty_partial_overlap")
    model.add_material("elastic", 1e5, .3, density=1.)
    for node, (x, y) in enumerate(SOURCE_XY, 1):
        model.add_node(node, x, y, .0401)
    for node, (x, y) in enumerate(TARGET_XY, 7):
        model.add_node(node, x, y, 0.)
    for eid, ids in enumerate(ELEMENTS, 1):
        model.add_element(eid, create_shell_element(eid, tuple(i+1 for i in ids), "elastic",
            thickness=.05, reference_normal=(0., 0., 1.)))
    for eid, ids in ((3, (7, 8, 10)), (4, (8, 9, 10))):
        model.add_element(eid, create_shell_element(eid, ids, "elastic", thickness=.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0., 0., 1.),
            reference_surface_offset=.01))
    for name, ids in (("left", (1, 4)), ("target", (7, 8, 9, 10))):
        model.add_boundary_condition(BoundaryCondition(name, ids,
            {component: 0. for component in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    model.add_boundary_condition(BoundaryCondition("guided", (2, 3, 5, 6),
        {component: 0. for component in ("rx", "ry", "rz")}))
    model.add_boundary_condition(BoundaryCondition("in_plane", (3, 5, 6),
        {component: 0. for component in ("ux", "uy")}))
    model.apply_boundary_conditions()
    return model


def one_dimensional_moments(upper):
    s = np.array([upper-upper**2/2, upper**2/2])
    m = np.array([[upper-upper**2+upper**3/3, upper**2/2-upper**3/3],
                  [upper**2/2-upper**3/3, upper**3/3]])
    return s, m


def rectangle_integrals():
    support, mass = np.zeros(6), np.zeros((6, 6))
    y_s, y_m = one_dimensional_moments(.9)
    local_xy = ((0, 0), (1, 0), (1, 1), (0, 1))
    for ids, upper in zip(ELEMENTS, (1., .8), strict=True):
        x_s, x_m = one_dimensional_moments(upper)
        for i, (ix, iy) in enumerate(local_xy):
            support[ids[i]] += .5*x_s[ix]*y_s[iy]
            for j, (jx, jy) in enumerate(local_xy):
                mass[ids[i], ids[j]] += .5*x_m[ix, jx]*y_m[iy, jy]
    return support, mass


def source_shapes(x, y):
    column = 0 if x <= .6 else 1
    a, b = (x-(.1+.5*column))/.5, y-.1
    shape = np.zeros(6)
    shape[np.array(ELEMENTS[column])] = [(1-a)*(1-b), a*(1-b), a*b, (1-a)*b]
    return shape


def target_shapes(x, y):
    return np.array([1-x-y, x, 0., y]) if x+y <= 1 else np.array([0., 1-y, x+y-1, 1-x])


def target_pairing():
    # Independent polynomial quadrature split at the actual S3 diagonal and
    # source x knots. Degree <=4 after y integration: three x points are exact.
    pairing = np.zeros((6, 4))
    gx, wx = np.polynomial.legendre.leggauss(3)
    gy, wy = np.polynomial.legendre.leggauss(2)
    for left, right in ((.1, .6), (.6, .9), (.9, 1.)):
        for xi, x_weight in zip(gx, wx, strict=True):
            x = (left+right)/2+(right-left)*xi/2
            intervals = ((.1, 1-x), (1-x, 1.)) if x < .9 else ((.1, 1.),)
            for bottom, top in intervals:
                for eta, y_weight in zip(gy, wy, strict=True):
                    y = (bottom+top)/2+(top-bottom)*eta/2
                    pairing += np.outer(source_shapes(x, y), target_shapes(x, y))* (
                        (right-left)*x_weight*(top-bottom)*y_weight/4)
    return pairing


def physical_gap_and_slopes(u):
    rows = []
    for ids, x_upper in zip(ELEMENTS, (1., .8), strict=True):
        q = u[np.array(ids)]
        gaps = []
        slopes = []
        for a, b in ((0., 0.), (x_upper, 0.), (x_upper, .9), (0., .9)):
            weights = np.array([(1-a)*(1-b), a*(1-b), a*b, (1-a)*b])
            gaps.append(float(CLEARANCE+weights@q))
            slopes.append([float(((1-b)*(q[1]-q[0])+b*(q[2]-q[3]))/.5),
                           float((1-a)*(q[3]-q[0])+a*(q[2]-q[1]))])
        rows.append(dict(source_nodes=[i+1 for i in ids], gap_corners_m=gaps, slopes=slopes))
    return dict(minimum_represented_gap_m=min(min(row["gap_corners_m"]) for row in rows),
        maximum_component_slope=max(abs(v) for row in rows for pair in row["slopes"] for v in pair),
        maximum_normal_displacement_over_thickness=float(np.max(abs(u))/.05), rows=rows)


def fixed_reference(stiffness, k_full, source_dofs, target_dofs, support, mass, pairing):
    g_rows = mass[:, FREE]
    k_ff = k_full[np.ix_(source_dofs[FREE], source_dofs[FREE])]
    external = np.zeros(6); external[[2, 5]] = -.25
    candidates = []
    for mask in itertools.product((False, True), repeat=6):
        active = np.array(mask)
        a = g_rows[active]
        tangent = k_ff+stiffness*(a.T/support[active])@a
        q = np.linalg.solve(tangent, external[FREE]-stiffness*CLEARANCE*np.sum(a, axis=0))
        gap = CLEARANCE+(g_rows@q)/support
        if np.all(gap[active] < 0.) and np.all(gap[~active] >= 0.):
            pressure = stiffness*np.maximum(-gap, 0.)
            candidates.append((q, gap, pressure, active, tangent))
    if len(candidates) != 1:
        raise ValueError(f"expected one unambiguous active subset, obtained {len(candidates)}")
    q, gap, pressure, active, tangent = candidates[0]
    u_source = np.zeros(6); u_source[FREE] = q
    global_u = np.zeros(k_full.shape[0]); global_u[source_dofs] = u_source
    physical_source_nodal = mass.T@pressure
    target_support_nodal = pairing.T@pressure
    contact_internal = np.zeros(len(global_u))
    contact_internal[source_dofs] = -physical_source_nodal
    contact_internal[target_dofs] = target_support_nodal
    global_load = np.zeros(len(global_u)); global_load[source_dofs] = external
    total = k_full@global_u+contact_internal-global_load
    residual = k_ff@q-g_rows.T@pressure-external[FREE]
    if np.linalg.norm(residual) > 1e-10 or abs(np.sum(total[source_dofs])+np.sum(total[target_dofs])-.5) > 1e-10:
        raise ValueError("independent reference residual/reaction inconsistency")
    return dict(stiffness_pa_per_m=stiffness, mask_count=64,
        active_pressure_source_nodes=(np.flatnonzero(active)+1).tolist(),
        source_normal_displacements_m=u_source.tolist(), pressure_all_six_pa=pressure.tolist(),
        normalized_gap_all_six_m=gap.tolist(), physical_source_contact_nodal_force_n=physical_source_nodal.tolist(),
        physical_source_contact_force_n=float(support@pressure),
        physical_target_contact_force_n=-float(support@pressure),
        fixed_target_support_nodal_reaction_n=target_support_nodal.tolist(),
        target_normal_support_reaction_n=float(np.sum(target_support_nodal)),
        source_normal_support_reaction_n=float(np.sum(total[source_dofs])),
        full_generalized_reactions_n_or_nm=total.tolist(), residual_free_n=residual.tolist(),
        reaction_balance_relative=float(abs(np.sum(total[source_dofs])+np.sum(total[target_dofs])-.5)/.5),
        tangent_condition_number=float(np.linalg.cond(tangent)),
        physical_gap_and_slopes=physical_gap_and_slopes(u_source))


def grid_description(x_grid, y_grid):
    xy = np.array([(x, y) for y in y_grid for x in x_grid])
    nx = len(x_grid)
    cells = [(j*nx+i, j*nx+i+1, (j+1)*nx+i+1, (j+1)*nx+i)
             for j in range(len(y_grid)-1) for i in range(nx-1)]
    return xy, cells


def refined_structural_fixture(xy, cells):
    model = FEModel("d2_projected_penalty_partial_overlap_spatial_reference")
    model.add_material("elastic", 1e5, .3, density=1.)
    for node, (x, y) in enumerate(xy, 1):
        model.add_node(node, x, y, .0401)
    first_target = len(xy)+1
    for node, (x, y) in enumerate(TARGET_XY, first_target):
        model.add_node(node, x, y, 0.)
    for eid, ids in enumerate(cells, 1):
        model.add_element(eid, create_shell_element(eid, tuple(i+1 for i in ids), "elastic",
            thickness=.05, reference_normal=(0., 0., 1.)))
    target_cells = ((first_target, first_target+1, first_target+3),
                    (first_target+1, first_target+2, first_target+3))
    for eid, ids in enumerate(target_cells, len(cells)+1):
        model.add_element(eid, create_shell_element(eid, ids, "elastic", thickness=.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0., 0., 1.),
            reference_surface_offset=.01))
    left_ids = tuple(i+1 for i, (x, y) in enumerate(xy) if x == .1)
    model.add_boundary_condition(BoundaryCondition("left_normal", left_ids, {"uz": 0.}))
    model.add_boundary_condition(BoundaryCondition("source_guides", tuple(range(1, len(xy)+1)),
        {component: 0. for component in ("ux", "uy", "rx", "ry", "rz")}))
    model.add_boundary_condition(BoundaryCondition("target", tuple(range(first_target, first_target+4)),
        {component: 0. for component in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    model.apply_boundary_conditions()
    return model, left_ids


def grid_integrals(xy, cells):
    """Exact tensor Q1 moments plus exact polynomial target P1 pairing.

    Each source cell starts inside the target lower x/y bounds. Integrate only
    its rectangle clipped at target x=y=1. Three-by-two Gauss points integrate
    Q1*P1 exactly after splitting at the target diagonal and its y intersections.
    No production clipping, support threshold or contact function is used.
    """
    n = len(xy)
    support, mass, pairing = np.zeros(n), np.zeros((n, n)), np.zeros((n, 4))
    gx, wx = np.polynomial.legendre.leggauss(3)
    gy, wy = np.polynomial.legendre.leggauss(2)
    local_xy = ((0, 0), (1, 0), (1, 1), (0, 1))
    clipped = []
    for ids in cells:
        left, bottom = xy[ids[0]]
        right, top = xy[ids[2]]
        width, height = right-left, top-bottom
        x_end, y_end = min(right, 1.), min(top, 1.)
        if not (0 <= left < x_end and 0 <= bottom < y_end):
            raise ValueError("declared cell must have positive overlap and nonnegative lower bounds")
        a, b = (x_end-left)/width, (y_end-bottom)/height
        sx, mx = one_dimensional_moments(a)
        sy, my = one_dimensional_moments(b)
        for i, (ix, iy) in enumerate(local_xy):
            support[ids[i]] += width*height*sx[ix]*sy[iy]
            for j, (jx, jy) in enumerate(local_xy):
                mass[ids[i], ids[j]] += width*height*mx[ix, jx]*my[iy, jy]
        clipped.append(dict(source_nodes=[i+1 for i in ids], x_bounds_m=[left, x_end],
            y_bounds_m=[bottom, y_end], normalized_upper=[a, b]))
        cuts = sorted({float(left), float(x_end), *[float(cut) for cut in
            (1-bottom, 1-y_end) if left < cut < x_end]})
        for xlo, xhi in zip(cuts[:-1], cuts[1:], strict=True):
            for xi, xweight in zip(gx, wx, strict=True):
                x = (xlo+xhi)/2+(xhi-xlo)*xi/2
                y_cuts = sorted({float(bottom), float(y_end), *([float(1-x)]
                    if bottom < 1-x < y_end else [])})
                for ylo, yhi in zip(y_cuts[:-1], y_cuts[1:], strict=True):
                    for eta, yweight in zip(gy, wy, strict=True):
                        y = (ylo+yhi)/2+(yhi-ylo)*eta/2
                        ax, by = (x-left)/width, (y-bottom)/height
                        shape = np.array([(1-ax)*(1-by), ax*(1-by), ax*by, (1-ax)*by])
                        pairing[np.array(ids)] += np.outer(shape, target_shapes(x, y))* (
                            (xhi-xlo)*xweight*(yhi-ylo)*yweight/4)
    checks = dict(mass_partition_unity_max_m2=float(np.max(abs(mass.sum(axis=1)-support))),
        target_partition_unity_max_m2=float(np.max(abs(pairing.sum(axis=1)-support))),
        overlap_area_error_m2=float(abs(support.sum()-.81)), mass_symmetry=float(np.linalg.norm(mass-mass.T)))
    if max(checks.values()) > 1e-12 or np.min(support) <= 0:
        raise ValueError("independent spatial integral consistency failed")
    return support, mass, pairing, clipped, checks


def semismooth_reference(k_ff, support, g_rows, force, stiffness):
    """Bounded fixed-support convex solve; no active-subset enumeration.

    Residual R=Kq-G.T p-F is the gradient of E=.5qKq +
    .5*k*sum S_i*min(c+(Gq)_i/S_i,0)^2-Fq on this fixed geometry.
    This statement does not extend to the moving-support projected work.
    """
    def evaluate(q):
        gap = CLEARANCE+g_rows@q/support
        p = stiffness*np.maximum(-gap, 0.)
        residual = k_ff@q-g_rows.T@p-force
        energy = .5*q@k_ff@q+.5*stiffness*support@(np.minimum(gap, 0.)**2)-force@q
        return gap, p, residual, float(energy)

    q = np.zeros(len(force))
    history = []
    for iteration in range(41):
        gap, p, residual, energy = evaluate(q)
        norm = float(np.linalg.norm(residual))
        active = gap < 0.
        tangent = k_ff+stiffness*(g_rows[active].T/support[active])@g_rows[active]
        row = dict(iteration=iteration, residual_norm_n=norm, fixed_support_energy_j=energy,
            active_pressure_rows=(np.flatnonzero(active)+1).tolist())
        history.append(row)
        if norm <= 1e-11:
            return q, gap, p, tangent, history
        if iteration == 40:
            raise ValueError("bounded semismooth reference exceeded 40 Newton updates")
        direction = np.linalg.solve(tangent, -residual)
        descent = float(residual@direction)
        if descent >= 0.:
            raise ValueError("reference tangent gave a non-descent direction")
        # Convex-energy Armijo globalisation; residual decrease also admits a
        # numerically flat energy at convergence. Record both at every trial.
        trials = []
        for backtrack in range(41):
            alpha = 2.**(-backtrack)
            trial_q = q+alpha*direction
            trial_gap, trial_p, trial_r, trial_energy = evaluate(trial_q)
            trial_norm = float(np.linalg.norm(trial_r))
            energy_roundoff = 64*np.finfo(float).eps*max(abs(energy), abs(trial_energy), 1e-12)
            armijo = trial_energy <= energy+1e-4*alpha*descent+energy_roundoff
            flat_energy_residual = (trial_norm < norm and trial_energy <= energy+energy_roundoff)
            accepted = armijo or flat_energy_residual
            trials.append(dict(alpha=alpha, residual_norm_n=trial_norm, fixed_support_energy_j=trial_energy,
                energy_roundoff_j=energy_roundoff, accepted=bool(accepted)))
            if accepted:
                q = trial_q
                break
        else:
            raise ValueError("bounded energy/residual backtracking failed")
        row["backtracking"] = trials
    raise AssertionError("unreachable iteration boundary")


def grid_gap_and_slopes(xy, cells, u):
    rows = []
    for ids in cells:
        left, bottom = xy[ids[0]]
        right, top = xy[ids[2]]
        width, height = right-left, top-bottom
        a, b = (min(right, 1.)-left)/width, (min(top, 1.)-bottom)/height
        q = u[np.array(ids)]
        corners, slopes = [], []
        for ax, by in ((0., 0.), (a, 0.), (a, b), (0., b)):
            weights = np.array([(1-ax)*(1-by), ax*(1-by), ax*by, (1-ax)*by])
            corners.append(dict(x_m=float(left+ax*width), y_m=float(bottom+by*height),
                gap_m=float(CLEARANCE+weights@q)))
            slopes.append([float(((1-by)*(q[1]-q[0])+by*(q[2]-q[3]))/width),
                float(((1-ax)*(q[3]-q[0])+ax*(q[2]-q[1]))/height)])
        rows.append(dict(source_nodes=[i+1 for i in ids], clipped_gap_corners=corners, slopes=slopes))
    all_corners = [corner for row in rows for corner in row["clipped_gap_corners"]]
    return dict(minimum_represented_gap_m=min(corner["gap_m"] for corner in all_corners),
        minimum_locations=[corner for corner in all_corners if corner["gap_m"] == min(c["gap_m"] for c in all_corners)],
        maximum_component_slope=max(abs(v) for row in rows for pair in row["slopes"] for v in pair),
        maximum_normal_displacement_over_thickness=float(np.max(abs(u))/.05), rows=rows)


def spatial_reference(args):
    started = time.perf_counter()
    baseline = json.loads(args.baseline_reference.read_text(encoding="utf-8"))
    snapshot = Path(__file__).with_name("d2_fixed_geometry_penalty_reference_v1_20260930.source.py")
    if identity(snapshot)["sha256"] != baseline["adapter"]["sha256"]:
        raise ValueError("v1 source snapshot does not match executed baseline")
    print(json.dumps(dict(stage="coarse_reference_consistency", elapsed_seconds=time.perf_counter()-started)), flush=True)
    coarse_model = structural_fixture()
    coarse_k = assemble_stiffness_matrix(coarse_model)[0].toarray()
    coarse_dofs = np.array([coarse_model.mesh.dof_manager.get_node_dofs(node)[2] for node in range(1, 7)])
    coarse_support, coarse_mass, coarse_pairing, _, coarse_checks = grid_integrals(SOURCE_XY, ELEMENTS)
    known = next(row["reference"] for row in baseline["rows"] if row["reference"]["stiffness_pa_per_m"] == 1e7)
    cq, cg, cp, ct, ch = semismooth_reference(coarse_k[np.ix_(coarse_dofs[FREE], coarse_dofs[FREE])],
        coarse_support, coarse_mass[:, FREE], np.array([0., -.25, 0., -.25]), 1e7)
    consistency = dict(structural_full_matrix_max_difference=float(np.max(abs(coarse_k-np.array(
            baseline["structural_oracle_input"]["full_q0_stiffness_n_per_m_or_generalized"])))),
        support_max_difference_m2=float(np.max(abs(coarse_support-np.array(baseline["independent_integrals"]["support_m2"])))),
        mass_max_difference_m2=float(np.max(abs(coarse_mass-np.array(baseline["independent_integrals"]["source_q1_mass_m2"])))),
        target_pairing_max_difference_m2=float(np.max(abs(coarse_pairing-np.array(baseline["independent_integrals"]["source_target_p1_pairing_m2"])))),
        normal_solution_max_difference_m=float(np.max(abs(cq-np.array(known["source_normal_displacements_m"])[FREE]))),
        pressure_max_difference_pa=float(np.max(abs(cp-np.array(known["pressure_all_six_pa"])))),
        model_fingerprint_equal=model_configuration_fingerprint(coarse_model) == baseline["structural_model_fingerprint"],
        integral_checks=coarse_checks, semismooth_iteration_history=ch)
    if (not consistency["model_fingerprint_equal"] or consistency["structural_full_matrix_max_difference"] > 1e-10
            or consistency["normal_solution_max_difference_m"] > 1e-12 or consistency["pressure_max_difference_pa"] > 1e-8
            or max(consistency[key] for key in ("support_max_difference_m2", "mass_max_difference_m2", "target_pairing_max_difference_m2")) > 1e-12):
        raise ValueError("six-hat baseline reference consistency failed; stop before spatial prediction")
    print(json.dumps(dict(stage="spatial_reference", elapsed_seconds=time.perf_counter()-started)), flush=True)
    x_grid, y_grid = (.1, .35, .6, .85, 1.1), (.1, .6, 1.1)
    xy, cells = grid_description(x_grid, y_grid)
    model, left_ids = refined_structural_fixture(xy, cells)
    k_full = assemble_stiffness_matrix(model)[0].toarray()
    source_dofs = np.array([model.mesh.dof_manager.get_node_dofs(node)[2] for node in range(1, 16)])
    target_dofs = np.array([model.mesh.dof_manager.get_node_dofs(node)[2] for node in range(16, 20)])
    free = np.array([i for i in range(15) if i+1 not in left_ids])
    support, mass, pairing, clipped, checks = grid_integrals(xy, cells)
    force = np.zeros(15)
    force[[4, 14]] = -.25
    k_ff = k_full[np.ix_(source_dofs[free], source_dofs[free])]
    q, gap, pressure, tangent, history = semismooth_reference(k_ff, support, mass[:, free], force[free], 1e7)
    u = np.zeros(15); u[free] = q
    global_u, global_f, contact_internal = (np.zeros(len(k_full)) for _ in range(3))
    global_u[source_dofs], global_f[source_dofs] = u, force
    source_physical = mass.T@pressure
    target_support = pairing.T@pressure
    contact_internal[source_dofs], contact_internal[target_dofs] = -source_physical, target_support
    reaction = k_full@global_u+contact_internal-global_f
    balance = float(reaction[source_dofs].sum()+reaction[target_dofs].sum()-.5)
    if np.linalg.norm(reaction[source_dofs[free]]) > 1e-10 or abs(balance) > 1e-10:
        raise ValueError("spatial reference residual/reaction inconsistency")
    physical_gap = grid_gap_and_slopes(xy, cells, u)
    correspondence = []
    for old_id, point in enumerate(SOURCE_XY, 1):
        matches = np.flatnonzero(np.all(xy == point, axis=1))
        if len(matches) != 1:
            raise ValueError("original source world node is missing or duplicated")
        fine_index = int(matches[0])
        old_q = known["source_normal_displacements_m"][old_id-1]
        correspondence.append(dict(coarse_source_id=old_id, refined_source_id=fine_index+1,
            world_xy_m=point.tolist(), coarse_normal_displacement_m=old_q,
            refined_normal_displacement_m=float(u[fine_index]), difference_m=float(u[fine_index]-old_q)))
    old_gap = known["physical_gap_and_slopes"]["minimum_represented_gap_m"]
    new_gap = physical_gap["minimum_represented_gap_m"]
    structural_paths = [ROOT/"src/anysolver"/name for name in
        ("__init__.py", "fe_core.py", "matrix_assembly.py", "e4_pl_element.py", "e4_pl_s3_v2d_element.py")]
    result = dict(status="development_independent_fixed_geometry_spatial_prediction", accepted=False, released=False,
        production_contact_calls=0, new_coupled_solves=0, cap=dict(time_limit_seconds=180, memory_limit_bytes=1073741824),
        adapter=identity(__file__), retained_v1_adapter=identity(snapshot), baseline_input=identity(args.baseline_reference),
        structural_source=[identity(path) for path in structural_paths],
        actual_structural_function=identity(inspect.getsourcefile(assemble_stiffness_matrix)), python_executable=sys.executable,
        coarse_consistency=consistency, structural_model_fingerprint=model_configuration_fingerprint(model),
        fixture=dict(source_world_xy_m=xy.tolist(), source_reference_z_m=.0401, target_world_xy_m=TARGET_XY.tolist(),
            target_reference_z_m=0., source_skin_bottom_z_m=.0151, target_skin_top_z_m=.015,
            source_q4_nodes=[[i+1 for i in ids] for ids in cells], target_s3_nodes=[[16, 17, 19], [17, 18, 19]],
            target_reference_surface_offset_m=.01, source_and_target_thickness_m=.05,
            young_modulus_pa=1e5, poisson_ratio=.3, density=1., clearance_m=CLEARANCE,
            stiffness_pa_per_m=1e7, all_source_inplane_and_rotations_fixed=True,
            source_fixed_normal_ids=list(left_ids), source_free_normal_ids=(free+1).tolist(),
            target_all_dofs_fixed=True, source_normal_external_force_n=force.tolist(), common_node_correspondence=correspondence),
        structural_oracle_input=dict(full_q0_stiffness_n_per_m_or_generalized=k_full.tolist(),
            free_normal_q0_stiffness_n_per_m=k_ff.tolist(), source_normal_global_dofs=source_dofs.tolist(),
            target_normal_global_dofs=target_dofs.tolist(), scope="Accepted structural q=0 tangent is an explicit shared input; independent contact reference uses no production contact calls."),
        independent_integrals=dict(support_m2=support.tolist(), source_q1_mass_m2=mass.tolist(),
            source_target_p1_pairing_m2=pairing.tolist(), clipped_cells=clipped, checks=checks),
        reference=dict(source_normal_displacements_m=u.tolist(), pressure_all_fifteen_pa=pressure.tolist(),
            normalized_gap_all_fifteen_m=gap.tolist(), active_pressure_source_nodes=(np.flatnonzero(pressure > 0)+1).tolist(),
            physical_source_contact_nodal_force_n=source_physical.tolist(), physical_source_contact_force_n=float(support@pressure),
            physical_target_contact_force_n=-float(support@pressure), fixed_target_support_nodal_reaction_n=target_support.tolist(),
            target_normal_support_reaction_n=float(target_support.sum()), source_normal_support_reaction_n=float(reaction[source_dofs].sum()),
            full_generalized_reactions_n_or_nm=reaction.tolist(), residual_free_n=reaction[source_dofs[free]].tolist(),
            normal_reaction_balance_error_n=balance, physical_gap_and_slopes=physical_gap,
            tangent_condition_number=float(np.linalg.cond(tangent)), iteration_history=history),
        comparison=dict(coarse_target_normal_reaction_n=known["target_normal_support_reaction_n"],
            coarse_source_normal_reaction_n=known["source_normal_support_reaction_n"], coarse_minimum_represented_gap_m=old_gap,
            change_in_minimum_gap_m=new_gap-old_gap, represented_penetration_reduction_fraction=1-abs(min(new_gap, 0.))/abs(min(old_gap, 0.)),
            target_normal_reaction_difference_n=float(target_support.sum()-known["target_normal_support_reaction_n"])),
        elapsed_seconds=time.perf_counter()-started,
        limits=["One prescribed spatial refinement at fixed kappa=1e7; no mesh sweep, continuum convergence or method acceptance.",
            "Fixed vertical normal and overlap; q=0 structural tangent is a declared oracle input. Moving projection and nonlinear structural corrections are omitted.",
            "All positive supported pressure hats retained, including prescribed source rows; no uncovered-tip gap enters the represented minimum.",
            "Changes in source structural stiffness accompany Q4/contact refinement; this prediction distinguishes spatial response from increasing penalty alone, not their separate contributions."])
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(output=str(args.output), elapsed_seconds=result["elapsed_seconds"],
        minimum_represented_gap_m=new_gap, target_normal_reaction_n=float(target_support.sum()),
        active_pressure_source_nodes=result["reference"]["active_pressure_source_nodes"],
        newton_updates=len(history)-1)), flush=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--saved-first", type=Path)
    parser.add_argument("--saved-second", type=Path)
    parser.add_argument("--spatial", action="store_true")
    parser.add_argument("--baseline-reference", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.spatial:
        if args.baseline_reference is None or args.saved_first or args.saved_second:
            parser.error("--spatial requires --baseline-reference and no saved pilot inputs")
        spatial_reference(args)
        return
    if args.saved_first is None or args.saved_second is None or args.baseline_reference:
        parser.error("provide both saved pilot inputs, or select --spatial --baseline-reference")
    started = time.perf_counter()
    saved = [json.loads(path.read_text(encoding="utf-8")) for path in
             (args.saved_first, args.saved_second)]
    model = structural_fixture()
    fingerprint = model_configuration_fingerprint(model)
    for record in saved:
        if record["rows"][0]["restart_checkpoint"]["model_fingerprint"] != fingerprint:
            raise ValueError("neutral copied structural fixture differs from saved pilot model")
    k_sparse, k_info = assemble_stiffness_matrix(model)
    k_full = k_sparse.toarray()
    source_dofs = np.array([model.mesh.dof_manager.get_node_dofs(node)[2] for node in range(1, 7)])
    target_dofs = np.array([model.mesh.dof_manager.get_node_dofs(node)[2] for node in range(7, 11)])
    support, mass = rectangle_integrals()
    pairing = target_pairing()
    integral_errors = dict(mass_partition_unity_max_m2=float(np.max(abs(np.sum(mass, axis=1)-support))),
        target_partition_unity_max_m2=float(np.max(abs(np.sum(pairing, axis=1)-support))),
        overlap_area_error_m2=float(abs(np.sum(support)-.81)),
        mass_symmetry=float(np.linalg.norm(mass-mass.T)))
    if max(integral_errors.values()) > 1e-12 or np.min(support) <= 0:
        raise ValueError("independent rectangle/target pairing consistency failed")
    rows = []
    for old in saved:
        observed = old["rows"][0]
        stiffness = observed["stiffness_pa_per_m"]
        reference = fixed_reference(stiffness, k_full, source_dofs, target_dofs, support, mass, pairing)
        actual_q = np.array(observed["final_displacements"])[source_dofs]
        actual_certificate = observed["solver_info"]["force_displacement_history"][-1]["contact"]
        actual_p = np.array(actual_certificate["numerical_pressure_pa"])
        ref_q = np.array(reference["source_normal_displacements_m"])
        ref_p = np.array(reference["pressure_all_six_pa"])
        reference_p_at_actual = stiffness*np.maximum(-(CLEARANCE+mass@actual_q/support), 0.)
        k_ff = k_full[np.ix_(source_dofs[FREE], source_dofs[FREE])]
        ref_residual_at_actual = k_ff@actual_q[FREE]-mass[:, FREE].T@reference_p_at_actual-np.array([0., -.25, 0., -.25])
        reaction_actual = abs(float(actual_certificate["target_force"][2]))
        rows.append(dict(reference=reference, observed_source_normal_displacements_m=actual_q.tolist(),
            observed_pressure_pa=actual_p.tolist(), observed_contact_certificate=actual_certificate,
            comparison=dict(normal_displacement_l2_relative_to_saved=float(np.linalg.norm(ref_q-actual_q)/np.linalg.norm(actual_q)),
                nodal_normal_difference_m=(ref_q-actual_q).tolist(),
                pressure_l2_relative_to_saved=float(np.linalg.norm(ref_p-actual_p)/np.linalg.norm(actual_p)),
                target_normal_reaction_relative_to_saved=abs(reference["target_normal_support_reaction_n"]-reaction_actual)/reaction_actual,
                fixed_reference_residual_at_saved_q_relative=float(np.linalg.norm(ref_residual_at_actual)/.5),
                fixed_reference_pressure_at_saved_q_pa=reference_p_at_actual.tolist(),
                fixed_reference_gap_at_saved_q=physical_gap_and_slopes(actual_q),
                observed_horizontal_source_contact_force_n=actual_certificate["integration_force"][:2],
                fixed_reference_horizontal_force_n=[0., 0.],
                interpretation="Fixed vertical normal, fixed support and q=0 structural tangent versus moving-projection/von-Karman saved pilot; no disagreement pass/fail gate.")))
    paths = [ROOT/"src/anysolver"/name for name in
             ("__init__.py", "fe_core.py", "matrix_assembly.py", "e4_pl_element.py", "e4_pl_s3_v2d_element.py")]
    result = dict(status="development_independent_fixed_geometry_penalty_reference", accepted=False,
        released=False, production_contact_calls=0, new_coupled_solves=0,
        cap=dict(time_limit_seconds=180, memory_limit_bytes=1073741824),
        adapter=identity(__file__), structural_source=[identity(path) for path in paths],
        actual_structural_function=identity(inspect.getsourcefile(assemble_stiffness_matrix)),
        pilot_input=[identity(path) for path in (args.saved_first, args.saved_second)],
        structural_model_fingerprint=fingerprint, python_executable=sys.executable,
        structural_oracle_input=dict(full_q0_stiffness_n_per_m_or_generalized=k_full.tolist(),
            free_normal_q0_stiffness_n_per_m=k_full[np.ix_(source_dofs[FREE], source_dofs[FREE])].tolist(),
            source_normal_global_dofs=source_dofs.tolist(), target_normal_global_dofs=target_dofs.tolist(),
            scope="Accepted owner structural stiffness, explicitly shared input; contact integrals/reference solve independent."),
        independent_integrals=dict(support_m2=support.tolist(), source_q1_mass_m2=mass.tolist(),
            source_target_p1_pairing_m2=pairing.tolist(), checks=integral_errors),
        rows=rows, elapsed_seconds=time.perf_counter()-started,
        limits=["Fixed projected rectangle and vertical normal; no moving-projection or nonlinear structural correction included.",
                "Positive local physical penetration can coexist with weak nodal-gap constraints; only the represented rectangle is assessed.",
                "Comparisons do not establish continuum accuracy, method acceptance or a moving-support potential."])
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(output=str(args.output), elapsed_seconds=result["elapsed_seconds"],
        displacement_relative=[row["comparison"]["normal_displacement_l2_relative_to_saved"] for row in rows],
        target_reaction_relative=[row["comparison"]["target_normal_reaction_relative_to_saved"] for row in rows])), flush=True)


if __name__ == "__main__":
    main()
