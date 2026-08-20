from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREREG_COMMIT = "97edc4265a7ce5ca9763f66875d1336e419bcef4"
PREREG_TREE = "e511c461b59162029eaf3e8ceb93f144d94bf910"
CLOSEOUT_SUBJECT = "docs: close E4 PL Q1R implementation-identity block"

CLOSEOUT_PATHS = {
    "docs/reference_cases/e4_pl_q1r_status.json",
    "docs/E4_PL_Q1R_LOCAL_QUALIFICATION.md",
    "docs/E4_PL_Q1R_INDEPENDENT_REVIEW.md",
    "docs/E4_PL_Q1R_COMPLETION.md",
    "tests/test_e4_pl_q1r_closeout.py",
}

DRAFTS = {
    "docs/reference_cases/e4_pl_q1r_reference.py": (
        102179,
        "115F577A67EFACBC20F6E2210C2AC2C67DC0222BB4510C55910B0E3EB312FE7A",
    ),
    "docs/reference_cases/e4_pl_q1r_oracle.py": (
        104363,
        "6902D4B540C72456B897F9AC6D607EB04E1F8213EA7CDB410082F6BC6F49F86A",
    ),
    "docs/reference_cases/e4_pl_q1r_implementation_manifest.json": (
        3640,
        "279C7D4AA765C75BF499BC0F65E8BABCEF9C7675B940D58DB6A5D4E3A0B87F07",
    ),
    "tests/test_e4_pl_q1r_frame_theorem.py": (
        2761,
        "60D57898901E02270D93A26504CB83344CB4DA7E01E74BA93929EC84DC631B5A",
    ),
    "tests/test_e4_pl_q1r_local_algebra.py": (
        1870,
        "D5D3B920163C45B4B8FFE7AA73A83BB2ABF6BB6821CA5D9F6FB6F41EADB4D9E3",
    ),
    "tests/test_e4_pl_q1r_covariance.py": (
        1564,
        "65E677884F5125179A162E448E894803A9089B35B7F83F4C8975421EF1DF6DF1",
    ),
    "tests/test_e4_pl_q1r_recovery.py": (
        1603,
        "309169544CD1A91A8EDF080F0BC56AB1CD2F62FBE1BEF438BF2E51DF68F79318",
    ),
    "tests/test_e4_pl_q1r_restricted_boundary.py": (
        1318,
        "4405EFC13D662D576DFCC44AEEC42C39C77819F66F34BC5FE480BAD25651EDA8",
    ),
}

BOUND = {
    "docs/agent_plans/S4_E4_PL_Q1R_NUMBERED_FRAME_PLAN.md": (
        7203,
        "A095EE95ABB3F62B42ABBBED077C74AE72F2B1EAA479DDBB241C321EF12722AD",
    ),
    "docs/E4_PL_Q1R_PLAN_REVIEW.md": (
        8613,
        "8B9FA2CE9E3A9456B0DEB2B7A1E5CEB81C6B05FDC0CE86FE3896402E501A1ACD",
    ),
    "docs/reference_cases/e4_pl_q1r_allowed_extent.json": (
        3073,
        "F9C838D3432165FFC30158BF88B54C6C53FC3A52371CC534E08B9E265EED5052",
    ),
    "docs/reference_cases/e4_pl_q1r_terminal_table.json": (
        3044,
        "CDEA948B03C89511E6D65F598E7BF8E9F4C54B30848727C7520D040A5F2D7FDC",
    ),
    "docs/reference_cases/e4_pl_q1r_status.json": (
        4139,
        "398A895358F84A58667A6C21BE1C4800990D570F4C3AD1AF881FE511077A6025",
    ),
    "docs/E4_PL_Q1R_LOCAL_QUALIFICATION.md": (
        3635,
        "0144C1A709A75EA9D57C082AD65F72CA851F67FF981863D7871728654728637E",
    ),
    "docs/E4_PL_Q1R_INDEPENDENT_REVIEW.md": (
        5992,
        "75D66AA1EDA1823245BF1B4B6417CF0CA499892F60F116E67A0AF06E9D6DE665",
    ),
    "docs/E4_PL_Q1R_COMPLETION.md": (
        1919,
        "129BEA1D54AC302C961849E11D17C6F2D6EF52568F1C0F1A3A5696ED713F0553",
    ),
    **DRAFTS,
}

PRESERVED_ROOTS = {
    ".s4_candidate_a_pinned/",
    ".s4_stage_m_execution/",
    ".s4_stage_m_mpmath/",
    ".s4_stage_m_mpmath_clean/",
    ".s4_stage_m_patch_tools/",
    "tmp/",
}

