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
ORACLE = ROOT / "docs/reference_cases/e4_ws_oracle.py"
CONTRACT = ROOT / "docs/reference_cases/e4_ws_contract.json"
OUTPUT = ROOT / "docs/reference_cases/e4_ws_output.json"
CASES = ROOT / "docs/reference_cases/e4_ws_cases.json"
FROZEN_BRANCH = {
    "docs/E4_WS_FEASIBILITY_THEOREM.md": (3839, "80E02F2564D6DE6D5E1A66857A78D97FCA83C828AEAB20BFE4707408EAD7BF19"),
    "docs/reference_cases/e4_ws_cases.json": (1224, "07C6ADC51095CF318EAECABECFF193FBB0CE2A2E2B604A9692F111BEBB8892E0"),
    "docs/reference_cases/e4_ws_source_map.json": (1204, "F421572687A814108C92F756DCCB7483429D0E67AA35268E4D6014F1BA9848E4"),
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


def test_e4_ws_zero_multiplier_block_has_no_exact_local_schur_exit() -> None:
    certificate = runpy.run_path(str(ORACLE))["build_certificate"]()
    assert certificate["terminal"] == "NO_GO_E4_WS_LOCAL_CONDENSATION_AND_RANK"
    assert certificate["theorem"] == "FIVE_FROZEN_REQUIREMENTS_CANNOT_HOLD_SIMULTANEOUSLY"
    assert certificate["local_condensation"] == {
        "d_stationarity_lambda_d_lambda_rank": 0,
        "finite_multiplier_schur_exists": False,
        "stationarity_lambda": "C*q=0_contains_no_lambda",
        "unique_lambda_at_fixed_q": False,
    }
    witness = certificate["exact_witness"]
    assert witness == {
        "C_rank": 4,
        "K0_rank": 14,
        "KKT_rank": 22,
        "lambda_block_rank": 0,
        "prohibited_CtC_completion_rank": 18,
    }


def test_e4_ws_all_algebraic_exits_violate_a_frozen_requirement() -> None:
    certificate = runpy.run_path(str(ORACLE))["build_certificate"]()
    alternatives = certificate["alternatives"]
    assert alternatives["reduce_external_coordinates_to_ker_C"] == {
        "dimension": 20, "violates_24_unconstrained": True
    }
    assert alternatives["retain_saddle_multiplier"] == "VIOLATES_NO_GLOBAL_MIXED_UNKNOWN"
    assert alternatives["add_multiplier_compliance_or_regularization"] == "VIOLATES_ZERO_ADDED_ENERGY"
    assert alternatives["add_primal_penalty_or_stabilization"] == "VIOLATES_ZERO_ADDED_ENERGY"
    assert certificate["scope"] == {
        "counterexample_functional_found": False,
        "inf_sup_or_macroelement_work": "STOPPED_NECESSARY_THEOREM",
        "weak_symmetry_methods_generally_impossible": False,
    }


def test_e4_ws_packet_is_exact_deterministic_and_caller_bound(tmp_path: Path) -> None:
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
    assert output["terminal"] == contract["scientific_terminal"] == "NO_GO_E4_WS_LOCAL_CONDENSATION_AND_RANK"
    emit = _run("--emit-contract")
    assert emit.returncode == 0 and emit.stderr == b"" and emit.stdout == CONTRACT.read_bytes()
    first = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", contract_sha)
    second = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", contract_sha)
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b"" and first.stdout == second.stdout == OUTPUT.read_bytes()
    wrong = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", "F" * 64)
    assert wrong.returncode == 2 and json.loads(wrong.stdout)["terminal"] == "BLOCKED_E4_CONTRACT_NONDETERMINISM_OR_REVIEW"
    tree = ast.parse(ORACLE.read_text(encoding="utf-8"), filename=str(ORACLE))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            imports.add(node.module.split(".")[0])
    assert imports <= {"__future__", "argparse", "fractions", "hashlib", "json", "pathlib", "sys"}
    first_certificate, second_certificate = _run("--certificate"), _run("--certificate")
    assert first_certificate.returncode == second_certificate.returncode == 0
    assert first_certificate.stderr == second_certificate.stderr == b""
    assert first_certificate.stdout == second_certificate.stdout
    namespace = runpy.run_path(str(ORACLE))
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_bytes(b'{"x":1,"x":2}\n')
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_bytes(b'{"x":Infinity}\n')
    with pytest.raises(namespace["EvidenceError"]):
        namespace["_load_json"](duplicate)
    with pytest.raises(namespace["EvidenceError"]):
        namespace["_load_json"](nonfinite)
