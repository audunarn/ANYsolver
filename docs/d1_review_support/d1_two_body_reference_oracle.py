"""Independent frozen-footprint linear Q1/S3 oracle for the bounded D1 fixture.

This deliberately does not call ANYsolver contact geometry or enforcement code.
It uses the structural model's linear stiffness, clips reference XY polygons,
integrates shape products with tensor Gauss quadrature, and solves a small KKT
active-set system. It is a development comparator, not a nonlinear oracle.
"""

from __future__ import annotations

import numpy as np

from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import assemble_stiffness_matrix


def _cross(a: np.ndarray, b: np.ndarray) -> float:
    return float(a[0]*b[1] - a[1]*b[0])


def _clip(polygon: np.ndarray, triangle: np.ndarray) -> np.ndarray:
    """Intersect a convex XY polygon with a counterclockwise triangle."""
    output = [np.asarray(point, dtype=float) for point in polygon]
    if _cross(triangle[1]-triangle[0], triangle[2]-triangle[0]) <= 0:
        raise ValueError("oracle triangle must be counterclockwise")
    for index in range(3):
        start, end = triangle[index], triangle[(index+1) % 3]
        edge = end-start
        source = output
        output = []
        if not source:
            break
        for first, second in zip(source, source[1:]+source[:1]):
            first_side = _cross(edge, first-start)
            second_side = _cross(edge, second-start)
            first_inside = first_side >= -1e-14
            second_inside = second_side >= -1e-14
            if first_inside != second_inside:
                fraction = first_side/(first_side-second_side)
                output.append(first + fraction*(second-first))
            if second_inside:
                output.append(second)
    return np.asarray(output).reshape(-1, 2)


def _triangle_quadrature(vertices: np.ndarray):
    """Integrate polynomials of sufficient degree via a tensor Gauss map."""
    roots, weights = np.polynomial.legendre.leggauss(4)
    roots = 0.5*(roots+1)
    weights = 0.5*weights
    origin, first, second = vertices
    jacobian = abs(_cross(first-origin, second-origin))
    for u, wu in zip(roots, weights):
        for v, wv in zip(roots, weights):
            point = origin+u*(first-origin)+(1-u)*v*(second-origin)
            yield point, float(wu*wv*(1-u)*jacobian)


def _source_shape(point: np.ndarray, corners: np.ndarray) -> np.ndarray:
    x0, y0 = corners[0]
    y1 = corners[2, 1]
    eta = (point[1]-y0)/(y1-y0)
    left = (1-eta)*x0+eta*corners[3, 0]
    right = (1-eta)*corners[1, 0]+eta*corners[2, 0]
    xi = (point[0]-left)/(right-left)
    return np.array(((1-xi)*(1-eta), xi*(1-eta), xi*eta,
                     (1-xi)*eta))


def _target_shape(point: np.ndarray, triangle: np.ndarray) -> np.ndarray:
    a, b, c = triangle
    denominator = _cross(b-a, c-a)
    beta = _cross(point-a, c-a)/denominator
    gamma = _cross(b-a, point-a)/denominator
    return np.array((1-beta-gamma, beta, gamma))


def independent_gap_work(model, definition, source_shift_x: float,
                         target_skin_xy: dict[int, np.ndarray] | None = None,
                         source_skin_xy: dict[int, np.ndarray] | None = None):
    """Return reference support and the full-coordinate weighted gap map."""
    source_ids = sorted({node for element_id in definition.surfaces[0].element_ids
                         for node in model.mesh.elements[element_id].node_ids})
    target_ids = sorted({node for element_id in definition.surfaces[1].element_ids
                         for node in model.mesh.elements[element_id].node_ids})
    index = {node: row for row, node in enumerate(source_ids)}
    ndof = model.mesh.dof_manager.total_dofs
    support = np.zeros(len(source_ids))
    work = np.zeros((len(source_ids), ndof))
    integrated_area = 0.0
    for source_element_id in definition.surfaces[0].element_ids:
        source_element = model.mesh.elements[source_element_id]
        source_nodes = tuple(source_element.node_ids)
        source_xy = np.array([
            ((model.mesh.nodes[node].x+source_shift_x,
              model.mesh.nodes[node].y)
             if source_skin_xy is None else source_skin_xy[node])
            for node in source_nodes])
        if not (abs(source_xy[0, 1]-source_xy[1, 1]) < 1e-13
                and abs(source_xy[2, 1]-source_xy[3, 1]) < 1e-13):
            raise ValueError("oracle admits horizontal Q4 rows only")
        for target_element_id in definition.surfaces[1].element_ids:
            target_element = model.mesh.elements[target_element_id]
            target_nodes = tuple(target_element.node_ids)
            target_xy = np.array([
                ((model.mesh.nodes[node].x, model.mesh.nodes[node].y)
                 if target_skin_xy is None else target_skin_xy[node])
                for node in target_nodes])
            polygon = _clip(source_xy, target_xy)
            if len(polygon) < 3:
                continue
            for fan in range(1, len(polygon)-1):
                triangle = np.asarray((polygon[0], polygon[fan],
                                       polygon[fan+1]))
                if abs(_cross(triangle[1]-triangle[0],
                              triangle[2]-triangle[0])) < 1e-16:
                    continue
                for point, weight in _triangle_quadrature(triangle):
                    source_shape = _source_shape(point, source_xy)
                    target_shape = _target_shape(point, target_xy)
                    integrated_area += weight
                    for local_pressure, source_node in enumerate(source_nodes):
                        row = index[source_node]
                        mass = weight*source_shape[local_pressure]
                        support[row] += mass
                        for local_displacement, node in enumerate(source_nodes):
                            dof = model.mesh.dof_manager.get_node_dofs(node)[2]
                            work[row, dof] += mass*source_shape[local_displacement]
                        for local_displacement, node in enumerate(target_nodes):
                            dof = model.mesh.dof_manager.get_node_dofs(node)[2]
                            work[row, dof] -= mass*target_shape[local_displacement]
    if np.min(support) <= 0.0:
        raise ValueError("oracle needs positive support on every pressure node")
    if abs(np.sum(support)-integrated_area) > 1e-12:
        raise AssertionError("oracle partition of unity failed")
    return tuple(source_ids), support, work, integrated_area