REQUIRED_ABSENCES = {
    "docs/E4_PL_Q1R_IMPLEMENTATION_REVIEW.md",
    "docs/reference_cases/e4_pl_q1r_contract.json",
    "docs/E4_PL_Q1R_CONTRACT_REVIEW.md",
    "docs/reference_cases/e4_pl_q1r_reference_output.json",
    "docs/reference_cases/e4_pl_q1r_oracle_output.json",
    "docs/reference_cases/e4_pl_q1r_output.json",
    "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md",
}


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _raw(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _strict_json(path: str) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    def nonfinite(token: str) -> object:
        raise ValueError(f"nonfinite JSON token: {token}")

    raw = _raw(path)
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    canonical = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    assert raw == canonical
    return value


def _outside_preserved(path: str) -> bool:
    return not any(path.startswith(prefix) for prefix in PRESERVED_ROOTS)


def test_q1r_blocked_closeout_is_content_addressed_and_fail_closed() -> None:
    for path, (size, digest) in BOUND.items():
        raw = _raw(path)
        assert len(raw) == size, path
        assert _sha256(raw) == digest, path
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert b"\r" not in raw, path
        assert raw.endswith(b"\n"), path

    status = _strict_json("docs/reference_cases/e4_pl_q1r_status.json")
    assert isinstance(status, dict)
    assert status["schema"] == "anysolver.s4.e4-pl-q1r-blocked-status-v1"
    assert status["final"] == {
        "production_terminal": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_authorized": False,
        "terminal": "BLOCKED_E4_PL_Q1R_IMPLEMENTATION_IDENTITY",
    }
    assert status["candidate"]["status"] == "DORMANT_UNQUALIFIED"
    assert status["candidate"]["scientific_classification"] == "NOT_ESTABLISHED"
    assert status["implementation_drafts"]["classification_authority"] is False
    assert (
        status["implementation_drafts"]["disposition"]
        == "NONAUTHORITATIVE_SUCCESSOR_SCAFFOLDING"
    )
    assert status["evidence_chain"]["registered_mechanics_run"] is False
    assert status["evidence_chain"]["caller_bound_contract_created"] is False
    assert status["evidence_chain"]["implementation_review_created"] is False
    assert len(status["component_ledger"]["implementation_identity"]["deficiencies"]) == 4

    review = _raw("docs/E4_PL_Q1R_INDEPENDENT_REVIEW.md").decode("utf-8")
    assert review.count("`ACCEPT_Q1R_BLOCKED_CLOSEOUT_NO_P0_P1`") == 1
    assert "accepts only the authority, terminal selection, evidence" in review
    assert "No implementation mechanics" in review
    assert "was\nrun or reviewed" in review

    for path in REQUIRED_ABSENCES:
        assert not (ROOT / path).exists(), path


def test_q1r_blocked_closeout_preserves_drafts_and_production_boundary() -> None:
    for path, (size, digest) in DRAFTS.items():
        raw = _raw(path)
        assert len(raw) == size, path
        assert _sha256(raw) == digest, path
        assert _git("ls-files", "--error-unmatch", "--", path, check=False).returncode != 0

    assert _git("diff", "--cached", "--quiet", check=False).returncode == 0
    assert _git("diff", "--quiet", check=False).returncode == 0
    assert (
        _git(
            "diff",
            "--name-only",
            PREREG_COMMIT,
            "--",
            ".gitattributes",
            ".github",
            "pyproject.toml",
            "setup.cfg",
            "setup.py",
            "src",
        ).stdout.splitlines()
        == []
    )
    for prefix in PRESERVED_ROOTS:
        assert (ROOT / prefix.rstrip("/")).is_dir(), prefix


def test_q1r_blocked_closeout_extent_and_commit_boundary_are_exact() -> None:
    tracked = {
        line.replace("\\", "/")
        for line in _git("diff", "--name-only", PREREG_COMMIT, "--").stdout.splitlines()
        if line
    }
    untracked = {
        line.replace("\\", "/")
        for line in _git("ls-files", "--others", "--exclude-standard").stdout.splitlines()
        if line and _outside_preserved(line.replace("\\", "/"))
    }
    assert tracked | untracked == CLOSEOUT_PATHS | set(DRAFTS)
    assert tracked <= CLOSEOUT_PATHS
    assert untracked >= set(DRAFTS)

    head = _git("rev-parse", "HEAD").stdout.strip()
    tree = _git("rev-parse", "HEAD^{tree}").stdout.strip()
    if head == PREREG_COMMIT:
        assert tree == PREREG_TREE
        assert untracked == CLOSEOUT_PATHS | set(DRAFTS)
    else:
        assert _git("rev-parse", "HEAD^").stdout.strip() == PREREG_COMMIT
        assert _git("show", "-s", "--format=%s", "HEAD").stdout.strip() == CLOSEOUT_SUBJECT
        commit_paths = {
            line.replace("\\", "/")
            for line in _git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"
            ).stdout.splitlines()
            if line
        }
        assert commit_paths == CLOSEOUT_PATHS
        assert tracked == CLOSEOUT_PATHS
        assert untracked == set(DRAFTS)
