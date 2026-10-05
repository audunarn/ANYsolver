"""Independent current-skin Q4/S3 mortar values at one saved slide pose.

The quadrature uses current XY clipping and the source reference-area measure.
It does not call the production contact geometry or derivative kernel.
"""

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np

import anysolver
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from docs.d1_review_support.d1_two_body_reference_oracle import (
    _clip, _source_shape, _target_shape, _triangle_quadrature,
)
from scripts.general_contact_d1_free_target_press_probe import build_free_target_case


def physical_vertices(model, element, displacement, side):
    nodes = [model.mesh.nodes[node] for node in element.node_ids]
    reference = np.asarray([(node.x, node.y, node.z) for node in nodes])
    if side == "bottom":
        assert len(nodes) == 4
        director = np.cross(reference[1]-reference[0],
                            reference[3]-reference[0])
        director /= np.linalg.norm(director)
        offset = -0.5*element.thickness
    else:
        assert side == "top" and len(nodes) == 3
        director = (np.asarray(element.reference_normal)
                    *element.director_polarity)
        offset = 0.5*element.thickness-element.reference_surface_offset
    current = []
    for node, point in zip(element.node_ids, reference, strict=True):
        dofs = model.mesh.dof_manager.get_node_dofs(node)
        current.append(point+displacement[dofs[:3]]
                       +offset*(director+np.cross(displacement[dofs[3:6]],
                                                       director)))
    return reference+offset*director, np.asarray(current)


def q4_shape(xi, eta):
    return np.array(((1-xi)*(1-eta), xi*(1-eta), xi*eta,
                     (1-xi)*eta))


def q4_derivatives(vertices, xi, eta):
    along_x = (1-eta)*(vertices[1]-vertices[0]) \
              +eta*(vertices[2]-vertices[3])
    along_y = (1-xi)*(vertices[3]-vertices[0]) \
              +xi*(vertices[2]-vertices[1])
    return along_x, along_y


def source_shape_current_xy(point, vertices):
    """Invert a convex bilinear Q4 independently in the projected plane."""
    xi = eta = 0.5
    for _ in range(12):
        shape = q4_shape(xi, eta)
        difference = shape @ vertices-point
        dx, dy = q4_derivatives(vertices, xi, eta)
        correction = np.linalg.solve(np.column_stack((dx, dy)), difference)
        xi -= float(correction[0])
        eta -= float(correction[1])
        if np.linalg.norm(correction, ord=np.inf) < 2e-14:
            break
    if (not -1e-10 <= xi <= 1+1e-10
            or not -1e-10 <= eta <= 1+1e-10
            or np.linalg.norm(q4_shape(xi, eta) @ vertices-point,
                              ord=np.inf) > 1e-11):
        raise ValueError("independent current Q4 inverse failed")
    return q4_shape(xi, eta)


def overlap_incidence(source_xy, target_xy, polygon):
    """Identify the source and target edges incident to clipped vertices.

    This is an oracle branch signature, not a physical contact-feature label.
    Cyclic normalization removes the arbitrary starting corner of the clipper
    while retaining vertex order around the overlap.
    """
    length = max(float(np.linalg.norm(np.roll(vertices, -1, axis=0)
                                      -vertices, axis=1).max())
                 for vertices in (source_xy, target_xy))
    tolerance = 1e-10*length

    def edges_at(point, vertices):
        matches = []
        for edge_id, start in enumerate(vertices):
            edge = vertices[(edge_id+1) % len(vertices)]-start
            edge_length = float(np.linalg.norm(edge))
            if edge_length <= 0:
                raise ValueError("degenerate oracle polygon edge")
            along = float(np.dot(point-start, edge))/edge_length
            distance = abs(float(np.linalg.det(np.stack((edge, point-start))))) / edge_length
            if (distance <= tolerance
                    and -tolerance <= along <= edge_length+tolerance):
                matches.append(edge_id)
        return tuple(matches)

    incidences = []
    for point in polygon:
        source_edges = edges_at(point, source_xy)
        target_edges = edges_at(point, target_xy)
        if not source_edges and not target_edges:
            raise AssertionError("clipped vertex has no parent edge")
        incidences.append((source_edges, target_edges))
    if not incidences:
        return (0, ())
    rotations = (tuple(incidences[index:]+incidences[:index])
                 for index in range(len(incidences)))
    return (len(polygon), min(rotations))


