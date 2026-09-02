from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs" / "reference_cases" / "e4_pl_s3_v6o_stage4a_missing_leaf_graph.py"
CANDIDATE = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6n-lease-optimization-c1e2ad9\candidate-source.tar"
)


def _load():
    spec = importlib.util.spec_from_file_location("_s3_v6o_graph_test", PROGRAM)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v6o_graph_is_exact_missing_subset() -> None:
    module = _load()
    graph = module.build_graph(CANDIDATE)
    module.validate_graph(graph)
    assert graph["activation_authorized"] is False
    assert graph["stage4a_execution_authorized"] is False
    assert graph["leaf_count"] == 12
    assert graph["wave_count"] == 4
    assert graph["source_wave_indices"] == [23, 24, 25, 26]
    observed = tuple(
        worker["record_id"]
        for wave in graph["waves"]
        for worker in wave["workers"]
    )
    assert observed == module.MISSING_RECORD_IDS
    assert all(record.startswith("N80:") for record in observed)


def test_v6o_graph_rejects_coverage_candidate_and_retry_mutations() -> None:
    module = _load()
    graph = module.build_graph(CANDIDATE)
    mutations = []
    changed = copy.deepcopy(graph)
    changed["waves"][0]["workers"][0]["record_id"] = "N20:1PCT:dispersed:slash"
    mutations.append(changed)
    changed = copy.deepcopy(graph)
    changed["candidate"]["archive_sha256"] = "0" * 64
    mutations.append(changed)
    changed = copy.deepcopy(graph)
    changed["runtime_policy"]["automatic_retry"] = True
    mutations.append(changed)
    for mutation in mutations:
        with pytest.raises(module.V6OError):
            module.validate_graph(mutation)


def test_v6o_program_changes_no_defaults_or_q4_mechanics() -> None:
    source = PROGRAM.read_text(encoding="utf-8")
    assert "DEFAULT_S3_FORMULATION" not in source
    assert "DEFAULT_Q4_FORMULATION" not in source
    assert "PROVISIONAL_GO_E4_PL_S3_DEFAULT_ACTIVATION" not in source
    assert "full frozen Phase-4A plan" in source
