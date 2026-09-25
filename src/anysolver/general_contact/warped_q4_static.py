"""Narrow, opt-in small-rotation warped Q4 contact with a rigid plane.

This development profile uses the qualified Q4's reference varying frame and
the ordinary nonlinear static transaction. It does not admit finite rotations
or deformable paired warped surfaces.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

from .warped_q4_plane import WarpedQ4PlaneMortar
from .warped_q4_skin import WarpedQ4Skin


PROFILE = "WARPED_Q4_RIGID_PLANE_SMALL_ROTATION_PENALTY_MORTAR_STATIC_DEV_V0"

_REQUIRED_SETTINGS = (
    "warped_q4_quadrature_order", "warped_q4_control_order",
    "warped_q4_integration_tolerance", "warped_q4_gap_accuracy",
    "warped_q4_maximum_gap_cells", "warped_q4_maximum_gap_depth",
)


def validate_warped_q4_plane(model, definition, settings, *, analysis_control="force"):
    from .core import ContactValidationReport
    from anysolver.e4_pl_element import QualifiedE4PLShellElement

    issues = []
    if (len(definition.surfaces) != 1 or len(definition.rigid_bodies) != 1
            or len(definition.interactions) != 1):
        issues.append("warped Q4 plane profile needs one surface, plane and interaction")
    if settings.pair_motion != "guided" or settings.normal_discretization != "primal_mortar":
        issues.append("warped Q4 plane profile needs guided primal mortar settings")
    if settings.maximum_shell_tilt is None:
        issues.append("warped Q4 plane profile needs explicit maximum_shell_tilt in radians")
    missing = [name for name in _REQUIRED_SETTINGS if getattr(settings, name) is None]
    if missing:
        issues.append("warped Q4 plane profile needs explicit " + ", ".join(missing))
    elif settings.warped_q4_control_order <= settings.warped_q4_quadrature_order:
        issues.append("warped Q4 control quadrature must exceed work quadrature")
    if settings.warped_q4_control_order is not None and settings.warped_q4_control_order > 32:
        issues.append("warped Q4 control quadrature may not exceed order 32")
    if len(definition.surfaces) == 1:
        surface = definition.surfaces[0]
        if surface.beam_radius is not None or len(surface.element_ids) != 1:
            issues.append("warped Q4 plane profile needs exactly one shell Q4 face")
        elif type(model.mesh.elements.get(surface.element_ids[0])) is not QualifiedE4PLShellElement:
            issues.append("warped Q4 plane profile needs an exact qualified Q4 formulation")
        else:
            try:
                WarpedQ4Skin(model, surface.element_ids[0], surface.side)
            except ValueError as exc:
                issues.append(str(exc))
    if len(definition.rigid_bodies) == 1 and definition.rigid_bodies[0].kind != "plane":
        issues.append("warped Q4 profile needs an analytic rigid plane")
    if len(definition.interactions) == 1:
        interaction = definition.interactions[0]
        if interaction.normal_law != "penalty" or interaction.normal_stiffness is None:
            issues.append("warped Q4 profile needs explicit pressure penalty stiffness")
        if interaction.line_stiffness is not None or interaction.endpoint_stiffness is not None:
            issues.append("warped Q4 profile does not use line or endpoint stiffness")
        if (len(definition.surfaces) == 1 and len(definition.rigid_bodies) == 1
                and (interaction.surface != definition.surfaces[0].name
                     or interaction.target != definition.rigid_bodies[0].name)):
            issues.append("warped Q4 interaction participants do not match")
    if settings.maximum_candidate_pairs < 1:
        issues.append("warped Q4 candidate budget is exhausted")
    return ContactValidationReport("invalid" if issues else "ok", tuple(issues), PROFILE)


class WarpedQ4PlaneManager:
    """Assemble one local mortar law into authoritative global shell DOFs."""

    def __init__(self, model, definition, settings, initial_displacement=None):
        report = validate_warped_q4_plane(model, definition, settings)
        if not report.valid:
            raise ValueError("unsupported warped Q4 plane contact: " + "; ".join(report.issues))
        self.model = model
        self.definition = definition
        self.settings = settings
        self.profile = report.profile
        surface = definition.surfaces[0]
        body = definition.rigid_bodies[0]
        interaction = definition.interactions[0]
        self.skin = WarpedQ4Skin(model, surface.element_ids[0], surface.side)
        self.normal = np.asarray(body.normal, dtype=float)
        self.reference_point = np.asarray(body.point, dtype=float)
        self.path_translation = (np.zeros(3) if body.path_translation is None
                                 else np.asarray(body.path_translation, dtype=float))
        self.path_factor = 0.0
        self.point = self.reference_point.copy()
        self.stiffness = interaction.normal_stiffness
        self.gap_tolerance = interaction.gap_tolerance
        self.swept_trial_cutbacks = 0
        self.dofs = np.asarray([
            model.mesh.dof_manager.get_node_dofs(node_id)[:6]
            for node_id in self.skin.node_ids
        ], dtype=np.intp)
        self.n_dof = model.mesh.dof_manager.total_dofs
        self.law = WarpedQ4PlaneMortar(
            self.skin, self.reference_point, self.normal, self.stiffness,
            quadrature_order=settings.warped_q4_quadrature_order,
            control_order=settings.warped_q4_control_order,
            integration_relative_tolerance=settings.warped_q4_integration_tolerance,
        )
        initial = np.zeros(self.n_dof) if initial_displacement is None else initial_displacement
        initial_gap = self._certificate(initial, self.point)
        scale = max(1.0, float(np.max(np.abs(self.skin.reference))),
                    float(np.max(np.abs(self.point))))
        roundoff = 256.0 * np.finfo(float).eps * scale
        if initial_gap.conservative_lower_gap < -roundoff:
            raise ValueError(
                f"initial warped Q4 plane gap is unresolved or overclosed: "
                f"lower bound {initial_gap.conservative_lower_gap:.6g} m; "
                f"sample {initial_gap.minimum_sampled_gap:.6g} m"
            )

    def restart_contract(self):
        surface = self.definition.surfaces[0]
        body = self.definition.rigid_bodies[0]
        interaction = self.definition.interactions[0]
        return {
            "profile": self.profile,
            "surface": {"name": surface.name, "element_ids": list(surface.element_ids),
                        "side": surface.side},
            "rigid_body": {"name": body.name, "kind": body.kind,
                           "point": list(body.point), "normal": list(body.normal),
                           "path_translation": (None if body.path_translation is None
                                                else list(body.path_translation))},
            "interaction": {"name": interaction.name, "surface": interaction.surface,
                            "target": interaction.target,
                            "normal_stiffness": interaction.normal_stiffness,
                            "gap_tolerance": interaction.gap_tolerance,
                            "normal_law": interaction.normal_law},
            "settings": {
                "warped_q4_plane": True,
                "pair_motion": self.settings.pair_motion,
                "normal_discretization": self.settings.normal_discretization,
                "maximum_candidate_pairs": self.settings.maximum_candidate_pairs,
                "maximum_shell_tilt": self.settings.maximum_shell_tilt,
                **{name: getattr(self.settings, name) for name in _REQUIRED_SETTINGS},
            },
        }

    def point_at(self, factor):
        factor = float(factor)
        if not np.isfinite(factor) or factor < 0.0:
            raise ValueError("rigid-plane path factor must be finite and nonnegative")
        point = self.reference_point + factor * self.path_translation
        if not np.all(np.isfinite(point)):
            raise ValueError("rigid-plane path position is nonfinite")
        return point

    def set_path_factor(self, factor):
        point = self.point_at(factor)
        self.path_factor = float(factor)
        self.point = point

    def _coordinates(self, displacement):
        u = np.asarray(displacement, dtype=float).reshape(-1)
        if u.size != self.n_dof or not np.all(np.isfinite(u)):
            raise ValueError("warped Q4 contact displacement has invalid size or values")
        coordinates = u[self.dofs]
        if (np.max(np.linalg.norm(coordinates[:, 3:], axis=1))
                > self.settings.maximum_shell_tilt):
            raise ValueError("warped Q4 small-rotation limit exceeded")
        return coordinates

    def _certificate(self, displacement, point):
        return self.skin.certify_linearized_plane_gap(
            self._coordinates(displacement), point, self.normal,
            accuracy=self.settings.warped_q4_gap_accuracy,
            maximum_cells=self.settings.warped_q4_maximum_gap_cells,
            maximum_depth=self.settings.warped_q4_maximum_gap_depth,
        )

    def evaluate(self, displacement, *, tangent=True):
        coordinates = self._coordinates(displacement)
        plane_normal_translation = float(self.normal @ (self.point - self.reference_point))
        state = self.law.evaluate(
            coordinates, plane_normal_translation=plane_normal_translation,
        )
        certificate = self._certificate(displacement, self.point)
        self.last_gap_certificate = certificate
        dofs = self.dofs.reshape(24)
        force = np.zeros(self.n_dof)
        np.add.at(force, dofs, state.residual.reshape(24))
        stiffness = None
        if tangent:
            local = sparse.coo_matrix(state.tangent)
            stiffness = sparse.coo_matrix(
                (local.data, (dofs[local.row], dofs[local.col])),
                shape=(self.n_dof, self.n_dof),
            ).tocsr()
        local_physical_force = -state.residual[:, :3]
        shell_force = np.sum(local_physical_force, axis=0)
        shell_moment = np.sum(np.cross(
            self.skin.reference + coordinates[:, :3], local_physical_force,
        ) - state.residual[:, 3:], axis=0)
        results = self._results(state, certificate, shell_force, shell_moment)
        return force, stiffness, results

    def _results(self, state, certificate, shell_force, shell_moment):
        from .core import ContactResults

        return ContactResults(
            self.profile, certificate.conservative_lower_gap, state.energy,
            tuple(map(float, shell_force)), tuple(map(float, -shell_force)),
            tuple(map(float, shell_moment)), tuple(map(float, -shell_moment)),
            int(np.count_nonzero(state.normalized_gap < 0.0)),
            certificate.conservative_lower_gap >= -self.gap_tolerance,
        )

    def admissible_step_fraction(self, start, end):
        start_u = np.asarray(start, dtype=float).reshape(-1)
        end_u = np.asarray(end, dtype=float).reshape(-1)
        first = self._certificate(start_u, self.point).conservative_lower_gap
        if end_u.size != self.n_dof or not np.all(np.isfinite(end_u)):
            raise ValueError("warped Q4 trial displacement has invalid size or values")
        first_rotations = start_u[self.dofs][:, 3:]
        end_rotations = end_u[self.dofs][:, 3:]
        cap = self.settings.maximum_shell_tilt
        rotation_fraction = 1.0
        for first_rotation, end_rotation in zip(first_rotations, end_rotations):
            first_norm = float(np.linalg.norm(first_rotation))
            end_norm = float(np.linalg.norm(end_rotation))
            if end_norm > cap:
                rotation_fraction = min(
                    rotation_fraction, (cap - first_norm) / (end_norm - first_norm),
                )
        if rotation_fraction < 1.0:
            rotation_fraction = max(0.0, 0.98 * rotation_fraction)
            self.swept_trial_cutbacks += 1
        clipped_end = start_u + rotation_fraction * (end_u - start_u)
        last = self._certificate(clipped_end, self.point).conservative_lower_gap
        if first < -self.gap_tolerance:
            raise ValueError("committed warped Q4 plane pose exceeds the gap tolerance")
        if last >= -self.gap_tolerance:
            return rotation_fraction
        # The represented gap is affine along the coordinate trial path.
        # A convex combination of two valid lower bounds bounds every point.
        allowed = (first + self.gap_tolerance) / (first - last)
        self.swept_trial_cutbacks += 1
        return max(0.0, min(1.0, rotation_fraction * 0.98 * allowed))

    def swept_increment_admissible(self, start, end, start_factor, end_factor):
        first_point = self.point_at(start_factor)
        last_point = self.point_at(end_factor)
        swept = self.skin.certify_linearized_swept_plane_gap(
            self._coordinates(start), self._coordinates(end),
            first_point, last_point, self.normal,
            accuracy=self.settings.warped_q4_gap_accuracy,
            maximum_cells=self.settings.warped_q4_maximum_gap_cells,
            maximum_depth=self.settings.warped_q4_maximum_gap_depth,
        )
        if swept.start.conservative_lower_gap < -self.gap_tolerance:
            raise ValueError("committed warped Q4 plane pose exceeds the gap tolerance")
        if swept.conservative_lower_gap < -self.gap_tolerance:
            self.swept_trial_cutbacks += 1
            return False
        return True

    def tool_work_increment(self, start, end, start_factor, end_factor):
        if not np.any(self.path_translation):
            return 0.0
        previous = self.path_factor
        try:
            self.set_path_factor(start_factor)
            first_force = np.asarray(self.evaluate(start, tangent=False)[2].rigid_force)
            self.set_path_factor(end_factor)
            last_force = np.asarray(self.evaluate(end, tangent=False)[2].rigid_force)
        finally:
            self.set_path_factor(previous)
        work = float(0.5 * (first_force + last_force)
                     @ ((float(end_factor) - float(start_factor))
                        * self.path_translation))
        if not np.isfinite(work):
            raise ValueError("rigid-plane contact work is nonfinite")
        return work
