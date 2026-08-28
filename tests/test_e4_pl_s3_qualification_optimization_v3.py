"""Authority and coverage tests for the S3 qualification-v3 successor."""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
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
V2_PROGRAM = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_default_activation_v2.py"
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
    qualification_contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
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
        verified_file_bytes={
            "formal_runner": FORMAL.read_bytes(),
            "successor": SUCCESSOR.read_bytes(),
        },
        qualification_contract=qualification_contract,
    )


def test_v3_coordinators_are_standard_library_and_have_no_elapsed_ceiling() -> None:
    forbidden = {"anysolver", "numpy", "scipy", "sympy", "psutil"}
    assert _top_level_imports(COLD).isdisjoint(forbidden)
    assert _top_level_imports(FORMAL).isdisjoint(forbidden)
    formal_source = FORMAL.read_text(encoding="utf-8")
    contract_source = CONTRACT.read_text(encoding="utf-8")
    contract = json.loads(contract_source)
    for source in (formal_source, contract_source):
        assert "timeout_seconds_per_process" not in source
        assert "total_command_limit_seconds" not in source
        assert "forecast_acceptance_seconds" not in source
    assert "INACTIVITY_SECONDS = 1800" in formal_source
    assert "MEMORY_LIMIT_BYTES = 24 * (1 << 30)" in formal_source
    assert '"total_runtime_limit_seconds": None' in formal_source
    assert '"runtime_classification": False' in formal_source
    assert 'sys.executable,\n        "-I",\n        "-S",\n        "-B",' in formal_source
    environment_start = formal_source.index("def _environment")
    environment_end = formal_source.index("def _checkpoint_identity", environment_start)
    environment_source = formal_source[environment_start:environment_end]
    assert 'environment["PYTHONPATH"]' not in environment_source
    assert "environment = dict(process_environment)" in environment_source
    assert "os.environ.copy()" not in environment_source
    assert 'environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"' in environment_source
    assert (
        contract["execution_policy"]["python_startup"]["pytest_plugin_autoload"]
        is False
    )
    main_start = formal_source.index("def main(")
    main_source = formal_source[main_start:]
    assert main_source.index("_preclaim_launched_resource(args.output_root)") < (
        main_source.rindex("authority = load_authority(args.binding, args.authorization)")
    )
    formal = _load("_s3_v3_frozen_generator_identity", FORMAL)
    generator_raw = GENERATOR.read_bytes()
    assert formal.BINDING_GENERATOR_IDENTITY == {
        "bytes": len(generator_raw),
        "path": "scripts/prepare_e4_pl_s3_qualification_v3_input.py",
        "sha256": hashlib.sha256(generator_raw).hexdigest().upper(),
    }
    loader = formal_source[
        formal_source.index("def load_authority(") : formal_source.index(
            "def _manifest_rows", formal_source.index("def load_authority(")
        )
    ]
    assert loader.index("binding_raw, binding = read_json(binding_path)") < (
        loader.index("_load_module_from_verified_bytes(")
    )
    assert "_load_module(\"_s3_v3_binding_generator\"" not in loader
    assert "types.MappingProxyType(verified_program_bytes)" in loader
    worker_source = formal_source[
        formal_source.index("def run_worker(") : formal_source.index(
            "@dataclass(frozen=True)\nclass ProcessRow", formal_source.index("def run_worker(")
        )
    ]
    assert "_load_module(" not in worker_source
    assert "base._load_module = verified_loader" in worker_source
    assert "verified_loader=verified_loader" in worker_source
    process_source = formal_source[
        formal_source.index("def _run_process(") : formal_source.index(
            "def _expected_worker_fields", formal_source.index("def _run_process(")
        )
    ]
    assert "str(Path(__file__).resolve())" not in process_source
    assert "stdin=subprocess.PIPE" in process_source
    assert 'runner_raw = frozen_files["formal_runner"]' in process_source
    assert process_source.index("control._attach_tree_controller(") < (
        process_source.index("process.stdin.write(runner_raw)")
    )
    assert worker_source.index("_await_tree_accounting_release()") < (
        worker_source.index("successor_authority = load_authority(")
    )


