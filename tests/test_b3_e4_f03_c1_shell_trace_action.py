"""Verify same-action work reconstructed from physical trace stations."""

import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_shell_trace_action import evaluate


ROOT = Path(__file__).resolve().parents[1] / "docs" / "agent_plans"


def test_station_trace_reproduces_saved_component_work():
    result = evaluate(ROOT / "B3_E4_F03_C1_MATERIAL_LINE_P0_SOLID_RECON_DEV_V1.json")
    prior = json.loads((ROOT / "B3_E4_F03_C1_MATERIAL_LINE_SAME_ACTION_DEV_V1.json").read_text())
    assert result["solid_unit_field_count"] == 24
    for label, case in result["cases"].items():
        assert len(case["intervals"]) == 4
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
