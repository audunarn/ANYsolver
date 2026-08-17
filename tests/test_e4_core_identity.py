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
CASES = ROOT / "docs/reference_cases/e4_core_cases.json"
ORACLE = ROOT / "docs/reference_cases/e4_core_oracle.py"
CONTRACT = ROOT / "docs/reference_cases/e4_core_contract.json"
OUTPUT = ROOT / "docs/reference_cases/e4_core_output.json"
FROZEN_INPUTS = {
    "docs/agent_plans/S4_E4_VARIATIONAL_DRILL_CLOSURE_PLAN.md": (5570, "BE515556E2019CDE69E4E7489FD9200F16CDE8D82C032131776EA0520DEB59A1"),
    "docs/E4_OPEN_CORE_IDENTITY.md": (6688, "BAFC21DC85C0CD9101C30ACC5D84F4BC57F3394EA4C0AEFB31CCFA7E43655E5D"),
    "docs/reference_cases/e4_baseline.json": (3309, "7A404185E3F15FA56B589264FA5C816031B3BF25BA8003D081844B517EABB793"),
    "docs/reference_cases/e4_environment.json": (1235, "EC3FE4B95C556F8CF6983083FD29EBA974D9FB953E33017CA3C37CBDC37B3B6F"),
    "docs/reference_cases/e4_test_inventory.json": (3581, "9B6F67242586BFC5A661D2790AFA8774254D68116871D8ACA4E3D1F126D220DA"),
    "docs/reference_cases/e4_source_registry.json": (3421, "66C395568FB4BCC90BCD57D9B8167E204C92A4390BBA643F3FA8516470CA4FA3"),
    "docs/reference_cases/e4_allowed_extent.json": (2052, "A34D96E442DADA69F7EBD2A9E3888B2885386431BC82D6BF80AD57B851A9842E"),
    "docs/reference_cases/e4_core_source_map.json": (2758, "594C74AD59486AE6A23074079E610ED9E1625DA15B626A97BB98E31ED55F1EC1"),
    "docs/reference_cases/e4_core_cases.json": (5435, "FE08E59D9E01073E04251C52544EDF10C4CC86861EA8B98FC6CB1A645427FEF2"),
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
    canonical = (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    assert raw == canonical
    return value


def _run(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONHASHSEED"] = "0"
    return subprocess.run(
        [sys.executable, str(ORACLE), *arguments], cwd=ROOT, env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30,
    )


def test_e4_core_exact_coordinate_split_rank_and_rigid_modes() -> None:
    namespace = runpy.run_path(str(ORACLE))
    certificate = namespace["build_certificate"]()
    assert certificate["terminal"] == "GO_E4_OPEN_CORE_IDENTITY"
    assert certificate["coordinate_split"] == {
        "QD_T_QD_I4": True,
        "T5_T_QD_zero": True,
        "T5_T_T5_I20": True,
        "complete_I24": True,
    }
    assert certificate["dimensions"] == {"core_internal": 35, "external": 24, "physical": 20}
    assert certificate["embedding"]["embedded_rank"] == 14
    assert certificate["embedding"]["embedded_nullity"] == 10
    assert certificate["embedding"]["direct_drill_load_projection"] == ["0"] * 4
    for geometry in certificate["geometries"].values():
        assert geometry["ranks"] == {"D": 35, "F": 14, "Gq": 14, "H": 21, "K5": 14}
        assert geometry["nullity"] == 6
        assert geometry["B_polynomial_rank"] == 14
        assert geometry["Gq_B_row_equivalent"] is True
        assert geometry["S_ldl_positive"] is True
        assert all(geometry["rigid_images_zero"].values())
    registered = _json(CASES)["source_exact_operator"]["square_matrix_signatures"]
    expected_hashes = {key: value for key, value in registered.items() if key != "canonicalization"}
    assert certificate["normalized_square"]["matrix_signatures"] == expected_hashes


def test_e4_core_stationary_mixed_condensed_load_and_recovery_parity() -> None:
    certificate = runpy.run_path(str(ORACLE))["build_certificate"]()
    parity = certificate["mixed_condensed"]
    assert parity["internal_block_dimension"] == 35
    assert parity["internal_block_invertible"] is True
    assert parity["internal_stationarity"] is True
    assert parity["energy_parity"] is True
    assert parity["residual_parity"] is True
    assert parity["tangent_parity"] is True
    assert parity["virtual_work_parity"] is True
    embedding = certificate["embedding"]
    assert embedding["physical_load_work_parity"] is True
    assert embedding["recovery_parity"] is True
    assert certificate["scope"] == {
        "core_classification_operator": "SOURCE_EXACT_WG_F_G_H_D_S_K5",
        "direct_drill_moments": "EXCLUDED",
        "generic_I35_surrogate": "FORBIDDEN_NOT_USED",
        "mass": "DEFERRED_NOT_RUN",
        "nonlinear_and_buckling": "DEFERRED_NOT_RUN",
    }


def test_e4_core_packet_is_content_addressed_and_caller_bound() -> None:
    contract, output = _json(CONTRACT), _json(OUTPUT)
    identities = contract["input_identities"]
    for relative, expected in FROZEN_INPUTS.items():
        raw = (ROOT / relative).read_bytes()
        assert (len(raw), _sha(raw)) == expected
        assert identities[relative] == {"bytes": expected[0], "path": relative, "sha256": expected[1]}
    oracle_relative = ORACLE.relative_to(ROOT).as_posix()
    oracle_raw = ORACLE.read_bytes()
    assert identities[oracle_relative] == {
        "bytes": len(oracle_raw), "path": oracle_relative, "sha256": _sha(oracle_raw)
    }
    contract_sha = _sha(CONTRACT.read_bytes())
    assert contract["scientific_terminal"] == output["terminal"] == "GO_E4_OPEN_CORE_IDENTITY"
    assert output["contract_sha256"] == contract_sha
    emitted = _run("--emit-contract")
    assert emitted.returncode == 0 and emitted.stderr == b"" and emitted.stdout == CONTRACT.read_bytes()
    first = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", contract_sha)
    second = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", contract_sha)
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout == OUTPUT.read_bytes()
    wrong = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", "0" * 64)
    assert wrong.returncode == 2
    assert json.loads(wrong.stdout)["terminal"] == "BLOCKED_E4_CONTRACT_NONDETERMINISM_OR_REVIEW"


def test_e4_core_oracle_is_stdlib_deterministic_and_rejects_bad_json(tmp_path: Path) -> None:
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
    nonfinite.write_bytes(b'{"x":NaN}\n')
    with pytest.raises(namespace["EvidenceError"]):
        namespace["_load_json"](duplicate)
    with pytest.raises(namespace["EvidenceError"]):
        namespace["_load_json"](nonfinite)