def integrate_current_skin(model, definition, pose, *, pressure_gram=False,
                           support_by_source_face=False):
    pressure_nodes = sorted({
        node for element_id in definition.surfaces[0].element_ids
        for node in model.mesh.elements[element_id].node_ids
    })
    pressure_index = {node: index for index, node in enumerate(pressure_nodes)}
    support = np.zeros(len(pressure_nodes))
    weighted_gap = np.zeros(len(pressure_nodes))
    gram = (np.zeros((len(pressure_nodes), len(pressure_nodes)))
            if pressure_gram else None)
    face_support = (np.zeros((len(definition.surfaces[0].element_ids),
                              len(pressure_nodes)))
                    if support_by_source_face else None)
    current_xy_area = 0.0
    quadrature_points = 0
    topology = []
    for source_index, source_id in enumerate(definition.surfaces[0].element_ids):
        source_element = model.mesh.elements[source_id]
        reference_source, current_source = physical_vertices(
            model, source_element, pose, "bottom")
        source_xy = current_source[:, :2]
        for target_id in definition.surfaces[1].element_ids:
            target_element = model.mesh.elements[target_id]
            _reference_target, current_target = physical_vertices(
                model, target_element, pose, "top")
            polygon = _clip(source_xy, current_target[:, :2])
            topology.append((int(source_id), int(target_id), overlap_incidence(
                source_xy, current_target[:, :2], polygon)))
            for fan in range(1, len(polygon)-1):
                triangle = polygon[[0, fan, fan+1]]
                for point, weight in _triangle_quadrature(triangle):
                    source_shape = source_shape_current_xy(point, source_xy)
                    target_shape = _target_shape(point, current_target[:, :2])
                    xi = source_shape[1]+source_shape[2]
                    eta = source_shape[2]+source_shape[3]
                    assert np.max(abs(source_shape-q4_shape(xi, eta))) < 1e-12
                    dx, dy = q4_derivatives(current_source, xi, eta)
                    rdx, rdy = q4_derivatives(reference_source, xi, eta)
                    physical_normal = np.cross(dx, dy)
                    projected_jacobian = float(physical_normal[2])
                    assert projected_jacobian > 0
                    reference_jacobian = float(np.linalg.norm(
                        np.cross(rdx, rdy)))
                    physical_normal /= np.linalg.norm(physical_normal)
                    source_point = source_shape @ current_source
                    target_point = target_shape @ current_target
                    gap = float(physical_normal @ (source_point-target_point))
                    reference_weight = (weight*reference_jacobian
                                        /projected_jacobian)
                    for local, node in enumerate(source_element.node_ids):
                        index = pressure_index[node]
                        value = reference_weight*source_shape[local]
                        support[index] += value
                        if face_support is not None:
                            face_support[source_index, index] += value
                        weighted_gap[index] += value*gap
                    if gram is not None:
                        indices = [pressure_index[node]
                                   for node in source_element.node_ids]
                        gram[np.ix_(indices, indices)] += (
                            reference_weight*np.outer(source_shape,
                                                      source_shape))
                    current_xy_area += weight
                    quadrature_points += 1
    assert np.all(support > 0)
    result = (support, weighted_gap, current_xy_area, quadrature_points,
              tuple(topology))
    if gram is not None:
        result = (*result, gram)
    if face_support is not None:
        result = (*result, face_support)
    return result


