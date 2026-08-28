"""Focused exact-wheel installed-target authority checks for S3 v3."""

from __future__ import annotations

import base64
import copy
import csv
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "prepare_e4_pl_s3_qualification_v3_input.py"
SUCCESSOR = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_qualification_optimization_v3.py"
)
CROSS_WHEEL = ROOT / "tests" / "test_e4_pl_s3_cross_wheel_v3.py"


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _record_hash(raw: bytes) -> str:
    value = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b"=")
    return "sha256=" + value.decode("ascii")


def _record_bytes(files: dict[str, bytes], record_path: str) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    for path in sorted(files):
        raw = files[path]
        writer.writerow((path, _record_hash(raw), str(len(raw))))
    writer.writerow((record_path, "", ""))
    return stream.getvalue().encode("utf-8")


def _normalized(value: str) -> str:
    return value.lower().replace("-", "_").replace(".", "_")


def _make_wheel_and_install(
    directory: Path,
    target: Path,
    candidate_name: str,
    distribution: str,
    version: str,
    import_name: str,
) -> dict[str, Any]:
    dist_info = f"{_normalized(distribution)}-{version}.dist-info"
    record_path = f"{dist_info}/RECORD"
    files = {
        f"{import_name}/__init__.py": (
            f"__version__ = {version!r}\nCANDIDATE = {candidate_name!r}\n"
        ).encode("utf-8"),
        f"{dist_info}/METADATA": (
            "Metadata-Version: 2.3\n"
            f"Name: {distribution}\n"
            f"Version: {version}\n\n"
        ).encode("utf-8"),
        f"{dist_info}/WHEEL": (
            "Wheel-Version: 1.0\nGenerator: exact-target-test\n"
            "Root-Is-Purelib: true\nTag: py3-none-any\n"
        ).encode("utf-8"),
    }
    record = _record_bytes(files, record_path)
    wheel_files = {**files, record_path: record}
    wheel_path = directory / f"{_normalized(distribution)}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(wheel_files):
            archive.writestr(path, wheel_files[path])
    for path, raw in wheel_files.items():
        installed = target / Path(path)
        installed.parent.mkdir(parents=True, exist_ok=True)
        installed.write_bytes(raw)
    wheel_raw = wheel_path.read_bytes()
    return {
        "bytes": len(wheel_raw),
        "filename": wheel_path.name,
        "path": str(wheel_path),
        "sha256": hashlib.sha256(wheel_raw).hexdigest().upper(),
    }


