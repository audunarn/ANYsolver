"""Research-only common authority and deterministic I/O for E4 PL Q1B.

This module deliberately contains no element mechanics.  The producer and
checker share schemas, frozen identifiers, mesh ordering, hashing, and process
guards only; their operator construction remains separate.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence


STUDY_ID = "study_e4_pl_q1b.q1aa_nonintrusion_stability_locking_plan_v1"
CANDIDATE_ID = "candidate_e4_pl_q1b.wg2020_numbered_frame_surface_pl_planar_linear_iso_nonintrusion_stability_locking_v1"
PLAN_SCHEMA = "anysolver.s4.e4-pl-q1b-plan-contract-v1"
MANIFEST_SCHEMA = "anysolver.s4.e4-pl-q1b-implementation-manifest-v1"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1b-execution-contract-v1"
SHARD_SCHEMA = "anysolver.s4.e4-pl-q1b-shard-record-v1"
CHECK_SCHEMA = "anysolver.s4.e4-pl-q1b-shard-check-v1"
CYCLE_SCHEMA = "anysolver.s4.e4-pl-q1b-cycle-v1"
AUTHORITY_SCHEMA = "anysolver.s4.e4-pl-q1b-execution-authority-v1"
CONTRACT_PATH = "docs/reference_cases/e4_pl_q1b_execution_contract.json"
CONTRACT_REVIEW_PATH = "docs/reference_cases/e4_pl_q1b_contract_review.json"
CONTRACT_TEST_PATH = "tests/test_e4_pl_q1b_contract.py"
CONTRACT3_PATHS = (CONTRACT_PATH, CONTRACT_REVIEW_PATH, CONTRACT_TEST_PATH)
COMMIT3_SUBJECT = "docs: authorize E4 PL Q1B bounded assembled execution"
RUNNER_IDS = (
    "Q1B_BOUNDED_COORDINATOR",
    "Q1B_HYBRID_NUMERIC_INTERVAL_PRODUCER",
    "Q1B_INDEPENDENT_AFFINE_AND_EVIDENCE_CHECKER",
)
CONTRACT_KEYS = {
    "agreement","authorization","candidate_id","commit_ancestry","environment",
    "implementation_inputs","inherited_inputs","output_absences","plan_inputs",
    "production_base_commit","production_restriction","q1y3_commissioning",
    "review_authorities","runner_inventory","runtime","schema",
    "scientific_inventory","study_id","terminal_authority",
}
PLAN_INPUT_PATHS = (
    "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md",
    "docs/reference_cases/e4_pl_q1b_baseline.json",
    "docs/reference_cases/e4_pl_q1b_plan_contract.json",
    "docs/reference_cases/e4_pl_q1b_plan_review.json",
    "docs/reference_cases/e4_pl_q1b_test_inventory.json",
    "tests/test_e4_pl_q1b_preregistration_authority.py",
)
IMPLEMENTATION_INPUT_PATHS = (
    "docs/reference_cases/e4_pl_q1b_assembled_checker.py",
    "docs/reference_cases/e4_pl_q1b_assembled_producer.py",
    "docs/reference_cases/e4_pl_q1b_bounded_runner.py",
    "docs/reference_cases/e4_pl_q1b_common.py",
    "docs/reference_cases/e4_pl_q1b_implementation_manifest.json",
    "docs/reference_cases/e4_pl_q1b_implementation_review.json",
    "tests/test_e4_pl_q1b_assembled_stability.py",
    "tests/test_e4_pl_q1b_implementation_authority.py",
    "tests/test_e4_pl_q1b_locking_refinement.py",
    "tests/test_e4_pl_q1b_nonintrusion_recovery.py",
    "tests/test_e4_pl_q1b_runner_bounds.py",
)
SCIENTIFIC_NODES = (
    "tests/test_e4_pl_q1b_assembled_stability.py::test_q1b_supported_assembled_stability_and_coercivity",
    "tests/test_e4_pl_q1b_locking_refinement.py::test_q1b_thickness_and_mesh_locking_sequences",
    "tests/test_e4_pl_q1b_nonintrusion_recovery.py::test_q1b_numerical_diagnostics_remain_outside_physical_recovery",
    "tests/test_e4_pl_q1b_runner_bounds.py::test_q1b_parallel_bounds_timeout_and_determinism",
    "tests/test_e4_pl_q1b_implementation_authority.py::test_q1b_implementation_hashes_and_independence",
)
Q1Y3_PROOFS = (
    ("Q0_SQUARE.proof.json",349048,"CC8CD653401496B81BCB1DD6EFDBFAF69FDA5950AD8D23797BFB5073F2F34117"),
    ("Q1_AFFINE_SKEW.proof.json",1275362,"4E7AE3DBC6FDFDE3B2F6E593D44F3699AB90BDE072D41AF06F2232ACF5706333"),
    ("Q2_TRAPEZOID.proof.json",350387,"297DBE2E242A272148EFA6FB9862A779D629272D739598C2954DDE20DEC66AEE"),
    ("Q3_TAPERED_SKEW.proof.json",1283377,"3B82B7909BB055B56BC30D3FD8929D369415278791A8CB327E96223883BEBF57"),
    ("Q4_HOSTILE_ASYMMETRIC_1.proof.json",1272146,"CDF10D2DD1B2F1A67CA94E21EACCBB6B4A4EC4ED9CB07CB11369349F6484B49F"),
    ("Q5_HOSTILE_ASYMMETRIC_2.proof.json",1278580,"4F501637B4A4C127C71FC39D61CA51D1BE7FD40D5C69901AA582AC22564DFC9E"),
)

SHARDS = ("ASSEMBLED_STABILITY", "LOCKING_REFINEMENT", "NONINTRUSION_RECOVERY")
GEOMETRY_IDS = (
    "Q0_SQUARE", "Q1_AFFINE_SKEW", "Q2_TRAPEZOID",
    "Q3_TAPERED_SKEW", "Q4_HOSTILE_ASYMMETRIC_1",
    "Q5_HOSTILE_ASYMMETRIC_2",
)
GEOMETRY_FAMILIES = (
    "AFFINE_SQUARE", "AFFINE_PARALLELOGRAM", "NONAFFINE_TRAPEZOID",
    "TAPERED_SKEW", "HOSTILE_ASYMMETRIC_1", "HOSTILE_ASYMMETRIC_2",
)
GEOMETRY_MAP = dict(zip(GEOMETRY_FAMILIES, GEOMETRY_IDS, strict=True))
REFINEMENTS = (1, 2, 4, 8)
LOCKING_DIVISIONS = (4, 8, 16, 32)
THICKNESS_RATIOS = ("1e-2", "1e-3", "1e-4", "1e-5", "1e-6")

TERMINALS = (
    "BLOCKED_E4_PL_Q1B_AUTHORITY_OR_REVIEW",
    "BLOCKED_E4_PL_Q1B_IMPLEMENTATION_CONTRACT_OR_NONDETERMINISM",
    "NO_GO_E4_PL_Q1B_ASSEMBLED_STABILITY_OR_COERCIVITY",
    "NO_GO_E4_PL_Q1B_LOCKING_OR_CATEGORY_DRIFT",
    "NO_GO_E4_PL_Q1B_NONINTRUSION_OR_RECOVERY_SEPARATION",
    "UNCLASSIFIED_E4_PL_Q1B_BOUNDED_ASSEMBLED_EVIDENCE",
    "PROVISIONAL_GO_E4_PL_Q1B_LINEAR_STATIC_INTEGRATION_PLAN",
)

OUTCOME_PATHS = (
    "docs/reference_cases/e4_pl_q1b_cycle1.json",
    "docs/reference_cases/e4_pl_q1b_cycle2.json",
    "docs/reference_cases/e4_pl_q1b_agreement.json",
    "docs/reference_cases/e4_pl_q1b_output.json",
    "docs/reference_cases/e4_pl_q1b_status.json",
    "docs/reference_cases/e4_pl_q1b_execution_authority.json",
    "docs/reference_cases/e4_pl_q1b_scientific_test_result.json",
    "docs/E4_PL_Q1B_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1b_scientific_review.json",
    "docs/E4_PL_Q1B_COMPLETION.md",
    "tests/test_e4_pl_q1b_closeout.py",
)


class Q1BError(RuntimeError):
    """Fail-closed Q1B authority or evidence error."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def read_json(path: Path) -> tuple[bytes, Any]:
    if path.is_symlink() or not path.is_file():
        raise Q1BError(f"not a regular JSON file: {path}")
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"), parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise Q1BError(f"invalid JSON: {path}") from exc
    if canonical_bytes(value) != raw:
        raise Q1BError(f"noncanonical JSON: {path}")
    return raw, value


