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


def _sha256_with_lf(path: Path) -> str:
    normalized = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def test_nonfollower_profile_gate_is_bound_before_product_work() -> None:
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    bound = gate["bound_inputs"]

    portable_hashes = {
        "representative_manifest": (
            "ae2e0e3aef093203c32975819717f651569c3cacbba661be0a97f5ebf5bca071"
        ),
        "build_provenance": (
            "36cd87293626366464f0221d57e2dc33c9fdc3a165c6f0e7c71a103a07e024e2"
        ),
        "campaign_runner": (
            "865f5a26c1010d649a6e070426dac5a2953d48a7214e3d7aba4d94f6df599164"
        ),
        "profile_runner": (
            "20c75c455cbf3605fa4313bd0b3d49b74d7d4293b79e2d74fcfe3436bda72c8e"
        ),
    }
    execution_hashes = {
        "representative_manifest": (
            "ae2e0e3aef093203c32975819717f651569c3cacbba661be0a97f5ebf5bca071"
        ),
        "build_provenance": (
            "36cd87293626366464f0221d57e2dc33c9fdc3a165c6f0e7c71a103a07e024e2"
        ),
        "campaign_runner": (
            "5764f1104f23272ca3103df50f1655c0aa6ca6701f930ee324313bd10e752d13"
        ),
        "profile_runner": (
            "379fc4e9bbb2c705942f9a941b0ccc9ec3afe4f5a399ec15fbfe0a8feda72e77"
        ),
    }
    for path_key, hash_key in (
        ("representative_manifest", "representative_manifest_sha256"),
        ("build_provenance", "build_provenance_sha256"),
        ("campaign_runner", "campaign_runner_sha256"),
        ("profile_runner", "profile_runner_sha256"),
    ):
        path = ROOT / bound[path_key]
        assert bound[hash_key] == execution_hashes[path_key]
        assert _sha256_with_lf(path) == portable_hashes[path_key]

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
