"""Cross-check pure and mixed action work against saved component results."""

import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_pure_action_modes import evaluate


ROOT = Path(__file__).resolve().parents[1] / "docs" / "agent_plans"


def test_pure_and_mixed_modes_reproduce_independent_fixed_dual_work():
    result = evaluate(ROOT / "B3_E4_F03_C1_MATERIAL_LINE_P0_SOLID_RECON_DEV_V1.json")
    prior = json.loads((ROOT / "B3_E4_F03_C1_COMPONENT_COMPLIANCE_DEV_V1.json").read_text())
    assert set(result["cases"]) == {
        "axial_Fx", "transverse_Fz", "torsion_Mx", "bending_My"}
    for case in result["cases"].values():
        assert len(case["intervals"]) == 4
        assert all(value > 0. for value in case["uniform_component_work_J"].values())
    names = {"solid_plate": "solid_shell", "solid_bar": "solid_bar",
             "native_E4": "native_shell", "native_B3": "native_bar"}
    for domain, record in result["saved_mixed_tip_fz_action"].items():
        np.testing.assert_allclose(
            record["total_work_J"],
            prior["cases"]["tip_fz"]["components"][names[domain]]["work_J"],
            rtol=1e-11, atol=1e-12,
        )
        np.testing.assert_allclose(
            sum(record["same_channel_work_J"].values()) +
            sum(record["cross_channel_work_J"].values()),
            record["total_work_J"], rtol=1e-10, atol=1e-12,
        )
