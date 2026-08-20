from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs/reference_cases"


def _canonical(value: object) -> bytes:
    return (json.dumps(value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _load(name: str) -> tuple[dict[str, object], bytes]:
    path = CASES / name
    assert path.is_file(), f"registered evidence absent: {name}"
    raw = path.read_bytes()
    value = json.loads(raw)
    assert raw == _canonical(value)
    return value, raw


def test_q1u_evidence_terminal_and_cross_implementation_contract() -> None:
    reference, reference_raw = _load("e4_pl_q1u_reference_raw.json")
    oracle, oracle_raw = _load("e4_pl_q1u_oracle_raw.json")
    agreement, agreement_raw = _load("e4_pl_q1u_agreement.json")
    output, _ = _load("e4_pl_q1u_output.json")
    payload = reference["certificate_payload"]
    assert payload == oracle["certificate_payload"] == output["certificate_payload"]
    payload_raw = _canonical(payload)
    digest = hashlib.sha256(payload_raw).hexdigest().upper()
    assert reference["certificate_payload_sha256"] == oracle["certificate_payload_sha256"] == digest
    assert agreement["byte_identical_certificate_payload"] is True
    assert agreement["certificate_payload_sha256"] == digest
    for key, raw, impl in (("reference", reference_raw, "Q1U_REFERENCE_STDLIB_FIELD_ALG"), ("oracle", oracle_raw, "Q1U_ORACLE_SYMPY_ALGEBRAIC_FIELD")):
        row = agreement[key]
        raw_sha = hashlib.sha256(raw).hexdigest().upper()
        assert row["implementation_id"] == impl and row["deterministic"] is True
        assert row["sha256"] == row["run1_sha256"] == row["run2_sha256"] == raw_sha
    assert output["agreement_sha256"] == hashlib.sha256(agreement_raw).hexdigest().upper()
    classification = payload["classification"]
    assert classification["production"] == output["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert classification["q1b_execution"] == "UNAUTHORIZED"
    assert classification["terminal"] == agreement["terminal"] == output["classification"]
