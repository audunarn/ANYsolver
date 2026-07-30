"""Focused tests for the solver-owned structural material contract."""

from __future__ import annotations

import numpy as np
import pytest

from anysolver import (
    ENGINEERING_VOIGT_ORDER,
    FEModel,
    Hill48Yield,
    Material,
    OrthotropicMaterial,
    StructuralMaterial,
    beam_material_properties,
    elastic_compliance_matrix,
    hill48_equivalent_stress,
    is_isotropic_material,
    is_orthotropic_material,
    shell_material_matrices,
    validate_production_model,
)


def _orthotropic(**overrides) -> OrthotropicMaterial:
    properties = {
        "name": "ud",
        "elastic_modulus_1": 150.0e9,
        "elastic_modulus_2": 10.0e9,
        "elastic_modulus_3": 8.0e9,
        "poisson_ratio_12": 0.25,
        "poisson_ratio_13": 0.20,
        "poisson_ratio_23": 0.30,
        "shear_modulus_12": 5.0e9,
        "shear_modulus_13": 4.0e9,
        "shear_modulus_23": 3.0e9,
        "density": 1600.0,
    }
    properties.update(overrides)
    return OrthotropicMaterial(**properties)


def test_legacy_material_satisfies_contract_and_isotropic_compliance() -> None:
    material = Material("steel", 210.0e9, 0.3, density=7850.0)

    assert isinstance(material, StructuralMaterial)
    assert material.elastic_symmetry == "isotropic"
    assert is_isotropic_material(material)
    assert not is_orthotropic_material(material)
    assert ENGINEERING_VOIGT_ORDER == ("11", "22", "33", "23", "13", "12")

    compliance = elastic_compliance_matrix(material)
    assert compliance.shape == (6, 6)
    assert np.allclose(compliance, compliance.T)
    assert compliance[0, 0] == pytest.approx(1.0 / material.elastic_modulus)
    assert compliance[0, 1] == pytest.approx(-material.poisson_ratio / material.elastic_modulus)
    assert compliance[5, 5] == pytest.approx(1.0 / material.shear_modulus)


def test_orthotropic_compliance_reciprocity_and_reduced_properties() -> None:
    material = _orthotropic()

    assert isinstance(material, StructuralMaterial)
    assert is_orthotropic_material(material)
    compliance = material.elastic_compliance_matrix()
    assert np.allclose(compliance, compliance.T)
    assert compliance[0, 1] == pytest.approx(-material.poisson_ratio_12 / material.elastic_modulus_1)
    assert material.poisson_ratio_21 / material.elastic_modulus_2 == pytest.approx(
        material.poisson_ratio_12 / material.elastic_modulus_1
    )
    assert np.all(np.linalg.eigvalsh(compliance) > 0.0)

    plane_stress, transverse_shear, drilling_shear = shell_material_matrices(material)
    expected_plane_stress = np.linalg.inv(compliance[np.ix_((0, 1, 5), (0, 1, 5))])
    assert np.allclose(plane_stress, expected_plane_stress)
    assert np.allclose(transverse_shear, np.diag([material.shear_modulus_13, material.shear_modulus_23]))
    assert drilling_shear == pytest.approx(material.shear_modulus_12)

    beam = beam_material_properties(material)
    assert beam.axial_modulus == pytest.approx(material.elastic_modulus_1)
    assert beam.shear_modulus_xy == pytest.approx(material.shear_modulus_12)
    assert beam.shear_modulus_xz == pytest.approx(material.shear_modulus_13)
    assert beam.characteristic_modulus == pytest.approx(material.elastic_modulus_1)


def test_orthotropic_isotropic_limit_matches_legacy_reductions() -> None:
    E = 70.0e9
    nu = 0.25
    G = E / (2.0 * (1.0 + nu))
    isotropic = Material("iso", E, nu)
    orthotropic = OrthotropicMaterial(
        "ortho_iso",
        E,
        E,
        E,
        nu,
        nu,
        nu,
        G,
        G,
        G,
    )

    assert np.allclose(
        elastic_compliance_matrix(orthotropic),
        elastic_compliance_matrix(isotropic),
    )
    iso_shell = shell_material_matrices(isotropic)
    ortho_shell = shell_material_matrices(orthotropic)
    assert all(np.allclose(left, right) for left, right in zip(iso_shell, ortho_shell))
    assert beam_material_properties(orthotropic) == pytest.approx(
        beam_material_properties(isotropic)
    )


