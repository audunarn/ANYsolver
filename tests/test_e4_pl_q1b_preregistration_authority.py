"""Nonmechanical Q1B preregistration authority checks."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "docs" / "reference_cases"
PLAN = ROOT / "docs" / "agent_plans" / "S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md"
BASELINE = REF / "e4_pl_q1b_baseline.json"
CONTRACT = REF / "e4_pl_q1b_plan_contract.json"
INVENTORY = REF / "e4_pl_q1b_test_inventory.json"
REVIEW = REF / "e4_pl_q1b_plan_review.json"
THIS_TEST = ROOT / "tests" / "test_e4_pl_q1b_preregistration_authority.py"

PLAN6 = {
    "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md",
    "docs/reference_cases/e4_pl_q1b_baseline.json",
    "docs/reference_cases/e4_pl_q1b_plan_contract.json",
    "docs/reference_cases/e4_pl_q1b_plan_review.json",
    "docs/reference_cases/e4_pl_q1b_test_inventory.json",
    "tests/test_e4_pl_q1b_preregistration_authority.py",
}
ACCEPTED_PLAN_COMMIT = "9cba0a191eb5f82ca4f9959ffc4f92df69b98d42"


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    assert raw.endswith(b"\n") and b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf")
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    assert isinstance(value, dict)
    canonical = (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    assert raw == canonical, path
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def test_q1b_base_and_inherited_authority_are_exact() -> None:
    baseline = _load(BASELINE)
    assert baseline["base"] == {
        "commit": "be64f1d7f284bfa044e8dd4b40bece29e7311f44",
        "parent_commits": ["31cea60897889310e6b62dc479c7a86bd506b4b4", "f39cbcdd39c164b26fd636b73df9d1a7dad6cc89"],
        "subject": "Merge pull request #13 from audunarn/codex/s4-e4-pl-q1aa-local-qualification-synthesis",
        "tree": "b412998399c3fa0bc5d40bd4658dbea77ab945ab",
    }
    # Bind the accepted PLAN6 commit itself, then permit normal merge commits
    # and later preregistered descendants without coupling this historical test
    # to whatever commit happens to be current HEAD.
    assert _git("rev-parse", f"{ACCEPTED_PLAN_COMMIT}^") == baseline["base"]["commit"]
    assert _git("show", "-s", "--format=%s", ACCEPTED_PLAN_COMMIT) == "docs: preregister E4 PL Q1B nonintrusion stability locking"
    committed_paths = set(_git("diff-tree", "--no-commit-id", "--name-only", "-r", ACCEPTED_PLAN_COMMIT).splitlines())
    assert committed_paths == PLAN6
    _git("merge-base", "--is-ancestor", ACCEPTED_PLAN_COMMIT, "HEAD")
    assert len(baseline["authority_rows"]) == 12
    assert len({row["path"] for row in baseline["authority_rows"]}) == 12
    for row in baseline["authority_rows"]:
        path = ROOT / row["path"]
        assert path.stat().st_size == row["bytes"]
        assert _sha(path) == row["sha256"]
        assert _git("rev-parse", f"HEAD:{row['path']}") == row["git_blob"]
    q1aa = _load(REF / "e4_pl_q1aa_status.json")
    assert q1aa["terminal"] == "PROVISIONAL_GO_E4_PL_Q1AA_Q1B_PLAN"
    assert q1aa["q1b_plan_preparation"] == "AUTHORIZED_SEPARATE_REVIEWED_PLAN_ONLY"
    assert q1aa["q1b_execution"] == "UNAUTHORIZED"


def test_q1b_stage_extents_cases_thresholds_and_terminals_are_frozen() -> None:
    contract = _load(CONTRACT)
    stages = contract["stage_paths"]
    assert set(stages) == {"PLAN6", "IMPLEMENTATION11", "CONTRACT3", "OUTCOME11"}
    assert {key: len(value) for key, value in stages.items()} == {
        "PLAN6": 6,
        "IMPLEMENTATION11": 11,
        "CONTRACT3": 3,
        "OUTCOME11": 11,
    }
    assert set(stages["PLAN6"]) == PLAN6
    all_paths = [path for rows in stages.values() for path in rows]
    assert len(all_paths) == len(set(all_paths)) == 31
    assert contract["geometry_families"] == [
        "AFFINE_SQUARE", "AFFINE_PARALLELOGRAM", "NONAFFINE_TRAPEZOID",
        "TAPERED_SKEW", "HOSTILE_ASYMMETRIC_1", "HOSTILE_ASYMMETRIC_2",
    ]
    assert contract["mesh_families"] == {
        "locking_elements_along_span": [4, 8, 16, 32],
        "locking_thickness_to_length": ["1e-2", "1e-3", "1e-4", "1e-5", "1e-6"],
        "stability_and_patch_refinements": [1, 2, 4, 8],
    }
    assert [row["precedence"] for row in contract["terminals"]] == list(range(1, 8))
    assert [row["id"] for row in contract["terminals"]] == [
        "BLOCKED_E4_PL_Q1B_AUTHORITY_OR_REVIEW",
        "BLOCKED_E4_PL_Q1B_IMPLEMENTATION_CONTRACT_OR_NONDETERMINISM",
        "NO_GO_E4_PL_Q1B_ASSEMBLED_STABILITY_OR_COERCIVITY",
        "NO_GO_E4_PL_Q1B_LOCKING_OR_CATEGORY_DRIFT",
        "NO_GO_E4_PL_Q1B_NONINTRUSION_OR_RECOVERY_SEPARATION",
        "UNCLASSIFIED_E4_PL_Q1B_BOUNDED_ASSEMBLED_EVIDENCE",
        "PROVISIONAL_GO_E4_PL_Q1B_LINEAR_STATIC_INTEGRATION_PLAN",
    ]
    assert contract["thresholds"]["locking_analytical_displacement_relative_error_max"] == "2e-2"
    assert contract["thresholds"]["locking_response_ratio_spread_max"] == "5e-3"
    assert contract["thresholds"]["finest_pl_hourglass_energy_fraction_max"] == "1e-2"
    domain = contract["admissible_geometry_domain"]
    assert domain["domain_id"] == "G1_PLANAR_BILINEAR_SHAPE_REGULAR"
    assert domain["jacobian_bounds"] == {
        "centre_relative_variation_max": "1/2",
        "determinant": "STRICTLY_POSITIVE_EVERYWHERE",
        "singular_value_ratio_min": "1/4",
    }
    assert set(domain["samples"]) == set(contract["geometry_families"])
    assert domain["coverage_obligation"].startswith("DOMAIN_WIDE_CERTIFICATE_REQUIRED")
    coercivity = contract["coercivity"]
    assert coercivity["uniform_lower_bound"] == {
        "alpha_star_min": "1e-6",
        "requirement": "ONE_OUTCOME_INDEPENDENT_ALPHA_STAR_AND_EVERY_REGISTERED_ALPHA_H_GE_ALPHA_STAR",
    }
    assert "R_C_TRANSPOSE_W_C_R_C" in coercivity["component_rigid_projection"]
    assert coercivity["domain_certificate"].startswith("INTERVAL_BRANCH_CERTIFICATE_OVER_COMPLETE_G1_DOMAIN")
    benchmarks = contract["benchmark_definitions"]
    assert benchmarks["locking_strip"]["dimensions"] == {"length": "1", "width": "1/10"}
    assert benchmarks["locking_strip"]["material"] == {"E": "15", "nu": "1/4"}
    assert benchmarks["monotonicity"]["rule"] == "NEXT_LE_PREVIOUS_PLUS_1E_MINUS12_TIMES_MAX_1_PREVIOUS"
    assert benchmarks["nonaffine_convergence"]["load"] == "PHYSICAL_SURFACE_LOAD_P_X_Y_EQUALS_1_PLUS_X_PLUS_2_Y"
    reaction = contract["reaction_semantics"]
    assert reaction["total_reaction"] == "R_TOTAL_EQUALS_R_PHYS_PLUS_R_PL_PLUS_R_HG"
    assert "MAY_BE_NONZERO" in reaction["internal_numerical_reactions"]
    assert "QD_TRANSPOSE_REACTION_EXACT_ZERO" in reaction["support_multiplier_reaction"]


def test_q1b_plan_scope_runtime_and_production_boundary() -> None:
    baseline = _load(BASELINE)
    contract = _load(CONTRACT)
    inventory = _load(INVENTORY)
    assert baseline["scope"] == {
        "eigenvalue_buckling": False,
        "mechanics_execution": False,
        "production_changes": False,
        "research_only": True,
        "src_changes": False,
    }
    runtime = contract["future_campaign"]["runtime"]
    assert runtime == {
        "automatic_retry": False,
        "memory_limit_gib_per_process": 24,
        "numerical_threads_per_process": 1,
        "timeout_seconds_per_process": 600,
        "worker_count": 3,
    }
    assert contract["future_campaign"]["cycles"] == 2
    assert contract["future_campaign"]["execution_requires_separate_user_request"] is True
    assert contract["correction_policy"]["plan_corrections_used"] == 1
    assert contract["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert contract["q1b_execution"] == "UNAUTHORIZED_BY_PLAN_ONLY_STAGE"
    assert inventory["mechanics_allowed_in_preregistration"] is False
    forbidden_roots = ("src/", ".github/", "pyproject.toml")
    assert not any(path.startswith(forbidden_roots) for path in PLAN6)
    observed_paths = [line[3:].replace("\\", "/") for line in _git("status", "--porcelain").splitlines() if len(line) >= 4]
    assert not any("Q1B" in path and path not in PLAN6 for path in observed_paths)
    assert PLAN.read_text(encoding="utf-8").count("Eigenvalue buckling") == 1
    plan_text = PLAN.read_text(encoding="utf-8")
    for required in (
        "G1_PLANAR_BILINEAR_SHAPE_REGULAR",
        "alpha_h=min",
        "w_EB=F L^3/(3 E I)",
        "r_total=r_phys+r_PL+r_hg",
        "Numerical reactions are not required to vanish",
    ):
        assert required in plan_text


def test_q1b_independent_plan_review_binds_other_five_inputs() -> None:
    review = _load(REVIEW)
    assert set(review) == {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
    assert review["schema"] == "anysolver.s4.e4-pl-q1b-plan-review-v1"
    assert review["verdict"] == "ACCEPT_Q1B_PREREGISTRATION_NO_P0_P1"
    assert review["findings"] == []
    assert review["reviewer_independence"] == {
        "mechanics_executed": False,
        "reviewer_role": "INDEPENDENT_Q1B_PLAN_REVIEWER",
        "same_agent_as_packet_author": False,
    }
    expected_paths = sorted(str(path.relative_to(ROOT)).replace("\\", "/") for path in (PLAN, BASELINE, CONTRACT, INVENTORY, THIS_TEST))
    assert [row["path"] for row in review["reviewed_inputs"]] == expected_paths
    for row in review["reviewed_inputs"]:
        path = ROOT / row["path"]
        assert set(row) == {"bytes", "path", "sha256"}
        assert path.stat().st_size == row["bytes"]
        assert _sha(path) == row["sha256"]
