"""Run one exact-target S3 activation candidate preflight exactly once.

This is a nonclassifying gate runner.  It uses the hash-bound installed target,
an explicit pytest configuration, isolated Python startup, and the candidate
root recorded by the final graph.  It never retries a failed gate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "prepare_e4_pl_s3_qualification_v4_input.py"
MEMORY_LIMIT_BYTES = 24 * (1 << 30)
INACTIVITY_SECONDS = 1800
POLL_SECONDS = 0.1
TREE_RELEASE_ENVIRONMENT = "ANYSOLVER_S3_PREFLIGHT_TREE_RELEASE"
TREE_RELEASE_BYTES = b"ANYSOLVER_S3_PREFLIGHT_TREE_ACCOUNTED_V1\n"
TREE_RELEASE_PROTOCOL = "ATTACH_BEFORE_GATE_RELEASE_V1"


class PreflightError(RuntimeError):
    """The requested preflight was malformed or changed frozen inputs."""


def _load_generator() -> Any:
    resolved = GENERATOR.resolve(strict=True)
    if not resolved.is_file() or resolved.is_symlink():
        raise PreflightError("candidate binding generator is not a regular file")
    spec = importlib.util.spec_from_file_location("_s3_preflight_v4_generator", resolved)
    if spec is None or spec.loader is None:
        raise PreflightError("candidate binding generator is not loadable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_controller(generator: Any) -> Any:
    resolved = Path(generator.COORDINATOR).resolve(strict=True)
    if not resolved.is_file() or resolved.is_symlink():
        raise PreflightError("process-tree controller is not a regular file")
    spec = importlib.util.spec_from_file_location("_s3_preflight_v4_controller", resolved)
    if spec is None or spec.loader is None:
        raise PreflightError("process-tree controller is not loadable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _directory_activity(path: Path) -> tuple[int, int, int]:
    count = size = newest = 0
    try:
        rows = tuple(path.rglob("*"))
    except OSError:
        return 0, 0, 0
    for row in rows:
        try:
            status = row.stat()
        except OSError:
            continue
        if row.is_file():
            count += 1
            size += int(status.st_size)
            newest = max(newest, int(status.st_mtime_ns))
    return count, size, newest


def _run_controlled(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
    activity_root: Path,
    controller_module: Any,
) -> tuple[int, dict[str, object]]:
    started = time.monotonic()
    peak = 0
    inactive_since = started
    reason = "completed"
    descendants_observed = False
    signals_observed: set[str] = set()
    release = stdout_path.with_name(f".{stdout_path.name}.tree-accounting.release")
    child_environment = dict(environment)
    child_environment.pop(TREE_RELEASE_ENVIRONMENT, None)
    child_environment[TREE_RELEASE_ENVIRONMENT] = str(release.resolve())
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        stdout.write(f"BOUND_EXECUTION_TARGET={environment['PYTHONPATH']}\n".encode())
        stdout.flush()
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=child_environment,
            stdout=stdout,
            stderr=stderr,
            creationflags=(
                int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
                if os.name == "nt"
                else 0
            ),
        )
        controller = None
        try:
            try:
                controller = controller_module._attach_tree_controller(
                    process, MEMORY_LIMIT_BYTES
                )
            except (OSError, RuntimeError):
                reason = "memory-accounting-unavailable"
                controller_module._terminate_tree(
                    process,
                    None,
                    deadline_ns=time.monotonic_ns() + 2_000_000_000,
                )
            else:
                try:
                    with release.open("xb") as stream:
                        stream.write(TREE_RELEASE_BYTES)
                        stream.flush()
                        os.fsync(stream.fileno())
                except OSError:
                    reason = "tree-release-failed"
                    controller_module._terminate_tree(
                        process,
                        controller,
                        deadline_ns=time.monotonic_ns() + 2_000_000_000,
                    )
                else:
                    previous = None
                    while True:
                        tree_peak, active, cpu = controller.sample_activity()
                        descendants_observed = descendants_observed or active > 1
                        peak = max(peak, int(tree_peak))
                        token = (
                            cpu,
                            int(active),
                            controller_module._file_activity(stdout_path),
                            controller_module._file_activity(stderr_path),
                            _directory_activity(activity_root),
                        )
                        now = time.monotonic()
                        if previous is None or token != previous:
                            if previous is not None:
                                for index, label in enumerate(
                                    (
                                        "cpu",
                                        "active-processes",
                                        "stdout",
                                        "stderr",
                                        "files",
                                    )
                                ):
                                    if token[index] != previous[index]:
                                        signals_observed.add(label)
                            inactive_since = now
                            previous = token
                        if peak >= MEMORY_LIMIT_BYTES:
                            reason = "memory-limit"
                            controller_module._terminate_tree(
                                process,
                                controller,
                                deadline_ns=time.monotonic_ns() + 2_000_000_000,
                            )
                            break
                        if now - inactive_since >= INACTIVITY_SECONDS:
                            reason = "no-progress"
                            controller_module._terminate_tree(
                                process,
                                controller,
                                deadline_ns=time.monotonic_ns() + 2_000_000_000,
                            )
                            break
                        if process.poll() is not None and active == 0:
                            break
                        time.sleep(POLL_SECONDS)
            returncode = int(process.wait())
        finally:
            if controller is not None:
                controller.close()
            try:
                release.unlink()
            except FileNotFoundError:
                pass
            stdout.flush()
            stderr.flush()
            os.fsync(stdout.fileno())
            os.fsync(stderr.fileno())
    return returncode, {
        "active_descendants_observed": descendants_observed,
        "inactivity_seconds": INACTIVITY_SECONDS,
        "memory_limit_bytes": MEMORY_LIMIT_BYTES,
        "peak_tree_memory_bytes": peak,
        "progress_signals_observed": sorted(signals_observed),
        "terminal": reason,
        "tree_accounting_release": TREE_RELEASE_PROTOCOL,
    }


def _binding(path: Path) -> dict[str, object]:
    resolved = path.resolve(strict=True)
    raw = resolved.read_bytes()
    return {
        "bytes": len(raw),
        "path": str(resolved),
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
    }


def _process_environment(generator: Any) -> dict[str, str]:
    controlled_names = {
        environment_name
        for mapping in generator.CANDIDATE_GATE_ROOT_ENVIRONMENTS.values()
        for environment_name in mapping
    }
    if controlled_names & set(os.environ):
        raise PreflightError("preflight dependency roots must not be inherited")
    discovered = shutil.which("git")
    if discovered is None:
        raise PreflightError("Git launcher is unavailable")
    launcher = Path(discovered).resolve(strict=True)
    provisional = generator._closed_process_environment(launcher, launcher)
    exec_path = generator._git_probe(launcher, ("--exec-path",), provisional)
    engine = generator._git_engine_from_exec_path(launcher, exec_path)
    return generator._closed_process_environment(launcher, engine)


def _identity(generator: Any, root: Path) -> tuple[str, str]:
    return (
        generator._git(root, "rev-parse", "HEAD"),
        generator._git(root, "rev-parse", "HEAD^{tree}"),
    )


def _requested_dependency_roots(
    candidate: str,
    values: Sequence[str],
    expected_dependencies: set[str],
) -> dict[str, Path]:
    supplied: dict[str, Path] = {}
    for value in values:
        name, separator, raw_path = value.partition("=")
        if (
            separator != "="
            or not name
            or not raw_path
            or name in supplied
        ):
            raise PreflightError("preflight dependency-root argument is malformed")
        supplied[name] = Path(raw_path)
    if set(supplied) != expected_dependencies:
        raise PreflightError(f"{candidate} preflight dependency roots differ")
    return supplied


def _dependency_candidate_bindings(
    generator: Any,
    dependency_roots: dict[str, Path],
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for name, supplied_root in sorted(dependency_roots.items()):
        root = Path(supplied_root).resolve(strict=True)
        commit, tree = _identity(generator, root)
        result[name] = {
            "commit": commit,
            "root": str(root),
            "subject": generator._git(root, "show", "-s", "--format=%s", "HEAD"),
            "tree": tree,
            "working_tree": generator._closed_worktree_binding(root),
        }
    return result


def _write_exclusive(path: Path, value: object, generator: Any) -> None:
    with path.open("xb") as stream:
        stream.write(generator.canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def run(args: argparse.Namespace) -> int:
    generator = _load_generator()
    controller_module = _load_controller(generator)
    if (
        generator.PREFLIGHT_TREE_RELEASE_ENVIRONMENT != TREE_RELEASE_ENVIRONMENT
        or generator.PREFLIGHT_TREE_RELEASE_BYTES != TREE_RELEASE_BYTES
    ):
        raise PreflightError("preflight tree-release binding differs")
    name = str(args.candidate)
    if name not in generator.CANDIDATES:
        raise PreflightError("unknown candidate")
    dependency_roots = _requested_dependency_roots(
        name,
        args.dependency_root,
        set(
            generator.CANDIDATE_GATE_ROOT_ENVIRONMENTS.get(name, {}).values()
        ),
    )
    root = Path(args.root).resolve(strict=True)
    target = Path(args.execution_target).resolve(strict=True)
    output = Path(args.output_directory).resolve()
    output.mkdir(parents=False, exist_ok=False)
    if not target.is_dir() or target.is_symlink():
        raise PreflightError("execution target is not a regular directory")
    if _identity(generator, root) != (args.commit, args.tree):
        raise PreflightError("candidate Git identity differs")
    checkout_before = generator._closed_worktree_binding(root)
    dependency_candidates_before = _dependency_candidate_bindings(
        generator,
        dependency_roots,
    )

    process_environment = _process_environment(generator)
    runtime = {
        "process_environment": process_environment,
        "python": {
            **generator._tool_record(
                Path(sys.executable), label="preflight Python executable"
            ),
            "version": sys.version,
        },
    }
    environment = generator._preflight_environment(
        runtime,
        target,
        name,
        dependency_roots,
    )
    gates: list[dict[str, object]] = []
    passed = True
    for identifier in generator.PREFLIGHT_GATE_IDS[name]:
        command = generator._preflight_command(
            name,
            identifier,
            root,
            target,
            runtime,
            output,
        )
        log_path = output / f"{name}-{identifier}.log"
        stderr_path = output / f"{name}-{identifier}.stderr.log"
        returncode, control = _run_controlled(
            command,
            cwd=root,
            environment=environment,
            stdout_path=log_path,
            stderr_path=stderr_path,
            activity_root=output,
            controller_module=controller_module,
        )
        gate_passed = returncode == 0 and control["terminal"] == "completed"
        gates.append(
            {
                "command": command,
                "environment": environment,
                "id": identifier,
                "log": _binding(log_path),
                "stderr_log": _binding(stderr_path),
                "controller": control,
                "passed": gate_passed,
                "returncode": returncode,
                "working_directory": str(root),
            }
        )
        if not gate_passed:
            passed = False
            break

    final_identity = _identity(generator, root)
    checkout_after: dict[str, object] | None = None
    try:
        checkout_after = generator._closed_worktree_binding(root)
    except generator.BindingError:
        checkout_after = None
    dependency_candidates_after: dict[str, dict[str, object]] | None = None
    try:
        dependency_candidates_after = _dependency_candidate_bindings(
            generator,
            dependency_roots,
        )
    except (generator.BindingError, OSError, subprocess.SubprocessError):
        dependency_candidates_after = None
    record = {
        "candidate": name,
        "checkout_after": checkout_after,
        "checkout_before": checkout_before,
        "clean_tree": (
            checkout_after == checkout_before
            and final_identity == (args.commit, args.tree)
        ),
        "commit": final_identity[0],
        "dependency_candidates_after": dependency_candidates_after,
        "dependency_candidates_before": dependency_candidates_before,
        "dependency_roots_clean": (
            dependency_candidates_after == dependency_candidates_before
        ),
        "execution_target": generator._preflight_target_identity(target),
        "gates": gates,
        "generated_products": [],
        "preflight_config": generator._file_binding(generator.PREFLIGHT_CONFIG),
        "preflight_runner": generator._file_binding(generator.PREFLIGHT_RUNNER),
        "python_runtime": generator._preflight_python_identity(runtime),
        "schema": generator.PREFLIGHT_SCHEMA,
        "tree": final_identity[1],
    }
    result_path = output / f"{name}-preflight.json"
    _write_exclusive(result_path, record, generator)
    print(json.dumps(_binding(result_path), separators=(",", ":"), sort_keys=True))
    return 0 if passed and record["clean_tree"] and record["dependency_roots_clean"] else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--execution-target", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument(
        "--dependency-root",
        action="append",
        default=[],
        metavar="CANDIDATE=PATH",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    return run(_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
