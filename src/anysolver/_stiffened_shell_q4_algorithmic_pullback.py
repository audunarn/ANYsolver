"""Explicit Q4 elastic/J2 full-map adapter; ordinary Q4 routes are unchanged."""

import numpy as np

from ._ge_beam3_variational_shell import deformation
from ._stiffened_shell_algorithmic_pullback import spatial_response
from .e4_pl_element import FORMULATION_ID
from .material_curves import DNVC208MaterialCurve


POLICY = "STIFFENED_SHELL_Q4_ALGORITHMIC_PULLBACK_V1"
HISTORICAL_POLICY = "historical_corotational"


def local_coordinates(model, element, displacement, *, rotation_anchors=None):
    reference = np.array([model.mesh.nodes[node].coords() for node in element.node_ids])
    return deformation(reference, displacement, stable_translation=True,
                       rotation_anchors=rotation_anchors)[0]


def response(model, element, displacement, origin, layers, *, rotation_anchors=None):
    """Differentiate the unchanged local update from one accepted predecessor."""
    material = model.get_material(element.material_name)
    curve = material.hardening_curve
    if (getattr(element, "formulation_id", None) != FORMULATION_ID or
            element.num_nodes != 4 or element.shell_section is not None or
            (curve is not None and not isinstance(curve, DNVC208MaterialCurve)) or
            (curve is None and material.yield_stress != 0.) or origin is None):
        raise ValueError("experimental Q4 elastic/isotropic J2 accepted predecessor required")
    reference = np.array([model.mesh.nodes[node].coords() for node in element.node_ids])
    u = np.asarray(displacement, dtype=float)
    local, differential, second = deformation(reference, u, stable_translation=True,
                                              rotation_anchors=rotation_anchors)
    force, tangent, candidate = element.compute_nonlinear_response(
        model.mesh, material, local, origin, layers, True)
    force, tangent = np.asarray(force), np.asarray(tangent)
    if (force.shape != (24,) or tangent.shape != (24, 24) or
            not np.isfinite(force).all() or not np.isfinite(tangent).all() or
            candidate is None):
        raise ValueError("finite Q4 algorithmic trial required")
    residual, spatial_tangent = spatial_response(u, force, tangent, differential, second)
    return residual, spatial_tangent, candidate
