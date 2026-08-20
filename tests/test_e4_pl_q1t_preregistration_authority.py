from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BASE = "914a9a633c585d45a419d97f92b4faf7fa1e4486"
BASE_TREE = "569c0b15c9e5d50835fa5fe16414d5d1864d0106"
BASE_PARENT = "00d6a66c34712c8f3fd1e38113c83d0a03b2de43"
BRANCH = "codex/s4-e4-pl-q1t-exact-oracle-completion"
COMMIT1_SUBJECT = "docs: preregister E4 PL Q1T exact-oracle completion"
ATTACHMENT = Path(
    r"C:\Users\AudunArnesenNyhus\Downloads\S4_E4_PL_Q1T_EXACT_ORACLE_COMPLETION_PLAN.md"
)
ATTACHMENT_BYTES = 28_982
ATTACHMENT_SHA = "2B546D1621A576A7A48F34130CF87B3F08F6D0E20C16838C4F26708981604BEB"
ENV_SHA = "5461206324E7FC2A52B334CE736A512EE71313ED79181438047E3E20069A9746"

PLAN_PATHS = {
    "docs/agent_plans/S4_E4_PL_Q1T_EXACT_ORACLE_COMPLETION_PLAN.md",
    "docs/reference_cases/e4_pl_q1t_plan_review.json",
    "docs/reference_cases/e4_pl_q1t_baseline.json",
    "docs/reference_cases/e4_pl_q1t_inheritance_manifest.json",
    "docs/reference_cases/e4_pl_q1t_rejected_evidence_manifest.json",
    "docs/reference_cases/e4_pl_q1t_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1t_environment.json",
    "docs/reference_cases/e4_pl_q1t_environment_builder.py",
    "docs/reference_cases/e4_pl_q1t_exact_backend_contract.json",
    "docs/reference_cases/e4_pl_q1t_certificate_schema.json",
    "docs/reference_cases/e4_pl_q1t_authority_contract.json",
    "docs/reference_cases/e4_pl_q1t_terminal_table.json",
    "docs/reference_cases/e4_pl_q1t_test_inventory.json",
    "tests/test_e4_pl_q1t_preregistration_authority.py",
}

LATER_PATHS = {
    "docs/reference_cases/e4_pl_q1t_reference.py",
    "docs/reference_cases/e4_pl_q1t_oracle.py",
    "docs/reference_cases/e4_pl_q1t_scientific_test_runner.py",
    "docs/reference_cases/e4_pl_q1t_implementation_manifest.json",
    "docs/reference_cases/e4_pl_q1t_implementation_review.json",
    "tests/test_e4_pl_q1t_exact_backend.py",
    "tests/test_e4_pl_q1t_frame_and_fields.py",
    "tests/test_e4_pl_q1t_local_algebra.py",
    "tests/test_e4_pl_q1t_recovery.py",
    "tests/test_e4_pl_q1t_global_supports.py",
    "tests/test_e4_pl_q1t_terminal_and_agreement.py",
    "docs/reference_cases/e4_pl_q1t_execution_contract.json",
    "docs/reference_cases/e4_pl_q1t_contract_review.json",
    "tests/test_e4_pl_q1t_contract.py",
    "docs/reference_cases/e4_pl_q1t_reference_raw.json",
    "docs/reference_cases/e4_pl_q1t_oracle_raw.json",
    "docs/reference_cases/e4_pl_q1t_agreement.json",
    "docs/reference_cases/e4_pl_q1t_output.json",
    "docs/reference_cases/e4_pl_q1t_status.json",
    "docs/reference_cases/e4_pl_q1t_execution_authority.json",
    "docs/reference_cases/e4_pl_q1t_scientific_test_result.json",
    "docs/E4_PL_Q1T_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1t_scientific_review.json",
    "docs/E4_PL_Q1T_COMPLETION.md",
    "tests/test_e4_pl_q1t_closeout.py",
}


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=check, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def _raw(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _strict(raw: bytes) -> object:
    def pairs(rows: list[tuple[str, object]]) -> dict[str, object]:
        out: dict[str, object] = {}
        for key, value in rows:
            if key in out:
                raise ValueError(f"duplicate key: {key}")
            out[key] = value
        return out

    def nonfinite(token: str) -> object:
        raise ValueError(f"nonfinite: {token}")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def _canonical(path: str) -> dict[str, object]:
    raw = _raw(path)
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw
    value = _strict(raw)
    assert isinstance(value, dict)
    expected = (json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ) + "\n").encode("utf-8")
    assert raw == expected, path
    return value


