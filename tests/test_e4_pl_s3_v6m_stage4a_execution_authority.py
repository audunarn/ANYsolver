from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"
INCIDENT = REFERENCE / "e4_pl_s3_v6l_validator_recursion_incident.json"
CONTRACT = REFERENCE / "e4_pl_s3_v6m_stage4a_execution_contract.json"
PREDECESSOR = REFERENCE / "e4_pl_s3_v6l_stage4a_execution_graph.py"
SUCCESSOR = REFERENCE / "e4_pl_s3_v6m_stage4a_execution_graph.py"
V6L_ROOT = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6l-dependency-closure"
)
GRAPH = V6L_ROOT / "execution-graph.json"
CANDIDATE_ARCHIVE = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6k-2d91bba2\candidate-source.tar"
)


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw)
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return value


def test_v6l_validator_incident_is_exact_and_preworker() -> None:
    incident = _canonical(INCIDENT)
    assert incident["terminal"] == "BLOCKED_E4_PL_S3_V6L_PROCESS_OR_EVIDENCE"
    assert incident["scientific_disposition"]["worker_processes_launched"] == 0
    assert incident["scientific_disposition"]["scientific_records_created"] == 0
    for binding in incident["external_evidence"]:
        raw = (V6L_ROOT / binding["path"]).read_bytes()
        assert len(raw) == binding["bytes"]
        assert hashlib.sha256(raw).hexdigest().upper() == binding["sha256"]


def _normalized_catalog(graph: dict[str, object]) -> list[dict[str, object]]:
    made: list[dict[str, object]] = []
    for leaf in graph["leaf_catalog"]:
        assignment = copy.deepcopy(leaf["assignment"])
        assignment.pop("producer_program_sha256")
        made.append(assignment)
    return made


def test_v6m_graph_preserves_every_scientific_assignment() -> None:
    predecessor = _module(PREDECESSOR, "v6m_predecessor")
    successor = _module(SUCCESSOR, "v6m_successor")
    old = predecessor.build_graph(CANDIDATE_ARCHIVE)
    new = successor.build_graph(CANDIDATE_ARCHIVE)
    assert old["plan"] == new["plan"]
    assert _normalized_catalog(old) == _normalized_catalog(new)
    assert [wave["sequence_key"] for wave in old["waves"]] == [
        wave["sequence_key"] for wave in new["waves"]
    ]
    assert new["runtime_policy"]["maximum_concurrent_workers"] == 2
    assert successor.canonical_bytes(new) == successor.canonical_bytes(
        successor.build_graph(CANDIDATE_ARCHIVE)
    )


def test_v6m_validator_remains_safe_after_runtime_preparation() -> None:
    successor = _module(SUCCESSOR, "v6m_preparation_regression")
    graph = successor.build_graph(CANDIDATE_ARCHIVE)
    successor._prepare_execution_base()
    successor.validate_graph(graph)
    successor.validate_graph(graph)


def test_v6m_contract_preserves_limits_and_defaults() -> None:
    contract = _canonical(CONTRACT)
    assert contract["correction"] == {
        "case_coverage_changed": False,
        "dependency_closure_changed": False,
        "mechanics_changed": False,
        "protocol_changed": False,
        "runtime_validator_calls_frozen_preparation_safe_predecessor": True,
        "thresholds_changed": False,
    }
    assert contract["runtime_policy"]["child_wall_seconds"] == 600
    assert contract["runtime_policy"]["wave_wall_seconds"] == 1800
    assert contract["production_boundary"]["default_q4_formulation"] == "e4-pl"
    assert contract["production_boundary"]["default_s3_formulation"] == "legacy-s3"