def _installed_graph(generator: Any, tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    wheels = tmp_path / "wheels"
    target = tmp_path / "target"
    wheels.mkdir()
    target.mkdir()
    candidates: dict[str, Any] = {}
    for name, (distribution, version, import_name) in sorted(
        generator.PACKAGED_IDENTITIES.items()
    ):
        candidates[name] = {
            "wheel": _make_wheel_and_install(
                wheels,
                target,
                name,
                distribution,
                version,
                import_name,
            )
        }
    return target, candidates


def _rewrite_installed_record(target: Path, dist_info: str, changed: str) -> None:
    record_path = target / dist_info / "RECORD"
    rows = list(csv.reader(io.StringIO(record_path.read_text(encoding="utf-8"))))
    changed_raw = (target / changed).read_bytes()
    for row in rows:
        if row[0] == changed:
            row[1] = _record_hash(changed_raw)
            row[2] = str(len(changed_raw))
            break
    stream = io.StringIO(newline="")
    csv.writer(stream, lineterminator="\n").writerows(rows)
    record_path.write_text(stream.getvalue(), encoding="utf-8", newline="")


def test_exact_wheel_records_bind_one_closed_installed_target(tmp_path: Path) -> None:
    generator = _load("_s3_v3_exact_target_green", GENERATOR)
    target, candidates = _installed_graph(generator, tmp_path)
    bound = generator._bind_installed_target(target, candidates)
    assert generator._verify_bound_installed_target(target, bound) == bound
    inventories = {
        (
            row["wheel"]["installed_target"]["closed_target"]["directory_count"],
            row["wheel"]["installed_target"]["closed_target"]["directories_sha256"],
            row["wheel"]["installed_target"]["closed_target"]["file_count"],
            row["wheel"]["installed_target"]["closed_target"]["rows_sha256"],
        )
        for row in bound.values()
    }
    assert len(inventories) == 1
    directory_count, directories_sha256, file_count, rows_sha256 = inventories.pop()
    assert directory_count == 7 * 2
    assert len(directories_sha256) == 64
    assert file_count == 7 * 4
    assert len(rows_sha256) == 64
    for name, row in bound.items():
        installed = row["wheel"]["installed_target"]
        assert installed["wheel_sha256"] == row["wheel"]["sha256"]
        assert installed["distribution"] == generator.PACKAGED_IDENTITIES[name][0]
        assert installed["version"] == generator.PACKAGED_IDENTITIES[name][1]
        assert installed["import_name"] == generator.PACKAGED_IDENTITIES[name][2]
        assert {item["provenance"] for item in installed["files"]} == {
            "TARGET_RECORD",
            "WHEEL_RECORD",
        }


def test_same_version_target_substitute_fails_exact_wheel_content(
    tmp_path: Path,
) -> None:
    generator = _load("_s3_v3_exact_target_substitute", GENERATOR)
    target, candidates = _installed_graph(generator, tmp_path)
    changed = "anysolver/__init__.py"
    (target / changed).write_bytes(b"__version__ = '0.4.0'\nSUBSTITUTE = True\n")
    _rewrite_installed_record(target, "anysolver-0.4.0.dist-info", changed)
    with pytest.raises(generator.BindingError, match="differs from exact wheel"):
        generator._bind_installed_target(target, candidates)


@pytest.mark.parametrize("name", ("sitecustomize.py", "usercustomize.py"))
def test_python_startup_customization_is_rejected(
    tmp_path: Path,
    name: str,
) -> None:
    generator = _load(f"_s3_v3_exact_target_{name}", GENERATOR)
    target, candidates = _installed_graph(generator, tmp_path)
    (target / name).write_text("raise RuntimeError('startup injection')\n", encoding="utf-8")
    with pytest.raises(generator.BindingError, match="forbidden customization"):
        generator._bind_installed_target(target, candidates)


def test_unregistered_file_and_late_target_mutation_fail_closed(tmp_path: Path) -> None:
    generator = _load("_s3_v3_exact_target_unregistered", GENERATOR)
    target, candidates = _installed_graph(generator, tmp_path)
    bound = generator._bind_installed_target(target, candidates)
    (target / "unregistered.txt").write_text("not wheel-owned\n", encoding="utf-8")
    with pytest.raises(generator.BindingError, match="unregistered files"):
        generator._bind_installed_target(target, candidates)
    with pytest.raises(generator.BindingError, match="inventory differs"):
        generator._reverify_one_installed_target(
            "ANYsolver",
            {
                key: value
                for key, value in bound["ANYsolver"]["wheel"].items()
                if key != "installed_target"
            },
            bound["ANYsolver"]["wheel"]["installed_target"],
        )


def test_unregistered_empty_directory_and_late_mutation_fail_closed(
    tmp_path: Path,
) -> None:
    generator = _load("_s3_v3_exact_target_unregistered_directory", GENERATOR)
    target, candidates = _installed_graph(generator, tmp_path)
    bound = generator._bind_installed_target(target, candidates)
    (target / "unregistered_namespace").mkdir()
    with pytest.raises(generator.BindingError, match="unregistered directories"):
        generator._bind_installed_target(target, candidates)
    with pytest.raises(generator.BindingError, match="inventory differs"):
        generator._reverify_one_installed_target(
            "ANYsolver",
            {
                key: value
                for key, value in bound["ANYsolver"]["wheel"].items()
                if key != "installed_target"
            },
            bound["ANYsolver"]["wheel"]["installed_target"],
        )


def test_isolated_runtime_distributions_are_record_bound_and_reverified(
    tmp_path: Path,
) -> None:
    generator = _load("_s3_v3_exact_runtime_environment", GENERATOR)
    target, candidates = _installed_graph(generator, tmp_path)
    wheels = tmp_path / "runtime-wheels"
    wheels.mkdir()
    for distribution, version in (
        ("numpy", "2.4.3"),
        ("psutil", "7.2.2"),
        ("pytest", "9.0.1"),
        ("scipy", "1.16.3"),
    ):
        _make_wheel_and_install(
            wheels,
            target,
            f"runtime-{distribution}",
            distribution,
            version,
            distribution,
        )
    bound, runtime = generator._bind_execution_target(target, candidates)
    assert generator._verify_bound_execution_target(target, bound, runtime) == bound
    assert {row["normalized_name"] for row in runtime["distributions"]} == {
        "numpy",
        "psutil",
        "pytest",
        "scipy",
    }
    assert runtime["python"]["path"] == str(Path(sys.executable).resolve())
    assert runtime["python"]["file_count"] > 0
    assert runtime["python"]["isolated_probe"]["bytes"] > 0
    assert runtime["python"]["runtime_surface"] == (
        "EXECUTABLE_DLL_STDLIB_AND_BASE_ROOT_IMPORT_SURFACE"
    )
    assert runtime["schema"] == "anysolver.e4-pl-s3-isolated-runtime-environment-v2"
    process_environment = runtime["process_environment"]
    assert process_environment["GIT_NO_LAZY_FETCH"] == "1"
    assert process_environment["GIT_CONFIG_COUNT"] == str(
        len(generator.GIT_BOUND_CONFIG_OVERRIDES)
    )
    assert tuple(
        (
            process_environment[f"GIT_CONFIG_KEY_{index}"],
            process_environment[f"GIT_CONFIG_VALUE_{index}"],
        )
        for index in range(len(generator.GIT_BOUND_CONFIG_OVERRIDES))
    ) == generator.GIT_BOUND_CONFIG_OVERRIDES
    assert generator._activate_bound_runtime_environment(runtime) == Path(
        runtime["git"]["launcher"]["path"]
    )
    changed_environment = copy.deepcopy(runtime)
    changed_environment["process_environment"]["UNBOUND_CONTROL"] = "1"
    with pytest.raises(generator.BindingError, match="isolated execution environment"):
        generator._verify_bound_execution_target(target, bound, changed_environment)
    changed_stdlib = copy.deepcopy(runtime)
    changed_stdlib["python"]["rows_sha256"] = "0" * 64
    with pytest.raises(generator.BindingError, match="bound isolated execution"):
        generator._verify_bound_execution_target(target, bound, changed_stdlib)
    changed_git = copy.deepcopy(runtime)
    changed_git["git"]["launcher"]["sha256"] = "0" * 64
    with pytest.raises(generator.BindingError, match="Git launcher identity"):
        generator._activate_bound_runtime_environment(changed_git)
    (target / "numpy" / "__init__.py").write_text(
        "__version__ = 'mutated'\n",
        encoding="utf-8",
    )
    with pytest.raises(generator.BindingError, match="runtime RECORD hash"):
        generator._verify_bound_execution_target(target, bound, runtime)


def test_candidate_checkout_rejects_ignored_or_extra_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = _load("_s3_v3_closed_candidate_checkout", GENERATOR)
    root = tmp_path / "candidate"
    root.mkdir()
    (root / ".git").mkdir()
    tracked = root / "tracked.py"
    tracked.write_text("VALUE = 1\n", encoding="utf-8")

    def fake_git(_root: Path, *arguments: str) -> str:
        if arguments[0] == "config":
            return ""
        if arguments[:3] == ("rev-parse", "--git-path", "info/attributes"):
            return str(root / ".git" / "info" / "attributes")
        assert "ls-files" in arguments
        if "-v" in arguments:
            return "H tracked.py\0"
        if "--stage" in arguments:
            return f"100644 {'A' * 40} 0\ttracked.py\0"
        return "tracked.py\0"

    monkeypatch.setattr(generator, "_git", fake_git)
    monkeypatch.setattr(
        generator,
        "_git_hash_worktree",
        lambda _root, paths: ["A" * 40 for _path in paths],
    )
    real_fake_git = generator._git

    def fake_git_with_tree(_root: Path, *arguments: str) -> str:
        if arguments[0] == "ls-tree":
            return f"100644 blob {'A' * 40}\ttracked.py\0"
        return real_fake_git(_root, *arguments)

    monkeypatch.setattr(generator, "_git", fake_git_with_tree)
    first = generator._closed_worktree_binding(root)
    assert first["file_count"] == 1
    (root / "ignored.pyc").write_bytes(b"ignored")
    with pytest.raises(generator.BindingError, match="ignored, untracked"):
        generator._closed_worktree_binding(root)
    (root / "ignored.pyc").unlink()
    tracked.write_text("VALUE = 2\n", encoding="utf-8")
    second = generator._closed_worktree_binding(root)
    assert second["rows_sha256"] != first["rows_sha256"]


def test_candidate_checkout_rejects_filter_routes_and_index_flags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = _load("_s3_v3_closed_candidate_git_controls", GENERATOR)
    root = tmp_path / "candidate"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "tracked.py").write_text("VALUE = 1\n", encoding="utf-8")

    def filtered_git(_root: Path, *arguments: str) -> str:
        if arguments[0] == "config":
            return "local\0filter.hidden.clean\nhelper-command\0"
        raise AssertionError("Git status must not run after a filter is detected")

    monkeypatch.setattr(generator, "_git", filtered_git)
    with pytest.raises(generator.BindingError, match="executable override"):
        generator._closed_worktree_binding(root)

    def flagged_git(_root: Path, *arguments: str) -> str:
        if arguments[0] == "config":
            return ""
        if arguments[:3] == ("rev-parse", "--git-path", "info/attributes"):
            return str(root / ".git" / "info" / "attributes")
        if "-v" in arguments:
            return "S tracked.py\0"
        if arguments[0] == "ls-tree":
            return f"100644 blob {'A' * 40}\ttracked.py\0"
        if "--stage" in arguments:
            return f"100644 {'A' * 40} 0\ttracked.py\0"
        return "tracked.py\0"

    monkeypatch.setattr(generator, "_git", flagged_git)
    with pytest.raises(generator.BindingError, match="index flags"):
        generator._closed_worktree_binding(root)


