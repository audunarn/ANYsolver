"""Determinism and raw-evidence tests for the GE-Beam3 P2 producer."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs" / "reference_cases" / "ge_beam3_mixed_p2_formal_producer.py"


def _load_module() -> Any:
    spec = importlib.util.spec_from_file_location("ge_beam3_mixed_p2_formal_producer_test", PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


producer = _load_module()


@pytest.fixture(scope="module")
def proof() -> dict[str, Any]:
    return producer.build_proof()


def test_proof_is_canonical_deterministic_and_raw_only(proof: dict[str, Any]) -> None:
    first = producer.canonical_bytes(proof)
    second = producer.canonical_bytes(producer.build_proof())
    assert first == second
    assert json.loads(first) == proof
    assert set(proof) == {
        "bindings",
        "candidate_id",
        "content_sha256",
        "counts",
        "effective_recovery_case_ids",
        "predicates",
        "records",
        "schema",
        "study_id",
        "terminal",
    }
    body = dict(proof)
    digest = body.pop("content_sha256")
    assert digest == hashlib.sha256(producer.canonical_bytes(body)).hexdigest().upper()
    assert proof["predicates"] == {
        "producer_scientific_adjudication_present": False,
        "raw_binary64_values_encoded_little_endian": True,
    }
    assert "pass" not in json.dumps(proof["records"]).lower()
    assert "finding" not in json.dumps(proof["records"]).lower()


def test_proof_has_exact_frozen_case_coverage(proof: dict[str, Any]) -> None:
    assert proof["counts"] == {
        "load_mass_recovery": 11,
        "modal_buckling": 4,
        "solver_chart_state": 6,
        "total": 21,
    }
    assert [item["case_id"] for item in proof["records"]["solver_chart_state"]] == [
        "NONZERO_SOLVER_CHART",
        "TWO_NONCOMMUTING_COMMITS",
        "REJECTED_TRIAL_ROLLBACK_AND_CUTBACK",
        "SPLIT_RESTART_IDENTITY",
        "SHARED_NODE_DISTINCT_MATERIAL_TRIADS",
        "CONNECTIVITY_REVERSAL_STATE",
    ]
    assert [item["case_id"] for item in proof["records"]["load_mass_recovery"]] == [
        "TIP_NODAL_SPATIAL_DEAD",
        "UNIFORM_LINE_SPATIAL_DEAD",
        "LINEAR_LINE_MATERIAL_DEAD_SKEW",
        "CONSERVATIVE_FOLLOWER_REJECT",
        "NONCONSERVATIVE_FOLLOWER_REJECT",
        "REFERENCE_MASS_DIAGONAL_UNIT",
        "REFERENCE_MASS_COUPLED_SKEW",
        "RECOVERY_ZERO_NATIVE_STATE",
        "RECOVERY_UNIFORM_AXIAL_NATIVE_STATE",
        "RECOVERY_MANUFACTURED_UNIFORM_SHEAR_Y_NATIVE_STATE",
        "RECOVERY_TORSION_SIDED_NATIVE_STATE",
    ]
    assert [item["case_id"] for item in proof["records"]["modal_buckling"]] == [
        "CANTILEVER_REFERENCE_LINEAR",
        "EULER_PINNED_WEAK_Z",
        "EULER_PINNED_STRONG_Y",
        "UNSUPPORTED_PRIVATE_ROUTES",
    ]
    assert "RECOVERY_UNIFORM_SHEAR_Y_NATIVE_STATE" not in proof["effective_recovery_case_ids"]
    assert "RECOVERY_MANUFACTURED_UNIFORM_SHEAR_Y_NATIVE_STATE" in proof["effective_recovery_case_ids"]


def test_every_numeric_array_is_typed_little_endian(proof: dict[str, Any]) -> None:
    seen = 0

    def visit(value: Any) -> None:
        nonlocal seen
        if isinstance(value, dict):
            if set(value) == {"data_hex", "dtype", "shape"}:
                seen += 1
                assert value["dtype"] == "<f8"
                assert value["data_hex"] == value["data_hex"].upper()
                expected = 8
                for size in value["shape"]:
                    expected *= size
                assert len(bytes.fromhex(value["data_hex"])) == expected
            else:
                for child in value.values():
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(proof["records"])
    assert seen >= 50


def test_proof_binds_every_frozen_input(proof: dict[str, Any]) -> None:
    assert set(proof["bindings"]) == set(producer.BOUND_INPUTS)
    for name, binding in proof["bindings"].items():
        raw = (producer.REFERENCE / name).read_bytes()
        assert binding == {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
        }


def test_cli_uses_exclusive_output(tmp_path: Path) -> None:
    output = tmp_path / "proof.json"
    original = list(__import__("sys").argv)
    try:
        __import__("sys").argv = [str(PATH), "--output", str(output)]
        assert producer.main() == 0
        assert output.read_bytes() == producer.canonical_bytes(json.loads(output.read_text()))
        with pytest.raises(FileExistsError):
            producer.main()
    finally:
        __import__("sys").argv = original
