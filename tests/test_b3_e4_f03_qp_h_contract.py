"""Bounded adversarial checks for the prospective Q6 evidence schema."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts._b3_e4_f03_qp_h_contract import (
    minimum_inverse_bytes, trace_for_case, validate_case_payload,
    validate_spatial_payload,
)


_X2 = (Path(__file__).parents[1] / "docs" / "agent_plans" /
       "B3_GE_E4_PL_G0_F03_QP_NESTED_X2_Q6_20260923.json")
_X2_SPATIAL = (Path(__file__).parents[1] / "docs" / "agent_plans" /
       "B3_GE_E4_PL_G0_F03_QP_NESTED_X2_SPATIAL_V3_20260924.json")


def test_saved_x2_has_the_declared_full_case_shape():
    row = json.loads(_X2.read_text(encoding="utf-8"))
    checked = validate_case_payload("X2", row)
    assert checked.free_state.size == 5890
    assert checked.functional.coefficients.shape[0] == 25
    assert len(trace_for_case("X2").station_intervals()) == 25
    assert not checked.free_state.flags.writeable
    assert not checked.root_multiplier.flags.writeable
    with pytest.raises(ValueError):
        checked.free_state[0] = 0.
    assert minimum_inverse_bytes("X0") > 64 * 1024**2


@pytest.mark.parametrize("damage", ("state", "cosine", "grid", "crossings"))
def test_tampered_case_cannot_pass_shape_or_identity(damage):
    row = json.loads(_X2.read_text(encoding="utf-8"))
    if damage == "state":
        row["free_state"][0] += 1.
    elif damage == "cosine":
        row["functional"]["cosine"] = [0., float("nan"), 0.]
    elif damage == "grid":
        row["x_hex"][2] = row["x_hex"][3]
    else:
        row["numerical"]["exact_interior_crossings"] -= 1
    with pytest.raises(ValueError):
        validate_case_payload("X2", row)


def test_spatial_schema_rejects_stale_case_and_numerical_failure():
    case_bytes = _X2.read_bytes()
    digest = hashlib.sha256(case_bytes).hexdigest()
    row = json.loads(_X2_SPATIAL.read_text(encoding="utf-8"))
    row.update(status="UNREGISTERED_Q6_SPATIAL_AUDIT", grid="x2",
               input_sha256=digest)
    assert max(validate_spatial_payload("X2", digest, row).values()) < 2e-9
    stale = copy.deepcopy(row)
    stale["input_sha256"] = "0"*64
    with pytest.raises(ValueError):
        validate_spatial_payload("X2", digest, stale)
    failed = copy.deepcopy(row)
    failed["numerical"]["maximum_spatial_work_defect_scaled"] = 2.1e-9
    with pytest.raises(ArithmeticError):
        validate_spatial_payload("X2", digest, failed)
    incomplete = copy.deepcopy(row)
    del incomplete["spatial_work"]
    with pytest.raises(ValueError):
        validate_spatial_payload("X2", digest, incomplete)


def test_fixed_grid_identity_rejects_equal_count_coordinate_change(monkeypatch):
    import scripts._b3_e4_f03_qp_h_contract as contract
    original = contract.refined_x2()
    monkeypatch.setattr(contract, "refined_x2",
                        lambda: original[:3] + (original[3] + 1e-4,) + original[4:])
    with pytest.raises(ArithmeticError, match="frozen Q6"):
        contract.trace_for_case("X2")


def test_case_shape_rejects_oversized_functional_before_construction():
    row = json.loads(_X2.read_text(encoding="utf-8"))
    row["functional"]["coefficients"].append(row["functional"]["coefficients"][0])
    with pytest.raises(ValueError, match="bounded Q6 functional shape"):
        validate_case_payload("X2", row)
