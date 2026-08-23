"""Cross-package ownership and compatibility guarantees for ANYsolver 0.3."""

from __future__ import annotations

import anyfileio
import anymaterial
import anymesher

import anysolver
from anysolver import external_references
from anysolver.mesh_gen import InterpolatedBeamShellMPCElement


def test_material_public_api_is_canonical_anymaterial() -> None:
    assert anysolver.Material is anymaterial.IsotropicMaterial
    assert anysolver.OrthotropicMaterial is anymaterial.OrthotropicMaterial
    assert anysolver.Hill48Yield is anymaterial.Hill48Yield
    assert anysolver.DNVC208MaterialCurve is anymaterial.DNVC208MaterialCurve
    assert anysolver.elastic_compliance_matrix is anymaterial.elastic_compliance_matrix


def test_mesh_geometry_public_api_is_canonical_anymesher() -> None:
    assert anysolver.StiffenerCrossSection is anymesher.StiffenerCrossSection


def test_interpolated_beam_shell_mpc_is_available_from_the_root_api() -> None:
    assert anysolver.InterpolatedBeamShellMPCElement is InterpolatedBeamShellMPCElement


def test_file_document_and_result_api_is_canonical_anyfileio() -> None:
    assert anysolver.SesamFemDocument is anyfileio.SesamFemDocument
    assert anysolver.FemRawRecord is anyfileio.FemRawRecord
    assert anysolver.CalculixParsedResults is anyfileio.CalculixParsedResults
    assert external_references.parse_calculix_frd is anyfileio.parse_frd
    assert external_references.parse_calculix_dat is anyfileio.parse_dat
    assert external_references.merge_calculix_results is anyfileio.merge_results


def test_distribution_version_marks_the_extraction_boundary() -> None:
    assert anysolver.__version__ == "0.3.0"
