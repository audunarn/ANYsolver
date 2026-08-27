"""Create a deterministic, non-authorizing S3-v3 candidate binding.

The final candidate graph is intentionally supplied at execution time so
refreshed sibling commits and locally qualified wheels cannot be silently
inherited from protocol v2.  This standard-library program verifies clean Git
identities and live wheel bytes, binds the successor programs, and writes one
exclusive canonical JSON input.  A later reviewed authorization commit must
bind that output before any formal qualification execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
BINDING_GENERATOR = Path(__file__).resolve()
CONTRACT = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_qualification_optimization_v3_contract.json"
)
COORDINATOR = ROOT / "scripts" / "benchmark_e4_pl_s3_activation_cold_path.py"
FORMAL_RUNNER = ROOT / "scripts" / "run_e4_pl_s3_qualification_v3.py"
SUCCESSOR = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_qualification_optimization_v3.py"
)
TEST = ROOT / "tests" / "test_e4_pl_s3_activation_cold_path.py"
FORMAL_TEST = ROOT / "tests" / "test_e4_pl_s3_qualification_optimization_v3.py"
OPTIMIZATION_EVIDENCE = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_qualification_optimization_v3_evidence.json"
)
MANIFEST = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
)
SCHEMA = "anysolver.e4-pl-s3-qualification-candidate-binding-v3"
GRAPH_SCHEMA = "anysolver.e4-pl-s3-final-candidate-graph-v3"
PREFLIGHT_SCHEMA = "anysolver.e4-pl-s3-candidate-preflight-v3"
CANDIDATES = (
    "ANYfem",
    "ANYfileIO",
    "ANYgeometry",
    "ANYintelligent",
    "ANYmaterial",
    "ANYmesh",
    "ANYsolver",
    "ANYstructure",
)
PACKAGED = frozenset(
    {
        "ANYsolver",
        "ANYmesh",
        "ANYfem",
        "ANYstructure",
        "ANYfileIO",
        "ANYmaterial",
        "ANYgeometry",
    }
)
PREFLIGHT_GATE_IDS = {
    "ANYfem": (
        "full-repository-tests",
        "qualified-s3-policy-and-migration",
    ),
    "ANYfileIO": (
        "full-repository-tests",
        "neutral-shell-formulation-and-owner-normal",
    ),
    "ANYgeometry": ("full-repository-tests",),
    "ANYintelligent": (
        "full-repository-tests",
        "production-anysolver-adapter-routing",
    ),
    "ANYmaterial": ("full-repository-tests",),
    "ANYmesh": (
        "full-repository-tests",
        "qualified-s3-admission-repair-and-normals",
    ),
    "ANYsolver": (
        "full-repository-tests",
        "package-isolation-and-default-routing",
        "q4-mechanics-identity",
    ),
    "ANYstructure": (
        "full-repository-tests",
        "runtime-state-v2-formulation-and-normal",
    ),
}
HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9A-F]{64}")
Q4_BASE_IDENTITY = {
    "commit": "62464bea649229aa2c9f89ba7cbe431bf6a9282a",
    "parent": "19d7726ad09a4969c187af1816bab08596db7590",
    "subject": "docs: record bounded S3 activation forecast",
    "tree": "c5cc24fa60a3ce1cdc3a1910bd45fe0efe7ec620",
}
Q4_GUARD_SOURCE_IDENTITY = {
    "commit": "04ec1d5cbb5725913aec35ec62ba1de754881360",
    "parent": Q4_BASE_IDENTITY["commit"],
    "subject": "fix: bind Q4 vector state sealing to producer origin",
    "tree": "310f9cc18b3dd0fe439a96f8adcc0e36bafe94fb",
}
Q4_GUARD_IMPORT_IDENTITY = {
    "commit": "eeec9ebd430c65d0af5ac29f0f4ba0c1fe5ddbbc",
    "parent": "084f6da03d573ea0dedd46c0ecb45ebd487fad08",
    "subject": Q4_GUARD_SOURCE_IDENTITY["subject"],
    "tree": "60a01afc1cfe7521bb62c4a928632e4d7f4f2555",
}
Q4_GUARD_PATH_BLOBS = (
    (
        "docs/reference_cases/e4_pl_q4_state_seal_guard_v2_incident.md",
        "dbb69ff168d2ed938eec87f3d86143aa3c0ec92d",
    ),
    (
        "src/anysolver/e4_pl_element.py",
        "031da1cde23e7983c0f94d837f5610a24737920b",
    ),
    (
        "src/anysolver/nonlinear_performance.py",
        "80e7bc75c897aa83617ae1d35b47631b894d5481",
    ),
    (
        "src/anysolver/nonlinear_state.py",
        "9b578d2d8ed55c3ab8e14f11c24737361d2a785e",
    ),
    (
        "src/anysolver/nonlinear_static.py",
        "645fcee0d5dd6ccf7ca89ea80870b2b0e22ba974",
    ),
    (
        "tests/test_e4_pl_q4_current_tangent.py",
        "ac4a695088aeb79dc6392163446f6acb2f662247",
    ),
)
Q4_GUARD_SOURCE_PATHS = tuple(
    path for path, _blob in Q4_GUARD_PATH_BLOBS if path.startswith("src/")
)
Q4_NONMECHANICS_INTEGRATION_PATHS = (
    "src/anysolver/anystructure_fem_mode.py",
    "src/anysolver/production_readiness.py",
)
Q4_FROZEN_SOURCE_EXCLUSIONS = tuple(
    sorted((*Q4_GUARD_SOURCE_PATHS, *Q4_NONMECHANICS_INTEGRATION_PATHS))
)
Q4_FROZEN_SOURCE_FILE_COUNT = 104
Q4_FROZEN_SOURCE_ROWS_SHA256 = (
    "1D9750A40548B268C78BFB017F60C290E2554E8018D806F0C1185BB30C6BF365"
)


class BindingError(ValueError):
    """The supplied candidate graph cannot be bound safely."""


def _pairs(values: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise BindingError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise BindingError(f"nonfinite JSON value is forbidden: {value}")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_bytes(),
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise BindingError(f"{path} must contain one JSON object")
    return value


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _file_binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file() or resolved.is_symlink():
        raise BindingError(f"binding target is not a regular file: {path}")
    raw = resolved.read_bytes()
    if not raw:
        raise BindingError(f"binding target is empty: {path}")
    return {
        "bytes": len(raw),
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
    }


def _git(root: Path, *arguments: str) -> str:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_GRAFT_FILE": os.devnull,
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_REPLACE_REF_BASE": "refs/disabled-replacements/",
        }
    )
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.attributesFile=NUL" if os.name == "nt" else "core.attributesFile=/dev/null",
            "-C",
            str(root),
            *arguments,
        ],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )
    if result.returncode != 0:
        raise BindingError(f"Git identity check failed for {root}")
    return result.stdout.rstrip("\r\n")


def _commit_identity(root: Path, commit: str) -> dict[str, str]:
    fields = _git(
        root,
        "show",
        "-s",
        "--format=%H%x00%T%x00%P%x00%s",
        commit,
    ).split("\x00")
    if len(fields) != 4 or " " in fields[2]:
        raise BindingError(f"Git commit identity differs for {commit}")
    return {
        "commit": fields[0],
        "tree": fields[1],
        "parent": fields[2],
        "subject": fields[3],
    }


def _changed_paths(root: Path, parent: str, commit: str) -> list[str]:
    value = _git(root, "diff", "--name-only", parent, commit)
    return value.splitlines() if value else []


def _blob(root: Path, commit: str, path: str) -> str:
    return _git(root, "rev-parse", f"{commit}:{path}")


def _frozen_source_rows(root: Path, commit: str) -> list[dict[str, str]]:
    output = _git(root, "ls-tree", "-r", commit, "--", "src/anysolver")
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        metadata, separator, path = line.partition("\t")
        fields = metadata.split()
        if (
            separator != "\t"
            or len(fields) != 3
            or fields[1] != "blob"
            or HEX40.fullmatch(fields[2]) is None
            or not path.startswith("src/anysolver/")
        ):
            raise BindingError("frozen Q4 source tree entry is malformed")
        if path not in Q4_FROZEN_SOURCE_EXCLUSIONS:
            rows.append({"git_blob": fields[2], "path": path})
    if [row["path"] for row in rows] != sorted(row["path"] for row in rows):
        raise BindingError("frozen Q4 source tree order differs")
    return rows


def _verify_anysolver_policy(
    value: object,
    solver: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind the reviewed guard correction and a base-identical source superset."""

    if not isinstance(value, dict) or set(value) != {
        "base_commit",
        "changed_paths",
        "q4_guard_import_commit",
    }:
        raise BindingError("ANYsolver policy fields differ")
    base_commit = value["base_commit"]
    changed_paths = value["changed_paths"]
    guard_import_commit = value["q4_guard_import_commit"]
    if (
        base_commit != Q4_BASE_IDENTITY["commit"]
        or guard_import_commit != Q4_GUARD_IMPORT_IDENTITY["commit"]
        or not isinstance(changed_paths, list)
        or any(type(path) is not str or not path for path in changed_paths)
        or changed_paths != sorted(set(changed_paths))
    ):
        raise BindingError("ANYsolver policy is malformed")
    solver_root = Path(str(solver["root"])).resolve(strict=True)
    candidate_commit = str(solver["commit"])
    if _commit_identity(solver_root, base_commit) != Q4_BASE_IDENTITY:
        raise BindingError("frozen Q4 base identity differs")
    if (
        _commit_identity(solver_root, Q4_GUARD_SOURCE_IDENTITY["commit"])
        != Q4_GUARD_SOURCE_IDENTITY
    ):
        raise BindingError("reviewed Q4 guard source identity differs")
    if (
        _commit_identity(solver_root, guard_import_commit)
        != Q4_GUARD_IMPORT_IDENTITY
    ):
        raise BindingError("imported Q4 guard identity differs")
    if _changed_paths(
        solver_root,
        Q4_GUARD_SOURCE_IDENTITY["parent"],
        Q4_GUARD_SOURCE_IDENTITY["commit"],
    ) != [path for path, _blob_id in Q4_GUARD_PATH_BLOBS]:
        raise BindingError("reviewed Q4 guard path set differs")
    if _changed_paths(
        solver_root,
        Q4_GUARD_IMPORT_IDENTITY["parent"],
        Q4_GUARD_IMPORT_IDENTITY["commit"],
    ) != [path for path, _blob_id in Q4_GUARD_PATH_BLOBS]:
        raise BindingError("imported Q4 guard path set differs")
    for path, expected_blob in Q4_GUARD_PATH_BLOBS:
        observed = {
            _blob(solver_root, Q4_GUARD_SOURCE_IDENTITY["commit"], path),
            _blob(solver_root, guard_import_commit, path),
            _blob(solver_root, candidate_commit, path),
        }
        if observed != {expected_blob}:
            raise BindingError(f"reviewed Q4 guard blob differs: {path}")
    _git(solver_root, "merge-base", "--is-ancestor", guard_import_commit, candidate_commit)
    observed_paths = _changed_paths(solver_root, base_commit, candidate_commit)
    if observed_paths != changed_paths:
        raise BindingError("ANYsolver changed paths differ")
    base_rows = _frozen_source_rows(solver_root, base_commit)
    candidate_rows = _frozen_source_rows(solver_root, candidate_commit)
    rows_sha256 = hashlib.sha256(canonical_bytes(base_rows)).hexdigest().upper()
    if (
        base_rows != candidate_rows
        or len(base_rows) != Q4_FROZEN_SOURCE_FILE_COUNT
        or rows_sha256 != Q4_FROZEN_SOURCE_ROWS_SHA256
    ):
        raise BindingError("frozen Q4 mechanics/source identity differs")
    return {
        "base": dict(Q4_BASE_IDENTITY),
        "candidate": {
            "commit": candidate_commit,
            "tree": str(solver["tree"]),
        },
        "changed_paths": changed_paths,
        "frozen_q4_source_identity": {
            "excluded_authorized_guard_paths": list(Q4_GUARD_SOURCE_PATHS),
            "excluded_nonmechanics_integration_paths": list(
                Q4_NONMECHANICS_INTEGRATION_PATHS
            ),
            "file_count": len(base_rows),
            "rows_sha256": rows_sha256,
            "scope": (
                "ALL_TRACKED_SRC_ANYSOLVER_FILES_EXCEPT_EXACT_GUARD_AND_"
                "NON_Q4_INTEGRATION_PATHS"
            ),
        },
        "guard_correction": {
            "authorized_paths": [
                {"git_blob": blob_id, "path": path}
                for path, blob_id in Q4_GUARD_PATH_BLOBS
            ],
            "imported": dict(Q4_GUARD_IMPORT_IDENTITY),
            "reviewed_source": dict(Q4_GUARD_SOURCE_IDENTITY),
            "scope": "GUARD_SERIALIZATION_AND_STATE_LIFECYCLE_ONLY",
        },
        "q4_mechanics_change": "NONE",
    }


