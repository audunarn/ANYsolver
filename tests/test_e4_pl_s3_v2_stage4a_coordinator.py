from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_v2_stage4a_coordinator.py"
)


def _load():
    name = "_test_e4_pl_s3_v2_stage4a_coordinator"
    spec = importlib.util.spec_from_file_location(name, PROGRAM)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def _sequence(mask: str, fraction: int, *, advisory: bool = False, failure: str | None = None):
    failures = [] if failure is None else [failure]
    return {
        "advisory_triggered": advisory,
        "all_q4_response_slope": 2.1,
        "energy_norm_slope": 1.2,
        "energy_norm_slope_lower_95_percent": 1.0,
        "energy_norm_values": [0.4, 0.2, 0.1],
        "failed_subgates": failures,
        "finest_error_ratio_to_all_q4": 1.1,
        "fraction_percent": fraction,
        "mask": mask,
        "record_ids": [
            f"{mask}-{fraction}-N20",
            f"{mask}-{fraction}-N40",
            f"{mask}-{fraction}-N80",
        ],
        "response_error_slope": 2.0,
        "response_errors": [0.04, 0.01, 0.0025],
        "slope_deficit_from_all_q4": 0.1,
        "successive_refinement_passed": failure != "SUCCESSIVE_RESPONSE_ERROR",
    }


def _checker_value(
    module,
    assignment_id: str,
    *,
    advisory: bool = False,
    no_go: bool = False,
):
    diagonal = module.EXPECTED_SHARDS[assignment_id]
    sequences = [
        _sequence(
            mask,
            fraction,
            advisory=advisory and mask == "dispersed" and fraction == 1,
            failure=(
                "RESPONSE_SLOPE"
                if no_go and mask == "dispersed" and fraction == 1
                else None
            ),
        )
        for mask in module.MASK_ORDER
        for fraction in module.FRACTION_ORDER
    ]
    failures = ["dispersed:1:RESPONSE_SLOPE"] if no_go else []
    return {
        "advisory_review_required": bool(advisory and not no_go),
        "assignment_id": assignment_id,
        "assignment_sha256": "A" * 64,
        "classifying_record_count": 27,
        "diagonal": diagonal,
        "formal_failures": failures,
        "plan_sha256": "B" * 64,
        "production_restriction": module.PRODUCTION_RESTRICTION,
        "proof_sha256": "C" * 64,
        "schema": module.CHECKER_RESULT_SCHEMA,
        "sequence_results": sequences,
        "successor_expansion_authorized": bool(not advisory and not no_go),
        "terminal": module.NO_GO if no_go else module.PASS,
        "v1_diagnostic_record_count": 24,
    }


def _replica(
    module,
    tmp_path: Path,
    replica_index: int,
    values: dict[str, dict],
):
    made = []
    for assignment_id in module.EXPECTED_SHARDS:
        value = values[assignment_id]
        raw = module.canonical_bytes(value)
        output = (tmp_path / f"replica-{replica_index}" / f"{assignment_id}.json").resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(raw)
        made.append(
            {
                "assignment_id": assignment_id,
                "cpu_100ns": 10,
                "output_path": str(output),
                "output_sha256": module.sha256(raw),
                "peak_tree_memory_bytes": 1024,
                "stderr_sha256": module.sha256(b""),
                "stdout_sha256": module.sha256(b""),
                "termination_proven": True,
                "value": value,
            }
        )
    return made


def _values(module, **overrides):
    made = {
        assignment_id: _checker_value(module, assignment_id)
        for assignment_id in module.EXPECTED_SHARDS
    }
    for assignment_id, options in overrides.items():
        made[assignment_id] = _checker_value(module, assignment_id, **options)
    return made


def _aggregate(module, tmp_path: Path, first_values, second_values=None):
    if second_values is None:
        second_values = copy.deepcopy(first_values)
    replicas = [
        _replica(module, tmp_path, 1, first_values),
        _replica(module, tmp_path, 2, second_values),
    ]
    return module.aggregate_checker_results(
        replicas,
        producer_result_sha256="D" * 64,
        contract_sha256="E" * 64,
        authorization_sha256="F" * 64,
    )


def test_strict_json_rejects_duplicate_keys_and_nonfinite_constants():
    module = _load()
    with pytest.raises(module.CoordinatorError, match="duplicate JSON key"):
        module.strict_json_bytes(b'{"a":1,"a":2}', "duplicate")
    with pytest.raises(module.CoordinatorError, match="non-finite JSON constant"):
        module.strict_json_bytes(b'{"a":NaN}', "nonfinite")
    with pytest.raises(module.CoordinatorError, match="non-finite number"):
        module.canonical_bytes({"a": float("inf")})


