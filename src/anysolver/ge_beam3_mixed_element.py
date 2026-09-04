"""Private two-cell mixed discrete-curvature GE-B3 candidate.

The element packages two published lowest-order mixed Simo--Reissner cells on
vertex pairs 1--2 and 2--3.  It is intentionally not exported or selectable.
All 18 public nodal coordinates remain external; the 12 material-moment and
six element-rotation coordinates are solved locally and Schur condensed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from ._ge_beam3_mixed_ad import (
    Jet2,
    RotationDomainError,
    constant_matrix,
    dot,
    matmul,
    matvec,
    proper_rotation,
    rotation_exponential,
    rotation_log,
    so3_exp,
    so3_log,
    transpose,
)
from .beam_sections import generalized_beam_stiffness, resolve_generalized_beam_section
from .elements import Element


GE_BEAM3_MIXED_CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2"
GE_BEAM3_MIXED_RESERVED_FORMULATION_ID = "GE_BEAM3_DC_MIXED_K1_MACRO_V2"
GE_BEAM3_MIXED_FORMULATION_ID = GE_BEAM3_MIXED_CANDIDATE_ID
GE_BEAM3_MIXED_SCHEMA_ID = "GE_BEAM3_MIXED_K1_MACRO_SCHEMA_V1"
GE_BEAM3_MIXED_QUADRATURE_ID = "K1_FORCE_GAUSS1_MOMENT_GAUSS2_V1"
GE_BEAM3_MIXED_ROTATION_ID = "ELEMENT_P0_VERTEX_HYBRID_SPATIAL_INCREMENT_V1"
GE_BEAM3_MIXED_CONDENSATION_ID = "TWO_CELL_18_LOCAL_SCHUR_V1"
GE_BEAM3_MIXED_REFERENCE_ID = "STRAIGHT_TWO_EQUAL_CELLS_V1"
GE_BEAM3_MIXED_RELATIVE_ROTATION_LIMIT = 0.9 * np.pi

_CELLS = ((0, 1), (1, 2))
_MOMENT_MASS = np.array(((1.0 / 3.0, 1.0 / 6.0), (1.0 / 6.0, 1.0 / 3.0)))
_GEOMETRY_TOLERANCE = 1.0e-12


class GeBeam3MixedError(RuntimeError):
    """Base error for the private mixed candidate."""


class GeBeam3MixedGeometryError(GeBeam3MixedError, ValueError):
    """The straight two-cell reference geometry is inadmissible."""


class GeBeam3MixedLocalSolveError(GeBeam3MixedError):
    """The element-local mixed stationary problem did not converge."""


class GeBeam3MixedStateError(GeBeam3MixedError, ValueError):
    """A finite rotation was supplied outside the authoritative matrix path."""


@dataclass(frozen=True)
class _LocalState:
    rotations: np.ndarray
    moments: np.ndarray
    iterations: int
    residual_norm: float


def _value_matrix(matrix: Sequence[Sequence[Jet2]]) -> np.ndarray:
    return np.asarray([[entry.value for entry in row] for row in matrix])


def _value_vector(vector: Sequence[Jet2]) -> np.ndarray:
    return np.asarray([entry.value for entry in vector])


def _quadratic(vector: Sequence[Jet2], matrix: np.ndarray) -> Jet2:
    made = matvec(constant_matrix(matrix, vector[0].gradient.size), vector)
    return dot(vector, made)


def _geodesic_midpoint(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    relative = rotation_log(left.T @ right)
    return left @ rotation_exponential(0.5 * relative)


class GeometricallyExactBeam3D3NElement(Element):
    """Straight-reference, two-cell mixed GE-B3 candidate.

    This private class is a mechanics prototype.  It deliberately does not
    inherit from ``QuadraticBeamElement`` and is absent from public factories.
    """

    candidate_id = GE_BEAM3_MIXED_CANDIDATE_ID
    formulation_id = GE_BEAM3_MIXED_FORMULATION_ID
    formulation_native_total_lagrangian = True
    native_state_consistency_required = False
    solver_integration_authorized = False
    REVERSAL_STRAIN_MAP = np.diag((1.0, -1.0, 1.0, 1.0, -1.0, 1.0))

    def __init__(
        self,
        element_id: int,
        node_ids: Sequence[int],
        material_name: str = "default",
        cross_section: Optional[Mapping[str, Any]] = None,
        section: Any = None,
        reference_orientation: Any = None,
        reference_axis_direction: Any = None,
    ) -> None:
        nodes = [int(value) for value in node_ids]
        super().__init__(int(element_id), nodes, str(material_name))
        if len(nodes) != 3 or len(set(nodes)) != 3:
            raise ValueError("mixed GE-B3 requires three distinct nodes")
        self.cross_section = dict(cross_section or {})
        inline_orientation = self.cross_section.get("orientation")
        if reference_orientation is not None and inline_orientation is not None:
            raise ValueError("reference orientation must be supplied once")
        orientation = reference_orientation if reference_orientation is not None else inline_orientation
        values = np.asarray(orientation, dtype=np.float64) if orientation is not None else np.empty(0)
        if values.shape != (3,) or not np.all(np.isfinite(values)) or np.linalg.norm(values) == 0.0:
            raise GeBeam3MixedGeometryError("mixed GE-B3 requires a finite nonzero physical reference orientation")
        self.reference_orientation = np.array(values, copy=True)
        if reference_axis_direction is None:
            self.reference_axis_direction = None
        else:
            axis = np.asarray(reference_axis_direction, dtype=np.float64)
            if axis.shape != (3,) or not np.all(np.isfinite(axis)) or np.linalg.norm(axis) == 0.0:
                raise GeBeam3MixedGeometryError("reference_axis_direction must contain three finite nonzero values")
            self.reference_axis_direction = np.array(axis, copy=True)
        self.generalized_section = resolve_generalized_beam_section(self.cross_section, section)
        if self.generalized_section is None:
            raise ValueError("mixed GE-B3 requires a symmetric positive-definite generalized 6x6 section")
        stiffness = generalized_beam_stiffness(self.generalized_section)
        transform = self.REVERSAL_STRAIN_MAP
        reversal_sensitive = not np.allclose(
            transform @ stiffness @ transform,
            stiffness,
            rtol=0.0,
            atol=1.0e-12 * max(1.0, float(np.linalg.norm(stiffness, ord=np.inf))),
        )
        if reversal_sensitive and self.reference_axis_direction is None:
            raise GeBeam3MixedGeometryError(
                "reversal-sensitive coupled section requires physical reference_axis_direction"
            )

    @property
    def num_nodes(self) -> int:
        return 3

    @property
    def dofs_per_node(self) -> int:
        return 6

    def get_node_coordinates(self, mesh: Any) -> np.ndarray:
        coordinates = []
        for node_id in self.node_ids:
            node = mesh.get_node(node_id)
            if node is None:
                raise GeBeam3MixedGeometryError(f"mixed GE-B3 references missing node {node_id}")
            coordinates.append(np.asarray(node.coords(), dtype=np.float64))
        made = np.asarray(coordinates)
        if made.shape != (3, 3) or not np.all(np.isfinite(made)):
            raise GeBeam3MixedGeometryError("mixed GE-B3 coordinates must be finite")
        return made

    def _reference_geometry(self, mesh: Any) -> tuple[np.ndarray, float, np.ndarray, int]:
        coordinates = self.get_node_coordinates(mesh)
        chord = coordinates[2] - coordinates[0]
        length = float(np.linalg.norm(chord))
        if not np.isfinite(length) or length <= 1.0e-14:
            raise GeBeam3MixedGeometryError("mixed GE-B3 reference line has zero or nonfinite length")
        midpoint = 0.5 * (coordinates[0] + coordinates[2])
        if np.linalg.norm(coordinates[1] - midpoint) > _GEOMETRY_TOLERANCE * length:
            raise GeBeam3MixedGeometryError("mixed GE-B3 V2 requires two equal straight reference cells")
        e1 = chord / length
        projected = self.reference_orientation - float(self.reference_orientation @ e1) * e1
        if np.linalg.norm(projected) <= _GEOMETRY_TOLERANCE * np.linalg.norm(self.reference_orientation):
            raise GeBeam3MixedGeometryError("reference orientation is parallel to the beam axis")
        e2 = projected / np.linalg.norm(projected)
        e3 = np.cross(e1, e2)
        e3 /= np.linalg.norm(e3)
        frame = np.column_stack((e1, e2, e3))
        polarity = 1
        if self.reference_axis_direction is not None:
            physical = self.reference_axis_direction / np.linalg.norm(self.reference_axis_direction)
            alignment = float(physical @ e1)
            if abs(abs(alignment) - 1.0) > _GEOMETRY_TOLERANCE:
                raise GeBeam3MixedGeometryError("reference_axis_direction must be parallel to the beam axis")
            polarity = 1 if alignment >= 0.0 else -1
        return coordinates, length, frame, polarity

    def reference_triad(self, mesh: Any) -> np.ndarray:
        return np.array(self._reference_geometry(mesh)[2], copy=True)

    def _section_stiffness(self, mesh: Any) -> np.ndarray:
        _coordinates, _length, _frame, polarity = self._reference_geometry(mesh)
        stiffness = generalized_beam_stiffness(self.generalized_section)
        if polarity < 0:
            transform = self.REVERSAL_STRAIN_MAP
            stiffness = transform @ stiffness @ transform
        return stiffness

    @staticmethod
    def reverse_section_stiffness(stiffness: Any) -> np.ndarray:
        matrix = np.asarray(stiffness, dtype=np.float64)
        if matrix.shape != (6, 6):
            raise ValueError("section stiffness must have shape (6, 6)")
        transform = GeometricallyExactBeam3D3NElement.REVERSAL_STRAIN_MAP
        return transform @ matrix @ transform

    @staticmethod
    def _guard_vertex_rotations(rotations: np.ndarray) -> None:
        for left, right in _CELLS:
            angle = float(np.linalg.norm(rotation_log(rotations[left].T @ rotations[right])))
            if angle >= GE_BEAM3_MIXED_RELATIVE_ROTATION_LIMIT:
                raise RotationDomainError(
                    f"mixed GE-B3 relative vertex rotation {left + 1}-{right + 1} is {angle:.9g} rad; refine or cut back"
                )

    def _base_configuration(
        self,
        mesh: Any,
        displacement: Any,
        rotation_matrices: Any = None,
    ) -> tuple[np.ndarray, np.ndarray, float, np.ndarray, np.ndarray]:
        reference, length, frame, _polarity = self._reference_geometry(mesh)
        local = np.asarray(displacement, dtype=np.float64)
        if local.shape != (18,) or not np.all(np.isfinite(local)):
            raise ValueError("mixed GE-B3 displacement must contain 18 finite values")
        nodal = local.reshape(3, 6)
        positions = reference + nodal[:, :3]
        if np.any(nodal[:, 3:] != 0.0):
            raise GeBeam3MixedStateError(
                "mixed GE-B3 rotation-vector coordinates are increments, not accumulated state; "
                "keep them zero and supply authoritative rotation_matrices"
            )
        if rotation_matrices is None:
            rotations = np.repeat(frame[None, :, :], 3, axis=0)
        else:
            supplied = np.asarray(rotation_matrices, dtype=np.float64)
            if supplied.shape != (3, 3, 3):
                raise ValueError("rotation_matrices must have shape (3, 3, 3)")
            rotations = np.asarray([proper_rotation(value, label=f"rotation_matrices[{index}]") for index, value in enumerate(supplied)])
        self._guard_vertex_rotations(rotations)
        return positions, rotations, 0.5 * length, frame, self._section_stiffness(mesh)

    @staticmethod
    def _potential(
        positions: np.ndarray,
        vertex_rotations: np.ndarray,
        cell_length: float,
        section: np.ndarray,
        local_rotations: np.ndarray,
        moments: np.ndarray,
        *,
        include_external: bool,
    ) -> Jet2:
        external_size = 18 if include_external else 0
        size = external_size + 18
        variables = [Jet2.variable(0.0, index, size) for index in range(size)]
        made_positions: list[list[Jet2]] = []
        made_vertices: list[list[list[Jet2]]] = []
        for node in range(3):
            made_positions.append(
                [
                    Jet2.constant(positions[node, axis], size)
                    + (variables[node * 6 + axis] if include_external else 0.0)
                    for axis in range(3)
                ]
            )
            if include_external:
                increment = so3_exp(variables[node * 6 + 3 : node * 6 + 6])
                made_vertices.append(matmul(increment, constant_matrix(vertex_rotations[node], size)))
            else:
                made_vertices.append(constant_matrix(vertex_rotations[node], size))
        a = section[:3, :3]
        b = section[:3, 3:]
        d_inverse = np.linalg.inv(section[3:, 3:])
        total = Jet2.constant(0.0, size)
        e1 = [Jet2.constant(1.0, size), Jet2.constant(0.0, size), Jet2.constant(0.0, size)]
        for cell, (left_node, right_node) in enumerate(_CELLS):
            start = external_size + cell * 9
            local_increment = so3_exp(variables[start : start + 3])
            local_rotation = matmul(local_increment, constant_matrix(local_rotations[cell], size))
            cell_moments: list[list[Jet2]] = []
            for endpoint in range(2):
                moment_start = start + 3 + endpoint * 3
                cell_moments.append(
                    [Jet2.constant(moments[cell, endpoint, component], size) + variables[moment_start + component] for component in range(3)]
                )
            tangent = [
                (made_positions[right_node][axis] - made_positions[left_node][axis]) / cell_length
                for axis in range(3)
            ]
            gamma = [entry - ref for entry, ref in zip(matvec(transpose(local_rotation), tangent), e1)]
            total = total + 0.5 * cell_length * _quadratic(gamma, a)
            bt_gamma = matvec(constant_matrix(b.T, size), gamma)
            complementary = [[entry - coupled for entry, coupled in zip(endpoint, bt_gamma)] for endpoint in cell_moments]
            for row in range(2):
                for column in range(2):
                    total = total - 0.5 * cell_length * _MOMENT_MASS[row, column] * dot(
                        complementary[row],
                        matvec(constant_matrix(d_inverse, size), complementary[column]),
                    )
            relative_left = so3_log(matmul(transpose(local_rotation), made_vertices[left_node]))
            relative_right = so3_log(matmul(transpose(local_rotation), made_vertices[right_node]))
            total = total + dot(relative_right, cell_moments[1]) - dot(relative_left, cell_moments[0])
        return total

    @classmethod
    def _solve_local(
        cls,
        positions: np.ndarray,
        vertex_rotations: np.ndarray,
        cell_length: float,
        section: np.ndarray,
    ) -> _LocalState:
        local_rotations = np.asarray(
            [_geodesic_midpoint(vertex_rotations[left], vertex_rotations[right]) for left, right in _CELLS]
        )
        moments = np.zeros((2, 2, 3))
        initial_norm = None
        for iteration in range(30):
            potential = cls._potential(
                positions,
                vertex_rotations,
                cell_length,
                section,
                local_rotations,
                moments,
                include_external=False,
            )
            residual = potential.gradient
            residual_norm = float(np.linalg.norm(residual, ord=np.inf))
            if initial_norm is None:
                initial_norm = max(1.0, residual_norm)
            if residual_norm <= 2.0e-11 * initial_norm:
                return _LocalState(np.array(local_rotations, copy=True), np.array(moments, copy=True), iteration, residual_norm)
            hessian = 0.5 * (potential.hessian + potential.hessian.T)
            try:
                step = np.linalg.solve(hessian, -residual)
            except np.linalg.LinAlgError as exc:
                raise GeBeam3MixedLocalSolveError("mixed GE-B3 local Hessian is singular") from exc
            accepted = False
            for exponent in range(12):
                scale = 0.5**exponent
                trial_rotations = np.asarray(
                    [rotation_exponential(scale * step[cell * 9 : cell * 9 + 3]) @ local_rotations[cell] for cell in range(2)]
                )
                trial_moments = np.array(moments, copy=True)
                for cell in range(2):
                    trial_moments[cell, 0] += scale * step[cell * 9 + 3 : cell * 9 + 6]
                    trial_moments[cell, 1] += scale * step[cell * 9 + 6 : cell * 9 + 9]
                trial = cls._potential(
                    positions,
                    vertex_rotations,
                    cell_length,
                    section,
                    trial_rotations,
                    trial_moments,
                    include_external=False,
                )
                if np.linalg.norm(trial.gradient, ord=np.inf) < residual_norm:
                    local_rotations, moments = trial_rotations, trial_moments
                    accepted = True
                    break
            if not accepted:
                raise GeBeam3MixedLocalSolveError("mixed GE-B3 local Newton line search stalled")
        raise GeBeam3MixedLocalSolveError("mixed GE-B3 local Newton exceeded 30 iterations")

    def evaluate_candidate(
        self,
        mesh: Any,
        displacement: Any,
        *,
        rotation_matrices: Any = None,
        tangent: bool = True,
    ) -> tuple[float, np.ndarray, Optional[np.ndarray], dict[str, Any]]:
        positions, rotations, cell_length, frame, section = self._base_configuration(
            mesh, displacement, rotation_matrices
        )
        local = self._solve_local(positions, rotations, cell_length, section)
        potential = self._potential(
            positions,
            rotations,
            cell_length,
            section,
            local.rotations,
            local.moments,
            include_external=True,
        )
        residual = np.array(potential.gradient[:18], copy=True)
        made_tangent = None
        if tangent:
            hessian = 0.5 * (potential.hessian + potential.hessian.T)
            hee = hessian[:18, :18]
            hei = hessian[:18, 18:]
            hii = hessian[18:, 18:]
            made_tangent = hee - hei @ np.linalg.solve(hii, hei.T)
            made_tangent = 0.5 * (made_tangent + made_tangent.T)
        # Recover material strains/resultants at both moment endpoints per cell.
        strains = []
        resultants = []
        d_inverse = np.linalg.inv(section[3:, 3:])
        for cell, (left, right) in enumerate(_CELLS):
            gamma = local.rotations[cell].T @ ((positions[right] - positions[left]) / cell_length) - np.array((1.0, 0.0, 0.0))
            for endpoint in range(2):
                moment = local.moments[cell, endpoint]
                curvature = d_inverse @ (moment - section[:3, 3:].T @ gamma)
                strain = np.concatenate((gamma, curvature))
                strains.append(strain)
                resultants.append(section @ strain)
        fields = {
            "candidate_id": GE_BEAM3_MIXED_CANDIDATE_ID,
            "condensation_id": GE_BEAM3_MIXED_CONDENSATION_ID,
            "formulation_id": GE_BEAM3_MIXED_FORMULATION_ID,
            "generalized_resultant": np.asarray(resultants),
            "generalized_strain": np.asarray(strains),
            "local_iterations": local.iterations,
            "local_moments": np.array(local.moments, copy=True),
            "local_residual_norm": local.residual_norm,
            "local_rotations": np.array(local.rotations, copy=True),
            "quadrature_id": GE_BEAM3_MIXED_QUADRATURE_ID,
            "reference_frame": np.array(frame, copy=True),
            "reference_id": GE_BEAM3_MIXED_REFERENCE_ID,
            "rotation_id": GE_BEAM3_MIXED_ROTATION_ID,
            "schema_id": GE_BEAM3_MIXED_SCHEMA_ID,
        }
        return float(potential.value), residual, made_tangent, fields

    def compute_candidate_stiffness_matrix(self, mesh: Any) -> np.ndarray:
        """Return the research-gate reference tangent without enabling assembly."""

        _energy, _force, tangent, _fields = self.evaluate_candidate(
            mesh, np.zeros(18), tangent=True
        )
        assert tangent is not None
        return np.array(tangent, copy=True)

    def compute_stiffness_matrix(self, mesh: Any, material: Any) -> np.ndarray:
        del mesh, material
        raise GeBeam3MixedStateError(
            "mixed GE-B3 linear solver integration is not authorized; "
            "use the private compute_candidate_stiffness_matrix research gate only"
        )

    def compute_internal_forces(self, mesh: Any, displacements: Any, material: Any) -> np.ndarray:
        del mesh, displacements, material
        raise GeBeam3MixedStateError(
            "mixed GE-B3 solver integration is not authorized; use the private evaluate_candidate gate only"
        )

    def compute_nonlinear_response(self, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise GeBeam3MixedStateError(
            "mixed GE-B3 native rotation transaction is not implemented or authorized"
        )

    @property
    def capability_gaps(self) -> frozenset[str]:
        return frozenset(
            {
                "beam_shell_connection",
                "buckling",
                "curved_reference",
                "distributed_follower_loads",
                "history_bearing_sections",
                "mass_and_dynamics",
                "native_restart",
                "public_selector",
            }
        )
