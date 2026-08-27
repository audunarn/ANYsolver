"""Focused equivalence and bounding tests for activation-v2 cold-path work."""

from __future__ import annotations

import ast
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs" / "reference_cases" / "e4_pl_s3_default_activation_v2.py"
SMOKE_PROGRAM = ROOT / "scripts" / "benchmark_e4_pl_s3_activation_cold_path.py"
INPUT = ROOT / "docs" / "reference_cases" / "e4_pl_s3_default_activation_v2_input.json"
CONTRACT = ROOT / "docs" / "reference_cases" / "e4_pl_s3_default_activation_v2_contract.json"
MANIFEST = ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _runtime(name: str = "base") -> tuple[Any, Any, Any, Any]:
    runner = _load(f"_activation_cold_test_{name}", PROGRAM)
    input_value = json.loads(INPUT.read_text(encoding="utf-8"))
    contract_value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    manifest_value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = (ROOT / "src").resolve()
    authority = runner.Authority(
        INPUT,
        INPUT.read_bytes(),
        input_value,
        CONTRACT,
        CONTRACT.read_bytes(),
        contract_value,
        MANIFEST,
        runner.canonical_bytes(manifest_value),
        manifest_value,
        source,
    )
    bundle = runner._activate(authority)
    synthetic = runner._structural_authority(authority, bundle, "alternating")
    return runner, authority, bundle, synthetic


def _record(bundle: Any, synthetic: Any, *, fraction: int = 0) -> dict[str, Any]:
    return bundle.structural_common.find_record(
        synthetic,
        level=20,
        fraction=fraction,
        mask="none" if fraction == 0 else "dispersed",
        diagonal="alternating",
    )


def _plate_model_and_load(
    bundle: Any,
    synthetic: Any,
    *,
    fraction: int,
) -> tuple[Any, Any]:
    from anysolver.boundary import LoadCase

    producer = bundle.structural_producer
    smoke_authorities = producer._smoke_authorities(synthetic)
    record = _record(bundle, synthetic, fraction=fraction)
    built = synthetic.smoke_runner.build_case_model(
        smoke_authorities,
        producer.case_spec(record, prefix="STRUCTURAL_SOLVER_PARITY"),
        include_auxiliary_inputs=False,
    )
    producer._plate_boundaries(built.model, 20)
    pressure = float(synthetic.input["coverage"]["convergence_reference"]["pressure"])
    load = LoadCase("uniform_pressure_mindlin_reference")
    for element_id in built.model.mesh.elements:
        load.add_pressure_load(int(element_id), pressure)
    built.model.load_cases = [load]
    return built.model, load


def _reference_vector(runner: Any, bundle: Any, synthetic: Any, model: Any) -> np.ndarray:
    reference_spec = synthetic.input["coverage"]["convergence_reference"]
    model_spec = bundle.smoke.input_payload["model"]
    material_spec = model_spec["material"]
    modes = bundle.structural_producer._mindlin_plate_reference(
        length=float(reference_spec["length"]),
        width=float(reference_spec["width"]),
        thickness=float(reference_spec["thickness"]),
        pressure=float(reference_spec["pressure"]),
        elastic_modulus=float(material_spec["elastic_modulus"]),
        poisson_ratio=float(material_spec["poisson_ratio"]),
        terms=int(reference_spec["series_max_odd_index"]),
    )["modes"]
    return runner._reference_nodal_field(
        model,
        modes,
        length=float(reference_spec["length"]),
        width=float(reference_spec["width"]),
    )


