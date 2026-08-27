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
    policy = graph["anysolver_policy"]
    if not isinstance(policy, dict) or set(policy) != {
        "base_commit",
        "changed_paths",
        "q4_mechanics_git_blob",
    }:
        raise BindingError("ANYsolver policy fields differ")
    base_commit = policy["base_commit"]
    changed_paths = policy["changed_paths"]
    q4_blob = policy["q4_mechanics_git_blob"]
    solver = verified_candidates["ANYsolver"]
    solver_root = Path(str(solver["root"])).resolve(strict=True)
    if (
        type(base_commit) is not str
        or HEX40.fullmatch(base_commit) is None
        or type(q4_blob) is not str
        or HEX40.fullmatch(q4_blob) is None
        or not isinstance(changed_paths, list)
        or any(type(path) is not str or not path for path in changed_paths)
        or changed_paths != sorted(set(changed_paths))
    ):
        raise BindingError("ANYsolver policy is malformed")
    observed_paths = _git(
        solver_root,
        "diff",
        "--name-only",
        base_commit,
        str(solver["commit"]),
    ).splitlines()
    observed_q4 = _git(
        solver_root,
        "rev-parse",
        f"{solver['commit']}:src/anysolver/e4_pl_element.py",
    )
    if observed_paths != changed_paths or observed_q4 != q4_blob:
        raise BindingError("ANYsolver changed paths or Q4 mechanics differ")
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
