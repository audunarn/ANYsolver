"""Bounded package, parity, and activation-gap audit for S3 V2D."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile
import time
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6v_activation_gap_contract.json"
CHECKER = REFERENCE / "e4_pl_s3_v6v_activation_gap_checker.py"
PROCESS = REFERENCE / "e4_pl_s3_v6s_stage4b.py"
CANDIDATE = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
PASS = "PASS_BOUND_REGISTERED_SCOPE"
FAIL = "FAIL_BOUND_REGISTERED_SCOPE"
BLOCKED = "BLOCKED_E4_PL_S3_V6V_PACKAGE_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V6V_PACKAGE_RESTART_OR_BATCH"
GO = "PROVISIONAL_GO_E4_PL_S3_V6V_FINAL_QUALIFICATION_PREPARATION"
CHILD_TIMEOUT_SECONDS = 600
MEMORY_LIMIT_GIB = 24
FOCUSED_TEST_COUNT = 42
FOCUSED_TESTS = (
    "tests/test_e4_pl_s3_v6c_offset_load_restart.py",
    "tests/test_e4_pl_s3_v6d_activity_contact_batch.py",
    "tests/test_e4_pl_s3_v6e_final_parity.py",
    "tests/test_e4_pl_s3_v6g_recovery_current_eigen.py",
    "tests/test_e4_pl_s3_v6t_global_cache.py",
    "tests/test_e4_pl_s3_v6u_performance.py",
    "tests/test_e4_pl_s3_v6u_performance_closeout.py",
)


def _sibling(name: str) -> Path:
    for base in (ROOT, *ROOT.parents):
        candidate = base / name
        if candidate.is_dir():
            return candidate.resolve()
    raise RuntimeError(f"required sibling repository is absent: {name}")


ANYFILEIO_ROOT = _sibling("ANYfileIO")


class V6VError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise V6VError(f"duplicate key: {key}")
        value[key] = item
    return value


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            V6VError(f"nonfinite token: {token}")
        ),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6VError(f"noncanonical JSON: {path}")
    return raw, value


def _module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise V6VError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _git(*arguments: str) -> str:
    return _git_at(ROOT, *arguments)


def _git_command(repository: Path, *arguments: str) -> list[str]:
    return [
        "git",
        "-c",
        f"safe.directory={repository.as_posix()}",
        *arguments,
    ]


def _git_at(repository: Path, *arguments: str) -> str:
    process = subprocess.run(
        _git_command(repository, *arguments),
        cwd=repository,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode:
        raise V6VError(process.stderr.decode("utf-8", "replace").strip())
    return process.stdout.decode("ascii").strip()


def validate_contract() -> tuple[bytes, dict[str, Any]]:
    raw, value = load(CONTRACT)
    if value.get("schema") != "anysolver.e4-pl-s3-v6v-activation-gap-contract-v1":
        raise V6VError("V6V contract schema differs")
    if value.get("execution") != {
        "automatic_retry": False,
        "child_timeout_seconds": CHILD_TIMEOUT_SECONDS,
        "maximum_concurrency": 2,
        "memory_limit_gib_per_process_tree": MEMORY_LIMIT_GIB,
        "numerical_library_threads_per_process": 1,
    }:
        raise V6VError("V6V execution scope differs")
    if value.get("focused_tests") != list(FOCUSED_TESTS):
        raise V6VError("V6V focused test inventory differs")
    for row in value.get("frozen_inputs", []):
        raw_input = (ROOT / row["path"]).read_bytes()
        if len(raw_input) != row["bytes"] or sha256(raw_input) != row["sha256"]:
            raise V6VError(f"frozen input differs: {row['path']}")
    dependency = value.get("dependency_inputs", {}).get("anyfileio", {})
    dependency_pyproject = (ANYFILEIO_ROOT / "pyproject.toml").read_bytes()
    if (
        _git_at(ANYFILEIO_ROOT, "rev-parse", "HEAD") != dependency.get("commit")
        or _git_at(ANYFILEIO_ROOT, "rev-parse", "HEAD^{tree}")
        != dependency.get("tree")
        or _git_at(ANYFILEIO_ROOT, "status", "--porcelain")
        or dependency.get("pyproject")
        != {"bytes": len(dependency_pyproject), "sha256": sha256(dependency_pyproject)}
    ):
        raise V6VError("ANYfileIO dependency identity differs")
    return raw, value


def validate_authorization(path: Path, contract_raw: bytes) -> None:
    _raw, value = load(path)
    if value.get("schema") != "anysolver.e4-pl-s3-v6v-execution-authorization-v1":
        raise V6VError("V6V authorization schema differs")
    if value.get("execution_authorized") is not True:
        raise V6VError("V6V execution is not authorized")
    if value.get("activation_authorized") is not False:
        raise V6VError("V6V cannot activate S3")
    if value.get("contract_sha256") != sha256(contract_raw):
        raise V6VError("V6V authorization contract differs")
    if _git("rev-parse", "HEAD^") != value.get("authority_commit"):
        raise V6VError("V6V authorization topology differs")
    if _git("show", "-s", "--format=%s", "HEAD") != value.get(
        "expected_authorization_subject"
    ):
        raise V6VError("V6V authorization subject differs")
    if _git("status", "--porcelain"):
        raise V6VError("V6V frozen worktree is dirty")


def _write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def _run_command(
    command: Sequence[str], cwd: Path, prefix: Path, timeout: int = 540
) -> subprocess.CompletedProcess[bytes]:
    process = subprocess.run(
        list(command),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    _write(prefix.with_suffix(".stdout.log"), process.stdout)
    _write(prefix.with_suffix(".stderr.log"), process.stderr)
    return process


def _log_record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": sha256(raw)}


def _is_reparse(path: Path) -> bool:
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def package_worker(output: Path) -> dict[str, Any]:
    work = output.parent
    archive = work / "source.tar"
    source = work / "source"
    wheelhouse = work / "wheelhouse"
    dependency_archive = work / "anyfileio-source.tar"
    dependency_source = work / "anyfileio-source"
    dependency_wheelhouse = work / "anyfileio-wheelhouse"
    target = work / "installed"
    source.mkdir()
    wheelhouse.mkdir()
    dependency_source.mkdir()
    dependency_wheelhouse.mkdir()
    target.mkdir()
    dependency_archive_process = _run_command(
        _git_command(
            ANYFILEIO_ROOT,
            "archive",
            "--format=tar",
            "HEAD",
            "-o",
            str(dependency_archive),
        ),
        ANYFILEIO_ROOT,
        work / "anyfileio-archive",
    )
    if dependency_archive_process.returncode:
        raise V6VError("ANYfileIO git archive failed")
    with tarfile.open(dependency_archive, "r") as stream:
        stream.extractall(dependency_source, filter="data")
    dependency_build = _run_command(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(dependency_wheelhouse),
            str(dependency_source),
        ],
        work,
        work / "anyfileio-build",
    )
    if dependency_build.returncode:
        raise V6VError("ANYfileIO wheel build failed")
    dependency_wheels = sorted(dependency_wheelhouse.glob("*.whl"))
    if len(dependency_wheels) != 1:
        raise V6VError("ANYfileIO wheel count differs")
    dependency_wheel = dependency_wheels[0]
    if (
        not dependency_wheel.is_file()
        or _is_reparse(dependency_wheel)
        or dependency_wheel.stat().st_size <= 0
        or not dependency_wheel.name.lower().startswith("anyfileio-")
    ):
        raise V6VError("ANYfileIO wheel identity differs")
    dependency_install = _run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(target),
            str(dependency_wheel),
        ],
        work,
        work / "anyfileio-install",
    )
    if dependency_install.returncode:
        raise V6VError("ANYfileIO wheel install failed")
    archive_process = _run_command(
        _git_command(ROOT, "archive", "--format=tar", "HEAD", "-o", str(archive)),
        ROOT,
        work / "archive",
    )
    if archive_process.returncode:
        raise V6VError("git archive failed")
    with tarfile.open(archive, "r") as stream:
        stream.extractall(source, filter="data")
    build = _run_command(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(wheelhouse),
            str(source),
        ],
        work,
        work / "build",
    )
    if build.returncode:
        raise V6VError("wheel build failed")
    wheels = sorted(wheelhouse.glob("*.whl"))
    if len(wheels) != 1:
        raise V6VError("wheel count differs")
    wheel = wheels[0]
    if (
        not wheel.is_file()
        or _is_reparse(wheel)
        or wheel.stat().st_size <= 0
        or not wheel.name.lower().startswith("anysolver-")
    ):
        raise V6VError("wheel identity differs")
    install = _run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(target),
            str(wheel),
        ],
        work,
        work / "install",
    )
    if install.returncode:
        raise V6VError("wheel install failed")
    smoke_source = "\n".join(
        (
            "import importlib.metadata as md, json, pathlib, sys",
            "target=pathlib.Path(sys.argv[1]).resolve()",
            "sys.path.insert(0,str(target))",
            "import anyfileio, anysolver",
            "from anysolver import DEFAULT_Q4_FORMULATION, DEFAULT_S3_FORMULATION, create_shell_element, shell_element_from_dict",
            "element=create_shell_element(1,[1,2,3],'steel',formulation='e4-pl-s3-v2d',thickness=0.08,reference_normal=(0.0,0.0,1.0))",
            "payload=element.to_dict()",
            "restored=shell_element_from_dict(payload)",
            "origin=pathlib.Path(anysolver.__file__).resolve()",
            "anyfileio_origin=pathlib.Path(anyfileio.__file__).resolve()",
            "assert origin.is_relative_to(target)",
            "assert anyfileio_origin.is_relative_to(target)",
            "result={'anyfileio_import_from_target':True,'anyfileio_import_origin':str(anyfileio_origin),'class_name':type(element).__name__,'default_q4':DEFAULT_Q4_FORMULATION,'default_s3':DEFAULT_S3_FORMULATION,'formulation_id':payload['formulation_id'],'import_from_target':True,'import_origin':str(origin),'round_trip_exact':restored.to_dict()==payload,'version':anysolver.__version__}",
            "print(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False))",
        )
    )
    smoke = _run_command(
        [sys.executable, "-I", "-c", smoke_source, str(target)],
        work,
        work / "smoke",
    )
    smoke_value: dict[str, Any] | None = None
    if smoke.returncode == 0:
        try:
            smoke_value = json.loads(smoke.stdout, object_pairs_hook=_pairs)
        except (json.JSONDecodeError, UnicodeError, V6VError):
            smoke_value = None
    passed = bool(
        smoke_value
        and smoke_value.get("class_name")
        == "NativeParityE4PLS3V2DShellElement"
        and smoke_value.get("default_q4") == "e4-pl"
        and smoke_value.get("default_s3") == "legacy-s3"
        and smoke_value.get("formulation_id")
        == "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
        and smoke_value.get("import_from_target") is True
        and smoke_value.get("anyfileio_import_from_target") is True
        and smoke_value.get("round_trip_exact") is True
    )
    wheel_raw = wheel.read_bytes()
    record = {
        "candidate_commit": _git("rev-parse", "HEAD"),
        "candidate_tree": _git("rev-parse", "HEAD^{tree}"),
        "dependencies": {
            "anyfileio": {
                "bytes": dependency_wheel.stat().st_size,
                "commit": _git_at(ANYFILEIO_ROOT, "rev-parse", "HEAD"),
                "filename": dependency_wheel.name,
                "sha256": sha256(dependency_wheel.read_bytes()),
                "tree": _git_at(ANYFILEIO_ROOT, "rev-parse", "HEAD^{tree}"),
            }
        },
        "gate_status": PASS if passed else FAIL,
        "logs": {
            f"{name}_{kind}": _log_record(work / f"{name}.{kind}.log")
            for name in (
                "anyfileio-archive",
                "anyfileio-build",
                "anyfileio-install",
                "archive",
                "build",
                "install",
                "smoke",
            )
            for kind in ("stdout", "stderr")
        },
        "schema": "anysolver.e4-pl-s3-v6v-package-record-v1",
        "smoke": smoke_value,
        "wheel": {
            "bytes": len(wheel_raw),
            "filename": wheel.name,
            "regular_file": True,
            "reparse_point": False,
            "sha256": sha256(wheel_raw),
        },
    }
    _write(output, canonical_bytes(record))
    return record


def test_worker(output: Path) -> dict[str, Any]:
    work = output.parent
    command = [
        sys.executable,
        "-m",
        "pytest",
        *FOCUSED_TESTS,
        "-q",
        "--basetemp",
        str(work / "pytest-temp"),
    ]
    process = _run_command(command, ROOT, work / "pytest")
    text = process.stdout.decode("utf-8", "replace")
    matches = [int(value) for value in re.findall(r"(\d+) passed", text)]
    count = matches[-1] if matches else 0
    record = {
        "gate_status": PASS
        if process.returncode == 0 and count == FOCUSED_TEST_COUNT
        else FAIL,
        "schema": "anysolver.e4-pl-s3-v6v-focused-tests-record-v1",
        "stderr": _log_record(work / "pytest.stderr.log"),
        "stdout": _log_record(work / "pytest.stdout.log"),
        "test_count": count,
    }
    _write(output, canonical_bytes(record))
    return record


def run(authorization: Path, output: Path) -> dict[str, Any]:
    contract_raw, contract = validate_contract()
    validate_authorization(authorization, contract_raw)
    if output.exists():
        raise V6VError("exclusive V6V output exists")
    output.mkdir(parents=True)
    process = _module(f"_v6v_process_{time.monotonic_ns()}", PROCESS)
    jobs = (
        (
            "PACKAGE",
            [sys.executable, str(Path(__file__).resolve()), "--package-worker", "--output", str(output / "package" / "record.json")],
            output / "package",
        ),
        (
            "FOCUSED_TESTS",
            [sys.executable, str(Path(__file__).resolve()), "--test-worker", "--output", str(output / "tests" / "record.json")],
            output / "tests",
        ),
    )
    try:
        launched = process._jobs(jobs, 2, time.monotonic() + CHILD_TIMEOUT_SECONDS)
        if any(row[0] != "COMPLETE" for row in launched.values()):
            raise V6VError("V6V worker process failed")
        package_raw, package = load(output / "package" / "record.json")
        test_raw, tests = load(output / "tests" / "record.json")
        passed = package["gate_status"] == PASS and tests["gate_status"] == PASS
        package_witness = package["wheel"]
        common = {
            "activation_authorized": False,
            "candidate_formulation_id": CANDIDATE,
            "focused_test_count": tests["test_count"],
            "gate_status": {
                name: PASS if passed else FAIL
                for name in (
                    "batching",
                    "migration",
                    "package_isolation",
                    "provenance",
                    "restart",
                    "stage4a_spatial",
                    "stage4b",
                )
            },
            "next_gate": "V6W_FINAL_QUALIFICATION_EVIDENCE_COMPOSITION" if passed else None,
            "package": {
                "import_from_target": bool(package.get("smoke") and package["smoke"].get("import_from_target")),
                "record_sha256": sha256(package_raw),
                "round_trip_exact": bool(package.get("smoke") and package["smoke"].get("round_trip_exact")),
                "wheel_bytes": package_witness["bytes"],
                "wheel_filename": package_witness["filename"],
                "wheel_sha256": package_witness["sha256"],
            },
            "predecessor_terminals": contract["predecessor_terminals"],
            "production_boundary": {
                "anymesh_untouched": True,
                "default_q4_formulation": "e4-pl",
                "default_s3_formulation": "legacy-s3",
                "q4_mechanics_unchanged": True,
            },
            "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
            "schema": "anysolver.e4-pl-s3-v6v-activation-gap-common-v1",
            "terminal": GO if passed else NO_GO,
            "test_record_sha256": sha256(test_raw),
        }
        common_raw = canonical_bytes(common)
        _write(output / "common.json", common_raw)
        checks = []
        for replica in (1, 2):
            directory = output / "checkers" / str(replica)
            command = [
                sys.executable,
                str(CHECKER),
                "--verify-v6v-common",
                "--common",
                str(output / "common.json"),
                "--output",
                str(directory / "check.json"),
            ]
            checks.append((f"CHECKER-{replica}", command, directory))
        checked = process._jobs(checks, 2, time.monotonic() + CHILD_TIMEOUT_SECONDS)
        if any(row[0] != "COMPLETE" for row in checked.values()):
            raise V6VError("V6V checker process failed")
        first = (output / "checkers" / "1" / "check.json").read_bytes()
        second = (output / "checkers" / "2" / "check.json").read_bytes()
        if first != second:
            raise V6VError("V6V checker replicas disagree")
        aggregate = {
            "activation_authorized": False,
            "authorization_sha256": sha256(authorization.read_bytes()),
            "checker_replicas_byte_identical": True,
            "common_sha256": sha256(common_raw),
            "error": None,
            "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
            "schema": "anysolver.e4-pl-s3-v6v-activation-gap-aggregate-v1",
            "terminal": common["terminal"],
        }
    except Exception as exc:
        aggregate = {
            "activation_authorized": False,
            "authorization_sha256": sha256(authorization.read_bytes()),
            "checker_replicas_byte_identical": False,
            "common_sha256": None,
            "error": f"{type(exc).__name__}: {exc}",
            "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
            "schema": "anysolver.e4-pl-s3-v6v-activation-gap-aggregate-v1",
            "terminal": BLOCKED,
        }
        _write(output / "failure.txt", (aggregate["error"] + "\n").encode("utf-8"))
    _write(output / "aggregate.json", canonical_bytes(aggregate))
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--package-worker", action="store_true")
    mode.add_argument("--test-worker", action="store_true")
    mode.add_argument("--run-v6v", action="store_true")
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.package_worker:
        if args.authorization is not None:
            raise V6VError("package worker authorization argument forbidden")
        package_worker(args.output)
        return 0
    if args.test_worker:
        if args.authorization is not None:
            raise V6VError("test worker authorization argument forbidden")
        test_worker(args.output)
        return 0
    if args.authorization is None:
        raise V6VError("V6V coordinator requires authorization")
    result = run(args.authorization, args.output)
    print(canonical_bytes(result).decode("ascii"), end="")
    return 0 if result["terminal"] != BLOCKED else 2


if __name__ == "__main__":
    raise SystemExit(main())
