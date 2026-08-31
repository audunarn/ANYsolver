from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
if str(REFERENCE_CASES) not in sys.path:
    sys.path.insert(0, str(REFERENCE_CASES))

import e4_pl_s3_v2_flat_funnel as funnel
import e4_pl_s3_v2_flat_funnel_producer as producer


def _plan(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    manifest, raw = funnel.strict_json_load(producer.MANIFEST_PATH)
    records = funnel.validate_manifest(manifest, raw)
    plan = funnel.build_phase_plan(records, "4A")
    path = tmp_path / "phase4a-plan.json"
    path.write_bytes(funnel.canonical_bytes(plan))
    return path, plan


def _tiny_q4_model() -> tuple[object, dict[int, str]]:
    from anysolver.boundary import LoadCase
    from anysolver.elements import create_shell_element
    from anysolver.fe_core import FEModel

    level = 2
    model = FEModel("tiny-phase4a-q4")
    model.add_material(
        "phase4a_steel",
        producer.ELASTIC_MODULUS,
        producer.POISSON_RATIO,
        density=producer.DENSITY,
    )
    for j in range(level + 1):
        for i in range(level + 1):
            model.add_node(
                producer._node_id(i, j, level),
                i / level,
                j / level,
                0.0,
            )
    kinds: dict[int, str] = {}
    element_id = 0
    for j in range(level):
        for i in range(level):
            element_id += 1
            nodes = (
                producer._node_id(i, j, level),
                producer._node_id(i + 1, j, level),
                producer._node_id(i + 1, j + 1, level),
                producer._node_id(i, j + 1, level),
            )
            element = create_shell_element(
                element_id,
                list(nodes),
                "phase4a_steel",
                formulation="e4-pl",
                thickness=producer.THICKNESS,
                drilling_stabilization=0.001,
                hourglass_stabilization=0.001,
                pl_stabilization=1.0,
                planar_tolerance=1.0e-10,
                warped_formulation="varying_frame",
            )
            model.add_element(element_id, element)
            kinds[element_id] = "Q4"
    producer._hard_navier_supports(model, level)
    load = LoadCase("tiny-uniform-pressure")
    for registered_id in model.mesh.elements:
        load.add_pressure_load(registered_id, producer.PRESSURE)
    model.add_load_case(load)
    return model, kinds


def test_assignment_is_exact_phase4a_diagonal_shard(tmp_path: Path) -> None:
    plan_path, plan = _plan(tmp_path)
    made_plan, shard, digest = producer.load_assignment(
        plan_path,
        shard_index=1,
        selector="e4-pl-s3-v2",
    )
    assert made_plan == plan
    assert shard["diagonal"] == "backslash"
    assert len(shard["records"]) == 27
    assert digest == funnel.sha256(plan_path.read_bytes())
    with pytest.raises(funnel.FlatFunnelError, match="only the exact"):
        producer.load_assignment(plan_path, shard_index=1, selector="e4-pl-s3")


def test_mindlin_nodal_input_is_deterministic_and_satisfies_hard_trace() -> None:
    vector, digest, center = producer.mindlin_nodal_reference(2)
    repeated, repeated_digest, repeated_center = producer.mindlin_nodal_reference(2)
    np.testing.assert_array_equal(vector, repeated)
    assert digest == repeated_digest
    assert center == repeated_center
    assert len(digest) == 64 and digest == digest.upper()
    rows = vector.reshape(9, 6)
    for j in range(3):
        for i in range(3):
            row = rows[producer._node_id(i, j, 2) - 1]
            if i in (0, 2) or j in (0, 2):
                np.testing.assert_array_equal(row[:3], np.zeros(3))
            if i in (0, 2):
                assert row[4] == 0.0
            if j in (0, 2):
                assert row[3] == 0.0
    assert center != 0.0


def test_tiny_q4_production_solve_closes_discrete_energy_identity() -> None:
    model, kinds = _tiny_q4_model()
    reference, _digest, _center = producer.mindlin_nodal_reference(2)
    solver, measured, solution = producer._solve_and_measure(model, kinds, reference)
    assert solver["status"] == "CONVERGED_DIRECT_SPARSE"
    assert solver["total_dofs"] == 54
    assert solver["free_dofs"] > 0
    assert solver["residual_relative"] < 1.0e-10
    assert np.all(np.isfinite(solution))
    recomputed = (
        measured["solution_total"]
        + measured["reference_total"]
        - 2.0 * measured["solution_reference_cross"]
    )
    assert measured["error_total"] == pytest.approx(max(recomputed, 0.0), rel=2.0e-13)
    assert measured["strain_total"] == pytest.approx(
        measured["strain_physical"]
        + measured["strain_q4_pl"]
        + measured["strain_s3_pl"]
        + measured["strain_q4_hourglass"],
        rel=2.0e-12,
    )
    assert measured["strain_s3_pl"] == 0.0


def test_three_fake_shards_cover_exact_81_classifying_and_72_v1_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan_path, plan = _plan(tmp_path)
    calls: list[tuple[str, str]] = []

    def fake_case(member: dict[str, object], *, s3_selector: str) -> dict[str, object]:
        calls.append((str(member["record_id"]), s3_selector))
        return {
            "classification": (
                producer.CLASSIFICATION
                if s3_selector == producer.SELECTOR
                else "NONCLASSIFYING_V1_COMPARATOR_ONLY"
            ),
            "record_id": str(member["record_id"]),
        }

    monkeypatch.setattr(producer, "produce_case", fake_case)
    documents = []
    for shard_index in range(3):
        documents.append(
            producer.run_assignment(
                plan_path,
                shard_index=shard_index,
                selector=producer.SELECTOR,
                output=tmp_path / f"scientific-{shard_index}.json",
                progress=tmp_path / f"progress-{shard_index}.jsonl",
            )
        )
    payloads = [document["scientific_payload"] for document in documents]
    assert sum(len(payload["classifying_records"]) for payload in payloads) == 81
    assert sum(len(payload["v1_comparator_diagnostics"]) for payload in payloads) == 72
    assert len({row["record_id"] for payload in payloads for row in payload["classifying_records"]}) == 81
    assert {payload["diagonal"] for payload in payloads} == set(funnel.DIAGONALS)
    assert all(
        payload["v1_comparator_disposition"] == producer.V1_DISPOSITION
        for payload in payloads
    )
    assert sum(selector == producer.SELECTOR for _record, selector in calls) == 81
    assert sum(selector == "e4-pl-s3" for _record, selector in calls) == 72
    for shard_index, document in enumerate(documents):
        raw = (tmp_path / f"scientific-{shard_index}.json").read_bytes()
        assert raw == funnel.canonical_bytes(document)
        assert document["assignment_sha256"] == plan["shards"][shard_index]["assignment_sha256"]
        progress_rows = [
            json.loads(line)
            for line in (tmp_path / f"progress-{shard_index}.jsonl").read_text().splitlines()
        ]
        assert len(progress_rows) == 29
        assert progress_rows[0]["completed"] == 0
        assert progress_rows[-1]["completed"] == 27


def test_v2_failure_never_launches_v1_or_publishes_canonical_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan_path, _plan_value = _plan(tmp_path)
    selectors: list[str] = []

    def fail_v2(_member: object, *, s3_selector: str) -> object:
        selectors.append(s3_selector)
        raise RuntimeError("synthetic V2 contradiction")

    monkeypatch.setattr(producer, "produce_case", fail_v2)
    output = tmp_path / "must-not-exist.json"
    with pytest.raises(RuntimeError, match="synthetic V2"):
        producer.run_assignment(
            plan_path,
            shard_index=0,
            selector=producer.SELECTOR,
            output=output,
            progress=tmp_path / "failed-progress.jsonl",
        )
    assert selectors == [producer.SELECTOR]
    assert not output.exists()


def test_cli_requires_the_exact_shard_interface() -> None:
    parser = producer._parser()
    arguments = parser.parse_args(
        [
            "--run-flat-assignment",
            "plan.json",
            "--shard-index",
            "2",
            "--selector",
            producer.SELECTOR,
            "--output",
            "scientific.json",
            "--progress",
            "progress.jsonl",
        ]
    )
    assert arguments.shard_index == 2
    assert arguments.selector == producer.SELECTOR
