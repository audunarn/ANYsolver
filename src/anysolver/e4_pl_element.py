"""Dormant production implementation of the qualified E4-PL four-node shell.

The class deliberately is not registered as the package default.  It reuses
the mature :class:`~anysolver.elements.ShellElement` infrastructure for mass,
geometric stiffness, recovery, state, nonlinear, dynamics, contact and
serialization behavior.  Planar facets use the qualified 35+3 stationary
E4-PL formulation.  Genuinely warped facets use the established varying-frame
Q4 surface kernel explicitly, because a single projected plane does not retain
the six physical rigid modes on a warped bilinear surface.

The physical condensed tangent, centre-PL term and retained drilling
hourglass term are exposed separately so numerical fields cannot silently
enter physical recovery or reaction reporting.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np

from .elements import ShellElement, _shell_material_matrices


FORMULATION_ID = "E4_PL_QUALIFIED_Q4_HYBRID_V2"
_PLANAR_FORMULATION_ID = "E4_PL_QUALIFIED_PLANAR_LINEAR_V1"
_WARPED_FORMULATIONS = frozenset({"varying_frame", "reject"})
_GAUSS = tuple(
    (r, s)
    for r, s in (
        (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
        (1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
        (1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
        (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
    )
)


def _shape(r: float, s: float) -> np.ndarray:
    return np.asarray(
        ((1.0 - r) * (1.0 - s), (1.0 + r) * (1.0 - s),
         (1.0 + r) * (1.0 + s), (1.0 - r) * (1.0 + s)),
        dtype=float,
    ) / 4.0


def _shape_derivatives(r: float, s: float) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.asarray((-(1.0 - s), 1.0 - s, 1.0 + s, -(1.0 + s)), dtype=float) / 4.0,
        np.asarray((-(1.0 - r), -(1.0 + r), 1.0 + r, 1.0 - r), dtype=float) / 4.0,
    )


def _normalize(vector: np.ndarray, label: str) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 1.0e-12:
        raise ValueError(f"cannot normalize E4-PL {label}")
    return vector / norm


def equation7_frame(nodes: Sequence[Sequence[float]]) -> tuple[np.ndarray, np.ndarray, float]:
    """Return the frozen numbered-frame basis, local nodes and warpage ratio."""

    coordinates = np.asarray(nodes, dtype=float)
    if coordinates.shape != (4, 3) or not np.all(np.isfinite(coordinates)):
        raise ValueError("E4-PL nodes must be a finite 4x3 array")
    diagonal_1 = coordinates[2] - coordinates[0]
    diagonal_2 = coordinates[1] - coordinates[3]
    normalized_1 = _normalize(diagonal_1, "first diagonal")
    normalized_2 = _normalize(diagonal_2, "second diagonal")
    tangent_1 = _normalize(normalized_1 + normalized_2, "first tangent")
    tangent_2 = _normalize(normalized_1 - normalized_2, "second tangent")
    normal = _normalize(np.cross(tangent_1, tangent_2), "normal")
    tangent_2 = _normalize(np.cross(normal, tangent_1), "orthogonal tangent")
    tangent_1 = _normalize(np.cross(tangent_2, normal), "renormalized tangent")
    frame = np.column_stack((tangent_1, tangent_2, normal))
    centre = np.mean(coordinates, axis=0)
    relative = coordinates - centre
    local = relative @ frame[:, :2]
    length = max(float(np.linalg.norm(diagonal_1)), float(np.linalg.norm(diagonal_2)), 1.0)
    warpage = float(np.max(np.abs(relative @ normal)) / length)
    return frame, local, warpage


def _coefficients(local: np.ndarray) -> Dict[str, float]:
    modal = np.asarray(
        ((1, 1, 1, 1), (-1, 1, 1, -1), (-1, -1, 1, 1), (1, -1, 1, -1)),
        dtype=float,
    ) / 4.0
    x0, xr, xs, xrs = modal @ local[:, 0]
    y0, yr, ys, yrs = modal @ local[:, 1]
    return {
        "x0": float(x0), "xr": float(xr), "xs": float(xs), "xrs": float(xrs),
        "y0": float(y0), "yr": float(yr), "ys": float(ys), "yrs": float(yrs),
        "jc": float(xr * ys - xs * yr),
        "jr": float(xr * yrs - xrs * yr),
        "js": float(xrs * ys - xs * yrs),
    }


def _jacobian(c: Mapping[str, float], r: float, s: float) -> tuple[float, float, float, float, float]:
    xr = c["xr"] + c["xrs"] * s
    xs = c["xs"] + c["xrs"] * r
    yr = c["yr"] + c["yrs"] * s
    ys = c["ys"] + c["yrs"] * r
    return xr, xs, yr, ys, xr * ys - xs * yr


def _natural_shear(local: np.ndarray, r: float, s: float, direction: int) -> np.ndarray:
    shape = _shape(r, s)
    nr, ns = _shape_derivatives(r, s)
    derivative = nr if direction == 0 else ns
    x_direction = float(local[:, 0] @ derivative)
    y_direction = float(local[:, 1] @ derivative)
    row = np.zeros(20, dtype=float)
    for index in range(4):
        base = 5 * index
        row[base + 2] = derivative[index]
        row[base + 3] = -y_direction * shape[index]
        row[base + 4] = x_direction * shape[index]
    return row


def _compatible(local: np.ndarray, c: Mapping[str, float], r: float, s: float) -> np.ndarray:
    nr, ns = _shape_derivatives(r, s)
    xr, xs, yr, ys, determinant = _jacobian(c, r, s)
    nx = (ys * nr - yr * ns) / determinant
    ny = (-xs * nr + xr * ns) / determinant
    result = np.zeros((8, 20), dtype=float)
    for index in range(4):
        base = 5 * index
        result[0, base] = nx[index]
        result[1, base + 1] = ny[index]
        result[2, base] = ny[index]
        result[2, base + 1] = nx[index]
        result[3, base + 4] = nx[index]
        result[4, base + 3] = -ny[index]
        result[5, base + 4] = ny[index]
        result[5, base + 3] = -nx[index]
    row_r_minus = _natural_shear(local, 0.0, -1.0, 0)
    row_r_plus = _natural_shear(local, 0.0, 1.0, 0)
    row_s_plus = _natural_shear(local, 1.0, 0.0, 1)
    row_s_minus = _natural_shear(local, -1.0, 0.0, 1)
    row_r = 0.5 * (1.0 - s) * row_r_minus + 0.5 * (1.0 + s) * row_r_plus
    row_s = 0.5 * (1.0 + r) * row_s_plus + 0.5 * (1.0 - r) * row_s_minus
    result[6] = (ys * row_r - yr * row_s) / determinant
    result[7] = (-xs * row_r + xr * row_s) / determinant
    return result


def _tensor_transform(xr: float, xs: float, yr: float, ys: float, a: float, b: float) -> np.ndarray:
    return np.asarray(
        (
            (xr * xr, xs * xs, a * xr * xs),
            (yr * yr, ys * ys, a * yr * ys),
            (b * xr * yr, b * xs * ys, xr * ys + yr * xs),
        ),
        dtype=float,
    )


def _source_fields(c: Mapping[str, float], r: float, s: float) -> tuple[np.ndarray, np.ndarray]:
    jc, jr, js = c["jc"], c["jr"], c["js"]
    r_bar, s_bar = jr / (3.0 * jc), js / (3.0 * jc)
    stress_transform = _tensor_transform(c["xr"], c["xs"], c["yr"], c["ys"], 2.0, 1.0)
    strain_transform = _tensor_transform(c["xr"], c["xs"], c["yr"], c["ys"], 1.0, 2.0)
    shear_transform = np.asarray(((c["xr"], c["xs"]), (c["yr"], c["ys"])), dtype=float)
    n_sigma = np.zeros((8, 14), dtype=float)
    n_epsilon = np.zeros((8, 21), dtype=float)
    n_sigma[:, :8] = np.eye(8)
    n_epsilon[:, :8] = np.eye(8)
    seed = np.asarray(((s - s_bar, 0.0), (0.0, r - r_bar), (0.0, 0.0)), dtype=float)
    stress_vary = stress_transform @ seed
    strain_vary = strain_transform @ seed
    for row, column in ((0, 8), (3, 10)):
        n_sigma[row : row + 3, column : column + 2] = stress_vary
        n_epsilon[row : row + 3, column : column + 2] = strain_vary
    shear_seed = np.asarray(((s - s_bar, 0.0), (0.0, r - r_bar)), dtype=float)
    n_sigma[6:8, 12:14] = shear_transform @ shear_seed
    n_epsilon[6:8, 12:14] = shear_transform @ shear_seed
    enrichment = np.asarray(
        ((r, 0, 0, 0, r * s, 0, 0), (0, s, 0, 0, 0, r * s, 0), (0, 0, r, s, 0, 0, r * s)),
        dtype=float,
    )
    determinant = _jacobian(c, r, s)[4]
    n_epsilon[:3, 14:21] = (jc / determinant) * (strain_transform @ enrichment)
    return n_sigma, n_epsilon


def _centre_taylor(c: Mapping[str, float]) -> np.ndarray:
    f0 = np.ones(4, dtype=float) / 4.0
    fr = np.asarray((-1, 1, 1, -1), dtype=float) / 4.0
    fs = np.asarray((-1, -1, 1, 1), dtype=float) / 4.0
    frs = np.asarray((1, -1, 1, -1), dtype=float) / 4.0
    result = np.zeros((3, 24), dtype=float)
    jc, jr, js = c["jc"], c["jr"], c["js"]
    for coordinate in range(24):
        node, component = divmod(coordinate, 6)
        ur = fr[node] if component == 0 else 0.0
        us = fs[node] if component == 0 else 0.0
        urs = frs[node] if component == 0 else 0.0
        vr = fr[node] if component == 1 else 0.0
        vs = fs[node] if component == 1 else 0.0
        vrs = frs[node] if component == 1 else 0.0
        d0 = f0[node] if component == 5 else 0.0
        dr = fr[node] if component == 5 else 0.0
        ds = fs[node] if component == 5 else 0.0
        n0 = -c["xs"] * ur + c["xr"] * us - c["ys"] * vr + c["yr"] * vs
        nr = -c["xrs"] * ur + c["xr"] * urs - c["yrs"] * vr + c["yr"] * vrs
        ns = -c["xs"] * urs + c["xrs"] * us - c["ys"] * vrs + c["yrs"] * vs
        result[0, coordinate] = d0 + n0 / (2.0 * jc)
        result[1, coordinate] = dr + (nr * jc - n0 * jr) / (2.0 * jc * jc)
        result[2, coordinate] = ds + (ns * jc - n0 * js) / (2.0 * jc * jc)
    return result


def _residual_mode(local: np.ndarray, c: Mapping[str, float]) -> np.ndarray:
    x = local[:, 0]
    y = local[:, 1]
    centred_x = x - c["x0"]
    centred_y = y - c["y0"]
    xi = np.asarray((-1, 1, 1, -1), dtype=float)
    eta = np.asarray((-1, -1, 1, 1), dtype=float)
    alternating = np.asarray((1, -1, 1, -1), dtype=float)
    area = 4.0 * c["jc"]
    b1 = ((eta @ centred_y) * xi - (xi @ centred_y) * eta) / (4.0 * area)
    b2 = (-(eta @ centred_x) * xi + (xi @ centred_x) * eta) / (4.0 * area)
    return (alternating - (alternating @ centred_x) * b1 - (alternating @ centred_y) * b2) / 4.0


def _global_transform(frame: np.ndarray) -> np.ndarray:
    transform = np.zeros((24, 24), dtype=float)
    for node in range(4):
        transform[6 * node : 6 * node + 3, 6 * node : 6 * node + 3] = frame
        transform[6 * node + 3 : 6 * node + 6, 6 * node + 3 : 6 * node + 6] = frame
    return transform


class QualifiedE4PLShellElement(ShellElement):
    """Dormant qualified E4-PL element for four-node shell facets."""

    formulation_id = FORMULATION_ID
    legacy_stiffness_batch_eligible = False
    legacy_nonlinear_batch_eligible = True

    def __init__(
        self,
        element_id: int,
        node_ids: list[int],
        material_name: str = "default",
        thickness: float = 0.01,
        drilling_stabilization: float = 1.0e-3,
        reduced_integration: bool = False,
        hourglass_stabilization: float = 1.0e-3,
        material_direction: Optional[np.ndarray] = None,
        material_angle_deg: float = 0.0,
        shell_section: Optional[Any] = None,
        *,
        pl_stabilization: float = 1.0,
        planar_tolerance: float = 1.0e-10,
        warped_formulation: str = "varying_frame",
        legacy_warped_fallback: Optional[bool] = None,
    ) -> None:
        if len(node_ids) != 4:
            raise ValueError("QualifiedE4PLShellElement requires exactly four nodes")
        super().__init__(
            element_id,
            node_ids,
            material_name,
            thickness,
            drilling_stabilization,
            reduced_integration,
            hourglass_stabilization,
            material_direction,
            material_angle_deg,
            shell_section,
        )
        self.pl_stabilization = float(pl_stabilization)
        self.planar_tolerance = float(planar_tolerance)
        if legacy_warped_fallback is not None:
            warped_formulation = (
                "varying_frame" if bool(legacy_warped_fallback) else "reject"
            )
        self.warped_formulation = str(warped_formulation).strip().lower()
        if not math.isfinite(self.pl_stabilization) or self.pl_stabilization < 0.0:
            raise ValueError("pl_stabilization must be finite and nonnegative")
        if not math.isfinite(self.planar_tolerance) or self.planar_tolerance < 0.0:
            raise ValueError("planar_tolerance must be finite and nonnegative")
        if self.warped_formulation not in _WARPED_FORMULATIONS:
            raise ValueError(
                "warped_formulation must be one of "
                f"{sorted(_WARPED_FORMULATIONS)}"
            )
        self._qualified_components: Optional[Dict[str, Any]] = None
        self._qualified_cache_key: Optional[tuple[Any, ...]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "drilling_stabilization": float(self.drilling_stabilization),
                "formulation_id": FORMULATION_ID,
                "hourglass_stabilization": float(self.hourglass_stabilization),
                "planar_tolerance": self.planar_tolerance,
                "pl_stabilization": self.pl_stabilization,
                "reduced_integration": bool(self.reduced_integration),
                "warped_formulation": self.warped_formulation,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "QualifiedE4PLShellElement":
        """Reconstruct a candidate from its lossless JSON-compatible record."""

        data = dict(payload)
        if data.get("formulation_id") not in {FORMULATION_ID, _PLANAR_FORMULATION_ID}:
            raise ValueError("serialized E4-PL formulation_id is missing or incompatible")
        if data.get("type") not in {cls.__name__, "e4-pl"}:
            raise ValueError("serialized E4-PL type is incompatible")
        return cls(
            element_id=int(data["element_id"]),
            node_ids=[int(value) for value in data["node_ids"]],
            material_name=str(data.get("material_name", "default")),
            thickness=float(data.get("thickness", 0.01)),
            drilling_stabilization=float(data.get("drilling_stabilization", 1.0e-3)),
            reduced_integration=bool(data.get("reduced_integration", False)),
            hourglass_stabilization=float(data.get("hourglass_stabilization", 1.0e-3)),
            material_direction=data.get("material_direction"),
            material_angle_deg=float(data.get("material_angle_deg", 0.0)),
            shell_section=data.get("shell_section"),
            pl_stabilization=float(data.get("pl_stabilization", 1.0)),
            planar_tolerance=float(data.get("planar_tolerance", 1.0e-10)),
            warped_formulation=str(
                data.get(
                    "warped_formulation",
                    "varying_frame"
                    if bool(data.get("legacy_warped_fallback", True))
                    else "reject",
                )
            ),
        )

    def _constitutive_and_drill_stiffness(
        self, material: Any, frame: np.ndarray
    ) -> tuple[np.ndarray, float]:
        constitutive = np.zeros((8, 8), dtype=float)
        if self.shell_section is not None:
            section = self._generalized_section_in_frame(frame)
            assert section is not None
            constitutive[:3, :3] = section.A
            constitutive[:3, 3:6] = section.B
            constitutive[3:6, :3] = section.B.T
            constitutive[3:6, 3:6] = section.D
            constitutive[6:, 6:] = section.As
            drill_stiffness = float(section.A[2, 2])
        else:
            membrane, shear, _strain_transform, _stress_transform = _shell_material_matrices(
                material, self._material_angle(frame)
            )
            constitutive[:3, :3] = self.thickness * membrane
            constitutive[3:6, 3:6] = self.thickness**3 / 12.0 * membrane
            constitutive[6:, 6:] = (5.0 / 6.0) * self.thickness * shear
            drill_stiffness = float(self.thickness * membrane[2, 2])
        if not np.all(np.isfinite(constitutive)) or drill_stiffness <= 0.0:
            raise ValueError("E4-PL constitutive matrix must be finite with positive in-plane shear")
        return constitutive, drill_stiffness

    def _qualified_stiffness_cache_key(
        self,
        mesh: Any,
        material: Any,
        coordinates: Optional[np.ndarray] = None,
    ) -> tuple[Any, ...]:
        coordinates = (
            self.get_node_coordinates(mesh)
            if coordinates is None
            else np.asarray(coordinates, dtype=float)
        )
        revisions = getattr(mesh, "revision_signature", lambda: {})()
        relative = coordinates - np.mean(coordinates, axis=0)
        return (
            id(mesh),
            id(material),
            int(revisions.get("geometry", 0)),
            int(revisions.get("material", 0)),
            np.ascontiguousarray(relative, dtype=float).tobytes(),
            float(self.thickness),
            float(self.drilling_stabilization),
            float(self.hourglass_stabilization),
            float(self.material_angle_deg),
            None
            if self.material_direction is None
            else tuple(np.asarray(self.material_direction, dtype=float)),
            id(self.shell_section),
            float(self.pl_stabilization),
            float(self.planar_tolerance),
            self.warped_formulation,
        )

    def _adopt_qualified_components(
        self,
        cache_key: tuple[Any, ...],
        components: Mapping[str, Any],
    ) -> np.ndarray:
        copied: Dict[str, Any] = {}
        for name, value in components.items():
            copied[name] = value.copy() if isinstance(value, np.ndarray) else value
        self._qualified_components = copied
        self._qualified_cache_key = cache_key
        self._hourglass_stiffness_matrix = np.asarray(copied["hourglass"], dtype=float)
        self._stiffness_matrix = np.asarray(copied["total"], dtype=float)
        return self._stiffness_matrix

    def compute_stiffness_components(self, mesh: Any, material: Any) -> Dict[str, Any]:
        coordinates = self.get_node_coordinates(mesh)
        cache_key = self._qualified_stiffness_cache_key(mesh, material, coordinates)
        if (
            self._qualified_components is not None
            and self._qualified_cache_key == cache_key
        ):
            return self._qualified_components
        frame, local, warpage = equation7_frame(coordinates)
        if warpage > self.planar_tolerance:
            if self.warped_formulation == "reject":
                raise ValueError(
                    f"E4-PL element {self.element_id} is warped by {warpage:.6e}, "
                    f"above planar_tolerance={self.planar_tolerance:.6e}"
                )
            physical = ShellElement.compute_stiffness_matrix(self, mesh, material)
            zero = np.zeros_like(physical)
            result = {
                "core": physical.copy(),
                "physical": physical.copy(),
                "pl": zero.copy(),
                "hourglass": zero.copy(),
                "numerical": zero.copy(),
                "total": physical.copy(),
                "frame": frame,
                "jacobian_centre": math.nan,
                "mixed_condensed": False,
                "legacy_fallback": False,
                "warped_direct": True,
                "warped_formulation": "varying_frame",
                "warpage_ratio": warpage,
            }
            self._qualified_components = result
            self._qualified_cache_key = cache_key
            return result

        c = _coefficients(local)
        determinants = [c["jc"], *(_jacobian(c, r, s)[4] for r, s in _GAUSS)]
        scale = max(abs(c["jc"]), 1.0)
        if min(determinants) <= 1.0e-12 * scale:
            raise ValueError(f"E4-PL element {self.element_id} has a nonpositive local Jacobian")
        constitutive, drill_stiffness = self._constitutive_and_drill_stiffness(material, frame)
        f_matrix = np.zeros((21, 14), dtype=float)
        coupling_20 = np.zeros((14, 20), dtype=float)
        strain_gram = np.zeros((21, 21), dtype=float)
        gram = np.zeros((3, 3), dtype=float)
        for r, s in _GAUSS:
            determinant = _jacobian(c, r, s)[4]
            n_sigma, n_epsilon = _source_fields(c, r, s)
            compatible = _compatible(local, c, r, s)
            f_matrix -= determinant * (n_epsilon.T @ n_sigma)
            coupling_20 += determinant * (n_sigma.T @ compatible)
            strain_gram += determinant * (n_epsilon.T @ constitutive @ n_epsilon)
            polynomial = np.asarray((1.0, r, s), dtype=float)
            gram += determinant * np.outer(polynomial, polynomial)
        stationary = np.zeros((35, 35), dtype=float)
        stationary[:14, 14:] = f_matrix.T
        stationary[14:, :14] = f_matrix
        stationary[14:, 14:] = strain_gram
        coupling = np.zeros((24, 35), dtype=float)
        physical_coupling = np.zeros((20, 35), dtype=float)
        physical_coupling[:, :14] = coupling_20.T
        for node in range(4):
            coupling[6 * node : 6 * node + 5] = physical_coupling[5 * node : 5 * node + 5]
        try:
            solution = np.linalg.solve(stationary, coupling.T)
        except np.linalg.LinAlgError as exc:
            raise ValueError(f"E4-PL element {self.element_id} stationary system is singular") from exc
        core_local = -coupling @ solution
        core_local = 0.5 * (core_local + core_local.T)
        centre = _centre_taylor(c)
        pl_local = self.pl_stabilization * drill_stiffness * (centre.T @ gram @ centre)
        gamma = _residual_mode(local, c)
        gamma_24 = np.zeros(24, dtype=float)
        gamma_24[5::6] = gamma
        area = 4.0 * c["jc"]
        hourglass_local = (
            2.0
            * float(self.hourglass_stabilization)
            * drill_stiffness
            * area
            * np.outer(gamma_24, gamma_24)
        )
        transform = _global_transform(frame)
        core = transform @ core_local @ transform.T
        pl = transform @ pl_local @ transform.T
        hourglass = transform @ hourglass_local @ transform.T
        for matrix in (core, pl, hourglass):
            matrix[:] = 0.5 * (matrix + matrix.T)
        numerical = pl + hourglass
        total = core + numerical
        result = {
            "core": core,
            "physical": core,
            "pl": pl,
            "hourglass": hourglass,
            "numerical": numerical,
            "total": total,
            "frame": frame,
            "jacobian_centre": c["jc"],
            "mixed_condensed": True,
            "legacy_fallback": False,
            "warped_direct": False,
            "warped_formulation": "planar_e4_pl",
            "warpage_ratio": warpage,
        }
        self._qualified_components = result
        self._qualified_cache_key = cache_key
        return result

    def compute_stiffness_matrix(self, mesh: Any, material: Any) -> np.ndarray:
        components = self.compute_stiffness_components(mesh, material)
        self._hourglass_stiffness_matrix = np.asarray(components["hourglass"], dtype=float)
        self._stiffness_matrix = np.asarray(components["total"], dtype=float)
        return self._stiffness_matrix

    def compute_internal_forces(
        self,
        mesh: Any,
        displacements: np.ndarray,
        material: Any,
    ) -> np.ndarray:
        """Return the qualified linear internal force for local or global input."""

        vector = self._get_element_displacements(mesh, displacements)
        return self.compute_stiffness_matrix(mesh, material) @ vector

    def _qualified_linear_correction(
        self,
        mesh: Any,
        material: Any,
        num_layers: int,
    ) -> np.ndarray:
        """Difference between the qualified and inherited elastic tangents.

        The mature ``ShellElement`` nonlinear implementation supplies the
        geometric, material-state and generalized-section increments.  Its
        zero-displacement tangent is the legacy elastic shell, however.  The
        constant correction below replaces that baseline with E4-PL without
        disturbing the established nonlinear/state algorithms.  For a warped
        facet the explicit fallback makes the correction identically zero.
        """

        coordinates = self.get_node_coordinates(mesh)
        _frame, _local, warpage = equation7_frame(coordinates)
        if warpage > self.planar_tolerance:
            return np.zeros((self.total_dofs, self.total_dofs), dtype=float)
        # The correction is an elastic tangent delta and is independent of
        # the caller's through-thickness integration count.  Use a fixed valid
        # Lobatto rule for the inherited zero-state nonlinear tangent: this
        # preserves the generalized-section baseline while permitting plan
        # cache bookkeeping probes to use arbitrary layer identifiers.
        self._hourglass_stiffness_matrix = None
        _force, legacy, _state = ShellElement.compute_nonlinear_response(
            self,
            mesh,
            material,
            np.zeros(self.total_dofs, dtype=float),
            None,
            5,
            True,
        )
        if legacy is None:
            raise RuntimeError("ShellElement returned no zero-state tangent")
        qualified = np.asarray(self.compute_stiffness_matrix(mesh, material), dtype=float)
        return qualified - np.asarray(legacy, dtype=float)

    def compute_nonlinear_response(
        self,
        mesh: Any,
        material: Any,
        u_elem: np.ndarray,
        state: Optional[Any] = None,
        num_layers: int = 5,
        tangent: bool = True,
    ) -> tuple[np.ndarray, Optional[np.ndarray], Optional[Any]]:
        """Use mature nonlinear/state mechanics with the qualified baseline.

        This additive construction is exact at zero displacement and retains
        the existing von-Karman, plasticity, orthotropy, initial-field and
        generalized-section increments.  Numerical PL/hourglass contributions
        remain a constant separately recoverable part of the tangent.
        """

        vector = np.asarray(u_elem, dtype=float).reshape(self.total_dofs)
        self._hourglass_stiffness_matrix = None
        force, inherited_tangent, trial_state = super().compute_nonlinear_response(
            mesh,
            material,
            vector,
            state,
            num_layers,
            tangent,
        )
        correction = self._qualified_linear_correction(mesh, material, num_layers)
        force = np.asarray(force, dtype=float) + correction @ vector
        if not tangent:
            return force, None, trial_state
        if inherited_tangent is None:
            raise RuntimeError("ShellElement returned no tangent with tangent=True")
        return force, np.asarray(inherited_tangent, dtype=float) + correction, trial_state

    def numerical_internal_force(self, displacement: np.ndarray) -> Dict[str, np.ndarray]:
        """Return PL/hourglass forces separately from physical recovery."""

        if self._qualified_components is None:
            raise RuntimeError("compute_stiffness_matrix must run before numerical force recovery")
        vector = np.asarray(displacement, dtype=float).reshape(self.total_dofs)
        return {
            "pl": np.asarray(self._qualified_components["pl"]) @ vector,
            "hourglass": np.asarray(self._qualified_components["hourglass"]) @ vector,
            "numerical": np.asarray(self._qualified_components["numerical"]) @ vector,
        }


__all__ = ["FORMULATION_ID", "QualifiedE4PLShellElement", "equation7_frame"]
