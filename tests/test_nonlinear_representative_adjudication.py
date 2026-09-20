from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_follower_correction_requires_exact_physical_equality() -> None:
    module = _load(
        ROOT / "scripts/adjudicate_nonlinear_representative.py", "adjudicator"
    )
    pair = {
        "baseline": {
            "physical": {
                "family_checks": {
                    "completed": True,
                    "current_external_load": False,
                }
            }
        },
        "candidate": {
            "physical": {
                "family_checks": {
                    "completed": True,
                    "current_external_load": True,
                }
            }
        },
        "physical_comparison": {
            "max_displacement_difference": 1.0,
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
        },
    }
    with pytest.raises(ValueError, match="exact physical equality"):
        module._require_follower_compatibility(pair)


def test_adjudicator_rejects_unbound_campaign_runner() -> None:
    module = _load(
        ROOT / "scripts/adjudicate_nonlinear_representative.py", "adjudicator_identity"
    )
    with pytest.raises(RuntimeError, match="campaign runner SHA-256 mismatch"):
        module._load_runner("0" * 64)
