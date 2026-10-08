"""Check the fixed-dual physical/completion partition against saved work."""

import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_shell_completion_work import evaluate


ROOT = Path(__file__).resolve().parents[1] / "docs" / "agent_plans"


def test_completion_work_partitions_saved_fixed_dual_response():
    result = evaluate(ROOT / "B3_E4_F03_C1_MATERIAL_LINE_P0_SOLID_RECON_DEV_V1.json")
    prior = json.loads((ROOT / "B3_E4_F03_C1_MATERIAL_LINE_SAME_ACTION_DEV_V1.json").read_text())
    for label, case in result["cases"].items():
        np.testing.assert_allclose(
            case["total_action_work_J"],
            prior["cases"][label]["native_shell_action_only_work_J"],
            rtol=1e-11, atol=1e-12,
        )
        np.testing.assert_allclose(
            case["physical_operator_work_J"] +
            case["completion_operator_work_J"],
            case["total_action_work_J"],
            rtol=1e-10, atol=1e-12,
        )
        assert case["equilibrium_ratio"] < 1e-9
