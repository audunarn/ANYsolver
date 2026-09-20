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
        assert _sha256_with_lf(path) == expected


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
