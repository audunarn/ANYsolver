"""Structural material contracts and constitutive-property dispatch.

The solver deliberately owns this small protocol so material objects supplied
by other packages (including a future :mod:`ANYmaterial`) can be registered
without introducing a repository dependency.  Elastic compliance uses
engineering Voigt order ``[11, 22, 33, 23, 13, 12]``:

``[eps11, eps22, eps33, gamma23, gamma13, gamma12] = S @
  [sig11, sig22, sig33, tau23, tau13, tau12]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol, Tuple, runtime_checkable

import numpy as np


ENGINEERING_VOIGT_ORDER: Tuple[str, ...] = ("11", "22", "33", "23", "13", "12")
SUPPORTED_ELASTIC_SYMMETRIES = frozenset({"isotropic", "orthotropic"})


@runtime_checkable
class StructuralMaterial(Protocol):
    """Minimal solver-facing contract for a structural material."""

    name: str
    density: float
    elastic_symmetry: str

    def elastic_compliance_matrix(self) -> np.ndarray:
        """Return the 6x6 engineering compliance in solver Voigt order."""


@dataclass(frozen=True)
class BeamMaterialProperties:
    """Elastic constants used by beam formulations in their local axes."""

    axial_modulus: float
    shear_modulus_xy: float
    shear_modulus_xz: float
    characteristic_modulus: float


@dataclass(frozen=True)
class Hill48Yield:
    """Symmetric Hill-48 directional yield strengths in material axes.

    ``X``, ``Y`` and ``Z`` are uniaxial strengths in directions 1, 2 and 3.
    ``S12``, ``S13`` and ``S23`` are the corresponding shear strengths.  All
    values are physical stresses in Pa.
    """

    X: float
    Y: float
    Z: float
    S12: float
    S13: float
    S23: float

    def __post_init__(self) -> None:
        values = np.asarray((self.X, self.Y, self.Z, self.S12, self.S13, self.S23), dtype=float)
        if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError("Hill-48 strengths X, Y, Z, S12, S13 and S23 must be finite and positive")

        eigvals = np.linalg.eigvalsh(self.quadratic_form_matrix())
        scale = max(float(np.max(np.abs(eigvals))), np.finfo(float).tiny)
        tolerance = 1.0e-12 * scale
        # Hydrostatic stress supplies the one expected null direction.  Every
        # deviatoric normal and shear direction must remain bounded.
        if float(eigvals[0]) < -tolerance or float(eigvals[1]) <= tolerance:
            raise ValueError(
                "Hill-48 strengths do not define a convex, bounded deviatoric yield surface"
            )

    def coefficients(self) -> Tuple[float, float, float, float, float, float]:
        """Return conventional ``(F, G, H, L, M, N)`` coefficients.

        The resulting quadratic form is a dimensionless utilization squared:

        ``F(s2-s3)^2 + G(s3-s1)^2 + H(s1-s2)^2
        + 2L*t23^2 + 2M*t13^2 + 2N*t12^2``.
        """

        x2 = float(self.X) ** 2
        y2 = float(self.Y) ** 2
        z2 = float(self.Z) ** 2
        s12_2 = float(self.S12) ** 2
        s13_2 = float(self.S13) ** 2
        s23_2 = float(self.S23) ** 2
        F = 0.5 * (1.0 / y2 + 1.0 / z2 - 1.0 / x2)
        G = 0.5 * (1.0 / z2 + 1.0 / x2 - 1.0 / y2)
        H = 0.5 * (1.0 / x2 + 1.0 / y2 - 1.0 / z2)
        L = 0.5 / s23_2
        M = 0.5 / s13_2
        N = 0.5 / s12_2
        return F, G, H, L, M, N

    @property
    def F(self) -> float:
        return self.coefficients()[0]

    @property
    def G(self) -> float:
        return self.coefficients()[1]

    @property
    def H(self) -> float:
        return self.coefficients()[2]

    @property
    def L(self) -> float:
        return self.coefficients()[3]

    @property
    def M(self) -> float:
        return self.coefficients()[4]

    @property
    def N(self) -> float:
        return self.coefficients()[5]

    def quadratic_form_matrix(self) -> np.ndarray:
        """Return the 6x6 utilization-squared matrix in solver Voigt order."""

        F, G, H, L, M, N = self.coefficients()
        matrix = np.zeros((6, 6), dtype=float)
        matrix[:3, :3] = np.array(
            [
                [G + H, -H, -G],
                [-H, F + H, -F],
                [-G, -F, F + G],
            ],
            dtype=float,
        )
        matrix[3, 3] = 2.0 * L
        matrix[4, 4] = 2.0 * M
        matrix[5, 5] = 2.0 * N
        return matrix

    def plane_stress_quadratic_matrix(self) -> np.ndarray:
        """Return the material-axis plane-stress matrix for ``[s11,s22,t12]``."""

        indices = (0, 1, 5)
        matrix = self.quadratic_form_matrix()
        return matrix[np.ix_(indices, indices)]

    def utilization(self, stress: Any) -> np.ndarray | float:
        """Evaluate Hill utilization for one or more 6-component stresses."""

        values = np.asarray(stress, dtype=float)
        if values.shape == (6,):
            phi = float(values @ self.quadratic_form_matrix() @ values)
            return float(np.sqrt(max(phi, 0.0)))
        if values.ndim < 1 or values.shape[-1] != 6:
            raise ValueError("Hill-48 stress must have trailing shape (6,)")
        phi = np.einsum("...i,ij,...j->...", values, self.quadratic_form_matrix(), values)
        return np.sqrt(np.maximum(phi, 0.0))

    def equivalent_stress(self, stress: Any, reference_stress: Optional[float] = None) -> np.ndarray | float:
        """Return a stress-valued Hill equivalent referenced to ``X`` by default."""

        reference = float(self.X if reference_stress is None else reference_stress)
        if not np.isfinite(reference) or reference <= 0.0:
            raise ValueError("Hill-48 reference stress must be finite and positive")
        return reference * self.utilization(stress)


@dataclass
class OrthotropicMaterial:
    """Homogeneous three-dimensional orthotropic engineering material."""

    name: str
    elastic_modulus_1: float
    elastic_modulus_2: float
    elastic_modulus_3: float
    poisson_ratio_12: float
    poisson_ratio_13: float
    poisson_ratio_23: float
    shear_modulus_12: float
    shear_modulus_13: float
    shear_modulus_23: float
    density: float = 0.0
    hill_yield: Optional[Hill48Yield] = None
    hardening_curve: Optional[object] = None

    def __post_init__(self) -> None:
        validate_material(self)

    @property
    def elastic_symmetry(self) -> str:
        return "orthotropic"

    @property
    def poisson_ratio_21(self) -> float:
        return float(self.poisson_ratio_12) * float(self.elastic_modulus_2) / float(self.elastic_modulus_1)

    @property
    def poisson_ratio_31(self) -> float:
        return float(self.poisson_ratio_13) * float(self.elastic_modulus_3) / float(self.elastic_modulus_1)

    @property
    def poisson_ratio_32(self) -> float:
        return float(self.poisson_ratio_23) * float(self.elastic_modulus_3) / float(self.elastic_modulus_2)

    @property
    def hill48_yield(self) -> Optional[Hill48Yield]:
        """Compatibility spelling for consumers that name the criterion."""

        return self.hill_yield

    def elastic_compliance_matrix(self) -> np.ndarray:
        """Return symmetric 3D engineering compliance in material axes."""

        E1 = float(self.elastic_modulus_1)
        E2 = float(self.elastic_modulus_2)
        E3 = float(self.elastic_modulus_3)
        nu12 = float(self.poisson_ratio_12)
        nu13 = float(self.poisson_ratio_13)
        nu23 = float(self.poisson_ratio_23)
        matrix = np.zeros((6, 6), dtype=float)
        matrix[0, 0] = 1.0 / E1
        matrix[1, 1] = 1.0 / E2
        matrix[2, 2] = 1.0 / E3
        matrix[0, 1] = matrix[1, 0] = -nu12 / E1
        matrix[0, 2] = matrix[2, 0] = -nu13 / E1
        matrix[1, 2] = matrix[2, 1] = -nu23 / E2
        matrix[3, 3] = 1.0 / float(self.shear_modulus_23)
        matrix[4, 4] = 1.0 / float(self.shear_modulus_13)
        matrix[5, 5] = 1.0 / float(self.shear_modulus_12)
        return matrix


def material_symmetry(material: Any) -> str:
    """Return the normalized declared elastic symmetry.

    Legacy duck-typed isotropic objects without the declaration remain
    recognizable when they expose the historical ``elastic_modulus`` and
    ``poisson_ratio`` fields.
    """

    symmetry = getattr(material, "elastic_symmetry", None)
    if symmetry is None and hasattr(material, "elastic_modulus") and hasattr(material, "poisson_ratio"):
        return "isotropic"
    if not isinstance(symmetry, str) or not symmetry.strip():
        raise ValueError(
            "Structural material must declare elastic_symmetry as 'isotropic' or 'orthotropic'"
        )
    return symmetry.strip().lower()


def is_isotropic_material(material: Any) -> bool:
    """Return whether a material declares isotropic elasticity."""

    try:
        return material_symmetry(material) == "isotropic"
    except ValueError:
        return False


def is_orthotropic_material(material: Any) -> bool:
    """Return whether a material declares orthotropic elasticity."""

    try:
        return material_symmetry(material) == "orthotropic"
    except ValueError:
        return False


def elastic_compliance_matrix(material: Any) -> np.ndarray:
    """Return a material compliance matrix with a stable numpy representation."""

    provider = getattr(material, "elastic_compliance_matrix", None)
    if callable(provider):
        matrix = np.asarray(provider(), dtype=float)
    elif is_isotropic_material(material):
        E = float(material.elastic_modulus)
        nu = float(material.poisson_ratio)
        G = E / (2.0 * (1.0 + nu))
        matrix = np.array(
            [
                [1.0 / E, -nu / E, -nu / E, 0.0, 0.0, 0.0],
                [-nu / E, 1.0 / E, -nu / E, 0.0, 0.0, 0.0],
                [-nu / E, -nu / E, 1.0 / E, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0 / G, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0 / G, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0 / G],
            ],
            dtype=float,
        )
    else:
        raise ValueError("Structural material must provide elastic_compliance_matrix()")
    if matrix.shape != (6, 6):
        raise ValueError(
            f"Material elastic compliance must have shape (6, 6), received {matrix.shape}"
        )
    return matrix


def shell_material_matrices(material: Any) -> Tuple[np.ndarray, np.ndarray, float]:
    """Return material-axis shell ``(Q, G_transverse, G12)`` matrices.

    ``Q`` acts on ``[eps11, eps22, gamma12]``.  The transverse matrix acts on
    ``[gamma13, gamma23]``.  Rotation into an element frame is intentionally
    left to the shell element because orientation is an element property.
    """

    symmetry = material_symmetry(material)
    if symmetry not in SUPPORTED_ELASTIC_SYMMETRIES:
        raise NotImplementedError(
            f"Elastic symmetry {symmetry!r} is not supported; general anisotropic materials "
            "require arbitrary constitutive coupling"
        )
    compliance = elastic_compliance_matrix(material)
    plane_indices = (0, 1, 5)
    shear_indices = (4, 3)
    try:
        plane_stress = np.linalg.inv(compliance[np.ix_(plane_indices, plane_indices)])
        transverse_shear = np.linalg.inv(compliance[np.ix_(shear_indices, shear_indices)])
    except np.linalg.LinAlgError as exc:
        raise ValueError("Material compliance is singular for shell plane-stress reduction") from exc
    drilling_shear = 1.0 / float(compliance[5, 5])
    return plane_stress, transverse_shear, drilling_shear


def beam_material_properties(material: Any) -> BeamMaterialProperties:
    """Return local-axis beam elastic constants without fake isotropic fields."""

    symmetry = material_symmetry(material)
    if symmetry not in SUPPORTED_ELASTIC_SYMMETRIES:
        raise NotImplementedError(
            f"Elastic symmetry {symmetry!r} is not supported; general anisotropic beam "
            "section stiffness is not implemented"
        )
    compliance = elastic_compliance_matrix(material)
    try:
        axial = 1.0 / float(compliance[0, 0])
        shear_xy = 1.0 / float(compliance[5, 5])
        shear_xz = 1.0 / float(compliance[4, 4])
    except (ZeroDivisionError, FloatingPointError) as exc:
        raise ValueError("Material compliance is singular for beam reduction") from exc
    return BeamMaterialProperties(
        axial_modulus=axial,
        shear_modulus_xy=shear_xy,
        shear_modulus_xz=shear_xz,
        characteristic_modulus=axial,
    )


def shell_characteristic_modulus(material: Any) -> float:
    """Return the documented shell numerical-scaling modulus ``max(E1, E2)``."""

    compliance = elastic_compliance_matrix(material)
    return max(1.0 / float(compliance[0, 0]), 1.0 / float(compliance[1, 1]))


def material_validation_errors(material: Any) -> Tuple[str, ...]:
    """Return deterministic structural-material contract violations."""

    errors = []
    name = getattr(material, "name", None)
    if not isinstance(name, str) or not name.strip():
        errors.append("material name must be a non-empty string")

    try:
        symmetry = material_symmetry(material)
    except ValueError as exc:
        symmetry = ""
        errors.append(str(exc))
    if symmetry and symmetry not in SUPPORTED_ELASTIC_SYMMETRIES:
        if symmetry == "anisotropic":
            errors.append(
                "general anisotropic elasticity is not supported; use isotropic or orthotropic elasticity"
            )
        else:
            errors.append(
                f"elastic symmetry {symmetry!r} is not supported; use 'isotropic' or 'orthotropic'"
            )

    density = getattr(material, "density", None)
    try:
        density_value = float(density)
    except (TypeError, ValueError):
        density_value = float("nan")
    if not np.isfinite(density_value) or density_value < 0.0:
        errors.append("density must be finite and non-negative")

    if symmetry == "isotropic":
        E = getattr(material, "elastic_modulus", None)
        nu = getattr(material, "poisson_ratio", None)
        if E is not None:
            try:
                E_value = float(E)
            except (TypeError, ValueError):
                E_value = float("nan")
            if not np.isfinite(E_value) or E_value <= 0.0:
                errors.append("isotropic elastic modulus must be finite and positive")
        if nu is not None:
            try:
                nu_value = float(nu)
            except (TypeError, ValueError):
                nu_value = float("nan")
            if not np.isfinite(nu_value) or not (-1.0 < nu_value < 0.5):
                errors.append("isotropic Poisson ratio must satisfy -1 < nu < 0.5")

    if symmetry == "orthotropic":
        for field_name in (
            "elastic_modulus_1",
            "elastic_modulus_2",
            "elastic_modulus_3",
            "shear_modulus_12",
            "shear_modulus_13",
            "shear_modulus_23",
        ):
            if hasattr(material, field_name):
                try:
                    value = float(getattr(material, field_name))
                except (TypeError, ValueError):
                    value = float("nan")
                if not np.isfinite(value) or value <= 0.0:
                    errors.append(f"{field_name} must be finite and positive")
        for field_name in ("poisson_ratio_12", "poisson_ratio_13", "poisson_ratio_23"):
            if hasattr(material, field_name):
                try:
                    value = float(getattr(material, field_name))
                except (TypeError, ValueError):
                    value = float("nan")
                if not np.isfinite(value):
                    errors.append(f"{field_name} must be finite")

    if symmetry in SUPPORTED_ELASTIC_SYMMETRIES:
        try:
            compliance = elastic_compliance_matrix(material)
        except Exception as exc:
            errors.append(f"invalid elastic compliance: {exc}")
        else:
            if not np.all(np.isfinite(compliance)):
                errors.append("elastic compliance matrix must contain only finite values")
            else:
                compliance_scale = max(
                    float(np.max(np.abs(compliance))),
                    np.finfo(float).tiny,
                )
            if np.all(np.isfinite(compliance)) and not np.allclose(
                compliance,
                compliance.T,
                rtol=1.0e-10,
                atol=compliance_scale * 1.0e-12,
            ):
                errors.append(
                    "elastic compliance matrix must be symmetric and obey reciprocal Poisson relations"
                )
            elif np.all(np.isfinite(compliance)):
                try:
                    eigvals = np.linalg.eigvalsh(0.5 * (compliance + compliance.T))
                except np.linalg.LinAlgError as exc:
                    errors.append(f"elastic compliance eigensolution failed: {exc}")
                else:
                    if float(np.min(eigvals)) <= 0.0:
                        errors.append("elastic compliance matrix must be positive definite")

    hill_yield = getattr(material, "hill_yield", getattr(material, "hill48_yield", None))
    if hill_yield is not None:
        try:
            # Validate structurally so an ANYmaterial-owned Hill record can
            # cross the repository boundary without subclassing this class.
            Hill48Yield(
                X=float(hill_yield.X),
                Y=float(hill_yield.Y),
                Z=float(hill_yield.Z),
                S12=float(hill_yield.S12),
                S13=float(hill_yield.S13),
                S23=float(hill_yield.S23),
            )
        except (AttributeError, TypeError, ValueError) as exc:
            errors.append(f"hill_yield must provide valid X, Y, Z, S12, S13 and S23 strengths: {exc}")

    curve = getattr(material, "hardening_curve", None)
    if symmetry == "orthotropic" and curve is not None:
        if hill_yield is None:
            errors.append(
                "orthotropic hardening_curve requires hill_yield directional strengths"
            )
        if not callable(getattr(curve, "flow_stress", None)):
            errors.append("orthotropic hardening_curve must provide flow_stress(alpha)")
        if not callable(getattr(curve, "hardening_modulus", None)):
            errors.append("orthotropic hardening_curve must provide hardening_modulus(alpha)")

    return tuple(dict.fromkeys(errors))


def validate_material(material: Any) -> None:
    """Raise ``ValueError`` when a material violates the solver contract."""

    errors = material_validation_errors(material)
    if errors:
        label = getattr(material, "name", type(material).__name__)
        raise ValueError(f"Invalid structural material {label!r}: " + "; ".join(errors))


__all__ = [
    "BeamMaterialProperties",
    "ENGINEERING_VOIGT_ORDER",
    "Hill48Yield",
    "OrthotropicMaterial",
    "StructuralMaterial",
    "SUPPORTED_ELASTIC_SYMMETRIES",
    "beam_material_properties",
    "elastic_compliance_matrix",
    "is_isotropic_material",
    "is_orthotropic_material",
    "material_symmetry",
    "material_validation_errors",
    "shell_characteristic_modulus",
    "shell_material_matrices",
    "validate_material",
]