def test_global_stiffness_quadratic_forms_match_original_elementwise_sum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    runner, _authority, bundle, synthetic = _runtime("energy")
    captured: dict[str, Any] = {}
    original = runner._solve_hard_navier_plate_v2

    def capture(model: Any, load: Any) -> Any:
        result = original(model, load)
        captured.update(model=model, displacement=np.asarray(result[0], dtype=float))
        return result

    monkeypatch.setattr(runner, "_solve_hard_navier_plate_v2", capture)
    row, _errors = runner._plate_case_v2(
        bundle,
        synthetic,
        _record(bundle, synthetic),
        recover_interface=False,
    )
    model = captured["model"]
    displacement = captured["displacement"]
    reference = _reference_vector(runner, bundle, synthetic, model)
    error = displacement - reference
    stiffness, _info = assemble_stiffness_matrix(model)
    global_forms = (
        0.5 * float(displacement @ stiffness @ displacement),
        float(error @ stiffness @ error),
        float(reference @ stiffness @ reference),
    )
    element_forms = [0.0, 0.0, 0.0]
    for element in model.mesh.elements.values():
        mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        components = element.compute_stiffness_components(
            model.mesh,
            model.get_material(element.material_name),
        )
        tangent = np.asarray(components["total"], dtype=float)
        local = displacement[mapping]
        local_reference = reference[mapping]
        local_error = local - local_reference
        element_forms[0] += 0.5 * float(local @ tangent @ local)
        element_forms[1] += float(local_error @ tangent @ local_error)
        element_forms[2] += float(local_reference @ tangent @ local_reference)
    np.testing.assert_allclose(global_forms, element_forms, rtol=1.0e-12, atol=1.0e-16)
    assert row["finite_element_strain_energy"] == pytest.approx(
        global_forms[0], rel=3.0e-13, abs=1.0e-16
    )
    assert row["discrete_reference_energy"] == pytest.approx(
        global_forms[2], rel=3.0e-13, abs=1.0e-16
    )
    assert row["energy_norm_error"] == pytest.approx(
        np.sqrt(global_forms[1] / global_forms[2]), rel=3.0e-13, abs=1.0e-16
    )