@pytest.mark.parametrize(
    ("scope", "key"),
    (
        ("local", "core.fsmonitor"),
        ("worktree", "core.fsmonitorHookVersion"),
        ("local", "core.commitGraph"),
        ("worktree", "commitGraph.generationVersion"),
        ("local", "extensions.partialClone"),
        ("worktree", "remote.origin.promisor"),
        ("local", "remote.origin.partialCloneFilter"),
        ("local", "log.showSignature"),
        ("worktree", "gpg.ssh.program"),
    ),
)
def test_candidate_checkout_rejects_bound_git_execution_controls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scope: str,
    key: str,
) -> None:
    generator = _load(f"_s3_v3_reject_{scope}_{key}", GENERATOR)
    root = tmp_path / "candidate"
    root.mkdir()
    calls: list[tuple[str, ...]] = []

    def configured_git(_root: Path, *arguments: str) -> str:
        calls.append(arguments)
        if arguments == ("config", "--show-scope", "--null", "--list"):
            return f"{scope}\0{key}\nconfigured-value\0"
        raise AssertionError("no repository operation may follow a rejected Git control")

    monkeypatch.setattr(generator, "_git", configured_git)
    with pytest.raises(generator.BindingError, match="executable override"):
        generator._closed_worktree_binding(root)
    assert calls == [("config", "--show-scope", "--null", "--list")]


