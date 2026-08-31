"""Bounded coordinator for the formal S3 V2A Stage-4A funnel.

The coordinator validates the frozen Git candidate before numerical imports,
creates an exact source archive and three-shard producer manifest, runs the
existing Windows Job-Object wave, then runs two independent checker replicas
per shard.  It publishes one canonical aggregate only after every launched
process has reached a proven terminal state.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
AUTHORITY_PATH = REFERENCE_CASES / "e4_pl_s3_v2_stage4a_authority.json"
MANIFEST_PATH = REFERENCE_CASES / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
SCAFFOLD_CONTRACT_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel_contract.json"
SOURCE_CONTRACT_PATH = REFERENCE_CASES / "e4_pl_s3_v2_source_equation_contract.json"
PRODUCER_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel_producer.py"
CHECKER_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel_checker.py"
FUNNEL_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel.py"
BOUNDED_PATH = REFERENCE_CASES / "e4_pl_s3_v2_bounded_process.py"

CONTRACT_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-contract-v5"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-execution-authorization-v2"
AUTHORITY_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-authority-v5"
REVIEW_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-implementation-review-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-aggregate-v2"
CHECKER_RESULT_SCHEMA = "anysolver.e4-pl-s3-v2-phase4a-checker-result-v1"
PRODUCER_RESULT_SCHEMA = "anysolver.e4-pl-s3-v2-bounded-wave-result-v1"
BLOCKED = "BLOCKED_E4_PL_S3_V2_PROCESS_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V2A_MIXED_FLEXURAL_CONVERGENCE"
PASS = "PASS_E4_PL_S3_V2A_FLAT_FUNNEL_PHASE_4A"
PRODUCTION_RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
CHECKER_WALL_SECONDS = 300
WAVE_WALL_SECONDS = 1800
COORDINATOR_WALL_SECONDS = 1800
COORDINATOR_FAIL_CLOSED_PUBLICATION_RESERVE_SECONDS = 15
COORDINATOR_HARD_EXIT_CODE = 124
GIT_SUBPROCESS_WALL_SECONDS = 60
MEMORY_LIMIT_BYTES = 24 * (1 << 30)
OS_HEADROOM_BYTES = 16 * (1 << 30)
MAXIMUM_REGISTERED_WORKERS = 3
MAXIMUM_CONCURRENT_WORKERS = 2
WORKER_SCHEDULE = "TWO_CONCURRENT_THEN_REMAINING_ONE_IN_FROZEN_ORDER"
CHECKER_PHASE_SCHEDULE = "REPLICA_PAIRS_BY_FROZEN_SHARD_ORDER"
CHECKER_PHASE_FINALIZATION_RESERVE_SECONDS = 60
CHECKER_PHASE_REQUIRED_SECONDS = 960
EXPECTED_SHARDS = {
    "S3_V2_FLAT_4A_SLASH": "slash",
    "S3_V2_FLAT_4A_BACKSLASH": "backslash",
    "S3_V2_FLAT_4A_ALTERNATING": "alternating",
}
DIAGONAL_ORDER = ("slash", "backslash", "alternating")
MASK_ORDER = ("dispersed", "chain")
FRACTION_ORDER = (1, 5, 10, 25)
RESOURCE_MANAGER_ROOT = Path(r"C:\Github\.resource-manager")
RESOURCE_LEDGER_PATH = RESOURCE_MANAGER_ROOT / "ledger.md"
RESOURCE_LOCK_OWNER_PATH = RESOURCE_MANAGER_ROOT / "active-lock" / "owner.json"
PREDECESSOR_INCIDENT_ROOT = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2-stage4a-20260831-cycle1"
)
PREDECESSOR_REPOSITORY = (
    r"C:\Github\ANYsolver\.perf2-worktrees\s3-e4-pl-v2-formulation"
)
PREDECESSOR_REQUEST_ID = "98dfaf4a153a4bb7bcce46c11d9de13a"
PREDECESSOR_REQUESTED_AT = "2026-08-31T09:06:41.6684913+02:00"
PREDECESSOR_TASK = "ANYsolver S3 V2A Stage 4A bounded mixed-flexural gate"
PREDECESSOR_REQUEST_SHA256 = (
    "4E272F0B247C496AEE65645B5E4AADE7D2E0136491A1DD77128558ABFB926559"
)
PREDECESSOR_COMMAND_SHA256 = (
    "4E5564A38C85DB66803F4337D69800DC8DD3736A478E84EC69A8EBDCA3CAC55B"
)
PREDECESSOR_AUTHORIZATION_COMMIT = "37af54dd1c2684010a5c41c30e82df92b2558004"
PREDECESSOR_AUTHORIZATION_TREE = "75fd1d5d36ba7834c6c783633fe73b85e17092f9"
PREDECESSOR_AUTHORIZATION_PARENT = "b79932e8b745153d7fae77c5d092011d39333125"
PREDECESSOR_AUTHORIZATION_SUBJECT = (
    "docs: authorize S3 V2A Stage 4A formal execution"
)
PREDECESSOR_AUTHORIZATION_PATH = (
    "docs/reference_cases/e4_pl_s3_v2_stage4a_execution_authorization.json"
)
PREDECESSOR_AUTHORIZATION_SHA256 = (
    "0A48D63557CF82CE9401DC2C2DB1049683E540104B17647C80172F6FCC966F20"
)
PREDECESSOR_AUTHORIZATION_BYTE_COUNT = 2336
PREDECESSOR_CONTRACT_PATH = (
    "docs/reference_cases/e4_pl_s3_v2_stage4a_contract.json"
)
PREDECESSOR_CONTRACT_SHA256 = (
    "C3A5F67633B7F7016141E2B3F526F2DF8A4A0B91A5E66DC9D4957F7CE1C21A60"
)
PREDECESSOR_CONTRACT_BYTE_COUNT = 8079
PREDECESSOR_CANDIDATE_COMMIT = "b382215b531568910db846ce7212580eefa5746e"
PREDECESSOR_CANDIDATE_TREE = "12b76c6a4e5fa0aeead61085c635344bc38f58fe"
PREDECESSOR_COORDINATOR_SHA256 = (
    "9084E9AACB901492726541EA137176C863B6452F35ABE6D7F5820F001AF9D63B"
)
PREDECESSOR_BOUNDED_SHA256 = (
    "15D30B50668BE82F2EB70D913137FA66B1084AFF19AC3998943E376C9724518D"
)
PREDECESSOR_CONNECTIVITY_MANIFEST_SHA256 = (
    "3EA7ABD0B332831D62B30B3CD52E0DB85EC951B125340FFAF40A891DC37BD589"
)
PREDECESSOR_LEDGER_ROW_SHA256 = {
    "APPROVED": "F369A3D0390937653BC1097C0BF1C6CE18AFC828CB93173F93E5E0DE28CD0718",
    "EXECUTION_STARTED": "F4AA97F951460D8DB748AC31102E28A6CE887B0BADDDC229DDD76F7ED6B7C0C3",
    "COMPLETED_FAIL": "890184F7F2E9BF1FCF4862715E566ED84DCE4C805E80EFD87FFB1D44F995D2F3",
}
PREDECESSOR_ARTIFACTS = {
    "aggregate": (
        "stage4a-aggregate.json",
        613,
        "575BD64910B30B38F7A80A29C98A196F4D4499FC1D9D60AF62C37D600D45239F",
    ),
    "approval_snapshot": (
        "approval-snapshot.json",
        1427,
        "5A706825428F8F9D45A183AFC1227623234A17691AC1343B3C81A6618CF0F6DF",
    ),
    "candidate_archive": (
        "candidate-source.tar",
        27_166_720,
        "8888007F135F5D0977DDC5B7DAB02A7D882A8D7163CC033ACEE314F0F037AB3F",
    ),
    "candidate_binding": (
        "candidate-source-binding.json",
        507,
        "60FD209E00B187BD64F9E3C3B9542694C81190EFC02ECB75FF31312A65F2991D",
    ),
    "ledger_snapshot": (
        "resource-ledger-pre-run.md",
        92_923,
        "DD38D91CF636D94D567FA79FED928727CE0C6BEC4633D46FEB64068EF8429EB5",
    ),
    "manifest": (
        "producer-wave-manifest.json",
        12_259,
        "432E1CCB99CFBA1EAA3FEBA29AA2E97530BC27F60BBB9F341BCB9EF892D653E5",
    ),
    "phase_plan": (
        "phase4a-plan.json",
        40_609,
        "03095DB243064F7D70F9EA0BF4CCCCEF36DF983D441B5A3B09E8D6568412C9E0",
    ),
    "transcript": (
        "formal-transcript.txt",
        4031,
        "1F9317E839A9451B6B97F0E0D60A4B5E316F74D3F754B90763A754081C89931B",
    ),
}
RESOURCE_DEFERRED_INCIDENT_ROOT = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2-stage4a-20260831-correction1-cycle1"
)
RESOURCE_DEFERRED_REPOSITORY = PREDECESSOR_REPOSITORY
RESOURCE_DEFERRED_REQUEST_ID = "3725cb19803543bfa789903b2a11f59a"
RESOURCE_DEFERRED_REQUESTED_AT = "2026-08-31T09:58:56.9567735+02:00"
RESOURCE_DEFERRED_TASK = PREDECESSOR_TASK
RESOURCE_DEFERRED_REQUEST_BYTE_COUNT = 1335
RESOURCE_DEFERRED_REQUEST_SHA256 = (
    "3BD8B7CE627647C563F8FA8D32F61F3E80322914358259364EAF6CA7280D81C6"
)
RESOURCE_DEFERRED_COMMAND_SHA256 = (
    "DAC6537170A4315EE72983954DB68B404A9F7DB95A70E1E9A4929AB46572DC8C"
)
RESOURCE_DEFERRED_ATTEMPT_BYTE_COUNT = 182
RESOURCE_DEFERRED_ATTEMPT_SHA256 = (
    "A3BC7CD54F2EF5AF1F36172F77EDC914567FF23F6FE168C279D278D5ADD32BD7"
)
RESOURCE_DEFERRED_AUTHORIZATION_COMMIT = (
    "b428c772e509b8e599af09f6d9f548fdaf9eef94"
)
RESOURCE_DEFERRED_AUTHORIZATION_TREE = "f663d308ccafbb76cc02968bf432df153c538156"
RESOURCE_DEFERRED_AUTHORIZATION_PARENT = (
    "88836999a43b70ac6c2b8c2c14a19bb7b7ada060"
)
RESOURCE_DEFERRED_AUTHORIZATION_SUBJECT = (
    "docs: reauthorize corrected S3 V2A Stage 4A execution"
)
RESOURCE_DEFERRED_AUTHORIZATION_BYTE_COUNT = 2394
RESOURCE_DEFERRED_AUTHORIZATION_SHA256 = (
    "F92015A3B16398C17EC5FD52A87949225A14436794D6A20DECF3EA84090DF5FB"
)
RESOURCE_DEFERRED_CONTRACT_COMMIT = "17a8bf10ae65f0ecc8e6d3c91864fa6f118a0145"
RESOURCE_DEFERRED_CONTRACT_TREE = "427f0e9d70046ab98c202cc59a06c311a006ee17"
RESOURCE_DEFERRED_CONTRACT_PARENT = "2d924788b05115ba3318bacb538f5040684ac1ae"
RESOURCE_DEFERRED_CONTRACT_SUBJECT = "docs: refreeze Stage 4A after process incident"
RESOURCE_DEFERRED_CONTRACT_BYTE_COUNT = 12_324
RESOURCE_DEFERRED_CONTRACT_SHA256 = (
    "B32545BF9559D1F5DE9F91473767BEADC2ED13F2D42FD8AC8371D5FA775A50EE"
)
RESOURCE_DEFERRED_CANDIDATE_COMMIT = "2d924788b05115ba3318bacb538f5040684ac1ae"
RESOURCE_DEFERRED_CANDIDATE_TREE = "7c961d3ee6dee727a2f22ac2b9d858055e770be5"
RESOURCE_DEFERRED_AUTHORITY_SHA256 = (
    "17B7B768EDE593A600F4B37C120E0653BE3C522B2E5C62687EFCD8C02272C322"
)
RESOURCE_DEFERRED_COORDINATOR_SHA256 = (
    "3338C3C48C518F207CDB78A43952F0D168A53693F528E749082F96B46704BEB8"
)
RESOURCE_DEFERRED_BOUNDED_SHA256 = PREDECESSOR_BOUNDED_SHA256
RESOURCE_DEFERRED_CONNECTIVITY_MANIFEST_SHA256 = (
    PREDECESSOR_CONNECTIVITY_MANIFEST_SHA256
)
RESOURCE_DEFERRED_ARCHIVE_REF = (
    "refs/archive/s3-v2-stage4a-resource-deferred-correction1-cycle1"
)
RESOURCE_DEFERRED_ARCHIVE_COMMIT = RESOURCE_DEFERRED_AUTHORIZATION_COMMIT
RESOURCE_DEFERRED_CANDIDATE_FILE_COUNT = 995
RESOURCE_DEFERRED_CANDIDATE_DIRECTORY_COUNT = 15
RESOURCE_DEFERRED_OLD_ADMISSION_REQUIRED_BYTES = 94_489_280_512
RESOURCE_DEFERRED_LEDGER_ROW_SHA256 = {
    "APPROVED": "5011DA117D98DC5F9850B41B28E814625EA00DAD523E65C121691BEEC103CD73",
    "EXECUTION_STARTED": "CE4FABF5E412C281C730E0D972E58D753C80F2B3AFEC8B48F724C9ADF9E9524C",
    "COMPLETED_FAIL": "1CC6AC5D477B134CD7A3FC2C834A8DE21FD5B8C3E81E84704FFB9C718B0F4718",
}
RESOURCE_DEFERRED_ARTIFACTS = {
    "aggregate": (
        "stage4a-aggregate.json",
        681,
        "87FD564CD9C68385B7C1A36DBC8D7817508813C57B0E060F6C07B39342211B49",
    ),
    "approval_snapshot": (
        "approval-snapshot.json",
        1500,
        "E4B84F20AEE7FB5C6C9CF36FB63C5A343522B5DDF5DB716EA18695E10BB70646",
    ),
    "candidate_archive": (
        "candidate-source.tar",
        27_238_400,
        "EC79D671E0381B98D984F4BA0F493C4C9CC073F3967E20BAA935E1BDBEA453A8",
    ),
    "candidate_binding": (
        "candidate-source-binding.json",
        519,
        "D63EEF89BB81C5E83E3AF2CB577DAF699F14D1474574778960BBCBB251E6479D",
    ),
    "ledger_snapshot": (
        "resource-ledger-pre-run.md",
        95_210,
        "79CA316DAF38E24E1958218165EE2475BF5755FAEF78DC904EDE0325843F64B8",
    ),
    "manifest": (
        "producer-wave-manifest.json",
        12_667,
        "C5BCE5CDF047E7AC3894D7AE4AD6629D194CC3EF11894552101786B9C0AF8D47",
    ),
    "phase_plan": (
        "phase4a-plan.json",
        40_609,
        "03095DB243064F7D70F9EA0BF4CCCCEF36DF983D441B5A3B09E8D6568412C9E0",
    ),
    "transcript": (
        "formal-transcript.txt",
        4162,
        "767F1E5666875E5197C0F94FF8CBCE1621DF75B353F5A97269835EA5F53A15D4",
    ),
}
RESOURCE_DEFERRED_PRODUCER_RESULT = (
    "producer-wave/producer-wave-result.json",
    245,
    "7DF0A1759C6E99BC099486BB425BD345093578B4C699681853810796B471BB9B",
)
CONTRACT_KEYS = frozenset(
    {
        "adjudication",
        "authority",
        "candidate",
        "coverage",
        "dependencies",
        "execution",
        "frozen_files",
        "git_authority",
        "predecessor_process_incident",
        "predecessor_resource_deferred_incident",
        "production_boundary",
        "protocol",
        "schema",
        "stage",
    }
)
PROCESS_REVIEW_PATH = (
    REFERENCE_CASES / "e4_pl_s3_v2_stage4a_process_implementation_review.json"
)
SCIENTIFIC_REVIEW_PATH = (
    REFERENCE_CASES / "e4_pl_s3_v2_stage4a_scientific_implementation_review.json"
)
EXPECTED_REVIEW_VERDICTS = {
    "PROCESS_AND_AUTHORITY": "ACCEPT_STAGE4A_PROCESS_IMPLEMENTATION_NO_P0_P1",
    "SCIENTIFIC_AND_MECHANICS": "ACCEPT_STAGE4A_SCIENTIFIC_IMPLEMENTATION_NO_P0_P1",
}
REQUIRED_FROZEN_PATHS = {
    "docs/reference_cases/e4_pl_s3_mixed_mesh_connectivity_manifest.json",
    "docs/reference_cases/e4_pl_s3_v2_bounded_process.py",
    "docs/reference_cases/e4_pl_s3_v2_candidate_binding.json",
    "docs/reference_cases/e4_pl_s3_v2_flat_funnel.py",
    "docs/reference_cases/e4_pl_s3_v2_flat_funnel_checker.py",
    "docs/reference_cases/e4_pl_s3_v2_flat_funnel_contract.json",
    "docs/reference_cases/e4_pl_s3_v2_flat_funnel_producer.py",
    "docs/reference_cases/e4_pl_s3_v2_source_equation_contract.json",
    "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json",
    "docs/reference_cases/e4_pl_s3_v2_stage4a_coordinator.py",
    "src/anysolver/e4_pl_element.py",
    "src/anysolver/e4_pl_s3_element.py",
    "src/anysolver/e4_pl_s3_v2_element.py",
    "tests/test_e4_pl_s3_v2_candidate_binding.py",
    "tests/test_e4_pl_s3_v2_bounded_process.py",
    "tests/test_e4_pl_s3_v2_flat_candidate_review.py",
    "tests/test_e4_pl_s3_v2_flat_funnel_checker.py",
    "tests/test_e4_pl_s3_v2_flat_funnel_producer.py",
    "tests/test_e4_pl_s3_v2_mixed_scope.py",
    "tests/test_e4_pl_s3_v2_stage4a_authority.py",
    "tests/test_e4_pl_s3_v2_stage4a_coordinator.py",
}
DEPENDENCY_REPOSITORIES = (
    ("ANYmaterial", Path(r"C:\Github\ANYmaterial")),
    ("ANYgeometry", Path(r"C:\Github\ANYgeometry")),
    (
        "ANYmesh",
        Path(
            r"C:\Github\ANYsolver\.perf2-worktrees\s3-v2-stage4a-anymesh-dependency"
        ),
    ),
    ("ANYfileIO", Path(r"C:\Github\ANYfileIO")),
)


class CoordinatorError(RuntimeError):
    """Raised when formal process or evidence authority is incomplete."""


class _CoordinatorWallExceeded(CoordinatorError):
    """Raised when cooperative work reaches the reserved publication window."""


class _CheckerTreeNotDrained(CoordinatorError):
    """Raised when a checker Job cannot prove that its process tree is empty."""


class _CheckerPhaseError(CoordinatorError):
    """Carry checker-phase tree-drain disposition to the coordinator."""

    def __init__(self, message: str, *, trees_proven_terminal: bool) -> None:
        super().__init__(message)
        self.trees_proven_terminal = trees_proven_terminal


_ACTIVE_COORDINATOR_GUARD: "_CoordinatorWallGuard | None" = None


class _CoordinatorWallGuard:
    """Enforce one wall across validation, preparation, workers, and publication."""

    def __init__(
        self,
        *,
        aggregate_path: Path,
        started: float,
        exit_function: Any = os._exit,
    ) -> None:
        self.aggregate_path = aggregate_path.resolve()
        self.hard_deadline = started + COORDINATOR_WALL_SECONDS
        self.work_deadline = (
            self.hard_deadline
            - COORDINATOR_FAIL_CLOSED_PUBLICATION_RESERVE_SECONDS
        )
        self._exit_function = exit_function
        self._stop = threading.Event()
        self._expired = threading.Event()
        self._state_lock = threading.Lock()
        self._publication_lock = threading.Lock()
        self._authorization_sha256: str | None = None
        self._contract_sha256: str | None = None
        self._producer_result_path: Path | None = None
        self._process_trees_proven_terminal = True
        self._published: dict[str, Any] | None = None
        self._publisher = threading.Thread(
            target=self._publisher_main,
            name="s3-v2-stage4a-fail-closed-publisher",
            daemon=True,
        )
        self._hard_exit = threading.Thread(
            target=self._hard_exit_main,
            name="s3-v2-stage4a-hard-wall",
            daemon=True,
        )
        self._started_threads: list[threading.Thread] = []

    def bind_evidence(
        self, *, authorization_sha256: str, contract_sha256: str
    ) -> None:
        with self._state_lock:
            self._authorization_sha256 = authorization_sha256
            self._contract_sha256 = contract_sha256

    def bind_producer_result(self, path: Path) -> None:
        with self._state_lock:
            self._producer_result_path = path

    def mark_process_phase_active(self) -> None:
        with self._state_lock:
            self._process_trees_proven_terminal = False

    def mark_process_phase_terminal(self, *, proven: bool) -> None:
        with self._state_lock:
            self._process_trees_proven_terminal = proven

    def require_canonical_publication_is_safe(self, path: Path) -> None:
        if path.resolve() != self.aggregate_path:
            return
        with self._state_lock:
            proven = self._process_trees_proven_terminal
        if not proven:
            raise CoordinatorError(
                "canonical aggregate publication requires a proven-empty process tree"
            )

    def start(self) -> None:
        for thread in (self._publisher, self._hard_exit):
            thread.start()
            self._started_threads.append(thread)

    def close(self) -> None:
        self._stop.set()
        for thread in self._started_threads:
            thread.join(timeout=0.2)

    def checkpoint(self) -> None:
        if self._expired.is_set() or time.monotonic() >= self.work_deadline:
            self._expired.set()
            self.publish_fail_closed()
            raise _CoordinatorWallExceeded(
                "Stage 4A coordinator entered its fail-closed publication reserve"
            )

    def _publisher_main(self) -> None:
        delay = max(0.0, self.work_deadline - time.monotonic())
        if self._stop.wait(delay):
            return
        self._expired.set()

    def _hard_exit_main(self) -> None:
        delay = max(0.0, self.hard_deadline - time.monotonic())
        if self._stop.wait(delay):
            return
        self._exit_function(COORDINATOR_HARD_EXIT_CODE)

    def publish_fail_closed(self) -> dict[str, Any] | None:
        """Publish one fixed-schema timeout aggregate when hashes are available."""

        with self._publication_lock:
            if self._published is not None:
                return self._published
            if os.path.lexists(self.aggregate_path):
                try:
                    value, raw = strict_json_load(self.aggregate_path)
                except Exception:
                    return None
                if raw == canonical_bytes(value) and isinstance(value, dict):
                    self._published = value
                    return value
                return None
            with self._state_lock:
                authorization_sha256 = self._authorization_sha256
                contract_sha256 = self._contract_sha256
                producer_result_path = self._producer_result_path
                process_trees_proven = self._process_trees_proven_terminal
            if not process_trees_proven:
                return None
            if authorization_sha256 is None or contract_sha256 is None:
                return None
            producer_result_sha256 = None
            if producer_result_path is not None and producer_result_path.is_file():
                try:
                    producer_result_sha256 = sha256(producer_result_path.read_bytes())
                except OSError:
                    producer_result_sha256 = None
            aggregate = blocked_aggregate(
                authorization_sha256=authorization_sha256,
                contract_sha256=contract_sha256,
                producer_result_sha256=producer_result_sha256,
                reason="COORDINATOR_WALL_EXCEEDED",
            )
            try:
                _write_exclusive(
                    self.aggregate_path,
                    canonical_bytes(aggregate),
                    deadline_exempt=True,
                )
            except Exception:
                return None
            self._published = aggregate
            return aggregate


def _coordinator_checkpoint() -> None:
    guard = _ACTIVE_COORDINATOR_GUARD
    if guard is not None:
        guard.checkpoint()


def _git_subprocess_timeout() -> float:
    """Return a finite Git timeout capped by the active coordinator deadline."""

    guard = _ACTIVE_COORDINATOR_GUARD
    if guard is None:
        return float(GIT_SUBPROCESS_WALL_SECONDS)
    guard.checkpoint()
    remaining = guard.work_deadline - time.monotonic()
    if remaining <= 0:
        guard.checkpoint()
    return max(0.001, min(float(GIT_SUBPROCESS_WALL_SECONDS), remaining))


def _execution_policy() -> dict[str, Any]:
    """Return the exact Stage 4A bounded process contract."""

    return {
        "canonical_aggregate_requires_proven_empty_process_trees": True,
        "checker_tree_drain_required_before_queue_advance": True,
        "checker_phase_finalization_reserve_seconds": (
            CHECKER_PHASE_FINALIZATION_RESERVE_SECONDS
        ),
        "checker_phase_required_seconds": CHECKER_PHASE_REQUIRED_SECONDS,
        "checker_phase_schedule": CHECKER_PHASE_SCHEDULE,
        "checker_replica_wall_seconds": CHECKER_WALL_SECONDS,
        "checker_replicas_per_shard": 2,
        "coordinator_wall_seconds": COORDINATOR_WALL_SECONDS,
        "coordinator_fail_closed_publication_reserve_seconds": (
            COORDINATOR_FAIL_CLOSED_PUBLICATION_RESERVE_SECONDS
        ),
        "coordinator_hard_exit_code": COORDINATOR_HARD_EXIT_CODE,
        "coordinator_work_deadline_action": "MARK_EXPIRED_ONLY",
        "git_subprocess_wall_seconds": GIT_SUBPROCESS_WALL_SECONDS,
        "hard_coordinator_wall_enforced": True,
        "inactivity_seconds": 300,
        "maximum_concurrent_workers": MAXIMUM_CONCURRENT_WORKERS,
        "maximum_memory_gib_per_process_tree": MEMORY_LIMIT_BYTES // (1 << 30),
        "maximum_workers": MAXIMUM_REGISTERED_WORKERS,
        "memory_admission_headroom_gib": OS_HEADROOM_BYTES // (1 << 30),
        "memory_admission_required_bytes": (
            MAXIMUM_CONCURRENT_WORKERS * MEMORY_LIMIT_BYTES + OS_HEADROOM_BYTES
        ),
        "no_automatic_retry": True,
        "numerical_library_threads_per_worker": 1,
        "producer_wall_seconds": 900,
        "registered_shards": MAXIMUM_REGISTERED_WORKERS,
        "schedule": WORKER_SCHEDULE,
        "timeout_aggregate_requires_proven_empty_process_trees": True,
        "unproven_tree_hard_deadline_action": (
            "EXIT_WITHOUT_CANONICAL_AGGREGATE"
        ),
        "wave_wall_seconds": WAVE_WALL_SECONDS,
    }


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CoordinatorError(f"cannot load registered program: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def _reject_constant(value: str) -> None:
    raise CoordinatorError(f"non-finite JSON constant is forbidden: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise CoordinatorError(f"duplicate JSON key is forbidden: {key}")
        made[key] = value
    return made


def strict_json_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, CoordinatorError):
            raise
        raise CoordinatorError(f"{label} is invalid strict JSON: {exc}") from exc


def strict_json_load(path: Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CoordinatorError(f"cannot read {path}: {exc}") from exc
    return strict_json_bytes(raw, str(path)), raw


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any, location: str) -> None:
        if item is None or isinstance(item, (bool, int, str)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise CoordinatorError(f"non-finite number at {location}")
            return
        if isinstance(item, list):
            for index, member in enumerate(item):
                visit(member, f"{location}[{index}]")
            return
        if isinstance(item, dict):
            for key, member in item.items():
                if not isinstance(key, str):
                    raise CoordinatorError(f"non-string key at {location}")
                visit(member, f"{location}.{key}")
            return
        raise CoordinatorError(f"unsupported canonical value at {location}")

    visit(value, "$")
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _exact(value: Any, keys: set[str], location: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise CoordinatorError(
            f"{location} keys differ: expected={sorted(keys)} actual={actual}"
        )
    return value


def _digest(value: Any, location: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789ABCDEF" for character in value)
    ):
        raise CoordinatorError(f"{location} must be an uppercase SHA-256")
    return value


def _lower_object(value: Any, location: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise CoordinatorError(f"{location} must be a lowercase SHA-1 Git object")
    return value


def _repo_relative_path(value: Any, location: str, *, regular_file: bool = True) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise CoordinatorError(f"{location} must be a repository-relative POSIX path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise CoordinatorError(f"{location} escapes the repository")
    lexical = ROOT.joinpath(*pure.parts)
    resolved = lexical.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise CoordinatorError(f"{location} resolves outside the repository") from exc
    if regular_file and (not resolved.is_file() or resolved.is_symlink()):
        raise CoordinatorError(f"{location} is not a regular non-link file")
    return resolved


def _strict_external_json(path: Path, location: str) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
        value = json.loads(
            text,
            object_pairs_hook=_reject_pairs,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, CoordinatorError):
            raise
        raise CoordinatorError(f"{location} is invalid strict JSON: {exc}") from exc
    return value, raw


def _validate_external_file_binding(
    value: Any,
    location: str,
    *,
    expected_path: Path | None = None,
) -> tuple[Path, bytes]:
    binding = _exact(value, {"byte_count", "path", "sha256"}, location)
    raw_path = binding["path"]
    if not isinstance(raw_path, str) or not raw_path or raw_path != raw_path.strip():
        raise CoordinatorError(f"{location}.path must be an absolute path string")
    path = Path(raw_path)
    if not path.is_absolute():
        raise CoordinatorError(f"{location}.path must be absolute")
    if expected_path is not None and raw_path != str(expected_path):
        raise CoordinatorError(f"{location}.path differs from its frozen path")
    byte_count = _nonnegative_integer(binding["byte_count"], f"{location}.byte_count")
    digest = _digest(binding["sha256"], f"{location}.sha256")
    try:
        information = path.lstat()
    except OSError as exc:
        raise CoordinatorError(f"cannot read {location}: {exc}") from exc
    file_attributes = getattr(information, "st_file_attributes", 0)
    if (
        not stat.S_ISREG(information.st_mode)
        or path.is_symlink()
        or file_attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    ):
        raise CoordinatorError(f"{location} is not a regular non-reparse file")
    for ancestor in path.parents:
        try:
            ancestor_information = ancestor.lstat()
        except OSError as exc:
            raise CoordinatorError(f"cannot inspect {location} ancestor: {exc}") from exc
        ancestor_attributes = getattr(ancestor_information, "st_file_attributes", 0)
        if (
            ancestor.is_symlink()
            or ancestor_attributes
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise CoordinatorError(f"{location} has a reparse-path ancestor")
    try:
        with path.open("rb") as stream:
            opened_information = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(opened_information.st_mode)
                or not os.path.samestat(information, opened_information)
            ):
                raise CoordinatorError(f"{location} identity changed while opening")
            raw = stream.read()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise CoordinatorError(f"cannot read {location}: {exc}") from exc
    if byte_count <= 0 or byte_count != len(raw) or digest != sha256(raw):
        raise CoordinatorError(f"{location} identity differs")
    return resolved, raw


def _nonnegative_integer(value: Any, location: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CoordinatorError(f"{location} must be a nonnegative integer")
    return value


def _validate_sequence_results(
    value: Any,
    *,
    assignment_id: str,
) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or len(value) != 8:
        raise CoordinatorError(
            f"checker shard must contain exactly eight sequences: {assignment_id}"
        )
    expected_coordinates = {
        (mask, fraction) for mask in MASK_ORDER for fraction in FRACTION_ORDER
    }
    made_coordinates: set[tuple[str, int]] = set()
    checked: list[Mapping[str, Any]] = []
    keys = {
        "advisory_triggered",
        "all_q4_response_slope",
        "energy_norm_slope",
        "energy_norm_slope_lower_95_percent",
        "energy_norm_values",
        "failed_subgates",
        "finest_error_ratio_to_all_q4",
        "fraction_percent",
        "mask",
        "record_ids",
        "response_error_slope",
        "response_errors",
        "slope_deficit_from_all_q4",
        "successive_refinement_passed",
    }
    for index, raw_sequence in enumerate(value):
        sequence = _exact(
            raw_sequence,
            keys,
            f"$.checker[{assignment_id}].sequence_results[{index}]",
        )
        mask = sequence["mask"]
        fraction = sequence["fraction_percent"]
        if (
            mask not in MASK_ORDER
            or isinstance(fraction, bool)
            or not isinstance(fraction, int)
        ):
            raise CoordinatorError("checker sequence coordinate is invalid")
        coordinate = (str(mask), fraction)
        if coordinate in made_coordinates:
            raise CoordinatorError("checker sequence coordinate is duplicated")
        made_coordinates.add(coordinate)
        if (
            not isinstance(sequence["advisory_triggered"], bool)
            or not isinstance(sequence["successive_refinement_passed"], bool)
            or not isinstance(sequence["failed_subgates"], list)
            or any(
                not isinstance(failure, str)
                for failure in sequence["failed_subgates"]
            )
            or not isinstance(sequence["record_ids"], list)
            or len(sequence["record_ids"]) != 3
            or any(not isinstance(record_id, str) for record_id in sequence["record_ids"])
        ):
            raise CoordinatorError("checker sequence evidence is malformed")
        checked.append(sequence)
    if made_coordinates != expected_coordinates:
        raise CoordinatorError("checker sequence coverage differs")
    return checked


def _validate_checker_result(
    wrapper: Mapping[str, Any],
    *,
    expected_assignment_id: str,
    expected_proof: Mapping[str, Any],
) -> tuple[Mapping[str, Any], bytes]:
    wrapper = _exact(
        wrapper,
        {
            "assignment_id",
            "cpu_100ns",
            "output_path",
            "output_sha256",
            "peak_tree_memory_bytes",
            "proof_path",
            "proof_sha256",
            "stderr_sha256",
            "stdout_sha256",
            "termination_proven",
            "value",
        },
        "$.checker_wrapper",
    )
    if (
        wrapper["assignment_id"] != expected_assignment_id
        or wrapper["termination_proven"] is not True
    ):
        raise CoordinatorError("checker wrapper identity or termination differs")
    _nonnegative_integer(wrapper["cpu_100ns"], "$.checker_wrapper.cpu_100ns")
    _nonnegative_integer(
        wrapper["peak_tree_memory_bytes"],
        "$.checker_wrapper.peak_tree_memory_bytes",
    )
    for key in ("output_sha256", "stderr_sha256", "stdout_sha256"):
        _digest(wrapper[key], f"$.checker_wrapper.{key}")
    proof_path = Path(str(wrapper["proof_path"])).resolve()
    if (
        not proof_path.is_file()
        or proof_path.is_symlink()
        or proof_path != Path(str(expected_proof["proof_path"])).resolve()
        or wrapper["proof_sha256"] != expected_proof["proof_sha256"]
        or sha256(proof_path.read_bytes()) != expected_proof["proof_sha256"]
    ):
        raise CoordinatorError("checker wrapper proof binding differs")
    output_path = Path(str(wrapper["output_path"]))
    if not output_path.is_absolute() or not output_path.is_file():
        raise CoordinatorError("checker output path is not an absolute regular file")
    output_value, output_raw = strict_json_load(output_path)
    if output_raw != canonical_bytes(output_value):
        raise CoordinatorError("checker output is not canonical JSON")
    if sha256(output_raw) != wrapper["output_sha256"]:
        raise CoordinatorError("checker output wrapper hash differs")
    if output_value != wrapper["value"]:
        raise CoordinatorError("checker wrapper value differs from its output")
    result = _exact(
        output_value,
        {
            "advisory_review_required",
            "assignment_id",
            "assignment_sha256",
            "classifying_record_count",
            "diagonal",
            "formal_failures",
            "plan_sha256",
            "production_restriction",
            "proof_sha256",
            "schema",
            "sequence_results",
            "successor_expansion_authorized",
            "terminal",
            "v1_diagnostic_record_count",
        },
        f"$.checker[{expected_assignment_id}]",
    )
    classifying_count = _nonnegative_integer(
        result["classifying_record_count"],
        f"$.checker[{expected_assignment_id}].classifying_record_count",
    )
    v1_count = _nonnegative_integer(
        result["v1_diagnostic_record_count"],
        f"$.checker[{expected_assignment_id}].v1_diagnostic_record_count",
    )
    if (
        result["schema"] != CHECKER_RESULT_SCHEMA
        or result["assignment_id"] != expected_assignment_id
        or result["diagonal"] != EXPECTED_SHARDS[expected_assignment_id]
        or classifying_count != 27
        or v1_count != 24
        or result["production_restriction"] != PRODUCTION_RESTRICTION
    ):
        raise CoordinatorError("checker result identity or coverage differs")
    for key in ("assignment_sha256", "plan_sha256", "proof_sha256"):
        _digest(result[key], f"$.checker[{expected_assignment_id}].{key}")
    if (
        result["assignment_sha256"] != expected_proof["assignment_sha256"]
        or result["plan_sha256"] != expected_proof["plan_sha256"]
        or result["proof_sha256"] != expected_proof["proof_sha256"]
    ):
        raise CoordinatorError("checker result is not joined to its producer proof")
    failures = result["formal_failures"]
    if (
        not isinstance(failures, list)
        or any(not isinstance(failure, str) for failure in failures)
        or failures != sorted(set(failures))
    ):
        raise CoordinatorError("checker formal failures are not canonical")
    terminal = result["terminal"]
    if terminal not in (PASS, NO_GO) or (terminal == NO_GO) != bool(failures):
        raise CoordinatorError("checker terminal and formal failures disagree")
    if not isinstance(result["advisory_review_required"], bool):
        raise CoordinatorError("checker advisory disposition is not Boolean")
    expected_expansion = terminal == PASS and not result["advisory_review_required"]
    if result["successor_expansion_authorized"] is not expected_expansion:
        raise CoordinatorError("checker successor disposition differs")
    sequences = _validate_sequence_results(
        result["sequence_results"], assignment_id=expected_assignment_id
    )
    sequence_failures = sorted(
        f"{sequence['mask']}:{sequence['fraction_percent']}:{failure}"
        for sequence in sequences
        for failure in sequence["failed_subgates"]
    )
    if sequence_failures != failures:
        raise CoordinatorError("checker sequence and shard failures disagree")
    advisory = any(bool(sequence["advisory_triggered"]) for sequence in sequences)
    if result["advisory_review_required"] is not bool(advisory and not failures):
        raise CoordinatorError("checker sequence and shard advisory differs")
    return result, output_raw


def _git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for key in tuple(environment):
        if key in {
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_ATTR_SOURCE",
            "GIT_CEILING_DIRECTORIES",
            "GIT_COMMON_DIR",
            "GIT_CONFIG",
            "GIT_CONFIG_COUNT",
            "GIT_CONFIG_SYSTEM",
            "GIT_DIR",
            "GIT_DISCOVERY_ACROSS_FILESYSTEM",
            "GIT_EXTERNAL_DIFF",
            "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY",
            "GIT_NAMESPACE",
            "GIT_SHALLOW_FILE",
            "GIT_WORK_TREE",
        } or key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            environment.pop(key, None)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    return environment


def _git_runtime_paths() -> tuple[Path, Path]:
    launcher_text = shutil.which("git")
    if launcher_text is None:
        raise CoordinatorError("registered Git launcher cannot be resolved")
    launcher = Path(launcher_text).resolve()
    if os.name == "nt":
        engine = (launcher.parent.parent / "mingw64" / "bin" / "git.exe").resolve()
    else:
        engine = launcher
    for label, path in (("launcher", launcher), ("engine", engine)):
        if not path.is_file() or path.is_symlink():
            raise CoordinatorError(f"Git {label} is not a regular non-link file")
    return launcher, engine


def _discover_git_runtime() -> dict[str, Any]:
    launcher, engine = _git_runtime_paths()
    try:
        completed_version = subprocess.run(
            [str(engine), "--version"],
            cwd=ROOT,
            env=_git_environment(),
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_git_subprocess_timeout(),
        )
        completed_exec = subprocess.run(
            [str(engine), "--exec-path"],
            cwd=ROOT,
            env=_git_environment(),
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_git_subprocess_timeout(),
        )
    except subprocess.TimeoutExpired as exc:
        raise CoordinatorError("Git runtime discovery exceeded its bound") from exc
    exec_path = Path(completed_exec.stdout.decode("utf-8").strip()).resolve()
    if not exec_path.is_dir() or exec_path.is_symlink():
        raise CoordinatorError("Git exec path is not a regular directory")
    return {
        "engine_byte_count": engine.stat().st_size,
        "engine_path": str(engine),
        "engine_sha256": sha256(engine.read_bytes()),
        "exec_path": str(exec_path),
        "launcher_byte_count": launcher.stat().st_size,
        "launcher_path": str(launcher),
        "launcher_sha256": sha256(launcher.read_bytes()),
        "version": completed_version.stdout.decode("utf-8").strip(),
    }


def _git_command(*arguments: str, repository: Path = ROOT) -> list[str]:
    _launcher, engine = _git_runtime_paths()
    return [
        str(engine),
        "-c",
        f"safe.directory={repository.resolve()}",
        "-c",
        "core.autocrlf=true",
        "-c",
        "core.attributesfile=NUL",
        "-c",
        "extensions.objectformat=sha1",
        *arguments,
    ]


def _git_run(
    *arguments: str,
    check: bool = True,
    stdout: Any = subprocess.PIPE,
    repository: Path = ROOT,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            _git_command(*arguments, repository=repository),
            cwd=repository,
            env=_git_environment(),
            check=check,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=subprocess.PIPE,
            timeout=_git_subprocess_timeout(),
        )
    except subprocess.TimeoutExpired as exc:
        raise CoordinatorError("Git subprocess exceeded its bound") from exc


def _git(
    *arguments: str,
    binary: bool = False,
    repository: Path = ROOT,
) -> bytes | str:
    completed = _git_run(*arguments, repository=repository)
    return completed.stdout if binary else completed.stdout.decode("utf-8").strip()


def _validate_git_object_authority(repository: Path = ROOT) -> None:
    included = _git_run(
        "config",
        "--local",
        "--no-includes",
        "--get-regexp",
        r"^include(If)?\.",
        check=False,
        repository=repository,
    )
    if included.returncode not in {0, 1} or included.stdout.strip():
        raise CoordinatorError("repository-local Git config includes are forbidden")
    attributes_setting = _git_run(
        "config",
        "--local",
        "--no-includes",
        "--get-all",
        "core.attributesfile",
        check=False,
        repository=repository,
    )
    if attributes_setting.returncode not in {0, 1} or attributes_setting.stdout.strip():
        raise CoordinatorError("repository-local external attributes are forbidden")
    if _git(
        "for-each-ref",
        "--format=%(refname)",
        "refs/replace",
        repository=repository,
    ):
        raise CoordinatorError("Git replacement objects are forbidden")
    common = Path(
        str(_git("rev-parse", "--git-common-dir", repository=repository))
    )
    if not common.is_absolute():
        common = (repository / common).resolve()
    git_dir = Path(str(_git("rev-parse", "--git-dir", repository=repository)))
    if not git_dir.is_absolute():
        git_dir = (repository / git_dir).resolve()
    forbidden = {
        common / "info" / "attributes": "Git common attributes",
        common / "info" / "grafts": "Git graft authority",
        common / "objects" / "info" / "alternates": "Git object alternates",
        common / "objects" / "info" / "http-alternates": "Git HTTP alternates",
        git_dir / "info" / "attributes": "Git worktree attributes",
    }
    for path, label in forbidden.items():
        if os.path.lexists(path):
            raise CoordinatorError(f"{label} is forbidden")


def _git_blob_sha256(commit: str, path: str) -> str:
    return sha256(_git("show", f"{commit}:{path}", binary=True))


def _canonical_external_json(raw: bytes, location: str) -> Mapping[str, Any]:
    value = strict_json_bytes(raw, location)
    if raw != canonical_bytes(value) or not isinstance(value, dict):
        raise CoordinatorError(f"{location} is not canonical JSON")
    return value


def _validate_predecessor_process_incident(value: Any) -> None:
    """Validate and cross-join the consumed, pre-worker Stage-4A incident."""

    location = "$.contract.predecessor_process_incident"
    incident = _exact(
        value,
        {
            "aggregate",
            "approval_snapshot",
            "authorization",
            "candidate_archive",
            "candidate_binding",
            "ledger_snapshot",
            "manifest",
            "output_root",
            "phase_plan",
            "request",
            "root_cause",
            "scientific_execution",
            "terminal_ledger_rows",
            "transcript",
        },
        location,
    )
    if (
        incident["output_root"] != str(PREDECESSOR_INCIDENT_ROOT)
        or incident["root_cause"]
        != "PRODUCER_RESULT_PATH_OUTSIDE_REGISTERED_WAVE_ROOT"
    ):
        raise CoordinatorError("predecessor process incident identity differs")
    scientific = _exact(
        incident["scientific_execution"],
        {
            "checker_processes_started",
            "classifying_records",
            "producer_processes_started",
            "producer_result_present",
        },
        f"{location}.scientific_execution",
    )
    if (
        _nonnegative_integer(
            scientific["checker_processes_started"],
            f"{location}.scientific_execution.checker_processes_started",
        )
        != 0
        or _nonnegative_integer(
            scientific["classifying_records"],
            f"{location}.scientific_execution.classifying_records",
        )
        != 0
        or _nonnegative_integer(
            scientific["producer_processes_started"],
            f"{location}.scientific_execution.producer_processes_started",
        )
        != 0
        or scientific["producer_result_present"] is not False
    ):
        raise CoordinatorError("predecessor scientific-execution disposition differs")

    incident_root = PREDECESSOR_INCIDENT_ROOT.resolve()
    bound: dict[str, tuple[Path, bytes]] = {}
    for name, (filename, expected_count, expected_sha256) in (
        PREDECESSOR_ARTIFACTS.items()
    ):
        raw_binding = _exact(
            incident[name],
            {"byte_count", "path", "sha256"},
            f"{location}.{name}",
        )
        if (
            _nonnegative_integer(
                raw_binding["byte_count"], f"{location}.{name}.byte_count"
            )
            != expected_count
            or _digest(raw_binding["sha256"], f"{location}.{name}.sha256")
            != expected_sha256
        ):
            raise CoordinatorError(f"predecessor {name} frozen identity differs")
        expected_path = PREDECESSOR_INCIDENT_ROOT / filename
        bound[name] = _validate_external_file_binding(
            raw_binding,
            f"{location}.{name}",
            expected_path=expected_path,
        )
        if bound[name][0] != expected_path.resolve():
            raise CoordinatorError(f"predecessor {name} resolved path differs")

    request_path = (
        RESOURCE_MANAGER_ROOT / "requests" / f"{PREDECESSOR_REQUEST_ID}.json"
    )
    request_binding = _exact(
        incident["request"],
        {"byte_count", "path", "sha256"},
        f"{location}.request",
    )
    if (
        _nonnegative_integer(
            request_binding["byte_count"], f"{location}.request.byte_count"
        )
        != 1311
        or _digest(request_binding["sha256"], f"{location}.request.sha256")
        != PREDECESSOR_REQUEST_SHA256
    ):
        raise CoordinatorError("predecessor request frozen identity differs")
    request_file, request_raw = _validate_external_file_binding(
        request_binding,
        f"{location}.request",
        expected_path=request_path,
    )
    if request_file != request_path.resolve():
        raise CoordinatorError("predecessor request resolved path differs")

    try:
        actual_names = {entry.name for entry in os.scandir(incident_root)}
    except OSError as exc:
        raise CoordinatorError(f"cannot enumerate predecessor incident: {exc}") from exc
    expected_names = {artifact[0] for artifact in PREDECESSOR_ARTIFACTS.values()}
    expected_names.add("candidate-source-tree")
    if actual_names != expected_names:
        raise CoordinatorError("predecessor incident artifact extent differs")

    request, observed_request_raw = _strict_external_json(
        request_file, "predecessor resource request"
    )
    request = _exact(
        request,
        {
            "command",
            "estimate_minutes",
            "repository",
            "request_id",
            "requested_at",
            "status",
            "task",
        },
        f"{location}.request_file",
    )
    command = request["command"]
    if (
        observed_request_raw != request_raw
        or request["request_id"] != PREDECESSOR_REQUEST_ID
        or request["requested_at"] != PREDECESSOR_REQUESTED_AT
        or request["task"] != PREDECESSOR_TASK
        or request["repository"] != PREDECESSOR_REPOSITORY
        or request["status"] != "PENDING"
        or _nonnegative_integer(
            request["estimate_minutes"], f"{location}.request_file.estimate_minutes"
        )
        != 30
        or not isinstance(command, str)
        or not command
        or sha256(command.encode("utf-8")) != PREDECESSOR_COMMAND_SHA256
    ):
        raise CoordinatorError("predecessor resource request identity differs")

    snapshot = _exact(
        _canonical_external_json(
            bound["approval_snapshot"][1], "predecessor approval snapshot"
        ),
        {"approved_row", "candidate", "ledger", "request", "schema"},
        f"{location}.approval_snapshot_file",
    )
    approved_row = _exact(
        snapshot["approved_row"],
        {"line", "sha256"},
        f"{location}.approval_snapshot_file.approved_row",
    )
    approved_line = approved_row["line"]
    if (
        snapshot["schema"]
        != "anysolver.e4-pl-s3-v2-stage4a-approval-snapshot-v2"
        or snapshot["candidate"]
        != {
            "commit": PREDECESSOR_CANDIDATE_COMMIT,
            "tree": PREDECESSOR_CANDIDATE_TREE,
        }
        or not isinstance(approved_line, str)
        or "\n" in approved_line
        or "\r" in approved_line
        or _digest(approved_row["sha256"], f"{location}.approved_row.sha256")
        != PREDECESSOR_LEDGER_ROW_SHA256["APPROVED"]
        or sha256((approved_line + "\n").encode("utf-8"))
        != PREDECESSOR_LEDGER_ROW_SHA256["APPROVED"]
    ):
        raise CoordinatorError("predecessor approval snapshot identity differs")
    snapshot_request = _exact(
        snapshot["request"],
        {"byte_count", "path", "request_id", "sha256"},
        f"{location}.approval_snapshot_file.request",
    )
    snapshot_ledger = _exact(
        snapshot["ledger"],
        {"byte_count", "path", "sha256", "snapshot_path"},
        f"{location}.approval_snapshot_file.ledger",
    )
    if (
        snapshot_request
        != {
            "byte_count": 1311,
            "path": str(request_path),
            "request_id": PREDECESSOR_REQUEST_ID,
            "sha256": PREDECESSOR_REQUEST_SHA256,
        }
        or snapshot_ledger
        != {
            "byte_count": PREDECESSOR_ARTIFACTS["ledger_snapshot"][1],
            "path": str(RESOURCE_LEDGER_PATH),
            "sha256": PREDECESSOR_ARTIFACTS["ledger_snapshot"][2],
            "snapshot_path": str(
                PREDECESSOR_INCIDENT_ROOT
                / PREDECESSOR_ARTIFACTS["ledger_snapshot"][0]
            ),
        }
    ):
        raise CoordinatorError("predecessor approval snapshot joins differ")
    try:
        ledger_snapshot_text = bound["ledger_snapshot"][1].decode("utf-8-sig")
    except UnicodeError as exc:
        raise CoordinatorError("predecessor ledger snapshot is not UTF-8") from exc
    if ledger_snapshot_text.splitlines().count(approved_line) != 1:
        raise CoordinatorError("predecessor approved row is absent or duplicated")

    candidate_binding = _exact(
        _canonical_external_json(
            bound["candidate_binding"][1], "predecessor candidate binding"
        ),
        {
            "artifact_path",
            "artifact_sha256",
            "candidate_id",
            "commit",
            "formulation_id",
            "schema",
            "selector",
            "tree",
        },
        f"{location}.candidate_binding_file",
    )
    if candidate_binding != {
        "artifact_path": str(
            PREDECESSOR_INCIDENT_ROOT
            / PREDECESSOR_ARTIFACTS["candidate_archive"][0]
        ),
        "artifact_sha256": PREDECESSOR_ARTIFACTS["candidate_archive"][2],
        "candidate_id": "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1",
        "commit": PREDECESSOR_CANDIDATE_COMMIT,
        "formulation_id": "E4_PL_QUALIFIED_S3_COMPANION_V2",
        "schema": "anysolver.e4-pl-s3-v2-flat-candidate-binding-v1",
        "selector": "e4-pl-s3-v2",
        "tree": PREDECESSOR_CANDIDATE_TREE,
    }:
        raise CoordinatorError("predecessor candidate archive join differs")

    plan = _exact(
        _canonical_external_json(bound["phase_plan"][1], "predecessor phase plan"),
        {
            "advisory_review_triggers",
            "formal_thresholds",
            "manifest_sha256",
            "phase",
            "prerequisites",
            "record_count",
            "schema",
            "scope",
            "selector",
            "shards",
        },
        f"{location}.phase_plan_file",
    )
    shards = plan["shards"]
    if (
        plan["schema"] != "anysolver.e4-pl-s3-v2-flat-funnel-plan-v1"
        or plan["phase"] != "4A"
        or plan["scope"] != "full"
        or plan["selector"] != "e4-pl-s3-v2"
        or plan["prerequisites"] != []
        or plan["manifest_sha256"]
        != PREDECESSOR_CONNECTIVITY_MANIFEST_SHA256
        or _nonnegative_integer(plan["record_count"], f"{location}.plan.record_count")
        != 81
        or not isinstance(shards, list)
        or len(shards) != 3
        or [
            shard.get("assignment_id") if isinstance(shard, dict) else None
            for shard in shards
        ]
        != list(EXPECTED_SHARDS)
        or any(
            not isinstance(shard.get("records"), list)
            or len(shard["records"]) != 27
            for shard in shards
        )
    ):
        raise CoordinatorError("predecessor phase-plan identity or coverage differs")

    manifest = _exact(
        _canonical_external_json(
            bound["manifest"][1], "predecessor producer-wave manifest"
        ),
        {"lane", "output_root", "schema", "wave_id", "workers"},
        f"{location}.manifest_file",
    )
    wave_root = (PREDECESSOR_INCIDENT_ROOT / "producer-wave").resolve()
    workers = manifest["workers"]
    if (
        manifest["schema"]
        != "anysolver.e4-pl-s3-v2-bounded-wave-manifest-v1"
        or manifest["wave_id"] != "S3_V2_FLAT_FUNNEL_4A_FULL"
        or manifest["lane"] != "flat-proof"
        or manifest["output_root"] != str(PREDECESSOR_INCIDENT_ROOT / "producer-wave")
        or not isinstance(workers, list)
        or len(workers) != 3
        or [
            worker.get("assignment_id") if isinstance(worker, dict) else None
            for worker in workers
        ]
        != list(EXPECTED_SHARDS)
    ):
        raise CoordinatorError("predecessor producer-wave manifest identity differs")
    for worker in workers:
        if (
            worker.get("plan_path")
            != str(PREDECESSOR_INCIDENT_ROOT / PREDECESSOR_ARTIFACTS["phase_plan"][0])
            or worker.get("plan_sha256") != PREDECESSOR_ARTIFACTS["phase_plan"][2]
        ):
            raise CoordinatorError("predecessor worker plan binding differs")
        for key in ("progress_path", "scientific_path", "stderr_path", "stdout_path"):
            raw_worker_path = worker.get(key)
            if not isinstance(raw_worker_path, str) or not Path(raw_worker_path).is_absolute():
                raise CoordinatorError("predecessor worker output path is invalid")
            try:
                Path(raw_worker_path).resolve().relative_to(wave_root)
            except ValueError as exc:
                raise CoordinatorError(
                    "predecessor worker output escapes the registered wave root"
                ) from exc
    bounded = _load_module(
        "_s3_v2_predecessor_incident_bounded", BOUNDED_PATH
    )
    validated_wave_id, validated_lane, validated_root, validated_workers = (
        bounded.validate_manifest(manifest)
    )
    if (
        validated_wave_id != manifest["wave_id"]
        or validated_lane != manifest["lane"]
        or validated_root != wave_root
        or [worker.assignment_id for worker in validated_workers]
        != list(EXPECTED_SHARDS)
    ):
        raise CoordinatorError("predecessor bounded manifest validation differs")

    aggregate = _exact(
        _canonical_external_json(
            bound["aggregate"][1], "predecessor blocked aggregate"
        ),
        {
            "advisory_review_required",
            "authorization_sha256",
            "checker_replica_bindings",
            "classifying_record_count",
            "contract_sha256",
            "formal_failures",
            "producer_wave_result_sha256",
            "production_restriction",
            "schema",
            "sequence_results",
            "successor_expansion_authorized",
            "terminal",
            "v1_diagnostic_record_count",
        },
        f"{location}.aggregate_file",
    )
    if (
        aggregate["schema"] != AGGREGATE_SCHEMA
        or aggregate["terminal"] != BLOCKED
        or aggregate["formal_failures"] != ["FORMAL_PROCESS_FAILED"]
        or aggregate["authorization_sha256"] != PREDECESSOR_AUTHORIZATION_SHA256
        or aggregate["contract_sha256"] != PREDECESSOR_CONTRACT_SHA256
        or aggregate["production_restriction"] != PRODUCTION_RESTRICTION
        or aggregate["producer_wave_result_sha256"] is not None
        or aggregate["checker_replica_bindings"] != []
        or aggregate["sequence_results"] != []
        or aggregate["advisory_review_required"] is not False
        or aggregate["successor_expansion_authorized"] is not False
        or _nonnegative_integer(
            aggregate["classifying_record_count"],
            f"{location}.aggregate.classifying_record_count",
        )
        != 0
        or _nonnegative_integer(
            aggregate["v1_diagnostic_record_count"],
            f"{location}.aggregate.v1_diagnostic_record_count",
        )
        != 0
    ):
        raise CoordinatorError("predecessor blocked aggregate disposition differs")

    authorization_binding = _exact(
        incident["authorization"],
        {"byte_count", "commit", "parent", "path", "sha256", "subject", "tree"},
        f"{location}.authorization",
    )
    if (
        _nonnegative_integer(
            authorization_binding["byte_count"],
            f"{location}.authorization.byte_count",
        )
        != PREDECESSOR_AUTHORIZATION_BYTE_COUNT
        or authorization_binding["commit"] != PREDECESSOR_AUTHORIZATION_COMMIT
        or authorization_binding["tree"] != PREDECESSOR_AUTHORIZATION_TREE
        or authorization_binding["parent"] != PREDECESSOR_AUTHORIZATION_PARENT
        or authorization_binding["subject"] != PREDECESSOR_AUTHORIZATION_SUBJECT
        or authorization_binding["path"] != PREDECESSOR_AUTHORIZATION_PATH
        or _digest(
            authorization_binding["sha256"], f"{location}.authorization.sha256"
        )
        != PREDECESSOR_AUTHORIZATION_SHA256
    ):
        raise CoordinatorError("predecessor authorization binding differs")
    _validate_git_object_authority()
    if (
        _git("rev-parse", PREDECESSOR_AUTHORIZATION_COMMIT)
        != PREDECESSOR_AUTHORIZATION_COMMIT
        or _git(
            "rev-parse", f"{PREDECESSOR_AUTHORIZATION_COMMIT}^{{tree}}"
        )
        != PREDECESSOR_AUTHORIZATION_TREE
        or _git(
            "show", "-s", "--format=%P", PREDECESSOR_AUTHORIZATION_COMMIT
        )
        != PREDECESSOR_AUTHORIZATION_PARENT
        or _git(
            "show", "-s", "--format=%s", PREDECESSOR_AUTHORIZATION_COMMIT
        )
        != PREDECESSOR_AUTHORIZATION_SUBJECT
    ):
        raise CoordinatorError("predecessor authorization Git identity differs")
    authorization_raw = _git(
        "show",
        f"{PREDECESSOR_AUTHORIZATION_COMMIT}:{PREDECESSOR_AUTHORIZATION_PATH}",
        binary=True,
    )
    if (
        len(authorization_raw) != PREDECESSOR_AUTHORIZATION_BYTE_COUNT
        or sha256(authorization_raw) != PREDECESSOR_AUTHORIZATION_SHA256
    ):
        raise CoordinatorError("predecessor authorization blob differs")
    authorization = _exact(
        _canonical_external_json(
            authorization_raw, "predecessor execution authorization"
        ),
        {
            "contract_path",
            "contract_sha256",
            "execution_paths",
            "formal_execution_authorized",
            "implementation_reviews",
            "ledger_approval",
            "resource_lock_required",
            "resource_request",
            "schema",
            "user_approval",
        },
        f"{location}.authorization_blob",
    )
    execution_paths = _exact(
        authorization["execution_paths"],
        {
            "aggregate_path",
            "approval_snapshot_path",
            "output_root",
            "python_executable",
        },
        f"{location}.authorization_blob.execution_paths",
    )
    resource_request = _exact(
        authorization["resource_request"],
        {
            "command_sha256",
            "repository",
            "request_id",
            "request_path",
            "request_sha256",
            "task",
        },
        f"{location}.authorization_blob.resource_request",
    )
    ledger_approval = _exact(
        authorization["ledger_approval"],
        {
            "approved_row_sha256",
            "ledger_path",
            "snapshot_path",
            "snapshot_sha256",
        },
        f"{location}.authorization_blob.ledger_approval",
    )
    user_approval = _exact(
        authorization["user_approval"],
        {"recorded", "source"},
        f"{location}.authorization_blob.user_approval",
    )
    if (
        authorization["schema"] != AUTHORIZATION_SCHEMA
        or authorization["contract_path"] != PREDECESSOR_CONTRACT_PATH
        or authorization["contract_sha256"] != PREDECESSOR_CONTRACT_SHA256
        or authorization["formal_execution_authorized"] is not True
        or authorization["resource_lock_required"] is not True
        or execution_paths["output_root"] != str(PREDECESSOR_INCIDENT_ROOT)
        or execution_paths["aggregate_path"]
        != str(PREDECESSOR_INCIDENT_ROOT / PREDECESSOR_ARTIFACTS["aggregate"][0])
        or execution_paths["approval_snapshot_path"]
        != str(
            PREDECESSOR_INCIDENT_ROOT
            / PREDECESSOR_ARTIFACTS["approval_snapshot"][0]
        )
        or resource_request
        != {
            "command_sha256": PREDECESSOR_COMMAND_SHA256,
            "repository": PREDECESSOR_REPOSITORY,
            "request_id": PREDECESSOR_REQUEST_ID,
            "request_path": str(request_path),
            "request_sha256": PREDECESSOR_REQUEST_SHA256,
            "task": PREDECESSOR_TASK,
        }
        or ledger_approval
        != {
            "approved_row_sha256": PREDECESSOR_LEDGER_ROW_SHA256["APPROVED"],
            "ledger_path": str(RESOURCE_LEDGER_PATH),
            "snapshot_path": str(
                PREDECESSOR_INCIDENT_ROOT
                / PREDECESSOR_ARTIFACTS["approval_snapshot"][0]
            ),
            "snapshot_sha256": PREDECESSOR_ARTIFACTS["approval_snapshot"][2],
        }
        or user_approval["recorded"] is not True
        or not isinstance(user_approval["source"], str)
        or PREDECESSOR_REQUEST_ID not in user_approval["source"]
    ):
        raise CoordinatorError("predecessor authorization joins differ")

    predecessor_contract_raw = _git(
        "show",
        f"{PREDECESSOR_AUTHORIZATION_COMMIT}:{PREDECESSOR_CONTRACT_PATH}",
        binary=True,
    )
    if (
        len(predecessor_contract_raw) != PREDECESSOR_CONTRACT_BYTE_COUNT
        or sha256(predecessor_contract_raw) != PREDECESSOR_CONTRACT_SHA256
    ):
        raise CoordinatorError("predecessor contract blob differs")
    predecessor_contract = _canonical_external_json(
        predecessor_contract_raw, "predecessor Stage 4A contract"
    )
    predecessor_candidate = predecessor_contract.get("candidate")
    if (
        predecessor_contract.get("schema")
        != "anysolver.e4-pl-s3-v2-stage4a-contract-v2"
        or not isinstance(predecessor_candidate, dict)
        or predecessor_candidate.get("commit") != PREDECESSOR_CANDIDATE_COMMIT
        or predecessor_candidate.get("tree") != PREDECESSOR_CANDIDATE_TREE
    ):
        raise CoordinatorError("predecessor contract candidate identity differs")
    frozen_files = predecessor_contract.get("frozen_files")
    if not isinstance(frozen_files, list):
        raise CoordinatorError("predecessor frozen-file graph is malformed")
    frozen_by_path: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(frozen_files):
        binding = _exact(
            item,
            {"git_blob_sha256", "path", "role"},
            f"{location}.predecessor_contract.frozen_files[{index}]",
        )
        if not isinstance(binding["path"], str) or binding["path"] in frozen_by_path:
            raise CoordinatorError("predecessor frozen-file path is invalid or duplicated")
        frozen_by_path[binding["path"]] = binding
    coordinator_path = "docs/reference_cases/e4_pl_s3_v2_stage4a_coordinator.py"
    bounded_path = "docs/reference_cases/e4_pl_s3_v2_bounded_process.py"
    if (
        frozen_by_path.get(coordinator_path, {}).get("git_blob_sha256")
        != PREDECESSOR_COORDINATOR_SHA256
        or frozen_by_path.get(bounded_path, {}).get("git_blob_sha256")
        != PREDECESSOR_BOUNDED_SHA256
    ):
        raise CoordinatorError("predecessor process-program authority differs")
    predecessor_coordinator_raw = _git(
        "show",
        f"{PREDECESSOR_AUTHORIZATION_COMMIT}:{coordinator_path}",
        binary=True,
    )
    predecessor_bounded_raw = _git(
        "show",
        f"{PREDECESSOR_AUTHORIZATION_COMMIT}:{bounded_path}",
        binary=True,
    )
    if (
        sha256(predecessor_coordinator_raw) != PREDECESSOR_COORDINATOR_SHA256
        or sha256(predecessor_bounded_raw) != PREDECESSOR_BOUNDED_SHA256
        or b'producer_result_path = (output_root / "producer-wave-result.json").resolve()'
        not in predecessor_coordinator_raw
        or b"result_path.relative_to(output_root)" not in predecessor_bounded_raw
        or b'raise BoundedProcessError("canonical wave result path escapes output_root")'
        not in predecessor_bounded_raw
    ):
        raise CoordinatorError("predecessor containment implementation differs")

    failed_result_path = (incident_root / "producer-wave-result.json").resolve()
    corrected_result_path = (wave_root / "producer-wave-result.json").resolve()
    try:
        failed_result_path.relative_to(wave_root)
    except ValueError:
        pass
    else:
        raise CoordinatorError("predecessor root cause is not reproduced")
    try:
        corrected_result_path.relative_to(wave_root)
    except ValueError as exc:
        raise CoordinatorError("corrected producer result containment is invalid") from exc
    absent_paths = (
        wave_root,
        failed_result_path,
        corrected_result_path,
        incident_root / "checker-replica-1",
        incident_root / "checker-replica-2",
    )
    if any(os.path.lexists(path) for path in absent_paths):
        raise CoordinatorError("predecessor worker or result output unexpectedly exists")

    try:
        transcript = bound["transcript"][1].decode("utf-8-sig")
    except UnicodeError as exc:
        raise CoordinatorError("predecessor transcript is not UTF-8") from exc
    transcript_lines = [line.strip() for line in transcript.splitlines()]
    if (
        transcript_lines.count("REGISTERED_COMMAND_EXIT=2") != 1
        or "REGISTERED_COMMAND_EXIT=0" in transcript_lines
        or f"FORMAL_TERMINAL={PASS}" in transcript_lines
        or f"FORMAL_TERMINAL={NO_GO}" in transcript_lines
    ):
        raise CoordinatorError("predecessor transcript disposition differs")

    terminal_rows = incident["terminal_ledger_rows"]
    if not isinstance(terminal_rows, list) or len(terminal_rows) != 2:
        raise CoordinatorError("predecessor terminal ledger-row coverage differs")
    expected_statuses = ("EXECUTION_STARTED", "COMPLETED_FAIL")
    terminal_lines: list[str] = []
    for index, (raw_row, expected_status) in enumerate(
        zip(terminal_rows, expected_statuses)
    ):
        row = _exact(
            raw_row,
            {"line", "sha256", "status"},
            f"{location}.terminal_ledger_rows[{index}]",
        )
        line = row["line"]
        if (
            row["status"] != expected_status
            or not isinstance(line, str)
            or "\r" in line
            or "\n" in line
            or _digest(row["sha256"], f"{location}.terminal_ledger_rows[{index}].sha256")
            != PREDECESSOR_LEDGER_ROW_SHA256[expected_status]
            or sha256((line + "\n").encode("utf-8"))
            != PREDECESSOR_LEDGER_ROW_SHA256[expected_status]
        ):
            raise CoordinatorError("predecessor terminal ledger row differs")
        fields = [field.strip() for field in line.split("|")]
        if len(fields) < 5 or fields[2] != PREDECESSOR_REQUEST_ID or fields[3] != expected_status:
            raise CoordinatorError("predecessor terminal ledger row fields differ")
        terminal_lines.append(line)
    try:
        live_ledger = RESOURCE_LEDGER_PATH.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise CoordinatorError(f"cannot validate predecessor live ledger: {exc}") from exc
    matching_rows = [
        line
        for line in live_ledger.splitlines()
        if f"| {PREDECESSOR_REQUEST_ID} |" in line
    ]
    if matching_rows != [approved_line, *terminal_lines]:
        raise CoordinatorError("predecessor live ledger history differs")


def _resource_deferred_archive_inventory(
    archive_path: Path,
) -> tuple[set[str], dict[str, tuple[int, str]]]:
    """Return the exact regular directory/file inventory of the bound Git archive."""

    directories: set[str] = set()
    files: dict[str, tuple[int, str]] = {}
    seen: set[str] = set()
    try:
        with tarfile.open(archive_path, mode="r:") as bundle:
            for member in bundle:
                raw_name = member.name
                normalized_name = raw_name[:-1] if raw_name.endswith("/") else raw_name
                raw_parts = normalized_name.split("/")
                pure = PurePosixPath(normalized_name)
                if (
                    not normalized_name
                    or "\\" in raw_name
                    or pure.is_absolute()
                    or any(part in {"", ".", ".."} for part in raw_parts)
                ):
                    raise CoordinatorError(
                        "resource-deferred candidate archive contains an unsafe path"
                    )
                relative = pure.as_posix()
                if relative in seen:
                    raise CoordinatorError(
                        "resource-deferred candidate archive path is duplicated"
                    )
                seen.add(relative)
                for parent in pure.parents:
                    if parent != PurePosixPath("."):
                        directories.add(parent.as_posix())
                if member.isdir():
                    directories.add(relative)
                    continue
                if not member.isfile():
                    raise CoordinatorError(
                        "resource-deferred candidate archive contains a link or special entry"
                    )
                stream = bundle.extractfile(member)
                if stream is None:
                    raise CoordinatorError(
                        "resource-deferred candidate archive member cannot be read"
                    )
                digest = hashlib.sha256()
                byte_count = 0
                while True:
                    chunk = stream.read(1 << 20)
                    if not chunk:
                        break
                    byte_count += len(chunk)
                    digest.update(chunk)
                if byte_count != member.size:
                    raise CoordinatorError(
                        "resource-deferred candidate archive member size differs"
                    )
                files[relative] = (byte_count, digest.hexdigest().upper())
    except (OSError, tarfile.TarError) as exc:
        raise CoordinatorError(
            f"cannot read resource-deferred candidate archive: {exc}"
        ) from exc
    if directories.intersection(files):
        raise CoordinatorError(
            "resource-deferred candidate archive has a file/directory collision"
        )
    return directories, files


def _validate_resource_deferred_candidate_tree(
    value: Any, location: str, *, archive_path: Path
) -> None:
    binding = _exact(value, {"directory_count", "file_count", "path"}, location)
    nominal_root = RESOURCE_DEFERRED_INCIDENT_ROOT / "candidate-source-tree"
    if binding["path"] != str(RESOURCE_DEFERRED_INCIDENT_ROOT / "candidate-source-tree"):
        raise CoordinatorError("resource-deferred candidate-tree path differs")
    if (
        _nonnegative_integer(binding["file_count"], f"{location}.file_count")
        != RESOURCE_DEFERRED_CANDIDATE_FILE_COUNT
        or _nonnegative_integer(
            binding["directory_count"], f"{location}.directory_count"
        )
        != RESOURCE_DEFERRED_CANDIDATE_DIRECTORY_COUNT
    ):
        raise CoordinatorError("resource-deferred candidate-tree counts differ")

    actual_directories: set[str] = set()
    actual_files: dict[str, tuple[int, str]] = {}
    try:
        root_information = nominal_root.lstat()
        root_attributes = getattr(root_information, "st_file_attributes", 0)
        if (
            not stat.S_ISDIR(root_information.st_mode)
            or nominal_root.is_symlink()
            or root_attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise CoordinatorError(
                "resource-deferred candidate tree contains a linked directory"
            )
        expected_root = nominal_root.resolve()
        for current, directory_names, file_names in os.walk(
            expected_root,
            topdown=True,
            followlinks=False,
            onerror=lambda error: (_ for _ in ()).throw(error),
        ):
            current_path = Path(current)
            current_information = current_path.lstat()
            current_attributes = getattr(current_information, "st_file_attributes", 0)
            if (
                not stat.S_ISDIR(current_information.st_mode)
                or current_path.is_symlink()
                or current_attributes
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            ):
                raise CoordinatorError(
                    "resource-deferred candidate tree contains a linked directory"
                )
            directory_names.sort()
            file_names.sort()
            for name in directory_names:
                child = current_path / name
                information = child.lstat()
                attributes = getattr(information, "st_file_attributes", 0)
                if (
                    not stat.S_ISDIR(information.st_mode)
                    or child.is_symlink()
                    or attributes
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                ):
                    raise CoordinatorError(
                        "resource-deferred candidate tree contains a linked directory"
                    )
                actual_directories.add(
                    child.relative_to(expected_root).as_posix()
                )
            for name in file_names:
                child = current_path / name
                information = child.lstat()
                attributes = getattr(information, "st_file_attributes", 0)
                if (
                    not stat.S_ISREG(information.st_mode)
                    or child.is_symlink()
                    or attributes
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                ):
                    raise CoordinatorError(
                        "resource-deferred candidate tree contains a non-regular file"
                    )
                relative = child.relative_to(expected_root).as_posix()
                digest = hashlib.sha256()
                byte_count = 0
                with child.open("rb") as stream:
                    while True:
                        chunk = stream.read(1 << 20)
                        if not chunk:
                            break
                        byte_count += len(chunk)
                        digest.update(chunk)
                actual_files[relative] = (byte_count, digest.hexdigest().upper())
    except OSError as exc:
        raise CoordinatorError(
            f"cannot enumerate resource-deferred candidate tree: {exc}"
        ) from exc
    if (
        len(actual_files) != RESOURCE_DEFERRED_CANDIDATE_FILE_COUNT
        or len(actual_directories) != RESOURCE_DEFERRED_CANDIDATE_DIRECTORY_COUNT
    ):
        raise CoordinatorError("resource-deferred candidate-tree extent differs")
    archive_directories, archive_files = _resource_deferred_archive_inventory(
        archive_path
    )
    if actual_directories != archive_directories or set(actual_files) != set(archive_files):
        raise CoordinatorError(
            "resource-deferred candidate-tree extent differs from archive"
        )
    for relative, identity in actual_files.items():
        if identity != archive_files[relative]:
            raise CoordinatorError(
                "resource-deferred candidate-tree content differs from archive"
            )


def _validate_predecessor_resource_deferred_incident(value: Any) -> None:
    """Validate the consumed zero-worker resource-admission deferral."""

    location = "$.contract.predecessor_resource_deferred_incident"
    incident = _exact(
        value,
        {
            "aggregate",
            "approval_snapshot",
            "archive_ref",
            "attempt_claim",
            "authorization",
            "candidate_archive",
            "candidate_binding",
            "candidate_tree",
            "contract",
            "ledger_snapshot",
            "manifest",
            "memory_admission",
            "output_root",
            "phase_plan",
            "producer_result",
            "request",
            "request_reuse_forbidden",
            "root_cause",
            "scientific_execution",
            "terminal_ledger_rows",
            "transcript",
        },
        location,
    )
    if (
        incident["output_root"] != str(RESOURCE_DEFERRED_INCIDENT_ROOT)
        or incident["root_cause"]
        != "RESOURCE_ADMISSION_DEFERRED_BEFORE_WORKER_LAUNCH"
        or incident["request_reuse_forbidden"] is not True
    ):
        raise CoordinatorError("resource-deferred incident identity differs")

    scientific = _exact(
        incident["scientific_execution"],
        {
            "checker_processes_started",
            "classifying_records",
            "producer_processes_started",
            "producer_result_present",
        },
        f"{location}.scientific_execution",
    )
    if (
        _nonnegative_integer(
            scientific["checker_processes_started"],
            f"{location}.scientific_execution.checker_processes_started",
        )
        != 0
        or _nonnegative_integer(
            scientific["classifying_records"],
            f"{location}.scientific_execution.classifying_records",
        )
        != 0
        or _nonnegative_integer(
            scientific["producer_processes_started"],
            f"{location}.scientific_execution.producer_processes_started",
        )
        != 0
        or scientific["producer_result_present"] is not True
    ):
        raise CoordinatorError("resource-deferred scientific disposition differs")

    memory = _exact(
        incident["memory_admission"],
        {
            "concurrent_workers_assumed",
            "maximum_memory_gib_per_process_tree",
            "observed_at_event_available_bytes",
            "observation_status",
            "os_headroom_gib",
            "registered_workers",
            "required_bytes",
        },
        f"{location}.memory_admission",
    )
    if (
        _nonnegative_integer(
            memory["concurrent_workers_assumed"],
            f"{location}.memory_admission.concurrent_workers_assumed",
        )
        != 3
        or _nonnegative_integer(
            memory["maximum_memory_gib_per_process_tree"],
            f"{location}.memory_admission.maximum_memory_gib_per_process_tree",
        )
        != 24
        or memory["observed_at_event_available_bytes"] is not None
        or memory["observation_status"] != "NOT_RECORDED"
        or _nonnegative_integer(
            memory["os_headroom_gib"],
            f"{location}.memory_admission.os_headroom_gib",
        )
        != 16
        or _nonnegative_integer(
            memory["registered_workers"],
            f"{location}.memory_admission.registered_workers",
        )
        != 3
        or _nonnegative_integer(
            memory["required_bytes"], f"{location}.memory_admission.required_bytes"
        )
        != RESOURCE_DEFERRED_OLD_ADMISSION_REQUIRED_BYTES
        or memory["required_bytes"]
        != (memory["concurrent_workers_assumed"] * 24 + 16) * (1 << 30)
    ):
        raise CoordinatorError("resource-deferred memory admission differs")

    incident_root = RESOURCE_DEFERRED_INCIDENT_ROOT.resolve()
    bound: dict[str, tuple[Path, bytes]] = {}
    for name, (filename, expected_count, expected_sha256) in (
        RESOURCE_DEFERRED_ARTIFACTS.items()
    ):
        raw_binding = _exact(
            incident[name],
            {"byte_count", "path", "sha256"},
            f"{location}.{name}",
        )
        if (
            _nonnegative_integer(
                raw_binding["byte_count"], f"{location}.{name}.byte_count"
            )
            != expected_count
            or _digest(raw_binding["sha256"], f"{location}.{name}.sha256")
            != expected_sha256
        ):
            raise CoordinatorError(f"resource-deferred {name} identity differs")
        expected_path = RESOURCE_DEFERRED_INCIDENT_ROOT / filename
        bound[name] = _validate_external_file_binding(
            raw_binding, f"{location}.{name}", expected_path=expected_path
        )
        if bound[name][0] != expected_path.resolve():
            raise CoordinatorError(f"resource-deferred {name} resolved path differs")

    request_path = (
        RESOURCE_MANAGER_ROOT / "requests" / f"{RESOURCE_DEFERRED_REQUEST_ID}.json"
    )
    request_binding = _exact(
        incident["request"],
        {"byte_count", "path", "sha256"},
        f"{location}.request",
    )
    if (
        _nonnegative_integer(
            request_binding["byte_count"], f"{location}.request.byte_count"
        )
        != RESOURCE_DEFERRED_REQUEST_BYTE_COUNT
        or _digest(request_binding["sha256"], f"{location}.request.sha256")
        != RESOURCE_DEFERRED_REQUEST_SHA256
    ):
        raise CoordinatorError("resource-deferred request identity differs")
    request_file, request_raw = _validate_external_file_binding(
        request_binding, f"{location}.request", expected_path=request_path
    )

    attempt_path = (
        RESOURCE_MANAGER_ROOT / "attempts" / f"{RESOURCE_DEFERRED_REQUEST_ID}.json"
    )
    attempt_binding = _exact(
        incident["attempt_claim"],
        {"byte_count", "path", "sha256"},
        f"{location}.attempt_claim",
    )
    if (
        _nonnegative_integer(
            attempt_binding["byte_count"], f"{location}.attempt_claim.byte_count"
        )
        != RESOURCE_DEFERRED_ATTEMPT_BYTE_COUNT
        or _digest(attempt_binding["sha256"], f"{location}.attempt_claim.sha256")
        != RESOURCE_DEFERRED_ATTEMPT_SHA256
    ):
        raise CoordinatorError("resource-deferred attempt identity differs")
    attempt_file, attempt_raw = _validate_external_file_binding(
        attempt_binding, f"{location}.attempt_claim", expected_path=attempt_path
    )

    producer_filename, producer_count, producer_sha256 = (
        RESOURCE_DEFERRED_PRODUCER_RESULT
    )
    producer_path = RESOURCE_DEFERRED_INCIDENT_ROOT.joinpath(
        *PurePosixPath(producer_filename).parts
    )
    producer_binding = _exact(
        incident["producer_result"],
        {"byte_count", "path", "sha256"},
        f"{location}.producer_result",
    )
    if (
        _nonnegative_integer(
            producer_binding["byte_count"], f"{location}.producer_result.byte_count"
        )
        != producer_count
        or _digest(
            producer_binding["sha256"], f"{location}.producer_result.sha256"
        )
        != producer_sha256
    ):
        raise CoordinatorError("resource-deferred producer result identity differs")
    producer_file, producer_raw = _validate_external_file_binding(
        producer_binding,
        f"{location}.producer_result",
        expected_path=producer_path,
    )

    try:
        actual_root_names = {entry.name for entry in os.scandir(incident_root)}
        actual_wave_names = {
            entry.name for entry in os.scandir(incident_root / "producer-wave")
        }
    except OSError as exc:
        raise CoordinatorError(
            f"cannot enumerate resource-deferred incident: {exc}"
        ) from exc
    expected_root_names = {
        artifact[0] for artifact in RESOURCE_DEFERRED_ARTIFACTS.values()
    } | {"candidate-source-tree", "producer-wave"}
    if actual_root_names != expected_root_names:
        raise CoordinatorError("resource-deferred incident artifact extent differs")
    if actual_wave_names != {Path(producer_filename).name}:
        raise CoordinatorError("resource-deferred producer-wave extent differs")
    _validate_resource_deferred_candidate_tree(
        incident["candidate_tree"],
        f"{location}.candidate_tree",
        archive_path=bound["candidate_archive"][0],
    )

    request_value, observed_request_raw = _strict_external_json(
        request_file, "resource-deferred request"
    )
    request = _exact(
        request_value,
        {
            "command",
            "estimate_minutes",
            "repository",
            "request_id",
            "requested_at",
            "status",
            "task",
        },
        f"{location}.request_file",
    )
    if (
        request_file != request_path.resolve()
        or observed_request_raw != request_raw
        or request["request_id"] != RESOURCE_DEFERRED_REQUEST_ID
        or request["requested_at"] != RESOURCE_DEFERRED_REQUESTED_AT
        or request["task"] != RESOURCE_DEFERRED_TASK
        or request["repository"] != RESOURCE_DEFERRED_REPOSITORY
        or request["status"] != "PENDING"
        or _nonnegative_integer(
            request["estimate_minutes"], f"{location}.request_file.estimate_minutes"
        )
        != 30
        or not isinstance(request["command"], str)
        or sha256(request["command"].encode("utf-8"))
        != RESOURCE_DEFERRED_COMMAND_SHA256
    ):
        raise CoordinatorError("resource-deferred request content differs")

    attempt = _exact(
        _canonical_external_json(attempt_raw, "resource-deferred attempt claim"),
        {"contract_sha256", "request_id", "schema"},
        f"{location}.attempt_claim_file",
    )
    if (
        attempt_file != attempt_path.resolve()
        or attempt
        != {
            "contract_sha256": RESOURCE_DEFERRED_CONTRACT_SHA256,
            "request_id": RESOURCE_DEFERRED_REQUEST_ID,
            "schema": "anysolver.resource-attempt-claim-v1",
        }
    ):
        raise CoordinatorError("resource-deferred consumed attempt differs")

    snapshot = _exact(
        _canonical_external_json(
            bound["approval_snapshot"][1], "resource-deferred approval snapshot"
        ),
        {"approved_row", "candidate", "ledger", "request", "schema"},
        f"{location}.approval_snapshot_file",
    )
    approved = _exact(
        snapshot["approved_row"],
        {"line", "sha256"},
        f"{location}.approval_snapshot_file.approved_row",
    )
    approved_line = approved["line"]
    if (
        snapshot["schema"]
        != "anysolver.e4-pl-s3-v2-stage4a-approval-snapshot-v2"
        or snapshot["candidate"]
        != {
            "commit": RESOURCE_DEFERRED_CANDIDATE_COMMIT,
            "tree": RESOURCE_DEFERRED_CANDIDATE_TREE,
        }
        or not isinstance(approved_line, str)
        or "\n" in approved_line
        or "\r" in approved_line
        or _digest(approved["sha256"], f"{location}.approved_row.sha256")
        != RESOURCE_DEFERRED_LEDGER_ROW_SHA256["APPROVED"]
        or sha256((approved_line + "\n").encode("utf-8"))
        != RESOURCE_DEFERRED_LEDGER_ROW_SHA256["APPROVED"]
    ):
        raise CoordinatorError("resource-deferred approval snapshot differs")
    snapshot_request = _exact(
        snapshot["request"],
        {"byte_count", "path", "request_id", "sha256"},
        f"{location}.approval_snapshot_file.request",
    )
    snapshot_ledger = _exact(
        snapshot["ledger"],
        {"byte_count", "path", "sha256", "snapshot_path"},
        f"{location}.approval_snapshot_file.ledger",
    )
    if (
        snapshot_request
        != {
            "byte_count": RESOURCE_DEFERRED_REQUEST_BYTE_COUNT,
            "path": str(request_path),
            "request_id": RESOURCE_DEFERRED_REQUEST_ID,
            "sha256": RESOURCE_DEFERRED_REQUEST_SHA256,
        }
        or snapshot_ledger
        != {
            "byte_count": RESOURCE_DEFERRED_ARTIFACTS["ledger_snapshot"][1],
            "path": str(RESOURCE_LEDGER_PATH),
            "sha256": RESOURCE_DEFERRED_ARTIFACTS["ledger_snapshot"][2],
            "snapshot_path": str(
                RESOURCE_DEFERRED_INCIDENT_ROOT
                / RESOURCE_DEFERRED_ARTIFACTS["ledger_snapshot"][0]
            ),
        }
    ):
        raise CoordinatorError("resource-deferred approval joins differ")
    try:
        ledger_snapshot_text = bound["ledger_snapshot"][1].decode("utf-8-sig")
    except UnicodeError as exc:
        raise CoordinatorError("resource-deferred ledger snapshot is not UTF-8") from exc
    if ledger_snapshot_text.splitlines().count(approved_line) != 1:
        raise CoordinatorError("resource-deferred approved row is absent or duplicated")

    candidate_binding = _exact(
        _canonical_external_json(
            bound["candidate_binding"][1], "resource-deferred candidate binding"
        ),
        {
            "artifact_path",
            "artifact_sha256",
            "candidate_id",
            "commit",
            "formulation_id",
            "schema",
            "selector",
            "tree",
        },
        f"{location}.candidate_binding_file",
    )
    if candidate_binding != {
        "artifact_path": str(
            RESOURCE_DEFERRED_INCIDENT_ROOT
            / RESOURCE_DEFERRED_ARTIFACTS["candidate_archive"][0]
        ),
        "artifact_sha256": RESOURCE_DEFERRED_ARTIFACTS["candidate_archive"][2],
        "candidate_id": "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1",
        "commit": RESOURCE_DEFERRED_CANDIDATE_COMMIT,
        "formulation_id": "E4_PL_QUALIFIED_S3_COMPANION_V2",
        "schema": "anysolver.e4-pl-s3-v2-flat-candidate-binding-v1",
        "selector": "e4-pl-s3-v2",
        "tree": RESOURCE_DEFERRED_CANDIDATE_TREE,
    }:
        raise CoordinatorError("resource-deferred candidate archive join differs")

    plan = _exact(
        _canonical_external_json(
            bound["phase_plan"][1], "resource-deferred phase plan"
        ),
        {
            "advisory_review_triggers",
            "formal_thresholds",
            "manifest_sha256",
            "phase",
            "prerequisites",
            "record_count",
            "schema",
            "scope",
            "selector",
            "shards",
        },
        f"{location}.phase_plan_file",
    )
    shards = plan["shards"]
    if (
        plan["schema"] != "anysolver.e4-pl-s3-v2-flat-funnel-plan-v1"
        or plan["phase"] != "4A"
        or plan["scope"] != "full"
        or plan["selector"] != "e4-pl-s3-v2"
        or plan["prerequisites"] != []
        or plan["manifest_sha256"]
        != RESOURCE_DEFERRED_CONNECTIVITY_MANIFEST_SHA256
        or _nonnegative_integer(plan["record_count"], f"{location}.plan.record_count")
        != 81
        or not isinstance(shards, list)
        or len(shards) != 3
        or [
            shard.get("assignment_id") if isinstance(shard, dict) else None
            for shard in shards
        ]
        != list(EXPECTED_SHARDS)
        or any(
            not isinstance(shard.get("records"), list)
            or len(shard["records"]) != 27
            for shard in shards
        )
    ):
        raise CoordinatorError("resource-deferred phase-plan identity differs")

    manifest = _exact(
        _canonical_external_json(
            bound["manifest"][1], "resource-deferred producer manifest"
        ),
        {"lane", "output_root", "schema", "wave_id", "workers"},
        f"{location}.manifest_file",
    )
    wave_root = (RESOURCE_DEFERRED_INCIDENT_ROOT / "producer-wave").resolve()
    workers = manifest["workers"]
    if (
        manifest["schema"] != "anysolver.e4-pl-s3-v2-bounded-wave-manifest-v1"
        or manifest["wave_id"] != "S3_V2_FLAT_FUNNEL_4A_FULL"
        or manifest["lane"] != "flat-proof"
        or manifest["output_root"]
        != str(RESOURCE_DEFERRED_INCIDENT_ROOT / "producer-wave")
        or not isinstance(workers, list)
        or len(workers) != 3
        or [worker.get("assignment_id") for worker in workers]
        != list(EXPECTED_SHARDS)
    ):
        raise CoordinatorError("resource-deferred producer manifest identity differs")
    for worker in workers:
        if (
            worker.get("plan_path")
            != str(
                RESOURCE_DEFERRED_INCIDENT_ROOT
                / RESOURCE_DEFERRED_ARTIFACTS["phase_plan"][0]
            )
            or worker.get("plan_sha256")
            != RESOURCE_DEFERRED_ARTIFACTS["phase_plan"][2]
        ):
            raise CoordinatorError("resource-deferred worker plan binding differs")
        assignment_id = worker["assignment_id"]
        assignment_root = wave_root / assignment_id
        for key, filename in (
            ("progress_path", "progress.jsonl"),
            ("scientific_path", "scientific.json"),
            ("stderr_path", "stderr.log"),
            ("stdout_path", "stdout.log"),
        ):
            if worker.get(key) != str(assignment_root / filename):
                raise CoordinatorError("resource-deferred worker output path differs")
        input_hashes = worker.get("input_hashes")
        if not isinstance(input_hashes, list):
            raise CoordinatorError("resource-deferred worker input graph is malformed")
        inputs = {
            item.get("path"): item.get("sha256")
            for item in input_hashes
            if isinstance(item, dict) and set(item) == {"path", "sha256"}
        }
        if (
            len(inputs) != len(input_hashes)
            or inputs.get(str(AUTHORITY_PATH))
            != RESOURCE_DEFERRED_AUTHORITY_SHA256
            or inputs.get(str(REFERENCE_CASES / "e4_pl_s3_v2_stage4a_contract.json"))
            != RESOURCE_DEFERRED_CONTRACT_SHA256
            or inputs.get(
                str(REFERENCE_CASES / "e4_pl_s3_v2_stage4a_execution_authorization.json")
            )
            != RESOURCE_DEFERRED_AUTHORIZATION_SHA256
            or inputs.get(
                str(
                    RESOURCE_DEFERRED_INCIDENT_ROOT
                    / RESOURCE_DEFERRED_ARTIFACTS["candidate_binding"][0]
                )
            )
            != RESOURCE_DEFERRED_ARTIFACTS["candidate_binding"][2]
        ):
            raise CoordinatorError("resource-deferred worker frozen-input join differs")
    bounded = _load_module(
        "_s3_v2_resource_deferred_incident_bounded", BOUNDED_PATH
    )
    validated_wave_id, validated_lane, validated_root, validated_workers = (
        bounded.validate_manifest(manifest)
    )
    if (
        validated_wave_id != manifest["wave_id"]
        or validated_lane != manifest["lane"]
        or validated_root != wave_root
        or [worker.assignment_id for worker in validated_workers]
        != list(EXPECTED_SHARDS)
    ):
        raise CoordinatorError("resource-deferred bounded manifest validation differs")

    producer_result = _exact(
        _canonical_external_json(producer_raw, "resource-deferred producer result"),
        {"lane", "manifest_sha256", "schema", "terminal", "wave_id", "workers"},
        f"{location}.producer_result_file",
    )
    if (
        producer_file != producer_path.resolve()
        or producer_result
        != {
            "lane": "flat-proof",
            "manifest_sha256": RESOURCE_DEFERRED_ARTIFACTS["manifest"][2],
            "schema": PRODUCER_RESULT_SCHEMA,
            "terminal": "RESOURCE_DEFERRED",
            "wave_id": "S3_V2_FLAT_FUNNEL_4A_FULL",
            "workers": [],
        }
    ):
        raise CoordinatorError("resource-deferred producer result differs")

    aggregate = _exact(
        _canonical_external_json(
            bound["aggregate"][1], "resource-deferred aggregate"
        ),
        {
            "advisory_review_required",
            "authorization_sha256",
            "checker_replica_bindings",
            "classifying_record_count",
            "contract_sha256",
            "formal_failures",
            "producer_wave_result_sha256",
            "production_restriction",
            "schema",
            "sequence_results",
            "successor_expansion_authorized",
            "terminal",
            "v1_diagnostic_record_count",
        },
        f"{location}.aggregate_file",
    )
    if (
        aggregate["schema"] != AGGREGATE_SCHEMA
        or aggregate["terminal"] != BLOCKED
        or aggregate["formal_failures"] != ["PRODUCER_WAVE_NOT_COMPLETED"]
        or aggregate["authorization_sha256"]
        != RESOURCE_DEFERRED_AUTHORIZATION_SHA256
        or aggregate["contract_sha256"] != RESOURCE_DEFERRED_CONTRACT_SHA256
        or aggregate["producer_wave_result_sha256"] != producer_sha256
        or aggregate["checker_replica_bindings"] != []
        or aggregate["sequence_results"] != []
        or aggregate["production_restriction"] != PRODUCTION_RESTRICTION
        or aggregate["advisory_review_required"] is not False
        or aggregate["successor_expansion_authorized"] is not False
        or _nonnegative_integer(
            aggregate["classifying_record_count"],
            f"{location}.aggregate.classifying_record_count",
        )
        != 0
        or _nonnegative_integer(
            aggregate["v1_diagnostic_record_count"],
            f"{location}.aggregate.v1_diagnostic_record_count",
        )
        != 0
    ):
        raise CoordinatorError("resource-deferred aggregate disposition differs")

    authorization_binding = _exact(
        incident["authorization"],
        {"byte_count", "commit", "parent", "path", "sha256", "subject", "tree"},
        f"{location}.authorization",
    )
    contract_binding = _exact(
        incident["contract"],
        {"byte_count", "commit", "parent", "path", "sha256", "subject", "tree"},
        f"{location}.contract",
    )
    expected_authorization_binding = {
        "byte_count": RESOURCE_DEFERRED_AUTHORIZATION_BYTE_COUNT,
        "commit": RESOURCE_DEFERRED_AUTHORIZATION_COMMIT,
        "parent": RESOURCE_DEFERRED_AUTHORIZATION_PARENT,
        "path": PREDECESSOR_AUTHORIZATION_PATH,
        "sha256": RESOURCE_DEFERRED_AUTHORIZATION_SHA256,
        "subject": RESOURCE_DEFERRED_AUTHORIZATION_SUBJECT,
        "tree": RESOURCE_DEFERRED_AUTHORIZATION_TREE,
    }
    expected_contract_binding = {
        "byte_count": RESOURCE_DEFERRED_CONTRACT_BYTE_COUNT,
        "commit": RESOURCE_DEFERRED_CONTRACT_COMMIT,
        "parent": RESOURCE_DEFERRED_CONTRACT_PARENT,
        "path": PREDECESSOR_CONTRACT_PATH,
        "sha256": RESOURCE_DEFERRED_CONTRACT_SHA256,
        "subject": RESOURCE_DEFERRED_CONTRACT_SUBJECT,
        "tree": RESOURCE_DEFERRED_CONTRACT_TREE,
    }
    if authorization_binding != expected_authorization_binding:
        raise CoordinatorError("resource-deferred authorization binding differs")
    if contract_binding != expected_contract_binding:
        raise CoordinatorError("resource-deferred contract binding differs")
    _validate_git_object_authority()
    for binding in (authorization_binding, contract_binding):
        commit = binding["commit"]
        if (
            _git("rev-parse", commit) != commit
            or _git("rev-parse", f"{commit}^{{tree}}") != binding["tree"]
            or _git("show", "-s", "--format=%P", commit) != binding["parent"]
            or _git("show", "-s", "--format=%s", commit) != binding["subject"]
        ):
            raise CoordinatorError("resource-deferred Git topology differs")
    authorization_raw = _git(
        "show",
        f"{RESOURCE_DEFERRED_AUTHORIZATION_COMMIT}:{PREDECESSOR_AUTHORIZATION_PATH}",
        binary=True,
    )
    contract_raw = _git(
        "show",
        f"{RESOURCE_DEFERRED_CONTRACT_COMMIT}:{PREDECESSOR_CONTRACT_PATH}",
        binary=True,
    )
    contract_at_authorization = _git(
        "show",
        f"{RESOURCE_DEFERRED_AUTHORIZATION_COMMIT}:{PREDECESSOR_CONTRACT_PATH}",
        binary=True,
    )
    if (
        len(authorization_raw) != RESOURCE_DEFERRED_AUTHORIZATION_BYTE_COUNT
        or sha256(authorization_raw) != RESOURCE_DEFERRED_AUTHORIZATION_SHA256
        or len(contract_raw) != RESOURCE_DEFERRED_CONTRACT_BYTE_COUNT
        or sha256(contract_raw) != RESOURCE_DEFERRED_CONTRACT_SHA256
        or contract_at_authorization != contract_raw
    ):
        raise CoordinatorError("resource-deferred Git evidence blob differs")

    authorization = _exact(
        _canonical_external_json(
            authorization_raw, "resource-deferred execution authorization"
        ),
        {
            "contract_path",
            "contract_sha256",
            "execution_paths",
            "formal_execution_authorized",
            "implementation_reviews",
            "ledger_approval",
            "resource_lock_required",
            "resource_request",
            "schema",
            "user_approval",
        },
        f"{location}.authorization_blob",
    )
    execution_paths = _exact(
        authorization["execution_paths"],
        {"aggregate_path", "approval_snapshot_path", "output_root", "python_executable"},
        f"{location}.authorization_blob.execution_paths",
    )
    resource_request = _exact(
        authorization["resource_request"],
        {
            "command_sha256",
            "repository",
            "request_id",
            "request_path",
            "request_sha256",
            "task",
        },
        f"{location}.authorization_blob.resource_request",
    )
    ledger_approval = _exact(
        authorization["ledger_approval"],
        {"approved_row_sha256", "ledger_path", "snapshot_path", "snapshot_sha256"},
        f"{location}.authorization_blob.ledger_approval",
    )
    user_approval = _exact(
        authorization["user_approval"],
        {"recorded", "source"},
        f"{location}.authorization_blob.user_approval",
    )
    expected_reviews = [
        {
            "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_process_implementation_review.json",
            "role": "PROCESS_AND_AUTHORITY",
            "sha256": "7B7CF54AD998E31B11B2F4286C3BE638126817D28D7290F90B15BA1AAB0109E3",
            "verdict": "ACCEPT_STAGE4A_PROCESS_IMPLEMENTATION_NO_P0_P1",
        },
        {
            "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_scientific_implementation_review.json",
            "role": "SCIENTIFIC_AND_MECHANICS",
            "sha256": "22EA28DAC7719F8748389204860AA4B90E936EE96AE564F414801D539D84A797",
            "verdict": "ACCEPT_STAGE4A_SCIENTIFIC_IMPLEMENTATION_NO_P0_P1",
        },
    ]
    if (
        authorization["schema"] != AUTHORIZATION_SCHEMA
        or authorization["contract_path"] != PREDECESSOR_CONTRACT_PATH
        or authorization["contract_sha256"] != RESOURCE_DEFERRED_CONTRACT_SHA256
        or authorization["formal_execution_authorized"] is not True
        or authorization["resource_lock_required"] is not True
        or authorization["implementation_reviews"] != expected_reviews
        or execution_paths["output_root"] != str(RESOURCE_DEFERRED_INCIDENT_ROOT)
        or execution_paths["aggregate_path"]
        != str(
            RESOURCE_DEFERRED_INCIDENT_ROOT
            / RESOURCE_DEFERRED_ARTIFACTS["aggregate"][0]
        )
        or execution_paths["approval_snapshot_path"]
        != str(
            RESOURCE_DEFERRED_INCIDENT_ROOT
            / RESOURCE_DEFERRED_ARTIFACTS["approval_snapshot"][0]
        )
        or resource_request
        != {
            "command_sha256": RESOURCE_DEFERRED_COMMAND_SHA256,
            "repository": RESOURCE_DEFERRED_REPOSITORY,
            "request_id": RESOURCE_DEFERRED_REQUEST_ID,
            "request_path": str(request_path),
            "request_sha256": RESOURCE_DEFERRED_REQUEST_SHA256,
            "task": RESOURCE_DEFERRED_TASK,
        }
        or ledger_approval
        != {
            "approved_row_sha256": RESOURCE_DEFERRED_LEDGER_ROW_SHA256["APPROVED"],
            "ledger_path": str(RESOURCE_LEDGER_PATH),
            "snapshot_path": str(
                RESOURCE_DEFERRED_INCIDENT_ROOT
                / RESOURCE_DEFERRED_ARTIFACTS["approval_snapshot"][0]
            ),
            "snapshot_sha256": RESOURCE_DEFERRED_ARTIFACTS["approval_snapshot"][2],
        }
        or user_approval["recorded"] is not True
        or not isinstance(user_approval["source"], str)
        or RESOURCE_DEFERRED_REQUEST_ID not in user_approval["source"]
    ):
        raise CoordinatorError("resource-deferred authorization joins differ")

    contract = _canonical_external_json(contract_raw, "resource-deferred contract")
    contract_candidate = contract.get("candidate")
    if (
        contract.get("schema") != "anysolver.e4-pl-s3-v2-stage4a-contract-v3"
        or not isinstance(contract_candidate, dict)
        or contract_candidate.get("commit") != RESOURCE_DEFERRED_CANDIDATE_COMMIT
        or contract_candidate.get("tree") != RESOURCE_DEFERRED_CANDIDATE_TREE
        or contract.get("execution", {}).get("maximum_workers") != 3
        or contract.get("execution", {}).get("maximum_memory_gib_per_process_tree")
        != 24
    ):
        raise CoordinatorError("resource-deferred contract content differs")
    frozen_files = contract.get("frozen_files")
    if not isinstance(frozen_files, list):
        raise CoordinatorError("resource-deferred frozen graph is malformed")
    frozen_by_path = {
        item.get("path"): item.get("git_blob_sha256")
        for item in frozen_files
        if isinstance(item, dict)
    }
    coordinator_path = "docs/reference_cases/e4_pl_s3_v2_stage4a_coordinator.py"
    bounded_path = "docs/reference_cases/e4_pl_s3_v2_bounded_process.py"
    if (
        frozen_by_path.get(coordinator_path) != RESOURCE_DEFERRED_COORDINATOR_SHA256
        or frozen_by_path.get(bounded_path) != RESOURCE_DEFERRED_BOUNDED_SHA256
        or sha256(
            _git(
                "show",
                f"{RESOURCE_DEFERRED_AUTHORIZATION_COMMIT}:{coordinator_path}",
                binary=True,
            )
        )
        != RESOURCE_DEFERRED_COORDINATOR_SHA256
        or sha256(
            _git(
                "show",
                f"{RESOURCE_DEFERRED_AUTHORIZATION_COMMIT}:{bounded_path}",
                binary=True,
            )
        )
        != RESOURCE_DEFERRED_BOUNDED_SHA256
    ):
        raise CoordinatorError("resource-deferred process authority differs")

    archive_ref = _exact(
        incident["archive_ref"], {"commit", "ref"}, f"{location}.archive_ref"
    )
    if archive_ref != {
        "commit": RESOURCE_DEFERRED_ARCHIVE_COMMIT,
        "ref": RESOURCE_DEFERRED_ARCHIVE_REF,
    } or _git("rev-parse", RESOURCE_DEFERRED_ARCHIVE_REF) != RESOURCE_DEFERRED_ARCHIVE_COMMIT:
        raise CoordinatorError("resource-deferred archive ref differs")

    try:
        transcript = bound["transcript"][1].decode("utf-8-sig")
    except UnicodeError as exc:
        raise CoordinatorError("resource-deferred transcript is not UTF-8") from exc
    transcript_lines = [line.strip() for line in transcript.splitlines()]
    if (
        transcript_lines.count("REGISTERED_COMMAND_EXIT=2") != 1
        or "REGISTERED_COMMAND_EXIT=0" in transcript_lines
        or f"FORMAL_TERMINAL={PASS}" in transcript_lines
        or f"FORMAL_TERMINAL={NO_GO}" in transcript_lines
    ):
        raise CoordinatorError("resource-deferred transcript disposition differs")

    terminal_rows = incident["terminal_ledger_rows"]
    if not isinstance(terminal_rows, list) or len(terminal_rows) != 2:
        raise CoordinatorError("resource-deferred terminal ledger coverage differs")
    terminal_lines: list[str] = []
    for index, (raw_row, expected_status) in enumerate(
        zip(terminal_rows, ("EXECUTION_STARTED", "COMPLETED_FAIL"))
    ):
        row = _exact(
            raw_row,
            {"line", "sha256", "status"},
            f"{location}.terminal_ledger_rows[{index}]",
        )
        line = row["line"]
        if (
            row["status"] != expected_status
            or not isinstance(line, str)
            or "\r" in line
            or "\n" in line
            or _digest(row["sha256"], f"{location}.terminal_ledger_rows[{index}].sha256")
            != RESOURCE_DEFERRED_LEDGER_ROW_SHA256[expected_status]
            or sha256((line + "\n").encode("utf-8"))
            != RESOURCE_DEFERRED_LEDGER_ROW_SHA256[expected_status]
        ):
            raise CoordinatorError("resource-deferred terminal ledger row differs")
        fields = [field.strip() for field in line.split("|")]
        if (
            len(fields) < 5
            or fields[2] != RESOURCE_DEFERRED_REQUEST_ID
            or fields[3] != expected_status
        ):
            raise CoordinatorError("resource-deferred terminal ledger fields differ")
        terminal_lines.append(line)
    try:
        live_ledger = RESOURCE_LEDGER_PATH.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise CoordinatorError(
            f"cannot validate resource-deferred live ledger: {exc}"
        ) from exc
    matching_rows = [
        line
        for line in live_ledger.splitlines()
        if f"| {RESOURCE_DEFERRED_REQUEST_ID} |" in line
    ]
    if matching_rows != [approved_line, *terminal_lines]:
        raise CoordinatorError("resource-deferred live ledger history differs")


def validate_contract(path: Path) -> tuple[Mapping[str, Any], bytes]:
    value, raw = strict_json_load(path)
    if raw != canonical_bytes(value):
        raise CoordinatorError("Stage 4A contract is not canonical JSON")
    contract = _exact(
        value,
        CONTRACT_KEYS,
        "$contract",
    )
    if contract["schema"] != CONTRACT_SCHEMA or contract["stage"] != "STAGE_4A":
        raise CoordinatorError("Stage 4A contract identity differs")
    _validate_predecessor_process_incident(
        contract["predecessor_process_incident"]
    )
    _validate_predecessor_resource_deferred_incident(
        contract["predecessor_resource_deferred_incident"]
    )
    git_authority = _exact(
        contract["git_authority"],
        {
            "engine_byte_count",
            "engine_path",
            "engine_sha256",
            "exec_path",
            "launcher_byte_count",
            "launcher_path",
            "launcher_sha256",
            "version",
        },
        "$.contract.git_authority",
    )
    discovered_git = _discover_git_runtime()
    if git_authority != discovered_git:
        raise CoordinatorError("registered Git launcher or engine identity differs")
    _validate_git_object_authority()
    authority_value, authority_raw = strict_json_load(AUTHORITY_PATH)
    if authority_raw != canonical_bytes(authority_value):
        raise CoordinatorError("Stage 4A authority is not canonical JSON")
    if authority_value.get("schema") != AUTHORITY_SCHEMA:
        raise CoordinatorError("Stage 4A authority schema differs")
    authority = _exact(
        contract["authority"],
        {"commit", "path", "schema", "sha256", "tree"},
        "$.contract.authority",
    )
    authority_commit = _lower_object(authority["commit"], "$.contract.authority.commit")
    authority_tree = _lower_object(authority["tree"], "$.contract.authority.tree")
    authority_path = _repo_relative_path(authority["path"], "$.contract.authority.path")
    if (
        authority_path != AUTHORITY_PATH.resolve()
        or authority["schema"] != AUTHORITY_SCHEMA
        or authority["sha256"] != sha256(authority_raw)
        or _git("rev-parse", authority_commit) != authority_commit
        or _git("rev-parse", f"{authority_commit}^{{tree}}") != authority_tree
        or _git_blob_sha256(authority_commit, str(authority["path"])) != sha256(authority_raw)
    ):
        raise CoordinatorError("Stage 4A authority binding differs")
    candidate = _exact(
        contract["candidate"],
        {"changed_paths", "commit", "scope_base_commit", "subject", "tree"},
        "$.contract.candidate",
    )
    commit = _lower_object(candidate["commit"], "$.contract.candidate.commit")
    tree = _lower_object(candidate["tree"], "$.contract.candidate.tree")
    scope_base = _lower_object(
        candidate["scope_base_commit"], "$.contract.candidate.scope_base_commit"
    )
    if (
        _git("rev-parse", commit) != commit
        or _git("rev-parse", f"{commit}^{{tree}}") != tree
        or _git("show", "-s", "--format=%s", commit) != candidate["subject"]
        or scope_base != authority_value["scope_base"]["commit"]
    ):
        raise CoordinatorError("frozen candidate Git identity differs")
    if _git_run("merge-base", "--is-ancestor", commit, "HEAD", check=False).returncode:
        raise CoordinatorError("frozen candidate is not an ancestor of execution HEAD")
    if _git("status", "--porcelain=v1", "--untracked-files=all"):
        raise CoordinatorError("formal Stage 4A input worktree is dirty")
    changed_paths = candidate["changed_paths"]
    if (
        not isinstance(changed_paths, list)
        or any(not isinstance(item, str) for item in changed_paths)
        or changed_paths != sorted(set(changed_paths))
    ):
        raise CoordinatorError("candidate changed-path set is not canonical")
    registered_extent = sorted(
        authority_value["allowed_extent"]["authority_commit_paths"]
        + authority_value["allowed_extent"]["implementation_paths"]
    )
    actual_changed = sorted(
        filter(
            None,
            str(
                _git(
                    "diff",
                    "--no-ext-diff",
                    "--name-only",
                    scope_base,
                    commit,
                    "--",
                )
            ).splitlines(),
        )
    )
    if changed_paths != registered_extent or changed_paths != actual_changed:
        raise CoordinatorError("candidate changed-path extent differs")
    dependencies = contract["dependencies"]
    if not isinstance(dependencies, list) or len(dependencies) != len(
        DEPENDENCY_REPOSITORIES
    ):
        raise CoordinatorError("Stage 4A dependency graph differs")
    for index, ((expected_name, expected_root), raw_dependency) in enumerate(
        zip(DEPENDENCY_REPOSITORIES, dependencies)
    ):
        dependency = _exact(
            raw_dependency,
            {"commit", "name", "path", "source_path", "tree"},
            f"$.contract.dependencies[{index}]",
        )
        repository = Path(str(dependency["path"])).resolve()
        source = Path(str(dependency["source_path"])).resolve()
        dependency_commit = _lower_object(
            dependency["commit"], f"$.contract.dependencies[{index}].commit"
        )
        dependency_tree = _lower_object(
            dependency["tree"], f"$.contract.dependencies[{index}].tree"
        )
        if (
            dependency["name"] != expected_name
            or repository != expected_root.resolve()
            or source != (expected_root / "src").resolve()
            or not source.is_dir()
        ):
            raise CoordinatorError("Stage 4A dependency path or order differs")
        _validate_git_object_authority(repository)
        if (
            _git("rev-parse", "HEAD", repository=repository) != dependency_commit
            or _git(
                "rev-parse",
                f"{dependency_commit}^{{tree}}",
                repository=repository,
            )
            != dependency_tree
            or _git(
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                repository=repository,
            )
        ):
            raise CoordinatorError(f"Stage 4A dependency is dirty or differs: {expected_name}")
    files = contract["frozen_files"]
    if not isinstance(files, list) or not files:
        raise CoordinatorError("Stage 4A frozen-file graph is empty")
    seen: set[str] = set()
    roles: set[str] = set()
    for index, raw_binding in enumerate(files):
        binding = _exact(
            raw_binding,
            {"git_blob_sha256", "path", "role"},
            f"$.contract.frozen_files[{index}]",
        )
        made_path = str(binding["path"])
        _repo_relative_path(made_path, f"$.contract.frozen_files[{index}].path")
        role = binding["role"]
        if (
            made_path in seen
            or not isinstance(role, str)
            or not role
            or role in roles
        ):
            raise CoordinatorError("Stage 4A frozen-file path is absent or duplicated")
        seen.add(made_path)
        roles.add(role)
        if _git_blob_sha256(commit, made_path) != _digest(
            binding["git_blob_sha256"], f"$.contract.frozen_files[{index}].git_blob_sha256"
        ):
            raise CoordinatorError(f"frozen Git blob differs: {made_path}")
        if _git_run(
            "diff", "--no-ext-diff", "--quiet", commit, "--", made_path, check=False
        ).returncode:
            raise CoordinatorError(f"working file differs from frozen candidate: {made_path}")
    if seen != REQUIRED_FROZEN_PATHS or [item["path"] for item in files] != sorted(seen):
        raise CoordinatorError("Stage 4A frozen-file graph coverage or order differs")
    if contract["coverage"] != {
        "classifying_records": 81,
        "records_per_diagonal_shard": 27,
        "v1_diagnostic_records": 72,
    }:
        raise CoordinatorError("Stage 4A coverage contract differs")
    if contract["execution"] != _execution_policy():
        raise CoordinatorError("Stage 4A bounded execution contract differs")
    if contract["production_boundary"] != {
        "default_s3_formulation": "legacy-s3",
        "default_s3_unchanged": True,
        "q4_default": "e4-pl",
        "q4_mechanics_unchanged": True,
        "v1_fallback_forbidden": True,
    }:
        raise CoordinatorError("Stage 4A production boundary differs")
    if contract["protocol"] != authority_value["formal_protocol"]:
        raise CoordinatorError("Stage 4A scientific protocol differs from authority")
    if contract["adjudication"] != {
        "advisory_policy": authority_value["advisory_policy"],
        "production_restriction": PRODUCTION_RESTRICTION,
        "terminal_precedence": [BLOCKED, NO_GO, PASS],
    }:
        raise CoordinatorError("Stage 4A adjudication contract differs")
    return contract, raw


def _review_inputs(contract: Mapping[str, Any], contract_raw: bytes) -> dict[str, str]:
    return {
        "candidate_commit": str(contract["candidate"]["commit"]),
        "candidate_tree": str(contract["candidate"]["tree"]),
        "changed_paths_sha256": sha256(canonical_bytes(contract["candidate"]["changed_paths"])),
        "contract_sha256": sha256(contract_raw),
        "dependency_graph_sha256": sha256(canonical_bytes(contract["dependencies"])),
        "frozen_file_graph_sha256": sha256(canonical_bytes(contract["frozen_files"])),
    }


def _validate_review(
    path: Path,
    *,
    role: str,
    expected_inputs: Mapping[str, str],
) -> tuple[Mapping[str, Any], bytes]:
    value, raw = strict_json_load(path)
    if raw != canonical_bytes(value):
        raise CoordinatorError("implementation review is not canonical JSON")
    review = _exact(
        value,
        {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"},
        "$.review",
    )
    findings = _exact(review["findings"], {"P0", "P1"}, "$.review.findings")
    independence = _exact(
        review["reviewer_independence"],
        {
            "authored_candidate",
            "independent_of_other_reviewer",
            "reviewer_id",
            "reviewer_role",
        },
        "$.review.reviewer_independence",
    )
    if (
        review["schema"] != REVIEW_SCHEMA
        or review["verdict"] != EXPECTED_REVIEW_VERDICTS[role]
        or findings != {"P0": [], "P1": []}
        or review["reviewed_inputs"] != expected_inputs
        or independence["authored_candidate"] is not False
        or independence["independent_of_other_reviewer"] is not True
        or independence["reviewer_role"] != role
        or not isinstance(independence["reviewer_id"], str)
        or not independence["reviewer_id"]
    ):
        raise CoordinatorError("implementation review does not accept the exact freeze")
    return review, raw


def _powershell_quote(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def expected_resource_command(
    *,
    python_executable: Path,
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    aggregate_path: Path,
) -> str:
    dependency_path = ";".join(
        str((repository / "src").resolve())
        for _name, repository in DEPENDENCY_REPOSITORIES
    )
    parts = [
        f"$env:PYTHONPATH={_powershell_quote(dependency_path)};",
        "$env:PYTHONNOUSERSITE='1';",
        "$env:PYTHONDONTWRITEBYTECODE='1';",
        "&",
        _powershell_quote(python_executable.resolve()),
        "-I",
        "-B",
        _powershell_quote(Path(__file__).resolve()),
        _powershell_quote("--run-stage4a"),
        _powershell_quote("--contract"),
        _powershell_quote(contract_path.resolve()),
        _powershell_quote("--authorization"),
        _powershell_quote(authorization_path.resolve()),
        _powershell_quote("--output-root"),
        _powershell_quote(output_root.resolve()),
        _powershell_quote("--aggregate"),
        _powershell_quote(aggregate_path.resolve()),
    ]
    return " ".join(parts)


def _validate_approval_snapshot(
    path: Path,
    *,
    contract: Mapping[str, Any],
    request_id: str,
    request_path: Path,
    request_raw: bytes,
) -> tuple[Mapping[str, Any], bytes]:
    value, raw = strict_json_load(path)
    if raw != canonical_bytes(value):
        raise CoordinatorError("resource approval snapshot is not canonical JSON")
    snapshot = _exact(
        value,
        {"approved_row", "candidate", "ledger", "request", "schema"},
        "$.approval_snapshot",
    )
    approved = _exact(
        snapshot["approved_row"], {"line", "sha256"}, "$.approval_snapshot.approved_row"
    )
    ledger = _exact(
        snapshot["ledger"],
        {"byte_count", "path", "sha256", "snapshot_path"},
        "$.approval_snapshot.ledger",
    )
    request = _exact(
        snapshot["request"],
        {"byte_count", "path", "request_id", "sha256"},
        "$.approval_snapshot.request",
    )
    line = approved["line"]
    ledger_snapshot_path = Path(str(ledger["snapshot_path"])).resolve()
    ledger_byte_count = _nonnegative_integer(
        ledger["byte_count"], "$.approval_snapshot.ledger.byte_count"
    )
    if (
        not ledger_snapshot_path.is_file()
        or ledger_snapshot_path.is_symlink()
        or ledger_snapshot_path.parent != path.parent.resolve()
        or ledger_snapshot_path.name != "resource-ledger-pre-run.md"
    ):
        raise CoordinatorError("preserved pre-run ledger snapshot path differs")
    ledger_raw = ledger_snapshot_path.read_bytes()
    if (
        snapshot["schema"] != "anysolver.e4-pl-s3-v2-stage4a-approval-snapshot-v2"
        or snapshot["candidate"]
        != {"commit": contract["candidate"]["commit"], "tree": contract["candidate"]["tree"]}
        or not isinstance(line, str)
        or "\n" in line
        or f"| {request_id} | APPROVED |" not in line
        or approved["sha256"] != sha256((line.rstrip() + "\n").encode("utf-8"))
        or ledger["path"] != str(RESOURCE_LEDGER_PATH)
        or ledger_byte_count != len(ledger_raw)
        or ledger_byte_count <= 0
        or ledger["sha256"] != sha256(ledger_raw)
        or request
        != {
            "byte_count": len(request_raw),
            "path": str(request_path),
            "request_id": request_id,
            "sha256": sha256(request_raw),
        }
    ):
        raise CoordinatorError("resource approval snapshot identity differs")
    try:
        preserved_lines = ledger_raw.decode("utf-8-sig").splitlines()
    except UnicodeError as exc:
        raise CoordinatorError("preserved pre-run ledger is not UTF-8") from exc
    if preserved_lines.count(line) != 1:
        raise CoordinatorError("preserved pre-run ledger approval row differs")
    return snapshot, raw


def validate_authorization(
    path: Path,
    *,
    contract_path: Path,
    contract_raw: bytes,
) -> tuple[Mapping[str, Any], bytes]:
    value, raw = strict_json_load(path)
    if raw != canonical_bytes(value):
        raise CoordinatorError("execution authorization is not canonical JSON")
    authorization = _exact(
        value,
        {
            "contract_path",
            "contract_sha256",
            "execution_paths",
            "formal_execution_authorized",
            "implementation_reviews",
            "ledger_approval",
            "resource_request",
            "resource_lock_required",
            "schema",
            "user_approval",
        },
        "$authorization",
    )
    contract = strict_json_bytes(contract_raw, str(contract_path))
    registered_contract_path = _repo_relative_path(
        authorization["contract_path"], "$.authorization.contract_path"
    )
    if (
        authorization["schema"] != AUTHORIZATION_SCHEMA
        or authorization["formal_execution_authorized"] is not True
        or authorization["resource_lock_required"] is not True
        or registered_contract_path != contract_path.resolve()
        or authorization["contract_sha256"] != sha256(contract_raw)
    ):
        raise CoordinatorError("execution authorization identity differs")
    user_approval = _exact(
        authorization["user_approval"], {"recorded", "source"}, "$.authorization.user_approval"
    )
    if (
        user_approval["recorded"] is not True
        or not isinstance(user_approval["source"], str)
        or not user_approval["source"]
    ):
        raise CoordinatorError("explicit user approval is not recorded")
    reviews = authorization["implementation_reviews"]
    if not isinstance(reviews, list) or len(reviews) != 2:
        raise CoordinatorError("two implementation reviews are required")
    expected_paths = {
        "PROCESS_AND_AUTHORITY": PROCESS_REVIEW_PATH.resolve(),
        "SCIENTIFIC_AND_MECHANICS": SCIENTIFIC_REVIEW_PATH.resolve(),
    }
    reviewer_ids: set[str] = set()
    observed_roles: list[str] = []
    expected_inputs = _review_inputs(contract, contract_raw)
    for index, review in enumerate(reviews):
        binding = _exact(
            review, {"path", "role", "sha256", "verdict"}, f"$.reviews[{index}]"
        )
        role = str(binding["role"])
        if role not in EXPECTED_REVIEW_VERDICTS or role in observed_roles:
            raise CoordinatorError("implementation review role is missing or duplicated")
        review_path = _repo_relative_path(binding["path"], f"$.reviews[{index}].path")
        if review_path != expected_paths[role]:
            raise CoordinatorError("implementation review path differs")
        review_value, review_raw = _validate_review(
            review_path, role=role, expected_inputs=expected_inputs
        )
        if (
            binding["sha256"] != sha256(review_raw)
            or binding["verdict"] != EXPECTED_REVIEW_VERDICTS[role]
        ):
            raise CoordinatorError("implementation review binding differs")
        reviewer_ids.add(review_value["reviewer_independence"]["reviewer_id"])
        observed_roles.append(role)
    if observed_roles != list(EXPECTED_REVIEW_VERDICTS) or len(reviewer_ids) != 2:
        raise CoordinatorError("implementation reviews are not distinct and ordered")
    request = _exact(
        authorization["resource_request"],
        {
            "command_sha256",
            "request_id",
            "request_path",
            "request_sha256",
            "repository",
            "task",
        },
        "$.authorization.resource_request",
    )
    request_path = Path(str(request["request_path"]))
    request_id = request["request_id"]
    if (
        not isinstance(request_id, str)
        or len(request_id) != 32
        or any(character not in "0123456789abcdef" for character in request_id)
        or request_path.resolve()
        != (RESOURCE_MANAGER_ROOT / "requests" / f"{request_id}.json").resolve()
        or not request_path.is_file()
        or request_path.is_symlink()
    ):
        raise CoordinatorError("resource request path is not an absolute file")
    request_value, request_raw = _strict_external_json(request_path, "resource request")
    request_value = _exact(
        request_value,
        {
            "command",
            "estimate_minutes",
            "repository",
            "request_id",
            "requested_at",
            "status",
            "task",
        },
        "$.resource_request_file",
    )
    execution_paths = _exact(
        authorization["execution_paths"],
        {"aggregate_path", "approval_snapshot_path", "output_root", "python_executable"},
        "$.authorization.execution_paths",
    )
    python_executable = Path(str(execution_paths["python_executable"])).resolve()
    output_root = Path(str(execution_paths["output_root"])).resolve()
    aggregate_path = Path(str(execution_paths["aggregate_path"])).resolve()
    approval_snapshot_path = Path(str(execution_paths["approval_snapshot_path"])).resolve()
    expected_command = expected_resource_command(
        python_executable=python_executable,
        contract_path=contract_path,
        authorization_path=path,
        output_root=output_root,
        aggregate_path=aggregate_path,
    )
    expected_task = "ANYsolver S3 V2A Stage 4A bounded mixed-flexural gate"
    if (
        not python_executable.is_file()
        or aggregate_path.parent != output_root
        or approval_snapshot_path.parent != output_root
        or request_value["request_id"] != request_id
        or request_value["status"] != "PENDING"
        or request_value["task"] != expected_task
        or request_value["repository"] != str(ROOT)
        or request_value["estimate_minutes"] != 30
        or request_value["command"] != expected_command
        or request["task"] != expected_task
        or request["repository"] != str(ROOT)
        or request["command_sha256"] != sha256(expected_command.encode("utf-8"))
        or request["request_sha256"] != sha256(request_raw)
    ):
        raise CoordinatorError("resource request content differs")
    approval = _exact(
        authorization["ledger_approval"],
        {"approved_row_sha256", "ledger_path", "snapshot_path", "snapshot_sha256"},
        "$.authorization.ledger_approval",
    )
    if approval["ledger_path"] != str(RESOURCE_LEDGER_PATH):
        raise CoordinatorError("resource ledger path differs")
    snapshot, snapshot_raw = _validate_approval_snapshot(
        approval_snapshot_path,
        contract=contract,
        request_id=request_id,
        request_path=request_path,
        request_raw=request_raw,
    )
    if (
        Path(str(approval["snapshot_path"])).resolve() != approval_snapshot_path
        or approval["snapshot_sha256"] != sha256(snapshot_raw)
        or approval["approved_row_sha256"] != snapshot["approved_row"]["sha256"]
    ):
        raise CoordinatorError("resource ledger approval binding differs")
    try:
        ledger_lines = RESOURCE_LEDGER_PATH.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CoordinatorError(f"cannot inspect resource ledger: {exc}") from exc
    if ledger_lines.count(snapshot["approved_row"]["line"]) != 1:
        raise CoordinatorError("registered APPROVED row is absent or duplicated")
    return authorization, raw


def validate_resource_execution_state(
    authorization: Mapping[str, Any], *, claim_attempt: bool = True
) -> None:
    request = authorization["resource_request"]
    request_id = str(request["request_id"])
    request_path = Path(str(request["request_path"]))
    request_value, _request_raw = _strict_external_json(request_path, "resource request")
    try:
        ledger_lines = RESOURCE_LEDGER_PATH.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CoordinatorError(f"cannot inspect live resource ledger: {exc}") from exc
    matching = [line for line in ledger_lines if f"| {request_id} |" in line]
    statuses = [
        fields[3].strip()
        for line in matching
        if len(fields := line.split("|")) > 3
    ]
    if statuses.count("APPROVED") != 1:
        raise CoordinatorError("resource request lacks one APPROVED ledger row")
    if statuses.count("EXECUTION_STARTED") != 1:
        raise CoordinatorError("resource request lacks one EXECUTION_STARTED row")
    if len(statuses) != 2 or set(statuses) != {"APPROVED", "EXECUTION_STARTED"}:
        raise CoordinatorError("resource request was already consumed")
    if not RESOURCE_LOCK_OWNER_PATH.is_file():
        raise CoordinatorError("global resource lock is not held")
    owner, _owner_raw = _strict_external_json(RESOURCE_LOCK_OWNER_PATH, "resource lock owner")
    owner = _exact(
        owner,
        {"acquired_at", "command", "process_id", "repository", "request_id", "task"},
        "$.resource_lock_owner",
    )
    if (
        owner["request_id"] != request_id
        or owner["command"] != request_value["command"]
        or owner["repository"] != request_value["repository"]
        or owner["task"] != request_value["task"]
        or _nonnegative_integer(owner["process_id"], "$.resource_lock_owner.process_id") <= 0
    ):
        raise CoordinatorError("global resource lock owner differs")
    attempt_path = RESOURCE_MANAGER_ROOT / "attempts" / f"{request_id}.json"
    attempt = {
        "contract_sha256": authorization["contract_sha256"],
        "request_id": request_id,
        "schema": "anysolver.resource-attempt-claim-v1",
    }
    if claim_attempt:
        _write_exclusive(attempt_path, canonical_bytes(attempt))
    else:
        value, raw = strict_json_load(attempt_path)
        if raw != canonical_bytes(value) or value != attempt:
            raise CoordinatorError("resource attempt claim differs at finalization")


def _write_exclusive(
    path: Path, raw: bytes, *, deadline_exempt: bool = False
) -> None:
    """Stage, fsync, and atomically publish without exposing partial bytes."""

    if not deadline_exempt:
        guard = _ACTIVE_COORDINATOR_GUARD
        if guard is not None:
            guard.require_canonical_publication_is_safe(path)
        _coordinator_checkpoint()
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise CoordinatorError(f"refusing to overwrite canonical output: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.pending-",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if not deadline_exempt:
            guard = _ACTIVE_COORDINATOR_GUARD
            if guard is not None:
                guard.require_canonical_publication_is_safe(path)
            _coordinator_checkpoint()
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise CoordinatorError(
                f"refusing to overwrite canonical output: {path}"
            ) from exc
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def _publish_candidate_archive(path: Path, commit: str) -> None:
    _coordinator_checkpoint()
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise CoordinatorError("candidate source archive output already exists")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.pending-",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            _git_run("archive", "--format=tar", commit, stdout=stream)
            stream.flush()
            os.fsync(stream.fileno())
        _coordinator_checkpoint()
        if temporary.stat().st_size <= 0:
            raise CoordinatorError("candidate source archive is empty")
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise CoordinatorError("candidate source archive output already exists") from exc
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def _extract_candidate_archive(archive_path: Path, output_root: Path) -> Path:
    """Safely extract the exact Git archive into one fresh external tree."""

    _coordinator_checkpoint()
    candidate_root = (output_root / "candidate-source-tree").resolve()
    if os.path.lexists(candidate_root):
        raise CoordinatorError("candidate source tree output already exists")
    # Python 3.13 gives ``tempfile.mkdtemp`` a private Windows ACL.  The exact
    # source tree must remain readable by the separately contained producer
    # children, so create an exclusive ordinary directory that inherits the
    # already validated output-root ACL instead.
    staging: Path | None = None
    for _attempt in range(32):
        candidate = (
            output_root / f".candidate-source-tree.pending-{secrets.token_hex(12)}"
        ).resolve()
        try:
            candidate.relative_to(output_root.resolve())
            candidate.mkdir()
        except FileExistsError:
            continue
        staging = candidate
        break
    if staging is None:
        raise CoordinatorError("cannot create exclusive candidate staging directory")
    seen: set[str] = set()
    try:
        with tarfile.open(archive_path, mode="r:") as bundle:
            for member in bundle.getmembers():
                _coordinator_checkpoint()
                raw_name = member.name.rstrip("/")
                if not raw_name:
                    continue
                pure = PurePosixPath(raw_name)
                if pure.is_absolute() or any(
                    part in {"", ".", ".."} for part in pure.parts
                ):
                    raise CoordinatorError("candidate archive contains an unsafe path")
                folded = pure.as_posix().casefold()
                if folded in seen:
                    raise CoordinatorError("candidate archive path is duplicated")
                seen.add(folded)
                target = staging.joinpath(*pure.parts).resolve()
                try:
                    target.relative_to(staging)
                except ValueError as exc:
                    raise CoordinatorError(
                        "candidate archive path escapes its extraction root"
                    ) from exc
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=False)
                    continue
                if not member.isfile():
                    raise CoordinatorError(
                        "candidate archive contains a link or special entry"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                source = bundle.extractfile(member)
                if source is None:
                    raise CoordinatorError("candidate archive member cannot be read")
                with target.open("xb") as destination:
                    shutil.copyfileobj(source, destination)
                    destination.flush()
                    os.fsync(destination.fileno())
                _coordinator_checkpoint()
        if not (staging / "src" / "anysolver" / "__init__.py").is_file():
            raise CoordinatorError("candidate archive lacks the ANYsolver source tree")
        os.rename(staging, candidate_root)
        _coordinator_checkpoint()
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return candidate_root


def _producer_result_path(manifest_path: Path) -> Path:
    """Return a canonical producer result contained by the registered wave root."""

    manifest, raw = strict_json_load(manifest_path)
    if raw != canonical_bytes(manifest):
        raise CoordinatorError("producer wave manifest is not canonical JSON")
    manifest = _exact(
        manifest,
        {"lane", "output_root", "schema", "wave_id", "workers"},
        "$.producer_wave_manifest",
    )
    raw_root = manifest["output_root"]
    if not isinstance(raw_root, str) or not Path(raw_root).is_absolute():
        raise CoordinatorError("producer wave output root is not absolute")
    wave_root = Path(raw_root).resolve()
    result_path = (wave_root / "producer-wave-result.json").resolve()
    try:
        result_path.relative_to(wave_root)
    except ValueError as exc:
        raise CoordinatorError("producer wave result escapes its registered root") from exc
    return result_path


def _write_process_incident(
    path: Path,
    *,
    authorization_sha256: str,
    contract_sha256: str,
    error: BaseException,
    phase: str,
    producer_result_path: Path | None,
) -> None:
    """Preserve deterministic diagnostics without changing adjudication evidence."""

    producer_digest = None
    if producer_result_path is not None and producer_result_path.is_file():
        producer_digest = sha256(producer_result_path.read_bytes())
    message = str(error)
    replacements = (
        (path.parent.resolve(), "<OUTPUT_ROOT>"),
        (ROOT.resolve(), "<REPOSITORY_ROOT>"),
        (RESOURCE_MANAGER_ROOT.resolve(), "<RESOURCE_MANAGER_ROOT>"),
    )
    for registered_path, replacement in replacements:
        message = re.sub(
            re.escape(str(registered_path)), replacement, message, flags=re.IGNORECASE
        )
    message = re.sub(
        r"\.candidate-source-tree\.pending-[0-9a-f]{24}",
        ".candidate-source-tree.pending-<TOKEN>",
        message,
        flags=re.IGNORECASE,
    )
    if len(message) > 2_048:
        message = message[:2_048]
    incident = {
        "authorization_sha256": authorization_sha256,
        "contract_sha256": contract_sha256,
        "errno": getattr(error, "errno", None),
        "exception_message": message,
        "exception_type": f"{type(error).__module__}.{type(error).__qualname__}",
        "phase": phase,
        "producer_result_sha256": producer_digest,
        "schema": "anysolver.e4-pl-s3-v2-stage4a-process-incident-v1",
        "winerror": getattr(error, "winerror", None),
    }
    _write_exclusive(path, canonical_bytes(incident))


def prepare_wave(
    contract_path: Path,
    output_root: Path,
    *,
    authorization_path: Path | None = None,
) -> dict[str, Path]:
    _coordinator_checkpoint()
    contract, contract_raw = validate_contract(contract_path)
    _coordinator_checkpoint()
    if authorization_path is not None:
        validate_authorization(
            authorization_path,
            contract_path=contract_path,
            contract_raw=contract_raw,
        )
    _coordinator_checkpoint()
    funnel = _load_module("_s3_v2_stage4a_funnel", FUNNEL_PATH)
    manifest_value, manifest_raw = funnel.strict_json_load(MANIFEST_PATH)
    records = funnel.validate_manifest(manifest_value, manifest_raw)
    plan = funnel.build_phase_plan(records, "4A")
    _coordinator_checkpoint()
    plan_path = (output_root / "phase4a-plan.json").resolve()
    _write_exclusive(plan_path, funnel.canonical_bytes(plan))
    candidate = contract["candidate"]
    archive_path = (output_root / "candidate-source.tar").resolve()
    _publish_candidate_archive(archive_path, str(candidate["commit"]))
    archive_sha256 = sha256(archive_path.read_bytes())
    _coordinator_checkpoint()
    candidate_source_root = _extract_candidate_archive(archive_path, output_root)
    binding = {
        "artifact_path": str(archive_path),
        "artifact_sha256": archive_sha256,
        "candidate_id": "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1",
        "commit": candidate["commit"],
        "formulation_id": "E4_PL_QUALIFIED_S3_COMPANION_V2",
        "schema": "anysolver.e4-pl-s3-v2-flat-candidate-binding-v1",
        "selector": "e4-pl-s3-v2",
        "tree": candidate["tree"],
    }
    binding_path = (output_root / "candidate-source-binding.json").resolve()
    _write_exclusive(binding_path, canonical_bytes(binding))
    _coordinator_checkpoint()
    wave_manifest = funnel.build_bounded_wave_manifest(
        plan,
        plan_path=plan_path,
        producer_program=PRODUCER_PATH,
        python_executable=Path(sys.executable).resolve(),
        cwd=ROOT,
        output_root=(output_root / "producer-wave").resolve(),
        input_paths={
            "candidate_artifact": binding_path,
            "connectivity_manifest": MANIFEST_PATH,
            "flat_funnel_contract": SCAFFOLD_CONTRACT_PATH,
            "source_equation_contract": SOURCE_CONTRACT_PATH,
        },
    )
    extra_inputs = [contract_path.resolve(), AUTHORITY_PATH.resolve()]
    if authorization_path is not None:
        extra_inputs.append(authorization_path.resolve())
    for worker in wave_manifest["workers"]:
        worker["input_hashes"] = list(worker["input_hashes"])
        worker["command"].extend(
            [
                "--candidate-source-root",
                str(candidate_source_root),
                "--candidate-archive",
                str(archive_path),
                "--candidate-archive-sha256",
                archive_sha256,
            ]
        )
    for worker in wave_manifest["workers"]:
        for path in extra_inputs:
            worker["input_hashes"].append(
                {"path": str(path), "sha256": sha256(path.read_bytes())}
            )
        worker["input_hashes"].sort(key=lambda item: item["path"])
        _coordinator_checkpoint()
    wave_manifest_path = (output_root / "producer-wave-manifest.json").resolve()
    _write_exclusive(wave_manifest_path, canonical_bytes(wave_manifest))
    _coordinator_checkpoint()
    return {
        "archive": archive_path,
        "binding": binding_path,
        "candidate_source_root": candidate_source_root,
        "plan": plan_path,
        "producer_manifest": wave_manifest_path,
    }


def _run_checker_process(
    *,
    assignment_id: str,
    proof: Path,
    plan: Path,
    output: Path,
    stdout_path: Path,
    stderr_path: Path,
    deadline: float,
) -> dict[str, Any]:
    bounded = _load_module(
        f"_s3_v2_checker_bounded_{assignment_id}_{output.parent.name}",
        BOUNDED_PATH,
    )
    for path in (output, stdout_path, stderr_path):
        if path.exists():
            raise CoordinatorError(f"checker output is not exclusive: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    stdout = stdout_path.open("xb")
    stderr = stderr_path.open("xb")
    job = bounded._ProcessJob(MEMORY_LIMIT_BYTES)
    command = [
        str(Path(sys.executable).resolve()),
        str(CHECKER_PATH.resolve()),
        "--verify-proof",
        "--proof",
        str(proof.resolve()),
        "--plan",
        str(plan.resolve()),
        "--output",
        str(output.resolve()),
    ]
    started = time.monotonic()
    last_cpu = 0
    last_activity = started
    termination_proven = False
    slot_released = False
    peak = 0
    process: Any = None
    try:
        process = job.launch(
            command,
            cwd=ROOT,
            env=bounded._environment(),
            stdout=stdout,
            stderr=stderr,
        )
        while True:
            now = time.monotonic()
            cpu, active, peak = job.accounting()
            if cpu > last_cpu:
                last_cpu = cpu
                last_activity = now
            returncode = process.poll()
            if returncode is not None:
                if active == 0:
                    termination_proven = True
                    slot_released = True
                    if returncode != 0:
                        raise CoordinatorError(
                            f"checker process failed: {assignment_id}"
                        )
                    break
                raise CoordinatorError(
                    "checker root exited before its Job tree drained: "
                    f"{assignment_id} active={active}"
                )
            if now >= min(deadline, started + CHECKER_WALL_SECONDS) or now - last_activity >= 300:
                raise CoordinatorError(f"checker process exceeded its bound: {assignment_id}")
            time.sleep(0.05)
    except BaseException as exc:
        if not slot_released:
            try:
                termination_proven = bool(job.terminate())
            except BaseException:
                termination_proven = False
            slot_released = termination_proven
        if not slot_released:
            raise _CheckerTreeNotDrained(
                "checker Job termination could not prove an empty process tree: "
                f"{assignment_id}"
            ) from exc
        raise
    finally:
        cleanup_error: BaseException | None = None
        for stream in (stdout, stderr):
            try:
                stream.close()
            except BaseException as exc:
                if cleanup_error is None:
                    cleanup_error = exc
        try:
            job.close()
        except BaseException as exc:
            if cleanup_error is None:
                cleanup_error = exc
        if cleanup_error is not None:
            if not slot_released:
                raise _CheckerTreeNotDrained(
                    "checker cleanup failed before its process tree was proven empty: "
                    f"{assignment_id}"
                ) from cleanup_error
            raise CoordinatorError(
                f"checker cleanup failed: {assignment_id}"
            ) from cleanup_error
    value, raw = strict_json_load(output)
    if raw != canonical_bytes(value) or value.get("schema") != CHECKER_RESULT_SCHEMA:
        raise CoordinatorError("checker output is malformed or noncanonical")
    return {
        "assignment_id": assignment_id,
        "cpu_100ns": last_cpu,
        "output_path": str(output.resolve()),
        "output_sha256": sha256(raw),
        "peak_tree_memory_bytes": peak,
        "proof_path": str(proof.resolve()),
        "proof_sha256": sha256(proof.read_bytes()),
        "stderr_sha256": sha256(stderr_path.read_bytes()),
        "stdout_sha256": sha256(stdout_path.read_bytes()),
        "termination_proven": termination_proven,
        "value": value,
    }


def _checker_replica_required_memory_bytes() -> int:
    """Return the admission floor for one two-at-a-time checker replica."""

    return MAXIMUM_CONCURRENT_WORKERS * MEMORY_LIMIT_BYTES + OS_HEADROOM_BYTES


def _require_checker_phase_admission(bounded: Any, deadline: float) -> None:
    """Fail closed before any checker path or process is launched."""

    available = bounded.available_physical_memory_bytes()
    if isinstance(available, bool) or not isinstance(available, int) or available < 0:
        raise CoordinatorError("checker phase available-memory value is invalid")
    required = _checker_replica_required_memory_bytes()
    if available < required:
        raise CoordinatorError(
            "checker phase resources are deferred: "
            f"available={available} required={required}"
        )
    remaining = deadline - time.monotonic()
    if remaining < CHECKER_PHASE_REQUIRED_SECONDS:
        raise CoordinatorError(
            "checker phase has insufficient coordinator-wall budget: "
            f"remaining={remaining:.6f} required={CHECKER_PHASE_REQUIRED_SECONDS}"
        )


def _run_checker_phase(
    *,
    bounded: Any,
    proofs: Mapping[str, Path],
    plan: Path,
    output_root: Path,
    deadline: float,
    wall_guard: _CoordinatorWallGuard | None = None,
) -> list[list[dict[str, Any]]]:
    """Run all six checkers as three frozen-order replica pairs."""

    if set(proofs) != set(EXPECTED_SHARDS):
        raise CoordinatorError("checker phase proof coverage differs")
    _require_checker_phase_admission(bounded, deadline)
    if wall_guard is not None:
        wall_guard.mark_process_phase_active()
    results: dict[int, list[dict[str, Any]]] = {1: [], 2: []}
    first_error: Exception | None = None
    queue_blocked = False
    with ThreadPoolExecutor(max_workers=MAXIMUM_CONCURRENT_WORKERS) as pool:
        for assignment_id in EXPECTED_SHARDS:
            if queue_blocked:
                break
            proof = proofs[assignment_id]
            pair: list[tuple[int, Any]] = []
            for replica_index in (1, 2):
                root = output_root / f"checker-replica-{replica_index}" / assignment_id
                pair.append(
                    (
                        replica_index,
                        pool.submit(
                            _run_checker_process,
                            assignment_id=assignment_id,
                            proof=proof,
                            plan=plan,
                            output=root / "checker.json",
                            stdout_path=root / "stdout.log",
                            stderr_path=root / "stderr.log",
                            deadline=deadline,
                        ),
                    )
                )
            pair_tree_not_drained = False
            for replica_index, task in pair:
                try:
                    result = task.result()
                except _CheckerTreeNotDrained as exc:
                    pair_tree_not_drained = True
                    if first_error is None:
                        first_error = exc
                except Exception as exc:
                    if first_error is None:
                        first_error = exc
                else:
                    results[replica_index].append(result)
            queue_blocked = pair_tree_not_drained
    if first_error is not None:
        disposition = (
            "checker queue blocked because a Job tree did not drain"
            if queue_blocked
            else "all six registered tasks reached terminal state"
        )
        if wall_guard is not None:
            wall_guard.mark_process_phase_terminal(proven=not queue_blocked)
        raise _CheckerPhaseError(
            f"checker phase failed after {disposition}",
            trees_proven_terminal=not queue_blocked,
        ) from first_error
    replicas = [results[1], results[2]]
    if wall_guard is not None:
        wall_guard.mark_process_phase_terminal(
            proven=all(
                result.get("termination_proven") is True
                for replica in replicas
                for result in replica
            )
        )
    return replicas


def validate_producer_proofs(
    manifest: Mapping[str, Any],
    manifest_raw: bytes,
    producer_result: Mapping[str, Any],
    producer_result_raw: bytes,
) -> dict[str, dict[str, Any]]:
    """Join each completed worker result to its exact proof and assignment."""

    if producer_result_raw != canonical_bytes(producer_result):
        raise CoordinatorError("producer wave result is not canonical JSON")
    result = _exact(
        producer_result,
        {"lane", "manifest_sha256", "schema", "terminal", "wave_id", "workers"},
        "$.producer_result",
    )
    if (
        result["schema"] != PRODUCER_RESULT_SCHEMA
        or result["terminal"] != "COMPLETED"
        or result["manifest_sha256"] != sha256(manifest_raw)
        or not isinstance(result["workers"], list)
        or len(result["workers"]) != 3
    ):
        raise CoordinatorError("producer wave result identity differs")
    manifest_workers = manifest.get("workers")
    if not isinstance(manifest_workers, list) or len(manifest_workers) != 3:
        raise CoordinatorError("producer wave manifest coverage differs")
    by_manifest = {
        str(worker.get("assignment_id")): worker for worker in manifest_workers
    }
    by_result = {
        str(worker.get("assignment_id")): worker for worker in result["workers"]
        if isinstance(worker, dict)
    }
    if (
        set(by_manifest) != set(EXPECTED_SHARDS)
        or set(by_result) != set(EXPECTED_SHARDS)
        or len(by_manifest) != 3
        or len(by_result) != 3
    ):
        raise CoordinatorError("producer assignment coverage differs")
    worker_keys = {
        "assignment_id",
        "assignment_sha256",
        "cpu_100ns",
        "input_hashes",
        "last_progress_sequence",
        "peak_tree_memory_bytes",
        "plan_sha256",
        "program_sha256",
        "returncode",
        "scientific_byte_count",
        "scientific_payload_sha256",
        "scientific_record_count",
        "scientific_record_ids_sha256",
        "scientific_schema",
        "scientific_sha256",
        "scientific_terminal",
        "status",
        "stderr_sha256",
        "stdout_sha256",
        "termination_proven",
    }
    made: dict[str, dict[str, Any]] = {}
    for assignment_id in EXPECTED_SHARDS:
        registered = by_manifest[assignment_id]
        completed = _exact(
            by_result[assignment_id],
            worker_keys,
            f"$.producer_result.workers[{assignment_id}]",
        )
        proof_path = Path(str(registered.get("scientific_path"))).resolve()
        proof_sha256 = _digest(
            completed["scientific_sha256"],
            f"$.producer_result.workers[{assignment_id}].scientific_sha256",
        )
        if (
            completed["status"] != "COMPLETED"
            or completed["returncode"] != 0
            or completed["termination_proven"] is not True
            or completed["assignment_sha256"] != registered.get("assignment_sha256")
            or completed["plan_sha256"] != registered.get("plan_sha256")
            or not proof_path.is_file()
            or proof_path.is_symlink()
            or sha256(proof_path.read_bytes()) != proof_sha256
        ):
            raise CoordinatorError("producer proof binding differs")
        made[assignment_id] = {
            "assignment_sha256": completed["assignment_sha256"],
            "plan_sha256": completed["plan_sha256"],
            "proof_path": str(proof_path),
            "proof_sha256": proof_sha256,
        }
    return made


def aggregate_checker_results(
    replica_results: Sequence[Sequence[Mapping[str, Any]]],
    *,
    producer_proofs: Mapping[str, Mapping[str, Any]],
    producer_result_sha256: str,
    contract_sha256: str,
    authorization_sha256: str,
) -> dict[str, Any]:
    _digest(producer_result_sha256, "$.producer_result_sha256")
    _digest(contract_sha256, "$.contract_sha256")
    _digest(authorization_sha256, "$.authorization_sha256")
    if set(producer_proofs) != set(EXPECTED_SHARDS):
        raise CoordinatorError("producer proof binding coverage differs")
    for assignment_id, proof in producer_proofs.items():
        _exact(
            proof,
            {"assignment_sha256", "plan_sha256", "proof_path", "proof_sha256"},
            f"$.producer_proofs[{assignment_id}]",
        )
        _digest(proof["assignment_sha256"], "$.producer_proof.assignment_sha256")
        _digest(proof["plan_sha256"], "$.producer_proof.plan_sha256")
        _digest(proof["proof_sha256"], "$.producer_proof.proof_sha256")
    if len(replica_results) != 2 or any(len(replica) != 3 for replica in replica_results):
        raise CoordinatorError("exactly two complete three-shard checker replicas are required")
    by_replica = [
        {str(item["assignment_id"]): item for item in replica}
        for replica in replica_results
    ]
    expected_assignments = set(EXPECTED_SHARDS)
    if (
        set(by_replica[0]) != expected_assignments
        or set(by_replica[1]) != expected_assignments
        or any(
            len(replica) != len(mapping)
            for replica, mapping in zip(replica_results, by_replica)
        )
    ):
        raise CoordinatorError("checker replica assignment coverage differs")
    accepted: list[Mapping[str, Any]] = []
    for assignment_id in EXPECTED_SHARDS:
        first = by_replica[0][assignment_id]
        second = by_replica[1][assignment_id]
        first_value, first_raw = _validate_checker_result(
            first,
            expected_assignment_id=assignment_id,
            expected_proof=producer_proofs[assignment_id],
        )
        _second_value, second_raw = _validate_checker_result(
            second,
            expected_assignment_id=assignment_id,
            expected_proof=producer_proofs[assignment_id],
        )
        if first_raw != second_raw:
            raise CoordinatorError(f"checker replicas disagree: {assignment_id}")
        accepted.append(first_value)
    terminals = {str(value["terminal"]) for value in accepted}
    if not terminals <= {PASS, NO_GO}:
        raise CoordinatorError("checker result contains an unregistered terminal")
    terminal = NO_GO if NO_GO in terminals else PASS
    failures = sorted(
        f"{value['diagonal']}:{failure}"
        for value in accepted
        for failure in value["formal_failures"]
    )
    if (terminal == NO_GO) != bool(failures):
        raise CoordinatorError("checker terminal and formal failures disagree")
    advisory = any(bool(value["advisory_review_required"]) for value in accepted)
    sequences = []
    by_diagonal = {str(value["diagonal"]): value for value in accepted}
    for diagonal in DIAGONAL_ORDER:
        value = by_diagonal[diagonal]
        by_coordinate = {
            (str(sequence["mask"]), int(sequence["fraction_percent"])): sequence
            for sequence in value["sequence_results"]
        }
        for mask in MASK_ORDER:
            for fraction in FRACTION_ORDER:
                sequences.append(
                    {
                        "diagonal": diagonal,
                        **by_coordinate[(mask, fraction)],
                    }
                )
    if len(sequences) != 24:
        raise CoordinatorError("aggregate sequence coverage is not exactly 24")
    classifying_count = sum(int(value["classifying_record_count"]) for value in accepted)
    v1_count = sum(int(value["v1_diagnostic_record_count"]) for value in accepted)
    if classifying_count != 81 or v1_count != 72:
        raise CoordinatorError("aggregate checker record coverage differs")
    checker_bindings = []
    for assignment_id in EXPECTED_SHARDS:
        first = by_replica[0][assignment_id]
        second = by_replica[1][assignment_id]
        proof = producer_proofs[assignment_id]
        checker_bindings.append(
            {
                "assignment_id": assignment_id,
                "assignment_sha256": proof["assignment_sha256"],
                "checker_output_sha256": [
                    first["output_sha256"],
                    second["output_sha256"],
                ],
                "checker_stderr_sha256": [
                    first["stderr_sha256"],
                    second["stderr_sha256"],
                ],
                "checker_stdout_sha256": [
                    first["stdout_sha256"],
                    second["stdout_sha256"],
                ],
                "plan_sha256": proof["plan_sha256"],
                "proof_sha256": proof["proof_sha256"],
            }
        )
    return {
        "advisory_review_required": bool(advisory and terminal == PASS),
        "authorization_sha256": authorization_sha256,
        "classifying_record_count": classifying_count,
        "checker_replica_bindings": checker_bindings,
        "contract_sha256": contract_sha256,
        "formal_failures": failures,
        "production_restriction": PRODUCTION_RESTRICTION,
        "producer_wave_result_sha256": producer_result_sha256,
        "schema": AGGREGATE_SCHEMA,
        "sequence_results": sequences,
        "successor_expansion_authorized": bool(
            terminal == PASS and not advisory
        ),
        "terminal": terminal,
        "v1_diagnostic_record_count": v1_count,
    }


def blocked_aggregate(
    *,
    authorization_sha256: str,
    contract_sha256: str,
    producer_result_sha256: str | None,
    reason: str,
) -> dict[str, Any]:
    _digest(authorization_sha256, "$.authorization_sha256")
    _digest(contract_sha256, "$.contract_sha256")
    if producer_result_sha256 is not None:
        _digest(producer_result_sha256, "$.producer_result_sha256")
    if reason not in {
        "CHECKER_WAVE_FAILED",
        "COORDINATOR_WALL_EXCEEDED",
        "FORMAL_PROCESS_FAILED",
        "PRODUCER_WAVE_NOT_COMPLETED",
    }:
        raise CoordinatorError("unregistered blocked reason")
    return {
        "advisory_review_required": False,
        "authorization_sha256": authorization_sha256,
        "classifying_record_count": 0,
        "checker_replica_bindings": [],
        "contract_sha256": contract_sha256,
        "formal_failures": [reason],
        "production_restriction": PRODUCTION_RESTRICTION,
        "producer_wave_result_sha256": producer_result_sha256,
        "schema": AGGREGATE_SCHEMA,
        "sequence_results": [],
        "successor_expansion_authorized": False,
        "terminal": BLOCKED,
        "v1_diagnostic_record_count": 0,
    }


def _producer_process_trees_proven_terminal(result: Mapping[str, Any]) -> bool:
    workers = result.get("workers")
    if result.get("terminal") == "RESOURCE_DEFERRED" and workers == []:
        return True
    return bool(
        isinstance(workers, list)
        and workers
        and all(
            isinstance(worker, dict) and worker.get("termination_proven") is True
            for worker in workers
        )
    )


def _run_stage4a_guarded(
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    aggregate_path: Path,
    wall_guard: _CoordinatorWallGuard,
) -> dict[str, Any]:
    _coordinator_checkpoint()
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise CoordinatorError("formal Stage 4A requires the registered -I -B launcher")
    _contract, contract_raw = validate_contract(contract_path)
    _coordinator_checkpoint()
    authorization, authorization_raw = validate_authorization(
        authorization_path,
        contract_path=contract_path,
        contract_raw=contract_raw,
    )
    execution_paths = authorization["execution_paths"]
    if (
        Path(str(execution_paths["output_root"])).resolve() != output_root.resolve()
        or Path(str(execution_paths["aggregate_path"])).resolve() != aggregate_path.resolve()
        or Path(str(execution_paths["python_executable"])).resolve()
        != Path(sys.executable).resolve()
    ):
        raise CoordinatorError("live Stage 4A invocation differs from the resource request")
    validate_resource_execution_state(authorization)
    authorization_digest = sha256(authorization_raw)
    contract_digest = sha256(contract_raw)
    wall_guard.bind_evidence(
        authorization_sha256=authorization_digest,
        contract_sha256=contract_digest,
    )
    producer_result_path: Path | None = None
    process_phase = "PREPARE_WAVE"
    try:
        paths = prepare_wave(
            contract_path,
            output_root,
            authorization_path=authorization_path,
        )
        process_phase = "PRODUCER_RESULT_REGISTRATION"
        producer_result_path = _producer_result_path(paths["producer_manifest"])
        wall_guard.bind_producer_result(producer_result_path)
        process_phase = "LOAD_BOUNDED_RUNNER"
        bounded = _load_module("_s3_v2_stage4a_bounded", BOUNDED_PATH)
        process_phase = "PRODUCER_WAVE"
        wall_guard.mark_process_phase_active()
        producer_result = bounded.run_wave(
            paths["producer_manifest"], producer_result_path
        )
        wall_guard.mark_process_phase_terminal(
            proven=_producer_process_trees_proven_terminal(producer_result)
        )
    except _CoordinatorWallExceeded:
        raise
    except Exception as exc:
        producer_digest = (
            sha256(producer_result_path.read_bytes())
            if producer_result_path is not None and producer_result_path.is_file()
            else None
        )
        try:
            _write_process_incident(
                (output_root / "stage4a-process-incident.json").resolve(),
                authorization_sha256=authorization_digest,
                contract_sha256=contract_digest,
                error=exc,
                phase=process_phase,
                producer_result_path=producer_result_path,
            )
        except Exception:
            pass
        blocked = blocked_aggregate(
            authorization_sha256=authorization_digest,
            contract_sha256=contract_digest,
            producer_result_sha256=producer_digest,
            reason="FORMAL_PROCESS_FAILED",
        )
        _write_exclusive(aggregate_path, canonical_bytes(blocked))
        return blocked
    assert producer_result_path is not None
    if producer_result.get("terminal") != "COMPLETED":
        blocked = blocked_aggregate(
            authorization_sha256=authorization_digest,
            contract_sha256=contract_digest,
            producer_result_sha256=sha256(producer_result_path.read_bytes()),
            reason="PRODUCER_WAVE_NOT_COMPLETED",
        )
        _write_exclusive(aggregate_path, canonical_bytes(blocked))
        return blocked
    deadline = wall_guard.work_deadline
    replicas: list[list[dict[str, Any]]] = []
    try:
        manifest, raw_manifest = strict_json_load(paths["producer_manifest"])
        stored_producer_result, producer_result_raw = strict_json_load(
            producer_result_path
        )
        if stored_producer_result != producer_result:
            raise CoordinatorError("producer result changed after bounded execution")
        producer_proofs = validate_producer_proofs(
            manifest,
            raw_manifest,
            stored_producer_result,
            producer_result_raw,
        )
        proofs = {
            assignment_id: Path(str(binding["proof_path"]))
            for assignment_id, binding in producer_proofs.items()
        }
        if set(proofs) != set(EXPECTED_SHARDS):
            raise CoordinatorError("producer manifest does not expose three exact proofs")
        replicas = _run_checker_phase(
            bounded=bounded,
            proofs=proofs,
            plan=paths["plan"],
            output_root=output_root,
            deadline=deadline,
            wall_guard=wall_guard,
        )
        _coordinator_checkpoint()
        _final_contract, final_contract_raw = validate_contract(contract_path)
        _coordinator_checkpoint()
        final_authorization, final_authorization_raw = validate_authorization(
            authorization_path,
            contract_path=contract_path,
            contract_raw=final_contract_raw,
        )
        if final_contract_raw != contract_raw or final_authorization_raw != authorization_raw:
            raise CoordinatorError("formal authority changed during execution")
        validate_resource_execution_state(final_authorization, claim_attempt=False)
        _coordinator_checkpoint()
        aggregate = aggregate_checker_results(
            replicas,
            producer_proofs=producer_proofs,
            producer_result_sha256=sha256(producer_result_path.read_bytes()),
            contract_sha256=contract_digest,
            authorization_sha256=authorization_digest,
        )
        _coordinator_checkpoint()
    except _CoordinatorWallExceeded:
        raise
    except Exception:
        aggregate = blocked_aggregate(
            authorization_sha256=authorization_digest,
            contract_sha256=contract_digest,
            producer_result_sha256=sha256(producer_result_path.read_bytes()),
            reason="CHECKER_WAVE_FAILED",
        )
    _write_exclusive(aggregate_path, canonical_bytes(aggregate))
    return aggregate


def run_stage4a(
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    aggregate_path: Path,
) -> dict[str, Any]:
    """Run Stage 4A under one fail-closed coordinator-wide hard wall."""

    global _ACTIVE_COORDINATOR_GUARD
    if _ACTIVE_COORDINATOR_GUARD is not None:
        raise CoordinatorError("a coordinator wall guard is already active")
    guard = _CoordinatorWallGuard(
        aggregate_path=aggregate_path,
        started=time.monotonic(),
    )
    _ACTIVE_COORDINATOR_GUARD = guard
    try:
        guard.start()
        try:
            return _run_stage4a_guarded(
                contract_path,
                authorization_path,
                output_root,
                aggregate_path,
                guard,
            )
        except _CoordinatorWallExceeded as exc:
            aggregate = guard.publish_fail_closed()
            if aggregate is None:
                raise CoordinatorError(
                    "coordinator wall elapsed before canonical failure hashes were bound"
                ) from exc
            return aggregate
    finally:
        _ACTIVE_COORDINATOR_GUARD = None
        guard.close()


def run_prepare_stage4a(contract_path: Path, output_root: Path) -> dict[str, Path]:
    """Apply the same no-forever wall to the non-executing preparation mode."""

    global _ACTIVE_COORDINATOR_GUARD
    if _ACTIVE_COORDINATOR_GUARD is not None:
        raise CoordinatorError("a coordinator wall guard is already active")
    guard = _CoordinatorWallGuard(
        aggregate_path=(output_root / "stage4a-prepare-timeout.json").resolve(),
        started=time.monotonic(),
    )
    _ACTIVE_COORDINATOR_GUARD = guard
    try:
        guard.start()
        try:
            return prepare_wave(contract_path, output_root)
        except _CoordinatorWallExceeded as exc:
            raise CoordinatorError(
                "Stage 4A preparation exceeded its coordinator wall"
            ) from exc
    finally:
        _ACTIVE_COORDINATOR_GUARD = None
        guard.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--run-stage4a", action="store_true")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--aggregate", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    contract = args.contract.resolve()
    output_root = args.output_root.resolve()
    if args.prepare_only:
        if args.authorization is not None or args.aggregate is not None:
            raise CoordinatorError("prepare-only does not accept execution outputs")
        run_prepare_stage4a(contract, output_root)
        return 0
    if args.authorization is None or args.aggregate is None:
        raise CoordinatorError("formal execution requires authorization and aggregate")
    aggregate = run_stage4a(
        contract,
        args.authorization.resolve(),
        output_root,
        args.aggregate.resolve(),
    )
    return 0 if aggregate["terminal"] in {PASS, NO_GO} else 2


if __name__ == "__main__":
    raise SystemExit(main())