def _commit_blob_row(row: dict[str, object]) -> None:
    path = str(row["path"])
    commit = str(row["source_commit"])
    raw = subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout
    assert len(raw) == row["bytes"], path
    assert _sha(raw) == row["sha256"], path
    assert _git("rev-parse", f"{commit}:{path}").stdout.strip() == row["git_blob"]


def test_q1t_baseline_and_expanded_inheritance_are_exact() -> None:
    assert _git("branch", "--show-current").stdout.strip() == BRANCH
    assert _git("rev-parse", f"{BASE}^{{tree}}").stdout.strip() == BASE_TREE
    assert _git("rev-parse", f"{BASE}^").stdout.strip() == BASE_PARENT
    assert _git("show", "-s", "--format=%s", BASE).stdout.strip() == (
        "docs: close E4 PL Q1S implementation-identity block"
    )
    raw_attachment = ATTACHMENT.read_bytes()
    assert len(raw_attachment) == ATTACHMENT_BYTES
    assert _sha(raw_attachment) == ATTACHMENT_SHA

    baseline = _canonical("docs/reference_cases/e4_pl_q1t_baseline.json")
    assert baseline["mandatory_base"]["commit"] == BASE
    assert baseline["mandatory_base"]["tree"] == BASE_TREE
    assert baseline["q1s_preflight"]["node_count"] == 1
    assert baseline["q1s_preflight"]["required_result"] == "PASS"

    inherited = _canonical("docs/reference_cases/e4_pl_q1t_inheritance_manifest.json")
    assert inherited["counts"] == {
        "expanded_q1r_e4_inputs": 23,
        "q1s_closeout_inputs": 15,
        "q1s_commit1_inputs": 11,
        "total_directly_bound_inputs": 49,
    }
    rows = inherited["q1r_e4_inherited_inputs"] + inherited["q1s_commit1_inputs"] + inherited["q1s_closeout_inputs"]
    assert len(rows) == 49
    assert len({(row["source_commit"], row["path"]) for row in rows}) == 49
    for row in rows:
        _commit_blob_row(row)

    rejected = _canonical("docs/reference_cases/e4_pl_q1t_rejected_evidence_manifest.json")
    assert rejected["classification"] == "REJECTED_STATIC_EVIDENCE"
    assert rejected["rejected_path_count"] == 10
    assert len(rejected["rejected_paths"]) == 10
    assert rejected["disposition"]["q1s_oracle"] == "FORBIDDEN_IMPLEMENTATION_INPUT"
    assert rejected["disposition"]["scientific_classification"] == "NOT_ESTABLISHED"