def test_candidate_authority_rejects_fsmonitor_before_sentinel_hook_runs(
    tmp_path: Path,
) -> None:
    generator = _load("_s3_v3_fsmonitor_sentinel", GENERATOR)
    root = tmp_path / "candidate"
    sentinel = tmp_path / "fsmonitor-ran"
    hook = tmp_path / (
        "fsmonitor-sentinel.cmd" if os.name == "nt" else "fsmonitor-sentinel"
    )
    if os.name == "nt":
        hook.write_text(
            "@echo off\r\ntype nul > \"%~dp0fsmonitor-ran\"\r\nexit /b 0\r\n",
            encoding="utf-8",
        )
    else:
        hook.write_text(
            "#!/bin/sh\ntouch \"$(dirname \"$0\")/fsmonitor-ran\"\nexit 0\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)
    subprocess.run(
        ["git", "init", "--quiet", str(root)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "--local", "core.fsmonitor", str(hook)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "config",
            "--local",
            "core.fsmonitorHookVersion",
            "2",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert not sentinel.exists()

    with pytest.raises(generator.BindingError, match="executable override"):
        generator._verify_candidate(
            "ANYintelligent",
            {
                "commit": "a" * 40,
                "root": str(root),
                "subject": "fsmonitor sentinel candidate",
                "tree": "b" * 40,
                "wheel": None,
            },
        )
    assert not sentinel.exists()


def test_candidate_verification_runs_strict_full_fsck_before_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = _load("_s3_v3_strict_fsck", GENERATOR)
    root = tmp_path / "candidate"
    root.mkdir()
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(generator, "_reject_worktree_git_overrides", lambda _root: None)

    def fsck_then_dirty(_root: Path, *arguments: str) -> str:
        calls.append(arguments)
        if arguments == ("fsck", "--full", "--strict"):
            return ""
        if arguments == ("status", "--porcelain=v1", "--untracked-files=all"):
            return "M tracked.py"
        raise AssertionError(f"unexpected Git operation: {arguments}")

    monkeypatch.setattr(generator, "_git", fsck_then_dirty)
    with pytest.raises(generator.BindingError, match="candidate root is dirty"):
        generator._verify_candidate(
            "ANYintelligent",
            {
                "commit": "a" * 40,
                "root": str(root),
                "subject": "strict fsck candidate",
                "tree": "b" * 40,
                "wheel": None,
            },
        )
    assert calls == [
        ("fsck", "--full", "--strict"),
        ("status", "--porcelain=v1", "--untracked-files=all"),
    ]

    calls.clear()

    def rejected_fsck(_root: Path, *arguments: str) -> str:
        calls.append(arguments)
        raise generator.BindingError("strict object validation failed")

    monkeypatch.setattr(generator, "_git", rejected_fsck)
    with pytest.raises(generator.BindingError, match="strict object validation failed"):
        generator._verify_candidate(
            "ANYintelligent",
            {
                "commit": "a" * 40,
                "root": str(root),
                "subject": "rejected strict fsck candidate",
                "tree": "b" * 40,
                "wheel": None,
            },
        )
    assert calls == [("fsck", "--full", "--strict")]


def test_git_loadable_surface_detects_added_or_mutated_files(tmp_path: Path) -> None:
    generator = _load("_s3_v3_git_loadable_surface", GENERATOR)
    launcher_root = tmp_path / "cmd"
    engine_root = tmp_path / "bin"
    launcher_root.mkdir()
    engine_root.mkdir()
    launcher = launcher_root / "git.exe"
    engine = engine_root / "git.exe"
    launcher.write_bytes(b"launcher")
    engine.write_bytes(b"engine")
    dll = engine_root / "runtime.dll"
    dll.write_bytes(b"one")
    first = generator._git_loadable_surface(launcher, engine)
    dll.write_bytes(b"two")
    second = generator._git_loadable_surface(launcher, engine)
    assert second["rows_sha256"] != first["rows_sha256"]
    (engine_root / "extra.dll").write_bytes(b"extra")
    third = generator._git_loadable_surface(launcher, engine)
    assert third["file_count"] == second["file_count"] + 1


def test_bound_inventory_and_record_mutations_are_rejected(tmp_path: Path) -> None:
    generator = _load("_s3_v3_exact_target_binding_mutation", GENERATOR)
    target, candidates = _installed_graph(generator, tmp_path)
    bound = generator._bind_installed_target(target, candidates)
    bound["ANYsolver"]["wheel"]["installed_target"]["files_sha256"] = "0" * 64
    with pytest.raises(generator.BindingError, match="bound installed target"):
        generator._verify_bound_installed_target(target, bound)


def test_successor_and_cross_wheel_validate_before_candidate_imports() -> None:
    successor = SUCCESSOR.read_text(encoding="utf-8")
    cross_wheel = CROSS_WHEEL.read_text(encoding="utf-8")
    assert successor.index("_verify_bound_execution_target") < successor.index(
        '__import__("anysolver")'
    )
    assert 'environment = dict(process_environment)' in successor
    assert "os.environ.copy()" not in successor
    assert '"ANYSOLVER_S3_V3_CROSS_WHEEL": "1"' in successor
    assert '"OMP_NUM_THREADS": "1"' in successor
    assert '"-I"' in successor and '"-S"' in successor and '"-B"' in successor
    assert "ANYSOLVER_S3_V3_BINDING" in successor
    assert cross_wheel.index("_verify_bound_target_before_runtime_imports") < (
        cross_wheel.index("import anysolver", cross_wheel.index("def test_exact_wheels"))
    )
    assert "_verify_bound_execution_target" in cross_wheel


def test_generator_binds_indirect_programs_graph_and_nonmechanics_blobs() -> None:
    generator = _load("_s3_v3_exact_target_program_graph", GENERATOR)
    expected_programs = {
        generator.BASE_CONTRACT,
        generator.BASE_INPUT,
        generator.BASE_PROGRAM,
        generator.BASE_TEST,
        generator.BATCH_BENCHMARK,
        generator.MIXED_EIGEN_PERFORMANCE,
        generator.MIXED_MESH_MANIFEST_PROGRAM,
        generator.MIXED_MESH_RUNNER,
        generator.MIXED_MESH_SMOKE_INPUT,
        generator.MIXED_STRUCTURAL_COMMON,
        generator.MIXED_STRUCTURAL_PRODUCER,
        generator.SUCCESSOR,
    }
    assert all(path.is_file() for path in expected_programs)
    source = GENERATOR.read_text(encoding="utf-8")
    assert '"candidate_graph": _file_binding(graph_path)' in source
    for path, expected_blob in generator.Q4_NONMECHANICS_INTEGRATION_PATH_BLOBS:
        observed = subprocess.run(
            ["git", "rev-parse", f"HEAD:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert observed == expected_blob
        assert "bound nonmechanics integration blob differs" in source
