from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "docs"
    / "reference_cases"
    / "nonlinear_static_nonfollower_screen_manifest.json"
)
PROVENANCE = (
    ROOT
    / "reports"
    / "performance"
    / "nonlinear_static_nonfollower_screen_build_provenance.json"
)
RUNNER_EXECUTION_SHA256 = (
    "5764f1104f23272ca3103df50f1655c0aa6ca6701f930ee324313bd10e752d13"
)
RUNNER_NORMALIZED_LF_SHA256 = (
    "865f5a26c1010d649a6e070426dac5a2953d48a7214e3d7aba4d94f6df599164"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_with_lf(path: Path) -> str:
    normalized = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def test_nonfollower_screen_manifest_freezes_registered_contract() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["experiment"] == "nonfollower_shared_validation_scope_screen"
    assert manifest["execution"]["performance_pairs"] == 3
    assert manifest["execution"]["alternating_order"] is True
    assert manifest["execution"]["serial"] is True
    assert manifest["convergence_case_ids"] == []
    assert [case["id"] for case in manifest["performance_cases"]] == [
        "easy_elastic_shell_control",
        "large_deflection_shell_holdout",
        "plastic_s3_reversal_holdout",
        "prescribed_mpc_beam_holdout",
    ]
    assert manifest["screen_acceptance"] == {
        "case_reduction_fraction": 0.05,
        "minimum_improved_case_count": 2,
        "aggregate_reduction_fraction": 0.05,
        "maximum_case_regression_fraction": 0.05,
        "physical_equivalence_required": True,
        "work_equivalence_required": True,
    }

    contract = manifest["screen_contract"]
    for path_key, sha_key in (
        ("parent_gate", "parent_gate_sha256"),
        ("runner", "runner_sha256"),
        ("adjudicator", "adjudicator_sha256"),
    ):
        path = ROOT / contract[path_key]
        assert path.is_file()
        if path_key == "runner":
            # The frozen Windows runner contained mixed line endings. Preserve
            # its exact execution hash while binding the portable LF content
            # separately so Linux can verify the same source semantics.
            assert contract[sha_key] == RUNNER_EXECUTION_SHA256
            assert _sha256_with_lf(path) == RUNNER_NORMALIZED_LF_SHA256
        else:
            assert contract[sha_key] == _sha256(path)


def test_nonfollower_screen_provenance_matches_manifest_identity() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))

    assert provenance["baseline_revision"] == manifest["baseline_revision"]
    assert provenance["candidate_revision"] == manifest["candidate_revision"]
    assert provenance["baseline_tree"] == manifest["source_trees"]["baseline"]
    assert provenance["candidate_tree"] == manifest["source_trees"]["candidate"]
    assert provenance["baseline_wheel_sha256"] == (
        "4512f1172f446922272fdb6e34f77175755351f7c91fc9ca2bddacc30623792c"
    )
    assert provenance["candidate_wheel_sha256"] == (
        "562585e4107847e9cfb4757c7e1c84ca3cad9b01d9a0710cc05d16c29d3f84e1"
    )
