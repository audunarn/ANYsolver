from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_contract.json"
PRODUCER = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_producer.py"
CHECKER = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_checker.py"
COORDINATOR = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_coordinator.py"


def load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def test_contract_is_canonical_complete_and_hash_bound() -> None:
    contract = json.loads(CONTRACT.read_bytes())
    assert CONTRACT.read_bytes() == canonical(contract)
    assert contract["coverage"] == {
        "candidate_record_count_per_cycle": 18,
        "diagonals": ["slash", "backslash", "alternating"],
        "independent_q4_baseline_record_count_per_checker_replica": 3,
        "levels": [20, 40, 80],
        "masks": ["dispersed", "chain"],
        "s3_area_fraction_percent": 25,
        "sequence_count_per_cycle": 6,
    }
    assert contract["execution"] == {
        "automatic_retry": False,
        "checker_replicas_per_diagonal": 2,
        "child_wall_seconds": 600,
        "correction_cycle": 1,
        "cycle_wall_seconds": 1800,
        "maximum_concurrent_producers": 2,
        "memory_limit_gib_per_process_tree": 24,
        "numerical_library_threads_per_process": 1,
        "required_cycle_count": 2,
    }
    for name, path in (("producer", PRODUCER), ("checker", CHECKER), ("coordinator", COORDINATOR)):
        assert contract["programs"][name] == {"bytes": path.stat().st_size, "sha256": digest(path)}
    for item in contract["frozen_inputs"]:
        path = Path(item["path"])
        if not path.is_absolute():
            path = ROOT / path
        assert path.stat().st_size == item["bytes"]
        assert digest(path) == item["sha256"]


def test_authority_extent_and_static_boundaries() -> None:
    contract = json.loads(CONTRACT.read_bytes())
    authority = contract["authority_commit"]
    assert authority["expected_parent"] == "5cb08952ef3017df54924f3d13899a9eaa78ded5"
    assert authority["exact_path_count"] == len(authority["expected_paths"]) == 7
    assert contract["production_boundary"] == {
        "activation_authorized": False,
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }
    for path in (PRODUCER, CHECKER, COORDINATOR):
        ast.parse(path.read_text(encoding="utf-8"))
    text = PRODUCER.read_text(encoding="utf-8") + CHECKER.read_text(encoding="utf-8")
    assert "NODAL_UZ_RELATIVE_L2" in text
    assert "center_metric_classifying\": False" in text


def test_manifest_subset_is_exact() -> None:
    producer = load(PRODUCER, "_test_v6q_producer")
    ids: set[str] = set()
    for diagonal in producer.DIAGONALS:
        rows = producer._records(diagonal)
        assert len(rows) == 6
        for _index, row in rows:
            assert row["s3_area_fraction_percent"] == 25
            ids.add(f"N{row['level']}:25PCT:{row['mask']}:{row['diagonal']}")
    assert len(ids) == 18


def _sequence(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "diagonal": "slash",
        "mask": "chain",
        "spatial_slope_hex": (1.81).hex(),
        "spatial_slope_deficit_hex": (0.14).hex(),
        "spatial_finest_ratio_hex": (1.49).hex(),
        "spatial_successive_passed": True,
    }
    value.update(changes)
    return value


@pytest.mark.parametrize(
    ("change", "suffix"),
    [
        ({"spatial_slope_hex": (1.79).hex()}, "SPATIAL_RESPONSE_SLOPE"),
        ({"spatial_slope_deficit_hex": (0.16).hex()}, "SPATIAL_RESPONSE_SLOPE_DEFICIT"),
        ({"spatial_finest_ratio_hex": (1.51).hex()}, "SPATIAL_FINEST_ERROR_RATIO"),
        ({"spatial_successive_passed": False}, "SPATIAL_SUCCESSIVE_ERROR"),
    ],
)
def test_spatial_mutations_are_classifying(change: dict[str, object], suffix: str) -> None:
    checker = load(CHECKER, f"_test_v6q_checker_{suffix}")
    assert any(item.endswith(suffix) for item in checker._formal_failures(_sequence(**change)))


def test_center_metric_cannot_enter_formal_failures() -> None:
    checker = load(CHECKER, "_test_v6q_checker_center")
    value = _sequence(center_gate_passed=False, center_slope_hex=(0.0).hex())
    assert checker._formal_failures(value) == []


def test_terminal_precedence_and_cycle_identity() -> None:
    coordinator = load(COORDINATOR, "_test_v6q_coordinator")
    clean = {"cycle": 1, "formal_failure_count": 0, "formal_failures": [], "token": "A"}
    clean_2 = clean | {"cycle": 2}
    failed = clean | {"formal_failure_count": 1, "formal_failures": ["X"]}
    failed_2 = failed | {"cycle": 2}
    assert coordinator.adjudicate([], process_complete=False) == coordinator.BLOCKED
    assert coordinator.adjudicate([clean, clean | {"cycle": 2, "token": "B"}]) == coordinator.BLOCKED
    assert coordinator.adjudicate([failed, failed_2]) == coordinator.NO_GO
    assert coordinator.adjudicate([clean, clean_2]) == coordinator.PASS


def test_authority_validates_before_execution_authorization_exists() -> None:
    coordinator = load(COORDINATOR, "_test_v6q_coordinator_authority")
    contract, raw = coordinator.validate_authority(require_execution=False)
    assert contract["activation_authorized"] is False
    assert coordinator.sha256(raw) == digest(CONTRACT)


def test_bounded_guard_loader_registers_dataclass_module() -> None:
    coordinator = load(COORDINATOR, "_test_v6q_coordinator_guard")
    bounded = coordinator._load_bounded()
    assert bounded._ProcessJob.__module__ == "_s3_v6q_bounded_process"
    assert coordinator.sys.modules["_s3_v6q_bounded_process"] is bounded


def test_cycle_preloads_guard_before_concurrent_launch() -> None:
    tree = ast.parse(COORDINATOR.read_text(encoding="utf-8"))
    cycle = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_cycle")
    first_call = cycle.body[0]
    assert isinstance(first_call, ast.Expr)
    assert isinstance(first_call.value, ast.Call)
    assert isinstance(first_call.value.func, ast.Name)
    assert first_call.value.func.id == "_load_bounded"
