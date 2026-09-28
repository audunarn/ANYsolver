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
from d1_two_body_reference_oracle import (
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


path = Path(__file__).with_name("d1_two_body_reference_compare_full_20260928.json")
saved_bytes = path.read_bytes()
saved = json.loads(saved_bytes)
assert saved["production_status"] == "completed"
assert saved["production_accepted_steps"] == 4
model, definition, _settings, _program = build_free_target_case(
    4, steps_per_segment=2, four_phase=True,
    enforcement_solver="monolithic_active_set",
)
pose = np.asarray(saved["production_displacements"])
assert pose.shape == (model.mesh.dof_manager.total_dofs,)
pressure_nodes = sorted({node for element_id in definition.surfaces[0].element_ids
                         for node in model.mesh.elements[element_id].node_ids})
pressure_index = {node: index for index, node in enumerate(pressure_nodes)}
support = np.zeros(len(pressure_nodes))
weighted_gap = np.zeros(len(pressure_nodes))
current_xy_area = 0.0
quadrature_points = 0
for source_id in definition.surfaces[0].element_ids:
    source_element = model.mesh.elements[source_id]
    reference_source, current_source = physical_vertices(
        model, source_element, pose, "bottom")
    source_xy = current_source[:, :2]
    assert np.max(abs(source_xy[[0, 1], 1]-source_xy[0, 1])) < 1e-12
    assert np.max(abs(source_xy[[2, 3], 1]-source_xy[2, 1])) < 1e-12
    for target_id in definition.surfaces[1].element_ids:
        target_element = model.mesh.elements[target_id]
        _reference_target, current_target = physical_vertices(
            model, target_element, pose, "top")
        polygon = _clip(source_xy, current_target[:, :2])
        for fan in range(1, len(polygon)-1):
            triangle = polygon[[0, fan, fan+1]]
            for point, weight in _triangle_quadrature(triangle):
                source_shape = _source_shape(point, source_xy)
                target_shape = _target_shape(point, current_target[:, :2])
                xi = source_shape[1]+source_shape[2]
                eta = source_shape[2]+source_shape[3]
                assert np.max(abs(source_shape-q4_shape(xi, eta))) < 1e-12
                dx, dy = q4_derivatives(current_source, xi, eta)
                rdx, rdy = q4_derivatives(reference_source, xi, eta)
                physical_normal = np.cross(dx, dy)
                projected_jacobian = float(physical_normal[2])
                assert projected_jacobian > 0
                reference_jacobian = float(np.linalg.norm(np.cross(rdx, rdy)))
                physical_normal /= np.linalg.norm(physical_normal)
                source_point = source_shape @ current_source
                target_point = target_shape @ current_target
                gap = float(physical_normal @ (source_point-target_point))
                reference_weight = weight*reference_jacobian/projected_jacobian
                for local, node in enumerate(source_element.node_ids):
                    index = pressure_index[node]
                    value = reference_weight*source_shape[local]
                    support[index] += value
                    weighted_gap[index] += value*gap
                current_xy_area += weight
                quadrature_points += 1
assert np.all(support > 0)
saved_support = np.asarray(saved["production_support_m2"])
saved_gap = np.asarray(saved["production_normalized_gap_m"])
normalized_gap = weighted_gap/support
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
    "independent_support_m2": support.tolist(),
    "independent_normalized_gap_m": normalized_gap.tolist(),
}
print(json.dumps(record, indent=2))
