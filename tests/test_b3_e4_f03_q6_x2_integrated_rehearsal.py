"""Durable-case boundary for the unregistered integrated rehearsal."""

import json
from pathlib import Path

import pytest

from scripts._b3_e4_f03_qp_h_contract import validate_case_payload
from scripts.b3_e4_f03_q6_x2_integrated_rehearsal import _write_new


_SAVED_X2 = (Path(__file__).parents[1] / "docs" / "agent_plans" /
             "B3_GE_E4_PL_G0_F03_QP_NESTED_X2_Q6_20260923.json")


def test_physical_case_is_validated_after_json_tuple_conversion(tmp_path):
    row = json.loads(_SAVED_X2.read_text(encoding="utf-8"))
    row["x"] = tuple(row["x"])
    row["y"] = tuple(row["y"])
    row["station_intervals"] = tuple(tuple(pair) for pair in
                                     row["station_intervals"])
    with pytest.raises(ValueError, match="topology or identity"):
        validate_case_payload("X2", row)
    path = tmp_path / "physical.json"
    durable = _write_new(path, row)
    assert path.read_bytes() == durable
    assert validate_case_payload("X2", json.loads(durable)).free_state.size == 5890
    with pytest.raises(FileExistsError):
        _write_new(path, row)
