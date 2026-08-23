#!/usr/bin/env python3
"""Re-adjudicate frozen Q1B/Q1C/Q1D evidence without running mechanics."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Sequence


BASE_COMMIT = "f8f5a5db684922f0e7d056541a0dd68cba36fe21"
STUDY_ID = "study_e4_pl_q1e.q1b_q1c_q1d_assembled_evidence_readjudication_v1"
CANDIDATE_ID = "candidate_e4_pl_q1e.wg2020_assembled_evidence_readjudication_v1"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1e-synthesis-contract-v1"
EVIDENCE_SCHEMA = "anysolver.s4.e4-pl-q1e-synthesis-evidence-v1"
REVIEW_SCHEMA = "anysolver.s4.e4-pl-q1e-scientific-review-v1"
STATUS_SCHEMA = "anysolver.s4.e4-pl-q1e-status-v1"
REVIEW_VERDICT = "ACCEPT_Q1E_ASSEMBLED_READJUDICATION_NO_P0_P1"
PRODUCTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
TERMINALS = [
    "BLOCKED_E4_PL_Q1E_EVIDENCE_OR_REVIEW",
    "NO_GO_E4_PL_Q1E_LOCKING",
    "NO_GO_E4_PL_Q1E_SOLVER_EQUIVALENCE",
    "NO_GO_E4_PL_Q1E_STABILITY_OR_NONINTRUSION",
    "UNCLASSIFIED_E4_PL_Q1E_DOMAIN_COERCIVITY",
    "PROVISIONAL_GO_E4_PL_Q1E_ASSEMBLED_QUALIFICATION",
]
EXTENT = [
    "docs/agent_plans/S4_E4_PL_Q1E_ASSEMBLED_READJUDICATION_PLAN.md",
    "docs/reference_cases/e4_pl_q1e_scientific_review.json",
    "docs/reference_cases/e4_pl_q1e_status.json",
    "docs/reference_cases/e4_pl_q1e_synthesis_contract.json",
    "docs/reference_cases/e4_pl_q1e_synthesis_evidence.json",
    "docs/reference_cases/e4_pl_q1e_synthesizer.py",
    "tests/test_e4_pl_q1e_assembled_readjudication.py",
]
AUTHOR_EXTENT = [
    path
    for path in EXTENT
    if path
    not in {
        "docs/reference_cases/e4_pl_q1e_scientific_review.json",
        "docs/reference_cases/e4_pl_q1e_status.json",
    }
]
BASE_NONSTAGE_INDEX = {
    "path_count": 751,
    "sha256": "828A1391C33EFCF55F68F308634DB0E68C1829BE774C95194DB071F10EFCE5D9",
}
FORBIDDEN_PRODUCTION_PATHS = [".gitattributes", ".github", "pyproject.toml", "src"]


class SynthesisError(RuntimeError):
    """Fail-closed Q1E authority, evidence, or review error."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SynthesisError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(SynthesisError(f"nonfinite JSON: {token}")),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SynthesisError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise SynthesisError(f"noncanonical JSON: {path}")
    return raw, value


def _keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise SynthesisError(f"{label} exact-key mismatch")
    return value


def _expect(condition: bool, label: str) -> None:
    if not condition:
        raise SynthesisError(label)


