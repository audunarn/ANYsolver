from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = "fc8de7cb12bd9cd54a53b3ea26688cec268f1f44"
BASE = "c9d75eaed17e658e84879085a01ecca823dd32cd"
SUBJECT = "docs: close E4 PL Q1G bounded rigid-range repair"
OUTCOME = {
    "docs/E4_PL_Q1G_COMPLETION.md",
    "docs/E4_PL_Q1G_DOMAIN_COERCIVITY.md",
    "docs/reference_cases/e4_pl_q1g_evidence.json",
    "docs/reference_cases/e4_pl_q1g_scientific_review.json",
    "docs/reference_cases/e4_pl_q1g_status.json",
    "tests/test_e4_pl_q1g_closeout.py",
}
IDENTITIES = {
    "docs/E4_PL_Q1G_COMPLETION.md": (1160, "AFDDCC1043EFD82017D4D402BDFFADBA526B215D54DB5D98CADB5DEFEFFFD12B"),
    "docs/E4_PL_Q1G_DOMAIN_COERCIVITY.md": (1680, "DD48CADBCF767B4C82B5BF48F8E0E7B738AECEBF09D14D10E77EF16CEA244CB0"),
    "docs/reference_cases/e4_pl_q1g_evidence.json": (1454, "F96CE7C0E31BD069604D8A21B18697255AAEC2CECC9925E7B061A1008B6EFD24"),
    "docs/reference_cases/e4_pl_q1g_scientific_review.json": (942, "D89A23EEEA29586AC6FC16AB198789EC502B285FDE5A955AA51E78555F541082"),
    "docs/reference_cases/e4_pl_q1g_status.json": (1577, "459D51BD949A8AADFB7CCA95436F951827F06682E1EA44CCBB50189005B6A6E7"),
}


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout.strip()


def _strict(path: str) -> dict:
    raw = (ROOT / path).read_bytes()
    assert b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf")
    value = json.loads(raw.decode("utf-8"), parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    assert (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode() == raw
    return value


def test_q1g_static_closeout_integrity() -> None:
    for path, (size, digest) in IDENTITIES.items():
        raw = (ROOT / path).read_bytes()
        assert len(raw) == size
        assert hashlib.sha256(raw).hexdigest().upper() == digest
    evidence = _strict("docs/reference_cases/e4_pl_q1g_evidence.json")
    review = _strict("docs/reference_cases/e4_pl_q1g_scientific_review.json")
    status = _strict("docs/reference_cases/e4_pl_q1g_status.json")
    assert evidence["two_cycle_byte_identical"] is True
    assert [row["sha256"] for row in evidence["cycle_aggregates"]] == ["E6F8A3DB17CE2CB6F18A892DEB9AF1A37CCDC5BBFF9B54F251BBD049C49834CA"] * 2
    assert evidence["aggregate"]["local_reduction"] == {
        "basis_change_nonsingular": True,
        "coercivity_certified": False,
        "h_kernel_certified": False,
        "rigid_range_exact": True,
    }
    assert evidence["q1f_disposition"] == {
        "blocked_closeout_preserved": True,
        "premature_drafts_promoted": False,
        "premature_drafts_run": False,
    }
    assert review["findings"] == []
    assert review["verdict"] == "ACCEPT_Q1G_RIGID_RANGE_EVIDENCE_NO_P0_P1"
    assert status["terminal"] == "UNCLASSIFIED_E4_PL_Q1G_DOMAIN_COVERAGE"
    assert status["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert status["q1b_execution"] == "UNAUTHORIZED"
    assert status["q1h_plan_preparation"] == "UNAUTHORIZED_UNTIL_DOMAIN_COERCIVITY_CLOSED"
    head = _git("rev-parse", "HEAD")
    if head == AUTHORIZATION:
        untracked = set(_git("ls-files", "--others", "--exclude-standard").splitlines())
        assert OUTCOME <= untracked
    else:
        assert _git("rev-parse", "HEAD^") == AUTHORIZATION
        assert _git("show", "-s", "--format=%s", "HEAD") == SUBJECT
        assert set(_git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()) == OUTCOME
    changed = set(_git("diff", "--name-only", f"{BASE}..HEAD").splitlines()) | OUTCOME
    assert not any(path == ".gitattributes" or path == "pyproject.toml" or path.startswith(("src/", ".github/")) for path in changed)
    assert not any((ROOT / path).exists() for path in (
        "docs/reference_cases/e4_pl_q1f_common.py",
        "docs/reference_cases/e4_pl_q1f_domain_producer.py",
        "docs/reference_cases/e4_pl_q1f_domain_checker.py",
        "docs/reference_cases/e4_pl_q1f_bounded_runner.py",
    ))
