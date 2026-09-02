from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INCIDENT = ROOT / "docs/reference_cases/e4_pl_s3_v6m_bounded_timeout_incident.json"
FORMAL_ROOT = Path(r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6m-validator-safe")


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def test_v6m_timeout_incident_binds_23_complete_waves_and_three_timeouts() -> None:
    raw = INCIDENT.read_bytes()
    incident = json.loads(raw)
    assert raw == _canonical_bytes(incident)
    rows = []
    record_count = 0
    for number in range(1, 24):
        wave = FORMAL_ROOT / f"wave-{number:02d}"
        administration = FORMAL_ROOT / "administration" / f"wave-{number:02d}"
        bounded_raw = (wave / "bounded-result.json").read_bytes()
        bounded = json.loads(bounded_raw)
        wrapper_raw = (wave / "wave-wrapper-result.json").read_bytes()
        receipt_raw = (administration / "receipt.json").read_bytes()
        assert bounded["terminal"] == "COMPLETED"
        assert json.loads(receipt_raw)["terminal"] == "COMPLETED_PASS"
        record_count += sum(worker["scientific_record_count"] for worker in bounded["workers"])
        def binding(payload: bytes) -> dict[str, object]:
            return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest().upper()}
        rows.append({
            "bounded": binding(bounded_raw),
            "receipt": binding(receipt_raw),
            "wave_index": number - 1,
            "wrapper": binding(wrapper_raw),
        })
    index_raw = _canonical_bytes(rows)
    assert record_count == incident["campaign"]["completed_scientific_record_count"] == 69
    assert len(index_raw) == incident["campaign"]["completed_wave_index_bytes"]
    assert hashlib.sha256(index_raw).hexdigest().upper() == incident["campaign"]["completed_wave_index_sha256"]
    failed = json.loads((FORMAL_ROOT / "wave-24/bounded-result.json").read_bytes())
    assert [worker["status"] for worker in failed["workers"]] == ["TIMEOUT"] * 3
    assert [worker["returncode"] for worker in failed["workers"]] == [124] * 3
    assert not (FORMAL_ROOT / "wave-25").exists()


def test_v6m_timeout_external_evidence_and_production_boundary_are_exact() -> None:
    incident = json.loads(INCIDENT.read_bytes())
    for binding in incident["external_evidence"]:
        raw = (FORMAL_ROOT / binding["path"]).read_bytes()
        assert len(raw) == binding["bytes"]
        assert hashlib.sha256(raw).hexdigest().upper() == binding["sha256"]
    assert incident["terminal"] == "BLOCKED_E4_PL_S3_V6M_PROCESS_OR_EVIDENCE"
    assert incident["activation_authorized"] is False
    assert incident["production_restriction"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert incident["successor_gate"]["raise_limits_without_diagnosis"] is False
