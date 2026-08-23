from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "reference_cases"
PLAN = ROOT / "docs" / "agent_plans" / "S4_E4_PL_Q1F_DOMAIN_COERCIVITY_PLAN.md"
BASE_COMMIT = "61195c18a704438b4b3cf66e6e93d7839723b0fb"
BASE_TREE = "1249c9e9280d626c11c7194c1f2f5b164e5d99b7"
Q1E_COMMIT = "e47bade554b23cbac3272d9453162a42e7e082ee"
Q1R_COMMIT = "97edc4265a7ce5ca9763f66875d1336e419bcef4"
Q1V_COMMIT = "c51f4705a1f0f547ec2265a7846894dba098307d"
Q1Y3_COMMIT = "90bfd9375eee7825c38b4b6f646e1a220f7ce453"
PLAN_SUBJECT = "docs: preregister E4 PL Q1F domain coercivity"


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _strict_json(raw: bytes, *, require_canonical: bool = True) -> object:
    if not raw.endswith(b"\n") or b"\r" in raw:
        raise ValueError("JSON transport must be UTF-8/LF with one final LF")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    if require_canonical and raw != _canonical(value):
        raise ValueError("JSON is not canonical")
    return value


def _load(path: Path) -> dict[str, object]:
    value = _strict_json(path.read_bytes())
    assert isinstance(value, dict)
    return value


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _git(*args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=not binary
    )
    return result.stdout if binary else result.stdout.strip()


def _git_bytes(commit: str, path: str) -> bytes:
    return _git("show", f"{commit}:{path}", binary=True)  # type: ignore[return-value]


