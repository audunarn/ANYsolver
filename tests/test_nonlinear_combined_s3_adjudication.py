from __future__ import annotations

import importlib.util
import copy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts/adjudicate_nonlinear_combined_s3.py"
    spec = importlib.util.spec_from_file_location("combined_s3_adjudicator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _comparison(*, numerical_match: bool = True) -> dict[str, object]:
    return {
        "numerical_match": numerical_match,
        "max_displacement_difference": 0.0,
        "max_reaction_difference": 0.0,
        "max_plastic_state_difference": 0.0,
        "max_step_load_factor_difference": 0.0,
        "max_step_displacement_norm_difference": 0.0,
        "max_step_plastic_strain_difference": 0.0,
        "max_state_observable_difference": 0.0,
        "max_snapshot_displacement_difference": 0.0,
        "max_snapshot_state_difference": 0.0,
        "same_reaction_inventory": True,
        "same_step_path": True,
        "same_state_inventory": True,
        "same_snapshot_path": True,
        "same_snapshot_state_inventory": True,
    }


def _pair(number: int = 1) -> dict[str, object]:
    sample = {
        "ok": True,
        "status": "completed",
        "work": {"assembly_calls": 4},
        "physical": {"family_checks": {"completed": True}},
        "complete_route_wall_seconds": 1.0,
    }
    return {
        "pair": number,
        "baseline": copy.deepcopy(sample),
        "candidate": copy.deepcopy(sample),
        "physical_comparison": _comparison(),
    }


def test_component_requires_registered_reduction_and_exact_work() -> None:
    module = _load()
    gate = {
        "component_screen": {
            "case_id": "plastic_s3_reversal_holdout",
            "performance_pairs": 3,
            "minimum_route_reduction_fraction": 0.15,
        }
    }
    manifest = {
        "baseline_revision": "base",
        "candidate_revision": "candidate",
        "source_trees": {"baseline": "base-tree", "candidate": "candidate-tree"},
        "wheel_sha256": {"baseline": "base-wheel", "candidate": "candidate-wheel"},
    }
    pairs = [_pair(number) for number in (1, 2, 3)]
    raw = {
        "identity": {
            "baseline_revision": "base",
            "candidate_revision": "candidate",
            "baseline_tree": "base-tree",
            "candidate_tree": "candidate-tree",
            "baseline_wheel_sha256": "base-wheel",
            "candidate_wheel_sha256": "candidate-wheel",
        },
        "performance": {
            "plastic_s3_reversal_holdout": {
                "pairs": pairs,
                "summary": {
                    "baseline_median_seconds": 1.0,
                    "candidate_median_seconds": 0.8,
                    "median_reduction_fraction": 0.2,
                },
            }
        },
        "installed_regressions": {"ok": True},
        "failures": [],
    }
    accepted = module.adjudicate(raw, gate, manifest, "component")
    assert accepted["decision"]["advance"] is True

    pairs[0]["candidate"]["work"] = {"assembly_calls": 5}
    rejected = module.adjudicate(raw, gate, manifest, "component")
    assert rejected["decision"]["advance"] is False
    assert rejected["decision"]["completeness"] == "FAIL"


def test_follower_compatibility_requires_zero_physical_differences() -> None:
    module = _load()
    pair = _pair()
    pair["baseline"]["physical"]["family_checks"] = {
        "completed": True,
        "current_external_load": False,
    }
    pair["candidate"]["physical"]["family_checks"] = {
        "completed": True,
        "current_external_load": True,
    }
    pair["physical_comparison"] = _comparison(numerical_match=False)
    assert module._exact_follower_compatibility(pair) is True
    pair["physical_comparison"]["max_reaction_difference"] = 1.0
    assert module._exact_follower_compatibility(pair) is False
