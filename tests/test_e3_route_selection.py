from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BASE = "2ac678a7f94c250fe433f66378a83508d86ee499"
HW_ORACLE = ROOT / "docs/reference_cases/e3_hw29_oracle.py"
HW_CONTRACT = ROOT / "docs/reference_cases/e3_hw29_contract.json"
MITC_ORACLE = ROOT / "docs/reference_cases/e3_mitc9i_oracle.py"
MITC_CONTRACT = ROOT / "docs/reference_cases/e3_mitc9i_contract.json"
IDENTITIES = {
    "docs/E3_ROUTE_SELECTION_REPORT.md": (4575, "D76876A388BAEDBB2C1DF23C91D1E5E7A99BD365439902904B017D9A7A5B93B9"),
    "docs/agent_plans/S4_E3_A_VARIATIONAL_CLOSURE_STUDY_PLAN.md": (4794, "5903DFEC12D7F4331493CDFEFFB04ACBB22F94EA681993366D80957E403B09FA"),
    "docs/reference_cases/e3_hw29_contract.json": (2331, "E07C60EDE72DDD6D19D686F79978C3F0D1826DA91B1D2552534063BD28C394A0"),
    "docs/reference_cases/e3_hw29_output.json": (2441, "3D9E9C858CAD14CB3BDEBFC8866E971658F02E71B16573A320BAF0B08DFE9806"),
    "docs/reference_cases/e3_mitc9i_contract.json": (2116, "86824E91A460AEAC9F67B213048E471AF968C7AA9FE2C43E6B61B148A5C8FBED"),
    "docs/reference_cases/e3_mitc9i_output.json": (2475, "00A6603A7B163CBC4A25B7FDF74647DDC1BDA300D478598F1403E4582AF5B575"),
    "docs/reference_cases/e3_route_contract.json": (3610, "B39EE05F48EB4D5CF4A1A09C0FF20891886BB388631756FD08328CEE4FB99BF9"),
    "docs/reference_cases/e3_route_output.json": (708, "A2D3283C1F01A26EF01986A4C5396B6C07797C250B7D2BD3BDA21AD1E14C273E"),
    "docs/reference_cases/e3_search_log.json": (1559, "6A327A8120995CC52A943890E7C4EC6B7171C1F0F5F3C14300A82B5483C57495"),
    "docs/reference_cases/e3_source_registry.json": (2863, "3F28EEF4E2E83EE82BE9487233694547F946154B39114A785D61D341296322C7"),
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result
        result[key] = value
    return result


def _raw(relative: str) -> bytes:
    raw = (ROOT / relative).read_bytes()
    assert (len(raw), _sha(raw)) == IDENTITIES[relative]
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw and raw.endswith(b"\n")
    return raw


def _json(relative: str) -> dict[str, object]:
    raw = _raw(relative)
    value = json.loads(
        raw.decode("utf-8"), object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(AssertionError(token)),
    )
    canonical = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    assert raw == canonical and isinstance(value, dict)
    return value


def _run(oracle: Path, contract: Path, contract_hash: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0")
    return subprocess.run(
        [
            sys.executable, str(oracle), "--run", "--contract", str(contract),
            "--contract-sha256", contract_hash,
        ],
        cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, timeout=60,
    )


def test_e3_route_is_total_and_mitc9i_is_non_gating() -> None:
    hw = _json("docs/reference_cases/e3_hw29_output.json")
    mitc = _json("docs/reference_cases/e3_mitc9i_output.json")
    contract = _json("docs/reference_cases/e3_route_contract.json")
    route = _json("docs/reference_cases/e3_route_output.json")
    assert hw["component_terminal"] == "BLOCKED_E3_P_HW29_PUBLIC_SOURCE"
    assert hw["certificate"]["source_closure"]["closed_rows"] == 9
    assert len(hw["certificate"]["source_closure"]["missing_indispensable_ids"]) == 5
    assert mitc["status"] == "GO_REFERENCE_E3_Q9_MITC9I_PARTIAL_PACKET"
    assert mitc["hw29_route_gate"] == "NONE"
    assert route["component_statuses"] == {
        "hw29": hw["component_terminal"],
        "mitc9i": mitc["status"],
    }
    assert route["contract_sha256"] == IDENTITIES["docs/reference_cases/e3_route_contract.json"][1]
    assert route["route_terminal"] == "UNCLASSIFIED_E3_Q4_FORMULATION_ROUTE"
    assert route["route_authorization"] == "AUTHORIZE_E3_A_VARIATIONAL_CLOSURE_STUDY"
    assert contract["route_rule"]["mitc9i_route_gate"] == "NONE"


def test_e3_sources_include_all_user_supplied_files_without_committing_them() -> None:
    registry = _json("docs/reference_cases/e3_source_registry.json")
    search = _json("docs/reference_cases/e3_search_log.json")
    mitc_copy = registry["mitc9i"]["user_supplied_local_copy"]
    assert mitc_copy["byte_identical_to_open_primary"] is True
    assert mitc_copy["sha256"] == registry["mitc9i"]["open_primary"]["sha256"]
    detailed = registry["hw29"]["detailed_sources"][1]
    assert detailed["sha256"] == "E6AFAADE32B33D710D3C038635FE2AD2729E32FB952C5EC6706E68A93A3B1860"
    assert detailed["role"] == "P_DETAILED_PRIMARY_BUT_NOT_COMPLETE_DISCRETE_IDENTITY"
    background = registry["related_background"]["degenerated_q4_penalty_paper"]
    assert background["sha256"] == "B67AF5A43CB36FEC9E0D8CDAD745B391F9F5FC1861C842A249E2B982BDACD5E8"
    assert background["role"] == "B_DISTINCT_TUNABLE_TORSIONAL_PENALTY_NOT_HW29"
    assert registry["copyright_boundary"] == {
        "committed_external_pdf": False,
        "committed_figure": False,
        "committed_page_image": False,
        "committed_table": False,
        "committed_verbatim_passage": False,
    }
    assert search["result"]["hw29"] == (
        "DETAILED_2011_SOURCE_NARROWS_BUT_DOES_NOT_CLOSE_MANDATORY_DISCRETE_ROWS"
    )


def test_e3_component_oracles_repeat_exact_committed_outputs() -> None:
    runs = [
        (HW_ORACLE, HW_CONTRACT, "docs/reference_cases/e3_hw29_contract.json", "docs/reference_cases/e3_hw29_output.json"),
        (MITC_ORACLE, MITC_CONTRACT, "docs/reference_cases/e3_mitc9i_contract.json", "docs/reference_cases/e3_mitc9i_output.json"),
    ]
    for oracle, contract, contract_key, output_key in runs:
        contract_hash = IDENTITIES[contract_key][1]
        first = _run(oracle, contract, contract_hash)
        second = _run(oracle, contract, contract_hash)
        assert first.returncode == second.returncode == 0
        assert first.stderr == second.stderr == b""
        assert first.stdout == second.stdout == _raw(output_key)


def test_e3_historical_terminals_and_production_boundary_are_unchanged() -> None:
    baseline = json.loads((ROOT / "docs/reference_cases/e3_baseline.json").read_text(encoding="utf-8"))
    status_record = baseline["e2_closeout"]["status"]
    raw = (ROOT / status_record["path"]).read_bytes()
    assert (len(raw), _sha(raw)) == (status_record["bytes"], status_record["sha256"])
    historical = json.loads(raw)["historical_results"]
    assert historical == {
        "candidate_a": "NO_GO_CANDIDATE_A_DISCRETE_PAIR",
        "candidate_b": "NO_GO_CANDIDATE_B",
        "candidate_c": "NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP",
        "candidate_e0": "BLOCKED_CANDIDATE_E_SOURCE_OR_IDENTITY",
        "candidate_e1_a": "NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY",
        "candidate_e1_r": "PROVISIONAL_GO_CANDIDATE_E1_R_PLANAR_REGULARIZER_ONLY",
        "rank_four": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
    }
    route = _json("docs/reference_cases/e3_route_output.json")
    assert route["overall_release_terminal"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert route["production"] == {"legacy_shell_default": True, "production_changes": False}
    plan = _raw("docs/agent_plans/S4_E3_A_VARIATIONAL_CLOSURE_STUDY_PLAN.md").decode()
    assert "not a registered\ncandidate" in plan
    diff = subprocess.run(
        ["git", "diff", "--name-only", BASE, "--", "src", ".github", "pyproject.toml"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert diff.returncode == 0 and diff.stdout == b""