def read_registered_cycle(path: Path, *, expected_cycle: int, expected_contract_sha256: str) -> tuple[bytes, dict[str, Any], bytes]:
    """Strictly verify a promoted registered-cycle wrapper and common payload."""
    raw,value=read_json(path)
    required={"candidate_id","common_payload","common_payload_sha256","contract_sha256","cycle","diagnostic_hashes","schema","study_id"}
    if not isinstance(value,dict) or set(value)!=required or value.get("schema")!=CYCLE_SCHEMA or value.get("candidate_id")!=CANDIDATE_ID or value.get("study_id")!=STUDY_ID or value.get("cycle")!=expected_cycle or value.get("contract_sha256")!=expected_contract_sha256.upper():
        raise Q1BError("registered cycle wrapper mismatch")
    payload=value.get("common_payload")
    payload_raw=canonical_bytes(payload)
    if value.get("common_payload_sha256")!=sha256(payload_raw):
        raise Q1BError("registered common payload hash mismatch")
    if not isinstance(payload,dict) or set(payload)!={"candidate_id","coverage","production","shards","study_id","terminal"} or payload.get("candidate_id")!=CANDIDATE_ID or payload.get("study_id")!=STUDY_ID or payload.get("production")!="NO_GO_PRODUCTION_RESTRICTION_UNCHANGED" or payload.get("terminal") not in TERMINALS:
        raise Q1BError("registered common payload schema mismatch")
    if [row.get("shard") for row in payload.get("shards",[])]!=list(SHARDS):
        raise Q1BError("registered common payload shard order mismatch")
    diagnostics=value.get("diagnostic_hashes")
    if not isinstance(diagnostics,list) or [row.get("shard") for row in diagnostics]!=list(SHARDS):
        raise Q1BError("registered diagnostic hash order mismatch")
    for row in diagnostics:
        if set(row)!={"check_sha256","producer_sha256","shard"} or any(len(row[key])!=64 or row[key]!=row[key].upper() for key in ("check_sha256","producer_sha256")):
            raise Q1BError("registered diagnostic hash schema mismatch")
    return raw,value,payload_raw