def _ast_hashes(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            dump = ast.dump(node, include_attributes=False).encode("utf-8")
            result[node.name] = _sha(dump)
    return result


def test_q1f_strict_json_rejects_duplicates_nonfinite_and_noncanonical() -> None:
    assert _strict_json(b'{"a":1}\n') == {"a": 1}
    for raw in (
        b'{"a":1,"a":2}\n',
        b'{"a":NaN}\n',
        b'{"a":Infinity}\n',
        b'{"b":1,"a":2}\n',
        b'{"a":1}\r\n',
        b'{"a":1}',
    ):
        with pytest.raises((ValueError, UnicodeError)):
            _strict_json(raw)
    for name in (
        "e4_pl_q1f_allowed_extent.json",
        "e4_pl_q1f_baseline.json",
        "e4_pl_q1f_reduction_contract.json",
        "e4_pl_q1f_terminal_table.json",
        "e4_pl_q1f_test_inventory.json",
    ):
        _load(DOCS / name)


def test_q1f_baseline_binds_exact_q1e_q1r_q1v_and_q1y3_authority() -> None:
    baseline = _load(DOCS / "e4_pl_q1f_baseline.json")
    assert baseline["schema"] == "anysolver.s4.e4-pl-q1f-baseline-v1"
    assert baseline["branch"] == "codex/s4-e4-pl-q1f-domain-coercivity"
    assert baseline["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    base = baseline["base_authority"]
    assert isinstance(base, dict)
    assert base == {
        "commit": BASE_COMMIT,
        "parents": ["f8f5a5db684922f0e7d056541a0dd68cba36fe21", Q1E_COMMIT],
        "subject": "Merge pull request #19 from audunarn/codex/s4-e4-pl-q1e-assembled-readjudication",
        "tree": BASE_TREE,
    }
    assert _git("show", "-s", "--format=%T", BASE_COMMIT) == BASE_TREE
    assert _git("show", "-s", "--format=%P", BASE_COMMIT).split() == base["parents"]

    q1e = baseline["q1e_authority"]
    assert isinstance(q1e, dict) and len(q1e["paths"]) == 7
    assert q1e["status_terminal"] == "UNCLASSIFIED_E4_PL_Q1E_DOMAIN_COERCIVITY"
    assert q1e["q1f_plan_preparation"] == "AUTHORIZED_SEPARATE_REVIEWED_PLAN_ONLY"
    for row in q1e["paths"]:
        raw = _git_bytes(Q1E_COMMIT, row["path"])
        assert (len(raw), _sha(raw), _git("rev-parse", f"{Q1E_COMMIT}:{row['path']}")) == (
            row["bytes"], row["sha256"], row["git_blob"]
        )

    material = baseline["q1r_material_authority"]
    assert isinstance(material, dict)
    raw = _git_bytes(Q1R_COMMIT, material["path"])
    assert (len(raw), _sha(raw), _git("rev-parse", f"{Q1R_COMMIT}:{material['path']}")) == (
        material["bytes"], material["sha256"], material["git_blob"]
    )

    mechanics = baseline["mechanics_authority"]
    assert isinstance(mechanics, dict)
    q1v = mechanics["q1v_reference"]
    assert q1v["source_commit"] == Q1V_COMMIT
    raw = _git_bytes(Q1V_COMMIT, q1v["path"])
    assert (len(raw), _sha(raw), _git("rev-parse", f"{Q1V_COMMIT}:{q1v['path']}")) == (
        q1v["bytes"], q1v["sha256"], q1v["git_blob"]
    )
    q1y3 = mechanics["q1y3"]
    assert q1y3["closeout_commit"] == Q1Y3_COMMIT
    assert q1y3["accepted_terminal"] == "UNCLASSIFIED_E4_PL_Q1Y3_LOCAL_ALGEBRA_CLOSED_ONLY"
    for row in q1y3["paths"]:
        raw = _git_bytes(Q1Y3_COMMIT, row["path"])
        assert (len(raw), _sha(raw), _git("rev-parse", f"{Q1Y3_COMMIT}:{row['path']}")) == (
            row["bytes"], row["sha256"], row["git_blob"]
        )
    contract = json.loads(_git_bytes(Q1Y3_COMMIT, "docs/reference_cases/e4_pl_q1y3_local_algebra_contract.json"))
    result = json.loads(_git_bytes(Q1Y3_COMMIT, "docs/reference_cases/e4_pl_q1y3_bounded_result.json"))
    assert contract["checker"]["tying_policy"] == q1y3["tying_policy"]
    assert result["contract_sha256"] == "51CEE85123128C9ACA2BF99842416485C6A38604B8C24DC92912503E62FBD964"
    assert result["terminal"] == q1y3["accepted_terminal"]
    assert baseline["plan_correction"] == {
        "corrections_allowed": 1,
        "corrections_used": 1,
        "mechanics_executed": False,
        "reason": "CLOSE_SIX_INDEPENDENT_REVIEW_P1_FINDINGS_BEFORE_PLAN_REVIEW",
    }


def test_q1f_mechanics_gauge_norm_refinement_and_interval_reduction_are_frozen() -> None:
    contract = _load(DOCS / "e4_pl_q1f_reduction_contract.json")
    baseline = _load(DOCS / "e4_pl_q1f_baseline.json")
    assert contract["schema"] == "anysolver.s4.e4-pl-q1f-reduction-contract-v2"
    assert contract["candidate_id"] == baseline["candidate_id"]

    inventory = contract["mechanics_inventory"]
    assert inventory["dofs"] == {
        "node_major_order": ["u", "v", "w", "theta_r", "theta_s", "theta_n"],
        "node_natural_coordinates": [[-1, -1], [1, -1], [1, 1], [-1, 1]],
        "physical_count": 24,
    }
    expected_ast = inventory["symbol_ast_sha256"]
    for source, key in (
        (ROOT / "docs/reference_cases/e4_pl_q1v_reference.py", "q1v_reference"),
        (ROOT / "docs/reference_cases/e4_pl_q1y3_algebra_checker.py", "q1y3_checker"),
    ):
        observed = _ast_hashes(source)
        assert set(expected_ast[key]) <= set(observed)
        assert {name: observed[name] for name in expected_ast[key]} == expected_ast[key]
    assert inventory["source_fields"]["dimensions"] == {"N_epsilon": "8x21", "N_sigma": "8x14"}
    assert inventory["stationary_and_condensation"]["dimensions"] == {
        "core": 35, "external": 24, "pl": 3, "stationary": 38
    }
    assert "K=K_core+K_PL+K_hourglass" in inventory["stationary_and_condensation"]["schur"]

    domain = contract["domain"]
    assert domain["coordinates"]["parameters"] == {
        "p": ["-4", "4"], "q": ["1/4", "4"], "u": ["-2", "2"], "v": ["-2", "2"]
    }
    assert domain["uniqueness"]["no_reflection"] is True
    assert domain["uniqueness"]["orientation_selector"] == "q>0"
    p, q, u, v = map(Fraction, ("2/3", "3/2", "-1/4", "5/7"))
    nodes = [(-1-p+u, -q+v), (1-p-u, -q-v), (1+p+u, q+v), (-1+p-u, q-v)]
    a0 = tuple(sum(node[j] for node in nodes) / 4 for j in range(2))
    a1 = tuple((-nodes[0][j]+nodes[1][j]+nodes[2][j]-nodes[3][j]) / 4 for j in range(2))
    a2 = tuple((-nodes[0][j]-nodes[1][j]+nodes[2][j]+nodes[3][j]) / 4 for j in range(2))
    a3 = tuple((nodes[0][j]-nodes[1][j]+nodes[2][j]-nodes[3][j]) / 4 for j in range(2))
    assert a0 == (0, 0) and a1 == (1, 0) and a2 == (p, q) and a3 == (u, v)

    refinement = contract["refinement_theorem"]
    assert refinement["child_map"] == {"r": "r0+rho/2", "s": "s0+sigma/2"}
    assert refinement["child_parameters"] == {
        "p_prime": "dot(A,B)/dot(A,A)",
        "q_prime": "det(A,B)/dot(A,A)",
        "u_prime": "dot(A,C)/(2*dot(A,A))",
        "v_prime": "det(A,C)/(2*dot(A,A))",
    }
    assert len(refinement["proof_obligations"]) == 6

    reduction = contract["local_reduction"]
    assert reduction["alpha_star"] == "1/1000000"
    assert set(reduction["exact_obligations"]) >= {
        "K_e*R_e=0", "H_e*R_e=0", "rank(R_e)=6", "rank(H_e)=18",
        "kernel(H_e)=range(R_e)", "Z_e^T*H_e*Z_e_IS_POSITIVE_DEFINITE",
        "Z_e^T*(K_e-1/1000000*H_e)*Z_e_IS_POSITIVE_SEMIDEFINITE",
        "kernel(K_e)=range(R_e)",
    }
    assert reduction["norm_matrix"]["assembly"].startswith("H=SUM_GP_detJ*")
    assert len(reduction["rigid_matrix"]["columns"]) == 6
    scale = contract["gauge_congruence"]["coefficientwise_scale_certificate"]
    assert scale["k_minus_alpha_h"].startswith("DELTA_pullback(ell)=DELTA_bending+ell^2")
    assert "FALSE_BLANKET_SCALE_INVARIANCE" in contract["gauge_congruence"]["statement"]

    campaign = contract["interval_campaign"]
    assert campaign["partition_dag"]["tie_order"] == ["p", "q", "u", "v"]
    assert [row["bounds"]["p"] for row in campaign["partition_dag"]["root_boxes"]] == [
        {"lower": [-4, 1], "upper": [-4, 3]},
        {"lower": [-4, 3], "upper": [4, 3]},
        {"lower": [4, 3], "upper": [4, 1]},
    ]
    assert all(
        set(row) == {"bounds", "box_id", "depth", "parent_id", "split"}
        and row["depth"] == 0
        and row["parent_id"] is None
        and row["split"] is None
        for row in campaign["partition_dag"]["root_boxes"]
    )
    assert campaign["checker_replicas"]["count"] == 2
    assert "MIXED_SUPERSET_MECHANICS_CERTIFIED" in campaign["leaf_rules"]["POSITIVE"]
    grammar = contract["certificate_grammar"]
    assert grammar["endpoint"]["form"] == ["INTEGER_NUMERATOR", "POSITIVE_INTEGER_DENOMINATOR"]
    assert grammar["split_schema"]["top_level_keys"] == ["coordinate", "left_child_id", "right_child_id", "value"]
    assert grammar["leaf_schema"]["class_values"] == ["EXCLUDED", "NEGATIVE", "POSITIVE", "UNRESOLVED"]
    assert set(grammar["leaf_schema"]["domain_certificate_values"]) == {
        "ALL_ADMISSIBLE", "MIXED_SUPERSET_MECHANICS_CERTIFIED", "NO_ADMISSIBLE_POINT", "UNRESOLVED"
    }


def _status_paths() -> tuple[list[str], bool]:
    raw = _git("status", "--porcelain=v1", "--untracked-files=all")
    lines = [] if not raw else raw.splitlines()
    paths = sorted(line[3:].replace("\\", "/") for line in lines)
    return paths, all(line.startswith("?? ") for line in lines)


def test_q1f_stage_extents_routes_terminals_and_closed_world_are_exact() -> None:
    extent = _load(DOCS / "e4_pl_q1f_allowed_extent.json")
    terminals = _load(DOCS / "e4_pl_q1f_terminal_table.json")
    inventory = _load(DOCS / "e4_pl_q1f_test_inventory.json")
    stages = extent["stage_paths"]
    assert {name: len(paths) for name, paths in stages.items()} == {
        "CONTRACT3": 3, "IMPLEMENTATION10": 10, "OUTCOME8": 8, "PLAN8": 8
    }
    assert extent["stage_subjects"] == {
        "CONTRACT3": "docs: authorize E4 PL Q1F bounded domain proof",
        "IMPLEMENTATION10": "docs: freeze E4 PL Q1F coercivity proof tooling",
        "OUTCOME8": "docs: close E4 PL Q1F domain coercivity",
        "PLAN8": PLAN_SUBJECT,
    }
    blocked5 = {
        "docs/reference_cases/e4_pl_q1f_status.json",
        "docs/reference_cases/e4_pl_q1f_scientific_review.json",
        "docs/E4_PL_Q1F_DOMAIN_COERCIVITY.md",
        "docs/E4_PL_Q1F_COMPLETION.md",
        "tests/test_e4_pl_q1f_closeout.py",
    }
    for route, stage in (("PLAN_BLOCK", "PLAN8"), ("IMPLEMENTATION_BLOCK", "IMPLEMENTATION10"), ("CONTRACT_BLOCK", "CONTRACT3")):
        record = extent["blocked_routes"][route]
        assert set(record["paths"]) == set(stages[stage]) | blocked5
        assert record["path_count"] == len(record["paths"])
    assert set(extent["blocked_routes"]["POST_AUTHORITY_BLOCK"]["paths"]) == blocked5 | {
        "docs/reference_cases/e4_pl_q1f_execution_authority.json"
    }
    assert [row["id"] for row in terminals["terminals"]] == [
        "BLOCKED_E4_PL_Q1F_AUTHORITY_OR_REVIEW",
        "BLOCKED_E4_PL_Q1F_REDUCTION_IDENTITY",
        "BLOCKED_E4_PL_Q1F_PROOF_OR_NONDETERMINISM",
        "NO_GO_E4_PL_Q1F_DOMAIN_COERCIVITY",
        "UNCLASSIFIED_E4_PL_Q1F_INTERVAL_COVERAGE",
        "PROVISIONAL_GO_E4_PL_Q1F_Q1B_INTEGRATION_PLAN",
    ]
    assert [row["precedence"] for row in terminals["terminals"]] == list(range(1, 7))
    assert inventory["inventory_separation"].startswith("COUNTS_AND_RESULTS_MUST_REMAIN_STAGE_SEPARATE")
    assert all(group["mechanics_executed"] is False for group in inventory["inventories"].values())

    assert _git("branch", "--show-current") == "codex/s4-e4-pl-q1f-domain-coercivity"
    assert _git("diff", "--cached", "--name-only") == ""
    head = _git("rev-parse", "HEAD")
    profiles = extent["plan_authoring_profiles"]
    if head == BASE_COMMIT:
        paths, only_untracked = _status_paths()
        allowed = [profiles["PRE_REVIEW"]["paths"], profiles["REVIEWED_UNCOMMITTED"]["paths"]]
        assert paths in [sorted(value) for value in allowed]
        assert only_untracked
    else:
        assert _git("show", "-s", "--format=%P", head) == BASE_COMMIT
        assert _git("show", "-s", "--format=%s", head) == PLAN_SUBJECT
        assert sorted(_git("diff-tree", "--no-commit-id", "--name-only", "-r", head).splitlines()) == sorted(stages["PLAN8"])
        assert _git("status", "--porcelain=v1", "--untracked-files=all") == ""
    changed = set(stages["PLAN8"])
    assert not any(path == ".gitattributes" or path == "pyproject.toml" or path.startswith("src/") or path.startswith(".github/") for path in changed)
    for future in set(stages["IMPLEMENTATION10"] + stages["CONTRACT3"] + stages["OUTCOME8"]):
        assert not (ROOT / future).exists()
    assert "legacy `ShellElement` remains the default" in PLAN.read_text(encoding="utf-8")


def test_q1f_independent_plan_review_binds_other_seven_inputs() -> None:
    review_path = DOCS / "e4_pl_q1f_plan_review.json"
    assert review_path.exists(), "independent plan review has not yet been authored"
    review = _load(review_path)
    assert set(review) == {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
    assert review["schema"] == "anysolver.s4.e4-pl-q1f-plan-review-v1"
    assert review["verdict"] == "ACCEPT_Q1F_COERCIVITY_REDUCTION_NO_P0_P1"
    assert review["findings"] == []
    assert review["reviewer_independence"] == {
        "mechanics_executed": False,
        "reviewer_role": "INDEPENDENT_Q1F_REDUCTION_REVIEWER",
        "same_agent_as_packet_author": False,
    }
    extent = _load(DOCS / "e4_pl_q1f_allowed_extent.json")
    relative_review = review_path.relative_to(ROOT).as_posix()
    expected = []
    for path in sorted(set(extent["stage_paths"]["PLAN8"]) - {relative_review}):
        raw = (ROOT / path).read_bytes()
        expected.append({"bytes": len(raw), "path": path, "sha256": _sha(raw)})
    assert review["reviewed_inputs"] == expected
