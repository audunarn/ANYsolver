from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "docs/reference_cases/s4_candidate_e1_a_oracle.py"
CONTRACT = ROOT / "docs/reference_cases/s4_candidate_e1_a_contract.json"
OUTPUT = ROOT / "docs/reference_cases/s4_candidate_e1_a_output.json"
CONTRACT_SHA256 = "78ACB0EACC002B79C17A1E2C434FB890F64C7C178CA56493A7145F8E0EC5BFFA"
OUTPUT_SHA256 = "8022ECC3FB9D78637851EAF751044ABEE3C7E09D428160302450B726BD710788"
ORACLE_SHA256 = "DBD69B6A3128848A100F3F76BC21BF3885D041CA2B17CA9EAEF0949E60A2EBEB"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result
        result[key] = value
    return result


def _json(path: Path, sha256: str) -> dict[str, object]:
    raw = path.read_bytes()
    assert _sha(raw) == sha256
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw and raw.endswith(b"\n")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(AssertionError(token)),
    )
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()
    return value


def _run(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(ORACLE), *arguments],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )


def test_e1_a_packet_is_canonical_content_addressed_and_separate() -> None:
    contract = _json(CONTRACT, CONTRACT_SHA256)
    output = _json(OUTPUT, OUTPUT_SHA256)
    assert _sha(ORACLE.read_bytes()) == ORACLE_SHA256
    assert contract["candidate_id"] == output["candidate_id"]
    assert contract["scientific_terminal"]["value"] == output["candidate_terminal"]
    assert output["overall_release_terminal"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert output["production"] == {
        "legacy_shell_default": True,
        "public_api_changed": False,
        "selector_available": False,
        "serialization_changed": False,
    }
    assert output["e1_r_combined_or_used"] is False
    assert contract["allowed_extent"]["production_paths"] == []


def test_e1_a_oracle_is_stdlib_only_and_repeats_exact_bytes() -> None:
    tree = ast.parse(ORACLE.read_text(encoding="utf-8"), filename=str(ORACLE))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            imports.add(node.module.split(".")[0])
    assert imports <= {"__future__", "argparse", "ast", "fractions", "hashlib", "json", "pathlib", "sys"}
    assert _run("--emit-contract").stdout == CONTRACT.read_bytes()
    args = ("--run", "--contract", str(CONTRACT), "--contract-sha256", CONTRACT_SHA256)
    first, second = _run(*args), _run(*args)
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout == OUTPUT.read_bytes()


def test_e1_a_contract_failures_block_without_overwrite(tmp_path: Path) -> None:
    before = OUTPUT.read_bytes()
    wrong = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", "0" * 64)
    assert wrong.returncode == 2 and wrong.stderr == b""
    assert json.loads(wrong.stdout)["terminal"] == "BLOCKED_CANDIDATE_E1_NONDETERMINISTIC_EXECUTION"
    malformed = tmp_path / "contract.json"
    malformed.write_bytes(b'{"x":1,"x":2}\n')
    ns = runpy.run_path(str(ORACLE))
    try:
        ns["_decode"](malformed.read_bytes())
    except ns["BaselineMismatch"]:
        pass
    else:
        raise AssertionError("duplicate-key contract did not fail closed")
    function_globals = ns["_load_contract"].__globals__
    original = function_globals["build_contract"]
    def drift() -> dict[str, object]:
        raise ns["BaselineMismatch"]("synthetic baseline drift")
    function_globals["build_contract"] = drift
    try:
        ns["_load_contract"](CONTRACT, CONTRACT_SHA256)
    except ns["BaselineMismatch"]:
        pass
    else:
        raise AssertionError("baseline drift was misclassified as a contract fault")
    finally:
        function_globals["build_contract"] = original
    assert OUTPUT.read_bytes() == before


def test_e1_a_preserves_all_historical_terminals_and_production_sources() -> None:
    output = _json(OUTPUT, OUTPUT_SHA256)
    assert output["immutable_results"] == {
        "candidate_a": "NO_GO_CANDIDATE_A_DISCRETE_PAIR",
        "candidate_b": "NO_GO_CANDIDATE_B",
        "candidate_c": "NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP",
        "candidate_e0": "BLOCKED_CANDIDATE_E_SOURCE_OR_IDENTITY",
        "rank_four": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
    }
    baseline = json.loads((ROOT / "docs/reference_cases/s4_candidate_e1_baseline.json").read_text(encoding="utf-8"))
    for relative, record in baseline["production_sources"].items():
        raw = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        assert b"\r" not in raw
        assert len(raw) == record["canonical_lf_bytes"]
        assert _sha(raw) == record["canonical_lf_sha256"]