def write_exclusive(path: Path, value: Any) -> bytes:
    raw = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    if path.read_bytes() != raw:
        raise Q1BError("exclusive output reopen mismatch")
    return raw


def verify_file(path: Path, *, bytes_count: int, digest: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise Q1BError(f"bound file missing or symlink: {path}")
    raw = path.read_bytes()
    if len(raw) != bytes_count or sha256(raw) != digest.upper():
        raise Q1BError(f"bound file identity mismatch: {path}")
    return raw


def git(repository_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository_root), *args], capture_output=True,
        text=True, check=False, timeout=30,
    )
    if result.returncode:
        raise Q1BError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_bytes(repository_root: Path, *args: str) -> bytes:
    result = subprocess.run(["git","-C",str(repository_root),*args],capture_output=True,check=False,timeout=30)
    if result.returncode:
        raise Q1BError(f"git {' '.join(args)} failed")
    return result.stdout


def require_clean_tracked(repository_root: Path) -> None:
    if git(repository_root, "diff", "--name-only") or git(repository_root, "diff", "--cached", "--name-only"):
        raise Q1BError("tracked worktree or index is not clean")


def require_outcomes_absent(repository_root: Path) -> None:
    present = [path for path in OUTCOME_PATHS if (repository_root / path).exists()]
    if present:
        raise Q1BError(f"outcome path exists before execution: {present[0]}")


def require_no_production_delta(repository_root: Path, base: str) -> None:
    protected = ("src/", ".github/", "pyproject.toml", ".gitattributes")
    changed = git(repository_root, "diff", "--name-only", f"{base}..HEAD").splitlines()
    bad = [path for path in changed if path == "pyproject.toml" or path == ".gitattributes" or path.startswith(protected[:2])]
    if bad:
        raise Q1BError(f"production boundary changed: {bad[0]}")


