"""Verify same-action work reconstructed from physical trace stations."""

import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_shell_trace_action import (
    evaluate, thickness_mean_and_director,
)


ROOT = Path(__file__).resolve().parents[1] / "docs" / "agent_plans"


def test_thickness_chord_recovers_independent_rigid_section_motion():
    translation = np.array((.003, -.004, .005))
    rotation = np.array((.07, -.03, .11))
    thickness = .035
    top = translation + np.cross(rotation, (0., 0., thickness/2))
    bottom = translation + np.cross(rotation, (0., 0., -thickness/2))
    mid, director = thickness_mean_and_director(top, bottom, thickness)
    np.testing.assert_allclose(mid, translation, rtol=0., atol=1e-16)
    np.testing.assert_allclose(director, rotation[:2], rtol=0., atol=1e-15)


def test_station_trace_reproduces_saved_component_work():
    result = evaluate(ROOT / "B3_E4_F03_C1_MATERIAL_LINE_P0_SOLID_RECON_DEV_V1.json")
    prior = json.loads((ROOT / "B3_E4_F03_C1_MATERIAL_LINE_SAME_ACTION_DEV_V1.json").read_text())
    assert result["solid_unit_field_count"] == 24
    for label, case in result["cases"].items():
        assert len(case["intervals"]) == 4
        assert [item["x_m"] for item in case["fixed_distance_probes"]] == [
            .5, .75, .9, .95]
        for item in case["fixed_distance_probes"]:
            assert np.isfinite(item["translation_difference_m"]).all()
            assert np.isfinite(item["director_rotation_difference_rad"]).all()
        np.testing.assert_allclose(
            case["solid_shell_action_work_J"],
            prior["cases"][label]["solid_shell_action_only_work_J"],
            rtol=5e-10, atol=1e-11,
        )
        np.testing.assert_allclose(
            case["native_shell_action_work_J"],
            prior["cases"][label]["native_shell_action_only_work_J"],
            rtol=1e-11, atol=1e-12,
        )
        assert case["native_shell_equilibrium_ratio"] < 1e-9
