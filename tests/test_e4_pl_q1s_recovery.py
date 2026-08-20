from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_PATHS = [
    ROOT / "docs/reference_cases/e4_pl_q1s_reference_raw.json",
    ROOT / "docs/reference_cases/e4_pl_q1s_oracle_raw.json",
]


def _unique(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError(key)
        result[key] = value
    return result


def _payload() -> dict[str, object]:
    payloads = []
    for path in RAW_PATHS:
        assert path.is_file(), f"registered output absent: {path.name}"
        wrapper = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
        payloads.append(wrapper["certificate_payload"])
    assert payloads[0] == payloads[1]
    return payloads[0]


def test_q1s_all_224_station_recovery_and_numerical_separation() -> None:
    payload = _payload()
    recovery = payload["recovery"]
    assert set(recovery) == {
        "all_224_compatible_fields", "all_224_independent_fields",
        "all_224_physical_resultants", "all_numerical_fields_separate",
        "numerical_fields_excluded", "physical_resultants",
    }
    assert recovery["physical_resultants"] == ["N", "M", "Q"]
    assert recovery["numerical_fields_excluded"] == [
        "PL_CONSTRAINT",
        "PL_MULTIPLIER",
        "PL_COMPLIANCE_ENERGY",
        "RESIDUAL_MODE_COORDINATE",
        "RESIDUAL_MODE_ENERGY",
        "RESIDUAL_MODE_RESIDUAL",
        "RESIDUAL_MODE_TANGENT",
    ]
    assert all(
        isinstance(recovery[key], bool)
        for key in (
            "all_224_compatible_fields", "all_224_independent_fields",
            "all_224_physical_resultants", "all_numerical_fields_separate",
        )
    )
    station_ids: list[str] = []
    for row in payload["case_certificates"]:
        station_ids.extend(row["gauss_station_ids"])
        certificate = row["recovery"]
        assert set(certificate) == {
            "compatible_all_exact", "independent_all_exact", "physical_resultants_all_exact",
            "numerical_separate", "station_count",
        }
        assert certificate["station_count"] == 4
        assert all(isinstance(certificate[key], bool) for key in set(certificate) - {"station_count"})
        patches = row["patches"]
        assert set(patches) == {"membrane", "bending", "shear", "combined", "six_rigid_all_exact"}
        assert all(isinstance(value, bool) for value in patches.values())
    assert len(station_ids) == 224 and len(set(station_ids)) == 224
    passed = all(
        recovery[key]
        for key in (
            "all_224_compatible_fields", "all_224_independent_fields",
            "all_224_physical_resultants", "all_numerical_fields_separate",
        )
    )
    if not passed:
        assert payload["classification"]["terminal"] in {
            "NO_GO_E4_PL_Q1S_PATCH_OR_COVARIANCE",
            "UNCLASSIFIED_E4_PL_Q1S_LOCAL_PLANAR_IDENTITY",
        }