def validate_execution_authority(
    *, repository_root: Path, contract_path: Path, contract_sha256: str,
    authority_path: Path, authority_sha256: str, runner_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate caller-bound Commit-3 authority before importing mechanics."""
    root = Path(git(repository_root,"rev-parse","--show-toplevel")).resolve()
    if os.path.normcase(os.path.normpath(str(root))) != os.path.normcase(os.path.normpath(str(repository_root.resolve()))):
        raise Q1BError("repository root mismatch")
    expected_contract_path = (root / CONTRACT_PATH).resolve()
    if contract_path.is_symlink() or os.path.normcase(os.path.normpath(str(contract_path.resolve()))) != os.path.normcase(os.path.normpath(str(expected_contract_path))):
        raise Q1BError("contract path is not the committed CONTRACT3 artifact")
    contract_raw, contract = read_json(contract_path)
    authority_raw, authority = read_json(authority_path)
    if sha256(contract_raw) != contract_sha256.upper() or sha256(authority_raw) != authority_sha256.upper():
        raise Q1BError("caller-bound authority hash mismatch")
    if set(contract) != CONTRACT_KEYS or contract.get("schema") != CONTRACT_SCHEMA or authority.get("schema") != AUTHORITY_SCHEMA:
        raise Q1BError("authority schema mismatch")
    required = {"authorization","candidate_id","commit","contract_review_sha256","contract_sha256","implementation_commit","implementation_review_sha256","plan_review_sha256","production","runner_ids","schema","study_id","tree"}
    if set(authority) != required or authority.get("candidate_id") != CANDIDATE_ID or authority.get("study_id") != STUDY_ID:
        raise Q1BError("execution authority content mismatch")
    if authority.get("authorization") != contract["authorization"]["token"] or authority.get("production") != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED":
        raise Q1BError("authority token or production restriction mismatch")
    if authority.get("contract_sha256") != contract_sha256.upper() or authority.get("runner_ids") != list(RUNNER_IDS) or runner_id not in RUNNER_IDS:
        raise Q1BError("runner is not caller-authorized")
    head = git(root,"rev-parse","HEAD")
    if head != authority["commit"] or git(root,"rev-parse","HEAD^{tree}") != authority["tree"]:
        raise Q1BError("execution authority HEAD mismatch")
    if git(root,"show","-s","--format=%s",head) != COMMIT3_SUBJECT or sorted(git(root,"diff-tree","--no-commit-id","--name-only","-r",head).splitlines()) != sorted(CONTRACT3_PATHS):
        raise Q1BError("Commit3 subject or exact extent mismatch")
    parent = git(root,"rev-parse","HEAD^")
    implementation = contract["commit_ancestry"]["implementation"]
    if parent != implementation["commit"] or authority["implementation_commit"] != parent:
        raise Q1BError("Commit3 parent is not the bound implementation commit")
    if git_bytes(root,"show",f"HEAD:{CONTRACT_PATH}") != contract_raw:
        raise Q1BError("contract bytes are not committed at HEAD")
    if contract["authorization"] != {"commit3_paths":list(CONTRACT3_PATHS),"commit3_subject":COMMIT3_SUBJECT,"hard_freeze_event":"FIRST_SCHEMA_VALID_CANONICAL_REGISTERED_SHARD_EXCLUSIVELY_CREATED_REOPENED_AND_HASH_VERIFIED","token":"AUTHORIZE_E4_PL_Q1B_BOUNDED_ASSEMBLED_EXECUTION"}:
        raise Q1BError("contract authorization mismatch")
    if contract["runner_inventory"] != {"commissioning_before_mechanics":True,"runner_ids":list(RUNNER_IDS)}:
        raise Q1BError("contract runner inventory mismatch")
    if contract["runtime"] != {"automatic_retry":False,"memory_limit_gib_per_process":24,"numerical_threads_per_process":1,"timeout_seconds_per_process":600,"worker_count":3}:
        raise Q1BError("contract runtime mismatch")
    expected_environment={"numpy":"2.4.3","pytest":"9.0.1","python_implementation":"CPython","python_version":"3.13.9","q1t_exact_environment":{"bytes":227603,"path":"docs/reference_cases/e4_pl_q1t_environment.json","sha256":"5461206324E7FC2A52B334CE736A512EE71313ED79181438047E3E20069A9746"},"scipy":"1.16.3"}
    if contract["environment"] != expected_environment or sys.implementation.name != "cpython" or ".".join(map(str,sys.version_info[:3])) != "3.13.9":
        raise Q1BError("active Python or environment authority mismatch")
    for package,version in (("numpy","2.4.3"),("scipy","1.16.3"),("pytest","9.0.1")):
        if importlib.metadata.version(package) != version:
            raise Q1BError(f"active {package} version mismatch")
    environment_row=expected_environment["q1t_exact_environment"]
    environment_raw=verify_file(root/environment_row["path"],bytes_count=environment_row["bytes"],digest=environment_row["sha256"])
    if git_bytes(root,"show",f"HEAD:{environment_row['path']}") != environment_raw:
        raise Q1BError("Q1T environment record is not committed unchanged")
    if contract["output_absences"] != sorted(OUTCOME_PATHS) or contract["terminal_authority"] != list(TERMINALS):
        raise Q1BError("contract outcomes or terminal authority mismatch")
    if contract["scientific_inventory"] != list(SCIENTIFIC_NODES):
        raise Q1BError("scientific inventory mismatch")
    if contract["inherited_inputs"] != {"count":12,"source":"docs/reference_cases/e4_pl_q1b_baseline.json","source_sha256":"710C886A29ABBF8FDB4A5051C9005071831403D458D91ECB2EEFEC86E9C28692"}:
        raise Q1BError("inherited authority mismatch")
    expected_proofs=[{"bytes":size,"name":name,"sha256":digest} for name,size,digest in Q1Y3_PROOFS]
    if contract["q1y3_commissioning"] != {"classification":"EXACT_EQUIVALENCE_COMMISSIONING_INPUT","proofs":expected_proofs}:
        raise Q1BError("Q1Y3 commissioning authority mismatch")
    for group, commit in ((contract["plan_inputs"], parent),(contract["implementation_inputs"],parent)):
        if group.get("count") != len(group.get("rows",[])):
            raise Q1BError("contract input count mismatch")
        for row in group["rows"]:
            path = root / row["path"]
            raw = verify_file(path,bytes_count=row["bytes"],digest=row["sha256"])
            if git(root,"rev-parse",f"{commit}:{row['path']}") != row["git_blob"] or git_bytes(root,"show",f"{commit}:{row['path']}") != raw:
                raise Q1BError("contract input Git binding mismatch")
    if tuple(sorted(row["path"] for row in contract["plan_inputs"]["rows"])) != tuple(sorted(PLAN_INPUT_PATHS)) or tuple(sorted(row["path"] for row in contract["implementation_inputs"]["rows"])) != tuple(sorted(IMPLEMENTATION_INPUT_PATHS)):
        raise Q1BError("contract input path extent mismatch")
    review_rows = contract["review_authorities"]
    expected_review_authorities={
        "plan":{"path":"docs/reference_cases/e4_pl_q1b_plan_review.json","sha256":authority["plan_review_sha256"],"verdict":"ACCEPT_Q1B_PREREGISTRATION_NO_P0_P1"},
        "implementation":{"path":"docs/reference_cases/e4_pl_q1b_implementation_review.json","sha256":authority["implementation_review_sha256"],"verdict":"ACCEPT_Q1B_IMPLEMENTATION_FREEZE_NO_P0_P1"},
        "contract":{"hash_binding":"EXTERNAL_AUTHORITY_RECORD","path":CONTRACT_REVIEW_PATH,"verdict":"ACCEPT_Q1B_EXECUTION_CONTRACT_NO_P0_P1"},
    }
    if review_rows!=expected_review_authorities:
        raise Q1BError("contract review authority rows mismatch")
    review_specs = (
        ("plan", "docs/reference_cases/e4_pl_q1b_plan_review.json", "ACCEPT_Q1B_PREREGISTRATION_NO_P0_P1", authority["plan_review_sha256"]),
        ("implementation", "docs/reference_cases/e4_pl_q1b_implementation_review.json", "ACCEPT_Q1B_IMPLEMENTATION_FREEZE_NO_P0_P1", authority["implementation_review_sha256"]),
        ("contract", CONTRACT_REVIEW_PATH, "ACCEPT_Q1B_EXECUTION_CONTRACT_NO_P0_P1", authority["contract_review_sha256"]),
    )
    for key, path_text, verdict, expected_hash in review_specs:
        raw, review = read_json(root/path_text)
        if sha256(raw) != expected_hash or review_rows[key]["path"] != path_text or review.get("verdict") != verdict or review.get("findings") != [] or set(review) != {"findings","reviewed_inputs","reviewer_independence","schema","verdict"}:
            raise Q1BError("review authority content mismatch")
        if key != "contract" and review_rows[key]["sha256"] != expected_hash:
            raise Q1BError("bound review hash mismatch")
        if key == "contract" and review_rows[key].get("hash_binding") != "EXTERNAL_AUTHORITY_RECORD":
            raise Q1BError("contract review hash binding mismatch")
        expected_independence = {
            "plan":{"mechanics_executed":False,"reviewer_role":"INDEPENDENT_Q1B_PLAN_REVIEWER","same_agent_as_packet_author":False},
            "implementation":{"authored_review_only":True,"mechanics_executed":False,"reviewed_input_authorship":False,"role":"INDEPENDENT_STATIC_IMPLEMENTATION_REVIEWER"},
            "contract":{"authored_review_only":True,"mechanics_executed":False,"reviewed_input_authorship":False,"role":"INDEPENDENT_EXECUTION_CONTRACT_REVIEWER"},
        }[key]
        if review.get("reviewer_independence") != expected_independence:
            raise Q1BError("review independence mismatch")
        expected_reviewed_paths={
            "plan":set(PLAN_INPUT_PATHS)-{"docs/reference_cases/e4_pl_q1b_plan_review.json"},
            "implementation":set(IMPLEMENTATION_INPUT_PATHS)-{"docs/reference_cases/e4_pl_q1b_implementation_review.json"},
            "contract":{CONTRACT_PATH,CONTRACT_TEST_PATH},
        }[key]
        reviewed_rows=review.get("reviewed_inputs",[])
        if not isinstance(reviewed_rows,list) or len(reviewed_rows)!=len(expected_reviewed_paths) or {row.get("path") for row in reviewed_rows}!=expected_reviewed_paths:
            raise Q1BError("reviewed input extent mismatch")
        for row in reviewed_rows:
            review_input=root/row["path"]
            if set(row)!={"bytes","path","sha256"} or review_input.stat().st_size!=row["bytes"] or sha256(review_input.read_bytes())!=row["sha256"]:
                raise Q1BError("reviewed input identity mismatch")
    require_clean_tracked(root)
    require_outcomes_absent(root)
    require_no_production_delta(root, contract["production_base_commit"])
    return contract, authority


@dataclass(frozen=True)
class Bound:
    """Conservative scalar enclosure recorded as hexadecimal binary64 bounds."""

    lo: float
    hi: float

    def __post_init__(self) -> None:
        if not (math.isfinite(self.lo) and math.isfinite(self.hi) and self.lo <= self.hi):
            raise Q1BError("invalid finite bound")

    @classmethod
    def around(cls, value: float, operations: int = 1) -> "Bound":
        radius = max(1, int(operations)) * 16.0 * sys.float_info.epsilon * max(1.0, abs(float(value)))
        return cls(math.nextafter(float(value) - radius, -math.inf), math.nextafter(float(value) + radius, math.inf))

    def record(self) -> dict[str, str]:
        return {"hi": self.hi.hex(), "lo": self.lo.hex()}

    @classmethod
    def from_record(cls, value: Mapping[str, str]) -> "Bound":
        if set(value) != {"hi", "lo"}:
            raise Q1BError("bound record keys mismatch")
        return cls(float.fromhex(value["lo"]), float.fromhex(value["hi"]))


def bilinear(nodes: Sequence[Sequence[float]], r: float, s: float) -> tuple[float, float, float]:
    shape = ((1-r)*(1-s)/4, (1+r)*(1-s)/4, (1+r)*(1+s)/4, (1-r)*(1+s)/4)
    return tuple(sum(shape[i] * float(nodes[i][j]) for i in range(4)) for j in range(3))  # type: ignore[return-value]


def uniform_mesh(nodes: Sequence[Sequence[float]], divisions: int) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int, int]]]:
    if divisions < 1:
        raise Q1BError("mesh division must be positive")
    points: list[tuple[float, float, float]] = []
    for j in range(divisions + 1):
        s = -1.0 + 2.0 * j / divisions
        for i in range(divisions + 1):
            r = -1.0 + 2.0 * i / divisions
            points.append(bilinear(nodes, r, s))
    elements: list[tuple[int, int, int, int]] = []
    stride = divisions + 1
    for j in range(divisions):
        for i in range(divisions):
            n0 = j * stride + i
            elements.append((n0, n0 + 1, n0 + stride + 1, n0 + stride))
    return points, elements


def strict_record(value: Any, keys: Iterable[str], schema: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != set(keys) or value.get("schema") != schema:
        raise Q1BError(f"{schema} record mismatch")
    return value


def choose_terminal(*, blocked: bool, stability_no_go: bool, locking_no_go: bool, nonintrusion_no_go: bool, unresolved: bool) -> str:
    if blocked:
        return TERMINALS[1]
    if stability_no_go:
        return TERMINALS[2]
    if locking_no_go:
        return TERMINALS[3]
    if nonintrusion_no_go:
        return TERMINALS[4]
    if unresolved:
        return TERMINALS[5]
    return TERMINALS[6]


def one_thread_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "1"
    environment["PYTHONHASHSEED"] = "0"
    return environment