def test_orthotropic_validation_rejects_invalid_moduli_and_compliance() -> None:
    with pytest.raises(ValueError, match="elastic_modulus_2 must be finite and positive"):
        _orthotropic(elastic_modulus_2=0.0)

    with pytest.raises(ValueError, match="positive definite"):
        _orthotropic(poisson_ratio_12=4.0)

    with pytest.raises(ValueError, match="density must be finite and non-negative"):
        _orthotropic(density=-1.0)

    with pytest.raises(ValueError, match="hardening_curve requires hill_yield"):
        _orthotropic(hardening_curve=object())


def test_hill48_coefficients_reproduce_all_six_strengths() -> None:
    hill = Hill48Yield(
        X=400.0e6,
        Y=320.0e6,
        Z=280.0e6,
        S12=190.0e6,
        S13=175.0e6,
        S23=160.0e6,
    )
    strengths = (hill.X, hill.Y, hill.Z, hill.S23, hill.S13, hill.S12)
    for index, strength in enumerate(strengths):
        stress = np.zeros(6)
        stress[index] = strength
        assert hill.utilization(stress) == pytest.approx(1.0)

    stress = np.array([hill.X, 0.0, 0.0, 0.0, 0.0, 0.0])
    assert hill.equivalent_stress(stress) == pytest.approx(hill.X)
    assert hill48_equivalent_stress(stress, hill) == pytest.approx(hill.X)
    assert np.allclose(
        hill.plane_stress_quadratic_matrix(),
        hill.quadratic_form_matrix()[np.ix_((0, 1, 5), (0, 1, 5))],
    )

    with pytest.raises(ValueError, match="finite and positive"):
        Hill48Yield(1.0, 1.0, 1.0, 1.0, 0.0, 1.0)
    with pytest.raises(ValueError, match="convex"):
        Hill48Yield(1.0, 10.0, 10.0, 1.0, 1.0, 1.0)


def test_hill48_isotropic_limit_is_von_mises() -> None:
    yield_stress = 355.0e6
    shear_yield = yield_stress / np.sqrt(3.0)
    hill = Hill48Yield(
        yield_stress,
        yield_stress,
        yield_stress,
        shear_yield,
        shear_yield,
        shear_yield,
    )
    stress = np.array([240.0e6, -35.0e6, 80.0e6, 12.0e6, -9.0e6, 45.0e6])
    s1, s2, s3, t23, t13, t12 = stress
    von_mises = np.sqrt(
        0.5 * ((s1 - s2) ** 2 + (s2 - s3) ** 2 + (s3 - s1) ** 2)
        + 3.0 * (t23**2 + t13**2 + t12**2)
    )

    assert hill.equivalent_stress(stress) == pytest.approx(von_mises)


class _ExternalOrthotropicMaterial:
    def __init__(self, name: str = "external") -> None:
        self.name = name
        self.density = 1234.0
        self.elastic_symmetry = "orthotropic"
        self._compliance = _orthotropic().elastic_compliance_matrix()

    def elastic_compliance_matrix(self) -> np.ndarray:
        return self._compliance.copy()


def test_register_material_accepts_external_protocol_and_advances_revision() -> None:
    model = FEModel("external_material")
    initial_revision = model.revision_signature()["material"]
    first = _ExternalOrthotropicMaterial()

    returned = model.register_material(first)

    assert isinstance(first, StructuralMaterial)
    assert returned is first
    assert model.get_material("external") is first
    assert model.revision_signature()["material"] == initial_revision + 1

    replacement = _ExternalOrthotropicMaterial()
    model.register_material(replacement)
    assert model.get_material("external") is replacement
    assert model.revision_signature()["material"] == initial_revision + 2


def test_add_orthotropic_material_and_anisotropic_rejection_are_explicit() -> None:
    model = FEModel("orthotropic")
    material = model.add_orthotropic_material(
        "panel",
        150.0e9,
        10.0e9,
        8.0e9,
        0.25,
        0.20,
        0.30,
        5.0e9,
        4.0e9,
        3.0e9,
        density=1600.0,
        hill_yield=Hill48Yield(400e6, 300e6, 250e6, 180e6, 170e6, 160e6),
    )
    assert model.get_material("panel") is material
    assert material.hill48_yield is material.hill_yield

    anisotropic = _ExternalOrthotropicMaterial("general")
    anisotropic.elastic_symmetry = "anisotropic"
    with pytest.raises(ValueError, match="general anisotropic elasticity is not supported"):
        model.register_material(anisotropic)

    # Production validation also catches unsupported objects injected by
    # deserializers or legacy callers that bypass registration.
    model.materials["general"] = anisotropic
    report = validate_production_model(model, allow_free_mechanisms=True)
    messages = " ".join(issue.message for issue in report.errors)
    assert report.status == "invalid"
    assert "General anisotropic elasticity is not supported" in messages