def _git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and result.returncode:
        raise SynthesisError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def tracked_index_records(root: Path) -> list[bytes]:
    result = subprocess.run(
        ["git", "ls-files", "-s", "-z"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    _expect(result.returncode == 0, "cannot read tracked Git index")
    records = [record for record in result.stdout.split(b"\0") if record]
    for record in records:
        _expect(b"\t" in record, "malformed Git index record")
        header, path = record.split(b"\t", 1)
        fields = header.split(b" ")
        _expect(len(fields) == 3 and fields[2] == b"0" and path, "non-stage-zero Git index record")
    return records


def index_graph_for_records(records: list[bytes], excluded_paths: set[str] | None = None) -> dict[str, Any]:
    excluded = excluded_paths or set()
    retained: list[bytes] = []
    for record in records:
        path = record.split(b"\t", 1)[1].decode("utf-8")
        if path not in excluded:
            retained.append(record)
    payload = b"\n".join(sorted(retained)) + b"\n"
    return {"path_count": len(retained), "sha256": sha256(payload)}


def tracked_index_graph(root: Path, excluded_paths: set[str] | None = None) -> dict[str, Any]:
    return index_graph_for_records(tracked_index_records(root), excluded_paths)


def shallow_fallback_allowed(*, github_actions: bool, head: str, shallow_heads: set[str], graph_matches: bool) -> bool:
    return github_actions and graph_matches and head in shallow_heads


def closed_world_extent_allowed(*, untracked_paths: set[str], tracked_q1e_paths: set[str], dirty_tracked: bool) -> bool:
    if dirty_tracked:
        return False
    if not untracked_paths:
        return tracked_q1e_paths == set(EXTENT)
    return not tracked_q1e_paths and untracked_paths in (set(AUTHOR_EXTENT), set(EXTENT))


def _validate_closed_world_status(root: Path) -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    _expect(result.returncode == 0, "cannot read Git status")
    entries = [entry for entry in result.stdout.split(b"\0") if entry]
    untracked: set[str] = set()
    dirty_tracked = False
    for entry in entries:
        if entry.startswith(b"?? "):
            untracked.add(entry[3:].decode("utf-8"))
        else:
            dirty_tracked = True
    tracked_q1e = {
        record.split(b"\t", 1)[1].decode("utf-8")
        for record in tracked_index_records(root)
        if record.split(b"\t", 1)[1].decode("utf-8") in set(EXTENT)
    }
    _expect(
        closed_world_extent_allowed(
            untracked_paths=untracked,
            tracked_q1e_paths=tracked_q1e,
            dirty_tracked=dirty_tracked,
        ),
        "repository change set is not an exact Q1E stage",
    )


def validate_repository_boundary(root: Path) -> None:
    repository = root.resolve(strict=True)
    top = Path(_git(repository, "rev-parse", "--show-toplevel")).resolve(strict=True)
    _expect(os.path.normcase(str(top)) == os.path.normcase(str(repository)), "repository root mismatch")
    head = _git(repository, "rev-parse", "HEAD")
    graph = tracked_index_graph(repository, set(EXTENT))
    graph_matches = graph == BASE_NONSTAGE_INDEX
    _expect(graph_matches, "complete nonstage tracked-index graph mismatch")
    _validate_closed_world_status(repository)
    base_exists = subprocess.run(
        ["git", "cat-file", "-e", f"{BASE_COMMIT}^{{commit}}"],
        cwd=repository,
        check=False,
        capture_output=True,
    ).returncode == 0
    if base_exists:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_COMMIT, head],
            cwd=repository,
            check=False,
            capture_output=True,
        )
        _expect(ancestor.returncode == 0, "base is not an ancestor of HEAD")
        changed = _git(repository, "diff", "--name-only", f"{BASE_COMMIT}...HEAD", "--", *FORBIDDEN_PRODUCTION_PATHS)
        _expect(not changed, "production boundary changed")
        return
    git_dir_text = _git(repository, "rev-parse", "--git-dir")
    git_dir = Path(git_dir_text)
    if not git_dir.is_absolute():
        git_dir = repository / git_dir
    shallow = git_dir.resolve(strict=True) / "shallow"
    _expect(shallow.is_file(), "missing Git shallow boundary")
    shallow_heads = {line.strip() for line in shallow.read_text(encoding="ascii").splitlines() if line.strip()}
    _expect(
        shallow_fallback_allowed(
            github_actions=os.environ.get("GITHUB_ACTIONS") == "true",
            head=head,
            shallow_heads=shallow_heads,
            graph_matches=graph_matches,
        ),
        "unverifiable shallow repository boundary",
    )


