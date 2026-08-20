from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/reference_cases/e4_pl_q1t_execution_contract.json"
REVIEW = ROOT / "docs/reference_cases/e4_pl_q1t_contract_review.json"
COMMIT1 = "658619184d354401f55fc7a6640a4770d900ded7"
COMMIT2 = "083044167f9826e9868851c2709017112bc7553d"
COMMIT3_SUBJECT = "docs: authorize E4 PL Q1T scientific execution"
ENV_SHA = "5461206324E7FC2A52B334CE736A512EE71313ED79181438047E3E20069A9746"
CONTRACT_KEYS = {"agreement", "authorization", "candidate_id", "commit_ancestry", "environment", "implementation_inputs", "inherited_inputs", "output_absences", "plan_inputs", "production_restriction", "review_authorities", "runner_inventory", "runtime", "schema", "scientific_inventory", "study_id", "terminal_authority"}


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _canonical(path: Path) -> tuple[dict[str, object], bytes]:
    raw = path.read_bytes()
    def pairs(rows: list[tuple[str, object]]) -> dict[str, object]:
        out: dict[str, object] = {}
        for key, value in rows:
            if key in out:
                raise ValueError(key)
            out[key] = value
        return out
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    assert isinstance(value, dict)
    expected = (json.dumps(value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    assert raw == expected
    return value, raw


def _bound(row: dict[str, object]) -> None:
    path = ROOT / str(row["path"])
    raw = path.read_bytes()
    assert len(raw) == row["bytes"] and _sha(raw) == row["sha256"]


def test_q1t_contract_binds_exact_stages_environment_reviews_inventory_and_absences() -> None:
    contract, raw = _canonical(CONTRACT)
    assert set(contract) == CONTRACT_KEYS
    assert contract["schema"] == "anysolver.s4.e4-pl-q1t-execution-contract-v1"
    assert contract["commit_ancestry"]["commit1"]["commit"] == COMMIT1
    assert contract["commit_ancestry"]["commit2"]["commit"] == COMMIT2
    assert contract["commit_ancestry"]["commit2"]["tree"] == "3b52b601e509b1348145cffdb40cb1d478b9227f"
    assert contract["plan_inputs"]["count"] == 14
    assert contract["inherited_inputs"]["count"] == 49
    assert len(contract["implementation_inputs"]["scientific_tests"]) == 5
    assert contract["scientific_inventory"]["count"] == 5
    assert contract["runner_inventory"] == {"count": 3, "runner_ids": ["REFERENCE_RUNNER", "ORACLE_RUNNER", "SCIENTIFIC_TEST_RUNNER"]}
    assert contract["environment"]["sha256"] == ENV_SHA
    assert contract["environment"]["extracted_file_count"] == 1662
    for group in (contract["plan_inputs"]["rows"], contract["inherited_inputs"]["rows"]):
        for row in group:
            _bound(row)
    for value in contract["implementation_inputs"].values():
        rows = value if isinstance(value, list) else [value]
        for row in rows:
            _bound(row)

    review, _ = _canonical(REVIEW)
    assert set(review) == {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
    assert review["verdict"] == "ACCEPT_Q1T_EXECUTION_CONTRACT_NO_P0_P1"
    expected = []
    for path in (CONTRACT, Path(__file__)):
        path = path.resolve()
        file_raw = path.read_bytes()
        expected.append({"bytes": len(file_raw), "path": path.relative_to(ROOT).as_posix(), "sha256": _sha(file_raw)})
    assert review["reviewed_inputs"] == sorted(expected, key=lambda row: row["path"])

    head = _git("rev-parse", "HEAD")
    if head == COMMIT2:
        assert not _git("status", "--porcelain", "--untracked-files=no")
    else:
        assert _git("rev-parse", "HEAD^") == COMMIT2
        assert _git("show", "-s", "--format=%s", "HEAD") == COMMIT3_SUBJECT
        actual = sorted(filter(None, _git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()))
        assert actual == sorted(contract["authorization"]["commit3_paths"])
    assert not any((ROOT / path).exists() for path in contract["output_absences"]["paths"])
    assert len(raw) > 0


def _negative(program: str, runner_id: str, tmp_path: Path, output: bool) -> None:
    environment_root_text = os.environ.get("Q1T_EXACT_ENV_ROOT")
    assert environment_root_text
    raw = CONTRACT.read_bytes()
    external_root = Path(tempfile.gettempdir()).resolve()
    missing_authority = external_root / f"q1t-missing-authority-{os.getpid()}-{runner_id}.json"
    forbidden_output = external_root / f"q1t-forbidden-output-{os.getpid()}-{runner_id}.json"
    assert not missing_authority.exists() and not forbidden_output.exists()
    command = [sys.executable, str(ROOT / program), "--authority-record", str(missing_authority), "--authority-sha256", "0" * 64, "--contract", str(CONTRACT), "--contract-sha256", _sha(raw), "--environment-root", environment_root_text, "--environment-sha256", ENV_SHA, "--runner-id", runner_id]
    if output:
        command.extend(["--execute", "--output", str(forbidden_output)])
    else:
        command.append("--authority-check-only")
    completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert completed.returncode != 0
    assert any(token in completed.stderr for token in (b"FAIL_CLOSED", b"BLOCKED_E4_PL_Q1T_CONTRACT_OR_NONDETERMINISM", b"authority record must be a regular nonsymlink file"))
    assert not forbidden_output.exists()


def test_q1t_reference_runner_guard_fails_closed(tmp_path: Path) -> None:
    _negative("docs/reference_cases/e4_pl_q1t_reference.py", "REFERENCE_RUNNER", tmp_path, True)


def test_q1t_oracle_runner_guard_fails_closed(tmp_path: Path) -> None:
    _negative("docs/reference_cases/e4_pl_q1t_oracle.py", "ORACLE_RUNNER", tmp_path, True)


def test_q1t_scientific_runner_guard_fails_closed(tmp_path: Path) -> None:
    _negative("docs/reference_cases/e4_pl_q1t_scientific_test_runner.py", "SCIENTIFIC_TEST_RUNNER", tmp_path, False)
