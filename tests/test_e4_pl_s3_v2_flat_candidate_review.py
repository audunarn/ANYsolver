from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
REGISTERED_COMMIT = "d1f6d3d264882cc70a34b6a764476f5ec6baeb3b"
REVIEW_PATH = "docs/reference_cases/e4_pl_s3_v2_flat_candidate_review.json"


def _sanitized_git(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return subprocess.run(
        ["git", "-c", f"safe.directory={ROOT}", *arguments],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        check=False,
    )


def _is_explicit_github_shallow_boundary() -> bool:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return False
    shallow_repository = _sanitized_git("rev-parse", "--is-shallow-repository")
    if shallow_repository.returncode or shallow_repository.stdout.strip() != b"true":
        return False
    shallow_name = _sanitized_git("rev-parse", "--git-path", "shallow")
    head = _sanitized_git("rev-parse", "HEAD")
    if shallow_name.returncode or head.returncode:
        return False
    shallow = Path(os.fsdecode(shallow_name.stdout.strip()))
    if not shallow.is_absolute():
        shallow = (ROOT / shallow).resolve()
    if not shallow.is_file():
        return False
    return head.stdout.decode("ascii").strip() in shallow.read_text(
        encoding="ascii"
    ).splitlines()


def _registered_bytes(path: str) -> bytes:
    replacement_refs = _sanitized_git("replace", "-l")
    assert replacement_refs.returncode == 0, replacement_refs.stderr.decode(
        "utf-8", errors="replace"
    )
    assert replacement_refs.stdout == b"", "replacement refs are forbidden"
    graft_name = _sanitized_git("rev-parse", "--git-path", "info/grafts")
    assert graft_name.returncode == 0, graft_name.stderr.decode(
        "utf-8", errors="replace"
    )
    graft = Path(os.fsdecode(graft_name.stdout.strip()))
    if not graft.is_absolute():
        graft = (ROOT / graft).resolve()
    assert not graft.exists(), "Git grafts are forbidden"

    object_name = f"{REGISTERED_COMMIT}:{path}"
    probe = _sanitized_git("cat-file", "-e", object_name)
    if probe.returncode:
        assert _is_explicit_github_shallow_boundary(), (
            f"registered object is unavailable outside an explicit GitHub shallow "
            f"boundary: {object_name}: "
            f"{probe.stderr.decode('utf-8', errors='replace').strip()}"
        )
        pytest.skip(
            "immutable registered bytes are unavailable at the explicit GitHub "
            "shallow boundary; working-tree bytes are intentionally forbidden"
        )
    shown = _sanitized_git("show", "--no-ext-diff", "--no-textconv", object_name)
    assert shown.returncode == 0, shown.stderr.decode("utf-8", errors="replace")
    return shown.stdout


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    made: dict[str, object] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def _reject_nonfinite(value: str) -> object:
    raise ValueError(f"nonfinite JSON value: {value}")


def _decode(raw: bytes) -> dict[str, object]:
    made = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicates,
        parse_constant=_reject_nonfinite,
    )
    assert isinstance(made, dict)
    assert raw == (
        json.dumps(made, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    return made


def _canonical_repository_bytes(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def test_review_is_canonical_independent_empty_and_hash_bound() -> None:
    review = _decode(_registered_bytes(REVIEW_PATH))
    assert set(review) == {
        "findings",
        "reviewed_inputs",
        "reviewer_independence",
        "schema",
        "verdict",
    }
    assert review["findings"] == {"P0": [], "P1": []}
    assert review["schema"] == (
        "anysolver.e4-pl-s3-v2-flat-candidate-independent-review-v1"
    )
    assert review["verdict"] == (
        "ACCEPTED_STRICT_FLAT_OPT_IN_CANDIDATE_NO_P0_P1_STAGE4_UNAUTHORIZED"
    )
    independence = review["reviewer_independence"]
    assert independence["authored_reviewed_mechanics"] is False
    assert independence["production_candidate_authored"] is False

    paths = [record["path"] for record in review["reviewed_inputs"]]
    assert len(paths) == len(set(paths))
    assert "docs/reference_cases/e4_pl_s3_v2_candidate_binding.json" in paths
    for record in review["reviewed_inputs"]:
        raw = _canonical_repository_bytes(_registered_bytes(record["path"]))
        assert len(raw) == record["bytes"]
        assert hashlib.sha256(raw).hexdigest().upper() == record["sha256"]


def test_review_parser_rejects_duplicate_and_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="duplicate JSON key"):
        _decode(b'{"a":1,"a":2}\n')
    with pytest.raises(ValueError, match="nonfinite JSON value"):
        _decode(b'{"a":NaN}\n')
