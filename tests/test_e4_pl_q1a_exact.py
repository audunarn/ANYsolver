from __future__ import annotations

import ast
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "docs/reference_cases/e4_pl_q1a_oracle.py"
REFERENCE = ROOT / "docs/reference_cases/e4_pl_q1a_reference.py"
CONTRACT = ROOT / "docs/reference_cases/e4_pl_q1a_contract.json"
OUTPUT = ROOT / "docs/reference_cases/e4_pl_q1a_output.json"
SCIENTIFIC_TERMINAL = "NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE"
REFERENCE_AGREEMENT_SHA = "E2AB0103721712E610D203BA4A2649BBE86E8FDC4B8061BA8A9FBF8056C73BF5"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result
        result[key] = value
    return result


def _json(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw and raw.endswith(b"\n")
    value = json.loads(
        raw.decode("utf-8"), object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(AssertionError(token)),
    )
    assert isinstance(value, dict)
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    return value


def _run(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment.update({
        "OMP_NUM_THREADS": "1", "OMP_STACKSIZE": "1G",
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
    })
    return subprocess.run(
        [sys.executable, str(ORACLE), *arguments], cwd=ROOT, env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=180,
    )


@lru_cache(maxsize=1)
def _certificate() -> dict[str, object]:
    return runpy.run_path(str(ORACLE))["build_certificate"]()


def _reference() -> tuple[int, dict[str, object]]:
    environment = os.environ.copy()
    environment.update({
        "OMP_NUM_THREADS": "1", "OMP_STACKSIZE": "1G",
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
    })
    process = subprocess.run(
        [sys.executable, str(REFERENCE)], cwd=ROOT, env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=180,
    )
    assert process.stderr == b""
    value = json.loads(
        process.stdout.decode("utf-8"), object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(AssertionError(token)),
    )
    assert process.stdout == (json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ) + "\n").encode("utf-8")
    return process.returncode, value


def _oracle_agreement(certificate: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for case_id, record in certificate["geometry_results"].items():
        physical = record["physical_patches"]

        def patch(name: str) -> dict[str, bool]:
            source = physical[name]
            return {
                "energy_exact": source["energy_exact"],
                "gauss_strain_exact": source["compatible_strain_exact"],
                "numerical_zero": source["matched_drill_numerical_zero"],
                "recovery_exact": source["stationary_resultant_exact"],
            }

        numerical = record["patch_numerical_actions_zero"]
        result[case_id] = {
            "core_ranks": record["core_ranks"],
            "internal_block_rank": record["internal_block_rank"],
            "kdd_ldl_positive": record["kdd_ldl_positive"],
            "local_physical_schur_equals_k5": record["local_physical_schur_equals_k5"],
            "nullity": record["nullity"],
            "numerical_patch_actions_zero": {
                "bending_shear_decoupling": numerical["constant_bending_x"],
                "constant_extension": numerical["constant_membrane_x"],
                "constant_symmetric_shear": numerical["constant_symmetric_shear"],
                "general_affine_membrane_with_spin": numerical["combined_membrane"],
            },
            "physical_patches": {
                "bending": patch("constant_bending_x"),
                "combined": patch("combined_physical"),
                "membrane_nonzero_spin": patch("combined_membrane"),
                "transverse_shear": patch("constant_transverse_shear_x"),
            },
            "r_map_rank": record["r_map_rank"],
            "rank": record["rank"],
            "residual_drill_row": record["residual_drill_row"],
            "rigid_images_zero": record["rigid_images_zero"],
        }
    return result


def test_e4_pl_q1a_exact_affine_reproduction_and_actual_38_field_algebra() -> None:
    certificate = _certificate()
    assert certificate["terminal"] == SCIENTIFIC_TERMINAL
    assert certificate["candidate_id"] == (
        "candidate_e4_pl_q1.wg2020_n7_k0_surface_pl_planar_linear_iso_v1"
    )
    assert certificate["coordinate_split"] == {
        "QD_T_QD_I4": True, "T5_T_QD_zero": True, "T5_T_T5_I20": True,
    }
    affine = certificate["affine_reproduction"]
    accepted = _json(ROOT / "docs/reference_cases/e4_core_cases.json")
    signatures = accepted["source_exact_operator"]["square_matrix_signatures"]
    for name in ("D", "F", "Gq", "H", "K5", "S"):
        assert affine["accepted_core_matrix_signatures"][name] == signatures[name]
    assert affine["accepted_drill_rows_exact"] is True

    assert set(certificate["geometry_results"]) == {
        "unit_square", "affine_skew", "trapezoid", "tapered_skew",
    }
    expected_actions = {
        "alternating_drill": ["0", "0", "0", "1"],
        "matched_rigid_spin": ["0", "0", "0", "0"],
        "pure_common_drill": ["1", "0", "0", "0"],
        "translation_only_spin": ["-1", "0", "0", "0"],
    }
    for result in certificate["geometry_results"].values():
        assert result["arithmetic"] == "Q(sqrt(3))"
        assert result["core_ranks"] == {"D": 35, "F": 14, "Gq": 14, "H": 21, "K5": 14}
        assert result["internal_block_rank"] == 38
        assert result["r_map_rank"] == 4 and result["kdd_ldl_positive"] is True
        assert result["local_physical_schur_equals_k5"] is True
        assert result["rank"] == 18
        assert result["nullity"] == 6
        assert result["mode_actions"] == expected_actions
        assert all(result["rigid_images_zero"].values())
        assert all(result["patch_numerical_actions_zero"].values())
        assert all(all(checks.values()) for checks in result["physical_patches"].values())
        assert all(result["mixed_condensed"].values())
    assert certificate["geometry_results"]["unit_square"]["residual_drill_row"] == [
        "1/4", "-1/4", "1/4", "-1/4",
    ]
    assert certificate["geometry_results"]["affine_skew"]["residual_drill_row"] == [
        "1/4", "-1/4", "1/4", "-1/4",
    ]
    for name in ("trapezoid", "tapered_skew"):
        assert certificate["geometry_results"][name]["residual_drill_row"] == [
            "3/14", "-3/14", "2/7", "-2/7",
        ]
    assert certificate["component_ledger"] == {
        "dnv_material_recovery_contract": "GO_E4_PL_Q1A_DNV_MATERIAL_RECOVERY",
        "full_covariance": SCIENTIFIC_TERMINAL,
        "local_algebra": "GO_E4_PL_Q1A_LOCAL_ALGEBRA",
        "patch_fields": "GO_E4_PL_Q1A_PHYSICAL_PATCHES",
        "source_planar_identity": "GO_E4_PL_Q1A_SOURCE_PLANAR_IDENTITY",
    }
    assert certificate["patch_failures"] == []


def test_e4_pl_q1a_exact_covariance_recovery_and_material_boundary() -> None:
    certificate = _certificate()
    expected_counts = {
        "unit_square": (8, True),
        "affine_skew": (4, False),
        "trapezoid": (4, False),
        "tapered_skew": (8, True),
    }
    for case_id, result in certificate["geometry_results"].items():
        count, reversal = expected_counts[case_id]
        full = result["full_covariance"]
        assert full["d4_k5_count"] == full["d4_k24_count"] == count
        assert full["d4_k5_congruence"] is (count == 8)
        assert full["d4_k24_congruence"] is (count == 8)
        assert full["orientation_reversal_k5_congruence"] is reversal
        assert full["orientation_reversal_k24_congruence"] is reversal
        assert full["frame_k5_congruence"] is full["frame_k24_congruence"] is True
        assert full["origin_k5_invariant"] is full["origin_k24_invariant"] is True
        assert full["unit_k5_dimensional_congruence"] is True
        assert full["unit_k24_dimensional_congruence"] is True
        assert full["unit_scales"] == ["1/1000", "1000"]
        assert all(all(checks.values()) for checks in full["unit_dimensional_congruence"].values())
    assert certificate["covariance_failures"] == [
        {
            "d4_k24_count": 4, "d4_k5_count": 4, "geometry": "affine_skew",
            "orientation_reversal_k24_congruence": False,
            "orientation_reversal_k5_congruence": False,
        },
        {
            "d4_k24_count": 4, "d4_k5_count": 4, "geometry": "trapezoid",
            "orientation_reversal_k24_congruence": False,
            "orientation_reversal_k5_congruence": False,
        },
    ]
    assert certificate["recovery"] == {
        "physical_resultants_from": "WG_STATIONARY_FIELDS_ONLY",
        "pl_hourglass_in_physical_N_M_Q": False,
        "projected_numerical_reaction_reported_separately": True,
    }
    assert certificate["material_compatibility"] == {
        "density_required_metadata_but_unused": True,
        "dnv_approval": False,
        "grades": ["S235", "S275", "S355", "S420", "S460"],
        "new_public_fields": [],
        "reporting": "compatible with DNV analysis workflows",
        "row_count": 17,
        "row_ranges": {
            "S235": [[0, 16], [16, 40], [40, 63], [63, 100]],
            "S275": [[0, 16], [16, 40], [40, 63]],
            "S355": [[0, 16], [16, 40], [40, 63], [63, 100]],
            "S420": [[0, 16], [16, 40], [40, 63]],
            "S460": [[0, 16], [16, 40], [40, 63]],
        },
        "rp_c208_edition": "September_2019_amended_October_2022",
        "ru_ship_project_edition": "July_2025",
    }
    assert certificate["support_and_load_contract"] == {
        "forbidden_direct_drill_is_pure_QD": True,
        "full_clamp_is_hostile_physical_plus_drill": True,
        "physical_projector_idempotent": True,
        "physical_support_annihilates_QD": True,
        "projectors_orthogonal": True,
    }
    assert certificate["release_terminal"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"


def test_e4_pl_q1a_oracle_is_stdlib_independent_strict_and_deterministic(tmp_path: Path) -> None:
    source = ORACLE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(ORACLE))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            imports.add(node.module.split(".")[0])
    assert imports <= {
        "__future__", "argparse", "dataclasses", "fractions", "hashlib",
        "json", "pathlib", "sys",
    }
    # The reference path is content-addressed by the contract, but no code or
    # certificate is imported or executed by the independent oracle.
    assert "runpy" not in imports and "subprocess" not in imports
    first, second = _run("--certificate"), _run("--certificate")
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b"" and first.stdout == second.stdout
    assert json.loads(first.stdout)["terminal"] == SCIENTIFIC_TERMINAL

    reference_returncode, reference = _reference()
    assert reference_returncode == 2
    assert reference["terminal_hint"] == SCIENTIFIC_TERMINAL
    agreement = _oracle_agreement(_certificate())
    assert agreement == reference["agreement"]
    agreement_sha = _sha((json.dumps(
        agreement, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ) + "\n").encode("utf-8"))
    assert agreement_sha == reference["agreement_sha256"] == REFERENCE_AGREEMENT_SHA
    reference_covariance = {
        record["case_id"]: record["full_covariance"] for record in reference["cases"]
    }
    for case_id, record in _certificate()["geometry_results"].items():
        observed = record["full_covariance"]
        expected = reference_covariance[case_id]
        for key in (
            "d4_k24_congruence", "d4_k24_count", "d4_k5_congruence", "d4_k5_count",
            "frame_k24_congruence", "frame_k5_congruence",
            "orientation_reversal_k24_congruence", "orientation_reversal_k5_congruence",
            "origin_k24_invariant", "origin_k5_invariant",
            "unit_k24_dimensional_congruence", "unit_k5_dimensional_congruence", "unit_scales",
        ):
            assert observed[key] == expected[key]

    namespace = runpy.run_path(str(ORACLE))
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_bytes(b'{"x":1,"x":2}\n')
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_bytes(b'{"x":NaN}\n')
    missing_lf = tmp_path / "missing_lf.json"
    missing_lf.write_bytes(b'{"x":1}')
    for path in (duplicate, nonfinite, missing_lf):
        with pytest.raises(namespace["EvidenceError"]):
            namespace["_load_json"](path)
    terminal_cases = {
        "BaselineMismatch": "BLOCKED_E4_PL_Q1A_BASELINE_MISMATCH",
        "PlanAuthorityError": "BLOCKED_E4_PL_Q1A_PLAN_AUTHORITY",
        "SourceIdentityError": "BLOCKED_E4_PL_Q1A_SOURCE_OR_PLANAR_IDENTITY",
        "ContractError": "BLOCKED_E4_PL_Q1A_CONTRACT_OR_NONDETERMINISM",
        "OracleReviewError": "BLOCKED_E4_PL_Q1A_ORACLE_OR_REVIEW",
        "LocalAlgebraError": "NO_GO_E4_PL_Q1A_LOCAL_ALGEBRA",
        "PatchCovarianceError": "NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE",
        "MaterialRecoveryError": "NO_GO_E4_PL_Q1A_DNV_MATERIAL_OR_RECOVERY_CONTRACT",
        "UnclassifiedError": "UNCLASSIFIED_E4_PL_Q1A_PLANAR_IDENTITY_AND_LOCAL_ALGEBRA",
    }
    for exception_name, terminal in terminal_cases.items():
        assert namespace["_terminal_for"](namespace[exception_name]("probe")) == terminal


def test_e4_pl_q1a_caller_bound_contract_and_output_are_exact() -> None:
    if not CONTRACT.exists() or not OUTPUT.exists():
        pytest.skip("caller-bound commit-2 evidence is intentionally absent before preregistration")
    contract, output = _json(CONTRACT), _json(OUTPUT)
    contract_sha = _sha(CONTRACT.read_bytes())
    assert contract["scientific_terminal"] == SCIENTIFIC_TERMINAL
    assert output["contract_sha256"] == contract_sha
    assert output["terminal"] == SCIENTIFIC_TERMINAL
    emitted = _run("--emit-contract")
    assert emitted.returncode == 0 and emitted.stderr == b""
    assert emitted.stdout == CONTRACT.read_bytes()
    first = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", contract_sha)
    second = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", contract_sha)
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b"" and first.stdout == second.stdout == OUTPUT.read_bytes()
    wrong = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", "A" * 64)
    assert wrong.returncode == 2
    assert json.loads(wrong.stdout)["terminal"] == "BLOCKED_E4_PL_Q1A_CONTRACT_OR_NONDETERMINISM"
    missing = _run("--run")
    assert missing.returncode == 2
    assert json.loads(missing.stdout)["terminal"] == "BLOCKED_E4_PL_Q1A_CONTRACT_OR_NONDETERMINISM"
