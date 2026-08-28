from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import weakref

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs" / "reference_cases" / "e4_pl_s3_default_activation_v2.py"
BATCH_PROGRAM = ROOT / "scripts" / "benchmark_e4_pl_s3_reference_batch.py"


def _module():
    name = "_test_s3_default_activation_v2"
    spec = importlib.util.spec_from_file_location(name, PROGRAM)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _contract(module):
    _raw, contract = module._read_json(
        module.REFERENCE_CASES / "e4_pl_s3_default_activation_v2_contract.json",
        pretty=True,
        label="frozen v2 contract",
    )
    return contract


def test_authority_graph_and_frozen_q4_mechanics_are_valid() -> None:
    module = _module()
    contract = _contract(module)
    assert contract["protocol"]["topology_gated_record_count"] == 252
    assert contract["candidate_policy"]["q4_mechanics_sha256"] == (
        "8D8EA5956AD2C4EC5CE643DAF9D59200995C433543994BA0526AD01BBC56A3A3"
    )


def test_three_structural_shards_cover_exactly_252_ordered_records() -> None:
    module = _module()
    sequences = [
        row
        for diagonal in ("slash", "backslash", "alternating")
        for row in module._structural_sequences(diagonal)
    ]
    assert len(sequences) == 63
    assert len(
        {
            (row["diagonal"], row["fraction_percent"], row["mask"])
            for row in sequences
        }
    ) == 63
    assert len(sequences) * 4 == 252


def test_one_sided_slope_and_terminal_precedence_are_frozen() -> None:
    module = _module()
    contract = _contract(module)
    assert contract["coverage"]["eigen_performance"]["support"][
        "dofs"
    ] == ["ux", "uy", "uz", "rx-on-x-edges", "ry-on-y-edges"]
    lower = module._lower_one_sided_95(
        [0.25, 0.0625, 0.015625, 0.00390625], [20, 40, 80, 160]
    )
    assert lower == pytest.approx(2.0)
    assert module.TERMINALS == (
        "BLOCKED_E4_PL_S3_DEFAULT_ACTIVATION_EVIDENCE_OR_REVIEW",
        "NO_GO_E4_PL_S3_DEFAULT_ACTIVATION_QUALIFICATION",
        "PROVISIONAL_GO_E4_PL_S3_DEFAULT_ACTIVATION",
    )


def test_energy_gate_uses_the_reference_field_norm_not_the_historical_proxy() -> None:
    source = PROGRAM.read_text(encoding="utf-8")
    gate = source[source.index("def _gate_convergence"):source.index("def bundle_slope")]
    assert 'row["energy_norm_error"]' in gate
    assert 'row["energy_defect_proxy"]' not in gate
    assert "u_h - I_h u_ref" in source


def test_twelve_batch_repetitions_are_partitioned_without_overlap() -> None:
    tree = ast.parse(BATCH_PROGRAM.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "qualification_repetition_indices"
    )
    namespace: dict[str, object] = {}
    exec(
        compile(
            ast.Module(body=[function], type_ignores=[]),
            str(BATCH_PROGRAM),
            "exec",
        ),
        namespace,
    )
    partition = namespace["qualification_repetition_indices"]
    partitions = [
        partition(
            repeats=4,
            shard_index=index,
            shard_count=3,
            total_repeats=12,
        )
        for index in range(3)
    ]
    assert partitions == [[0, 3, 6, 9], [1, 4, 7, 10], [2, 5, 8, 11]]
    assert sorted(value for rows in partitions for value in rows) == list(range(12))


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}\n', b'{"a":NaN}\n'])
def test_strict_json_rejects_duplicate_and_nonfinite_values(raw: bytes) -> None:
    module = _module()
    with pytest.raises(module.QualificationError):
        module.strict_json(raw, label="mutation")


def test_authority_phase_has_no_top_level_mechanics_or_numeric_import() -> None:
    tree = ast.parse(PROGRAM.read_text(encoding="utf-8"))
    forbidden = {"anysolver", "numpy", "scipy", "sympy"}
    imported: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(forbidden)