def _reverify_bound_anysolver_policy(
    value: object,
    solver: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BindingError("bound ANYsolver policy is malformed")
    input_policy = {
        "base_commit": Q4_BASE_IDENTITY["commit"],
        "changed_paths": value.get("changed_paths"),
        "q4_guard_import_commit": Q4_GUARD_IMPORT_IDENTITY["commit"],
    }
    expected = _verify_anysolver_policy(input_policy, solver)
    if value != expected:
        raise BindingError("bound ANYsolver guard-only identity differs")
    return expected


def _verify_candidate(name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "commit",
        "root",
        "subject",
        "tree",
        "wheel",
    }:
        raise BindingError(f"{name} candidate fields differ")
    commit = value["commit"]
    tree = value["tree"]
    subject = value["subject"]
    if (
        type(commit) is not str
        or HEX40.fullmatch(commit) is None
        or type(tree) is not str
        or HEX40.fullmatch(tree) is None
        or type(subject) is not str
        or not subject
        or "\n" in subject
        or "\r" in subject
    ):
        raise BindingError(f"{name} Git identity is malformed")
    root = Path(str(value["root"])).resolve(strict=True)
    if not root.is_dir():
        raise BindingError(f"{name} root is not a directory")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise BindingError(f"{name} candidate root is dirty")
    observed = {
        "commit": _git(root, "rev-parse", "HEAD"),
        "tree": _git(root, "rev-parse", "HEAD^{tree}"),
        "subject": _git(root, "show", "-s", "--format=%s", "HEAD"),
    }
    if observed != {"commit": commit, "tree": tree, "subject": subject}:
        raise BindingError(f"{name} candidate Git identity differs")
    wheel = value["wheel"]
    if name in PACKAGED:
        if not isinstance(wheel, dict) or set(wheel) != {
            "bytes",
            "filename",
            "path",
            "sha256",
        }:
            raise BindingError(f"{name} wheel binding is malformed")
        wheel_path = Path(str(wheel["path"])).resolve(strict=True)
        raw = wheel_path.read_bytes()
        if (
            not wheel_path.is_file()
            or wheel_path.is_symlink()
            or wheel_path.name != wheel["filename"]
            or type(wheel["bytes"]) is not int
            or wheel["bytes"] != len(raw)
            or len(raw) <= 0
            or type(wheel["sha256"]) is not str
            or HEX64.fullmatch(wheel["sha256"]) is None
            or hashlib.sha256(raw).hexdigest().upper() != wheel["sha256"]
        ):
            raise BindingError(f"{name} wheel bytes differ")
    elif wheel is not None:
        raise BindingError(f"{name} must not carry a wheel")
    return {
        "commit": commit,
        "root": str(root),
        "subject": subject,
        "tree": tree,
        "wheel": wheel,
    }


def _verify_preflight(
    name: str,
    candidate: Mapping[str, Any],
    value: object,
) -> dict[str, Any]:
    """Verify one canonical clean-tree/test-gate result and all bound logs."""

    if not isinstance(value, dict) or set(value) != {
        "bytes",
        "path",
        "sha256",
    }:
        raise BindingError(f"{name} preflight binding is malformed")
    path = Path(str(value["path"])).resolve(strict=True)
    if not path.is_file() or path.is_symlink():
        raise BindingError(f"{name} preflight is not a regular file")
    raw = path.read_bytes()
    if (
        type(value["bytes"]) is not int
        or value["bytes"] != len(raw)
        or not raw
        or type(value["sha256"]) is not str
        or HEX64.fullmatch(value["sha256"]) is None
        or hashlib.sha256(raw).hexdigest().upper() != value["sha256"]
    ):
        raise BindingError(f"{name} preflight bytes differ")
    record = read_json(path)
    if raw != canonical_bytes(record) or set(record) != {
        "candidate",
        "clean_tree",
        "commit",
        "gates",
        "schema",
        "tree",
    }:
        raise BindingError(f"{name} preflight record differs")
    gates = record["gates"]
    if (
        record["schema"] != PREFLIGHT_SCHEMA
        or record["candidate"] != name
        or record["commit"] != candidate["commit"]
        or record["tree"] != candidate["tree"]
        or record["clean_tree"] is not True
        or not isinstance(gates, list)
        or not gates
    ):
        raise BindingError(f"{name} preflight identity is not green")
    identifiers: list[str] = []
    for gate in gates:
        if not isinstance(gate, dict) or set(gate) != {
            "command",
            "id",
            "log",
            "passed",
            "returncode",
        }:
            raise BindingError(f"{name} preflight gate differs")
        command = gate["command"]
        identifier = gate["id"]
        log = gate["log"]
        if (
            type(identifier) is not str
            or not identifier
            or not isinstance(command, list)
            or not command
            or any(type(item) is not str or not item for item in command)
            or gate["passed"] is not True
            or type(gate["returncode"]) is not int
            or gate["returncode"] != 0
            or not isinstance(log, dict)
            or set(log) != {"bytes", "path", "sha256"}
        ):
            raise BindingError(f"{name} preflight gate is not green")
        log_path = Path(str(log["path"])).resolve(strict=True)
        if not log_path.is_file() or log_path.is_symlink():
            raise BindingError(f"{name} preflight log is not regular")
        log_raw = log_path.read_bytes()
        if (
            type(log["bytes"]) is not int
            or log["bytes"] != len(log_raw)
            or not log_raw
            or type(log["sha256"]) is not str
            or HEX64.fullmatch(log["sha256"]) is None
            or hashlib.sha256(log_raw).hexdigest().upper() != log["sha256"]
        ):
            raise BindingError(f"{name} preflight log differs")
        identifiers.append(identifier)
    if identifiers != list(PREFLIGHT_GATE_IDS[name]):
        raise BindingError(f"{name} preflight gate order or identity differs")
    return {
        "record": record,
        "result": {
            "bytes": len(raw),
            "path": str(path),
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
        },
    }


def build_binding(graph_path: Path) -> dict[str, Any]:
    graph_raw = graph_path.read_bytes()
    graph = read_json(graph_path)
    if graph_raw != canonical_bytes(graph):
        raise BindingError("candidate graph is not canonical JSON")
    if set(graph) != {
        "anysolver_policy",
        "candidates",
        "execution_target",
        "preflight_results",
        "schema",
    }:
        raise BindingError("candidate graph fields differ")
    if graph["schema"] != GRAPH_SCHEMA:
        raise BindingError("candidate graph schema differs")
    candidates = graph["candidates"]
    if not isinstance(candidates, dict) or tuple(candidates) != CANDIDATES:
        raise BindingError("candidate order or membership differs")
    verified_candidates = {
        name: _verify_candidate(name, candidates[name]) for name in CANDIDATES
    }
    preflight = graph["preflight_results"]
    if not isinstance(preflight, dict) or tuple(preflight) != CANDIDATES:
        raise BindingError("candidate preflight membership or order differs")
    verified_preflight = {
        name: _verify_preflight(name, verified_candidates[name], preflight[name])
        for name in CANDIDATES
    }
    target = Path(str(graph["execution_target"])).resolve(strict=True)
    if not target.is_dir():
        raise BindingError("isolated execution target is not a directory")
    files = {
        "binding_generator": _file_binding(BINDING_GENERATOR),
        "contract": _file_binding(CONTRACT),
        "coordinator": _file_binding(COORDINATOR),
        "formal_runner": _file_binding(FORMAL_RUNNER),
        "formal_test": _file_binding(FORMAL_TEST),
        "manifest": _file_binding(MANIFEST),
        "optimization_evidence": _file_binding(OPTIMIZATION_EVIDENCE),
        "successor": _file_binding(SUCCESSOR),
        "test": _file_binding(TEST),
    }
    solver = verified_candidates["ANYsolver"]
    policy = _verify_anysolver_policy(graph["anysolver_policy"], solver)
    return {
        "anysolver_policy": policy,
        "candidate_graph": {
            "bytes": len(graph_raw),
            "sha256": hashlib.sha256(graph_raw).hexdigest().upper(),
        },
        "candidate_preflight": verified_preflight,
        "candidates": verified_candidates,
        "execution_target": str(target),
        "files": files,
        "formal_execution_authorized": False,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-graph", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        value = build_binding(args.candidate_graph)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(canonical_bytes(value))
        return 0
    except (BindingError, OSError, subprocess.SubprocessError) as exc:
        print(f"candidate binding blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
