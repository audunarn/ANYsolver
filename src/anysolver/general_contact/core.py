"""The first opt-in mortar contact profile: qualified planar Q4 and a plane.

The reference-area pressure basis is the element's nonnegative Q1 basis.  At
fixed reference support weights, its penalty potential is the sum of the
positive-part augmented potentials with zero multipliers.  The assembled
force and tangent are derivatives of that same discrete potential.  This is
an intentionally narrow coupled-solver slice, not a general-contact claim.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator

import numpy as np
from scipy import sparse


_Q4_PLANE_PROFILE = "PLANAR_Q4_RIGID_PLANE_PENALTY_MORTAR_V1"
_S3_PLANE_PROFILE = "PLANAR_Q4_S3_RIGID_PLANE_PENALTY_MORTAR_V0"

if TYPE_CHECKING:
    from anysolver.fe_core import FEModel


@dataclass(frozen=True)
class ContactSurface:
    name: str
    element_ids: tuple[int, ...]
    side: str = "midsurface"

    def __post_init__(self) -> None:
        if any(type(value) is not int or value <= 0 for value in self.element_ids):
            raise ValueError("contact element IDs must be positive integers")
        ids = tuple(self.element_ids)
        if not self.name or not ids or len(ids) != len(set(ids)):
            raise ValueError("contact surface requires a name and unique element IDs")
        if self.side not in {"midsurface", "top", "bottom"}:
            raise ValueError("shell side must be midsurface, top, or bottom")
        object.__setattr__(self, "element_ids", ids)


@dataclass(frozen=True)
class RigidContactBody:
    name: str
    kind: str
    point: tuple[float, float, float]
    normal: tuple[float, float, float]

    def __post_init__(self) -> None:
        point = np.asarray(self.point, dtype=float)
        normal = np.asarray(self.normal, dtype=float)
        if not self.name or self.kind != "plane":
            raise ValueError("this contact profile requires a named rigid plane")
        if point.shape != (3,) or normal.shape != (3,) or not (
            np.all(np.isfinite(point)) and np.all(np.isfinite(normal))
        ):
            raise ValueError("plane point and normal must contain three finite values")
        length = float(np.linalg.norm(normal))
        if length <= 0.0:
            raise ValueError("plane normal must be nonzero")
        object.__setattr__(self, "point", tuple(float(x) for x in point))
        object.__setattr__(self, "normal", tuple(float(x) for x in normal / length))


@dataclass(frozen=True)
class ContactInteraction:
    name: str
    surface: str
    target: str
    normal_stiffness: float
    gap_tolerance: float
    normal_law: str = "penalty"

    def __post_init__(self) -> None:
        if not self.name or not self.surface or not self.target:
            raise ValueError("contact interaction needs a name and two participants")
        if self.normal_law != "penalty":
            raise ValueError("only the penalty specialization is implemented")
        for name in ("normal_stiffness", "gap_tolerance"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class ContactDefinition:
    surfaces: tuple[ContactSurface, ...]
    rigid_bodies: tuple[RigidContactBody, ...]
    interactions: tuple[ContactInteraction, ...]

    def __post_init__(self) -> None:
        for name in ("surfaces", "rigid_bodies", "interactions"):
            values = tuple(getattr(self, name))
            if (name != "rigid_bodies" and not values) or len({value.name for value in values}) != len(values):
                raise ValueError(f"{name} must have unique names and be nonempty when required")
            object.__setattr__(self, name, values)
        participant_names = [item.name for item in (*self.surfaces, *self.rigid_bodies)]
        if len(participant_names) != len(set(participant_names)):
            raise ValueError("surface and rigid-body names must be distinct")


@dataclass(frozen=True)
class ContactSolverSettings:
    """Explicit resource and restricted-pair controls, versioned with the profile."""

    maximum_candidate_pairs: int = 100_000
    pair_motion: str = "guided"
    sliding_difference_step: float | None = None
    maximum_gap_triangles: int = 10_000
    maximum_patch_normal_dofs: int = 256

    def __post_init__(self) -> None:
        if type(self.maximum_candidate_pairs) is not int or self.maximum_candidate_pairs < 1:
            raise ValueError("maximum_candidate_pairs must be a positive integer")
        if self.pair_motion not in {"guided", "restricted_sliding"}:
            raise ValueError("pair_motion must be guided or restricted_sliding")
        if self.sliding_difference_step is not None and (
            not np.isfinite(self.sliding_difference_step)
            or self.sliding_difference_step <= 0.0
        ):
            raise ValueError("sliding_difference_step must be finite and positive")
        if type(self.maximum_gap_triangles) is not int or self.maximum_gap_triangles < 1:
            raise ValueError("maximum_gap_triangles must be a positive integer")
        if type(self.maximum_patch_normal_dofs) is not int or self.maximum_patch_normal_dofs < 1:
            raise ValueError("maximum_patch_normal_dofs must be a positive integer")
        if self.pair_motion == "restricted_sliding" and self.sliding_difference_step is None:
            raise ValueError("restricted sliding requires an explicit sliding_difference_step")
        if self.pair_motion == "guided" and self.sliding_difference_step is not None:
            raise ValueError("sliding_difference_step requires restricted_sliding pair_motion")


@dataclass(frozen=True)
class ContactValidationReport:
    status: str
    issues: tuple[str, ...]
    profile: str = "PLANAR_Q4_RIGID_PLANE_PENALTY_MORTAR_V1"

    @property
    def valid(self) -> bool:
        return self.status == "ok"


@dataclass(frozen=True)
class ContactResults:
    profile: str
    minimum_gap: float
    penalty_energy: float
    shell_force: tuple[float, float, float]
    rigid_force: tuple[float, float, float]
    shell_moment: tuple[float, float, float]
    rigid_moment: tuple[float, float, float]
    active_pressure_dofs: int
    gap_tolerance_met: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "minimum_gap": self.minimum_gap,
            "penalty_energy": self.penalty_energy,
            "shell_force": list(self.shell_force),
            "rigid_force": list(self.rigid_force),
            "shell_moment": list(self.shell_moment),
            "rigid_moment": list(self.rigid_moment),
            "active_pressure_dofs": self.active_pressure_dofs,
            "gap_tolerance_met": self.gap_tolerance_met,
        }


def validate_general_contact(model: FEModel, definition: ContactDefinition,
                             settings: ContactSolverSettings | None = None) -> ContactValidationReport:
    """Report every unsupported feature before contact changes the solve."""

    issues: list[str] = []
    if type(definition) is not ContactDefinition:
        return ContactValidationReport("invalid", ("ContactDefinition required",))
    if settings is not None and type(settings) is not ContactSolverSettings:
        return ContactValidationReport("invalid", ("ContactSolverSettings required",))
    if not definition.rigid_bodies:
        if settings is not None and settings.pair_motion == "restricted_sliding":
            if len(definition.surfaces) == 2 and any(
                len(surface.element_ids) > 1 for surface in definition.surfaces
            ):
                from .patch_sliding import validate_restricted_sliding_patch

                return validate_restricted_sliding_patch(model, definition, settings)
            from .sliding import validate_restricted_sliding_pair

            return validate_restricted_sliding_pair(model, definition)
        from .pair import validate_planar_shell_pair

        return validate_planar_shell_pair(model, definition)
    if settings is not None and settings.pair_motion != "guided":
        return ContactValidationReport("invalid", ("rigid contact does not support pair_motion",))
    surface_by_name = {surface.name: surface for surface in definition.surfaces}
    rigid_by_name = {body.name: body for body in definition.rigid_bodies}
    if tuple(map(len, (definition.surfaces, definition.rigid_bodies,
                       definition.interactions))) != (1, 1, 1):
        issues.append("this profile requires exactly one surface, one plane, and one interaction")
    from anysolver.e4_pl_element import FORMULATION_ID as q4_formulation
    from anysolver.e4_pl_s3_v2d_element import FORMULATION_ID as s3_formulation

    contains_s3 = False

    for surface in definition.surfaces:
        for element_id in surface.element_ids:
            element = model.mesh.elements.get(element_id)
            if element is None:
                issues.append(f"surface {surface.name}: missing element {element_id}")
                continue
            formulation = getattr(element, "formulation_id", None)
            if formulation not in {q4_formulation, s3_formulation}:
                issues.append(f"surface {surface.name}: element {element_id} is not admitted Q4/S3")
                continue
            if formulation == s3_formulation:
                contains_s3 = True
                try:
                    from .overlap import reference_shell_face

                    reference_shell_face(model, 1, element_id, surface.side)
                except ValueError as exc:
                    issues.append(f"surface {surface.name}: {exc}")
                continue
            coordinates = np.asarray(element.get_node_coordinates(model.mesh), dtype=float)
            diagonal = max(float(np.linalg.norm(coordinates[i] - coordinates[j]))
                           for i in range(4) for j in range(i))
            normal = np.cross(coordinates[1] - coordinates[0], coordinates[3] - coordinates[0])
            area = float(np.linalg.norm(normal))
            if area <= 1.0e-14 * diagonal * diagonal:
                issues.append(f"surface {surface.name}: element {element_id} is degenerate")
            elif abs(float((coordinates[2] - coordinates[0]) @ normal)) / area > 1.0e-10 * diagonal:
                issues.append(f"surface {surface.name}: warped Q4 element {element_id} is not yet admitted")
    for interaction in definition.interactions:
        if interaction.surface not in surface_by_name or interaction.target not in rigid_by_name:
            issues.append(f"interaction {interaction.name}: missing surface or rigid body")
    profile = _S3_PLANE_PROFILE if contains_s3 else _Q4_PLANE_PROFILE
    return ContactValidationReport("invalid" if issues else "ok", tuple(issues), profile)


class _PlanarQ4PlaneManager:
    def __init__(self, model: FEModel, definition: ContactDefinition,
                 settings: ContactSolverSettings | None = None,
                 initial_displacement: np.ndarray | None = None):
        report = validate_general_contact(model, definition)
        if not report.valid or not definition.rigid_bodies:
            raise ValueError("unsupported general contact: " + "; ".join(report.issues))
        self.model = model
        self.definition = definition
        self.profile = report.profile
        settings = ContactSolverSettings() if settings is None else settings
        self.settings = settings
        interaction = definition.interactions[0]
        surface = next(item for item in definition.surfaces if item.name == interaction.surface)
        if len(surface.element_ids) > settings.maximum_candidate_pairs:
            raise MemoryError("contact candidate limit exceeded; no pair was discarded")
        body = next(item for item in definition.rigid_bodies if item.name == interaction.target)
        self.stiffness = interaction.normal_stiffness
        self.gap_tolerance = interaction.gap_tolerance
        self.swept_trial_cutbacks = 0
        self.normal = np.asarray(body.normal, dtype=float)
        self.point = np.asarray(body.point, dtype=float)
        node_ids = sorted({int(node_id) for element_id in surface.element_ids
                           for node_id in model.mesh.elements[element_id].node_ids})
        pressure_index = {node_id: index for index, node_id in enumerate(node_ids)}
        self.output_nodes = tuple(
            (np.asarray(model.mesh.get_node(node_id).coords(), dtype=float),
             np.asarray(model.mesh.dof_manager.get_node_dofs(node_id)[:6], dtype=np.intp))
            for node_id in node_ids
        )
        n_dof = model.mesh.dof_manager.total_dofs
        support = np.zeros(len(node_ids), dtype=float)
        reference_weighted_gap = np.zeros(len(node_ids), dtype=float)
        rows: list[int] = []
        cols: list[int] = []
        data: list[float] = []
        self.patches = []
        contact_length_scale = 0.0
        from anysolver.e4_pl_s3_v2d_element import FORMULATION_ID as s3_formulation

        for element_id in surface.element_ids:
            element = model.mesh.elements[element_id]
            reference = np.asarray(element.get_node_coordinates(model.mesh), dtype=float)
            contact_length_scale = max(
                contact_length_scale,
                float(np.max(np.linalg.norm(reference - reference[0], axis=1))),
            )
            dofs = np.asarray(
                [model.mesh.dof_manager.get_node_dofs(int(node_id))[:6]
                 for node_id in element.node_ids], dtype=np.intp
            )
            normal = np.cross(reference[1] - reference[0], reference[-1] - reference[0])
            normal /= np.linalg.norm(normal)
            director = element.physical_reference_director
            if director is not None:
                normal = np.asarray(director, dtype=float)
            coordinate = {"midsurface": 0.0, "top": 1.0, "bottom": -1.0}[surface.side]
            if element.formulation_id == s3_formulation:
                offset = float(element.material_surface_offset_from_reference(coordinate))
            else:
                offset = 0.5 * coordinate * float(element.thickness)
            local_gap_gradient = np.r_[self.normal, offset * np.cross(normal, self.normal)]
            weights = []
            shapes = []
            for local, weight in zip(element.gauss_points, element.gauss_weights):
                if element.formulation_id == s3_formulation:
                    N, dxi, deta = element.compute_native_surface_shape_functions(
                        float(local[0]), float(local[1])
                    )
                else:
                    N, dxi, deta = element.compute_shape_functions(
                        float(local[0]), float(local[1])
                    )
                jacobian = float(np.linalg.norm(np.cross(dxi @ reference, deta @ reference)))
                if not np.isfinite(jacobian) or jacobian <= 0.0:
                    raise ValueError(f"contact element {element_id} has invalid reference measure")
                weights.append(float(weight) * jacobian)
                shapes.append(N)
            N = np.asarray(shapes, dtype=float)
            w = np.asarray(weights, dtype=float)
            element_support = N.T @ w
            if np.any(element_support <= 0.0):
                raise ValueError(f"contact element {element_id} has nonpositive pressure support")
            overlap = N.T @ (w[:, None] * N)
            reference_gap = (reference + offset * normal - self.point) @ self.normal
            for a, node_id_a in enumerate(element.node_ids):
                pressure_row = pressure_index[int(node_id_a)]
                support[pressure_row] += float(element_support[a])
                reference_weighted_gap[pressure_row] += float(overlap[a] @ reference_gap)
                for i in range(len(element.node_ids)):
                    for component in range(6):
                        coefficient = float(overlap[a, i] * local_gap_gradient[component])
                        if coefficient:
                            rows.append(pressure_row)
                            cols.append(int(dofs[i, component]))
                            data.append(coefficient)
            self.patches.append((reference, dofs, N, offset * normal,
                                 local_gap_gradient))
        if np.any(support <= 0.0):
            raise ValueError("contact pressure support must be positive")
        self.support = support
        reference_weighted_gap[
            np.abs(reference_weighted_gap)
            <= 256.0 * np.finfo(float).eps * contact_length_scale * support
        ] = 0.0
        self.reference_weighted_gap = reference_weighted_gap
        self.gap_gradient = sparse.coo_matrix(
            (data, (rows, cols)), shape=(len(node_ids), n_dof)
        ).tocsr()
        initial_u = (np.zeros(model.mesh.dof_manager.total_dofs)
                     if initial_displacement is None else initial_displacement)
        initial = self.evaluate(initial_u, tangent=False)[2]
        reference_scale = max(
            1.0,
            float(np.linalg.norm(self.point)),
            *(float(np.linalg.norm(reference)) for reference, _ in self.output_nodes),
        )
        roundoff = 64.0 * np.finfo(float).eps * reference_scale
        if initial.minimum_gap < -roundoff:
            raise ValueError(
                f"initial contact overclosure {initial.minimum_gap:.6g} m is not "
                "admitted; resolve initial geometry before solving"
            )

    def restart_contract(self) -> dict[str, object]:
        """Bind the state-free C0 penalty law to a versioned static checkpoint."""

        return {
            "profile": self.profile,
            "surfaces": [
                {"name": item.name, "element_ids": list(item.element_ids),
                 "side": item.side}
                for item in self.definition.surfaces
            ],
            "rigid_bodies": [
                {"name": item.name, "kind": item.kind, "point": list(item.point),
                 "normal": list(item.normal)}
                for item in self.definition.rigid_bodies
            ],
            "interactions": [
                {"name": item.name, "surface": item.surface,
                 "target": item.target, "normal_stiffness": item.normal_stiffness,
                 "gap_tolerance": item.gap_tolerance,
                 "normal_law": item.normal_law}
                for item in self.definition.interactions
            ],
            "settings": {
                "maximum_candidate_pairs": self.settings.maximum_candidate_pairs,
            },
        }

    def evaluate(self, displacement: np.ndarray, *, tangent: bool = True):
        n_dof = self.model.mesh.dof_manager.total_dofs
        u = np.asarray(displacement, dtype=float).reshape(-1)
        if u.size != n_dof or not np.all(np.isfinite(u)):
            raise ValueError("contact displacement has invalid size or nonfinite values")
        weighted_gap = self.reference_weighted_gap + np.asarray(
            self.gap_gradient @ u, dtype=float
        ).reshape(-1)
        normalized_gap = weighted_gap / self.support
        active_gap = np.minimum(normalized_gap, 0.0)
        # At exact first touch, choose the closed-side generalized tangent so
        # a free rigid approach mode can enter contact without a singular
        # initial Newton system.  Zero-gap nodes carry no pressure yet.
        active_mask = normalized_gap <= 0.0
        energy = 0.5 * self.stiffness * float(
            self.support @ (active_gap * active_gap)
        )
        force = np.asarray(
            self.gap_gradient.T @ (self.stiffness * active_gap), dtype=float
        ).reshape(-1)
        if tangent:
            active_gradient = self.gap_gradient[active_mask]
            stiffness = (
                self.stiffness * active_gradient.T
                @ sparse.diags(1.0 / self.support[active_mask])
                @ active_gradient
            ).tocsr()
        else:
            stiffness = None
        minimum_gap = float("inf")
        shell_force = np.zeros(3, dtype=float)
        shell_moment = np.zeros(3, dtype=float)
        for reference, dofs, N, skin_offset, gradient in self.patches:
            nodal_gap = (
                (reference + u[dofs[:, :3]] + skin_offset - self.point) @ self.normal
                + u[dofs[:, 3:]] @ gradient[3:]
            )
            sample_gap = N @ nodal_gap
            # A bilinear Q4 gap against a fixed plane has its minimum at a
            # corner; checking only Gauss points can hide edge penetration.
            minimum_gap = min(minimum_gap, float(np.min(sample_gap)),
                              float(np.min(nodal_gap)))
        for reference, dofs in self.output_nodes:
            local_force = force[dofs]
            shell_force += local_force[:3]
            shell_moment += np.cross(reference + u[dofs[:3]], local_force[:3])
            shell_moment += local_force[3:]
        # ``force`` is the internal residual dPi/du.  Physical contact force
        # on the shell is its negative; the plane receives the opposite.
        shell_tuple = tuple(float(-x) for x in shell_force)
        rigid_tuple = tuple(float(x) for x in shell_force)
        moment_tuple = tuple(float(-x) for x in shell_moment)
        rigid_moment_tuple = tuple(float(x) for x in shell_moment)
        results = ContactResults(
            self.profile,
            minimum_gap,
            energy,
            shell_tuple,
            rigid_tuple,
            moment_tuple,
            rigid_moment_tuple,
            int(np.count_nonzero(normalized_gap < 0.0)),
            minimum_gap >= -self.gap_tolerance,
        )
        return force, stiffness, results

    def admissible_step_fraction(self, start: np.ndarray, end: np.ndarray) -> float:
        """Bound a linear trial path by the physical corner gap tolerance.

        For this fixed-plane, affine Q4 profile each corner gap is affine in
        the trial coordinates.  The endpoint bound is therefore a complete
        swept certificate for the represented skin, including its edges.
        """

        start_u = np.asarray(start, dtype=float).reshape(-1)
        end_u = np.asarray(end, dtype=float).reshape(-1)
        fraction = 1.0
        for reference, dofs, _N, skin_offset, gradient in self.patches:
            base = (reference + skin_offset - self.point) @ self.normal
            first = base + start_u[dofs] @ gradient
            last = base + end_u[dofs] @ gradient
            crossing = last < -self.gap_tolerance
            if np.any(crossing):
                allowed = (first[crossing] + self.gap_tolerance) / (
                    first[crossing] - last[crossing]
                )
                fraction = min(fraction, float(np.min(allowed)))
        if fraction >= 1.0:
            return 1.0
        self.swept_trial_cutbacks += 1
        return max(0.0, 0.98 * fraction)


_ACTIVE_CONTACT: ContextVar[object | None] = ContextVar(
    "anysolver_general_contact", default=None
)


def active_contact_manager() -> object | None:
    return _ACTIVE_CONTACT.get()


@contextmanager
def suspend_contact() -> Iterator[None]:
    """Keep a nested contact-free solve independent of its calling solve."""

    token = _ACTIVE_CONTACT.set(None)
    try:
        yield
    finally:
        _ACTIVE_CONTACT.reset(token)


@contextmanager
def contact_scope(model: FEModel, definition: ContactDefinition,
                  settings: ContactSolverSettings | None = None,
                  initial_displacement: np.ndarray | None = None) -> Iterator[object]:
    settings = ContactSolverSettings() if settings is None else settings
    if definition.rigid_bodies:
        if settings.pair_motion != "guided":
            raise ValueError("rigid contact does not support pair_motion")
        manager = _PlanarQ4PlaneManager(model, definition, settings, initial_displacement)
    else:
        if settings.pair_motion == "restricted_sliding":
            if len(definition.surfaces) == 2 and any(
                len(surface.element_ids) > 1 for surface in definition.surfaces
            ):
                from .patch_sliding import _RestrictedSlidingPatchFEManager as manager_type
            else:
                from .sliding import _RestrictedSlidingPairFEManager as manager_type

            manager = manager_type(
                model, definition, settings, initial_displacement=initial_displacement,
            )
        else:
            from .pair import _PlanarShellPairManager

            manager = _PlanarShellPairManager(model, definition, settings, initial_displacement)
    token = _ACTIVE_CONTACT.set(manager)
    try:
        yield manager
    finally:
        _ACTIVE_CONTACT.reset(token)
