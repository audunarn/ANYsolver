"""Experimental objective S3 J2 algorithmic pullback from a fixed predecessor.

The local S3 material update is unchanged. Its algorithmic derivative is pulled
through the full deformational map and converted to spatial residual rows and
additive shell-chart columns. This does not assert a plastic energy potential.
"""

import numpy as np

from ._ge_beam3_pose_joint import _exp_terms
from ._ge_beam3_variational_shell import deformation
from .e4_pl_s3_v2d_element import FORMULATION_ID
from .material_curves import DNVC208MaterialCurve


POLICY = "STIFFENED_SHELL_S3_J2_ALGORITHMIC_PULLBACK_V1"


def local_coordinates(model, element, displacement):
    reference = np.array([model.mesh.nodes[node].coords()
                          for node in element.node_ids])
    return deformation(reference, displacement, stable_translation=True)[0]


def response(model, element, displacement, origin, layers):
    """Return one objective trial and owned local material candidate.

    With d(q), D=dd/dq: g=D.T f and dg/dq=D.T K_alg D+sum(f_i Hess d_i).
    The chart correction differentiates spatial rows, not a symmetrized K_alg.
    Every call uses the caller's same accepted local constitutive predecessor.
    """
    material = model.get_material(element.material_name)
    if (getattr(element, "formulation_id", None) != FORMULATION_ID or
            element.num_nodes != 3 or element.shell_section is not None or
            not isinstance(material.hardening_curve, DNVC208MaterialCurve) or
            origin is None):
        raise ValueError("experimental S3 isotropic J2 accepted predecessor required")
    reference = np.array([model.mesh.nodes[node].coords()
                          for node in element.node_ids])
    u = np.asarray(displacement, dtype=float)
    local, differential, second = deformation(reference, u, stable_translation=True)
    force, tangent, candidate = element.compute_nonlinear_response(
        model.mesh, material, local, origin, layers, True)
    force, tangent = np.asarray(force), np.asarray(tangent)
    if (force.shape != (18,) or tangent.shape != (18, 18) or
            not np.isfinite(force).all() or not np.isfinite(tangent).all() or
            candidate is None):
        raise ValueError("finite S3 J2 algorithmic trial required")
    covector = differential.T@force
    derivative = differential.T@tangent@differential+np.einsum(
        "i,ijk->jk", force, second)
    chart = np.eye(18)
    chart_derivatives = []
    for node, row in enumerate(u.reshape(3, 6)):
        _, jacobian, curvature = _exp_terms(row[3:])
        singular = np.linalg.svd(jacobian, compute_uv=False)
        if singular[-1] <= 1e-11*max(1., singular[0]):
            raise ValueError("singular additive shell chart; owner rebase required")
        slots = slice(6*node+3, 6*node+6)
        chart[slots, slots] = jacobian
        chart_derivatives.append((slots, curvature))
    residual = np.linalg.solve(chart.T, covector)
    correction = np.zeros((18, 18))
    for slots, curvature in chart_derivatives:
        correction[slots, slots] = np.einsum(
            "ijk,i->jk", curvature, residual[slots])
    spatial_tangent = np.linalg.solve(chart.T, derivative-correction)
    return residual, spatial_tangent, candidate
