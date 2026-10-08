"""Check the preserved tangent verdict with its explicit metadata amendment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def main(amendment_path: Path, output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(output_path)
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    original_path = Path(amendment["original_registration"])
    raw_path = Path(amendment["original_formal_raw"])
    numerical_path = Path(amendment["original_numerical_verdict"])
    original = json.loads(original_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    numerical = json.loads(numerical_path.read_text(encoding="utf-8"))
    correction = amendment["correction"]
    prefix = "source_blobs."
    field = correction["field"]
    if not field.startswith(prefix):
        raise ValueError("amendment may correct only one source blob")
    corrected_path = field[len(prefix):]
    source_commit = original["source_commit"]
    checks = {
        "original_registration_hash": _sha256(original_path)
        == amendment["original_registration_sha256"],
        "original_raw_hash": _sha256(raw_path)
        == amendment["original_formal_raw_sha256"],
        "original_numerical_verdict_hash": _sha256(numerical_path)
        == amendment["original_numerical_verdict_sha256"],
        "original_case_identity": original["case_id"] == amendment["amends"],
        "source_commit_identity": source_commit == amendment["source_commit"],
        "original_bad_value_preserved": original["source_blobs"].get(
            corrected_path) == correction["original_value"],
        "one_declared_correction": len([
            path for path, blob in original["source_blobs"].items()
            if blob != _git("rev-parse", f"{source_commit}:{path}")
        ]) == 1,
        "mechanics_unchanged": (
            amendment["mechanical_inputs_or_criteria_changed"] is False
            and amendment["additional_mechanics_execution"] is False),
        "numerical_verdict_binding": (
            numerical["registration_sha256"] == _sha256(original_path)
            and numerical["raw_sha256"] == _sha256(raw_path)
            and numerical["status"] == "pass"
            and all(numerical["checks"].values())
            and raw["status"] == "passed_development"),
    }
    blob_checks = {}
    for path, original_blob in original["source_blobs"].items():
        expected = (correction["corrected_value"]
                    if path == corrected_path else original_blob)
        blob_checks[path] = (
            bool(re.fullmatch(r"[0-9a-f]{40}", expected))
            and _git("rev-parse", f"{source_commit}:{path}") == expected
            and _git("rev-parse", f"HEAD:{path}") == expected
            and _git("status", "--porcelain", "--untracked-files=no", "--",
                     path) == ""
        )
    checks["all_corrected_blobs_match_source_and_current_tree"] = all(
        blob_checks.values())
    checks["correction_is_actual_blob"] = blob_checks.get(
        corrected_path, False)
    disposition = {
        "amendment": str(amendment_path),
        "amendment_sha256": _sha256(amendment_path),
        "original_registration_sha256": _sha256(original_path),
        "original_raw_sha256": _sha256(raw_path),
        "original_numerical_verdict_sha256": _sha256(numerical_path),
        "checks": checks,
        "blob_checks": blob_checks,
        "status": "pass" if all(checks.values()) else "fail",
    }
    output_path.write_text(json.dumps(disposition, indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({"status": disposition["status"], "checks": checks},
                     indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: identity_adjudicate.py AMENDMENT VERDICT")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
