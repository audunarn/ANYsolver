"""Authority and coverage tests for the S3 qualification-v3 successor."""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "scripts" / "run_e4_pl_s3_qualification_v3.py"
GENERATOR = ROOT / "scripts" / "prepare_e4_pl_s3_qualification_v3_input.py"
COLD = ROOT / "scripts" / "benchmark_e4_pl_s3_activation_cold_path.py"
SUCCESSOR = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_qualification_optimization_v3.py"
)
CONTRACT = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_qualification_optimization_v3_contract.json"
)
EVIDENCE = (
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
V2_CONTRACT = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_default_activation_v2_contract.json"
)


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            result.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".", 1)[0])
    return result


def _assignment_authority(formal: Any) -> Any:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    contract = json.loads(V2_CONTRACT.read_text(encoding="utf-8"))
    base_authority = SimpleNamespace(
        contract=contract,
        contract_raw=V2_CONTRACT.read_bytes(),
        manifest=manifest,
    )
    return formal.SuccessorAuthority(
        base=SimpleNamespace(),
        successor=SimpleNamespace(),
        authority=base_authority,
        binding_path=Path("binding.json"),
        binding_raw=b"binding\n",
        binding={"candidates": {}},
        authorization_path=Path("authorization.json"),
        authorization_raw=b"authorization\n",
        authorization={},
    )


def test_v3_coordinators_are_standard_library_and_have_no_elapsed_ceiling() -> None:
    forbidden = {"anysolver", "numpy", "scipy", "sympy", "psutil"}
    assert _top_level_imports(COLD).isdisjoint(forbidden)
    assert _top_level_imports(FORMAL).isdisjoint(forbidden)
    formal_source = FORMAL.read_text(encoding="utf-8")
    contract_source = CONTRACT.read_text(encoding="utf-8")
    for source in (formal_source, contract_source):
        assert "timeout_seconds_per_process" not in source
        assert "total_command_limit_seconds" not in source
        assert "forecast_acceptance_seconds" not in source
    assert "INACTIVITY_SECONDS = 1800" in formal_source
    assert "MEMORY_LIMIT_BYTES = 24 * (1 << 30)" in formal_source
    assert '"total_runtime_limit_seconds": None' in formal_source
    assert '"runtime_classification": False' in formal_source


def test_formal_assignments_cover_exact_252_special_and_batch_scope() -> None:
    formal = _load("_s3_v3_formal_assignment_test", FORMAL)
    authority = _assignment_authority(formal)
    structural = [
        formal.build_assignment(authority, worker)
        for worker in formal.STRUCTURAL_WORKERS
    ]
    rows = [
        item
        for assignment in structural
        for item in assignment["payload"]["manifest_records"]
    ]
    assert [assignment["payload"]["record_count"] for assignment in structural] == [
        84,
        84,
        84,
    ]
    assert len(rows) == 252
    assert len({item["sha256"] for item in rows}) == 252
    assert all(
        item["sha256"]
        == hashlib.sha256(formal.canonical_bytes(item["record"])).hexdigest().upper()
        for item in rows
    )
    eigen = formal.build_assignment(authority, "EIGEN_PERFORMANCE")["payload"]
    assert len(eigen["topology_records"]) == 3
    assert eigen["paired_performance_comparisons"] == 24
    special = formal.build_assignment(authority, "SPECIAL_ECOSYSTEM")["payload"]
    assert special["registered_special_fixtures"] == 8
    assert special["lane_count"] == len(special["lanes"]) > 0
    overlay = special["lanes"][-3:]
    assert overlay == [
        {
            "name": "anyfileio-neutral-shell-authority-v3",
            "nodes": [
                "tests/test_sesam.py::test_semantics_resolves_a_neutral_mesh_and_records",
                "tests/test_sesam.py::test_semantics_resolves_explicit_shell_local_axes",
            ],
            "repository": "ANYfileIO",
        },
        {
            "name": "anyintelligent-production-entrypoint-v3",
            "nodes": [
                "tests/test_external_anysolver_adapter.py::test_production_entrypoint_routes_qualified_geometry_through_adapter"
            ],
            "repository": "ANYintelligent",
        },
        {
            "name": "exact-wheel-cross-package-v3",
            "nodes": ["tests/test_e4_pl_s3_cross_wheel_v3.py"],
            "repository": "ANYsolver",
        },
    ]
    batch = [
        formal.build_assignment(authority, worker)["payload"]
        for worker in formal.BATCH_WORKERS
    ]
    assert sorted(index for shard in batch for index in shard["repetition_indices"]) == list(
        range(12)
    )
    assert all(shard["eligible_element_count"] == 4096 for shard in batch)


