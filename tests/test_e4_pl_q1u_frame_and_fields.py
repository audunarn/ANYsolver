from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = [
    ROOT / "docs/reference_cases/e4_pl_q1u_reference_raw.json",
    ROOT / "docs/reference_cases/e4_pl_q1u_oracle_raw.json",
]
GEOMETRIES = ["Q0_SQUARE", "Q1_AFFINE_SKEW", "Q2_TRAPEZOID", "Q3_TAPERED_SKEW", "Q4_HOSTILE_ASYMMETRIC_1", "Q5_HOSTILE_ASYMMETRIC_2", "Q3_TAPERED_SKEW_RSTAR_TRANSLATED"]
OPERATIONS = ["E", "R90", "R180", "R270", "MR", "MS", "MD", "MA"]
GAUSS = ["GP_MM", "GP_PM", "GP_PP", "GP_MP"]


def _pairs(rows: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in rows:
        if key in out:
            raise ValueError(key)
        out[key] = value
    return out


def _canonical(value: object) -> bytes:
    return (json.dumps(value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _payload() -> dict[str, object]:
    wrappers = []
    for path in RAW:
        assert path.is_file(), f"missing promoted registered output: {path.name}"
        raw = path.read_bytes()
        value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
        assert raw == _canonical(value)
        assert set(value) == {"candidate_id", "certificate_payload", "certificate_payload_sha256", "exact_environment_sha256", "execution_authority_sha256", "execution_contract_sha256", "implementation_diagnostics", "implementation_id", "schema", "study_id"}
        assert value["certificate_payload_sha256"] == hashlib.sha256(_canonical(value["certificate_payload"])).hexdigest().upper()
        wrappers.append(value)
    assert wrappers[0]["certificate_payload"] == wrappers[1]["certificate_payload"]
    return wrappers[0]["certificate_payload"]


def test_q1u_all_56_numbered_frames_and_field_work() -> None:
    payload = _payload()
    assert set(payload) == {"schema", "candidate_id", "study_id", "precision_bits", "coverage", "frame_and_fields", "local_algebra", "recovery", "global_supports", "classification", "case_certificates"}
    assert payload["schema"] == "e4_pl_q1u_common_certificate_payload_v1"
    assert payload["precision_bits"] == [256, 512, 1024]
    case_ids = [f"{geometry}::{operation}" for geometry in GEOMETRIES for operation in OPERATIONS]
    station_ids = [f"{case_id}::{gp}" for case_id in case_ids for gp in GAUSS]
    coverage = payload["coverage"]
    assert coverage["numbered_cases"] == 56 and coverage["gauss_records"] == 224 and coverage["centre_records"] == 56
    assert coverage["ordered_case_ids_sha256"] == hashlib.sha256(("\n".join(case_ids) + "\n").encode()).hexdigest().upper()
    assert coverage["ordered_station_ids_sha256"] == hashlib.sha256(("\n".join(station_ids) + "\n").encode()).hexdigest().upper()
    assert [row["case_id"] for row in payload["case_certificates"]] == case_ids
    for row in payload["case_certificates"]:
        assert set(row) == {"case_id", "geometry_id", "operation_id", "gauss_station_ids", "centre", "frame", "field_work", "local_algebra", "patches", "recovery", "global_support", "status"}
        assert row["status"] in {"PASS", "NO_GO", "UNCLASSIFIED"}
        assert len(row["gauss_station_ids"]) == 4
        for section in ("centre", "frame", "field_work"):
            assert all(isinstance(value, bool) for value in row[section].values())
    assert all(isinstance(value, bool) for value in payload["frame_and_fields"].values())
