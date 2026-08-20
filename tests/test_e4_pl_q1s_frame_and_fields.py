from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_PATHS = (
    ROOT / "docs/reference_cases/e4_pl_q1s_reference_raw.json",
    ROOT / "docs/reference_cases/e4_pl_q1s_oracle_raw.json",
)
GEOMETRIES = [
    "Q0_SQUARE",
    "Q1_AFFINE_SKEW",
    "Q2_TRAPEZOID",
    "Q3_TAPERED_SKEW",
    "Q4_HOSTILE_ASYMMETRIC_1",
    "Q5_HOSTILE_ASYMMETRIC_2",
    "Q3_TAPERED_SKEW_RSTAR_TRANSLATED",
]
OPERATIONS = ["E", "R90", "R180", "R270", "MR", "MS", "MD", "MA"]
GAUSS = ["GP_MM", "GP_PM", "GP_PP", "GP_MP"]


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError(key)
        result[key] = value
    return result


def _canonical(value: object) -> bytes:
    return (json.dumps(value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()


def _load_payloads() -> tuple[dict[str, object], dict[str, object]]:
    wrappers = []
    for path in RAW_PATHS:
        assert path.is_file(), f"missing registered raw output: {path.name}"
        raw = path.read_bytes()
        assert b"\r" not in raw and raw.endswith(b"\n") and not raw.startswith(b"\xef\xbb\xbf")
        value = json.loads(raw.decode(), object_pairs_hook=_pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        assert raw == _canonical(value)
        assert set(value) == {
            "candidate_id", "certificate_payload", "certificate_payload_sha256",
            "execution_authority_sha256", "execution_contract_sha256", "implementation_diagnostics",
            "implementation_id", "schema", "study_id",
        }
        assert value["schema"] == "anysolver.s4.e4-pl-q1s-certificate-wrapper-v1"
        assert value["certificate_payload_sha256"] == hashlib.sha256(_canonical(value["certificate_payload"])).hexdigest().upper()
        wrappers.append(value)
    assert wrappers[0]["certificate_payload"] == wrappers[1]["certificate_payload"]
    return wrappers[0], wrappers[0]["certificate_payload"]


def test_q1s_all_56_numbered_frames_and_field_work() -> None:
    _wrapper, payload = _load_payloads()
    assert set(payload) == {
        "candidate_id", "case_certificates", "classification", "coverage", "frame_and_fields",
        "global_supports", "local_algebra", "precision_bits", "recovery", "schema", "study_id",
    }
    assert payload["schema"] == "anysolver.s4.e4-pl-q1s-certificate-payload-v1"
    assert payload["precision_bits"] == [256, 512, 1024]
    case_ids = [f"{geometry}::{operation}" for geometry in GEOMETRIES for operation in OPERATIONS]
    station_ids = [f"{case_id}::{station}" for case_id in case_ids for station in GAUSS]
    coverage = payload["coverage"]
    assert set(coverage) == {
        "base_geometries", "centre_records", "d4_operations", "gauss_records",
        "global_transform_variants", "numbered_cases", "ordered_case_ids_sha256",
        "ordered_station_ids_sha256",
    }
    assert coverage == {
        "base_geometries": 6,
        "centre_records": 56,
        "d4_operations": 8,
        "gauss_records": 224,
        "global_transform_variants": 1,
        "numbered_cases": 56,
        "ordered_case_ids_sha256": hashlib.sha256(("\n".join(case_ids) + "\n").encode()).hexdigest().upper(),
        "ordered_station_ids_sha256": hashlib.sha256(("\n".join(station_ids) + "\n").encode()).hexdigest().upper(),
    }
    cases = payload["case_certificates"]
    assert [row["case_id"] for row in cases] == case_ids
    assert len(cases) == 56
    for row, case_id in zip(cases, case_ids, strict=True):
        geometry, operation = case_id.split("::")
        assert set(row) == {
            "case_id", "centre", "field_work", "frame", "gauss_station_ids", "geometry_id",
            "global_support", "local_algebra", "operation_id", "patches", "recovery", "status",
        }
        assert row["geometry_id"] == geometry and row["operation_id"] == operation
        assert row["gauss_station_ids"] == [f"{case_id}::{station}" for station in GAUSS]
        assert row["status"] in {"PASS", "NO_GO", "UNCLASSIFIED"}
        assert set(row["centre"]) == {"centre_j_positive", "centre_taylor_exact", "residual_mode_exact"}
        assert set(row["frame"]) == {"equation7_exact", "projectors_exact"}
        assert set(row["field_work"]) == {
            "fields_exact", "pseudo_fields_exact", "pl_exact", "work_exact", "gauss_correspondence_exact",
        }
        for section in (row["centre"], row["frame"], row["field_work"]):
            assert all(isinstance(value, bool) for value in section.values())
    aggregate = payload["frame_and_fields"]
    assert set(aggregate) == {
        "all_d4_field_maps_exact", "all_d4_frame_identities_exact", "all_d4_pl_maps_exact",
        "all_d4_work_equalities_exact", "all_gauss_correspondence_exact", "all_numbered_loads_exact",
        "all_numbered_projectors_exact", "all_numbered_residual_modes_exact",
    }
    passed = all(aggregate.values())
    terminal = payload["classification"]["terminal"]
    if not passed:
        assert terminal in {
            "NO_GO_E4_PL_Q1S_FRAME_IDENTITY",
            "NO_GO_E4_PL_Q1S_PATCH_OR_COVARIANCE",
            "UNCLASSIFIED_E4_PL_Q1S_LOCAL_PLANAR_IDENTITY",
        }
