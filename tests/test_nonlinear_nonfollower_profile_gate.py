from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = (
    ROOT
    / "docs"
    / "reference_cases"
    / "nonlinear_static_nonfollower_profile_gate.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_nonfollower_profile_gate_is_bound_before_product_work() -> None:
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    bound = gate["bound_inputs"]

    for path_key, hash_key in (
        ("representative_manifest", "representative_manifest_sha256"),
        ("build_provenance", "build_provenance_sha256"),
        ("campaign_runner", "campaign_runner_sha256"),
        ("profile_runner", "profile_runner_sha256"),
    ):
        assert _sha256(ROOT / bound[path_key]) == bound[hash_key]

    spec = importlib.util.spec_from_file_location(
        "registered_representative_runner", ROOT / bound["campaign_runner"]
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (
        hashlib.sha256(
            inspect.getsource(module._build_case).encode("utf-8")
        ).hexdigest()
        == bound["case_builder_sha256"]
    )


def test_nonfollower_profile_gate_preserves_formal_acceptance() -> None:
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    inventory = gate["inventory"]
    assert inventory["profile_case_ids"] == [
        "easy_elastic_shell_control",
        "large_deflection_shell_holdout",
        "plastic_s3_reversal_holdout",
        "prescribed_mpc_beam_holdout",
    ]
    assert inventory["excluded_target_case_id"] not in inventory[
        "profile_case_ids"
    ]
    assert gate["hotspot_selection"]["required_case_reach"] == 2
    assert gate["implementation_screen"]["performance_pairs"] == 3
    assert gate["formal_gate"]["performance_pairs"] == 7
    assert (
        gate["formal_gate"]["representative_median_reduction_fraction"]
        == 0.10
    )
    assert gate["formal_gate"]["maximum_case_regression_fraction"] == 0.05
    assert gate["formal_gate"]["criteria_change_after_observation"] is False
