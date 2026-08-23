"""Static Q1B OUTCOME11 closeout integrity check; imports no mechanics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
COMMIT3 = "621ab3d6e0563e068439fa96ca393a84b2609dd4"
SUBJECT = "docs: close E4 PL Q1B assembled qualification"
OUTCOME = {
    "docs/reference_cases/e4_pl_q1b_cycle1.json": (19154, "DF040D65A46820C7037111E0B85D6FF4C99E38338CEF9116A908A41F33888407"),
    "docs/reference_cases/e4_pl_q1b_cycle2.json": (19154, "945C1B95966836AA64A936AC0E40AE181C8FD3B4A261A894CC44A053332CA408"),
    "docs/reference_cases/e4_pl_q1b_agreement.json": (592, "065798A35225B0BC3D7D094EC116117AA0E898FF5752A2E47C39D55975E5A48B"),
    "docs/reference_cases/e4_pl_q1b_output.json": (527, "0EDF8AB29DDE337F7DF227F0848EA2BCA71E1B560C5A029584762BEF98475B05"),
    "docs/reference_cases/e4_pl_q1b_status.json": (1663, "CA326EA940236F746BE2C931E0D9A76F826924827DA031251A5038A832F271C5"),
    "docs/reference_cases/e4_pl_q1b_execution_authority.json": (1032, "CE4426DDFEC98C341102A26C934B577A5E342633E2EFFC1BDB87A4F407B15F1E"),
    "docs/reference_cases/e4_pl_q1b_scientific_test_result.json": (847, "A2B98F06BA49EA31B198C08CDD739A41D8B34127E1E1DC74886C859E3CA4BDDA"),
    "docs/E4_PL_Q1B_LOCAL_QUALIFICATION.md": (948, "3E86F03DDD44A7B00AE870A9F483FDE447EAAE12D761C887997CA3A8215AAE08"),
    "docs/reference_cases/e4_pl_q1b_scientific_review.json": (1466, "22609F3D6B64843C08C8430135FE2406AE32ABBB6475CC326329BD07ADD34BDB"),
    "docs/E4_PL_Q1B_COMPLETION.md": (1464, "C514D554FD44BF59047836F4C35E27B3B5900F451C43BE4C03E1BB32E0D5CA2C"),
}


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def _canonical(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw)
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return value


def test_q1b_closeout_hash_dag_terminal_and_production_boundary() -> None:
    this_path = "tests/test_e4_pl_q1b_closeout.py"
    assert set(OUTCOME) | {this_path} == {
        "docs/reference_cases/e4_pl_q1b_cycle1.json", "docs/reference_cases/e4_pl_q1b_cycle2.json",
        "docs/reference_cases/e4_pl_q1b_agreement.json", "docs/reference_cases/e4_pl_q1b_output.json",
        "docs/reference_cases/e4_pl_q1b_status.json", "docs/reference_cases/e4_pl_q1b_execution_authority.json",
        "docs/reference_cases/e4_pl_q1b_scientific_test_result.json", "docs/E4_PL_Q1B_LOCAL_QUALIFICATION.md",
        "docs/reference_cases/e4_pl_q1b_scientific_review.json", "docs/E4_PL_Q1B_COMPLETION.md", this_path,
    }
    for relative, (size, digest) in OUTCOME.items():
        raw = (ROOT / relative).read_bytes()
        assert len(raw) == size and hashlib.sha256(raw).hexdigest().upper() == digest
    cycle1 = _canonical(ROOT / "docs/reference_cases/e4_pl_q1b_cycle1.json")
    cycle2 = _canonical(ROOT / "docs/reference_cases/e4_pl_q1b_cycle2.json")
    agreement = _canonical(ROOT / "docs/reference_cases/e4_pl_q1b_agreement.json")
    output = _canonical(ROOT / "docs/reference_cases/e4_pl_q1b_output.json")
    status = _canonical(ROOT / "docs/reference_cases/e4_pl_q1b_status.json")
    review = _canonical(ROOT / "docs/reference_cases/e4_pl_q1b_scientific_review.json")
    assert cycle1["common_payload"] == cycle2["common_payload"]
    assert cycle1["common_payload_sha256"] == cycle2["common_payload_sha256"] == agreement["common_payload_sha256"]
    assert agreement["common_payload_byte_identical"] is True
    terminal = "NO_GO_E4_PL_Q1B_LOCKING_OR_CATEGORY_DRIFT"
    assert cycle1["common_payload"]["terminal"] == output["terminal"] == status["terminal"] == terminal
    assert review["verdict"] == "ACCEPT_Q1B_SCIENTIFIC_REVIEW_NO_P0_P1" and review["findings"] == []
    assert status["production"] == output["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert _git("diff", "--name-only") == "" and _git("diff", "--cached", "--name-only") == ""
    head = _git("rev-parse", "HEAD")
    if head == COMMIT3:
        observed = {line[3:].replace("\\", "/") for line in _git("status", "--porcelain").splitlines() if line.startswith("?? ")}
        assert observed == set(OUTCOME) | {this_path}
    else:
        assert _git("rev-parse", "HEAD^") == COMMIT3
        assert _git("show", "-s", "--format=%s", head) == SUBJECT
        assert set(_git("diff-tree", "--no-commit-id", "--name-only", "-r", head).splitlines()) == set(OUTCOME) | {this_path}
    changed = _git("diff", "--name-only", "be64f1d7f284bfa044e8dd4b40bece29e7311f44..HEAD").splitlines()
    assert not any(path == "pyproject.toml" or path == ".gitattributes" or path.startswith(("src/", ".github/")) for path in changed)
