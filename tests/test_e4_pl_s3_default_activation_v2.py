from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys

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


def test_authority_graph_and_frozen_q4_mechanics_are_valid() -> None:
    module = _module()
    authority = module.load_authority()
    assert authority.contract["protocol"]["topology_gated_record_count"] == 252
    assert authority.contract["candidate_policy"]["q4_mechanics_sha256"] == (
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
    authority = module.load_authority()
    assert authority.contract["coverage"]["eigen_performance"]["support"][
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
    name = "_test_s3_batch_partition"
    spec = importlib.util.spec_from_file_location(name, BATCH_PROGRAM)
    assert spec is not None and spec.loader is not None
    batch = importlib.util.module_from_spec(spec)
    sys.modules[name] = batch
    spec.loader.exec_module(batch)
    partitions = [
        batch.qualification_repetition_indices(
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
