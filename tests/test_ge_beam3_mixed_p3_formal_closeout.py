"""Strict closeout checks for the GE Beam3 P3 standalone opt-in gate."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference_cases"
EVIDENCE = REFERENCE / "ge_beam3_mixed_p3_formal_evidence.json"
REVIEW = REFERENCE / "ge_beam3_mixed_p3_formal_review.json"
STATUS = REFERENCE / "ge_beam3_mixed_p3_formal_status.json"
CONTRACT = REFERENCE / "ge_beam3_mixed_p3_formal_contract.json"

TERMINAL = "PROVISIONAL_GO_GE_BEAM3_STRAIGHT_STANDALONE_OPT_IN"
PACKAGE_TERMINAL = "ACCEPTED_GE_BEAM3_P3_PACKAGE_GATE"
STUDY = "study_ge_beam3.mixed_straight_optin_integration_v1"
CANDIDATE = "f63b2fc000c87003ae5c322dbd881e98f64b22ab"
CANDIDATE_TREE = "3402268699829119cc9f4abce711535323f84a4a"
IMPLEMENTATION_FREEZE = "d2545773c0b4bed321117d89f9c84ba5dc49b135"
H3 = "1e37e7e19d21694e06934dd2075ce1c938e20f17"
PACKAGE_AUTHORITY_COMMIT = "e85c8d558181e6fdd52a22008ea0911147abb0f9"
PERFORMANCE_AUTHORITY_COMMIT = "b843ba881eae78d0a349dd021ce1e7cf8bb567bf"

CLOSEOUT_PATHS = [
    "docs/reference_cases/ge_beam3_mixed_p3_formal_evidence.json",
    "docs/reference_cases/ge_beam3_mixed_p3_formal_review.json",
    "docs/reference_cases/ge_beam3_mixed_p3_formal_status.json",
    "tests/test_ge_beam3_mixed_p3_formal_closeout.py",
]
TERMINAL_PRECEDENCE = [
    "BLOCKED_GE_BEAM3_P3_BASELINE_OR_AUTHORITY",
    "BLOCKED_GE_BEAM3_P3_PROCESS_OR_EVIDENCE",
    "NO_GO_GE_BEAM3_P3_SELECTOR_OR_SERIALIZATION",
    "NO_GO_GE_BEAM3_P3_LINEAR_INTEGRATION",
    "NO_GO_GE_BEAM3_P3_PACKAGE_ISOLATION",
    "UNCLASSIFIED_GE_BEAM3_P3_PERFORMANCE",
    TERMINAL,
]
PRODUCTION_BOUNDARY = {
    "activation_authorized": False,
    "default_change_authorized": False,
    "ecosystem_exposure_authorized": False,
    "existing_b2_unchanged": True,
    "existing_b3_unchanged": True,
    "existing_beam_aliases_and_defaults_unchanged": True,
    "public_selector": "ge-beam3",
    "publication_authorized": False,
    "qualified_q4_unchanged": True,
    "qualified_s3_v2d_unchanged": True,
    "straight_standalone_opt_in_authorized": True,
}

REPO_INPUTS = {
    "docs/reference_cases/ge_beam3_mixed_p3_formal_contract.json": (
        6236,
        "642B49FD5B673B438E4DE37DBAE7D5D724FC893E5DBD6E753AAA7F34ED359727",
    ),
    "docs/reference_cases/ge_beam3_mixed_p3_formal_executor.py": (
        109745,
        "836A660C39CDA9F9E51632E2659AFBBA7D745746BDBF5720DAFDFFCBF5A175AD",
    ),
    "tests/test_ge_beam3_mixed_p3_formal_executor.py": (
        23156,
        "C2046020A28DF4D211028E129D203BA4C952C4CD0F8E2F49260125A3B208A44F",
    ),
    "docs/reference_cases/ge_beam3_mixed_p3_package_execution_authority.json": (
        8457,
        "94204D2B1318AE92A11D0FF9ACAF9A1FBAF220643272E5496EBAE12BA16E2096",
    ),
    "docs/reference_cases/ge_beam3_mixed_p3_package_execution_review.json": (
        478,
        "A24ABBF581632A008022962B9D05975C9127F7CD34AA3366053BC52FC36D59A0",
    ),
    "docs/reference_cases/ge_beam3_mixed_p3_performance_execution_authority.json": (
        10009,
        "DAA168BB1D42E9EFADB1D61E76DFCCD913A6C2072BEF50AFEA6D98C89683F7DF",
    ),
    "docs/reference_cases/ge_beam3_mixed_p3_performance_execution_review.json": (
        491,
        "8777EEA3DFAEB7DB71EABD74BD3EC17E654139B8499DDBB6F9DD8F30E5573B83",
    ),
}

EXTERNAL_INPUTS = {
    "external/ge-beam3-p3-formal-20260905/incident/package-cycle1-root-cause.json": (
        1693,
        "AEB6431DE2CCE7CDDBC166E747B1245C11C755BAEE03FA8F4752A87FD3B071C1",
    ),
    "external/ge-beam3-p3-formal-20260905-h2/incident/package-cycle2-root-cause.json": (
        2622,
        "5C37A9DAAF42168883ECCD5C837F1EBA5D8A3047A6B29FAC9CDA6412AC49BE74",
    ),
    "external/resource-manager/requests/245bb1e434c84b8a869ce5a141499e0e.json": (
        2680,
        "F763BD94FF034FF42FB6285055C2CC79CA59908B8F4683B939D89986E2425C65",
    ),
    "external/resource-manager/claims/245bb1e434c84b8a869ce5a141499e0e.json": (
        583,
        "838D26780D861C95AF88D416A2574D6AC95BC25EF27912670A28DE8A831AD25D",
    ),
    "external/resource-manager/attempts/50a1b4471d1f447c945fd7fea617b79d.json": (
        583,
        "838D26780D861C95AF88D416A2574D6AC95BC25EF27912670A28DE8A831AD25D",
    ),
    "external/resource-manager/receipts/245bb1e434c84b8a869ce5a141499e0e.json": (
        2221,
        "5987BDF602C5085196079CF2E7559D8BDC46CAEC7D4EE5CC91CF33E7A594DDDB",
    ),
    "external/ge-beam3-p3-formal-20260905-h3/canonical/package-result-245bb1e434c84b8a869ce5a141499e0e.json": (
        1696,
        "39187D9F144DB22BDB61C7E6C3932890C73338C32E601253F0EB634163CB3CB8",
    ),
    "external/ge-beam3-p3-formal-20260905-h3/package-work-50a1b4471d1f447c945fd7fea617b79d/gate/package-aggregate.json": (
        742,
        "D30D6BD15027E1A37ACF732DF87A53ECF7C7FD497A7BD15BF56B7AEC300F531C",
    ),
    "external/ge-beam3-p3-formal-20260905-h3/package-work-50a1b4471d1f447c945fd7fea617b79d/gate/wheel/anysolver-0.4.2-py3-none-any.whl": (
        1233936,
        "92A35F6214D629D56B2CB5EF3859A7A82875CF7D782DF96F650986D3B3EDDF02",
    ),
    "external/resource-manager/requests/1e14cc230fb74db185b031165a360dfa.json": (
        3635,
        "49D850EC42727E7FC8755795FBDD33F06DB9429B22FE78811B6616994880E692",
    ),
    "external/resource-manager/claims/1e14cc230fb74db185b031165a360dfa.json": (
        587,
        "296DBB4BC469383C98426CCBA73EA278D45660D7926298958E937F32314701C0",
    ),
    "external/resource-manager/attempts/d09e6b73508544a6bb553fe3514b7efc.json": (
        587,
        "296DBB4BC469383C98426CCBA73EA278D45660D7926298958E937F32314701C0",
    ),
    "external/resource-manager/receipts/1e14cc230fb74db185b031165a360dfa.json": (
        1979,
        "1DA020EF4D839FB585C1F80943DB4EBBABF0FBA57900B7B673FC9140D19A3892",
    ),
    "external/ge-beam3-p3-formal-20260905-h3/canonical/performance-result-1e14cc230fb74db185b031165a360dfa.json": (
        1437,
        "93640EB79ED1CB340C56C9C6E4C434320E3CBDF6CB7F4D045A5A9F0AA85FF990",
    ),
    "external/ge-beam3-p3-formal-20260905-h3/performance-work-d09e6b73508544a6bb553fe3514b7efc/gate/performance-aggregate.json": (
        2094,
        "20E6FE33300CFF6060DF50546253EE99E7D3A5C1073E258D597087F3B67BB1E2",
    ),
    "external/ge-beam3-p3-formal-20260905-h3/synthesis/final-synthesis-1.json": (
        3107,
        "7DFD5E272D39D7FE1BFE4C5A721A54FFB501DEB34AFAB05754E7A6B7559867DE",
    ),
    "external/ge-beam3-p3-formal-20260905-h3/synthesis/final-synthesis-2.json": (
        3107,
        "7DFD5E272D39D7FE1BFE4C5A721A54FFB501DEB34AFAB05754E7A6B7559867DE",
    ),
}


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON value: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _decode_strict(raw: bytes) -> object:
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )


def _canonical(path: Path) -> tuple[bytes, dict[str, object]]:
    raw = path.read_bytes()
    value = _decode_strict(raw)
    assert isinstance(value, dict)
    expected = (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    assert raw == expected
    return raw, value


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _record(path: str, size: int, sha256: str) -> dict[str, object]:
    return {"bytes": size, "path": path, "sha256": sha256}


def _git(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = {
        key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return subprocess.run(
        ["git", "-c", f"safe.directory={ROOT}", *arguments],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        check=False,
    )


def _git_text(*arguments: str) -> str:
    result = _git(*arguments)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    return result.stdout.decode("utf-8").strip()


def _assert_commit(
    commit: str,
    *,
    parent: str,
    tree: str,
    subject: str,
    paths: list[str],
) -> None:
    fields = _git_text("show", "-s", "--format=%H%n%T%n%P%n%s", commit).splitlines()
    assert fields == [commit, tree, parent, subject]
    actual_paths = _git_text(
        "diff-tree", "--no-commit-id", "--name-only", "-r", commit
    ).splitlines()
    assert actual_paths == paths


def _lookup(value: dict[str, object], path: str) -> object:
    current: object = value
    for key in path.split("."):
        assert isinstance(current, dict)
        current = current[key]
    return current


EXPECTED_IDENTITIES: dict[str, object] = {
    "archives.0.incident.sha256": "AEB6431DE2CCE7CDDBC166E747B1245C11C755BAEE03FA8F4752A87FD3B071C1",
    "archives.1.incident.sha256": "5C37A9DAAF42168883ECCD5C837F1EBA5D8A3047A6B29FAC9CDA6412AC49BE74",
    "authorities.package.commit": PACKAGE_AUTHORITY_COMMIT,
    "authorities.package.record.sha256": "94204D2B1318AE92A11D0FF9ACAF9A1FBAF220643272E5496EBAE12BA16E2096",
    "authorities.performance.commit": PERFORMANCE_AUTHORITY_COMMIT,
    "authorities.performance.record.sha256": "DAA168BB1D42E9EFADB1D61E76DFCCD913A6C2072BEF50AFEA6D98C89683F7DF",
    "candidate.commit": CANDIDATE,
    "candidate.tree": CANDIDATE_TREE,
    "executions.package.aggregate.sha256": "D30D6BD15027E1A37ACF732DF87A53ECF7C7FD497A7BD15BF56B7AEC300F531C",
    "executions.package.claim.sha256": "838D26780D861C95AF88D416A2574D6AC95BC25EF27912670A28DE8A831AD25D",
    "executions.package.receipt.sha256": "5987BDF602C5085196079CF2E7559D8BDC46CAEC7D4EE5CC91CF33E7A594DDDB",
    "executions.package.request.sha256": "F763BD94FF034FF42FB6285055C2CC79CA59908B8F4683B939D89986E2425C65",
    "executions.package.result.sha256": "39187D9F144DB22BDB61C7E6C3932890C73338C32E601253F0EB634163CB3CB8",
    "executions.package.wheel.sha256": "92A35F6214D629D56B2CB5EF3859A7A82875CF7D782DF96F650986D3B3EDDF02",
    "executions.performance.aggregate.sha256": "20E6FE33300CFF6060DF50546253EE99E7D3A5C1073E258D597087F3B67BB1E2",
    "executions.performance.claim.sha256": "296DBB4BC469383C98426CCBA73EA278D45660D7926298958E937F32314701C0",
    "executions.performance.receipt.sha256": "1DA020EF4D839FB585C1F80943DB4EBBABF0FBA57900B7B673FC9140D19A3892",
    "executions.performance.request.sha256": "49D850EC42727E7FC8755795FBDD33F06DB9429B22FE78811B6616994880E692",
    "executions.performance.result.sha256": "93640EB79ED1CB340C56C9C6E4C434320E3CBDF6CB7F4D045A5A9F0AA85FF990",
    "harness.commit": H3,
    "harness.tree": "fb0eab67907952374a998615a389e2b2c14a7a0a",
    "syntheses.0.sha256": "7DFD5E272D39D7FE1BFE4C5A721A54FFB501DEB34AFAB05754E7A6B7559867DE",
    "syntheses.1.sha256": "7DFD5E272D39D7FE1BFE4C5A721A54FFB501DEB34AFAB05754E7A6B7559867DE",
    "terminal": TERMINAL,
}


def _indexed_lookup(value: dict[str, object], path: str) -> object:
    current: object = value
    for component in path.split("."):
        if component.isdecimal():
            assert isinstance(current, list)
            current = current[int(component)]
        else:
            assert isinstance(current, dict)
            current = current[component]
    return current


def _validate_evidence(evidence: dict[str, object]) -> None:
    assert set(evidence) == {
        "adjudication",
        "archives",
        "authorities",
        "candidate",
        "closeout_review_state",
        "executions",
        "harness",
        "production_boundary",
        "production_restriction",
        "schema",
        "scope",
        "study_id",
        "syntheses",
        "terminal",
        "terminal_precedence",
    }
    assert evidence["schema"] == "anysolver.ge-beam3-mixed-p3-formal-evidence-v1"
    assert evidence["study_id"] == STUDY
    assert evidence["terminal_precedence"] == TERMINAL_PRECEDENCE
    assert evidence["production_boundary"] == PRODUCTION_BOUNDARY
    assert evidence["production_restriction"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert evidence["closeout_review_state"] == "COMPLETE_PENDING_INDEPENDENT_REVIEW"
    assert evidence["adjudication"] == {
        "accepted_final_execution_failures": [],
        "package_terminal": PACKAGE_TERMINAL,
        "performance_terminal": TERMINAL,
        "prior_incidents_preserved": True,
        "prior_incidents_reclassified": False,
        "syntheses_byte_identical": True,
        "synthesis_count": 2,
        "terminal_recomputed": True,
    }
    for path, expected in EXPECTED_IDENTITIES.items():
        assert _indexed_lookup(evidence, path) == expected
    assert evidence["executions"]["package"]["attempt"]["sha256"] == (
        evidence["executions"]["package"]["claim"]["sha256"]
    )
    assert evidence["executions"]["performance"]["attempt"]["sha256"] == (
        evidence["executions"]["performance"]["claim"]["sha256"]
    )
    assert all(
        execution["state"] == "CONSUMED_TERMINAL"
        and execution["retry_authorized"] is False
        and execution["request_reuse_authorized"] is False
        for execution in evidence["executions"].values()
    )


def _adjudicate(
    *,
    authority_ok: bool = True,
    process_ok: bool = True,
    selector_ok: bool = True,
    linear_ok: bool = True,
    package_ok: bool = True,
    performance_classified: bool = True,
) -> str:
    facts = [
        (not authority_ok, TERMINAL_PRECEDENCE[0]),
        (not process_ok, TERMINAL_PRECEDENCE[1]),
        (not selector_ok, TERMINAL_PRECEDENCE[2]),
        (not linear_ok, TERMINAL_PRECEDENCE[3]),
        (not package_ok, TERMINAL_PRECEDENCE[4]),
        (not performance_classified, TERMINAL_PRECEDENCE[5]),
    ]
    for failed, terminal in facts:
        if failed:
            return terminal
    return TERMINAL


def _external_path(logical: str) -> Path:
    if logical.startswith("external/resource-manager/"):
        root = Path(os.environ.get("GE_BEAM3_P3_REGISTRY", r"C:\Github\.resource-manager"))
        return root / logical.removeprefix("external/resource-manager/")
    release = Path(
        os.environ.get(
            "GE_BEAM3_P3_RELEASE_ROOT",
            r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease",
        )
    )
    return release / logical.removeprefix("external/")


def test_closeout_records_are_canonical_closed_and_hash_chained() -> None:
    evidence_raw, evidence = _canonical(EVIDENCE)
    review_raw, review = _canonical(REVIEW)
    status_raw, status = _canonical(STATUS)

    assert len(evidence_raw) == 8423
    assert _sha(evidence_raw) == (
        "E2E965C80A36E595D416DDBC8B2927414BAF79B6E0BAEEE9DADBB73B823657F5"
    )
    assert len(review_raw) == 5075
    assert _sha(review_raw) == (
        "8093A917FC8E4B85CD31EEED3DCFEE82562FA84577F99E79790640796E0C0AB8"
    )
    assert len(status_raw) == 3803
    assert _sha(status_raw) == (
        "067BF1B57DBE6E64B77452473C28D267D606202BBA786575DD43EE742914D38F"
    )
    _validate_evidence(evidence)
    assert set(review) == {
        "findings",
        "reviewed_inputs",
        "reviewer_independence",
        "schema",
        "verdict",
    }
    assert review["findings"] == []
    assert review["schema"] == "anysolver.ge-beam3-mixed-p3-formal-review-v1"
    assert review["reviewer_independence"] == {
        "authority_or_harness_authorship": False,
        "closeout_evidence_authorship": False,
        "evidence_recovery_method": (
            "READ_ONLY_CANONICAL_HASH_AUTHORITY_TOPOLOGY_AND_TERMINAL_RECOMPUTATION"
        ),
        "formal_process_executed": False,
        "mechanics_authorship": False,
        "role": "INDEPENDENT_GE_BEAM3_P3_FORMAL_CLOSEOUT_REVIEWER",
        "scope": (
            "H3_AUTHORITY_CONSUMPTION_INCIDENT_PRESERVATION_DETERMINISM_TERMINAL_"
            "AND_PRODUCTION_BOUNDARY_ONLY"
        ),
    }
    assert review["verdict"] == (
        "ACCEPT_PROVISIONAL_GO_GE_BEAM3_STRAIGHT_STANDALONE_OPT_IN_NO_P0_P1"
    )
    assert status["accepted_closeout"]["evidence"] == _record(
        CLOSEOUT_PATHS[0], len(evidence_raw), _sha(evidence_raw)
    )
    assert status["accepted_closeout"]["review"] == {
        **_record(CLOSEOUT_PATHS[1], len(review_raw), _sha(review_raw)),
        "verdict": review["verdict"],
    }


def test_all_bound_repository_and_available_external_hashes_recompute() -> None:
    _evidence_raw, evidence = _canonical(EVIDENCE)
    _review_raw, review = _canonical(REVIEW)
    reviewed = {item["path"]: item for item in review["reviewed_inputs"]}
    assert len(reviewed) == len(review["reviewed_inputs"]) == 25

    evidence_identity = (EVIDENCE.stat().st_size, _sha(EVIDENCE.read_bytes()))
    assert reviewed[CLOSEOUT_PATHS[0]] == _record(
        CLOSEOUT_PATHS[0], *evidence_identity
    )
    for logical, identity in REPO_INPUTS.items():
        raw = (ROOT / logical).read_bytes()
        assert (len(raw), _sha(raw)) == identity
        assert reviewed[logical] == _record(logical, *identity)

    expected_external = set(EXTERNAL_INPUTS)
    assert expected_external.issubset(reviewed)
    available = [path for path in expected_external if _external_path(path).is_file()]
    if available:
        assert set(available) == expected_external
        for logical in sorted(expected_external):
            raw = _external_path(logical).read_bytes()
            assert (len(raw), _sha(raw)) == EXTERNAL_INPUTS[logical]
            assert reviewed[logical] == _record(logical, *EXTERNAL_INPUTS[logical])

    assert evidence["syntheses"][0]["sha256"] == evidence["syntheses"][1]["sha256"]


def test_external_authority_consumption_chain_is_consistent_when_available() -> None:
    request_path = _external_path(
        "external/resource-manager/requests/245bb1e434c84b8a869ce5a141499e0e.json"
    )
    if not request_path.is_file():
        pytest.skip("immutable local resource-manager records are not present")

    def read(logical: str) -> dict[str, object]:
        value = _decode_strict(_external_path(logical).read_bytes())
        assert isinstance(value, dict)
        return value

    package_request = read(
        "external/resource-manager/requests/245bb1e434c84b8a869ce5a141499e0e.json"
    )
    package_claim = read(
        "external/resource-manager/claims/245bb1e434c84b8a869ce5a141499e0e.json"
    )
    package_receipt = read(
        "external/resource-manager/receipts/245bb1e434c84b8a869ce5a141499e0e.json"
    )
    package_result = read(
        "external/ge-beam3-p3-formal-20260905-h3/canonical/package-result-245bb1e434c84b8a869ce5a141499e0e.json"
    )
    package_aggregate = read(
        "external/ge-beam3-p3-formal-20260905-h3/package-work-50a1b4471d1f447c945fd7fea617b79d/gate/package-aggregate.json"
    )
    performance_request = read(
        "external/resource-manager/requests/1e14cc230fb74db185b031165a360dfa.json"
    )
    performance_claim = read(
        "external/resource-manager/claims/1e14cc230fb74db185b031165a360dfa.json"
    )
    performance_receipt = read(
        "external/resource-manager/receipts/1e14cc230fb74db185b031165a360dfa.json"
    )
    performance_result = read(
        "external/ge-beam3-p3-formal-20260905-h3/canonical/performance-result-1e14cc230fb74db185b031165a360dfa.json"
    )
    performance_aggregate = read(
        "external/ge-beam3-p3-formal-20260905-h3/performance-work-d09e6b73508544a6bb553fe3514b7efc/gate/performance-aggregate.json"
    )

    assert package_request["request_id"] == package_claim["request_id"]
    assert package_request["attempt_id"] == package_claim["attempt_id"]
    assert package_claim["authority_commit"] == PACKAGE_AUTHORITY_COMMIT
    assert package_receipt["claim_sha256"] == EXTERNAL_INPUTS[
        "external/resource-manager/claims/245bb1e434c84b8a869ce5a141499e0e.json"
    ][1]
    assert package_result["consumption"]["receipt_sha256"] == EXTERNAL_INPUTS[
        "external/resource-manager/receipts/245bb1e434c84b8a869ce5a141499e0e.json"
    ][1]
    assert package_receipt["terminal"] == package_result["terminal"] == PACKAGE_TERMINAL
    assert package_result["gate"]["aggregate"]["sha256"] == EXTERNAL_INPUTS[
        "external/ge-beam3-p3-formal-20260905-h3/package-work-50a1b4471d1f447c945fd7fea617b79d/gate/package-aggregate.json"
    ][1]
    assert package_aggregate["package_gate_passed"] is True

    assert performance_request["request_id"] == performance_claim["request_id"]
    assert performance_request["attempt_id"] == performance_claim["attempt_id"]
    assert performance_claim["authority_commit"] == PERFORMANCE_AUTHORITY_COMMIT
    assert performance_receipt["claim_sha256"] == EXTERNAL_INPUTS[
        "external/resource-manager/claims/1e14cc230fb74db185b031165a360dfa.json"
    ][1]
    assert performance_result["consumption"]["receipt_sha256"] == EXTERNAL_INPUTS[
        "external/resource-manager/receipts/1e14cc230fb74db185b031165a360dfa.json"
    ][1]
    assert performance_receipt["terminal"] == performance_result["terminal"] == TERMINAL
    assert performance_aggregate["all_existing_paths_pass"] is True
    assert performance_aggregate["ge_beam3_speed_gate"] == "NONE"
    assert performance_aggregate["package_aggregate_sha256"] == EXTERNAL_INPUTS[
        "external/ge-beam3-p3-formal-20260905-h3/package-work-50a1b4471d1f447c945fd7fea617b79d/gate/package-aggregate.json"
    ][1]


def test_authority_git_topology_incidents_and_candidate_freeze_are_exact() -> None:
    _assert_commit(
        CANDIDATE,
        parent=IMPLEMENTATION_FREEZE,
        tree=CANDIDATE_TREE,
        subject="fix: correct GE Beam3 P3 Windows RSS diagnostics",
        paths=[
            "docs/reference_cases/ge_beam3_mixed_p3_package_gate.py",
            "tests/test_ge_beam3_mixed_p3_performance.py",
        ],
    )
    _assert_commit(
        "48a3eba3347d9ebe0fd15cac6a8c7db64c1f743e",
        parent="ecf4cfe228d7513e9bb99f885c42da198a2d7fe5",
        tree="da4848f06678783e7f1e420c8b12f24050544470",
        subject="docs: authorize GE Beam3 P3 package execution",
        paths=[
            "docs/reference_cases/ge_beam3_mixed_p3_package_execution_authority.json",
            "docs/reference_cases/ge_beam3_mixed_p3_package_execution_review.json",
        ],
    )
    _assert_commit(
        "7367270451c612e0d3cd1f8cfe8f21be111b4082",
        parent="7ad427a0e45973ecb4a573ec8cfb63dbec735e20",
        tree="fc871781ab483231d3967cec14444a33fd60bdb6",
        subject="docs: authorize GE Beam3 P3 package execution",
        paths=[
            "docs/reference_cases/ge_beam3_mixed_p3_package_execution_authority.json",
            "docs/reference_cases/ge_beam3_mixed_p3_package_execution_review.json",
        ],
    )
    _assert_commit(
        H3,
        parent="7367270451c612e0d3cd1f8cfe8f21be111b4082",
        tree="fb0eab67907952374a998615a389e2b2c14a7a0a",
        subject="docs: repair GE Beam3 P3 private home harness",
        paths=[
            "docs/reference_cases/ge_beam3_mixed_p3_formal_contract.json",
            "docs/reference_cases/ge_beam3_mixed_p3_formal_executor.py",
            "tests/test_ge_beam3_mixed_p3_formal_executor.py",
        ],
    )
    _assert_commit(
        PACKAGE_AUTHORITY_COMMIT,
        parent=H3,
        tree="5082f219877fba51573ee575521e51c711d9a1fa",
        subject="docs: authorize GE Beam3 P3 package execution",
        paths=[
            "docs/reference_cases/ge_beam3_mixed_p3_package_execution_authority.json",
            "docs/reference_cases/ge_beam3_mixed_p3_package_execution_review.json",
        ],
    )
    _assert_commit(
        PERFORMANCE_AUTHORITY_COMMIT,
        parent=PACKAGE_AUTHORITY_COMMIT,
        tree="df527203b24891883db0e0ac5bc7f82c0c3ea81a",
        subject="docs: authorize GE Beam3 P3 performance execution",
        paths=[
            "docs/reference_cases/ge_beam3_mixed_p3_performance_execution_authority.json",
            "docs/reference_cases/ge_beam3_mixed_p3_performance_execution_review.json",
        ],
    )

    for archive, expected_commit in {
        "refs/archive/ge-beam3-p3-package-cycle1-blocked-20260905": (
            "48a3eba3347d9ebe0fd15cac6a8c7db64c1f743e"
        ),
        "refs/archive/ge-beam3-p3-package-cycle2-blocked-20260905": (
            "7367270451c612e0d3cd1f8cfe8f21be111b4082"
        ),
    }.items():
        resolved = _git("rev-parse", "--verify", archive)
        if resolved.returncode == 0:
            assert resolved.stdout.decode("ascii").strip() == expected_commit

    assert _git_text("diff", "--name-only", CANDIDATE, "HEAD", "--", "src") == ""
    assert _git_text(
        "diff", "--name-only", CANDIDATE, "HEAD", "--", "pyproject.toml", ".github"
    ) == ""


def test_closeout_extent_and_fail_closed_boundary_are_exact() -> None:
    _contract_raw, contract = _canonical(CONTRACT)
    _evidence_raw, evidence = _canonical(EVIDENCE)
    _status_raw, status = _canonical(STATUS)
    assert contract["closeout"]["exact_paths"] == CLOSEOUT_PATHS
    assert contract["closeout"]["syntheses"] == 2
    assert contract["closeout"]["syntheses_byte_identical"] is True
    assert status["closeout_extent"] == {
        "exact_paths": CLOSEOUT_PATHS,
        "expected_parent": PERFORMANCE_AUTHORITY_COMMIT,
        "expected_subject": "docs: close GE Beam3 P3 standalone opt-in gate",
    }
    assert status["production_boundary"] == evidence["production_boundary"] == (
        PRODUCTION_BOUNDARY
    )
    assert status["scientific_evidence_accepted"] is True
    assert status["terminal"] == evidence["terminal"] == TERMINAL
    assert set(CLOSEOUT_PATHS) == {
        EVIDENCE.relative_to(ROOT).as_posix(),
        REVIEW.relative_to(ROOT).as_posix(),
        STATUS.relative_to(ROOT).as_posix(),
        Path(__file__).resolve().relative_to(ROOT).as_posix(),
    }


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"authority_ok": False, "process_ok": False}, TERMINAL_PRECEDENCE[0]),
        ({"process_ok": False, "selector_ok": False}, TERMINAL_PRECEDENCE[1]),
        ({"selector_ok": False, "linear_ok": False}, TERMINAL_PRECEDENCE[2]),
        ({"linear_ok": False, "package_ok": False}, TERMINAL_PRECEDENCE[3]),
        ({"package_ok": False, "performance_classified": False}, TERMINAL_PRECEDENCE[4]),
        ({"performance_classified": False}, TERMINAL_PRECEDENCE[5]),
        ({}, TERMINAL),
    ],
)
def test_terminal_precedence_is_recomputed(
    overrides: dict[str, bool], expected: str
) -> None:
    assert _adjudicate(**overrides) == expected


@pytest.mark.parametrize("path", sorted(EXPECTED_IDENTITIES))
def test_identity_mutations_are_rejected(path: str) -> None:
    _raw, evidence = _canonical(EVIDENCE)
    mutated = copy.deepcopy(evidence)
    current: object = mutated
    components = path.split(".")
    for component in components[:-1]:
        if component.isdecimal():
            assert isinstance(current, list)
            current = current[int(component)]
        else:
            assert isinstance(current, dict)
            current = current[component]
    assert isinstance(current, dict)
    current[components[-1]] = "0" * 64
    with pytest.raises(AssertionError):
        _validate_evidence(mutated)


def test_strict_json_rejects_duplicate_and_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="duplicate JSON key"):
        _decode_strict(b'{"schema":"a","schema":"b"}\n')
    for constant in (b"NaN", b"Infinity", b"-Infinity"):
        with pytest.raises(ValueError, match="nonfinite JSON value"):
            _decode_strict(b'{"value":' + constant + b"}\n")
