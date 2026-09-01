"""Validate and synthesize the hash-bound V6 native-parity source selection."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
PLAN = REFERENCE / "e4_pl_s3_v6_native_parity_source_plan.json"
CONTRACT = REFERENCE / "e4_pl_s3_v6_native_parity_source_contract.json"
SELECTION = REFERENCE / "e4_pl_s3_v6_native_parity_source_selection.json"
BLOCKED = "BLOCKED_E4_PL_S3_V6_SOURCE_OR_REVIEW"
V3_REQUIRED = "UNCLASSIFIED_E4_PL_S3_V6_V3_PUBLISHED_FORMULATION_REQUIRED"
PASS = "PROVISIONAL_GO_E4_PL_S3_V6_V2D_NATIVE_PARITY_IMPLEMENTATION"


class V6SourceAuthorityError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise V6SourceAuthorityError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            V6SourceAuthorityError(f"nonfinite token: {token}")
        ),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6SourceAuthorityError(f"noncanonical JSON: {path}")
    return raw, value


def _git(repo: Path, *arguments: str) -> str:
    env = dict(os.environ)
    env.update(
        {
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": "",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_GRAFT_FILE": os.devnull,
            "GIT_NO_REPLACE_OBJECTS": "1",
        }
    )
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={repo.as_posix()}",
            "-c",
            f"core.attributesFile={os.devnull}",
            "-c",
            f"core.excludesFile={os.devnull}",
            "-C",
            str(repo),
            *arguments,
        ],
        check=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _validate_commit(contract: Mapping[str, Any]) -> dict[str, str]:
    authority = contract["authority"]
    head = _git(ROOT, "rev-parse", "HEAD")
    parent = _git(ROOT, "rev-parse", "HEAD^")
    subject = _git(ROOT, "show", "-s", "--format=%s", "HEAD")
    paths = sorted(
        line
        for line in _git(ROOT, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        if line
    )
    if parent != authority["expected_parent"]:
        raise V6SourceAuthorityError("V6 authority parent mismatch")
    if subject != authority["expected_subject"]:
        raise V6SourceAuthorityError("V6 authority subject mismatch")
    if paths != sorted(authority["exact_paths"]):
        raise V6SourceAuthorityError("V6 authority changed-path set mismatch")
    return {"commit": head, "tree": _git(ROOT, "rev-parse", "HEAD^{tree}")}


def _validate_local_sources(selection: Mapping[str, Any]) -> list[dict[str, Any]]:
    checked: list[dict[str, Any]] = []
    for row in selection["local_sources"]:
        path = ROOT / row["path"]
        raw = path.read_bytes()
        blob = _git(ROOT, "rev-parse", f"HEAD:{row['path']}")
        if len(raw) != row["bytes"] or sha256(raw) != row["sha256"] or blob != row["blob"]:
            raise V6SourceAuthorityError(f"local source mismatch: {row['path']}")
        checked.append({"bytes": len(raw), "path": row["path"], "role": row["role"], "sha256": row["sha256"]})
    return checked


def _validate_external_sources(
    contract: Mapping[str, Any], selection: Mapping[str, Any]
) -> list[dict[str, Any]]:
    external = contract["external"]
    base = Path(external["registered_root"])
    repositories = {row["role"]: row for row in external["repositories"]}
    selections = {row["role"]: row for row in selection["external_sources"]}
    if set(repositories) != set(selections):
        raise V6SourceAuthorityError("external repository role inventory mismatch")
    checked: list[dict[str, Any]] = []
    for role in sorted(repositories):
        binding = repositories[role]
        source = selections[role]
        repo = base / binding["directory"]
        if not repo.is_dir():
            raise V6SourceAuthorityError(f"external repository absent: {role}")
        if _git(repo, "rev-parse", "HEAD") != binding["expected_commit"] or source["commit"] != binding["expected_commit"]:
            raise V6SourceAuthorityError(f"external commit mismatch: {role}")
        if _git(repo, "rev-parse", "HEAD^{tree}") != binding["expected_tree"] or source["tree"] != binding["expected_tree"]:
            raise V6SourceAuthorityError(f"external tree mismatch: {role}")
        expected_paths = {row["path"] for row in source["files"]}
        observed_paths = {
            path.relative_to(repo).as_posix()
            for path in repo.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(repo).parts
        }
        if observed_paths != expected_paths:
            raise V6SourceAuthorityError(f"external registered-file inventory mismatch: {role}")
        for row in source["files"]:
            path = repo / row["path"]
            raw = path.read_bytes()
            blob = _git(repo, "rev-parse", f"HEAD:{row['path']}")
            if len(raw) != row["bytes"] or sha256(raw) != row["sha256"] or blob != row["blob"]:
                raise V6SourceAuthorityError(f"external source mismatch: {role}:{row['path']}")
            checked.append({"bytes": len(raw), "path": row["path"], "role": role, "sha256": row["sha256"]})
    return checked


def validate(
    selection: Mapping[str, Any] | None = None,
    *,
    require_commit: bool = False,
) -> dict[str, Any]:
    plan_raw, plan = load(PLAN)
    contract_raw, contract = load(CONTRACT)
    selection_raw, loaded_selection = load(SELECTION)
    selected = loaded_selection if selection is None else dict(selection)
    if plan.get("schema") != "anysolver.e4-pl-s3-v6-native-parity-source-plan-v1":
        raise V6SourceAuthorityError("V6 plan schema mismatch")
    if contract.get("schema") != "anysolver.e4-pl-s3-v6-native-parity-source-contract-v1":
        raise V6SourceAuthorityError("V6 contract schema mismatch")
    if selected.get("schema") != "anysolver.e4-pl-s3-v6-native-parity-source-selection-v1":
        raise V6SourceAuthorityError("V6 selection schema mismatch")
    for row in contract["frozen_inputs"]:
        raw = (ROOT / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or sha256(raw) != row["sha256"]:
            raise V6SourceAuthorityError(f"frozen input mismatch: {row['path']}")
    if sha256(plan_raw) != contract["frozen_inputs"][3]["sha256"] or sha256(selection_raw) != contract["frozen_inputs"][4]["sha256"]:
        raise V6SourceAuthorityError("V6 protocol binding mismatch")
    if selected.get("production_boundary") != contract["production_boundary"] or selected.get("production_boundary") != plan["production_boundary"]:
        raise V6SourceAuthorityError("V6 production boundary mismatch")
    decisions = selected.get("decisions")
    if not isinstance(decisions, dict) or set(decisions) != set(plan["required_source_decisions"]):
        raise V6SourceAuthorityError("V6 source decision inventory mismatch")
    for name, decision in decisions.items():
        if not isinstance(decision, dict) or not decision.get("authority") or not decision.get("decision"):
            raise V6SourceAuthorityError(f"V6 decision is incomplete: {name}")
    expected_scope = {
        "activation_authorized": False,
        "complete_activation_execution_authorized": False,
        "legacy_tri3_mechanics_authorized": False,
        "v2c_operator_change_authorized": False,
        "v2d_native_parity_implementation_authorized": True,
    }
    if selected.get("scope") != expected_scope or selected.get("terminal") != PASS:
        raise V6SourceAuthorityError("V6 scope or terminal mismatch")
    if selected.get("candidate", {}).get("formulation_id") != plan["candidate"]["formulation_id"]:
        raise V6SourceAuthorityError("V6 candidate mismatch")
    local = _validate_local_sources(selected)
    external = _validate_external_sources(contract, selected)
    authority = _validate_commit(contract) if require_commit else {
        "commit": _git(ROOT, "rev-parse", "HEAD"),
        "tree": _git(ROOT, "rev-parse", "HEAD^{tree}"),
    }
    return {
        "activation_authorized": False,
        "authority": authority,
        "candidate_formulation_id": selected["candidate"]["formulation_id"],
        "complete_activation_execution_authorized": False,
        "decision_count": len(decisions),
        "decision_ids": sorted(decisions),
        "external_file_count": len(external),
        "external_files_sha256": sha256(canonical_bytes(external)),
        "local_file_count": len(local),
        "local_files_sha256": sha256(canonical_bytes(local)),
        "next_gate": plan["next_gate_on_acceptance"],
        "production_boundary": plan["production_boundary"],
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v6-native-parity-source-evidence-v1",
        "selection_sha256": sha256(selection_raw),
        "terminal": PASS,
        "v2d_native_parity_implementation_authorized": True,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-source-authority", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    raw = canonical_bytes(validate(require_commit=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
