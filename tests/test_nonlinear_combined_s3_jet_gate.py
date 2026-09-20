from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = (
    ROOT
    / "docs"
    / "reference_cases"
    / "nonlinear_static_combined_s3_jet_gate.json"
)
CORRECTION = (
    ROOT
    / "docs"
    / "reference_cases"
    / "nonlinear_static_combined_s3_harness_correction_v3.json"
)


def _sha256_with_lf(path: Path) -> str:
    normalized = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def test_combined_s3_gate_binds_inputs_before_product_work() -> None:
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    assert gate["schema"] == "anysolver.nonlinear_static.combined_s3_jet_gate"
    assert gate["version"] == 1
    assert gate["authority"]["criteria_change_after_product_edit"] is False

    assert gate["accepted_main"] == {
        "revision": "26d35bcad1b5ac6ae693c09d283cc3a918aa650c",
        "tree": "26b2e4002d16b22b0e8d90a879e68c94b68ddccf",
        "wheel_sha256": (
            "6879ca073bbcc9e4daf4a715ec2f3f360a433e2fffd4539486d2e8fd8a4d3a1a"
        ),
        "wheel_build": (
            "git archive of the registered revision followed by "
            "python -m build --wheel --no-isolation"
        ),
    }
    follower = gate["retained_follower_parent"]
    assert follower["product_revision"] == (
        "b67517d16a589ebb397d1ef55441467ee0e62275"
    )
    assert follower["product_tree"] == (
        "c8515ee19b6924be7c17ca9490452f1d81f5f31b"
    )
    assert follower["wheel_sha256"] == (
        "ce891bf14073a02313d5508047df22f13ddfcebd70ff4e77f65e33709b132884"
    )

    bound = gate["bound_inputs"]
    portable_hashes = {
        "representative_manifest": (
            "ae2e0e3aef093203c32975819717f651569c3cacbba661be0a97f5ebf5bca071"
        ),
        "runner": (
            "865f5a26c1010d649a6e070426dac5a2953d48a7214e3d7aba4d94f6df599164"
        ),
        "reference_adjudicator": (
            "0cb719dc393df0eb5b06c3e39069915fde5b0911fac75b9316c6f5984e30e365"
        ),
    }
    for key, expected in portable_hashes.items():
        path = ROOT / bound[key]
        assert path.is_file()
        observed = _sha256_with_lf(path)
        if key != "runner":
            assert observed == expected
            continue
        correction = json.loads(CORRECTION.read_text(encoding="utf-8"))
        assert correction["prior_attempts"]["v1"]["performance_samples_recorded"] == 0
        assert correction["prior_attempts"]["v2"]["canonical_campaign_executed"] is False
        assert correction["correction"]["old_runner_lf_sha256"] == expected
        assert correction["correction"]["new_runner_lf_sha256"] == observed
        assert all(correction["unchanged_authority"].values())


def test_combined_s3_gate_freezes_promotion_thresholds() -> None:
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    screen = gate["component_screen"]
    assert screen["performance_pairs"] == 3
    assert screen["minimum_route_reduction_fraction"] == 0.15
    assert screen["physical_equivalence_required"] is True
    assert screen["exact_solver_work_required"] is True

    formal = gate["formal_gate"]
    assert formal["performance_pairs"] == 7
    assert formal["mpc_complete_routes_per_sample"] == 25
    assert formal["minimum_representative_reduction_fraction"] == 0.10
    assert formal["minimum_plastic_s3_reduction_fraction"] == 0.15
    assert formal["minimum_follower_target_reduction_fraction"] == 0.10
    assert formal["maximum_case_regression_fraction"] == 0.05
    assert formal["armijo_requalification"] is False
    assert gate["terminal_rules"]["criteria_change_after_observation"] is False


def test_combined_s3_gate_limits_product_scope() -> None:
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    candidate = gate["candidate_definition"]
    assert candidate["file"] == "src/anysolver/e4_pl_s3_element.py"
    assert candidate["required_changes"] == [
        "direct scalar addition and reverse addition",
        "direct scalar subtraction and reverse subtraction",
        "direct scalar multiplication without zero-valued outer products",
        "direct scalar division after preserving variable and zero-divisor errors",
        "independently owned gradient and Hessian arrays in every scalar result",
    ]
    assert "in-place jet arithmetic" in candidate["excluded_changes"]
    assert "Numba jet kernels" in candidate["excluded_changes"]


def test_corrected_execution_manifests_bind_exact_inventories() -> None:
    component = json.loads(
        (
            ROOT
            / "docs/reference_cases/nonlinear_static_combined_s3_component_manifest_v2.json"
        ).read_text(encoding="utf-8")
    )
    formal = json.loads(
        (
            ROOT
            / "docs/reference_cases/nonlinear_static_combined_s3_formal_manifest_v2.json"
        ).read_text(encoding="utf-8")
    )
    candidate = "89bd4623a8ae0cb9c95317bdf31ac5fbd91a2e0f"
    candidate_tree = "e0d84314d0f84a7974d8b94934678a0cb66a9d76"
    candidate_wheel = (
        "301b91bf52cb224e0ea0c2e897e616f250b11cfa9ca5d9d6c9d4739de2f17c66"
    )
    for manifest in (component, formal):
        assert manifest["candidate_revision"] == candidate
        assert manifest["source_trees"]["candidate"] == candidate_tree
        assert manifest["wheel_sha256"]["candidate"] == candidate_wheel
        assert "tests/test_e4_pl_s3_jet_scalar_fastpath.py" in manifest[
            "required_regressions"
        ]
        assert any(
            "test_values_jacobian_and_hessian_match_directional_finite_differences"
            in item
            for item in manifest["required_regressions"]
        )
        assert any(
            "test_canonical_s3_restart_matches_the_ordered_two_stage_path" in item
            for item in manifest["required_regressions"]
        )

    assert component["execution_mode"] == "component_screen"
    assert [case["id"] for case in component["performance_cases"]] == [
        "plastic_s3_reversal_holdout"
    ]
    assert component["execution"]["performance_pairs"] == 3
    assert formal["execution_mode"] == "representative"
    assert len(formal["performance_cases"]) == 5
    assert formal["execution"]["performance_pairs"] == 7