def test_aggregate_pass_has_exact_coverage_and_registered_order(tmp_path):
    module = _load()
    aggregate = _aggregate(module, tmp_path, _values(module))
    assert aggregate["terminal"] == module.PASS
    assert aggregate["successor_expansion_authorized"] is True
    assert aggregate["advisory_review_required"] is False
    assert aggregate["classifying_record_count"] == 81
    assert aggregate["v1_diagnostic_record_count"] == 72
    assert len(aggregate["sequence_results"]) == 24
    assert [
        (item["diagonal"], item["mask"], item["fraction_percent"])
        for item in aggregate["sequence_results"]
    ] == [
        (diagonal, mask, fraction)
        for diagonal in module.DIAGONAL_ORDER
        for mask in module.MASK_ORDER
        for fraction in module.FRACTION_ORDER
    ]


def test_aggregate_advisory_pass_requires_review_and_blocks_expansion(tmp_path):
    module = _load()
    assignment_id = "S3_V2_FLAT_4A_SLASH"
    aggregate = _aggregate(
        module,
        tmp_path,
        _values(module, **{assignment_id: {"advisory": True}}),
    )
    assert aggregate["terminal"] == module.PASS
    assert aggregate["advisory_review_required"] is True
    assert aggregate["successor_expansion_authorized"] is False
    assert aggregate["formal_failures"] == []


def test_aggregate_no_go_has_precedence_and_scopes_failure_to_diagonal(tmp_path):
    module = _load()
    assignment_id = "S3_V2_FLAT_4A_BACKSLASH"
    aggregate = _aggregate(
        module,
        tmp_path,
        _values(module, **{assignment_id: {"no_go": True}}),
    )
    assert aggregate["terminal"] == module.NO_GO
    assert aggregate["successor_expansion_authorized"] is False
    assert aggregate["advisory_review_required"] is False
    assert aggregate["formal_failures"] == [
        "backslash:dispersed:1:RESPONSE_SLOPE"
    ]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value.__setitem__("classifying_record_count", 26),
            "identity or coverage",
        ),
        (
            lambda value: value["sequence_results"].pop(),
            "exactly eight sequences",
        ),
        (
            lambda value: value["sequence_results"].__setitem__(
                7, copy.deepcopy(value["sequence_results"][0])
            ),
            "duplicated",
        ),
    ],
)
def test_aggregate_rejects_incomplete_or_duplicate_coverage(tmp_path, mutation, message):
    module = _load()
    values = _values(module)
    mutation(values["S3_V2_FLAT_4A_SLASH"])
    with pytest.raises(module.CoordinatorError, match=message):
        _aggregate(module, tmp_path, values)


def test_aggregate_rejects_replica_byte_disagreement(tmp_path):
    module = _load()
    first = _values(module)
    second = copy.deepcopy(first)
    second["S3_V2_FLAT_4A_ALTERNATING"]["proof_sha256"] = "9" * 64
    with pytest.raises(module.CoordinatorError, match="checker replicas disagree"):
        _aggregate(module, tmp_path, first, second)


def test_blocked_aggregate_uses_the_same_fixed_schema_as_scientific_aggregate(tmp_path):
    module = _load()
    passed = _aggregate(module, tmp_path, _values(module))
    blocked = module.blocked_aggregate(
        authorization_sha256="F" * 64,
        contract_sha256="E" * 64,
        producer_result_sha256=None,
        reason="FORMAL_PROCESS_FAILED",
    )
    assert set(blocked) == set(passed)
    assert blocked["terminal"] == module.BLOCKED
    assert blocked["formal_failures"] == ["FORMAL_PROCESS_FAILED"]
    assert blocked["sequence_results"] == []
    assert blocked["producer_wave_result_sha256"] is None
    assert blocked["successor_expansion_authorized"] is False


def test_registered_resource_command_isolated_and_supplies_only_bound_dependencies(tmp_path):
    module = _load()
    command = module.expected_resource_command(
        python_executable=Path(sys.executable),
        contract_path=ROOT / "contract.json",
        authorization_path=ROOT / "authorization.json",
        output_root=tmp_path,
        aggregate_path=tmp_path / "stage4a-aggregate.json",
    )
    assert "$env:PYTHONNOUSERSITE='1';" in command
    assert "$env:PYTHONDONTWRITEBYTECODE='1';" in command
    assert " -I -B " in command
    for _name, repository in module.DEPENDENCY_REPOSITORIES:
        assert str((repository / "src").resolve()) in command
    assert str(module.ROOT / "src") not in command
    assert command.count("--run-stage4a") == 1
