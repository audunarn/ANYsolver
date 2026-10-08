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


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--saved-first", type=Path, required=True)
    parser.add_argument("--saved-second", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
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