def test_selected_batched_interface_recovery_matches_scalar_elements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import anysolver.recovery as recovery

    runner, _authority, bundle, synthetic = _runtime("recovery")
    captured: dict[str, Any] = {}
    original = recovery._recover_qualified_interface_fields

    def observe(
        model: Any,
        displacement: Any,
        element_ids: Any,
        **kwargs: Any,
    ) -> Any:
        result = original(model, displacement, element_ids, **kwargs)
        captured.update(
            model=model,
            displacement=np.asarray(displacement, dtype=float),
            selected=tuple(int(element_id) for element_id in element_ids),
            recovered=result,
        )
        return result

    monkeypatch.setattr(recovery, "_recover_qualified_interface_fields", observe)
    _row, cell_errors = runner._plate_case_v2(
        bundle,
        synthetic,
        _record(bundle, synthetic, fraction=10),
        recover_interface=True,
    )
    assert cell_errors
    assert captured["selected"]
    assert set(captured["recovered"]) == set(captured["selected"])
    sample = (
        captured["selected"][0],
        captured["selected"][len(captured["selected"]) // 2],
        captured["selected"][-1],
    )
    for element_id in sample:
        model = captured["model"]
        element = model.mesh.elements[element_id]
        mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        scalar = element.compute_stresses(
            model.mesh,
            captured["displacement"][mapping],
            model.get_material(element.material_name),
            return_global=True,
        )
        observed = captured["recovered"][element_id]
        compared = {
            f"global_{component}_{surface}"
            for component in ("xx", "yy", "xy")
            for surface in ("top", "bot")
        }
        assert compared <= set(observed)
        assert compared <= set(scalar)
        for field in sorted(compared):
            actual = observed[field]
            expected = scalar[field]
            if isinstance(actual, np.ndarray):
                np.testing.assert_array_equal(actual, expected)
            else:
                assert actual == expected


@pytest.mark.parametrize("fraction", (0, 10), ids=("all-q4", "mixed-10pct"))
def test_bounded_flexural_block_solve_matches_public_full_solve(
    fraction: int,
) -> None:
    from anysolver.assembly import solve_linear

    runner, _authority, bundle, synthetic = _runtime(f"solver_parity_{fraction}")
    bounded_model, bounded_load = _plate_model_and_load(
        bundle, synthetic, fraction=fraction
    )
    full_model, full_load = _plate_model_and_load(
        bundle, synthetic, fraction=fraction
    )
    bounded, bounded_info, stiffness = runner._solve_hard_navier_plate_v2(
        bounded_model, bounded_load
    )
    full, full_info = solve_linear(
        full_model,
        full_load,
        constraint_mode="transformation",
    )
    assert bounded_info["convergence_info"]["status"] == "converged"
    assert full_info["convergence_info"]["status"] == "converged"
    np.testing.assert_allclose(bounded, full, rtol=2.0e-10, atol=2.0e-14)
    bounded_energy = 0.5 * float(bounded @ stiffness @ bounded)
    full_energy = 0.5 * float(full @ stiffness @ full)
    assert bounded_energy == pytest.approx(full_energy, rel=2.0e-10, abs=1.0e-14)


def test_mutate_restore_during_recovery_is_rejected_by_post_bracket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import anysolver.recovery as recovery

    runner, _authority, bundle, synthetic = _runtime("mutation")
    original = recovery._recover_qualified_interface_fields

    def mutate_restore(
        model: Any,
        displacement: Any,
        element_ids: Any,
        **kwargs: Any,
    ) -> Any:
        result = original(model, displacement, element_ids, **kwargs)
        node = next(iter(model.mesh.nodes.values()))
        original_x = node.x
        node.x = original_x + 0.125
        node.x = original_x
        return result

    monkeypatch.setattr(
        recovery, "_recover_qualified_interface_fields", mutate_restore
    )
    with pytest.raises(ValueError, match="qualified|changed|mutation"):
        runner._plate_case_v2(
            bundle,
            synthetic,
            _record(bundle, synthetic),
            recover_interface=True,
        )


def test_mutate_restore_then_recovery_failure_still_finalizes_outer_lease(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import anysolver.recovery as recovery

    runner, _authority, bundle, synthetic = _runtime("exceptional_mutation")

    def mutate_restore_then_fail(
        model: Any, displacement: Any, element_ids: Any, **kwargs: Any
    ) -> Any:
        del displacement, element_ids, kwargs
        node = next(iter(model.mesh.nodes.values()))
        original_x = node.x
        node.x = original_x + 0.125
        node.x = original_x
        raise RuntimeError("sentinel recovery failure")

    monkeypatch.setattr(
        recovery,
        "_recover_qualified_interface_fields",
        mutate_restore_then_fail,
    )
    with pytest.raises(ValueError, match="qualified|changed|mutation"):
        runner._plate_case_v2(
            bundle,
            synthetic,
            _record(bundle, synthetic),
            recover_interface=True,
        )


def _observe_plate_finalizations(
    runner: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, bool]]:
    observed: list[tuple[str, bool]] = []
    original = runner._run_finalized_plate_observation

    def run(model: Any, lease: Any, operation: Any) -> Any:
        def observed_lease(*args: Any, **kwargs: Any) -> Any:
            observed.append((str(kwargs.get("context")), kwargs.get("final") is True))
            return lease(*args, **kwargs)

        return original(model, observed_lease, operation)

    monkeypatch.setattr(runner, "_run_finalized_plate_observation", run)
    return observed


def test_component_traversal_exception_finalizes_observation_lease(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, _authority, bundle, synthetic = _runtime("component_exception")
    finalized = _observe_plate_finalizations(runner, monkeypatch)
    original = runner._observe_plate_case_v2

    class FailingSmoke:
        @staticmethod
        def _cell_connectivity(*_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("sentinel component traversal failure")

    def fail_component_traversal(**kwargs: Any) -> Any:
        kwargs["smoke"] = FailingSmoke()
        return original(**kwargs)

    monkeypatch.setattr(runner, "_observe_plate_case_v2", fail_component_traversal)
    with pytest.raises(RuntimeError, match="sentinel component traversal failure"):
        runner._plate_case_v2(
            bundle,
            synthetic,
            _record(bundle, synthetic),
            recover_interface=False,
        )
    assert finalized == [
        ("activation-v2 plate observation exceptional output", True)
    ]


def test_recovered_field_callback_exception_finalizes_observation_lease(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import anysolver.recovery as recovery

    runner, _authority, bundle, synthetic = _runtime("field_exception")
    finalized = _observe_plate_finalizations(runner, monkeypatch)
    original = recovery._recover_qualified_interface_fields

    class ArrayBomb:
        def __array__(self, *_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("sentinel recovered-field callback failure")

    def corrupt_one_field(*args: Any, **kwargs: Any) -> Any:
        recovered = original(*args, **kwargs)
        first = next(iter(recovered.values()))
        first["global_xx_top"] = ArrayBomb()
        return recovered

    monkeypatch.setattr(
        recovery,
        "_recover_qualified_interface_fields",
        corrupt_one_field,
    )
    with pytest.raises(RuntimeError, match="sentinel recovered-field callback failure"):
        runner._plate_case_v2(
            bundle,
            synthetic,
            _record(bundle, synthetic, fraction=10),
            recover_interface=True,
        )
    assert finalized == [
        ("activation-v2 plate observation exceptional output", True)
    ]


def test_post_stiffness_exception_with_aba_raises_final_lease_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import anysolver.matrix_assembly as matrix_assembly

    runner, _authority, bundle, synthetic = _runtime("post_stiffness_exception")
    finalized = _observe_plate_finalizations(runner, monkeypatch)
    original = matrix_assembly.assemble_stiffness_matrix

    def mutate_restore_then_fail(model: Any, *args: Any, **kwargs: Any) -> Any:
        original(model, *args, **kwargs)
        node = next(iter(model.mesh.nodes.values()))
        original_x = node.x
        node.x = original_x + 0.125
        node.x = original_x
        raise RuntimeError("sentinel post-stiffness failure")

    monkeypatch.setattr(
        matrix_assembly,
        "assemble_stiffness_matrix",
        mutate_restore_then_fail,
    )
    with pytest.raises(ValueError, match="qualified|changed|mutation") as caught:
        runner._plate_case_v2(
            bundle,
            synthetic,
            _record(bundle, synthetic),
            recover_interface=False,
        )
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert "sentinel post-stiffness failure" in str(caught.value.__cause__)
    assert finalized == [
        ("activation-v2 plate observation exceptional output", True)
    ]


def test_second_stiffness_bracket_rejects_changed_global_operator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, _authority, bundle, synthetic = _runtime("operator")
    original = runner._solve_hard_navier_plate_v2

    def changed_solver_matrix(model: Any, load: Any) -> Any:
        displacement, info, matrix = original(model, load)
        matrix = matrix.copy()
        matrix[0, 0] = float(matrix[0, 0]) + 1.0
        return displacement, info, matrix

    monkeypatch.setattr(
        runner, "_solve_hard_navier_plate_v2", changed_solver_matrix
    )
    with pytest.raises(runner.QualificationError, match="changed the qualified stiffness"):
        runner._plate_case_v2(
            bundle,
            synthetic,
            _record(bundle, synthetic),
            recover_interface=False,
        )


def test_cold_smoke_coordinator_is_stdlib_bounded_and_nonclassifying() -> None:
    smoke = _load("_activation_cold_smoke_contract", SMOKE_PROGRAM)
    tree = ast.parse(SMOKE_PROGRAM.read_text(encoding="utf-8"))
    top_level_imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level_imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level_imports.add(node.module.split(".", 1)[0])
    assert top_level_imports.isdisjoint({"anysolver", "numpy", "scipy", "sympy"})
    assert smoke.FRACTIONS == (0, 10, 25)
    assert smoke.ALLOWED_LEVELS == (20, 40, 80, 160)
    assert smoke.main.__defaults__ is not None
    source = SMOKE_PROGRAM.read_text(encoding="utf-8")
    assert 'default=[20, 40]' in source
    assert 'max_workers=workers' in source
    assert 'not 1 <= workers <= 3' in source
    assert 'not 1 <= global_limit_seconds <= 1200' in source
    assert '"automatic_retry": False' in source
    assert '"classification_authority": False' in source
    assert '"formal_execution_authorized": False' in source


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object ABI")
def test_cold_smoke_windows_job_api_uses_pointer_width_safe_signatures() -> None:
    smoke = _load("_activation_cold_smoke_windows_abi", SMOKE_PROGRAM)
    kernel32 = smoke._windows_kernel32()
    assert ctypes.sizeof(ctypes.c_void_p) == ctypes.sizeof(wintypes.HANDLE)
    assert kernel32.CreateJobObjectW.restype is wintypes.HANDLE
    assert kernel32.SetInformationJobObject.restype is wintypes.BOOL
    assert kernel32.AssignProcessToJobObject.restype is wintypes.BOOL
    assert kernel32.QueryInformationJobObject.restype is wintypes.BOOL
    assert kernel32.TerminateJobObject.restype is wintypes.BOOL
    assert kernel32.TerminateProcess.restype is wintypes.BOOL
    assert kernel32.CloseHandle.restype is wintypes.BOOL


def test_cold_smoke_forecast_is_complete_only_for_all_twelve_records() -> None:
    smoke = _load("_activation_cold_smoke_forecast", SMOKE_PROGRAM)
    rows = [
        {
            "elapsed_ms": level * fraction_scale,
            "fraction_percent": fraction,
            "level": level,
            "status": "COMPLETE",
        }
        for level in smoke.ALLOWED_LEVELS
        for fraction, fraction_scale in ((0, 1), (10, 2), (25, 3))
    ]
    expected = 60.0 + 1.25 * sum(
        level / 1000.0 + 20.0 * (3.0 * level / 1000.0)
        for level in smoke.ALLOWED_LEVELS
    )
    assert smoke.forecast_seconds(rows) == pytest.approx(expected)
    assert smoke.forecast_seconds(rows[:-1]) is None
    rows[-1]["status"] = "TIMEOUT"
    assert smoke.forecast_seconds(rows) is None


def test_cold_smoke_partial_forecast_proves_infeasibility_without_larger_levels() -> None:
    smoke = _load("_activation_cold_smoke_partial_forecast", SMOKE_PROGRAM)
    rows = [
        {
            "elapsed_ms": elapsed_ms,
            "fraction_percent": fraction,
            "level": level,
            "status": "COMPLETE",
        }
        for level, elapsed_by_fraction in (
            (20, {0: 5_000, 10: 9_000, 25: 16_000}),
            (40, {0: 20_000, 10: 40_000, 25: 80_000}),
        )
        for fraction, elapsed_ms in elapsed_by_fraction.items()
    ]
    expected = 60.0 + 1.25 * (
        5.0 + 20.0 * 16.0 + 20.0 + 20.0 * 80.0
    )
    assert smoke.forecast_seconds(rows) is None
    assert smoke.partial_forecast_lower_bound_seconds(rows) == expected
    assert expected > 480.0
    incomplete = rows[:-1]
    assert smoke.partial_forecast_lower_bound_seconds(incomplete) == (
        60.0 + 1.25 * (5.0 + 20.0 * 16.0)
    )


def test_cold_smoke_partial_forecast_ignores_failed_and_unregistered_rows() -> None:
    smoke = _load("_activation_cold_smoke_partial_forecast_filter", SMOKE_PROGRAM)
    rows = [
        {
            "elapsed_ms": 1000,
            "fraction_percent": fraction,
            "level": 20,
            "status": "COMPLETE",
        }
        for fraction in smoke.FRACTIONS
    ]
    rows.extend(
        (
            {
                "elapsed_ms": 999_999,
                "fraction_percent": 0,
                "level": 40,
                "status": "TIMEOUT",
            },
            {
                "elapsed_ms": 999_999,
                "fraction_percent": 99,
                "level": 20,
                "status": "COMPLETE",
            },
        )
    )
    assert smoke.partial_forecast_lower_bound_seconds(rows) == (
        60.0 + 1.25 * (1.0 + 20.0 * 1.0)
    )


def _valid_cold_smoke_child(smoke: Any) -> dict[str, Any]:
    return {
        "classification_authority": False,
        "elapsed_microseconds": 123,
        "energy_norm_error": 0.25,
        "fraction_percent": 10,
        "level": 20,
        "record_id": "N20:10PCT:dispersed:alternating",
        "schema": smoke.CHILD_SCHEMA,
    }


def test_cold_smoke_child_record_binds_canonical_bytes_and_hash(
    tmp_path: Path,
) -> None:
    smoke = _load("_activation_cold_smoke_child_valid", SMOKE_PROGRAM)
    value = _valid_cold_smoke_child(smoke)
    raw = smoke.canonical_bytes(value)
    path = tmp_path / "record.json"
    path.write_bytes(raw)
    observed, digest, byte_count = smoke._read_child(
        path,
        level=20,
        fraction=10,
    )
    assert observed == value
    assert digest == hashlib.sha256(raw).hexdigest().upper()
    assert byte_count == len(raw) > 0


@pytest.mark.parametrize(
    "mutation",
    (
        "duplicate",
        "nonfinite",
        "noncanonical",
        "schema",
        "classification",
        "level",
        "level_type",
        "fraction",
        "fraction_type",
        "record_id",
        "elapsed",
        "energy",
        "missing",
        "extra",
    ),
)
def test_cold_smoke_child_record_mutations_fail_closed(
    tmp_path: Path,
    mutation: str,
) -> None:
    smoke = _load(f"_activation_cold_smoke_child_{mutation}", SMOKE_PROGRAM)
    value = _valid_cold_smoke_child(smoke)
    if mutation == "schema":
        value["schema"] = "changed"
    elif mutation == "classification":
        value["classification_authority"] = True
    elif mutation == "level":
        value["level"] = 40
    elif mutation == "level_type":
        value["level"] = 20.0
    elif mutation == "fraction":
        value["fraction_percent"] = 25
    elif mutation == "fraction_type":
        value["fraction_percent"] = 10.0
    elif mutation == "record_id":
        value["record_id"] = "N20:10PCT:chain:alternating"
    elif mutation == "elapsed":
        value["elapsed_microseconds"] = -1
    elif mutation == "energy":
        value["energy_norm_error"] = -0.25
    elif mutation == "missing":
        del value["record_id"]
    elif mutation == "extra":
        value["unexpected"] = False
    raw = smoke.canonical_bytes(value)
    if mutation == "duplicate":
        raw = raw.replace(b'"level":20', b'"level":20,"level":20')
    elif mutation == "nonfinite":
        raw = raw.replace(b'"energy_norm_error":0.25', b'"energy_norm_error":NaN')
    elif mutation == "noncanonical":
        raw = raw[:-1] + b" \n"
    path = tmp_path / f"{mutation}.json"
    path.write_bytes(raw)
    with pytest.raises(smoke.SmokeError):
        smoke._read_child(path, level=20, fraction=10)


def test_cold_smoke_run_child_never_accepts_unvalidated_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    smoke = _load("_activation_cold_smoke_child_gate", SMOKE_PROGRAM)
    value = _valid_cold_smoke_child(smoke)
    value["record_id"] = "N20:10PCT:unregistered:alternating"
    rejected = smoke.canonical_bytes(value)

    class FinishedProcess:
        pid = 12345

        @staticmethod
        def poll() -> int:
            return 0

    class AccountedTree:
        @staticmethod
        def sample() -> tuple[int, int]:
            return 4096, 0

        @staticmethod
        def terminate() -> bool:
            return True

        @staticmethod
        def close() -> None:
            return None

    def launch(command: list[str], **_kwargs: Any) -> FinishedProcess:
        output = Path(command[command.index("--output") + 1])
        output.write_bytes(rejected)
        return FinishedProcess()

    monkeypatch.setattr(smoke.subprocess, "Popen", launch)
    monkeypatch.setattr(
        smoke,
        "_attach_tree_controller",
        lambda _process, _limit: AccountedTree(),
    )
    result = smoke._run_child(
        level=20,
        fraction=10,
        root=tmp_path,
        environment={},
        timeout_seconds=5.0,
        deadline_ns=smoke.time.monotonic_ns() + 5_000_000_000,
        memory_limit_bytes=1 << 30,
    )
    assert result.status == "MALFORMED_OUTPUT"
    assert result.child_elapsed_microseconds == -1
    assert result.record_byte_count == len(rejected)
    assert result.record_sha256 == hashlib.sha256(rejected).hexdigest().upper()
    assert not (tmp_path / "n20-10pct" / "record.json").exists()


def test_cold_smoke_oversized_malformed_output_is_not_read_or_hashed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    smoke = _load("_activation_cold_smoke_child_oversized", SMOKE_PROGRAM)
    oversized_count = smoke.MAX_CHILD_RECORD_BYTES + 1

    class FinishedProcess:
        pid = 11223

        @staticmethod
        def poll() -> int:
            return 0

    class AccountedTree:
        @staticmethod
        def sample() -> tuple[int, int]:
            return 4096, 0

        @staticmethod
        def terminate() -> bool:
            return True

        @staticmethod
        def close() -> None:
            return None

    def launch(command: list[str], **_kwargs: Any) -> FinishedProcess:
        output = Path(command[command.index("--output") + 1])
        output.write_bytes(b"x" * oversized_count)
        return FinishedProcess()

    monkeypatch.setattr(smoke.subprocess, "Popen", launch)
    monkeypatch.setattr(
        smoke,
        "_attach_tree_controller",
        lambda _process, _limit: AccountedTree(),
    )
    result = smoke._run_child(
        level=20,
        fraction=10,
        root=tmp_path,
        environment={},
        timeout_seconds=1.0,
        deadline_ns=smoke.time.monotonic_ns() + 1_000_000_000,
        memory_limit_bytes=1 << 30,
    )
    assert result.status == "MALFORMED_OUTPUT"
    assert result.record_byte_count == oversized_count
    assert result.record_sha256 == ""
    assert not (tmp_path / "n20-10pct" / "record.json").exists()


def test_cold_smoke_spawn_failure_is_a_deterministic_terminal_row(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    smoke = _load("_activation_cold_smoke_spawn_failure", SMOKE_PROGRAM)

    def fail_spawn(*_args: Any, **_kwargs: Any) -> Any:
        raise OSError("synthetic spawn failure")

    monkeypatch.setattr(smoke.subprocess, "Popen", fail_spawn)
    result = smoke._run_child(
        level=20,
        fraction=0,
        root=tmp_path,
        environment={},
        timeout_seconds=1.0,
        deadline_ns=smoke.time.monotonic_ns() + 1_000_000_000,
        memory_limit_bytes=1 << 30,
    )
    assert result.status == "SPAWN_FAILED"
    assert result.returncode == -1
    assert result.peak_tree_memory_bytes == -1
    assert result.record_byte_count == 0
    assert result.record_sha256 == ""
    assert result.directory == "n20-0pct"


def test_cold_smoke_hung_taskkill_has_bounded_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    smoke = _load("_activation_cold_smoke_hung_taskkill", SMOKE_PROGRAM)
    calls: dict[str, Any] = {"kill": 0, "wait": 0, "taskkill_timeout": None}

    class HungProcess:
        pid = 24680

        @staticmethod
        def poll() -> None:
            return None

        @staticmethod
        def kill() -> None:
            calls["kill"] += 1

        @staticmethod
        def wait(*, timeout: float) -> None:
            calls["wait"] += 1
            raise smoke.subprocess.TimeoutExpired("synthetic", timeout)

    class FailedController:
        @staticmethod
        def terminate() -> bool:
            return False

    def hung_taskkill(*_args: Any, **kwargs: Any) -> Any:
        calls["taskkill_timeout"] = kwargs["timeout"]
        raise smoke.subprocess.TimeoutExpired("taskkill", kwargs["timeout"])

    monkeypatch.setattr(smoke.os, "name", "nt")
    monkeypatch.setattr(smoke.subprocess, "run", hung_taskkill)
    started = smoke.time.monotonic()
    smoke._terminate_tree(
        HungProcess(),
        FailedController(),
        deadline_ns=smoke.time.monotonic_ns() + 100_000_000,
    )
    assert smoke.time.monotonic() - started < 0.5
    assert 0.0 < calls["taskkill_timeout"] <= smoke.TASKKILL_TIMEOUT_SECONDS
    assert calls["kill"] == 1
    assert calls["wait"] == 1


def test_cold_smoke_tree_memory_excess_terminates_and_removes_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    smoke = _load("_activation_cold_smoke_tree_memory", SMOKE_PROGRAM)
    limit = 1 << 30

    class RunningProcess:
        pid = 13579
        returncode: int | None = None

        def poll(self) -> int | None:
            return self.returncode

        def kill(self) -> None:
            self.returncode = 1

        def wait(self, *, timeout: float) -> int:
            del timeout
            self.returncode = 1
            return 1

    process = RunningProcess()
    calls = {"terminate": 0, "close": 0}

    class ExcessTree:
        @staticmethod
        def sample() -> tuple[int, int]:
            return limit + 1, 2

        @staticmethod
        def terminate() -> bool:
            calls["terminate"] += 1
            process.returncode = 1
            return True

        @staticmethod
        def close() -> None:
            calls["close"] += 1

    monkeypatch.setattr(
        smoke.subprocess, "Popen", lambda *_args, **_kwargs: process
    )
    monkeypatch.setattr(
        smoke.subprocess,
        "run",
        lambda *_args, **_kwargs: smoke.subprocess.CompletedProcess([], 0),
    )
    monkeypatch.setattr(
        smoke,
        "_attach_tree_controller",
        lambda _process, _limit: ExcessTree(),
    )
    result = smoke._run_child(
        level=20,
        fraction=25,
        root=tmp_path,
        environment={},
        timeout_seconds=1.0,
        deadline_ns=smoke.time.monotonic_ns() + 1_000_000_000,
        memory_limit_bytes=limit,
    )
    assert result.status == "MEMORY_LIMIT"
    assert result.peak_tree_memory_bytes == limit + 1
    assert calls == {"terminate": 1, "close": 1}
    assert not (tmp_path / "n20-25pct" / "record.json").exists()


def test_cold_smoke_waits_for_complete_job_tree_before_accepting_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    smoke = _load("_activation_cold_smoke_tree_completion", SMOKE_PROGRAM)
    value = _valid_cold_smoke_child(smoke)
    value["fraction_percent"] = 0
    value["record_id"] = "N20:0PCT:none:alternating"
    raw = smoke.canonical_bytes(value)

    class RootExitedProcess:
        pid = 97531

        @staticmethod
        def poll() -> int:
            return 0

    samples = [(1024, 1), (2048, 0)]
    calls = {"sample": 0, "close": 0}

    class DescendantTree:
        @staticmethod
        def sample() -> tuple[int, int]:
            calls["sample"] += 1
            return samples.pop(0)

        @staticmethod
        def terminate() -> bool:
            return True

        @staticmethod
        def close() -> None:
            calls["close"] += 1

    def launch(command: list[str], **_kwargs: Any) -> RootExitedProcess:
        Path(command[command.index("--output") + 1]).write_bytes(raw)
        return RootExitedProcess()

    monkeypatch.setattr(smoke.subprocess, "Popen", launch)
    monkeypatch.setattr(
        smoke,
        "_attach_tree_controller",
        lambda _process, _limit: DescendantTree(),
    )
    result = smoke._run_child(
        level=20,
        fraction=0,
        root=tmp_path,
        environment={},
        timeout_seconds=1.0,
        deadline_ns=smoke.time.monotonic_ns() + 1_000_000_000,
        memory_limit_bytes=1 << 30,
    )
    assert result.status == "COMPLETE"
    assert result.peak_tree_memory_bytes == 2048
    assert calls == {"sample": 2, "close": 1}


def test_cold_smoke_accounting_failure_blocks_before_acceptance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    smoke = _load("_activation_cold_smoke_accounting_failure", SMOKE_PROGRAM)

    class RunningProcess:
        pid = 86420
        returncode: int | None = None

        def poll(self) -> int | None:
            return self.returncode

        def kill(self) -> None:
            self.returncode = 1

        def wait(self, *, timeout: float) -> int:
            del timeout
            self.returncode = 1
            return 1

    process = RunningProcess()
    monkeypatch.setattr(
        smoke.subprocess, "Popen", lambda *_args, **_kwargs: process
    )
    monkeypatch.setattr(
        smoke.subprocess,
        "run",
        lambda *_args, **_kwargs: smoke.subprocess.CompletedProcess([], 0),
    )
    monkeypatch.setattr(
        smoke,
        "_attach_tree_controller",
        lambda _process, _limit: (_ for _ in ()).throw(
            smoke._TreeAccountingError("unavailable")
        ),
    )
    result = smoke._run_child(
        level=20,
        fraction=10,
        root=tmp_path,
        environment={},
        timeout_seconds=1.0,
        deadline_ns=smoke.time.monotonic_ns() + 1_000_000_000,
        memory_limit_bytes=1 << 30,
    )
    assert result.status == "MEMORY_ACCOUNTING_UNAVAILABLE"
    assert result.returncode == 1
    assert not (tmp_path / "n20-10pct" / "record.json").exists()


@pytest.mark.parametrize(
    ("workers", "global_limit"),
    ((4, 600), (3, 1201)),
)
def test_cold_smoke_rejects_unbounded_controls_without_creating_output(
    workers: int,
    global_limit: int,
) -> None:
    smoke = _load(
        f"_activation_cold_smoke_bounds_{workers}_{global_limit}", SMOKE_PROGRAM
    )
    output = ROOT / ".forbidden-cold-smoke-test"
    assert not output.exists()
    with pytest.raises(smoke.SmokeError):
        smoke.run_smoke(
            levels=(20,),
            output_root=output,
            workers=workers,
            timeout_seconds=120,
            global_limit_seconds=global_limit,
            memory_limit_gib=24,
        )
    assert not output.exists()


def test_cold_smoke_rejects_repository_output_before_execution() -> None:
    smoke = _load("_activation_cold_smoke_external_output", SMOKE_PROGRAM)
    output = ROOT / ".forbidden-cold-smoke-test"
    assert not output.exists()
    with pytest.raises(smoke.SmokeError, match="outside the repository"):
        smoke.run_smoke(
            levels=(20,),
            output_root=output,
            workers=3,
            timeout_seconds=120,
            global_limit_seconds=600,
            memory_limit_gib=24,
        )
    assert not output.exists()