def solve_reference(model, definition, program, accepted_step: int,
                    target_skin_xy: dict[int, np.ndarray] | None = None,
                    source_skin_xy: dict[int, np.ndarray] | None = None):
    """Solve the small linearized two-body contact KKT system."""
    controls = program.target_at(accepted_step)
    if len(controls) != 2 or abs(controls[0]-controls[1]) > 1e-14:
        raise ValueError("oracle requires equal prescribed source x motion")
    model.apply_boundary_conditions()
    stiffness, _ = assemble_stiffness_matrix(model)
    ndof = model.mesh.dof_manager.total_dofs
    _, _, transform, offset, _, _ = build_constraint_transformation(
        stiffness, np.zeros(ndof), model)
    if np.linalg.norm(offset) != 0.0:
        raise ValueError("oracle requires zero model boundary values")
    source_ids, support, work, area = independent_gap_work(
        model, definition, float(controls[0]), target_skin_xy,
        source_skin_xy)
    source_element = model.mesh.elements[definition.surfaces[0].element_ids[0]]
    target_element = model.mesh.elements[definition.surfaces[1].element_ids[0]]
    source_node = model.mesh.nodes[source_element.node_ids[0]]
    target_node = model.mesh.nodes[target_element.node_ids[0]]
    source_skin_z = source_node.z-0.5*source_element.thickness
    target_skin_z = (target_node.z+0.5*target_element.thickness
                     -target_element.reference_surface_offset)
    initial_gap = source_skin_z-target_skin_z
    assert abs(initial_gap-40e-6) < 1e-12
    external = np.zeros(ndof)
    for force, value in zip(program.nodal_forces,
                            program.force_values_at(accepted_step), strict=True):
        assert force.dof == "uz"
        dof = model.mesh.dof_manager.get_node_dofs(force.node_id)[2]
        external[dof] += value
    control_rows = np.zeros((len(program.controls), ndof))
    for row, control in enumerate(program.controls):
        for node, name, weight in control.terms:
            assert name == "ux"
            dof = model.mesh.dof_manager.get_node_dofs(node)[0]
            control_rows[row, dof] += weight
    reduced_k = (transform.T @ stiffness @ transform).toarray()
    reduced_f = np.asarray(transform.T @ external).reshape(-1)
    reduced_work = np.asarray(work @ transform)
    reduced_controls = np.asarray(control_rows @ transform)
    count = len(support)

    def equilibrate(active):
        selected = np.flatnonzero(active)
        active_work = reduced_work[selected]
        size = len(reduced_f)
        ncontrol = len(controls)
        matrix = np.block([
            [reduced_k, -active_work.T, reduced_controls.T],
            [active_work, np.zeros((len(selected), len(selected))),
             np.zeros((len(selected), ncontrol))],
            [reduced_controls, np.zeros((ncontrol, len(selected))),
             np.zeros((ncontrol, ncontrol))],
        ])
        rhs = np.r_[reduced_f, -initial_gap*support[selected], controls]
        solved = np.linalg.solve(matrix, rhs)
        pressure = np.zeros(count)
        pressure[selected] = solved[size:size+len(selected)]
        return solved[:size], pressure, solved[size+len(selected):]

    active = np.zeros(count, dtype=bool)
    for iteration in range(30):
        coordinates, pressure, control_reactions = equilibrate(active)
        normalized_gap = initial_gap+(reduced_work @ coordinates)/support
        updated = (pressure-definition.interactions[0].normal_stiffness
                   *normalized_gap) > 0.0
        if np.array_equal(updated, active):
            break
        active = updated
    else:
        raise RuntimeError("oracle active set did not converge")
    equilibrium = (reduced_k @ coordinates-reduced_f
                   -reduced_work.T @ pressure
                   +reduced_controls.T @ control_reactions)
    assert np.linalg.norm(equilibrium) < 1e-8
    assert np.min(pressure) > -1e-8
    assert np.min(normalized_gap) > -1e-8
    assert np.max(abs(pressure*normalized_gap)) < 1e-8
    return {
        "displacement": np.asarray(transform @ coordinates).reshape(-1),
        "pressure": pressure,
        "support": support,
        "weighted_gap_work": work,
        "normalized_gap": normalized_gap,
        "control_reactions": control_reactions,
        "source_pressure_nodes": source_ids,
        "integrated_area": area,
        "integrated_force": float(support @ pressure),
        "initial_gap": initial_gap,
        "active_set_iterations": iteration+1,
    }
