"""Validate the hash-bound V5G Stage 4B extension source authority."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
SELECTION = ROOT / "docs/reference_cases/e4_pl_s3_v5g_stage4b_extension_source_selection.json"
EXTERNAL_ROOT = Path(r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v5b-source-authority-20260901\MYSTRAN")
SCHEMA = "anysolver.e4-pl-s3-v5g-stage4b-extension-authority-result-v1"
PASS = "PROVISIONAL_GO_E4_PL_S3_V5G_V2C_EXTENSION_IMPLEMENTATION"


class ExtensionAuthorityError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise ExtensionAuthorityError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> Any:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(ExtensionAuthorityError(f"nonfinite token: {token}")))
    if raw != canonical_bytes(value):
        raise ExtensionAuthorityError(f"noncanonical JSON: {path}")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _git(*arguments: str) -> str:
    safe = EXTERNAL_ROOT.as_posix()
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={safe}", "-C", str(EXTERNAL_ROOT), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def validate(selection: Mapping[str, Any] | None = None) -> dict[str, Any]:
    document = load_canonical(SELECTION) if selection is None else dict(selection)
    if document.get("schema") != "anysolver.e4-pl-s3-v5g-stage4b-extension-source-selection-v1":
        raise ExtensionAuthorityError("unexpected V5G selection schema")
    source = document.get("external_source", {})
    if _git("rev-parse", "HEAD") != source.get("commit") or _git("rev-parse", "HEAD^{tree}") != source.get("tree"):
        raise ExtensionAuthorityError("external source Git identity mismatch")
    if _git("status", "--porcelain"):
        raise ExtensionAuthorityError("external source worktree is dirty")
    checked: list[dict[str, Any]] = []
    for binding in source.get("files", []):
        path = EXTERNAL_ROOT / str(binding["path"])
        raw = path.read_bytes()
        blob = _git("rev-parse", f"HEAD:{binding['path']}")
        if len(raw) != binding["bytes"] or hashlib.sha256(raw).hexdigest().upper() != binding["sha256"] or blob != binding["blob"]:
            raise ExtensionAuthorityError(f"external source binding mismatch: {binding['path']}")
        checked.append({"bytes": len(raw), "path": binding["path"], "sha256": binding["sha256"]})
    predecessor_paths = {
        "result_sha256": ROOT / "docs/reference_cases/e4_pl_s3_v5f_production_parity_result.json",
        "review_sha256": ROOT / "docs/reference_cases/e4_pl_s3_v5f_production_parity_review.json",
        "status_sha256": ROOT / "docs/reference_cases/e4_pl_s3_v5f_production_parity_status.json",
    }
    for key, path in predecessor_paths.items():
        if _sha(path) != document["predecessor"][key]:
            raise ExtensionAuthorityError(f"V5F predecessor mismatch: {key}")
    if document.get("terminal") != PASS or document.get("scope") != {
        "full_nonlinear_authorized": False,
        "generalized_sections_authorized": False,
        "legacy_dispatch_authorized": False,
        "stage4b_execution_authorized": False,
        "v2c_implementation_authorized": True,
    }:
        raise ExtensionAuthorityError("V5G scope or terminal mismatch")
    return {
        "activation_authorized": False,
        "candidate_formulation_id": document["candidate"]["formulation_id"],
        "external_commit": source["commit"],
        "external_file_count": len(checked),
        "external_files_sha256": hashlib.sha256(canonical_bytes(checked)).hexdigest().upper(),
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "selection_sha256": _sha(SELECTION),
        "stage4b_execution_authorized": False,
        "terminal": PASS,
        "v2c_implementation_authorized": True,
    }


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-source-authority", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, validate())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