def main():
    path = Path(__file__).with_name("d1_two_body_reference_compare_full_20260928.json")
    saved_bytes = path.read_bytes()
    saved = json.loads(saved_bytes)
    assert saved["production_status"] == "completed"
    assert saved["production_accepted_steps"] == 4
    model, definition, settings, _program = build_free_target_case(
        4, steps_per_segment=2, four_phase=True,
        enforcement_solver="monolithic_active_set",
    )
    pose = np.asarray(saved["production_displacements"])
    assert pose.shape == (model.mesh.dof_manager.total_dofs,)
    support, weighted_gap, current_xy_area, quadrature_points, signature = (
        integrate_current_skin(model, definition, pose))
    saved_support = np.asarray(saved["production_support_m2"])
    saved_gap = np.asarray(saved["production_normalized_gap_m"])
    normalized_gap = weighted_gap/support
    manager = GeneralS3PatchManager(model, definition, settings)
    pressure = np.asarray(saved["production_pressure_pa"])
    assert tuple(manager.law.pressure_mode_ids) == tuple(sorted({
        node for element_id in definition.surfaces[0].element_ids
        for node in model.mesh.elements[element_id].node_ids
    }))
    base = linearize(manager, pose, pressure*saved_support, tangent=False)
    np.testing.assert_allclose(base.state.reference_support, saved_support,
                               rtol=1e-9, atol=1e-12)
    directions = (
        ("source_4_ux", 4, 0, 2e-6),
        ("source_4_uz", 4, 2, 2e-6),
        ("source_9_ux", 9, 0, 2e-6),
        ("source_9_uz", 9, 2, 2e-6),
        ("target_12_ux", 12, 0, 2e-6),
        ("target_12_uz", 12, 2, 2e-6),
        ("target_12_ry", 12, 4, 2e-5),
        ("target_13_uz", 13, 2, 2e-6),
        ("target_13_ry", 13, 4, 2e-5),
    )
    derivative_checks = []
    for label, node, axis, step in directions:
        dof = int(model.mesh.dof_manager.get_node_dofs(node)[axis])
        plus_pose = pose.copy()
        minus_pose = pose.copy()
        plus_pose[dof] += step
        minus_pose[dof] -= step
        plus_support, plus_weighted, _area, _count, plus_signature = (
            integrate_current_skin(model, definition, plus_pose))
        minus_support, minus_weighted, _area, _count, minus_signature = (
            integrate_current_skin(model, definition, minus_pose))
        assert plus_signature == signature == minus_signature
        independent = ((plus_weighted/plus_support
                        -minus_weighted/minus_support)/(2*step))
        production = base.gap_gradient[:, dof]
        difference = float(np.linalg.norm(independent-production))
        scale = max(float(np.linalg.norm(production)), 1e-8)
        independent_work = float((pressure*saved_support) @ independent)
        production_work = float(-base.force[dof])
        derivative_checks.append({
            "direction": label,
            "step": step,
            "independent_gap_gradient_norm": float(np.linalg.norm(independent)),
            "production_gap_gradient_norm": float(np.linalg.norm(production)),
            "gradient_difference_norm": difference,
            "gradient_scaled_difference": difference/scale,
            "independent_contact_work_derivative": independent_work,
            "production_contact_work_derivative": production_work,
            "contact_work_derivative_difference": abs(
                independent_work-production_work),
        })
    record = {
        "status": "development_independent_current_skin_values_at_saved_slide",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                  text=True).strip(),
        "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
        "oracle_source_sha256": hashlib.sha256(Path(
            "docs/d1_review_support/d1_two_body_reference_oracle.py"
        ).read_bytes()).hexdigest(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "quadrature_points": quadrature_points,
        "current_xy_overlap_area_m2": current_xy_area,
        "reference_overlap_area_m2": float(np.sum(support)),
        "saved_production_reference_overlap_area_m2": float(np.sum(saved_support)),
        "support_relative_l2": float(np.linalg.norm(support-saved_support)
                                     /np.linalg.norm(saved_support)),
        "maximum_normalized_gap_difference_m": float(
            np.max(abs(normalized_gap-saved_gap))),
        "normalized_gap_difference_l2_m": float(np.linalg.norm(
            normalized_gap-saved_gap)),
        "directional_checks": derivative_checks,
        "maximum_scaled_directional_gradient_difference": max(
            item["gradient_scaled_difference"] for item in derivative_checks),
        "maximum_contact_work_derivative_difference": max(
            item["contact_work_derivative_difference"]
            for item in derivative_checks),
        "independent_support_m2": support.tolist(),
        "independent_normalized_gap_m": normalized_gap.tolist(),
    }
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