def test_formal_assignment_is_canonical_hash_bound_and_mutation_rejected(
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_formal_assignment_mutation", FORMAL)
    authority = _assignment_authority(formal)
    value = formal.build_assignment(authority, "STRUCTURAL_SLASH")
    path = tmp_path / "assignment.json"
    path.write_bytes(formal.canonical_bytes(value))
    observed, digest = formal.read_assignment(authority, path)
    assert observed == value
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest().upper()
    value["payload"]["manifest_records"][0]["sha256"] = "0" * 64
    path.write_bytes(formal.canonical_bytes(value))
    with pytest.raises(formal.QualificationError, match="assignment differs"):
        formal.read_assignment(authority, path)


def test_successor_skips_manifest_rebuild_and_amortizes_assembly_lease() -> None:
    tree = ast.parse(SUCCESSOR.read_text(encoding="utf-8"))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert not any(
        isinstance(node.func, ast.Attribute) and node.func.attr == "build_manifest"
        for node in calls
    )
    names = [
        node.func.id
        for node in calls
        if isinstance(node.func, ast.Name)
    ]
    assert names.count("_run_with_qualified_assembly_runtime_lease") == 1
    source = SUCCESSOR.read_text(encoding="utf-8")
    assert "_assemble_system_under_lease" in source
    assert "_assemble_element_matrix_under_lease" in source
    assert "timeout=" not in source


def test_contract_is_draft_regenerable_and_preserves_strict_q4_guard_identity() -> None:
    generator = _load("_s3_v3_generator_contract", GENERATOR)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["authority_state"] == "DRAFT_REQUIRES_FINAL_CANDIDATE_REBIND"
    assert contract["formal_qualification_authority"] is False
    assert contract["formal_runner"]["exact_topology_records"] == 252
    assert contract["formal_runner"]["exact_special_fixture_count"] == 8
    assert contract["execution_policy"]["total_runtime_limit_seconds"] is None
    assert contract["execution_policy"]["runtime_classification"] is False
    mechanics = contract["mechanics_equivalence"]
    assert mechanics["q4_base_mechanics_git_blob"] == (
        "59ceb9534dfd22e05ea69296f92abeb0511f14cf"
    )
    assert mechanics["q4_guard_corrected_git_blob"] == (
        "031da1cde23e7983c0f94d837f5610a24737920b"
    )
    identity = mechanics["q4_guard_only_identity"]
    assert identity["base"] == generator.Q4_BASE_IDENTITY
    assert identity["guard_correction"] == {
        "authorized_paths": [
            {"git_blob": blob, "path": path}
            for path, blob in generator.Q4_GUARD_PATH_BLOBS
        ],
        "imported": generator.Q4_GUARD_IMPORT_IDENTITY,
        "reviewed_source": generator.Q4_GUARD_SOURCE_IDENTITY,
        "scope": "GUARD_SERIALIZATION_AND_STATE_LIFECYCLE_ONLY",
    }
    frozen = identity["frozen_q4_source_identity"]
    assert frozen == {
        "excluded_authorized_guard_paths": list(generator.Q4_GUARD_SOURCE_PATHS),
        "excluded_nonmechanics_integration_paths": list(
            generator.Q4_NONMECHANICS_INTEGRATION_PATHS
        ),
        "file_count": generator.Q4_FROZEN_SOURCE_FILE_COUNT,
        "rows_sha256": generator.Q4_FROZEN_SOURCE_ROWS_SHA256,
        "scope": (
            "ALL_TRACKED_SRC_ANYSOLVER_FILES_EXCEPT_EXACT_GUARD_AND_"
            "NON_Q4_INTEGRATION_PATHS"
        ),
    }
    assert generator._frozen_source_rows(
        ROOT, generator.Q4_BASE_IDENTITY["commit"]
    ) == generator._frozen_source_rows(ROOT, "HEAD")
    assert contract["candidate_provenance"]["stable_ci_sibling_refs"] == {
        "ANYfileIO": "07124405ce0160437928e9b0c3c7a0d530c1f5de",
        "ANYgeometry": "97b06b0cfc72179c4f6522f9077d8a1d91911d61",
        "ANYmaterial": "2b6431c291c8f571803484f69d08807875996b72",
        "ANYmesh": "c06c8fa9ca58f282941a921548bf8303a8ddd084",
    }
    for path, expected_blob in generator.Q4_GUARD_PATH_BLOBS:
        observed = subprocess.run(
            ["git", "rev-parse", f"HEAD:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert observed == expected_blob
    required = set(contract["final_rebind_required"])
    assert {
        "formal_full_coverage_runner.bytes_and_sha256",
        "candidate_binding_generator.bytes_and_sha256",
        "ANYstructure.wheel.path_filename_bytes_and_sha256",
        "ANYmaterial.commit_tree_subject_root_and_wheel",
        "ANYgeometry.commit_tree_subject_root_and_wheel",
        "candidate_preflight_results_and_log_hashes",
    } <= required
    assert "ci_candidate_remote_refs" not in required


def test_nonclassifying_n20_n40_evidence_binds_all_efficiency_metrics() -> None:
    raw = EVIDENCE.read_bytes()
    evidence = json.loads(raw)
    assert raw == (
        json.dumps(evidence, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert evidence["formal_execution_authorized"] is False
    assert evidence["levels"] == [20, 40]
    assert evidence["before"]["scientific_payload_sha256"] == evidence["after"][
        "scientific_payload_sha256"
    ]
    assert evidence["comparison"]["scientific_payloads_byte_identical"] is True
    archive_root = Path(r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease") / (
        "s3-qualification-v3/optimization-evidence"
    )
    for name in ("before", "after"):
        path = Path(evidence[name]["external_path"])
        assert archive_root in path.parents
        assert ".perf2-artifacts" not in str(path)
        if path.exists():
            raw_summary = path.read_bytes()
            assert len(raw_summary) == evidence[name]["summary_bytes"]
            assert (
                hashlib.sha256(raw_summary).hexdigest().upper()
                == evidence[name]["summary_sha256"]
            )
    assert len(evidence["processes"]) == 6
    for row in evidence["processes"]:
        assert row["before"]["elapsed_ms"] > 0
        assert row["after"]["elapsed_ms"] > 0
        assert row["before"]["tree_cpu_time_100ns"] > 0
        assert row["after"]["tree_cpu_time_100ns"] > 0
        assert row["before"]["peak_tree_memory_bytes"] > 0
        assert row["after"]["peak_tree_memory_bytes"] > 0
        assert row["before"]["assembly_runtime_lease_captures"] == 3
        assert row["after"]["assembly_runtime_lease_captures"] == 1
        assert row["before"]["connectivity_manifest_regenerations"] == 1
        assert row["after"]["connectivity_manifest_regenerations"] == 0


def test_binding_generator_requires_all_exact_local_wheels() -> None:
    generator = _load("_s3_v3_generator_schema_test", GENERATOR)
    assert generator.CANDIDATES == tuple(sorted(generator.CANDIDATES))
    assert generator.PACKAGED == {
        "ANYsolver",
        "ANYmesh",
        "ANYfem",
        "ANYstructure",
        "ANYfileIO",
        "ANYmaterial",
        "ANYgeometry",
    }
    source = GENERATOR.read_text(encoding="utf-8")
    assert "formal_execution_authorized\": False" in source
    assert "candidate root is dirty" in source
    assert "wheel bytes differ" in source
    assert "q4_mechanics_git_blob" not in source
    assert "reviewed Q4 guard blob differs" in source
    assert "frozen Q4 mechanics/source identity differs" in source
    assert "timeout=30" not in source
    canonical = generator.canonical_bytes(
        {"candidates": {name: {} for name in generator.CANDIDATES}}
    )
    reparsed = json.loads(canonical)
    assert tuple(reparsed["candidates"]) == generator.CANDIDATES
    assert set(generator.PREFLIGHT_GATE_IDS) == set(generator.CANDIDATES)
    assert all(
        tuple(sorted(set(gates))) == gates
        for gates in generator.PREFLIGHT_GATE_IDS.values()
    )


def _live_solver_policy(generator: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    def git(*arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.rstrip("\r\n")

    commit = git("rev-parse", "HEAD")
    solver = {
        "commit": commit,
        "root": str(ROOT),
        "subject": git("show", "-s", "--format=%s", commit),
        "tree": git("rev-parse", f"{commit}^{{tree}}"),
        "wheel": None,
    }
    changed = git(
        "diff",
        "--name-only",
        generator.Q4_BASE_IDENTITY["commit"],
        commit,
    )
    policy = {
        "base_commit": generator.Q4_BASE_IDENTITY["commit"],
        "changed_paths": changed.splitlines() if changed else [],
        "q4_guard_import_commit": generator.Q4_GUARD_IMPORT_IDENTITY["commit"],
    }
    return policy, solver


@pytest.mark.parametrize(
    "mutation",
    ("guard_blob", "guard_commit", "frozen_hash", "candidate_tree"),
)
def test_bound_q4_guard_only_identity_mutations_fail_closed(mutation: str) -> None:
    generator = _load(f"_s3_v3_q4_guard_{mutation}", GENERATOR)
    policy, solver = _live_solver_policy(generator)
    bound = generator._verify_anysolver_policy(policy, solver)
    mutated = copy.deepcopy(bound)
    if mutation == "guard_blob":
        mutated["guard_correction"]["authorized_paths"][0]["git_blob"] = "0" * 40
    elif mutation == "guard_commit":
        mutated["guard_correction"]["imported"]["commit"] = "0" * 40
    elif mutation == "frozen_hash":
        mutated["frozen_q4_source_identity"]["rows_sha256"] = "0" * 64
    else:
        mutated["candidate"]["tree"] = "0" * 40
    with pytest.raises(generator.BindingError, match="guard-only identity"):
        generator._reverify_bound_anysolver_policy(mutated, solver)


def test_q4_frozen_source_mutation_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = _load("_s3_v3_q4_frozen_mutation", GENERATOR)
    policy, solver = _live_solver_policy(generator)
    original = generator._frozen_source_rows

    def mutated_rows(root: Path, commit: str) -> list[dict[str, str]]:
        rows = original(root, commit)
        if commit == solver["commit"]:
            rows = copy.deepcopy(rows)
            rows[0]["git_blob"] = "0" * 40
        return rows

    monkeypatch.setattr(generator, "_frozen_source_rows", mutated_rows)
    with pytest.raises(generator.BindingError, match="frozen Q4"):
        generator._verify_anysolver_policy(policy, solver)


def _preflight_binding(
    generator: Any,
    tmp_path: Path,
    name: str,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    gates = []
    for identifier in generator.PREFLIGHT_GATE_IDS[name]:
        log_path = tmp_path / f"{name}-{identifier}.log"
        log_raw = f"{name}:{identifier}:passed\n".encode("utf-8")
        log_path.write_bytes(log_raw)
        gates.append(
            {
                "command": ["python", "-m", "pytest", identifier],
                "id": identifier,
                "log": {
                    "bytes": len(log_raw),
                    "path": str(log_path),
                    "sha256": hashlib.sha256(log_raw).hexdigest().upper(),
                },
                "passed": True,
                "returncode": 0,
            }
        )
    record = {
        "candidate": name,
        "clean_tree": True,
        "commit": candidate["commit"],
        "gates": gates,
        "schema": generator.PREFLIGHT_SCHEMA,
        "tree": candidate["tree"],
    }
    result_path = tmp_path / f"{name}-preflight.json"
    raw = generator.canonical_bytes(record)
    result_path.write_bytes(raw)
    return {
        "bytes": len(raw),
        "path": str(result_path),
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
    }


def test_candidate_preflight_is_canonical_exact_and_green(tmp_path: Path) -> None:
    generator = _load("_s3_v3_preflight_green", GENERATOR)
    name = "ANYsolver"
    candidate = {"commit": "a" * 40, "tree": "b" * 40}
    binding = _preflight_binding(generator, tmp_path, name, candidate)
    verified = generator._verify_preflight(name, candidate, binding)
    assert verified["result"] == {
        "bytes": binding["bytes"],
        "path": str(Path(binding["path"]).resolve()),
        "sha256": binding["sha256"],
    }
    assert [gate["id"] for gate in verified["record"]["gates"]] == list(
        generator.PREFLIGHT_GATE_IDS[name]
    )


@pytest.mark.parametrize("mutation", ("failed", "missing", "log_hash"))
def test_candidate_preflight_mutations_fail_closed(
    tmp_path: Path,
    mutation: str,
) -> None:
    generator = _load(f"_s3_v3_preflight_{mutation}", GENERATOR)
    name = "ANYsolver"
    candidate = {"commit": "a" * 40, "tree": "b" * 40}
    binding = _preflight_binding(generator, tmp_path, name, candidate)
    result_path = Path(binding["path"])
    record = json.loads(result_path.read_text(encoding="utf-8"))
    if mutation == "failed":
        record["gates"][0]["passed"] = False
    elif mutation == "missing":
        record["gates"].pop()
    else:
        record["gates"][0]["log"]["sha256"] = "0" * 64
    raw = generator.canonical_bytes(record)
    result_path.write_bytes(raw)
    binding.update(
        bytes=len(raw),
        sha256=hashlib.sha256(raw).hexdigest().upper(),
    )
    with pytest.raises(generator.BindingError, match="preflight"):
        generator._verify_preflight(name, candidate, binding)


def test_preserved_root_evidence_and_review_temps_are_ignored_not_deleted() -> None:
    patterns = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert {
        ".perf2-artifacts/",
        ".perf2-tmp/",
        ".perf2-review-*-basetemp/",
        ".perf2-review-*-nodecollect/",
    } <= set(patterns)


def test_formal_loader_does_not_resolve_historical_candidate_roots() -> None:
    source = FORMAL.read_text(encoding="utf-8")
    assert "base.load_authority" not in source
    loader_start = source.index("def _load_frozen_v2_scientific_authority")
    loader_end = source.index("def load_authority", loader_start)
    loader = source[loader_start:loader_end]
    assert 'payload["candidates"]' not in loader
    assert "prior_eigen" not in loader
    assert "prior_structural" not in loader
    assert "opt_in_burnin" not in loader


@dataclass
class _CycleStubAuthority:
    pass


@pytest.mark.parametrize("first_terminal", ("BLOCKED", "NO_GO"))
def test_two_cycle_request_does_not_retry_blocked_or_no_go(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    first_terminal: str,
) -> None:
    formal = _load(f"_s3_v3_cycle_stop_{first_terminal}", FORMAL)
    terminal = formal.TERMINALS[0 if first_terminal == "BLOCKED" else 1]
    calls: list[Path] = []

    def fake_cycle(_authority: Any, path: Path) -> tuple[bytes, dict[str, Any]]:
        calls.append(path)
        return b"first\n", {"terminal": terminal}

    monkeypatch.setattr(formal, "run_cycle", fake_cycle)
    result = formal.run_cycles(_CycleStubAuthority(), tmp_path / "cycles", 2)
    assert len(calls) == 1
    assert result["cycles_completed"] == 1
    assert result["scientific_byte_identical"] is False
    assert result["terminal"] == terminal


def test_second_cycle_runs_only_after_provisional_go_and_must_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_cycle_go", FORMAL)
    calls: list[Path] = []

    def fake_cycle(_authority: Any, path: Path) -> tuple[bytes, dict[str, Any]]:
        calls.append(path)
        raw = b"same\n" if len(calls) == 1 else b"different\n"
        return raw, {"terminal": formal.TERMINALS[2]}

    monkeypatch.setattr(formal, "run_cycle", fake_cycle)
    result = formal.run_cycles(_CycleStubAuthority(), tmp_path / "cycles", 2)
    assert len(calls) == 2
    assert result["cycles_completed"] == 2
    assert result["scientific_byte_identical"] is False
    assert result["terminal"] == formal.TERMINALS[0]


def _process_authority(tmp_path: Path) -> Any:
    return SimpleNamespace(
        binding_path=tmp_path / "binding.json",
        authorization_path=tmp_path / "authorization.json",
        binding={
            "candidates": {
                "ANYintelligent": {"root": str(tmp_path)},
                "ANYstructure": {"root": str(tmp_path)},
            },
            "execution_target": str(tmp_path),
        },
    )


def test_formal_spawn_failure_is_one_deterministic_terminal_row(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_formal_spawn", FORMAL)

    class Control:
        TREE_RELEASE_ENVIRONMENT = "SYNTHETIC_RELEASE"
        TREE_RELEASE_BYTES = b"release\n"
        TERMINATION_BUDGET_SECONDS = 0.1

    monkeypatch.setattr(formal, "_load_module", lambda _name, _path: Control)
    monkeypatch.setattr(
        formal.subprocess,
        "Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("spawn")),
    )
    directory = tmp_path / "worker"
    directory.mkdir()
    assignment = directory / "assignment.json"
    assignment.write_bytes(b"{}\n")
    row = formal._run_process(
        _process_authority(tmp_path),
        "BATCH_0",
        directory,
        assignment,
        "A" * 64,
    )
    assert row.status == "SPAWN_FAILED"
    assert row.returncode == -1
    assert row.assignment_sha256 == "A" * 64
    assert not (directory / "record.json").exists()


@pytest.mark.parametrize(
    ("tree_peak", "expected"),
    ((24 * (1 << 30) + 1, "MEMORY_LIMIT"), (0, "INACTIVITY_TIMEOUT")),
)
def test_formal_memory_and_inactivity_fail_closed_and_clean_tree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    tree_peak: int,
    expected: str,
) -> None:
    formal = _load(f"_s3_v3_formal_{expected}", FORMAL)
    formal.INACTIVITY_SECONDS = 0
    calls = {"terminate": 0, "close": 0}

    class Process:
        pid = 1234
        returncode: int | None = None

        def poll(self) -> int | None:
            return self.returncode

    process = Process()

    class Controller:
        @staticmethod
        def sample_activity() -> tuple[int, int, tuple[int, int]]:
            return tree_peak, 1, (0, 0)

        @staticmethod
        def close() -> None:
            calls["close"] += 1

    class Control:
        TREE_RELEASE_ENVIRONMENT = "SYNTHETIC_RELEASE"
        TREE_RELEASE_BYTES = b"release\n"
        TERMINATION_BUDGET_SECONDS = 0.1

        @staticmethod
        def _attach_tree_controller(_process: Any, _limit: int) -> Controller:
            return Controller()

        @staticmethod
        def _terminate_tree(
            _process: Any, _controller: Any, *, deadline_ns: int
        ) -> None:
            del deadline_ns
            calls["terminate"] += 1
            process.returncode = 1

        @staticmethod
        def _file_activity(_path: Path) -> tuple[int, int]:
            return 0, 0

    monkeypatch.setattr(formal, "_load_module", lambda _name, _path: Control)
    monkeypatch.setattr(formal.subprocess, "Popen", lambda *_args, **_kwargs: process)
    directory = tmp_path / expected
    directory.mkdir()
    assignment = directory / "assignment.json"
    assignment.write_bytes(b"{}\n")
    row = formal._run_process(
        _process_authority(tmp_path),
        "BATCH_0",
        directory,
        assignment,
        "B" * 64,
    )
    assert row.status == expected
    assert calls == {"terminate": 1, "close": 1}
    assert not (directory / "record.json").exists()


def test_formal_worker_rejects_canonical_but_malformed_output(tmp_path: Path) -> None:
    formal = _load("_s3_v3_formal_malformed", FORMAL)
    path = tmp_path / "record.json"
    path.write_bytes(formal.canonical_bytes({"schema": formal.WORKER_SCHEMA}))
    with pytest.raises(formal.QualificationError, match="fields differ"):
        formal._read_worker(path, "BATCH_0", "C" * 64)
