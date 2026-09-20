from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


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
    physical = {"family_checks": {"completed": True}}
    work = {"assembly_calls": 4}
    physical_sha256 = hashlib.sha256(
        json.dumps(physical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    work_sha256 = hashlib.sha256(
        json.dumps(work, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    sample = {
        "ok": True,
        "status": "completed",
        "work": work,
        "physical": physical,
        "physical_sha256": physical_sha256,
        "identity": {"anysolver_module": "baseline-site/anysolver/__init__.py"},
        "complete_route_wall_seconds": 1.0,
        "solver_seconds": 0.9,
        "timing_repetitions": {
            "count": 1,
            "aggregation": "median",
            "route_seconds": [1.0],
            "solver_seconds": [0.9],
            "physical_sha256": physical_sha256,
            "work_sha256": work_sha256,
            "physical_match": True,
            "work_match": True,
        },
    }
    candidate = copy.deepcopy(sample)
    candidate["identity"]["anysolver_module"] = "candidate-site/anysolver/__init__.py"
    candidate["complete_route_wall_seconds"] = 0.8
    candidate["solver_seconds"] = 0.7
    candidate["timing_repetitions"]["route_seconds"] = [0.8]
    candidate["timing_repetitions"]["solver_seconds"] = [0.7]
    return {
        "pair": number,
        "order": ["baseline", "candidate"] if number % 2 else ["candidate", "baseline"],
        "baseline": copy.deepcopy(sample),
        "candidate": candidate,
        "physical_comparison": _comparison(),
    }


def test_component_requires_registered_reduction_and_exact_work() -> None:
    module = _load()
    gate = {
        "environment": {
            "thread_environment": {
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "NUMBA_NUM_THREADS": "1",
            }
        },
        "component_screen": {
            "case_id": "plastic_s3_reversal_holdout",
            "performance_pairs": 3,
            "minimum_route_reduction_fraction": 0.15,
        }
    }
    manifest = {
        "execution_mode": "component_screen",
        "baseline_revision": "base",
        "candidate_revision": "candidate",
        "source_trees": {"baseline": "base-tree", "candidate": "candidate-tree"},
        "wheel_sha256": {"baseline": "base-wheel", "candidate": "candidate-wheel"},
        "execution": {
            "numerical_threads": 1,
            "performance_pairs": 3,
            "serial": True,
            "alternating_order": True,
            "warmups_per_sample": 1,
        },
        "resource_limits": {"per_solve_timeout_seconds": 900},
        "performance_cases": [{"id": "plastic_s3_reversal_holdout"}],
        "required_regressions": ["test-a"],
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
            "manifest_sha256": "manifest-hash",
            "runner_sha256": "runner-hash",
            "thread_environment": gate["environment"]["thread_environment"],
            "installed_sites": {
                "baseline": {"site": "baseline-site"},
                "candidate": {"site": "candidate-site"},
            },
        },
        "resource_limits": manifest["resource_limits"],
        "performance": {
            "plastic_s3_reversal_holdout": {
                "spec": manifest["performance_cases"][0],
                "pairs": pairs,
                "summary": {
                    "baseline_median_seconds": 1.0,
                    "candidate_median_seconds": 0.8,
                    "median_reduction_fraction": (1.0 - 0.8) / 1.0,
                },
            }
        },
        "convergence": {},
        "installed_regressions": {
            "ok": True,
            "exit_code": 0,
            "tests": ["test-a"],
            "installed_site": "candidate-site",
        },
        "failures": [],
    }
    accepted = module.adjudicate(
        raw,
        gate,
        manifest,
        "component",
        manifest_sha256="manifest-hash",
        runner_sha256="runner-hash",
    )
    assert accepted["decision"]["advance"] is True

    pairs[0]["candidate"]["work"] = {"assembly_calls": 5}
    pairs[0]["candidate"]["timing_repetitions"]["work_sha256"] = hashlib.sha256(
        json.dumps(
            pairs[0]["candidate"]["work"],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    rejected = module.adjudicate(
        raw,
        gate,
        manifest,
        "component",
        manifest_sha256="manifest-hash",
        runner_sha256="runner-hash",
    )
    assert rejected["decision"]["advance"] is False
    assert rejected["decision"]["completeness"] == "FAIL"

    tampered = copy.deepcopy(raw)
    tampered["performance"]["plastic_s3_reversal_holdout"]["summary"][
        "candidate_median_seconds"
    ] = 0.1
    with pytest.raises(ValueError, match="summary differs"):
        module.adjudicate(
            tampered,
            gate,
            manifest,
            "component",
            manifest_sha256="manifest-hash",
            runner_sha256="runner-hash",
        )


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