def test_formal_scientific_loader_executes_only_captured_bytes(tmp_path: Path) -> None:
    formal = _load("_s3_v3_verified_scientific_loader", FORMAL)
    program = tmp_path / "registered_helper.py"
    captured = b"VALUE = 'captured'\n"
    program.write_bytes(captured)
    frozen = {formal._program_key(program): captured}
    program.write_bytes(b"VALUE = 'mutated-path'\n")

    module = formal._verified_program_loader(frozen, "_captured_helper", program)
    assert module.VALUE == "captured"

    with pytest.raises(formal.QualificationError, match="unregistered scientific"):
        formal._verified_program_loader(
            frozen,
            "_unregistered_helper",
            tmp_path / "unregistered.py",
        )

    successor_source = SUCCESSOR.read_text(encoding="utf-8")
    assert "common._load_source = verified_loader" in successor_source
    assert "eigen._load_module = verified_loader" in successor_source
    assert "smoke_runner._load_manifest_generator = lambda: manifest_generator" in (
        successor_source
    )


def test_worker_bootstrap_executes_pipe_buffer_not_bound_path(tmp_path: Path) -> None:
    formal = _load("_s3_v3_worker_bootstrap", FORMAL)
    bound_path = tmp_path / "formal_runner.py"
    bound_path.write_text("raise RuntimeError('live path executed')\n", encoding="utf-8")
    frozen = b"import sys;sys.stdout.write('frozen:'+sys.argv[1])\n"
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            "-c",
            formal.WORKER_BOOTSTRAP,
            str(bound_path),
            str(len(frozen)),
            "assigned",
        ],
        input=frozen,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode(errors="replace")
    assert completed.stdout == b"frozen:assigned"


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


