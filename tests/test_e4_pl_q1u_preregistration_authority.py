from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "docs" / "reference_cases"
BASE = "850733cc9d2f9185d0a73c5fa6c0acd89067caba"
BASE_TREE = "3d5db4e5cc321d5b91351280fe0b0ecd279814ac"
PLAN_SUBJECT = "docs: preregister E4 PL Q1U execution-guard completion"
PLAN_REVIEW = REF / "e4_pl_q1u_plan_review.json"
PLAN_REVIEW_VERDICT = "ACCEPT_Q1U_PREREGISTRATION_NO_P0_P1"


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant: {value}")


def _reject_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw and raw.endswith(b"\n")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_pairs,
        parse_constant=_reject_constant,
    )
    assert isinstance(value, dict)
    canonical = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    assert raw == canonical
    return value


def _git(*args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        text=text,
    )
    return result.stdout.strip() if text else result.stdout


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _plan_paths() -> list[str]:
    extent = _load(REF / "e4_pl_q1u_allowed_extent.json")
    return list(extent["path_sets"]["PLAN12"])


def test_q1u_baseline_and_82_row_inheritance_are_exact() -> None:
    baseline = _load(REF / "e4_pl_q1u_baseline.json")
    inheritance = _load(REF / "e4_pl_q1u_inheritance_manifest.json")
    assert baseline["mandatory_base"] == {
        "commit": BASE,
        "parent": "083044167f9826e9868851c2709017112bc7553d",
        "subject": "docs: close E4 PL Q1T contract-authority block",
        "tree": BASE_TREE,
    }
    assert baseline["attachment"]["bytes"] == 28573
    assert baseline["attachment"]["sha256"] == "D33A7F9F6510C8B1166FA37AA7930BF1783071600B9001E446F2883068C834FF"
    assert baseline["q1t_preflight"]["node_count"] == 1
    assert baseline["q1t_preflight"]["execution_worktree_label"] == ".perf2-worktrees/e4-pl-q1t-exact-oracle-completion"

    assert inheritance["counts"] == {
        "q1t_closeout_inputs": 8,
        "q1t_commit1_inputs": 14,
        "q1t_commit2_inputs": 11,
        "q1t_inherited_inputs": 49,
        "total_directly_bound_inputs": 82,
    }
    rows = inheritance["inputs"]
    assert isinstance(rows, list) and len(rows) == 82
    required = {"path", "bytes", "sha256", "git_blob", "source_commit", "source_tree", "classification"}
    for row in rows:
        assert set(row) == required
        assert _git("rev-parse", f"{row['source_commit']}^{{tree}}") == row["source_tree"]
        assert _git("rev-parse", f"{row['source_commit']}:{row['path']}") == row["git_blob"]
        raw = _git("show", f"{row['source_commit']}:{row['path']}", text=False)
        assert isinstance(raw, bytes)
        assert len(raw) == row["bytes"]
        assert _sha(raw) == row["sha256"]


def test_q1u_stage_extents_and_blocked_routes_are_exact() -> None:
    extent = _load(REF / "e4_pl_q1u_allowed_extent.json")
    authority = _load(REF / "e4_pl_q1u_authority_contract.json")
    assert extent["path_count"] == 40
    assert extent["stage_counts"] == {
        "BLOCKED5": 5,
        "CONTRACT3": 3,
        "IMPLEMENTATION14": 14,
        "OUTCOME11": 11,
        "PLAN12": 12,
    }
    all_paths = set()
    for name in ("PLAN12", "IMPLEMENTATION14", "CONTRACT3", "OUTCOME11"):
        rows = extent["path_sets"][name]
        assert len(rows) == extent["stage_counts"][name]
        assert len(rows) == len(set(rows))
        assert not (all_paths & set(rows))
        all_paths.update(rows)
    assert len(all_paths) == 40
    assert set(extent["path_sets"]["BLOCKED5"]).issubset(extent["path_sets"]["OUTCOME11"])
    route_counts = {row["stage"]: row["path_count"] for row in authority["blocked_routes"]}
    assert route_counts == {
        "PLAN_OR_INHERITANCE": 17,
        "IMPLEMENTATION": 19,
        "CONTRACT": 8,
        "POST_AUTHORITY": 6,
    }

    present = {path for path in all_paths if (ROOT / path).exists()}
    review_rel = "docs/reference_cases/e4_pl_q1u_plan_review.json"
    expected = set(extent["path_sets"]["PLAN12"])
    if not PLAN_REVIEW.exists():
        expected.remove(review_rel)
    assert present == expected
    assert not (ROOT / "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md").exists()


def test_q1u_vocabulary_review_schema_and_terminal_authority_are_exact() -> None:
    vocabulary = _load(REF / "e4_pl_q1u_contract_vocabulary.json")
    review_schema = _load(REF / "e4_pl_q1u_review_schema.json")
    terminal = _load(REF / "e4_pl_q1u_terminal_table.json")
    assert vocabulary["environment"]["canonical_record_field"] == "environment.record_path"
    assert vocabulary["agreement"]["canonical_mode"] == "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD"
    assert vocabulary["environment"]["forbidden_aliases"] == ["environment.path"]
    assert vocabulary["agreement"]["forbidden_aliases"] == ["BYTE_IDENTICAL_CANONICAL_COMMON_PAYLOAD"]
    assert review_schema["accepted_review_requirements"]["top_level_keys"] == [
        "findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"
    ]
    assert len(terminal["terminals"]) == 11
    assert [row["precedence"] for row in terminal["terminals"]] == list(range(1, 12))
    assert terminal["terminals"][3]["id"] == "BLOCKED_E4_PL_Q1U_EXACT_ORACLE_IDENTITY"
    assert terminal["terminals"][-1]["id"] == "PROVISIONAL_GO_E4_PL_Q1U_Q1B_PLAN"

    review = _load(PLAN_REVIEW)
    assert set(review) == {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
    assert review["findings"] == []
    assert review["verdict"] == PLAN_REVIEW_VERDICT
    assert review["reviewer_independence"] == {
        "authored_review_only": True,
        "mechanics_executed": False,
        "reviewed_input_authorship": False,
        "role": "INDEPENDENT_PLAN_ONLY_REVIEWER",
    }
    expected = []
    for rel in _plan_paths():
        if rel == "docs/reference_cases/e4_pl_q1u_plan_review.json":
            continue
        raw = (ROOT / rel).read_bytes()
        expected.append({"bytes": len(raw), "path": rel, "sha256": _sha(raw)})
    assert review["reviewed_inputs"] == sorted(expected, key=lambda row: row["path"])


def test_q1u_production_boundary_and_later_stage_absences() -> None:
    baseline = _load(REF / "e4_pl_q1u_baseline.json")
    extent = _load(REF / "e4_pl_q1u_allowed_extent.json")
    assert baseline["production"]["production_terminal"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert baseline["production"]["legacy_default"] == "ShellElement"
    for key, value in baseline["production"].items():
        if key in {"production_terminal", "legacy_default", "q1b_execution"}:
            continue
        assert value is False
    for stage in ("IMPLEMENTATION14", "CONTRACT3", "OUTCOME11"):
        assert all(not (ROOT / rel).exists() for rel in extent["path_sets"][stage])
    assert _git("diff", "--name-only", BASE, "--", "src", ".github", "pyproject.toml", ".gitattributes") == ""

    head = _git("rev-parse", "HEAD")
    if head != BASE:
        assert _git("show", "-s", "--format=%s", "HEAD") == PLAN_SUBJECT
        assert _git("rev-parse", "HEAD^") == BASE
        changed = _git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        assert sorted(changed) == sorted(_plan_paths())
