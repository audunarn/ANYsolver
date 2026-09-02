from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs" / "reference_cases" / "e4_pl_s3_v6n_lease_optimization_result.json"
EXTERNAL = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6n-lease-optimization-c1e2ad9"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_v6n_closeout_is_canonical_narrow_and_nonactivating() -> None:
    raw = RESULT.read_bytes()
    value = json.loads(raw)
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert value["terminal"] == "PROVISIONAL_GO_E4_PL_S3_V6N_MISSING_LEAF_COMPLETION"
    assert value["activation_authorized"] is False
    assert value["successor"]["full_81_record_rerun_forbidden"] is True
    assert value["successor"]["fresh_request_ids_required"] is True
    assert value["predecessor"]["completed_scientific_record_count"] == 69
    assert value["predecessor"]["missing_scientific_record_count"] == 12
    assert value["production_boundary"] == {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "qualified_q4_mechanics_changed": False,
    }


def test_v6n_equivalence_and_two_cycle_funnel_hashes() -> None:
    value = json.loads(RESULT.read_bytes())
    for record in value["equivalence"]:
        suffix = "n20" if record["record_id"].startswith("N20") else "n40"
        path = EXTERNAL / f"equivalence-{suffix}" / "diagnostic.json"
        assert path.stat().st_size == record["diagnostic_bytes"]
        assert _sha(path) == record["diagnostic_sha256"]
        assert record["exact_record_equality"] is True
    for record in value["repair_funnel"]:
        diagonal = record["record_id"].rsplit(":", 1)[1]
        first = EXTERNAL / f"optimized-profile-n80-{diagonal}-cycle1"
        second = EXTERNAL / f"optimized-profile-n80-{diagonal}-cycle2"
        first_diagnostic = first / "diagnostic.json"
        second_diagnostic = second / "diagnostic.json"
        assert first_diagnostic.read_bytes() == second_diagnostic.read_bytes()
        assert first_diagnostic.stat().st_size == record["diagnostic_bytes"]
        assert _sha(first_diagnostic) == record["diagnostic_sha256"]
        assert _sha(first / "bounded-result.json") == record["cycle_1_result_sha256"]
        assert _sha(second / "bounded-result.json") == record["cycle_2_result_sha256"]


def test_v6n_candidate_and_ledger_bindings() -> None:
    value = json.loads(RESULT.read_bytes())
    archive = EXTERNAL / "candidate-source.tar"
    assert archive.stat().st_size == value["candidate"]["archive_bytes"]
    assert _sha(archive) == value["candidate"]["archive_sha256"]
    ledger = Path(r"C:\Github\.resource-manager\ledger.md")
    assert ledger.stat().st_size == value["resource_ledger"]["after_bytes"]
    assert _sha(ledger) == value["resource_ledger"]["after_sha256"]
