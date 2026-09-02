"""Standard-library-only V6H Stage 4A preparation authority generator."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Mapping


SCHEMA = "anysolver.e4-pl-s3-v6h-stage4a-preparation-authority-v1"
CONTRACT_SCHEMA = "anysolver.e4-pl-s3-v6h-stage4a-authority-contract-v1"


class V6HAuthorityError(RuntimeError):
    """Raised when a frozen authority input differs."""


def _reject_constant(value: str) -> None:
    raise V6HAuthorityError(f"nonfinite JSON constant is forbidden: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise V6HAuthorityError(f"duplicate JSON key is forbidden: {key}")
        made[key] = value
    return made


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any) -> None:
        if item is None or isinstance(item, (bool, int, str)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise V6HAuthorityError("nonfinite JSON number is forbidden")
            return
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise V6HAuthorityError("JSON keys must be strings")
                visit(child)
            return
        raise V6HAuthorityError(f"unsupported JSON type: {type(item).__name__}")

    visit(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, V6HAuthorityError):
            raise
        raise V6HAuthorityError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6HAuthorityError(f"noncanonical JSON: {path}")
    return value, raw


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=NUL",
            "-c",
            "core.attributesFile=NUL",
            "-c",
            "extensions.objectFormat=sha1",
            *arguments,
        ],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def generate(root: Path, contract_path: Path, authority_commit: str) -> dict[str, Any]:
    root = root.resolve()
    contract_path = contract_path.resolve()
    contract, contract_raw = strict_json(contract_path)
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise V6HAuthorityError("V6H contract schema differs")
    frozen = contract.get("frozen_inputs")
    if not isinstance(frozen, list) or not frozen:
        raise V6HAuthorityError("V6H frozen input graph is empty")
    input_rows: list[dict[str, Any]] = []
    for item in frozen:
        if not isinstance(item, Mapping):
            raise V6HAuthorityError("V6H frozen input row is malformed")
        path = root / str(item["path"])
        raw = path.read_bytes()
        if len(raw) != int(item["bytes"]) or _sha256(raw) != item["sha256"]:
            raise V6HAuthorityError(f"V6H frozen input differs: {item['path']}")
        input_rows.append(dict(item))
    commit = str(authority_commit).lower()
    if len(commit) != 40 or any(value not in "0123456789abcdef" for value in commit):
        raise V6HAuthorityError("authority commit is not a canonical SHA-1")
    lines = _git(root, "show", "-s", "--format=%H%n%T%n%P%n%s", commit).splitlines()
    if len(lines) != 4:
        raise V6HAuthorityError("authority commit identity is malformed")
    actual_commit, tree, parent, subject = lines
    expected = contract["authority_commit"]
    paths = sorted(
        value
        for value in _git(
            root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit
        ).splitlines()
        if value
    )
    if (
        actual_commit != commit
        or parent != expected["expected_parent"]
        or subject != expected["expected_subject"]
        or paths != sorted(expected["expected_paths"])
        or len(paths) != int(expected["exact_path_count"])
    ):
        raise V6HAuthorityError("authority commit topology or extent differs")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise V6HAuthorityError("V6H authority requires a clean worktree")
    return {
        "activation_authorized": False,
        "authority_commit": {
            "commit": commit,
            "contract_sha256": _sha256(contract_raw),
            "parent": parent,
            "paths": paths,
            "subject": subject,
            "tree": tree,
        },
        "candidate": contract["candidate"],
        "frozen_inputs": input_rows,
        "next_gate": contract["next_gate"],
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "runtime_policy": contract["runtime_policy"],
        "schema": SCHEMA,
        "scientific_schema_compatibility": contract[
            "scientific_schema_compatibility"
        ],
        "stage4a_execution_authorized": False,
        "stage4a_preparation_authorized": True,
        "terminal": "PROVISIONAL_GO_E4_PL_S3_V6H_STAGE4A_PREPARATION",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--authority-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = canonical_bytes(generate(args.root, args.contract, args.authority_commit))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as handle:
        handle.write(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
