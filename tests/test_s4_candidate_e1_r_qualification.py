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
ORACLE = ROOT / "docs/reference_cases/s4_candidate_e1_r_oracle.py"
CONTRACT = ROOT / "docs/reference_cases/s4_candidate_e1_r_contract.json"
OUTPUT = ROOT / "docs/reference_cases/s4_candidate_e1_r_output.json"
CONTRACT_SHA256 = "9F3F19DD7BE8868D98E7B487FDD488DB9A77ACA429F12FB9824261551B6F7A4C"
OUTPUT_SHA256 = "ED26CF65363AD97BFA57234EA6CC7C708D8E94B4D477AAC64F5C6BAFB44B749B"
ORACLE_SHA256 = "C45CE53597F5DC5A90B051B7BC336D8BD114A92ACFB20F1BF03A47C2117FA02E"


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


def test_e1_r_packet_is_canonical_limited_and_separate() -> None:
    contract = _json(CONTRACT, CONTRACT_SHA256)
    output = _json(OUTPUT, OUTPUT_SHA256)
    assert _sha(ORACLE.read_bytes()) == ORACLE_SHA256
    assert contract["candidate_id"] == output["candidate_id"]
    assert output["candidate_terminal"] == "PROVISIONAL_GO_CANDIDATE_E1_R_PLANAR_REGULARIZER_ONLY"
    assert output["overall_release_terminal"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert output["qualified_scope"] == {
        "fallback_pattern_only": True,
        "modal_or_transient": False,
        "physical_rank_18_element": False,
        "production_activation": False,
    }
    assert contract["allowed_extent"]["production_paths"] == []


def test_e1_r_oracle_is_stdlib_only_and_repeats_exact_bytes() -> None:
    tree = ast.parse(ORACLE.read_text(encoding="utf-8"), filename=str(ORACLE))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            imports.add(node.module.split(".")[0])
    assert imports <= {"__future__", "argparse", "ast", "fractions", "hashlib", "json", "pathlib", "sys"}
    emitted = _run("--emit-contract")
    assert emitted.returncode == 0 and emitted.stderr == b"" and emitted.stdout == CONTRACT.read_bytes()
    args = ("--run", "--contract", str(CONTRACT), "--contract-sha256", CONTRACT_SHA256)
    first, second = _run(*args), _run(*args)
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout == OUTPUT.read_bytes()


def test_e1_r_contract_and_baseline_failures_are_distinct(tmp_path: Path) -> None:
    before = OUTPUT.read_bytes()
    wrong = _run("--run", "--contract", str(CONTRACT), "--contract-sha256", "0" * 64)
    assert wrong.returncode == 2
    assert json.loads(wrong.stdout)["terminal"] == "BLOCKED_CANDIDATE_E1_NONDETERMINISTIC_EXECUTION"
    malformed = tmp_path / "contract.json"
    malformed.write_bytes(b'{"x":1,"x":2}\n')
    ns = runpy.run_path(str(ORACLE))
    try:
        ns["_decode"](malformed.read_bytes())
    except ns["BaselineMismatch"]:
        pass
    else:
        raise AssertionError("duplicate-key input was accepted")
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
        raise AssertionError("baseline drift was misclassified")
    finally:
        function_globals["build_contract"] = original
    assert OUTPUT.read_bytes() == before


def test_e1_r_all_rp_c208_rows_need_no_new_material_input() -> None:
    fixtures = json.loads((ROOT / "docs/reference_cases/s4_candidate_e1_material_fixtures.json").read_text(encoding="utf-8"))
    inherited = fixtures["inherited_fixture"]
    inherited_raw = (ROOT / inherited["path"]).read_bytes()
    assert len(inherited_raw) == inherited["bytes"] and _sha(inherited_raw) == inherited["sha256"]
    e0 = json.loads(inherited_raw)
    grades = e0["rp_c208_dataset"]["grades"]
    assert sorted(grades) == fixtures["rp_c208"]["grades"]
    assert sum(len(rows) for rows in grades.values()) == fixtures["rp_c208"]["row_count"] == 17
    sibling_src = ROOT.parent / "ANYmaterial" / "src"
    sibling = sibling_src.parent
    revision = subprocess.run(
        ["git", "-c", f"safe.directory={sibling.as_posix()}", "rev-parse", "HEAD", "HEAD^{tree}"],
        cwd=sibling,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert revision.returncode == 0, revision.stderr.decode(errors="replace")
    assert revision.stdout.decode().splitlines() == [fixtures["anymaterial"]["commit"], fixtures["anymaterial"]["tree"]]
    for relative, record in e0["anymaterial"]["files"].items():
        raw = (sibling / relative).read_bytes().replace(b"\r\n", b"\n")
        assert b"\r" not in raw
        assert len(raw) == record["canonical_lf_bytes"]
        assert _sha(raw) == record["canonical_lf_sha256"]
    sys.path.insert(0, str(sibling_src))
    try:
        from anymaterial.library import available_grades, dnv_c208_steel_properties, steel, thickness_classes
        assert list(available_grades()) == fixtures["rp_c208"]["grades"]
        checked = 0
        for grade, rows in grades.items():
            assert len(thickness_classes(grade)) == len(rows)
            for lower, upper in rows:
                millimetres = upper if lower == 0 else (lower + upper) / 2
                properties = dnv_c208_steel_properties(grade, millimetres / 1000)
                material = steel(grade, millimetres / 1000, nonlinear=False)
                nonlinear = steel(grade, millimetres / 1000, nonlinear=True)
                assert properties["grade"] == grade
                assert material.elastic_modulus == properties["E_pa"] == 210_000_000_000
                assert material.poisson_ratio == 0.3 and material.density == 7850
                assert material.hardening_curve is None and nonlinear.hardening_curve is not None
                assert not any(hasattr(material, name) for name in ("drill_modulus", "internal_length", "rotational_micro_inertia"))
                checked += 1
        assert checked == 17
    finally:
        sys.path.remove(str(sibling_src))
    assert fixtures["compatibility"]["dnv_approval"] is False
    assert fixtures["compatibility"]["ru_ship_records_in_anymaterial"] is False
    assert fixtures["compatibility"]["new_public_fields"] == []
