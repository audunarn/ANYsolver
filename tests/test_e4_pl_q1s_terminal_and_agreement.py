from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs/reference_cases"


def _unique(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError(key)
        result[key] = value
    return result


def _canonical(value: object) -> bytes:
    return (json.dumps(value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()


def _load(name: str) -> tuple[dict[str, object], bytes]:
    path = CASES / name
    assert path.is_file(), f"registered evidence absent: {name}"
    raw = path.read_bytes()
    value = json.loads(raw.decode(), object_pairs_hook=_unique, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    assert raw == _canonical(value)
    return value, raw


def test_q1s_evidence_terminal_and_cross_implementation_contract() -> None:
    reference, reference_raw = _load("e4_pl_q1s_reference_raw.json")
    oracle, oracle_raw = _load("e4_pl_q1s_oracle_raw.json")
    agreement, agreement_raw = _load("e4_pl_q1s_agreement.json")
    output, _output_raw = _load("e4_pl_q1s_output.json")
    payload = reference["certificate_payload"]
    assert payload == oracle["certificate_payload"] == output["certificate_payload"]
    payload_raw = _canonical(payload)
    payload_sha = hashlib.sha256(payload_raw).hexdigest().upper()
    assert reference["certificate_payload_sha256"] == oracle["certificate_payload_sha256"] == payload_sha
    assert set(agreement) == {
        "byte_identical_certificate_payload", "candidate_id", "certificate_payload_bytes",
        "certificate_payload_sha256", "execution_authority_sha256", "execution_contract_sha256",
        "oracle", "reference", "schema", "study_id", "terminal",
    }
    assert agreement["schema"] == "anysolver.s4.e4-pl-q1s-agreement-v1"
    assert agreement["byte_identical_certificate_payload"] is True
    assert agreement["certificate_payload_bytes"] == len(payload_raw)
    assert agreement["certificate_payload_sha256"] == payload_sha
    for key, raw, implementation_id in (
        ("reference", reference_raw, "Q1S_REFERENCE_INDEPENDENT"),
        ("oracle", oracle_raw, "Q1S_ORACLE_INDEPENDENT"),
    ):
        row = agreement[key]
        assert set(row) == {"bytes", "deterministic", "implementation_id", "run1_sha256", "run2_sha256", "sha256"}
        digest = hashlib.sha256(raw).hexdigest().upper()
        assert row == {
            "bytes": len(raw),
            "deterministic": True,
            "implementation_id": implementation_id,
            "run1_sha256": digest,
            "run2_sha256": digest,
            "sha256": digest,
        }
    assert set(output) == {
        "agreement_sha256", "candidate_id", "certificate_payload", "certificate_payload_sha256",
        "classification", "execution_authority_sha256", "execution_contract_sha256",
        "production", "schema", "study_id",
    }
    assert output["schema"] == "anysolver.s4.e4-pl-q1s-output-v1"
    assert output["agreement_sha256"] == hashlib.sha256(agreement_raw).hexdigest().upper()
    classification = payload["classification"]
    assert set(classification) == {"inconclusive", "production", "q1b_execution", "terminal"}
    assert classification["production"] == output["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert classification["q1b_execution"] == "UNAUTHORIZED"
    terminal = classification["terminal"]
    assert terminal == agreement["terminal"] == output["classification"]
    frame_failed = not all(payload["frame_and_fields"].values())
    local_failed = not all(
        payload["local_algebra"][key]
        for key in (
            "all_38_field_blocks_invertible", "all_condensed_rank_18",
            "all_mixed_condensed_equalities_exact", "all_psd",
            "all_six_rigid_actions_exact_zero", "all_symmetric",
        )
    )
    patch_failed = not all(payload["global_supports"].values()) or not all(
        payload["recovery"][key]
        for key in (
            "all_224_compatible_fields", "all_224_independent_fields",
            "all_224_physical_resultants", "all_numerical_fields_separate",
        )
    ) or any(
        not all(row[section].values())
        for row in payload["case_certificates"]
        for section in ("patches", "recovery", "global_support")
        if not (section == "recovery" and "station_count" in row[section])
    ) or any(
        not all(value for key, value in row["recovery"].items() if key != "station_count")
        for row in payload["case_certificates"]
    )
    unresolved = payload["local_algebra"]["unresolved_at_1024"] or any(
        row["status"] == "UNCLASSIFIED" for row in payload["case_certificates"]
    )
    expected = (
        "NO_GO_E4_PL_Q1S_FRAME_IDENTITY" if frame_failed else
        "NO_GO_E4_PL_Q1S_LOCAL_ALGEBRA" if local_failed else
        "NO_GO_E4_PL_Q1S_PATCH_OR_COVARIANCE" if patch_failed else
        "UNCLASSIFIED_E4_PL_Q1S_LOCAL_PLANAR_IDENTITY" if unresolved else
        "PROVISIONAL_GO_E4_PL_Q1S_Q1B_PLAN"
    )
    assert terminal == expected
    assert classification["inconclusive"] is (terminal == "UNCLASSIFIED_E4_PL_Q1S_LOCAL_PLANAR_IDENTITY")
