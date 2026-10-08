"""Independent covered S3/S3 normal-coordinate manufactured reference.

S_i=integral Ns_i, M_ij=integral Ns_i Ns_j, H_ia=integral Ns_i Nt_a.
On fixed XY support G=[M,-H], g=gap0+Gq/S, p=kappa*max(-g,0),
and R=Kff*qfree-Gfree.T*p-F. This is a mathematical/code fixture,
not a moving-projection, continuum or point-load acceptance reference.

The two exported oracle functions do not mutate models or call production
contact code. Cell inputs use joint one-based node IDs: source1..6,target7..10.
The executable check uses an explicitly shared, accepted structural-only q=0
tangent assembled on a neutral literal copy of the declared covered shells.
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

SOURCE_XY = np.array(((.1, .1), (.6, .1), (1.1, .1),
                      (.1, 1.1), (.6, 1.1), (1.1, 1.1)))
SOURCE_CELLS = ((1, 2, 4), (2, 5, 4), (2, 3, 5), (3, 6, 5))
TARGET_XY = np.array(((0., 0.), (1.4, 0.), (1.4, 1.4), (0., 1.4)))
TARGET_CELLS = ((7, 8, 10), (8, 9, 10))
FREE = np.array([1, 2, 4, 5, 7, 8])
KNOWN_Q = 1e-6*np.array([0., -1., -1., 0., -1., -1., 0., .3, .3, 0.])


def _cross(a, b):
    return float(a[0]*b[1]-a[1]*b[0])


def _cell_indices(ids, first_id, size):
    original = np.asarray(ids)
    integers = np.asarray(ids, dtype=int)
    if (integers.shape != (3,) or not np.array_equal(original, integers)
            or len(set(integers)) != 3 or np.any(integers < first_id)
            or np.any(integers >= first_id+size)):
        raise ValueError("cells require three distinct joint one-based node IDs")
    return integers-first_id


def _clip_triangle(source, target):
    """Independent half-plane clipping in the declared XY plane."""
    polygon = [point.copy() for point in source]
    for start, end in zip(target, np.roll(target, -1, axis=0), strict=True):
        if not polygon:
            break
        edge, previous = end-start, polygon[-1]
        previous_distance = _cross(edge, previous-start)
        result = []
        for current in polygon:
            distance = _cross(edge, current-start)
            if (distance >= 0.) != (previous_distance >= 0.):
                fraction = previous_distance/(previous_distance-distance)
                result.append(previous+fraction*(current-previous))
            if distance >= 0.:
                result.append(current.copy())
            previous, previous_distance = current, distance
        polygon = result
    return np.asarray(polygon, dtype=float).reshape(-1, 2)


def independent_p1_integrals(source_xy, source_cells, target_xy, target_cells):
    """Return S, M, H and exact polygon-vertex affine hat values.

    Products of two affine hats on a triangle integrate as
    A/12*((sum f)*(sum h)+sum f_j*h_j). The common-refinement fan
    is only an integration device; no new pressure/contact features are made.
    """
    source_xy, target_xy = np.asarray(source_xy, float), np.asarray(target_xy, float)
    if (source_xy.ndim != 2 or target_xy.ndim != 2 or source_xy.shape[1] != 2
            or target_xy.shape[1] != 2 or not np.all(np.isfinite(source_xy))
            or not np.all(np.isfinite(target_xy))):
        raise ValueError("source and target XY coordinates must be finite Nx2 arrays")
    ns, nt = len(source_xy), len(target_xy)
    support, mass, cross_mass = np.zeros(ns), np.zeros((ns, ns)), np.zeros((ns, nt))
    source_rows = [_cell_indices(ids, 1, ns) for ids in source_cells]
    target_rows = [_cell_indices(ids, ns+1, nt) for ids in target_cells]
    for xy, rows in ((source_xy, source_rows), (target_xy, target_rows)):
        for row in rows:
            triangle = xy[row]
            if _cross(triangle[1]-triangle[0], triangle[2]-triangle[0]) <= 0.:
                raise ValueError("declared triangles must have positive XY orientation and area")
    cells = []
    for source_indices in source_rows:
        triangle_s = source_xy[source_indices]
        source_basis = np.linalg.inv(np.c_[triangle_s, np.ones(3)])
        for target_indices in target_rows:
            triangle_t = target_xy[target_indices]
            target_basis = np.linalg.inv(np.c_[triangle_t, np.ones(3)])
            polygon = _clip_triangle(triangle_s, triangle_t)
            if len(polygon) < 3:
                continue
            source_values = np.c_[polygon, np.ones(len(polygon))]@source_basis
            target_values = np.c_[polygon, np.ones(len(polygon))]@target_basis
            area_total = 0.
            for j in range(1, len(polygon)-1):
                fan = [0, j, j+1]
                triangle = polygon[fan]
                area = .5*_cross(triangle[1]-triangle[0], triangle[2]-triangle[0])
                if area < 0.:
                    raise ValueError("common-refinement polygon orientation is inconsistent")
                if area == 0.:
                    continue
                s_values, t_values = source_values[fan], target_values[fan]
                sum_s, sum_t = s_values.sum(axis=0), t_values.sum(axis=0)
                support[source_indices] += area*sum_s/3
                mass[np.ix_(source_indices, source_indices)] += area/12*(
                    np.outer(sum_s, sum_s)+s_values.T@s_values)
                cross_mass[np.ix_(source_indices, target_indices)] += area/12*(
                    np.outer(sum_s, sum_t)+s_values.T@t_values)
                area_total += area
            if area_total > 0.:
                cells.append(dict(source_indices=source_indices.tolist(), target_indices=target_indices.tolist(),
                    polygon_xy_m=polygon.tolist(), source_values=source_values.tolist(),
                    target_values=target_values.tolist(), area_m2=area_total))
    if not np.all(support > 0.):
        raise ValueError("this covered fixture requires every source pressure hat to have positive support")
    return support, mass, cross_mass, cells


def normal_reference(kff, free_indices, support, source_mass, cross_mass,
                     known_normal_displacements, *, gap0=1e-8, kappa=1e7):
    """Manufacture the six free forces and independently enumerate 64 masks."""
    support, mass, cross_mass = np.asarray(support, float), np.asarray(source_mass, float), np.asarray(cross_mass, float)
    kff, free = np.asarray(kff, float), np.asarray(free_indices, int)
    known = np.asarray(known_normal_displacements, float)
    ns, nt = len(support), cross_mass.shape[1]
    if (ns != 6 or mass.shape != (ns, ns) or cross_mass.shape[0] != ns
            or known.shape != (ns+nt,) or free.shape != (6,) or kff.shape != (6, 6)
            or len(set(free)) != 6 or np.any(free < 0) or np.any(free >= len(known))
            or np.any(support <= 0.) or not np.isfinite(gap0) or gap0 <= 0.
            or not np.isfinite(kappa) or kappa <= 0.
            or not all(np.all(np.isfinite(a)) for a in (support, mass, cross_mass, kff, known))):
        raise ValueError("covered six-pressure/six-free-normal reference inputs are invalid")
    if np.any(known[np.setdiff1d(np.arange(len(known)), free)] != 0.):
        raise ValueError("prescribed normal coordinates must be identically zero in this reference")
    if not np.allclose(kff, kff.T, rtol=1e-12, atol=1e-12) or np.min(np.linalg.eigvalsh(kff)) <= 0.:
        raise ValueError("declared q=0 structural Kff input must be symmetric positive definite")
    G = np.concatenate((mass, -cross_mass), axis=1)
    gfree = G[:, free]
    manufactured_gap = gap0+G@known/support
    manufactured_pressure = kappa*np.maximum(-manufactured_gap, 0.)
    force = kff@known[free]-gfree.T@manufactured_pressure
    answers = []
    for flags in itertools.product((False, True), repeat=6):
        active = np.array(flags)
        tangent = kff+kappa*(gfree[active].T/support[active])@gfree[active]
        qfree = np.linalg.solve(tangent, force-kappa*gap0*gfree[active].sum(axis=0))
        gap = gap0+gfree@qfree/support
        if np.any(gap[active] > 1e-14) or np.any(gap[~active] < -1e-14):
            continue
        pressure = kappa*np.maximum(-gap, 0.)
        residual = kff@qfree-gfree.T@pressure-force
        answers.append((qfree, gap, pressure, active, residual, tangent))
    if len(answers) != 1:
        raise ValueError(f"independent pressure-mask solve found {len(answers)} compatible masks")
    qfree, gap, pressure, active, residual, tangent = answers[0]
    recovered = np.zeros(ns+nt); recovered[free] = qfree
    if (np.max(abs(recovered-known)) > 1e-12 or np.linalg.norm(residual) > 1e-11
            or np.max(abs(pressure-manufactured_pressure)) > 1e-8):
        raise ValueError("manufactured displacement/pressure recovery or residual check failed")
    return dict(normal_displacements_m=recovered.tolist(), pressure_pa=pressure.tolist(),
        free_normal_forces_n=force.tolist(), contact_force_n=float(support@pressure), G=G.tolist(), kff=kff.tolist(),
        free_indices=free.tolist(), free_residual_n=residual.tolist(), active_node_ids=(np.flatnonzero(active)+1).tolist(),
        source_physical_contact_nodal_force_n=(mass.T@pressure).tolist(),
        target_physical_contact_nodal_force_n=(-cross_mass.T@pressure).tolist(),
        contact_internal_normal_forces_n=(-G.T@pressure).tolist(), normalized_gap_m=gap.tolist(),
        known_normal_displacements_m=known.tolist(), manufactured_pressure_pa=manufactured_pressure.tolist(),
        gap0_m=float(gap0), kappa_pa_per_m=float(kappa), mask_count=64, compatible_mask_count=len(answers),
        tangent_condition_number=float(np.linalg.cond(tangent)),
        normal_recovery_max_error_m=float(np.max(abs(recovered-known))),
        pressure_recovery_max_error_pa=float(np.max(abs(pressure-manufactured_pressure))))


def _shared_structural_input():
    # Neutral literal copied shells and the new joint normal BCs. The exported
    # oracle functions above receive matrices/arrays only; no model mutation.
    from anysolver import BoundaryCondition, create_shell_element
    from anysolver.fe_core import FEModel
    from anysolver.matrix_assembly import assemble_stiffness_matrix
    model = FEModel("d2_s3_deformable_mms_neutral_structural_input")
    model.add_material("elastic", 1e5, .3, density=1.)
    for node, (x, y) in enumerate(SOURCE_XY, 1):
        model.add_node(node, float(x), float(y), .04+1e-8)
    for node, (x, y) in enumerate(TARGET_XY, 7):
        model.add_node(node, float(x), float(y), 0.)
    for eid, ids in enumerate(SOURCE_CELLS+TARGET_CELLS, 1):
        model.add_element(eid, create_shell_element(eid, ids, "elastic", thickness=.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0., 0., 1.), reference_surface_offset=.01 if eid > 4 else 0.))
    model.add_boundary_condition(BoundaryCondition("normal_fixed", (1, 4, 7, 10), {"uz": 0.}))
    model.add_boundary_condition(BoundaryCondition("all_guides", tuple(range(1, 11)),
        {key: 0. for key in ("ux", "uy", "rx", "ry", "rz")}))
    model.apply_boundary_conditions()
    full = assemble_stiffness_matrix(model)[0].toarray()
    normal_dofs = np.array([model.mesh.dof_manager.get_node_dofs(node)[2] for node in range(1, 11)])
    return full, normal_dofs, inspect.getsourcefile(assemble_stiffness_matrix)


def _identity(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    support, mass, cross_mass, cells = independent_p1_integrals(SOURCE_XY, SOURCE_CELLS, TARGET_XY, TARGET_CELLS)
    errors = dict(area_error_m2=float(abs(support.sum()-1.)), mass_partition_error_m2=float(np.max(abs(mass.sum(axis=1)-support))),
        cross_partition_error_m2=float(np.max(abs(cross_mass.sum(axis=1)-support))), mass_symmetry=float(np.max(abs(mass-mass.T))),
        affine_x_reproduction_error_m3=float(np.max(abs(mass@SOURCE_XY[:, 0]-cross_mass@TARGET_XY[:, 0]))),
        affine_y_reproduction_error_m3=float(np.max(abs(mass@SOURCE_XY[:, 1]-cross_mass@TARGET_XY[:, 1]))))
    wrench_checks = []
    first_moment, squared_moment, mixed_moment = .6, (1.1**3-.1**3)/3, .6**2
    for constant, x_slope, y_slope in ((1., 0., 0.), (2., .3, -.4)):
        pressure = constant+x_slope*SOURCE_XY[:, 0]+y_slope*SOURCE_XY[:, 1]
        source_nodal, target_nodal = mass.T@pressure, -cross_mass.T@pressure
        expected_force = constant+x_slope*first_moment+y_slope*first_moment
        expected_moment = np.array([constant*first_moment+x_slope*mixed_moment+y_slope*squared_moment,
            -(constant*first_moment+x_slope*squared_moment+y_slope*mixed_moment), 0.])
        source_moment = np.array([SOURCE_XY[:, 1]@source_nodal, -SOURCE_XY[:, 0]@source_nodal, 0.])
        target_moment = np.array([TARGET_XY[:, 1]@target_nodal, -TARGET_XY[:, 0]@target_nodal, 0.])
        wrench_checks.append(dict(pressure_coefficients=[constant, x_slope, y_slope],
            literal_force_n=expected_force, source_force_n=float(source_nodal.sum()), target_force_n=float(target_nodal.sum()),
            literal_source_moment_nm=expected_moment.tolist(), source_moment_nm=source_moment.tolist(), target_moment_nm=target_moment.tolist(),
            maximum_error=float(max(abs(source_nodal.sum()-expected_force), abs(target_nodal.sum()+expected_force),
                np.max(abs(source_moment-expected_moment)), np.max(abs(target_moment+expected_moment))))))
    if max(errors.values()) > 1e-12 or max(row["maximum_error"] for row in wrench_checks) > 1e-12:
        raise ValueError("exact P1 area/partition/affine force-moment consistency failed")
    full_k, normal_dofs, structural_source = _shared_structural_input()
    normal_k = full_k[np.ix_(normal_dofs, normal_dofs)]
    oracle = normal_reference(normal_k[np.ix_(FREE, FREE)], FREE, support, mass, cross_mass, KNOWN_Q)
    recovered = np.array(oracle["normal_displacements_m"])
    polygon_gaps = [1e-8+np.array(cell["source_values"])@recovered[np.array(cell["source_indices"])]
        -np.array(cell["target_values"])@recovered[6+np.array(cell["target_indices"])] for cell in cells]
    root = Path(__file__).resolve().parents[2]
    structural_paths = [root/"src/anysolver"/name for name in
        ("matrix_assembly.py", "fe_core.py", "e4_pl_s3_v2d_element.py")]
    result = dict(status="development_independent_deformable_s3_mms_reference", accepted=False, released=False,
        production_contact_calls=0, coupled_shell_solves=0, cap=dict(time_limit_seconds=180, memory_limit_bytes=1073741824),
        adapter=_identity(__file__), literal_fixture_source=_identity(Path(__file__).with_name("d2_s3_projected_penalty_coupled_dev.py")),
        structural_source=[_identity(path) for path in structural_paths], actual_structural_function=_identity(structural_source),
        python_executable=sys.executable, fixture=dict(source_xy_m=SOURCE_XY.tolist(), source_cells=SOURCE_CELLS,
            target_xy_m=TARGET_XY.tolist(), target_cells=TARGET_CELLS, source_reference_z_m=.04+1e-8,
            target_reference_z_m=0., thickness_m=.05, source_offset_m=0., target_offset_m=.01,
            young_modulus_pa=1e5, poisson_ratio=.3, density=1., fixed_normal_node_ids=[1, 4, 7, 10],
            free_normal_node_ids=[2, 3, 5, 6, 8, 9], all_inplane_and_rotational_dofs_fixed=True),
        independent_integrals=dict(support_m2=support.tolist(), source_mass_m2=mass.tolist(), cross_mass_m2=cross_mass.tolist(),
            checks=errors, constant_affine_wrench_checks=wrench_checks, cells=cells),
        structural_oracle_input=dict(full_q0_stiffness_n_per_m_or_generalized=full_k.tolist(), normal_q0_stiffness_n_per_m=normal_k.tolist(),
            normal_global_dofs=normal_dofs.tolist(), scope="Accepted structural-only q=0 tangent explicitly shared as input; no production contact calls."),
        reference=oracle, independent_minimum_vertical_gap_m=float(min(np.min(values) for values in polygon_gaps)),
        elapsed_seconds=time.perf_counter()-started,
        limits=["Fixed XY common refinement and vertical normal; nonlinear structure/moving normal or support is excluded.",
            "Known normal field manufactures its load; no claim of continuum or point-load accuracy, qualification or release.",
            "Contact physical normal forces are +M.T*p on source and -H.T*p on target; generalized contact internal vector is -G.T*p."])
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(output=str(args.output), elapsed_seconds=result["elapsed_seconds"],
        common_polygons=len(cells), integral_max_error=max(errors.values()), wrench_max_error=max(row["maximum_error"] for row in wrench_checks),
        normal_recovery_max_error_m=oracle["normal_recovery_max_error_m"], pressure_recovery_max_error_pa=oracle["pressure_recovery_max_error_pa"],
        free_residual_norm_n=float(np.linalg.norm(oracle["free_residual_n"])), active_node_ids=oracle["active_node_ids"])), flush=True)


if __name__ == "__main__":
    main()