def test_execution_waves_never_exceed_three_processes() -> None:
    module = _module()
    assert len(module.STRUCTURAL_WORKERS) == 3
    assert len(module.FOLLOWUP_WORKERS) == 2
    assert len(module.BATCH_WORKERS) == 3
    assert module.EXECUTION_WAVES == (
        module.STRUCTURAL_WORKERS,
        module.FOLLOWUP_WORKERS,
        module.BATCH_WORKERS,
    )
    assert len(set().union(*map(set, module.EXECUTION_WAVES))) == len(
        module.WORKERS
    )
    assert max(map(len, module.EXECUTION_WAVES)) == 3


def test_response_slope_deficit_is_gated_against_all_q4() -> None:
    module = _module()
    levels = [20, 40, 80, 160]

    def sequence(fraction: int, scale: float, power: float) -> dict[str, object]:
        return {
            "sequence": {"fraction_percent": fraction},
            "records": [
                {
                    "center_displacement_relative_error": scale
                    * (level / levels[0]) ** (-power),
                    "energy_norm_error": 0.1
                    * (level / levels[0]) ** (-1.2),
                }
                for level in levels
            ],
        }

    authority = SimpleNamespace(
        contract={
            "acceptance_gates": {
                "convergence": {
                    "energy_norm_slope_lower_95_percent": "0.90",
                    "finest_error_ratio_at_25_percent": "1.50",
                    "finest_error_ratio_through_10_percent": "1.25",
                    "response_slope_lower_bound": "1.80",
                    "response_slope_maximum_deficit_from_all_q4": "0.15",
                    "successive_error_factor_maximum": "1.02",
                },
                "interface_resultants": {
                    "l2_ratio_at_25_percent": "1.50",
                    "l2_ratio_through_10_percent": "1.25",
                    "p99_ratio_at_25_percent": "2.00",
                    "p99_ratio_through_10_percent": "1.50",
                },
            },
            "coverage": {"structural": {"required_levels": levels}},
        }
    )
    gates, diagnostic = module._gate_convergence(
        authority,
        {
            "contradictions": [],
            "interface_rows": [],
            "rows": [sequence(0, 0.2, 2.2), sequence(10, 0.1, 2.0)],
        },
    )
    assert gates["convergence"] is False
    mixed = diagnostic["sequences"][1]
    assert mixed["response_error_slope"] == pytest.approx(2.0)
    assert mixed["response_error_slope_all_q4"] == pytest.approx(2.2)
    assert mixed["response_error_slope_deficit_from_all_q4"] == pytest.approx(0.2)


def test_paired_route_observation_releases_each_model_before_the_next() -> None:
    module = _module()
    live = 0
    maximum_live = 0
    references: list[weakref.ReferenceType[object]] = []

    class Built:
        def __init__(self) -> None:
            nonlocal live, maximum_live
            live += 1
            maximum_live = max(maximum_live, live)
            self.model = object()
            self.load_case = object()

        def __del__(self) -> None:
            nonlocal live
            live -= 1

    def build() -> Built:
        made = Built()
        references.append(weakref.ref(made))
        return made

    def solve(_model, _load_case, *, constraint_mode):
        assert constraint_mode == "transformation"
        return [0.0], {"convergence_info": {"status": "converged"}}

    for _ in range(2):
        observed = module._performance_route_observation(
            build,
            lambda _model: None,
            solve,
            rss_reader=lambda: 1024,
        )
        assert observed["rss"] == 1024.0
        assert references[-1]() is None
    assert live == 0
    assert maximum_live == 1


def _lane_result(module, name: str, outcomes: list[dict[str, object]], returncode: int):
    report = {
        "collected": len(outcomes),
        "collection_errors": 0,
        "outcomes": outcomes,
    }
    stdout = (
        module.PYTEST_LANE_REPORT_PREFIX
        + module.canonical_bytes(report).decode("ascii")
    )
    status = module._pytest_lane_status(returncode, report)
    return {
        "lane": name,
        "passed": status == "PASS",
        "report": report,
        "requested_node_count": 2,
        "returncode": returncode,
        "status": status,
        "stderr": "",
        "stdout": stdout,
    }