def test_q1t_environment_builder_and_toy_backend_capabilities() -> None:
    record_raw = _raw("docs/reference_cases/e4_pl_q1t_environment.json")
    record = _canonical("docs/reference_cases/e4_pl_q1t_environment.json")
    assert _sha(record_raw) == ENV_SHA
    assert record["absolute_paths_recorded"] is False
    assert record["extracted_file_count"] == 1662
    assert record["mpmath_categorical_evidence_permitted"] is False
    assert set(record["toy_sympy_capability_probes"].values()) == {True}
    graph = record["extracted_file_hash_graph"]
    assert len(graph) == 1662
    assert [row["path"] for row in graph] == sorted(row["path"] for row in graph)
    assert all(not Path(row["path"]).is_absolute() and ".." not in Path(row["path"]).parts for row in graph)

    backend = _canonical("docs/reference_cases/e4_pl_q1t_exact_backend_contract.json")
    assert backend["environment"]["environment_record_sha256"].upper() == ENV_SHA
    assert backend["e_numbering_fields"]["formal_degree_maximum"] == 32
    assert [row["id"] for row in backend["e_numbering_fields"]["generator_schedule"]] == ["g1", "g2", "g3", "g4", "g5"]
    assert backend["exact_equality"]["allowed"] == "QQ.algebraic_field_domain_element_equality_with_field_zero"
    assert backend["expression_and_sign"]["interval_engine"] == "independent_standard_library_dyadic_outward_interval"

    path = ROOT / "docs/reference_cases/e4_pl_q1t_environment_builder.py"
    spec = importlib.util.spec_from_file_location("q1t_environment_builder", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._safe_member_name("sympy/core/basic.py") == "sympy/core/basic.py"
    with pytest.raises(module.BuildError):
        module._safe_member_name("../escape")
    with pytest.raises(module.BuildError):
        module._safe_member_name("/absolute")


def test_q1t_stage_extent_reviews_and_authority_are_exact() -> None:
    with pytest.raises(ValueError):
        _strict(b'{"x":1,"x":2}\n')
    with pytest.raises(ValueError):
        _strict(b'{"x":NaN}\n')

    allowed = _canonical("docs/reference_cases/e4_pl_q1t_allowed_extent.json")
    assert allowed["path_count"] == 39
    assert allowed["stage_counts"] == {"CONTRACT": 3, "IMPLEMENTATION": 11, "OUTCOME": 11, "PLAN": 14}
    assert set(allowed["path_sets"]["PLAN"]) == PLAN_PATHS
    assert set(allowed["path_sets"]["IMPLEMENTATION"] + allowed["path_sets"]["CONTRACT"] + allowed["path_sets"]["OUTCOME"]) == LATER_PATHS
    assert allowed["sole_existing_file_modifications"] == []

    authority = _canonical("docs/reference_cases/e4_pl_q1t_authority_contract.json")
    assert set(authority["stage_extents"]["PLAN"]) == PLAN_PATHS
    assert [row["path_count"] for row in authority["commit_stages"]] == [14, 11, 3, 11]
    assert authority["correction_limits"]["outcome_or_science_after_first_registered_process"]["max"] == 0
    assert authority["blocked_closeout_protocol"]["exact_review_verdict"] == "ACCEPT_Q1T_BLOCKED_CLOSEOUT_NO_P0_P1"

    inventory = _canonical("docs/reference_cases/e4_pl_q1t_test_inventory.json")
    assert inventory["preregistration_inventory"]["count"] == 4
    assert inventory["exact_backend_inventory"]["count"] == 1
    assert inventory["scientific_inventory"]["count"] == 5
    assert inventory["contract_guard_inventory"]["count"] == 4
    assert inventory["closeout_inventory"]["count"] == 1
    assert inventory["inventories_must_not_be_combined"] is True

    review = _canonical("docs/reference_cases/e4_pl_q1t_plan_review.json")
    assert set(review) == {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
    assert review["verdict"] == "ACCEPT_Q1T_PREREGISTRATION_NO_P0_P1"
    expected = []
    for path in sorted(PLAN_PATHS - {"docs/reference_cases/e4_pl_q1t_plan_review.json"}):
        raw = _raw(path)
        expected.append({"bytes": len(raw), "path": path, "sha256": _sha(raw)})
    assert review["reviewed_inputs"] == expected
    assert review["reviewer_independence"] == {
        "authored_review_only": True,
        "mechanics_executed": False,
        "reviewed_input_authorship": False,
        "role": "INDEPENDENT_PLAN_ONLY_REVIEWER",
    }
    assert review["findings"] == []

    tracked = {p.replace("\\", "/") for p in _git("diff", "--name-only", BASE, "--").stdout.splitlines() if p}
    untracked = {p.replace("\\", "/") for p in _git("ls-files", "--others", "--exclude-standard").stdout.splitlines() if p}
    assert tracked | untracked == PLAN_PATHS
    head = _git("rev-parse", "HEAD").stdout.strip()
    if head == BASE:
        assert untracked == PLAN_PATHS
    else:
        assert _git("rev-parse", "HEAD^").stdout.strip() == BASE
        assert _git("show", "-s", "--format=%s", "HEAD").stdout.strip() == COMMIT1_SUBJECT
        paths = {p.replace("\\", "/") for p in _git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").stdout.splitlines() if p}
        assert paths == PLAN_PATHS


def test_q1t_production_boundary_and_outcome_absences() -> None:
    for path in LATER_PATHS:
        assert not (ROOT / path).exists(), path
    assert not (ROOT / "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md").exists()
    assert _git("diff", "--cached", "--quiet", check=False).returncode == 0
    assert _git("diff", "--name-only", BASE, "--", ".gitattributes", ".github", "pyproject.toml", "setup.cfg", "setup.py", "src", "tests/production").stdout.splitlines() == []
    for path in PLAN_PATHS:
        raw = _raw(path)
        assert raw.endswith(b"\n") and b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf")
