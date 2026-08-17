from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "docs/reference_cases/e4_pl_oracle.py"
CONTRACT = ROOT / "docs/reference_cases/e4_pl_contract.json"
OUTPUT = ROOT / "docs/reference_cases/e4_pl_output.json"
FROZEN_BRANCH = {
    "docs/E4_PL_VARIATIONAL_CLOSURE.md": (8302, "14BDA35109FE8C653B85BF890C36CC454CDE938BCDC3820CA39479EC620EFB4D"),
    "docs/reference_cases/e4_pl_cases.json": (4064, "37D0BA2197246A8D752916EDF40BBDF8E946946E93756C1B042FE374DFF53B59"),
    "docs/reference_cases/e4_pl_source_map.json": (3460, "8919A38DB727D5E863DA70161209C80F2A0F01851392A13A3080354F849B6B66"),
}


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
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    return value


def _run(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONHASHSEED"] = "0"
    return subprocess.run(
        [sys.executable, str(ORACLE), *arguments], cwd=ROOT, env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30,
    )


def test_e4_pl_exact_rank_modes_patches_and_covariance() -> None:
    certificate = runpy.run_path(str(ORACLE))["build_certificate"]()
    assert certificate["terminal"] == "PROVISIONAL_GO_E4_PL_LINEAR_QUALIFICATION_PLAN"
    assert certificate["identity"] == {
        "basis": ["1", "r", "s"],
        "core_operator": "SOURCE_EXACT_WG_D_Q_K0",
        "core_internal_parameters": 35,
        "deleted_only": "rotation_only_r_s_coefficient",
        "element_local_multiplier_parameters": 3,
        "external_coordinates": 24,
        "full_local_internal_parameters": 38,
        "scalar_normalization": "MITC9i_18_19_WITH_GAMMA_EQUAL_G",
        "surface_reduction": "h_times_stress_multiplier_functional",
    }
    for geometry in certificate["geometries"].values():
        assert geometry["retained_constraint_rank"] == 3
        assert geometry["hourglass_rank"] == 1
        assert geometry["combined_constraint_hourglass_rank"] == 4
        assert geometry["deleted_rs_translation_support"] == 0
        assert geometry["rank"] == 18 and geometry["nullity"] == 6
        assert geometry["psd_gram_decomposition"] is True
        assert geometry["source_exact_core"] == {
            "S_ldl_positive": True,
            "generic_I35_surrogate_used": False,
            "ranks": {"D": 35, "F": 14, "Gq": 14, "H": 21, "K0": 14},
        }
        assert all(geometry["rigid_images_zero"].values())
        covariance = geometry["covariance"]
        assert covariance["d4_count"] == 8
        assert all(value is True for key, value in covariance.items() if key != "d4_count")
        energies = geometry["energies"]
        assert energies["pure_common_drill"]["constraint"] == ["1", "0", "0"]
        assert energies["translation_only_spin"]["constraint"] == ["-1", "0", "0"]
        assert energies["matched_rigid_spin"]["pl_energy"] == "0"
        assert energies["matched_rigid_spin"]["hourglass_energy"] == "0"
        assert energies["alternating_drill"]["pl_energy"] == "0"
        assert energies["alternating_drill"]["hourglass_action"] == "1"
        for patch in ("constant_membrane_x", "constant_symmetric_shear", "bending_and_transverse_shear_decoupling"):
            assert energies[patch]["pl_energy"] == energies[patch]["hourglass_energy"] == "0"


def test_e4_pl_38_field_parity_material_recovery_and_sensitivity() -> None:
    certificate = runpy.run_path(str(ORACLE))["build_certificate"]()
    assert certificate["constitutive"] == {
        "E": "5/2", "G": "1", "h": "1", "new_public_material_inputs": [], "nu": "1/4"
    }
    for geometry in certificate["geometries"].values():
        parity = geometry["mixed_condensed"]
        assert parity["internal_block_dimension"] == 38
        assert parity["internal_block_invertible"] is True
        assert parity["stationarity"] is True
        assert parity["energy_parity"] is True
        assert parity["residual_parity"] is True
        assert parity["virtual_work_parity"] is True
        assert parity["tangent_parity"] is True
        assert parity["symmetric_tangent"] is True
    assert certificate["recovery"] == {
        "hourglass_and_multiplier_are_numerical_diagnostics": True,
        "physical_N_M_Q_from_WG_core_only": True,
    }
    assert certificate["sensitivity"] == {
        "classification_unchanged": True,
        "ranks": {
            "epsilon": {"1/100": 18, "1/1000": 18, "1/10000": 18},
            "gamma_over_G": {"1": 18, "1/10": 18, "10": 18},
        },
        "role": "DIAGNOSTIC_ONLY_NO_TUNING",
    }
    assert certificate["historical_hostile_terminals"] == {
        "candidate_a": "NO_GO_CANDIDATE_A_DISCRETE_PAIR",
        "candidate_b": "NO_GO_CANDIDATE_B",
        "candidate_c": "NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP",
        "candidate_e1_a": "NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY",
        "candidate_e2_a": "BLOCKED_E2_A_SOURCE_OR_FORMULATION_IDENTITY",
    }


def test_e4_pl_packet_is_content_addressed_and_caller_bound() -> None:
    contract, output = _json(CONTRACT), _json(OUTPUT)
    for relative, expected in FROZEN_BRANCH.items():
        raw = (ROOT / relative).read_bytes()
        assert (len(raw), _sha(raw)) == expected
        assert contract["input_identities"][relative] == {
            "bytes": expected[0], "path": relative, "sha256": expected[1]
        }
    assert contract["core_prerequisite"] == "GO_E4_OPEN_CORE_IDENTITY"
    assert _json(ROOT / "docs/reference_cases/e4_core_output.json")["terminal"] == contract["core_prerequisite"]
    contract_sha = _sha(CONTRACT.read_bytes())
    assert output["contract_sha256"] == contract_sha
    assert output["terminal"] == contract["scientific_terminal"] == "PROVISIONAL_GO_E4_PL_LINEAR_QUALIFICATION_PLAN"
    emit = _run("--emit-contract")
    assert emit.returncode == 0 and emit.stderr == b"" and emit.stdout == CONTRACT.read_bytes()
    first = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", contract_sha)
    second = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", contract_sha)
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b"" and first.stdout == second.stdout == OUTPUT.read_bytes()
    wrong = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", "A" * 64)
    assert wrong.returncode == 2 and json.loads(wrong.stdout)["terminal"] == "BLOCKED_E4_CONTRACT_NONDETERMINISM_OR_REVIEW"


def test_e4_pl_oracle_is_stdlib_deterministic_and_rejects_bad_json(tmp_path: Path) -> None:
    tree = ast.parse(ORACLE.read_text(encoding="utf-8"), filename=str(ORACLE))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            imports.add(node.module.split(".")[0])
    assert imports <= {"__future__", "argparse", "fractions", "hashlib", "json", "pathlib", "sys"}
    first, second = _run("--certificate"), _run("--certificate")
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b"" and first.stdout == second.stdout
    namespace = runpy.run_path(str(ORACLE))
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_bytes(b'{"x":1,"x":2}\n')
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_bytes(b'{"x":-Infinity}\n')
    with pytest.raises(namespace["EvidenceError"]):
        namespace["_load_json"](duplicate)
    with pytest.raises(namespace["EvidenceError"]):
        namespace["_load_json"](nonfinite)