def test_special_lanes_require_exact_machine_counted_d3_and_reversal_coverage() -> None:
    module = _module()
    lane = {
        "name": "coverage",
        "nodes": list(module.SPECIAL_COVERAGE_NODES.values())[:2],
        "repository": "ANYsolver",
    }
    d3_node = module.SPECIAL_COVERAGE_NODES["e4_pl_s3_d3_numbering_count"]
    reversal_node = module.SPECIAL_COVERAGE_NODES[
        "e4_pl_s3_director_reversal_case_count"
    ]
    result = _lane_result(
        module,
        "coverage",
        [
            {
                "nodeid": d3_node,
                "outcome": "passed",
                "properties": [["e4_pl_s3_d3_numbering_count", 6]],
            },
            {
                "nodeid": reversal_node,
                "outcome": "passed",
                "properties": [
                    ["e4_pl_s3_director_polarity_count", 2],
                    ["e4_pl_s3_director_reversal_case_count", 12],
                    ["e4_pl_s3_director_reversal_d3_numbering_count", 6],
                ],
            },
        ],
        0,
    )
    gates, _diagnostics, coverage = module._adjudicate_special_lanes(
        [lane], [result], module.REQUIRED_SPECIAL_FIXTURES
    )
    assert gates == {"lane_coverage": True}
    assert coverage["d3_numberings"] == 6
    assert coverage["director_polarities"] == 2
    assert coverage["director_reversal_cases"] == 12
    assert coverage["director_reversal_d3_numberings"] == 6
    assert coverage["special_collected_tests"] == 2
    assert coverage["special_passed_tests"] == 2


@pytest.mark.parametrize(
    ("returncode", "outcomes"),
    [
        (5, []),
        (
            0,
            [
                {
                    "nodeid": "tests/test_required.py::test_required",
                    "outcome": "skipped",
                    "properties": [],
                }
            ],
        ),
        (
            3,
            [
                {
                    "nodeid": "tests/test_required.py::test_required",
                    "outcome": "passed",
                    "properties": [],
                }
            ],
        ),
    ],
)
def test_zero_skip_and_pytest_process_failures_are_blocked(
    returncode: int, outcomes: list[dict[str, object]]
) -> None:
    module = _module()
    report = {
        "collected": len(outcomes),
        "collection_errors": 0,
        "outcomes": outcomes,
    }
    assert module._pytest_lane_status(returncode, report) == "BLOCKED"


def test_pytest_assertion_failure_remains_scientific_no_go() -> None:
    module = _module()
    report = {
        "collected": 1,
        "collection_errors": 0,
        "outcomes": [
            {
                "nodeid": "tests/test_required.py::test_required",
                "outcome": "failed",
                "properties": [],
            }
        ],
    }
    assert module._pytest_lane_status(1, report) == "FAIL"


def test_solver_blocked_status_is_not_collapsed_into_no_go() -> None:
    module = _module()
    expected = {"modal_frequency", "modal_mac", "rigid_modes"}
    with pytest.raises(module.QualificationError, match="solver process is blocked"):
        module._adjudicate_scientific_statuses(
            "modal",
            {
                "modal_frequency": "BLOCKED",
                "modal_mac": "PASS",
                "rigid_modes": "PASS",
            },
            expected,
            pass_status="PASS",
            fail_status="FAIL",
            blocked_status="BLOCKED",
        )
    assert module._adjudicate_scientific_statuses(
        "modal",
        {
            "modal_frequency": "FAIL",
            "modal_mac": "PASS",
            "rigid_modes": "PASS",
        },
        expected,
        pass_status="PASS",
        fail_status="FAIL",
        blocked_status="BLOCKED",
    ) is False