def test_contract_is_frozen_regenerable_and_preserves_strict_q4_guard_identity() -> None:
    generator = _load("_s3_v3_generator_contract", GENERATOR)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["authority_state"] == (
        "IMPLEMENTATION_FROZEN_REQUIRES_FINAL_CANDIDATE_GRAPH_AND_REVIEWS"
    )
    assert contract["formal_qualification_authority"] is False
    assert contract["formal_runner"]["exact_topology_records"] == 252
    assert contract["formal_runner"]["exact_special_fixture_count"] == 8
    assert contract["formal_runner"]["cycle_count_required"] == 2
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
    candidate_root = Path(candidate["root"])
    candidate_root.mkdir(parents=True, exist_ok=True)
    for nodes in generator.PREFLIGHT_GATE_NODES[name].values():
        for relative in nodes:
            node = candidate_root / relative
            node.parent.mkdir(parents=True, exist_ok=True)
            node.touch(exist_ok=True)
    gates = []
    for identifier in generator.PREFLIGHT_GATE_IDS[name]:
        log_path = tmp_path / f"{name}-{identifier}.log"
        log_raw = f"{name}:{identifier}:passed\n".encode("utf-8")
        log_path.write_bytes(log_raw)
        gates.append(
            {
                "command": [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    *generator.PREFLIGHT_GATE_NODES[name][identifier],
                ],
                "environment": generator.PREFLIGHT_ENVIRONMENT,
                "id": identifier,
                "log": {
                    "bytes": len(log_raw),
                    "path": str(log_path),
                    "sha256": hashlib.sha256(log_raw).hexdigest().upper(),
                },
                "passed": True,
                "returncode": 0,
                "working_directory": str(candidate_root),
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
    candidate = {
        "commit": "a" * 40,
        "root": str(tmp_path / "candidate"),
        "tree": "b" * 40,
    }
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
    candidate = {
        "commit": "a" * 40,
        "root": str(tmp_path / "candidate"),
        "tree": "b" * 40,
    }
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


def test_successor_loader_binds_live_programs_without_rewriting_v2_input(
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_live_program_loader", FORMAL)
    base = _load("_s3_v3_live_program_base", V2_PROGRAM)
    binding_path = tmp_path / "binding.json"
    binding_raw = formal.canonical_bytes({"candidate": "synthetic"})
    binding_path.write_bytes(binding_raw)
    paths = {
        "base_contract": ROOT
        / "docs/reference_cases/e4_pl_s3_default_activation_v2_contract.json",
        "base_input": ROOT
        / "docs/reference_cases/e4_pl_s3_default_activation_v2_input.json",
        "base_program": V2_PROGRAM,
        "base_test": ROOT / "tests/test_e4_pl_s3_default_activation_v2.py",
        "batch_benchmark": ROOT / "scripts/benchmark_e4_pl_s3_reference_batch.py",
        "manifest": MANIFEST,
    }
    verified_files = {name: path.read_bytes() for name, path in paths.items()}
    file_rows = {
        name: {
            "bytes": len(verified_files[name]),
            "path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
            "sha256": hashlib.sha256(verified_files[name]).hexdigest().upper(),
        }
        for name, path in paths.items()
    }
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    authority = formal._load_frozen_v2_scientific_authority(
        base,
        binding_path,
        binding_raw,
        {
            "candidates": {},
            "files": file_rows,
            "runtime_environment": {"synthetic": True},
        },
        tmp_path,
        verified_files,
        contract,
    )
    assert authority.manifest_path == MANIFEST.resolve()
    assert contract["frozen_successor_scientific_programs"] == {
        "batch_benchmark": {
            "bytes": 18309,
            "path": "scripts/benchmark_e4_pl_s3_reference_batch.py",
            "sha256": "A348DFBCE3FDC62E9DBEE42788022A142605B2C1E2C436B385A702B0A6389DA5",
        },
        "runner": {
            "bytes": 90136,
            "path": "docs/reference_cases/e4_pl_s3_default_activation_v2.py",
            "sha256": "E16EB76B2C3BCB6D50675F58694D61980614CB9760185E0F135BD51CA7CC82CF",
        },
        "test": {
            "bytes": 12704,
            "path": "tests/test_e4_pl_s3_default_activation_v2.py",
            "sha256": "CE6E5FDF4A1C8266B01E5EEA24132A07AA26DA74A708033AC1F423B21FBE48F3",
        },
    }


@dataclass
class _CycleStubAuthority:
    pass


def test_two_cycle_request_does_not_retry_blocked_process(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_cycle_stop_blocked", FORMAL)
    terminal = formal.TERMINALS[0]
    calls: list[Path] = []

    def fake_cycle(_authority: Any, path: Path) -> tuple[bytes, dict[str, Any]]:
        calls.append(path)
        path.mkdir(parents=True)
        (path / "process-binding.json").write_bytes(b"{}\n")
        return b"first\n", {"terminal": terminal}

    monkeypatch.setattr(formal, "run_cycle", fake_cycle)
    authority = SimpleNamespace(
        authorization_path=tmp_path / "authorization.json",
        authorization_raw=b"authorization\n",
        binding_path=tmp_path / "binding.json",
        binding_raw=b"binding\n",
    )
    monkeypatch.setattr(formal, "load_authority", lambda *_args: authority)
    monkeypatch.setattr(
        formal, "require_active_resource_execution", lambda *_args, **_kwargs: None
    )
    result = formal.run_cycles(authority, tmp_path / "cycles", 2)
    assert len(calls) == 1
    assert result["cycles_completed"] == 1
    assert result["scientific_byte_identical"] is False
    assert result["terminal"] == terminal
    assert result["publication_commit_marker"] == "cycle-set.json"
    assert not (tmp_path / "cycles" / "cycle-1" / "scientific.json").exists()


def test_scientific_no_go_runs_two_preregistered_cycles_and_must_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_cycle_no_go", FORMAL)
    calls: list[Path] = []

    def fake_cycle(_authority: Any, path: Path) -> tuple[bytes, dict[str, Any]]:
        calls.append(path)
        path.mkdir(parents=True)
        (path / "process-binding.json").write_bytes(b"{}\n")
        (path / ".pending-scientific.json").write_bytes(b"no-go\n")
        return b"no-go\n", {"terminal": formal.TERMINALS[1]}

    monkeypatch.setattr(formal, "run_cycle", fake_cycle)
    authority = SimpleNamespace(
        authorization_path=tmp_path / "authorization.json",
        authorization_raw=b"authorization\n",
        binding_path=tmp_path / "binding.json",
        binding_raw=b"binding\n",
    )
    monkeypatch.setattr(formal, "load_authority", lambda *_args: authority)
    monkeypatch.setattr(
        formal, "require_active_resource_execution", lambda *_args, **_kwargs: None
    )
    result = formal.run_cycles(authority, tmp_path / "cycles", 2)
    assert len(calls) == 2
    assert result["cycles_completed"] == 2
    assert result["scientific_byte_identical"] is True
    assert result["terminal"] == formal.TERMINALS[1]
    assert result["publication_commit_marker"] == "cycle-set.json"
    for cycle in (1, 2):
        assert (
            tmp_path / "cycles" / f"cycle-{cycle}" / "scientific.json"
        ).read_bytes() == b"no-go\n"


def test_second_cycle_scientific_evidence_must_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_cycle_go", FORMAL)
    calls: list[Path] = []

    def fake_cycle(_authority: Any, path: Path) -> tuple[bytes, dict[str, Any]]:
        calls.append(path)
        raw = b"same\n" if len(calls) == 1 else b"different\n"
        path.mkdir(parents=True)
        (path / "process-binding.json").write_bytes(b"{}\n")
        (path / ".pending-scientific.json").write_bytes(raw)
        return raw, {"terminal": formal.TERMINALS[2]}

    monkeypatch.setattr(formal, "run_cycle", fake_cycle)
    authority = SimpleNamespace(
        authorization_path=tmp_path / "authorization.json",
        authorization_raw=b"authorization\n",
        binding_path=tmp_path / "binding.json",
        binding_raw=b"binding\n",
    )
    monkeypatch.setattr(formal, "load_authority", lambda *_args: authority)
    monkeypatch.setattr(
        formal, "require_active_resource_execution", lambda *_args, **_kwargs: None
    )
    result = formal.run_cycles(authority, tmp_path / "cycles", 2)
    assert len(calls) == 2
    assert result["cycles_completed"] == 2
    assert result["scientific_byte_identical"] is False
    assert result["terminal"] == formal.TERMINALS[0]
    assert not (tmp_path / "cycles" / "cycle-1" / "scientific.json").exists()
    assert not (tmp_path / "cycles" / "cycle-2" / "scientific.json").exists()
    assert (tmp_path / "cycles" / "cycle-set.json").is_file()


def test_one_cycle_request_is_rejected_before_output_creation(tmp_path: Path) -> None:
    formal = _load("_s3_v3_one_cycle_rejected", FORMAL)
    output = tmp_path / "cycles"
    with pytest.raises(formal.QualificationError, match="exactly two"):
        formal.run_cycles(_CycleStubAuthority(), output, 1)
    assert not output.exists()


def test_blocked_cycle_never_writes_partial_scientific_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_blocked_not_scientific", FORMAL)
    authority = _assignment_authority(formal)

    def failed_process(
        _authority: Any,
        worker_id: str,
        _directory: Path,
        _assignment: Path,
        assignment_sha256: str,
    ) -> Any:
        return formal.ProcessRow(
            worker_id,
            "FAILED",
            1,
            1,
            0,
            assignment_sha256,
            "",
            "",
            hashlib.sha256(b"").hexdigest().upper(),
            hashlib.sha256(b"").hexdigest().upper(),
        )

    monkeypatch.setattr(formal, "_run_process", failed_process)
    raw, record = formal.run_cycle(authority, tmp_path / "cycle")
    assert record["terminal"] == formal.TERMINALS[0]
    assert record["schema"].endswith("blocked-v3")
    assert "coverage" not in record and "gates" not in record
    assert (tmp_path / "cycle" / "blocked.json").read_bytes() == raw
    assert not (tmp_path / "cycle" / "scientific.json").exists()


def test_scientific_projection_binds_measurements_but_not_raw_timings() -> None:
    formal = _load("_s3_v3_scientific_projection", FORMAL)
    structural_a = {"convergence": {"energy_norm_error": 0.125}}
    structural_b = {"convergence": {"energy_norm_error": 0.126}}
    assert formal.canonical_bytes(
        formal._scientific_projection("STRUCTURAL_SLASH", structural_a)
    ) != formal.canonical_bytes(
        formal._scientific_projection("STRUCTURAL_SLASH", structural_b)
    )
    eigen_a = {
        "modal_10": {"frequencies": [1.0, 2.0]},
        "performance_10": {"summaries": {"mixed": {"median": 4.0}}},
    }
    eigen_b = copy.deepcopy(eigen_a)
    eigen_b["performance_10"]["summaries"]["mixed"]["median"] = 99.0
    assert formal._scientific_projection("EIGEN_PERFORMANCE", eigen_a) == (
        formal._scientific_projection("EIGEN_PERFORMANCE", eigen_b)
    )
    eigen_b["modal_10"]["frequencies"][0] = 1.1
    assert formal._scientific_projection("EIGEN_PERFORMANCE", eigen_a) != (
        formal._scientific_projection("EIGEN_PERFORMANCE", eigen_b)
    )

    special = {
        "qualified-s3": {
            "passed": True,
            "report": {
                "collected": 1,
                "collection_errors": 0,
                "outcomes": [
                    {
                        "nodeid": "tests/test_s3.py::test_d3",
                        "outcome": "passed",
                        "properties": [["e4_pl_s3_d3_numbering_count", 6]],
                    }
                ],
            },
            "requested_node_count": 1,
            "returncode": 0,
            "status": "PASS",
            "stderr": "raw process diagnostic",
            "stdout": "raw process diagnostic",
        }
    }
    projected = formal._scientific_projection("SPECIAL_ECOSYSTEM", special)
    assert projected["qualified-s3"]["report"]["collected"] == 1
    assert "stdout" not in projected["qualified-s3"]
    mutated = copy.deepcopy(special)
    mutated["qualified-s3"]["report"]["outcomes"][0]["properties"][0][1] = 5
    assert formal._scientific_projection("SPECIAL_ECOSYSTEM", special) != (
        formal._scientific_projection("SPECIAL_ECOSYSTEM", mutated)
    )


def test_canonical_reviews_are_loaded_and_mutations_fail(
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_review_authority", FORMAL)
    binding = {"bytes": 11, "path": "binding.json", "sha256": "A" * 64}
    review = {
        "candidate_binding": binding,
        "disposition": "ACCEPTED_NO_P0_P1",
        "findings": [],
        "production_restriction": formal.PRODUCTION_RESTRICTION,
        "reviewer_id": "independent-a",
        "schema": formal.REVIEW_SCHEMA,
    }
    path = tmp_path / "review.json"
    path.write_bytes(formal.canonical_bytes(review))
    file_binding = {
        "bytes": path.stat().st_size,
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
    }
    reviewer, observed = formal._review_authority(
        file_binding,
        expected_binding=binding,
        label="review",
    )
    assert reviewer == "independent-a" and observed == path.resolve()
    review["findings"] = [{"priority": "P1"}]
    path.write_bytes(formal.canonical_bytes(review))
    file_binding.update(
        bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest().upper(),
    )
    with pytest.raises(formal.QualificationError, match="accepted canonical"):
        formal._review_authority(
            file_binding,
            expected_binding=binding,
            label="review",
        )
    review["findings"] = []
    review["reviewer_id"] = " independent-a"
    path.write_bytes(formal.canonical_bytes(review))
    file_binding.update(
        bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest().upper(),
    )
    with pytest.raises(formal.QualificationError, match="accepted canonical"):
        formal._review_authority(
            file_binding,
            expected_binding=binding,
            label="review",
        )


def test_resource_request_is_exact_approved_and_single_use(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_resource_authority", FORMAL)
    manager = tmp_path / "manager"
    requests = manager / "requests"
    requests.mkdir(parents=True)
    monkeypatch.setattr(formal, "RESOURCE_MANAGER", manager)
    binding_path = tmp_path / "binding.json"
    authorization_path = tmp_path / "authorization.json"
    output_root = tmp_path / "cycles"
    binding_path.write_bytes(b"{}\n")
    authorization_path.write_bytes(b"{}\n")
    request_id = "1" * 32
    arguments = [
        "--binding",
        str(binding_path),
        "--authorization",
        str(authorization_path),
        "--cycles",
        "2",
        "--output-root",
        str(output_root),
    ]
    command = formal._resource_command(request_id, sys.executable, arguments)
    request = {
        "command": command,
        "estimate_minutes": 60,
        "repository": str(ROOT.resolve()),
        "request_id": request_id,
        "requested_at": "2026-08-28T00:00:00+02:00",
        "status": "PENDING",
        "task": "ANYsolver S3 qualification v3 two-cycle formal execution",
    }
    request_path = requests / f"{request_id}.json"
    request_path.write_bytes(formal.canonical_bytes(request))
    approval_line = (
        f"| 2026-08-28T00:01:00Z | {request_id} | APPROVED | task | repo | "
        "request bound | diagnostic | standing approval |\n"
    )
    ledger = manager / "ledger.md"
    ledger.write_text(approval_line, encoding="utf-8", newline="")
    resource = {
        "approval_row_sha256": hashlib.sha256(
            approval_line.encode("utf-8")
        ).hexdigest().upper(),
        "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest().upper(),
        "coordinator_arguments": arguments,
        "ledger_path": str(ledger),
        "python_executable": sys.executable,
        "request": {
            "bytes": request_path.stat().st_size,
            "path": str(request_path),
            "request_id": request_id,
            "sha256": hashlib.sha256(request_path.read_bytes()).hexdigest().upper(),
        },
    }
    verified = formal._verify_resource_authority(
        resource,
        authorization_path=authorization_path,
    )
    assert verified["request"]["request_id"] == request_id
    with ledger.open("a", encoding="utf-8", newline="") as stream:
        stream.write(
            f"| 2026-08-28T00:02:00Z | {request_id} | COMPLETED_FAIL | task | repo | "
            "consumed | diagnostic | no retry |\n"
        )
    with pytest.raises(formal.QualificationError, match="one-use"):
        formal._verify_resource_authority(
            resource,
            authorization_path=authorization_path,
        )


def _process_authority(tmp_path: Path, control: Any) -> Any:
    return SimpleNamespace(
        binding_path=tmp_path / "binding.json",
        authorization_path=tmp_path / "authorization.json",
        binding={
            "candidates": {
                "ANYintelligent": {"root": str(tmp_path)},
                "ANYstructure": {"root": str(tmp_path)},
            },
            "execution_target": str(tmp_path),
            "files": {
                "formal_runner": {
                    "path": "scripts/run_e4_pl_s3_qualification_v3.py"
                }
            },
            "runtime_environment": {"process_environment": {}},
        },
        control=control,
        verified_file_bytes={"formal_runner": FORMAL.read_bytes()},
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
        _process_authority(tmp_path, Control),
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

        class Input:
            def __init__(self) -> None:
                self.raw = bytearray()
                self.closed = False

            def write(self, raw: bytes) -> int:
                self.raw.extend(raw)
                return len(raw)

            def close(self) -> None:
                self.closed = True

        stdin = Input()

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
        _process_authority(tmp_path, Control),
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
        formal._read_worker(
            path,
            "BATCH_0",
            "C" * 64,
            _assignment_authority(formal),
        )


@pytest.mark.parametrize(
    ("gates", "coverage"),
    (
        ({"equality": True}, {"batch_elements": 4096, "batch_repetitions": 4}),
        (
            {"equality": True, "scalar_fallback": True, "shard_complete": True},
            {"batch_elements": 4096.0, "batch_repetitions": 4},
        ),
    ),
)
def test_worker_gate_and_coverage_schemas_fail_closed(
    tmp_path: Path,
    gates: dict[str, Any],
    coverage: dict[str, Any],
) -> None:
    formal = _load("_s3_v3_formal_worker_schema", FORMAL)
    path = tmp_path / "record.json"
    path.write_bytes(
        formal.canonical_bytes(
            {
                "assignment_sha256": "C" * 64,
                "coverage": coverage,
                "gates": gates,
                "production_restriction": formal.PRODUCTION_RESTRICTION,
                "schema": formal.WORKER_SCHEMA,
                "scientific_payload_sha256": "D" * 64,
                "worker_id": "BATCH_0",
            }
        )
    )
    with pytest.raises(formal.QualificationError, match="gate or coverage schema"):
        formal._read_worker(
            path,
            "BATCH_0",
            "C" * 64,
            _assignment_authority(formal),
        )


def test_active_execution_rejects_a_different_live_interpreter(tmp_path: Path) -> None:
    formal = _load("_s3_v3_live_interpreter", FORMAL)
    with pytest.raises(formal.QualificationError, match="interpreter differs"):
        formal.require_active_resource_execution(
            SimpleNamespace(
                authorization={
                    "resource_execution": {
                        "python_executable": str(CONTRACT),
                    }
                }
            )
        )


def test_resource_attempt_is_exclusive_and_never_reused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    formal = _load("_s3_v3_resource_attempt", FORMAL)
    monkeypatch.setattr(formal, "RESOURCE_MANAGER", tmp_path / "manager")
    monkeypatch.delenv(formal.RESOURCE_ATTEMPT_ENVIRONMENT, raising=False)
    authority = SimpleNamespace(
        authorization={
            "resource_execution": {
                "command_sha256": "A" * 64,
                "request": {"request_id": "1" * 32},
            }
        }
    )
    digest = formal._claim_resource_attempt(authority, tmp_path / "cycles")
    assert len(digest) == 64
    assert os.environ[formal.RESOURCE_ATTEMPT_ENVIRONMENT] == digest
    with pytest.raises(FileExistsError):
        formal._claim_resource_attempt(authority, tmp_path / "cycles")


def test_launched_request_is_claimed_before_mutable_authority_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    formal = _load("_s3_v3_resource_preclaim", FORMAL)
    manager = tmp_path / "manager"
    requests = manager / "requests"
    active = manager / "active-lock"
    requests.mkdir(parents=True)
    active.mkdir()
    monkeypatch.setattr(formal, "RESOURCE_MANAGER", manager)
    request_id = "2" * 32
    output = tmp_path / "cycles"
    arguments = [
        "--binding",
        str(tmp_path / "malformed-binding.json"),
        "--authorization",
        str(tmp_path / "malformed-authorization.json"),
        "--cycles",
        "2",
        "--output-root",
        str(output),
    ]
    monkeypatch.setattr(formal.sys, "argv", [str(FORMAL), *arguments])
    monkeypatch.setenv(formal.RESOURCE_REQUEST_ENVIRONMENT, request_id)
    command = formal._resource_command(
        request_id,
        str(Path(sys.executable).resolve()),
        arguments,
    )
    request = {
        "command": command,
        "estimate_minutes": 60,
        "repository": str(ROOT.resolve()),
        "request_id": request_id,
        "requested_at": "2026-08-28T00:00:00+02:00",
        "status": "PENDING",
        "task": "ANYsolver S3 qualification v3 two-cycle formal execution",
    }
    (requests / f"{request_id}.json").write_bytes(formal.canonical_bytes(request))
    owner = {
        "acquired_at": "2026-08-28T00:01:00+02:00",
        "command": command,
        "process_id": 1,
        "repository": str(ROOT.resolve()),
        "request_id": request_id,
        "task": request["task"],
    }
    (active / "owner.json").write_bytes(formal.canonical_bytes(owner))
    (manager / "ledger.md").write_text(
        f"| 2026-08-28T00:01:00Z | {request_id} | EXECUTION_STARTED | task | repo |\n",
        encoding="utf-8",
        newline="",
    )
    digest = formal._preclaim_launched_resource(output)
    assert len(digest) == 64
    attempt = manager / "attempts" / f"{request_id}.json"
    assert attempt.is_file()
    with pytest.raises(FileExistsError):
        formal._preclaim_launched_resource(output)


def test_bound_repository_file_is_independent_of_worker_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    formal = _load("_s3_v3_relative_binding", FORMAL)
    raw = CONTRACT.read_bytes()
    binding = {
        "bytes": len(raw),
        "path": CONTRACT.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
    }
    monkeypatch.chdir(tmp_path)
    observed, path = formal._bound_regular_file(binding, label="contract")
    assert observed == raw
    assert path == CONTRACT.resolve()


def test_publication_rejects_pending_bytes_changed_after_adjudication(
    tmp_path: Path,
) -> None:
    formal = _load("_s3_v3_pending_publication", FORMAL)
    pending = tmp_path / ".pending.json"
    canonical = tmp_path / "canonical.json"
    pending.write_bytes(b"changed\n")
    with pytest.raises(formal.QualificationError, match="bytes differ"):
        formal._publish_staged(
            pending,
            canonical,
            expected_raw=b"accepted\n",
        )
    assert not canonical.exists()


def test_publication_is_independent_of_pending_inode_after_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    formal = _load("_s3_v3_pending_publication_race", FORMAL)
    pending = tmp_path / ".pending.json"
    canonical = tmp_path / "canonical.json"
    accepted = b"accepted\n"
    pending.write_bytes(accepted)
    real_link = formal.os.link

    def mutate_pending_before_link(source: Path, destination: Path) -> None:
        pending.write_bytes(b"changed\n")
        real_link(source, destination)

    monkeypatch.setattr(formal.os, "link", mutate_pending_before_link)
    formal._publish_staged(pending, canonical, expected_raw=accepted)
    assert canonical.read_bytes() == accepted
    assert not pending.exists()


def test_nested_special_lane_returns_the_strict_adjudicator_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    successor = _load("_s3_v3_nested_lane", SUCCESSOR)
    binding = tmp_path / "binding.json"
    binding.write_bytes(b"{}\n")
    report = {
        "collected": 1,
        "collection_errors": 0,
        "outcomes": [
            {
                "nodeid": "tests/test_s3.py::test_d3",
                "outcome": "passed",
                "properties": [["e4_pl_s3_d3_numbering_count", 6]],
            }
        ],
    }
    base = SimpleNamespace(
        QualificationError=RuntimeError,
        _parse_pytest_lane_report=lambda stdout: report,
        _pytest_lane_code=lambda authority, nodes: (
            "raise SystemExit(pytest.main([] + ['-q']))"
        ),
        _pytest_lane_status=lambda returncode, parsed: (
            "PASS" if returncode == 0 and parsed == report else "BLOCKED"
        ),
        strict_json=lambda raw, label: {
            "files": {
                "binding_generator": {
                    "bytes": 1,
                    "path": "scripts/prepare_e4_pl_s3_qualification_v3_input.py",
                    "sha256": "A" * 64,
                }
            }
        },
    )
    captured: dict[str, Any] = {}

    def run(command: list[str], **kwargs: Any) -> SimpleNamespace:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stderr="", stdout="report\n")

    monkeypatch.setattr(subprocess, "run", run)
    result = successor.run_pytest_lane_without_elapsed_ceiling(
        base,
        SimpleNamespace(
            input={"runtime_environment": {"process_environment": {}}},
            input_raw=b"{}\n",
            input_path=binding,
            target=tmp_path,
        ),
        "qualified-s3",
        tmp_path,
        ["tests/test_s3.py::test_d3"],
    )
    assert result == {
        "lane": "qualified-s3",
        "passed": True,
        "report": report,
        "requested_node_count": 1,
        "returncode": 0,
        "status": "PASS",
        "stderr": "",
        "stdout": "report\n",
    }
    assert captured["command"][1:4] == ["-I", "-S", "-B"]
    assert "no:cacheprovider" in captured["command"][5]
    assert "timeout" not in captured["kwargs"]
