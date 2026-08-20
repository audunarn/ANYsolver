from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _payload() -> dict[str, object]:
    values = []
    for name in ("e4_pl_q1t_reference_raw.json", "e4_pl_q1t_oracle_raw.json"):
        path = ROOT / "docs/reference_cases" / name
        assert path.is_file(), f"registered output absent: {name}"
        values.append(json.loads(path.read_text(encoding="utf-8"))["certificate_payload"])
    assert values[0] == values[1]
    return values[0]


def test_q1t_all_224_station_recovery_and_numerical_separation() -> None:
    payload = _payload()
    recovery = payload["recovery"]
    assert recovery["physical_resultants"] == ["N", "M", "Q"]
    assert recovery["numerical_fields_excluded"] == ["PL_CONSTRAINT", "PL_MULTIPLIER", "PL_COMPLIANCE_ENERGY", "RESIDUAL_MODE_COORDINATE", "RESIDUAL_MODE_ENERGY", "RESIDUAL_MODE_RESIDUAL", "RESIDUAL_MODE_TANGENT"]
    assert all(isinstance(recovery[key], bool) for key in ("all_224_compatible_fields", "all_224_independent_fields", "all_224_physical_resultants", "all_numerical_fields_separate"))
    stations: list[str] = []
    for row in payload["case_certificates"]:
        stations.extend(row["gauss_station_ids"])
        item = row["recovery"]
        assert item["station_count"] == 4
        assert all(isinstance(value, bool) for key, value in item.items() if key != "station_count")
        assert all(isinstance(value, bool) for value in row["patches"].values())
    assert len(stations) == len(set(stations)) == 224

