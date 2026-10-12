"""Negative-evidence controls using the retained actual development fixture."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import pytest

from docs.d1_review_support.d1_radial_spatial_assessment import assess_saved_radial_spatial


def _saved_pose_record_bytes(raw):
    """The saved-pose record form the frozen evidence binds, whatever the
    checkout line endings are."""
    return raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def _saved_pose_record_sha256(path):
    """Exact saved-pose record binding, independent of checkout line endings."""
    return hashlib.sha256(_saved_pose_record_bytes(path.read_bytes())).hexdigest()


def records():
    support = Path(__file__).resolve().parents[1]/"docs/d1_review_support"
    paths = [support/name for name in (
        "d1_radial_nonmatching_swept_search_coupled_v8_20260930.json",
        "d1_radial_saved_physical_bins_v10_20260930.json",
        "d1_radial_saved_wrench_v9_20260930.json",
        "d1_radial_linear_saved_assessment_v1_20260930.json")]
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths], _saved_pose_record_sha256(paths[0])


def test_saved_pose_identity_binds_record_content_not_checkout_line_endings():
    data, identity = records()
    support = Path(__file__).resolve().parents[1]/"docs/d1_review_support"
    raw = (support/"d1_radial_nonmatching_swept_search_coupled_v8_20260930.json").read_bytes()
    flipped = raw.replace(b"\r\n", b"\n") if b"\r\n" in raw else raw.replace(b"\n", b"\r\n")
    assert hashlib.sha256(_saved_pose_record_bytes(flipped)).hexdigest() == identity
    assert hashlib.sha256(_saved_pose_record_bytes(raw)).hexdigest() == identity
    assert all(record["input_sha256"] == identity for record in data[1:3])


def test_residual_compliance_does_not_replace_reference_uncertainty():
    data, identity = records()
    result = assess_saved_radial_spatial(*data, input_sha256=identity)
    assert result.get("missing_or_invalid_evidence") is None
    assert result["remaining_gates"] == ["oracle_solution_uncertainty_assessed"]
    assert not result["development_checks_met"]


def test_reaction_compensation_cannot_hide_net_contact_wrench():
    data, identity = records()
    bad = deepcopy(data)
    bad[2]["rows"][-1]["physical_contact_wrench"][0] = .08*2e-6
    result = assess_saved_radial_spatial(*bad, input_sha256=identity)
    assert not result["gates"]["step2_action_reaction_force"]
    assert not result["development_checks_met"]


def test_other_pose_or_nonfinite_work_evidence_cannot_pass():
    data, identity = records()
    bad = deepcopy(data)
    bad[1]["input_sha256"] = "0"*64
    result = assess_saved_radial_spatial(*bad, input_sha256=identity)
    assert not result["development_checks_met"]
    assert "same saved pose" in result["missing_or_invalid_evidence"]
    bad = deepcopy(data)
    bad[2]["rows"][-1]["bodies"]["source"]["contact_conversion_max_scaled"] = float("nan")
    result = assess_saved_radial_spatial(*bad, input_sha256=identity)
    assert not result["gates"]["step2_reaction_and_work"]


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
@pytest.mark.parametrize("independent", [False, True])
def test_nonfinite_gap_cannot_be_clamped_into_zero_penetration(value, independent):
    data, identity = records()
    if independent:
        data[0]["independent_gap_lower_m"] = value
    else:
        data[0]["history"][-1]["contact"]["minimum_gap"] = value
    result = assess_saved_radial_spatial(*data, input_sha256=identity)
    assert not result["development_checks_met"]
    assert "finite physical gap" in result["missing_or_invalid_evidence"]


@pytest.mark.parametrize("field,value", [("origin_m", [0., 0., 0.]),
    ("force_scale_n", .8), ("moment_scale_nm", .8)])
def test_changed_wrench_scales_or_origin_are_not_accepted(field, value):
    data, identity = records()
    data[2]["rows"][-1][field] = value
    result = assess_saved_radial_spatial(*data, input_sha256=identity)
    assert not result["development_checks_met"]
    assert "registered wrench origin" in result["missing_or_invalid_evidence"]


def test_scalar_reference_moment_cannot_broadcast_into_complete_evidence():
    data, identity = records()
    data[0]["numerical_reference_pressure_observables"]["total"]["moment_nm"] = 0.
    result = assess_saved_radial_spatial(*data, input_sha256=identity)
    assert not result["development_checks_met"]
    assert "three-component" in result["missing_or_invalid_evidence"]