def validate_contract(root: Path, path: Path, caller_sha256: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    repository = root.resolve(strict=True)
    validate_repository_boundary(repository)
    raw, contract = read_json(path)
    _expect(sha256(raw) == caller_sha256.upper(), "contract caller hash mismatch")
    _keys(
        contract,
        {
            "base_commit",
            "base_nonstage_index",
            "candidate_id",
            "decision_rules",
            "evidence_inputs",
            "extent",
            "production",
            "q1b_integration",
            "q1f_plan_preparation",
            "review_authority",
            "schema",
            "study_id",
            "terminals",
        },
        "contract",
    )
    _expect(contract["schema"] == CONTRACT_SCHEMA, "contract schema mismatch")
    _expect(contract["base_commit"] == BASE_COMMIT, "contract base mismatch")
    _expect(contract["base_nonstage_index"] == BASE_NONSTAGE_INDEX, "contract base index graph mismatch")
    _expect(contract["candidate_id"] == CANDIDATE_ID and contract["study_id"] == STUDY_ID, "contract identity mismatch")
    _expect(contract["production"] == PRODUCTION and contract["q1b_integration"] == "UNAUTHORIZED", "contract production boundary mismatch")
    _expect(contract["q1f_plan_preparation"] == "AUTHORIZED_ONLY_AFTER_ACCEPTED_INDEPENDENT_REVIEW", "Q1F authority mismatch")
    _expect(contract["terminals"] == TERMINALS, "terminal precedence mismatch")
    _expect(contract["extent"] == {"path_count": 7, "paths": EXTENT}, "Q1E extent mismatch")
    _expect(
        contract["decision_rules"]
        == {
            "coarse_locking_rows": "CONVERGENCE_EVIDENCE_NOT_DIRECT_LOCKING_TERMINAL",
            "domain_coercivity": "DOMAIN_WIDE_CERTIFICATE_REQUIRED_FINITE_MESH_SAMPLES_NOT_SUBSTITUTE",
            "finest_division": 32,
            "finest_error_max": "2e-2",
            "resolved_thickness_range": ["1e-2", "1e-3", "1e-4", "1e-5"],
            "response_ratio_spread_max": "5e-3",
            "ultrathin_precision_bits": 256,
            "ultrathin_thickness": "1e-6",
        },
        "decision rules mismatch",
    )
    _expect(
        contract["review_authority"]
        == {
            "independence": {
                "mechanics_executed": False,
                "reviewer_role": "INDEPENDENT_Q1E_SYNTHESIS_REVIEWER",
                "same_agent_as_packet_author": False,
            },
            "path": "docs/reference_cases/e4_pl_q1e_scientific_review.json",
            "schema": REVIEW_SCHEMA,
            "verdict": REVIEW_VERDICT,
        },
        "review authority mismatch",
    )

    rows = contract["evidence_inputs"]
    _expect(isinstance(rows, list) and len(rows) == 9, "evidence input count mismatch")
    expected_roles = [
        "Q1B_PLAN_CONTRACT",
        "Q1B_CYCLE1",
        "Q1B_CYCLE2",
        "Q1B_STATUS",
        "Q1B_SCIENTIFIC_REVIEW",
        "Q1C_CONTRACT",
        "Q1C_RESULT",
        "Q1D_CONTRACT",
        "Q1D_RESULT",
    ]
    _expect([row.get("role") for row in rows] == expected_roles, "evidence role order mismatch")
    _expect(len({row.get("path") for row in rows}) == 9, "duplicate evidence path")
    evidence: dict[str, dict[str, Any]] = {}
    for row in rows:
        _keys(row, {"bytes", "git_blob", "path", "role", "schema", "sha256"}, "evidence row")
        evidence_path = repository / row["path"]
        evidence_raw, value = read_json(evidence_path)
        _expect(len(evidence_raw) == row["bytes"] and sha256(evidence_raw) == row["sha256"], f"evidence identity mismatch: {row['path']}")
        _expect(value.get("schema") == row["schema"], f"evidence schema mismatch: {row['path']}")
        _expect(_git(repository, "rev-parse", f"HEAD:{row['path']}") == row["git_blob"], f"evidence Git blob mismatch: {row['path']}")
        evidence[row["role"]] = value
    return contract, evidence


def _shard(payload: dict[str, Any], shard_id: str) -> dict[str, Any]:
    rows = payload.get("common_payload", {}).get("shards", [])
    matches = [row for row in rows if row.get("shard") == shard_id]
    _expect(len(matches) == 1, f"missing or duplicate shard: {shard_id}")
    return matches[0]


def _upper(row: dict[str, Any], field: str) -> float:
    bound = row.get(field)
    _expect(isinstance(bound, dict) and set(bound) == {"hi", "lo"}, f"invalid bound: {field}")
    return float.fromhex(bound["hi"])


def recompute_gates(evidence: dict[str, dict[str, Any]]) -> dict[str, bool]:
    plan = evidence["Q1B_PLAN_CONTRACT"]
    cycle1 = evidence["Q1B_CYCLE1"]
    cycle2 = evidence["Q1B_CYCLE2"]
    q1b_status = evidence["Q1B_STATUS"]
    q1b_review = evidence["Q1B_SCIENTIFIC_REVIEW"]
    q1c_contract = evidence["Q1C_CONTRACT"]
    q1c = evidence["Q1C_RESULT"]
    q1d_contract = evidence["Q1D_CONTRACT"]
    q1d = evidence["Q1D_RESULT"]

    _expect(plan.get("thresholds", {}).get("locking_analytical_displacement_relative_error_max") == "2e-2", "Q1B error threshold mismatch")
    _expect(plan.get("thresholds", {}).get("locking_response_ratio_spread_max") == "5e-3", "Q1B spread threshold mismatch")
    _expect(plan.get("coercivity", {}).get("domain_certificate") == "INTERVAL_BRANCH_CERTIFICATE_OVER_COMPLETE_G1_DOMAIN_NOT_FINITE_SAMPLE_POSITIVITY", "Q1B coercivity requirement mismatch")
    _expect(cycle1.get("cycle") == 1 and cycle2.get("cycle") == 2, "Q1B cycle identity mismatch")
    _expect(cycle1.get("common_payload") == cycle2.get("common_payload"), "Q1B common payload disagreement")
    _expect(cycle1.get("common_payload_sha256") == sha256(canonical_bytes(cycle1["common_payload"])), "Q1B payload hash mismatch")
    _expect(cycle2.get("common_payload_sha256") == cycle1.get("common_payload_sha256"), "Q1B cycle payload hash disagreement")

    stability = _shard(cycle1, "ASSEMBLED_STABILITY")
    locking = _shard(cycle1, "LOCKING_REFINEMENT")
    nonintrusion = _shard(cycle1, "NONINTRUSION_RECOVERY")
    domain = stability.get("coverage", {}).get("domain_certificate", {})
    stability_closed = stability.get("contradictions") == [] and stability.get("disagreements") == [] and stability.get("coverage", {}).get("certified_failure") is False
    nonintrusion_closed = nonintrusion.get("contradictions") == [] and nonintrusion.get("disagreements") == [] and nonintrusion.get("coverage", {}).get("certified_failure") is False
    domain_unresolved = domain == {"alpha_star": "1e-6", "branch_count": 0, "status": "UNRESOLVED_NOT_FINITE_SAMPLE_SUBSTITUTION"}

    rows = locking.get("coverage", {}).get("rows", [])
    thicknesses = ["1e-2", "1e-3", "1e-4", "1e-5", "1e-6"]
    expected_order = [(division, thickness) for division in (4, 8, 16, 32) for thickness in thicknesses]
    _expect([(row.get("division"), row.get("thickness_ratio")) for row in rows] == expected_order, "Q1B locking coverage mismatch")
    _expect(locking.get("contradictions") == ["LOCKING_ANALYTICAL_ERROR"], "Q1B historical locking disposition mismatch")
    coarse_over_threshold = any(row["division"] < 32 and _upper(row, "relative_error") > 0.02 for row in rows)
    resolved_finest = [row for row in rows if row["division"] == 32 and row["thickness_ratio"] in thicknesses[:4]]
    q1b_resolved_finest_below_limit = len(resolved_finest) == 4 and all(_upper(row, "relative_error") < 0.02 for row in resolved_finest)

    _expect(q1b_status.get("terminal") == "NO_GO_E4_PL_Q1B_LOCKING_OR_CATEGORY_DRIFT", "Q1B historical terminal mismatch")
    _expect(q1b_status.get("production") == PRODUCTION, "Q1B production mismatch")
    _expect(q1b_review.get("verdict") == "ACCEPT_Q1B_SCIENTIFIC_REVIEW_NO_P0_P1" and q1b_review.get("findings") == [], "Q1B review mismatch")

    _expect(q1c_contract.get("q1b_authority", {}).get("cycle1", {}).get("sha256") == "DF040D65A46820C7037111E0B85D6FF4C99E38338CEF9116A908A41F33888407", "Q1C/Q1B binding mismatch")
    _expect(q1c.get("contract_sha256") == "E8D7C83BFE4C2F8734317E525BA8C01EBBDD592E11BCC234B0D3346123D0C89B", "Q1C contract binding mismatch")
    _expect(q1c.get("common_payload_sha256") == sha256(canonical_bytes(q1c["common_payload"])), "Q1C payload hash mismatch")
    _expect(len(q1c.get("cycles", [])) == 2 and q1c["cycles"][0]["aggregate_sha256"] == q1c["cycles"][1]["aggregate_sha256"], "Q1C cycle nondeterminism")
    spatial = _shard(q1c, "SPATIAL_DISCRETIZATION")
    thickness = _shard(q1c, "THICKNESS_LOCKING")
    separation = _shard(q1c, "CONDITIONING_SEPARATION")
    q1c_resolved = (
        spatial.get("contradictions") == []
        and spatial.get("classification_facts") == {
            "coarse_rows_are_convergence_evidence": True,
            "finest_error_below_two_percent": True,
            "monotone_spatial_convergence": True,
        }
        and thickness.get("contradictions") == []
        and thickness.get("classification_facts", {}).get("resolved_error_below_two_percent") is True
        and thickness.get("classification_facts", {}).get("resolved_response_spread_below_limit") is True
        and thickness.get("conditioning_unresolved") is True
        and separation.get("contradictions") == []
        and separation.get("classification_facts", {}).get("resolved_full_equation_parity") is True
        and separation.get("conditioning_unresolved") is True
    )

    _expect(q1d_contract.get("q1c_authority", {}).get("result", {}).get("sha256") == "783482D37DFC2BCCFC6FC8B1992AC12A0A44199DC46074088C5FBC9DB00E784B", "Q1D/Q1C binding mismatch")
    _expect(q1d_contract.get("runtime", {}).get("precision_bits") == [128, 192, 256], "Q1D precision authority mismatch")
    _expect(q1d.get("contract_sha256") == "DB21BE38827C8A0A8D2607D0D9D511C1241CF4E852FD5A3D69C6074A7B6A16CE", "Q1D contract binding mismatch")
    _expect(q1d.get("common_payload_sha256") == sha256(canonical_bytes(q1d["common_payload"])), "Q1D payload hash mismatch")
    _expect(len(q1d.get("cycles", [])) == 2 and q1d["cycles"][0]["aggregate_sha256"] == q1d["cycles"][1]["aggregate_sha256"], "Q1D cycle nondeterminism")
    full = _shard(q1d, "FULL_BLOCK_LDL")
    schur = _shard(q1d, "DRILL_SCHUR")
    refinement = _shard(q1d, "ULTRATHIN_REFINEMENT")
    q1d_ultrathin = all(
        row.get("contradictions") == []
        and row.get("disagreements") == []
        and row.get("precision_unresolved") is False
        and all(row.get("classification_facts", {}).values())
        for row in (full, schur, refinement)
    )
    q1d_equivalence = q1d.get("decision", {}).get("solver_equivalence") == "FULL_BLOCK_LDL_EQUALS_DRILL_SCHUR"
    q1d_locking = q1d.get("decision", {}).get("ultrathin_locking") == "NOT_REPRODUCED_AT_256_BITS"

    production_exact = (
        cycle1.get("common_payload", {}).get("production") == PRODUCTION
        and cycle2.get("common_payload", {}).get("production") == PRODUCTION
        and all(value.get("production") == PRODUCTION for value in (q1b_status, q1c, q1d))
    )
    return {
        "domain_coercivity_unresolved": domain_unresolved,
        "historical_q1b_locking_was_coarse_row_triggered": coarse_over_threshold,
        "historical_q1b_terminal_preserved": True,
        "nonintrusion_recovery_closed": nonintrusion_closed,
        "production_boundary_unchanged": production_exact,
        "q1b_resolved_finest_rows_below_limit": q1b_resolved_finest_below_limit,
        "q1c_resolved_range_locking_closed": q1c_resolved,
        "q1d_solver_equivalence_closed": q1d_equivalence,
        "q1d_ultrathin_locking_closed": q1d_ultrathin and q1d_locking,
        "stability_finite_samples_closed": stability_closed,
    }


def select_terminal(*, blocked: bool, locking: bool, solver_equivalence: bool, stability_or_nonintrusion: bool, domain_unresolved: bool) -> str:
    if blocked:
        return TERMINALS[0]
    if locking:
        return TERMINALS[1]
    if solver_equivalence:
        return TERMINALS[2]
    if stability_or_nonintrusion:
        return TERMINALS[3]
    if domain_unresolved:
        return TERMINALS[4]
    return TERMINALS[5]


def synthesize(root: Path, contract_path: Path, caller_sha256: str) -> dict[str, Any]:
    contract, inputs = validate_contract(root, contract_path, caller_sha256)
    gates = recompute_gates(inputs)
    locking = not (gates["q1b_resolved_finest_rows_below_limit"] and gates["q1c_resolved_range_locking_closed"] and gates["q1d_ultrathin_locking_closed"])
    equivalence = not gates["q1d_solver_equivalence_closed"]
    stability_or_nonintrusion = not (gates["stability_finite_samples_closed"] and gates["nonintrusion_recovery_closed"])
    expected_terminal = select_terminal(
        blocked=False,
        locking=locking,
        solver_equivalence=equivalence,
        stability_or_nonintrusion=stability_or_nonintrusion,
        domain_unresolved=gates["domain_coercivity_unresolved"],
    )
    _expect(expected_terminal == TERMINALS[4], "unexpected Q1E scientific disposition")
    return {
        "candidate_id": CANDIDATE_ID,
        "contract_sha256": caller_sha256.upper(),
        "decision": {
            "continuous_domain_coercivity": "UNRESOLVED_DOMAIN_WIDE_CERTIFICATE_REQUIRED",
            "historical_q1b_locking_interpretation": "SUPERSEDED_IN_Q1E_BY_Q1C_Q1D_BOUNDED_EVIDENCE",
            "historical_q1b_terminal": "NO_GO_E4_PL_Q1B_LOCKING_OR_CATEGORY_DRIFT",
            "solver_equivalence": "FULL_BLOCK_LDL_EQUALS_DRILL_SCHUR",
        },
        "evidence_disposition": "ASSEMBLED_READJUDICATION_COMPLETE_PENDING_INDEPENDENT_REVIEW",
        "evidence_hashes": {row["role"]: row["sha256"] for row in contract["evidence_inputs"]},
        "expected_terminal_after_accepted_review": expected_terminal,
        "gates": gates,
        "production": PRODUCTION,
        "q1b_integration": "UNAUTHORIZED",
        "q1f_plan_preparation": "PENDING_INDEPENDENT_REVIEW",
        "schema": EVIDENCE_SCHEMA,
        "study_id": STUDY_ID,
    }


def validate_review(root: Path, contract: dict[str, Any], reviewed_paths: list[str]) -> tuple[bytes, dict[str, Any]]:
    path = root / contract["review_authority"]["path"]
    raw, review = read_json(path)
    _keys(review, {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}, "review")
    _expect(review["schema"] == REVIEW_SCHEMA and review["verdict"] == REVIEW_VERDICT and review["findings"] == [], "review disposition mismatch")
    _expect(review["reviewer_independence"] == contract["review_authority"]["independence"], "review independence mismatch")
    rows = review["reviewed_inputs"]
    _expect(isinstance(rows, list) and [row.get("path") for row in rows] == sorted(reviewed_paths), "reviewed input extent mismatch")
    _expect(len({row.get("path") for row in rows}) == len(reviewed_paths), "duplicate reviewed input")
    for row in rows:
        _keys(row, {"bytes", "path", "sha256"}, "reviewed input")
        value = (root / row["path"]).read_bytes()
        _expect(len(value) == row["bytes"] and sha256(value) == row["sha256"], f"review binding mismatch: {row['path']}")
    return raw, review


def write_exclusive(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthesize-assembled-readjudication", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        value = synthesize(args.repository_root.resolve(strict=True), args.contract, args.contract_sha256)
        write_exclusive(args.output, value)
        return 0
    except (OSError, TypeError, ValueError, SynthesisError) as exc:
        print(f"{TERMINALS[0]}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
