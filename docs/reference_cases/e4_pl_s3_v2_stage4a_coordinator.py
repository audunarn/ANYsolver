"""Bounded coordinator for the formal S3 V2A Stage-4A funnel.

The coordinator validates the frozen Git candidate before numerical imports,
creates an exact source archive and 81 content-addressed V2 leaves, executes
them as 40 bounded pairs plus one singleton, and joins all 41 terminal
receipts.  It then reconstructs the three diagonal checker inputs and runs two
independent checker replicas per input.  Legacy monolithic and live V1 routes
fail closed.  A canonical aggregate is published only after every launched
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
LEAF_WAVE_AUTHORIZATION_PATH = (
    REFERENCE_CASES / "e4_pl_s3_v2_stage4a_leaf_wave_authorization.json"
)
EXECUTION_AUTHORIZATION_PATH = (
    REFERENCE_CASES / "e4_pl_s3_v2_stage4a_execution_authorization.json"
)
MANIFEST_PATH = REFERENCE_CASES / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
SCAFFOLD_CONTRACT_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel_contract.json"
SOURCE_CONTRACT_PATH = REFERENCE_CASES / "e4_pl_s3_v2_source_equation_contract.json"
PRODUCER_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel_producer.py"
CHECKER_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel_checker.py"
FUNNEL_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel.py"
BOUNDED_PATH = REFERENCE_CASES / "e4_pl_s3_v2_bounded_process.py"

CONTRACT_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-contract-v6"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-execution-authorization-v2"
LEAF_WAVE_AUTHORIZATION_SCHEMA = (
    "anysolver.e4-pl-s3-v2-stage4a-leaf-wave-authorization-v5"
)
AUTHORITY_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-authority-v8"
REVIEW_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-implementation-review-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-aggregate-v3"
HISTORICAL_AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-aggregate-v2"
CHECKER_RESULT_SCHEMA = "anysolver.e4-pl-s3-v2-phase4a-checker-result-v2"
PRODUCER_RESULT_SCHEMA = "anysolver.e4-pl-s3-v2-bounded-wave-result-v1"
LEAF_ASSIGNMENT_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-leaf-assignment-v3"
LEAF_CATALOG_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-leaf-catalog-v3"
LEAF_WAVE_CATALOG_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-leaf-wave-catalog-v3"
LEAF_PAYLOAD_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-leaf-payload-v3"
LEAF_SCIENTIFIC_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-leaf-scientific-v3"
LEAF_UNION_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-leaf-union-v3"
LEAF_WAVE_RECEIPT_SCHEMA = (
    "anysolver.e4-pl-s3-v2-stage4a-leaf-wave-receipt-v3"
)
LEAF_UNION_TERMINAL = "COMPLETE_FOR_DIAGONAL_RECONSTRUCTION"
LEAF_PROOF_TERMINAL = "ACCEPTED_FOR_AGGREGATION"
DIAGONAL_PAYLOAD_SCHEMA = "anysolver.e4-pl-s3-v2-phase4a-production-payload-v2"
DIAGONAL_SCIENTIFIC_SCHEMA = (
    "anysolver.e4-pl-s3-v2-flat-funnel-shard-scientific-v2"
)
LEAF_SELECTOR = "e4-pl-s3-v2"
LEAF_CLASSIFICATION = "CLASSIFYING_Q4_V2A_PRODUCTION_MECHANICS"
LEAF_V1_CLASSIFICATION = "NONCLASSIFYING_V1_COMPARATOR_ONLY"
LEAF_V1_FORMULATION_ID = "E4_PL_QUALIFIED_S3_COMPANION_V1"
LEAF_V1_DISPOSITION = (
    "HISTORICAL_V1_COMPARATOR_EXCLUDED_FROM_FORMAL_RUNTIME_NO_FALLBACK"
)
LEAF_V2_ROLE = "V2_CLASSIFYING"
LEAF_V1_ROLE = "V1_DIAGNOSTIC"
LEAF_V1_SELECTOR = "e4-pl-s3"
LEAF_LOGICAL_RECORD_COUNT = 81
LEAF_V2_COUNT = 81
LEAF_V1_DIAGNOSTIC_COUNT = 0
LEAF_CATALOG_COUNT = LEAF_V2_COUNT + LEAF_V1_DIAGNOSTIC_COUNT
LEAF_WAVE_PAIR_COUNT = 40
LEAF_WAVE_SINGLETON_COUNT = 1
LEAF_WAVE_COUNT = LEAF_WAVE_PAIR_COUNT + LEAF_WAVE_SINGLETON_COUNT
LEAF_WORKER_WALL_SECONDS = 1500
LEAF_FINALIZER_WALL_SECONDS = 1740
LEAF_FINALIZER_PUBLICATION_RESERVE_SECONDS = 15
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
CHECKER_REGISTERED_SHARDS = 3
MAXIMUM_CONCURRENT_WORKERS = 2
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
    "tests/test_e4_pl_s3_v2_component_cache.py",
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
        wall_seconds: int = COORDINATOR_WALL_SECONDS,
        publication_reserve_seconds: int = (
            COORDINATOR_FAIL_CLOSED_PUBLICATION_RESERVE_SECONDS
        ),
    ) -> None:
        if (
            isinstance(wall_seconds, bool)
            or not isinstance(wall_seconds, int)
            or wall_seconds <= 0
            or wall_seconds >= 1800
            and wall_seconds != COORDINATOR_WALL_SECONDS
        ):
            raise CoordinatorError("coordinator wall must be a positive registered bound")
        if (
            isinstance(publication_reserve_seconds, bool)
            or not isinstance(publication_reserve_seconds, int)
            or publication_reserve_seconds <= 0
            or publication_reserve_seconds >= wall_seconds
        ):
            raise CoordinatorError("coordinator publication reserve is invalid")
        self.aggregate_path = aggregate_path.resolve()
        self.hard_deadline = started + wall_seconds
        self.work_deadline = (
            self.hard_deadline
            - publication_reserve_seconds
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
        "checker_registered_shards": CHECKER_REGISTERED_SHARDS,
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
        "leaf_catalog_count": LEAF_CATALOG_COUNT,
        "leaf_finalizer_wall_seconds": LEAF_FINALIZER_WALL_SECONDS,
        "leaf_formal_v1_diagnostic_count": LEAF_V1_DIAGNOSTIC_COUNT,
        "leaf_historical_v1_disposition": LEAF_V1_DISPOSITION,
        "leaf_logical_record_count": LEAF_LOGICAL_RECORD_COUNT,
        "leaf_pair_wave_count": LEAF_WAVE_PAIR_COUNT,
        "leaf_pairing": "CONSECUTIVE_V2_LEAVES_IN_FROZEN_CATALOG_ORDER",
        "leaf_singleton_wave_count": LEAF_WAVE_SINGLETON_COUNT,
        "leaf_v2_classifying_count": LEAF_V2_COUNT,
        "leaf_wave_count": LEAF_WAVE_COUNT,
        "leaf_wave_receipt_count": LEAF_WAVE_COUNT,
        "leaf_wave_wall_seconds": LEAF_FINALIZER_WALL_SECONDS,
        "leaf_worker_wall_seconds": LEAF_WORKER_WALL_SECONDS,
        "maximum_concurrent_workers": MAXIMUM_CONCURRENT_WORKERS,
        "maximum_memory_gib_per_process_tree": MEMORY_LIMIT_BYTES // (1 << 30),
        "memory_admission_headroom_gib": OS_HEADROOM_BYTES // (1 << 30),
        "memory_admission_required_bytes": (
            MAXIMUM_CONCURRENT_WORKERS * MEMORY_LIMIT_BYTES + OS_HEADROOM_BYTES
        ),
        "no_automatic_retry": True,
        "numerical_library_threads_per_worker": 1,
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


def _external_file_binding(path: Path, location: str) -> dict[str, Any]:
    raw_path = Path(path)
    if not raw_path.is_absolute():
        raise CoordinatorError(f"{location} must be absolute")
    resolved = raw_path.resolve(strict=True)
    raw = resolved.read_bytes()
    if not raw:
        raise CoordinatorError(f"{location} must be nonempty")
    binding = {
        "byte_count": len(raw),
        "path": str(resolved),
        "sha256": sha256(raw),
    }
    _validate_external_file_binding(binding, location, expected_path=resolved)
    return binding


def _nonnegative_integer(value: Any, location: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CoordinatorError(f"{location} must be a nonnegative integer")
    return value


def _stage4a_plan_shards(
    plan: Mapping[str, Any], plan_raw: bytes
) -> tuple[Mapping[str, Any], ...]:
    """Validate the content-addressed structure needed by correction-4 leaves.

    The formal finalizer additionally joins this plan to the immutable
    connectivity manifest through ``validate_phase_plan``.  This local check is
    deliberately independent of the producer so catalog corruption is caught
    before any producer or checker is imported.
    """

    if plan_raw != canonical_bytes(plan):
        raise CoordinatorError("Stage 4A leaf plan is not canonical JSON")
    checked = _exact(
        plan,
        {
            "advisory_review_triggers",
            "formal_thresholds",
            "manifest_sha256",
            "phase",
            "prerequisites",
            "record_count",
            "schema",
            "selector",
            "shards",
            "scope",
        },
        "$.leaf_plan",
    )
    if (
        checked["schema"] != "anysolver.e4-pl-s3-v2-flat-funnel-plan-v1"
        or checked["phase"] != "4A"
        or checked["scope"] != "full"
        or checked["selector"] != LEAF_SELECTOR
        or checked["record_count"] != LEAF_LOGICAL_RECORD_COUNT
    ):
        raise CoordinatorError("Stage 4A leaf plan identity differs")
    _digest(checked["manifest_sha256"], "$.leaf_plan.manifest_sha256")
    raw_shards = checked["shards"]
    if not isinstance(raw_shards, list) or len(raw_shards) != len(EXPECTED_SHARDS):
        raise CoordinatorError("Stage 4A leaf plan shard coverage differs")
    made: list[Mapping[str, Any]] = []
    seen_indices: set[int] = set()
    seen_records: set[str] = set()
    for shard_index, (raw_shard, (assignment_id, diagonal)) in enumerate(
        zip(raw_shards, EXPECTED_SHARDS.items())
    ):
        location = f"$.leaf_plan.shards[{shard_index}]"
        shard = _exact(
            raw_shard,
            {
                "assignment_id",
                "assignment_sha256",
                "diagonal",
                "manifest_sha256",
                "phase",
                "records",
                "schema",
                "selector",
                "scope",
            },
            location,
        )
        members = shard["records"]
        if (
            shard["schema"]
            != "anysolver.e4-pl-s3-v2-flat-funnel-assignment-v1"
            or shard["assignment_id"] != assignment_id
            or shard["diagonal"] != diagonal
            or shard["manifest_sha256"] != checked["manifest_sha256"]
            or shard["phase"] != "4A"
            or shard["scope"] != "full"
            or shard["selector"] != LEAF_SELECTOR
            or not isinstance(members, list)
            or len(members) != 27
        ):
            raise CoordinatorError(f"Stage 4A leaf shard identity differs: {diagonal}")
        assignment_core = dict(shard)
        assignment_digest = assignment_core.pop("assignment_sha256")
        if (
            _digest(assignment_digest, f"{location}.assignment_sha256")
            != sha256(canonical_bytes(assignment_core))
        ):
            raise CoordinatorError(f"Stage 4A leaf shard hash differs: {diagonal}")
        for member_index, raw_member in enumerate(members):
            member_location = f"{location}.records[{member_index}]"
            member = _exact(
                raw_member,
                {"manifest_index", "record", "record_id"},
                member_location,
            )
            manifest_index = _nonnegative_integer(
                member["manifest_index"], f"{member_location}.manifest_index"
            )
            record_id = member["record_id"]
            record = member["record"]
            if (
                manifest_index in seen_indices
                or not isinstance(record_id, str)
                or not record_id
                or record_id in seen_records
                or not isinstance(record, dict)
                or record.get("diagonal") != diagonal
            ):
                raise CoordinatorError("Stage 4A leaf plan record coverage differs")
            s3_count = record.get("s3_element_count")
            if (
                isinstance(s3_count, bool)
                or not isinstance(s3_count, int)
                or s3_count < 0
            ):
                raise CoordinatorError("Stage 4A leaf plan S3 count is malformed")
            seen_indices.add(manifest_index)
            seen_records.add(record_id)
        made.append(shard)
    if (
        len(seen_indices) != LEAF_LOGICAL_RECORD_COUNT
        or len(seen_records) != LEAF_LOGICAL_RECORD_COUNT
    ):
        raise CoordinatorError("Stage 4A leaf plan does not contain 81 unique records")
    return tuple(made)


def _leaf_candidate_authority(
    *,
    candidate_commit: Any,
    candidate_tree: Any,
    candidate_archive_sha256: Any,
    producer_program_sha256: Any,
) -> dict[str, str]:
    """Return the exact four-field identity frozen into every leaf."""

    return {
        "candidate_archive_sha256": _digest(
            candidate_archive_sha256, "$.leaf_candidate.candidate_archive_sha256"
        ),
        "candidate_commit": _lower_object(
            candidate_commit, "$.leaf_candidate.candidate_commit"
        ),
        "candidate_tree": _lower_object(
            candidate_tree, "$.leaf_candidate.candidate_tree"
        ),
        "producer_program_sha256": _digest(
            producer_program_sha256, "$.leaf_candidate.producer_program_sha256"
        ),
    }


def _leaf_candidate_authority_sha256(authority: Mapping[str, Any]) -> str:
    checked = _exact(
        authority,
        {
            "candidate_archive_sha256",
            "candidate_commit",
            "candidate_tree",
            "producer_program_sha256",
        },
        "$.leaf_candidate_authority",
    )
    canonical = _leaf_candidate_authority(**checked)
    if dict(checked) != canonical:
        raise CoordinatorError("leaf candidate authority is noncanonical")
    return sha256(canonical_bytes(canonical))


def build_stage4a_leaf_catalog(
    plan: Mapping[str, Any],
    plan_raw: bytes,
    *,
    candidate_commit: str,
    candidate_tree: str,
    candidate_archive_sha256: str,
    producer_program_sha256: str,
) -> dict[str, Any]:
    """Build the deterministic content-addressed V2-only formal leaf catalog."""

    shards = _stage4a_plan_shards(plan, plan_raw)
    plan_digest = sha256(plan_raw)
    candidate_authority = _leaf_candidate_authority(
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
        candidate_archive_sha256=candidate_archive_sha256,
        producer_program_sha256=producer_program_sha256,
    )
    candidate_authority_sha256 = _leaf_candidate_authority_sha256(
        candidate_authority
    )
    leaves: list[dict[str, Any]] = []
    seen_digests: set[str] = set()
    logical_record_index = 0
    for shard in shards:
        for member in shard["records"]:
            assignment = {
                "catalog_index": len(leaves),
                **candidate_authority,
                "computation_role": LEAF_V2_ROLE,
                "diagonal": shard["diagonal"],
                "logical_record_index": logical_record_index,
                "manifest_index": member["manifest_index"],
                "parent_assignment_id": shard["assignment_id"],
                "parent_assignment_sha256": shard["assignment_sha256"],
                "phase": "4A",
                "plan_sha256": plan_digest,
                "record_id": member["record_id"],
                "record_member_sha256": sha256(canonical_bytes(dict(member))),
                "s3_selector": LEAF_SELECTOR,
                "schema": LEAF_ASSIGNMENT_SCHEMA,
                "selector": LEAF_SELECTOR,
            }
            digest = sha256(canonical_bytes(assignment))
            if digest in seen_digests:
                raise CoordinatorError("Stage 4A leaf assignment hash is duplicated")
            seen_digests.add(digest)
            leaves.append(
                {
                    "assignment": assignment,
                    "leaf_assignment_sha256": digest,
                    "leaf_id": f"S3_V2_FLAT_4A_LEAF_{digest}",
                }
            )
            logical_record_index += 1
    diagnostic_count = sum(
        leaf["assignment"]["computation_role"] == LEAF_V1_ROLE
        for leaf in leaves
    )
    classifying_count = sum(
        leaf["assignment"]["computation_role"] == LEAF_V2_ROLE
        for leaf in leaves
    )
    if (
        len(leaves) != LEAF_CATALOG_COUNT
        or len(seen_digests) != LEAF_CATALOG_COUNT
        or logical_record_index != LEAF_LOGICAL_RECORD_COUNT
        or classifying_count != LEAF_V2_COUNT
        or diagnostic_count != LEAF_V1_DIAGNOSTIC_COUNT
    ):
        raise CoordinatorError("Stage 4A leaf catalog coverage differs")
    return {
        "candidate_authority": candidate_authority,
        "candidate_authority_sha256": candidate_authority_sha256,
        "leaf_count": LEAF_CATALOG_COUNT,
        "leaves": leaves,
        "logical_record_count": LEAF_LOGICAL_RECORD_COUNT,
        "plan_sha256": plan_digest,
        "schema": LEAF_CATALOG_SCHEMA,
        "v2_classifying_count": LEAF_V2_COUNT,
        "v1_comparator_disposition": LEAF_V1_DISPOSITION,
        "v1_diagnostic_count": LEAF_V1_DIAGNOSTIC_COUNT,
    }


def _validate_stage4a_leaf_catalog(catalog: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    checked = _exact(
        catalog,
        {
            "candidate_authority",
            "candidate_authority_sha256",
            "leaf_count",
            "leaves",
            "logical_record_count",
            "plan_sha256",
            "schema",
            "v2_classifying_count",
            "v1_comparator_disposition",
            "v1_diagnostic_count",
        },
        "$.leaf_catalog",
    )
    if (
        checked["schema"] != LEAF_CATALOG_SCHEMA
        or checked["leaf_count"] != LEAF_CATALOG_COUNT
        or checked["logical_record_count"] != LEAF_LOGICAL_RECORD_COUNT
        or checked["v2_classifying_count"] != LEAF_V2_COUNT
        or checked["v1_diagnostic_count"] != LEAF_V1_DIAGNOSTIC_COUNT
        or checked["v1_comparator_disposition"] != LEAF_V1_DISPOSITION
    ):
        raise CoordinatorError("Stage 4A leaf catalog identity differs")
    plan_digest = _digest(checked["plan_sha256"], "$.leaf_catalog.plan_sha256")
    candidate_authority = _exact(
        checked["candidate_authority"],
        {
            "candidate_archive_sha256",
            "candidate_commit",
            "candidate_tree",
            "producer_program_sha256",
        },
        "$.leaf_catalog.candidate_authority",
    )
    candidate_authority_sha256 = _leaf_candidate_authority_sha256(
        candidate_authority
    )
    if checked["candidate_authority_sha256"] != candidate_authority_sha256:
        raise CoordinatorError("Stage 4A leaf candidate authority hash differs")
    raw_leaves = checked["leaves"]
    if not isinstance(raw_leaves, list) or len(raw_leaves) != LEAF_CATALOG_COUNT:
        raise CoordinatorError("Stage 4A leaf catalog count differs")
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    seen_roles: set[tuple[str, str]] = set()
    logical_records: dict[int, list[Mapping[str, Any]]] = {}
    diagnostic_count = 0
    classifying_count = 0
    leaves: list[Mapping[str, Any]] = []
    assignment_keys = {
        "catalog_index",
        "candidate_archive_sha256",
        "candidate_commit",
        "candidate_tree",
        "computation_role",
        "diagonal",
        "logical_record_index",
        "manifest_index",
        "parent_assignment_id",
        "parent_assignment_sha256",
        "phase",
        "plan_sha256",
        "producer_program_sha256",
        "record_id",
        "record_member_sha256",
        "s3_selector",
        "schema",
        "selector",
    }
    for index, raw_leaf in enumerate(raw_leaves):
        location = f"$.leaf_catalog.leaves[{index}]"
        leaf = _exact(
            raw_leaf,
            {"assignment", "leaf_assignment_sha256", "leaf_id"},
            location,
        )
        assignment = _exact(leaf["assignment"], assignment_keys, f"{location}.assignment")
        digest = _digest(
            leaf["leaf_assignment_sha256"], f"{location}.leaf_assignment_sha256"
        )
        record_id = assignment["record_id"]
        computation_role = assignment["computation_role"]
        if (
            assignment["schema"] != LEAF_ASSIGNMENT_SCHEMA
            or assignment["catalog_index"] != index
            or any(
                assignment[key] != candidate_authority[key]
                for key in candidate_authority
            )
            or assignment["phase"] != "4A"
            or assignment["plan_sha256"] != plan_digest
            or assignment["selector"] != LEAF_SELECTOR
            or computation_role != LEAF_V2_ROLE
            or assignment["s3_selector"] != LEAF_SELECTOR
            or assignment["diagonal"] not in DIAGONAL_ORDER
            or assignment["parent_assignment_id"]
            not in EXPECTED_SHARDS
            or EXPECTED_SHARDS.get(str(assignment["parent_assignment_id"]))
            != assignment["diagonal"]
            or not isinstance(record_id, str)
            or not record_id
            or sha256(canonical_bytes(dict(assignment))) != digest
            or leaf["leaf_id"] != f"S3_V2_FLAT_4A_LEAF_{digest}"
        ):
            raise CoordinatorError("Stage 4A leaf catalog member identity differs")
        _nonnegative_integer(
            assignment["manifest_index"], f"{location}.assignment.manifest_index"
        )
        logical_index = _nonnegative_integer(
            assignment["logical_record_index"],
            f"{location}.assignment.logical_record_index",
        )
        if logical_index >= LEAF_LOGICAL_RECORD_COUNT:
            raise CoordinatorError("Stage 4A logical record index is outside coverage")
        _digest(
            assignment["parent_assignment_sha256"],
            f"{location}.assignment.parent_assignment_sha256",
        )
        _digest(
            assignment["record_member_sha256"],
            f"{location}.assignment.record_member_sha256",
        )
        role_key = (str(record_id), str(computation_role))
        if leaf["leaf_id"] in seen_ids or digest in seen_hashes or role_key in seen_roles:
            raise CoordinatorError("Stage 4A leaf catalog contains a duplicate")
        seen_ids.add(str(leaf["leaf_id"]))
        seen_hashes.add(digest)
        seen_roles.add(role_key)
        logical_records.setdefault(logical_index, []).append(leaf)
        diagnostic_count += int(computation_role == LEAF_V1_ROLE)
        classifying_count += int(computation_role == LEAF_V2_ROLE)
        leaves.append(leaf)
    if (
        diagnostic_count != LEAF_V1_DIAGNOSTIC_COUNT
        or classifying_count != LEAF_V2_COUNT
        or set(logical_records) != set(range(LEAF_LOGICAL_RECORD_COUNT))
    ):
        raise CoordinatorError("Stage 4A formal leaf coverage differs")
    for logical_index, group in logical_records.items():
        if (
            [leaf["assignment"]["computation_role"] for leaf in group]
            != [LEAF_V2_ROLE]
            or any(
                leaf["assignment"]["logical_record_index"] != logical_index
                or leaf["assignment"]["record_id"]
                != group[0]["assignment"]["record_id"]
                or leaf["assignment"]["record_member_sha256"]
                != group[0]["assignment"]["record_member_sha256"]
                for leaf in group
            )
        ):
            raise CoordinatorError("Stage 4A logical V2 leaf differs")
    return leaves


def build_stage4a_leaf_wave_catalog(catalog: Mapping[str, Any]) -> dict[str, Any]:
    """Pair consecutive formal V2 leaves, leaving the final leaf singleton."""

    leaves = _validate_stage4a_leaf_catalog(catalog)
    waves: list[dict[str, Any]] = []
    for offset in range(0, LEAF_CATALOG_COUNT, MAXIMUM_CONCURRENT_WORKERS):
        group = leaves[offset : offset + MAXIMUM_CONCURRENT_WORKERS]
        wave_index = len(waves) + 1
        waves.append(
            {
                "leaf_assignment_sha256": [
                    leaf["leaf_assignment_sha256"] for leaf in group
                ],
                "leaf_ids": [leaf["leaf_id"] for leaf in group],
                "logical_record_indices": [
                    leaf["assignment"]["logical_record_index"] for leaf in group
                ],
                "record_ids": [leaf["assignment"]["record_id"] for leaf in group],
                "wave_id": f"S3_V2_FLAT_4A_WAVE_{wave_index:02d}",
                "worker_count": len(group),
            }
        )
    if (
        len(waves) != LEAF_WAVE_COUNT
        or sum(wave["worker_count"] == 2 for wave in waves)
        != LEAF_WAVE_PAIR_COUNT
        or sum(wave["worker_count"] == 1 for wave in waves)
        != LEAF_WAVE_SINGLETON_COUNT
        or [leaf_id for wave in waves for leaf_id in wave["leaf_ids"]]
        != [leaf["leaf_id"] for leaf in leaves]
        or [
            logical_index
            for wave in waves
            for logical_index in wave["logical_record_indices"]
        ]
        != list(range(LEAF_LOGICAL_RECORD_COUNT))
    ):
        raise CoordinatorError("Stage 4A leaf wave partition differs")
    return {
        "leaf_catalog_sha256": sha256(canonical_bytes(dict(catalog))),
        "maximum_concurrent_workers": MAXIMUM_CONCURRENT_WORKERS,
        "pair_wave_count": LEAF_WAVE_PAIR_COUNT,
        "schema": LEAF_WAVE_CATALOG_SCHEMA,
        "singleton_wave_count": LEAF_WAVE_SINGLETON_COUNT,
        "wave_count": LEAF_WAVE_COUNT,
        "waves": waves,
    }


_SCIENTIFIC_RECORD_KEYS = {
    "classification",
    "connectivity_sha256",
    "diagonal",
    "element_counts",
    "energy_norm",
    "formulation_counts",
    "level",
    "manifest_index",
    "mask",
    "node_count",
    "participation",
    "quadratic_forms",
    "record_id",
    "reference",
    "response",
    "s3_area_fraction_percent",
    "solution_energies",
    "solver",
    "support_counts",
}


def _validate_leaf_scientific_record(
    value: Any,
    *,
    member: Mapping[str, Any],
    diagnostic_v1: bool,
    location: str,
) -> Mapping[str, Any]:
    keys = set(_SCIENTIFIC_RECORD_KEYS)
    if diagnostic_v1:
        keys.add("formulation_id")
    record = _exact(value, keys, location)
    expected = member["record"]
    if (
        record["classification"]
        != (LEAF_V1_CLASSIFICATION if diagnostic_v1 else LEAF_CLASSIFICATION)
        or record["record_id"] != member["record_id"]
        or record["manifest_index"] != member["manifest_index"]
        or record["connectivity_sha256"] != expected["connectivity_sha256"]
        or record["level"] != expected["level"]
        or record["mask"] != expected["mask"]
        or record["diagonal"] != expected["diagonal"]
        or record["s3_area_fraction_percent"]
        != expected["s3_area_fraction_percent"]
    ):
        raise CoordinatorError(f"{location} differs from its immutable plan member")
    if diagnostic_v1 and record["formulation_id"] != LEAF_V1_FORMULATION_ID:
        raise CoordinatorError(f"{location} V1 formulation identity differs")
    # Canonical serialization recursively rejects non-finite or unsupported
    # values.  Detailed mechanics predicates remain solely in the independent
    # checker after diagonal reconstruction.
    canonical_bytes(dict(record))
    return record


def validate_stage4a_leaf_proof(
    value: Mapping[str, Any],
    raw: bytes,
    *,
    entry: Mapping[str, Any],
    member: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate one leaf and its exact parent/member cross-join."""

    if raw != canonical_bytes(value):
        raise CoordinatorError("Stage 4A leaf proof is not canonical JSON")
    proof = _exact(
        value,
        {
            "assignment_sha256",
            "plan_sha256",
            "record_count",
            "record_ids",
            "record_ids_sha256",
            "schema",
            "scientific_payload",
            "scientific_payload_sha256",
            "selector",
            "terminal",
        },
        "$.leaf_proof",
    )
    catalog_entry = _exact(
        entry,
        {"assignment", "leaf_assignment_sha256", "leaf_id"},
        "$.leaf_catalog_entry",
    )
    assignment = catalog_entry["assignment"]
    record_ids = proof["record_ids"]
    payload = _exact(
        proof["scientific_payload"],
        {
            "computation_role",
            "leaf_assignment",
            "phase",
            "protocol",
            "record",
            "schema",
            "v1_comparator_disposition",
        },
        "$.leaf_proof.scientific_payload",
    )
    if (
        proof["schema"] != LEAF_SCIENTIFIC_SCHEMA
        or proof["terminal"] != LEAF_PROOF_TERMINAL
        or proof["selector"] != LEAF_SELECTOR
        or proof["record_count"] != 1
        or proof["assignment_sha256"] != catalog_entry["leaf_assignment_sha256"]
        or proof["plan_sha256"] != assignment["plan_sha256"]
        or record_ids != [member["record_id"]]
        or payload["schema"] != LEAF_PAYLOAD_SCHEMA
        or payload["phase"] != "4A"
        or payload["leaf_assignment"] != assignment
        or payload["computation_role"] != LEAF_V2_ROLE
        or assignment["computation_role"] != LEAF_V2_ROLE
        or assignment["s3_selector"] != LEAF_SELECTOR
        or payload["v1_comparator_disposition"] != LEAF_V1_DISPOSITION
    ):
        raise CoordinatorError("Stage 4A leaf proof identity differs")
    if (
        _digest(proof["record_ids_sha256"], "$.leaf_proof.record_ids_sha256")
        != sha256(canonical_bytes(record_ids))
        or _digest(
            proof["scientific_payload_sha256"],
            "$.leaf_proof.scientific_payload_sha256",
        )
        != sha256(canonical_bytes(dict(payload)))
    ):
        raise CoordinatorError("Stage 4A leaf proof content hash differs")
    protocol = _exact(
        payload["protocol"],
        {"classification", "energy_norm_id", "load_id", "reference_id", "support_id"},
        "$.leaf_proof.scientific_payload.protocol",
    )
    if protocol["classification"] != LEAF_CLASSIFICATION or any(
        not isinstance(protocol[key], str) or not protocol[key]
        for key in ("energy_norm_id", "load_id", "reference_id", "support_id")
    ):
        raise CoordinatorError("Stage 4A leaf proof protocol identity differs")
    _validate_leaf_scientific_record(
        payload["record"],
        member=member,
        diagnostic_v1=False,
        location="$.leaf_proof.scientific_payload.record",
    )
    return proof


def build_stage4a_leaf_union(
    catalog: Mapping[str, Any],
    receipt_paths_by_wave_index: Mapping[int, Path],
    *,
    candidate_archive_path: Path,
    contract: Mapping[str, Any],
    contract_path: Path,
    contract_raw: bytes,
    authorization_path: Path,
    authorization_raw: bytes,
    output_root: Path,
) -> dict[str, Any]:
    """Build a union only from all canonical, process-complete wave receipts."""

    leaves = _validate_stage4a_leaf_catalog(catalog)
    if set(receipt_paths_by_wave_index) != set(range(1, LEAF_WAVE_COUNT + 1)):
        raise CoordinatorError("Stage 4A leaf wave receipt coverage differs")
    candidate_authority = catalog["candidate_authority"]
    raw_archive_path = Path(candidate_archive_path)
    if not raw_archive_path.is_absolute():
        raise CoordinatorError("Stage 4A candidate archive path must be absolute")
    archive_path = raw_archive_path.resolve()
    if not archive_path.is_file() or archive_path.is_symlink():
        raise CoordinatorError("Stage 4A candidate archive is not a regular non-link file")
    archive_raw = archive_path.read_bytes()
    if (
        not archive_raw
        or sha256(archive_raw) != candidate_authority["candidate_archive_sha256"]
    ):
        raise CoordinatorError("Stage 4A candidate archive identity differs")
    bindings: list[dict[str, Any]] = []
    receipt_bindings: list[dict[str, Any]] = []
    request_ids: set[str] = set()
    leaf_by_id = {str(leaf["leaf_id"]): leaf for leaf in leaves}
    for wave_index in range(1, LEAF_WAVE_COUNT + 1):
        cycle = _validate_stage4a_leaf_cycle(
            contract=contract,
            contract_path=contract_path,
            output_root=output_root,
            wave_index=wave_index,
        )
        validated = validate_stage4a_leaf_wave_receipt(
            Path(receipt_paths_by_wave_index[wave_index]),
            contract=contract,
            contract_path=contract_path,
            contract_raw=contract_raw,
            cycle=cycle,
            wave_index=wave_index,
            allowed_root=output_root,
            expected_authorization_path=authorization_path,
            expected_authorization_raw=authorization_raw,
        )
        receipt = validated["receipt"]
        request_id = str(receipt["request_id"])
        if request_id in request_ids:
            raise CoordinatorError("leaf wave resource request ID was reused")
        request_ids.add(request_id)
        receipt_bindings.append(
            _external_file_binding(validated["path"], "leaf wave receipt")
            | {
                "request_id": request_id,
                "terminal_ledger_row": validated["terminal_ledger_row"],
                "wave_index": wave_index,
            }
        )
        for worker in validated["workers"]:
            leaf_id = str(worker["leaf_id"])
            leaf = leaf_by_id.get(leaf_id)
            if leaf is None or worker["assignment_sha256"] != leaf["leaf_assignment_sha256"]:
                raise CoordinatorError("leaf receipt worker is absent from catalog")
            proof = worker["proof"]
            bindings.append(
                {
                    "attempt_sha256": receipt["attempt"]["sha256"],
                    "authorization_sha256": receipt["authorization"]["sha256"],
                    "byte_count": proof["byte_count"],
                    "leaf_assignment_sha256": leaf["leaf_assignment_sha256"],
                    "leaf_id": leaf_id,
                    "path": proof["path"],
                    "request_command_sha256": receipt["request_command_sha256"],
                    "request_id": request_id,
                    "result_sha256": receipt["result"]["sha256"],
                    "sha256": proof["sha256"],
                    "termination_proven": True,
                    "wave_receipt_sha256": sha256(validated["raw"]),
                }
            )
    expected_leaf_ids = [str(leaf["leaf_id"]) for leaf in leaves]
    if (
        [binding["leaf_id"] for binding in bindings] != expected_leaf_ids
        or len(request_ids) != LEAF_WAVE_COUNT
    ):
        raise CoordinatorError("Stage 4A receipt union leaf order differs")
    return {
        "candidate_archive": {
            "byte_count": len(archive_raw),
            "path": str(archive_path),
            "sha256": sha256(archive_raw),
        },
        "candidate_authority": candidate_authority,
        "candidate_authority_sha256": catalog["candidate_authority_sha256"],
        "leaf_catalog_sha256": sha256(canonical_bytes(dict(catalog))),
        "leaf_count": LEAF_CATALOG_COUNT,
        "logical_record_count": LEAF_LOGICAL_RECORD_COUNT,
        "leaf_wave_authorization": _external_file_binding(
            authorization_path, "leaf wave authorization"
        ),
        "plan_sha256": catalog["plan_sha256"],
        "proofs": bindings,
        "schema": LEAF_UNION_SCHEMA,
        "terminal": LEAF_UNION_TERMINAL,
        "v2_classifying_count": LEAF_V2_COUNT,
        "v1_comparator_disposition": LEAF_V1_DISPOSITION,
        "v1_diagnostic_count": LEAF_V1_DIAGNOSTIC_COUNT,
        "wave_receipts": receipt_bindings,
    }


def validate_stage4a_leaf_union(
    union_path: Path,
    *,
    catalog: Mapping[str, Any],
    plan: Mapping[str, Any],
    plan_raw: bytes,
    candidate_authority: Mapping[str, Any],
    contract: Mapping[str, Any],
    contract_path: Path,
    contract_raw: bytes,
    allowed_root: Path | None = None,
    frozen_union_raw: bytes | None = None,
) -> dict[str, Any]:
    """Validate complete leaf coverage and every proof before reconstruction."""

    canonical_authority = _leaf_candidate_authority(**candidate_authority)
    expected_catalog = build_stage4a_leaf_catalog(
        plan,
        plan_raw,
        **canonical_authority,
    )
    if catalog != expected_catalog:
        raise CoordinatorError("Stage 4A leaf catalog differs from the frozen plan")
    leaves = _validate_stage4a_leaf_catalog(catalog)
    if frozen_union_raw is None:
        union, union_raw = strict_json_load(union_path)
    else:
        union_raw = frozen_union_raw
        union = strict_json_bytes(union_raw, str(union_path))
    if union_raw != canonical_bytes(union):
        raise CoordinatorError("Stage 4A leaf union is not canonical JSON")
    bound = _exact(
        union,
        {
            "candidate_archive",
            "candidate_authority",
            "candidate_authority_sha256",
            "leaf_catalog_sha256",
            "leaf_count",
            "leaf_wave_authorization",
            "logical_record_count",
            "plan_sha256",
            "proofs",
            "schema",
            "terminal",
            "v2_classifying_count",
            "v1_comparator_disposition",
            "v1_diagnostic_count",
            "wave_receipts",
        },
        "$.leaf_union",
    )
    if (
        bound["schema"] != LEAF_UNION_SCHEMA
        or bound["terminal"] != LEAF_UNION_TERMINAL
        or bound["leaf_count"] != LEAF_CATALOG_COUNT
        or bound["logical_record_count"] != LEAF_LOGICAL_RECORD_COUNT
        or bound["v2_classifying_count"] != LEAF_V2_COUNT
        or bound["v1_diagnostic_count"] != LEAF_V1_DIAGNOSTIC_COUNT
        or bound["v1_comparator_disposition"] != LEAF_V1_DISPOSITION
        or bound["plan_sha256"] != sha256(plan_raw)
        or bound["leaf_catalog_sha256"] != sha256(canonical_bytes(dict(catalog)))
        or bound["candidate_authority"] != canonical_authority
        or bound["candidate_authority_sha256"]
        != _leaf_candidate_authority_sha256(canonical_authority)
    ):
        raise CoordinatorError("Stage 4A leaf union identity differs")
    archive_path, archive_raw = _validate_external_file_binding(
        bound["candidate_archive"], "$.leaf_union.candidate_archive"
    )
    if sha256(archive_raw) != canonical_authority["candidate_archive_sha256"]:
        raise CoordinatorError("Stage 4A leaf union archive identity differs")
    wave_authorization_path, wave_authorization_raw = (
        _validate_external_file_binding(
            bound["leaf_wave_authorization"],
            "$.leaf_union.leaf_wave_authorization",
        )
    )
    receipt_bindings = bound["wave_receipts"]
    if (
        not isinstance(receipt_bindings, list)
        or len(receipt_bindings) != LEAF_WAVE_COUNT
    ):
        raise CoordinatorError("Stage 4A leaf union receipt coverage differs")
    receipt_paths: dict[int, Path] = {}
    for expected_index, raw_receipt in enumerate(receipt_bindings, start=1):
        receipt_binding = _exact(
            raw_receipt,
            {
                "byte_count",
                "path",
                "request_id",
                "sha256",
                "terminal_ledger_row",
                "wave_index",
            },
            f"$.leaf_union.wave_receipts[{expected_index - 1}]",
        )
        terminal_row = _exact(
            receipt_binding["terminal_ledger_row"],
            {"line", "sha256", "status"},
            f"$.leaf_union.wave_receipts[{expected_index - 1}].terminal_ledger_row",
        )
        if (
            receipt_binding["wave_index"] != expected_index
            or not isinstance(receipt_binding["request_id"], str)
            or len(receipt_binding["request_id"]) != 32
            or terminal_row["status"] != "COMPLETED_PASS"
            or terminal_row["sha256"]
            != sha256((str(terminal_row["line"]).rstrip() + "\n").encode("utf-8"))
        ):
            raise CoordinatorError("Stage 4A leaf union receipt order differs")
        receipt_path, _receipt_raw = _validate_external_file_binding(
            {
                "byte_count": receipt_binding["byte_count"],
                "path": receipt_binding["path"],
                "sha256": receipt_binding["sha256"],
            },
            f"$.leaf_union.wave_receipts[{expected_index - 1}]",
        )
        receipt_paths[expected_index] = receipt_path
    if allowed_root is None:
        raise CoordinatorError("Stage 4A receipt union requires its cycle root")
    expected_union = build_stage4a_leaf_union(
        catalog,
        receipt_paths,
        candidate_archive_path=archive_path,
        contract=contract,
        contract_path=contract_path,
        contract_raw=contract_raw,
        authorization_path=wave_authorization_path,
        authorization_raw=wave_authorization_raw,
        output_root=allowed_root,
    )
    if bound != expected_union:
        raise CoordinatorError("Stage 4A leaf union differs from bounded wave receipts")
    bindings = bound["proofs"]
    if not isinstance(bindings, list) or len(bindings) != LEAF_CATALOG_COUNT:
        raise CoordinatorError("Stage 4A leaf union count differs")
    plan_members = {
        str(member["record_id"]): member
        for shard in _stage4a_plan_shards(plan, plan_raw)
        for member in shard["records"]
    }
    resolved_root = allowed_root.resolve() if allowed_root is not None else None
    if resolved_root is not None:
        try:
            archive_path.relative_to(resolved_root)
        except ValueError as exc:
            raise CoordinatorError("Stage 4A candidate archive escapes its output root") from exc
    made: dict[str, dict[str, Any]] = {}
    seen_paths: set[str] = set()
    for index, (raw_binding, entry) in enumerate(zip(bindings, leaves)):
        location = f"$.leaf_union.proofs[{index}]"
        binding = _exact(
            raw_binding,
            {
                "attempt_sha256",
                "authorization_sha256",
                "byte_count",
                "leaf_assignment_sha256",
                "leaf_id",
                "path",
                "request_command_sha256",
                "request_id",
                "result_sha256",
                "sha256",
                "termination_proven",
                "wave_receipt_sha256",
            },
            location,
        )
        if (
            binding["leaf_id"] != entry["leaf_id"]
            or binding["leaf_assignment_sha256"]
            != entry["leaf_assignment_sha256"]
            or binding["termination_proven"] is not True
        ):
            raise CoordinatorError("Stage 4A leaf union order or assignment differs")
        path, raw = _validate_external_file_binding(
            {
                "byte_count": binding["byte_count"],
                "path": binding["path"],
                "sha256": binding["sha256"],
            },
            location,
        )
        if resolved_root is not None:
            try:
                path.relative_to(resolved_root)
            except ValueError as exc:
                raise CoordinatorError("Stage 4A leaf proof escapes its output root") from exc
        if str(path) in seen_paths:
            raise CoordinatorError("Stage 4A leaf union aliases one proof path")
        seen_paths.add(str(path))
        value = strict_json_bytes(raw, str(path))
        member = plan_members[str(entry["assignment"]["record_id"])]
        proof = validate_stage4a_leaf_proof(
            value,
            raw,
            entry=entry,
            member=member,
        )
        made[str(entry["leaf_id"])] = {
            "document": proof,
            "path": path,
            "raw": raw,
        }
    if len(made) != LEAF_CATALOG_COUNT:
        raise CoordinatorError("Stage 4A leaf union is incomplete")
    return {"proofs": made, "union": bound, "union_raw": union_raw}


def reconstruct_stage4a_diagonal_documents(
    plan: Mapping[str, Any],
    plan_raw: bytes,
    validated_union: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Reconstruct the three legacy checker inputs without recomputation."""

    union = validated_union.get("union")
    if not isinstance(union, dict) or not isinstance(
        union.get("candidate_authority"), dict
    ):
        raise CoordinatorError("Stage 4A validated union candidate authority is absent")
    catalog = build_stage4a_leaf_catalog(
        plan,
        plan_raw,
        **union["candidate_authority"],
    )
    leaves = _validate_stage4a_leaf_catalog(catalog)
    proofs = validated_union.get("proofs")
    if not isinstance(proofs, dict) or set(proofs) != {
        str(leaf["leaf_id"]) for leaf in leaves
    }:
        raise CoordinatorError("Stage 4A validated leaf union coverage differs")
    by_assignment: dict[
        str, dict[int, dict[str, tuple[Mapping[str, Any], Mapping[str, Any]]]]
    ] = {assignment_id: {} for assignment_id in EXPECTED_SHARDS}
    protocol: Mapping[str, Any] | None = None
    for leaf in leaves:
        stored = proofs[str(leaf["leaf_id"])]
        if not isinstance(stored, dict) or not isinstance(stored.get("document"), dict):
            raise CoordinatorError("Stage 4A validated leaf proof is malformed")
        document = stored["document"]
        payload = document["scientific_payload"]
        if protocol is None:
            protocol = payload["protocol"]
        elif payload["protocol"] != protocol:
            raise CoordinatorError("Stage 4A leaf scientific protocols disagree")
        assignment = leaf["assignment"]
        logical_index = assignment["logical_record_index"]
        role = assignment["computation_role"]
        roles = by_assignment[str(assignment["parent_assignment_id"])].setdefault(
            logical_index, {}
        )
        if role in roles:
            raise CoordinatorError("Stage 4A diagonal role is duplicated")
        roles[role] = (leaf, payload)
    if protocol is None:
        raise CoordinatorError("Stage 4A leaf protocol is absent")
    made: dict[str, dict[str, Any]] = {}
    plan_digest = sha256(plan_raw)
    shards = _stage4a_plan_shards(plan, plan_raw)
    for shard in shards:
        assignment_id = str(shard["assignment_id"])
        role_groups = by_assignment[assignment_id]
        logical_indices = [
            next(
                leaf["assignment"]["logical_record_index"]
                for leaf in leaves
                if leaf["assignment"]["record_id"] == member["record_id"]
            )
            for member in shard["records"]
        ]
        if (
            set(role_groups) != set(logical_indices)
            or len(role_groups) != 27
        ):
            raise CoordinatorError("Stage 4A diagonal leaf order differs")
        classifying: list[Mapping[str, Any]] = []
        for member, logical_index in zip(shard["records"], logical_indices):
            roles = role_groups[logical_index]
            if set(roles) != {LEAF_V2_ROLE}:
                raise CoordinatorError("Stage 4A diagonal V2 coverage differs")
            v2_leaf, v2_payload = roles[LEAF_V2_ROLE]
            if v2_leaf["assignment"]["record_id"] != member["record_id"]:
                raise CoordinatorError("Stage 4A diagonal classifying order differs")
            classifying.append(v2_payload["record"])
        if len(classifying) != 27:
            raise CoordinatorError("Stage 4A diagonal classifying coverage differs")
        payload = {
            "assignment_id": assignment_id,
            "classifying_records": classifying,
            "diagonal": shard["diagonal"],
            "phase": "4A",
            "protocol": protocol,
            "schema": DIAGONAL_PAYLOAD_SCHEMA,
            "scope": "full",
            "v1_comparator_diagnostics": [],
            "v1_comparator_disposition": LEAF_V1_DISPOSITION,
        }
        record_ids = [str(member["record_id"]) for member in shard["records"]]
        made[assignment_id] = {
            "assignment_sha256": shard["assignment_sha256"],
            "plan_sha256": plan_digest,
            "record_count": 27,
            "record_ids": record_ids,
            "record_ids_sha256": sha256(canonical_bytes(record_ids)),
            "schema": DIAGONAL_SCIENTIFIC_SCHEMA,
            "scientific_payload": payload,
            "scientific_payload_sha256": sha256(canonical_bytes(payload)),
            "selector": LEAF_SELECTOR,
            "terminal": LEAF_PROOF_TERMINAL,
        }
    if set(made) != set(EXPECTED_SHARDS):
        raise CoordinatorError("Stage 4A diagonal reconstruction coverage differs")
    return made


def publish_stage4a_diagonal_documents(
    documents: Mapping[str, Mapping[str, Any]], output_root: Path
) -> dict[str, dict[str, Any]]:
    """Exclusively publish the three reconstructed legacy proof documents."""

    if list(documents) != list(EXPECTED_SHARDS):
        raise CoordinatorError("Stage 4A reconstructed proof order differs")
    made: dict[str, dict[str, Any]] = {}
    for assignment_id in EXPECTED_SHARDS:
        document = documents[assignment_id]
        raw = canonical_bytes(dict(document))
        path = (
            output_root
            / "reconstructed-diagonal-proofs"
            / assignment_id
            / "scientific.json"
        ).resolve()
        path = _contained_leaf_output(
            path, output_root.resolve(), "reconstructed diagonal proof"
        )
        _write_exclusive(path, raw)
        made[assignment_id] = {
            "assignment_sha256": document["assignment_sha256"],
            "plan_sha256": document["plan_sha256"],
            "proof_path": str(path),
            "proof_sha256": sha256(raw),
        }
    return made


def _validate_stage4a_plan_raw(
    plan_raw: bytes, *, label: str
) -> tuple[Mapping[str, Any], bytes]:
    funnel = _load_module("_s3_v2_stage4a_leaf_finalizer_funnel", FUNNEL_PATH)
    manifest_value, manifest_raw = funnel.strict_json_load(MANIFEST_PATH)
    records = funnel.validate_manifest(manifest_value, manifest_raw)
    plan_value = funnel.strict_json_bytes(plan_raw, label=label)
    try:
        plan = funnel.validate_phase_plan(plan_value, plan_raw, records, "4A")
    except Exception as exc:
        raise CoordinatorError(f"Stage 4A leaf plan validation failed: {exc}") from exc
    # Revalidate through the coordinator's independently authored catalog view.
    _stage4a_plan_shards(plan, plan_raw)
    return plan, plan_raw


def _load_validated_stage4a_plan(plan_path: Path) -> tuple[Mapping[str, Any], bytes]:
    return _validate_stage4a_plan_raw(
        plan_path.read_bytes(), label=str(plan_path)
    )


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
        or v1_count != 0
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
        aggregate["schema"] != HISTORICAL_AGGREGATE_SCHEMA
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
        aggregate["schema"] != HISTORICAL_AGGREGATE_SCHEMA
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
        "historical_v1_comparator_disposition": LEAF_V1_DISPOSITION,
        "records_per_diagonal_shard": 27,
        "v1_diagnostic_records": 0,
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
    execution_mode: str,
    plan_path: Path | None = None,
    leaf_union_path: Path | None = None,
    plan_sha256: str | None = None,
    leaf_union_sha256: str | None = None,
    leaf_wave_index: int | None = None,
    leaf_catalog_sha256: str | None = None,
    leaf_wave_manifest_sha256: str | None = None,
    leaf_wave_result_path: Path | None = None,
) -> str:
    if execution_mode == "legacy":
        raise CoordinatorError(
            "legacy Stage 4A execution is not authorized by correction 6"
        )
    if execution_mode not in {"leaf-finalizer", "leaf-wave"}:
        raise CoordinatorError("unregistered Stage 4A execution mode")
    if execution_mode == "leaf-finalizer":
        if (
            plan_path is None
            or leaf_union_path is None
            or plan_sha256 is None
            or leaf_union_sha256 is None
            or any(
                value is not None
                for value in (
                    leaf_wave_index,
                    leaf_catalog_sha256,
                    leaf_wave_manifest_sha256,
                    leaf_wave_result_path,
                )
            )
        ):
            raise CoordinatorError(
                "leaf finalizer command requires exact plan/union paths and hashes"
            )
        _digest(plan_sha256, "finalizer plan hash")
        _digest(leaf_union_sha256, "finalizer union hash")
    elif (
        leaf_wave_index is None
        or leaf_catalog_sha256 is None
        or leaf_wave_manifest_sha256 is None
        or plan_sha256 is None
        or leaf_wave_result_path is None
        or plan_path is not None
        or leaf_union_path is not None
        or leaf_union_sha256 is not None
    ):
        raise CoordinatorError("leaf wave command inputs are incomplete")
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
        _powershell_quote(
            "--finalize-leaf-union"
            if execution_mode == "leaf-finalizer"
            else "--run-leaf-wave"
        ),
        _powershell_quote("--contract"),
        _powershell_quote(contract_path.resolve()),
        _powershell_quote("--authorization"),
        _powershell_quote(authorization_path.resolve()),
        _powershell_quote("--output-root"),
        _powershell_quote(output_root.resolve()),
        _powershell_quote("--aggregate"),
        _powershell_quote(aggregate_path.resolve()),
    ]
    if execution_mode == "leaf-finalizer":
        assert (
            plan_path is not None
            and leaf_union_path is not None
            and plan_sha256 is not None
            and leaf_union_sha256 is not None
        )
        parts.extend(
            [
                _powershell_quote("--plan"),
                _powershell_quote(plan_path.resolve()),
                _powershell_quote("--leaf-union"),
                _powershell_quote(leaf_union_path.resolve()),
                _powershell_quote("--plan-sha256"),
                _powershell_quote(plan_sha256),
                _powershell_quote("--leaf-union-sha256"),
                _powershell_quote(leaf_union_sha256),
            ]
        )
    elif execution_mode == "leaf-wave":
        assert (
            leaf_wave_index is not None
            and plan_sha256 is not None
            and leaf_catalog_sha256 is not None
            and leaf_wave_manifest_sha256 is not None
            and leaf_wave_result_path is not None
        )
        parts.extend(
            [
                _powershell_quote("--leaf-wave-index"),
                _powershell_quote(str(leaf_wave_index)),
                _powershell_quote("--plan-sha256"),
                _powershell_quote(plan_sha256),
                _powershell_quote("--leaf-catalog-sha256"),
                _powershell_quote(leaf_catalog_sha256),
                _powershell_quote("--leaf-wave-manifest-sha256"),
                _powershell_quote(leaf_wave_manifest_sha256),
                _powershell_quote("--leaf-wave-result"),
                _powershell_quote(leaf_wave_result_path.resolve()),
            ]
        )
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


def _validate_leaf_wave_authorization_v5(
    *,
    path: Path,
    value: Mapping[str, Any],
    raw: bytes,
    contract_path: Path,
    contract_raw: bytes,
    selected_wave_index: int,
    selected_plan_sha256: str,
    selected_leaf_catalog_sha256: str,
    selected_manifest_sha256: str,
    selected_result_path: Path,
) -> tuple[Mapping[str, Any], bytes]:
    """Select one of 41 immutable requests from tracked wave authority."""

    if path.resolve() != LEAF_WAVE_AUTHORIZATION_PATH.resolve():
        raise CoordinatorError("leaf wave authorization path differs")

    authorization = _exact(
        value,
        {
            "contract_path",
            "contract_sha256",
            "formal_execution_authorized",
            "implementation_reviews",
            "leaf_waves",
            "resource_lock_required",
            "schema",
            "user_approval",
        },
        "$leaf_wave_authorization",
    )
    contract = strict_json_bytes(contract_raw, str(contract_path))
    if (
        authorization["schema"] != LEAF_WAVE_AUTHORIZATION_SCHEMA
        or authorization["formal_execution_authorized"] is not True
        or authorization["resource_lock_required"] is not True
        or _repo_relative_path(
            authorization["contract_path"],
            "$.leaf_wave_authorization.contract_path",
        )
        != contract_path.resolve()
        or authorization["contract_sha256"] != sha256(contract_raw)
    ):
        raise CoordinatorError("leaf wave authorization identity differs")
    user_approval = _exact(
        authorization["user_approval"],
        {"recorded", "source"},
        "$.leaf_wave_authorization.user_approval",
    )
    if (
        user_approval["recorded"] is not True
        or not isinstance(user_approval["source"], str)
        or not user_approval["source"]
    ):
        raise CoordinatorError("leaf wave user approval is not recorded")
    reviews = authorization["implementation_reviews"]
    if not isinstance(reviews, list) or len(reviews) != 2:
        raise CoordinatorError("two leaf wave implementation reviews are required")
    expected_paths = {
        "PROCESS_AND_AUTHORITY": PROCESS_REVIEW_PATH.resolve(),
        "SCIENTIFIC_AND_MECHANICS": SCIENTIFIC_REVIEW_PATH.resolve(),
    }
    expected_inputs = _review_inputs(contract, contract_raw)
    reviewer_ids: set[str] = set()
    observed_roles: list[str] = []
    for index, raw_review in enumerate(reviews):
        binding = _exact(
            raw_review,
            {"path", "role", "sha256", "verdict"},
            f"$.leaf_wave_authorization.reviews[{index}]",
        )
        role = str(binding["role"])
        if role not in EXPECTED_REVIEW_VERDICTS or role in observed_roles:
            raise CoordinatorError("leaf wave review role is missing or duplicated")
        review_path = _repo_relative_path(binding["path"], "$.leaf_wave_review.path")
        if review_path != expected_paths[role]:
            raise CoordinatorError("leaf wave review path differs")
        review_value, review_raw = _validate_review(
            review_path, role=role, expected_inputs=expected_inputs
        )
        if (
            binding["sha256"] != sha256(review_raw)
            or binding["verdict"] != EXPECTED_REVIEW_VERDICTS[role]
        ):
            raise CoordinatorError("leaf wave review binding differs")
        reviewer_ids.add(review_value["reviewer_independence"]["reviewer_id"])
        observed_roles.append(role)
    if observed_roles != list(EXPECTED_REVIEW_VERDICTS) or len(reviewer_ids) != 2:
        raise CoordinatorError("leaf wave reviews are not distinct and ordered")

    raw_waves = authorization["leaf_waves"]
    if not isinstance(raw_waves, list) or len(raw_waves) != LEAF_WAVE_COUNT:
        raise CoordinatorError(
            f"leaf wave authorization must bind exactly {LEAF_WAVE_COUNT} waves"
        )
    seen_request_ids: set[str] = set()
    seen_approval_snapshots: set[Path] = set()
    seen_receipts: set[Path] = set()
    seen_results: set[Path] = set()
    selected: Mapping[str, Any] | None = None
    try:
        ledger_lines = RESOURCE_LEDGER_PATH.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CoordinatorError(f"cannot inspect resource ledger: {exc}") from exc
    wave_keys = {
        "execution_paths",
        "leaf_catalog_sha256",
        "leaf_wave_manifest_sha256",
        "leaf_wave_result_path",
        "ledger_approval",
        "plan_sha256",
        "resource_request",
        "wave_index",
    }
    for index, raw_wave in enumerate(raw_waves, start=1):
        wave = _exact(
            raw_wave,
            wave_keys,
            f"$.leaf_wave_authorization.leaf_waves[{index - 1}]",
        )
        if wave["wave_index"] != index:
            raise CoordinatorError("leaf wave authorization order differs")
        plan_digest = _digest(wave["plan_sha256"], "$.leaf_wave.plan_sha256")
        catalog_digest = _digest(
            wave["leaf_catalog_sha256"], "$.leaf_wave.catalog_sha256"
        )
        manifest_digest = _digest(
            wave["leaf_wave_manifest_sha256"], "$.leaf_wave.manifest_sha256"
        )
        execution = _exact(
            wave["execution_paths"],
            {
                "aggregate_path",
                "approval_snapshot_path",
                "output_root",
                "python_executable",
            },
            "$.leaf_wave.execution_paths",
        )
        python_executable = Path(str(execution["python_executable"])).resolve()
        output_root = Path(str(execution["output_root"])).resolve()
        receipt_path = Path(str(execution["aggregate_path"])).resolve()
        approval_snapshot_path = Path(
            str(execution["approval_snapshot_path"])
        ).resolve()
        result_path = Path(str(wave["leaf_wave_result_path"])).resolve()
        try:
            receipt_path.relative_to(output_root)
            approval_snapshot_path.relative_to(output_root)
            result_path.relative_to(output_root)
        except ValueError as exc:
            raise CoordinatorError("leaf wave execution path escapes its output root") from exc
        if (
            not python_executable.is_file()
            or approval_snapshot_path in seen_approval_snapshots
            or receipt_path in seen_receipts
            or result_path in seen_results
            or len({approval_snapshot_path, receipt_path, result_path}) != 3
        ):
            raise CoordinatorError("leaf wave execution path differs or is duplicated")
        seen_approval_snapshots.add(approval_snapshot_path)
        seen_receipts.add(receipt_path)
        seen_results.add(result_path)
        request = _exact(
            wave["resource_request"],
            {
                "command_sha256",
                "request_id",
                "request_path",
                "request_sha256",
                "repository",
                "task",
            },
            "$.leaf_wave.resource_request",
        )
        request_id = request["request_id"]
        request_path = Path(str(request["request_path"]))
        if (
            not isinstance(request_id, str)
            or len(request_id) != 32
            or any(character not in "0123456789abcdef" for character in request_id)
            or request_id in seen_request_ids
            or request_path.resolve()
            != (RESOURCE_MANAGER_ROOT / "requests" / f"{request_id}.json").resolve()
            or not request_path.is_file()
            or request_path.is_symlink()
        ):
            raise CoordinatorError("leaf wave request ID/path is invalid or reused")
        seen_request_ids.add(request_id)
        request_value, request_raw = _strict_external_json(
            request_path, f"leaf wave request {index}"
        )
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
            "$.leaf_wave.request_file",
        )
        expected_command = expected_resource_command(
            python_executable=python_executable,
            contract_path=contract_path,
            authorization_path=path,
            output_root=output_root,
            aggregate_path=receipt_path,
            execution_mode="leaf-wave",
            plan_sha256=plan_digest,
            leaf_wave_index=index,
            leaf_catalog_sha256=catalog_digest,
            leaf_wave_manifest_sha256=manifest_digest,
            leaf_wave_result_path=result_path,
        )
        expected_task = (
            f"ANYsolver S3 V2A Stage 4A bounded leaf wave {index:02d}"
        )
        if (
            request_value["request_id"] != request_id
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
            raise CoordinatorError("leaf wave request content differs")
        approval = _exact(
            wave["ledger_approval"],
            {"approved_row_sha256", "ledger_path", "snapshot_path", "snapshot_sha256"},
            "$.leaf_wave.ledger_approval",
        )
        if approval["ledger_path"] != str(RESOURCE_LEDGER_PATH):
            raise CoordinatorError("leaf wave ledger path differs")
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
            or ledger_lines.count(snapshot["approved_row"]["line"]) != 1
        ):
            raise CoordinatorError("leaf wave approval binding differs")
        if index == selected_wave_index:
            selected = {
                "contract_path": authorization["contract_path"],
                "contract_sha256": authorization["contract_sha256"],
                "execution_paths": execution,
                "formal_execution_authorized": True,
                "implementation_reviews": reviews,
                "leaf_catalog_sha256": catalog_digest,
                "leaf_wave_manifest_sha256": manifest_digest,
                "leaf_wave_result_path": str(result_path),
                "ledger_approval": approval,
                "plan_sha256": plan_digest,
                "resource_lock_required": True,
                "resource_request": request,
                "schema": LEAF_WAVE_AUTHORIZATION_SCHEMA,
                "user_approval": user_approval,
                "wave_index": index,
            }
            if (
                plan_digest != selected_plan_sha256
                or catalog_digest != selected_leaf_catalog_sha256
                or manifest_digest != selected_manifest_sha256
                or result_path != selected_result_path.resolve()
            ):
                raise CoordinatorError("selected leaf wave command inputs differ")
    if selected is None:
        raise CoordinatorError("selected leaf wave authorization is absent")
    return selected, raw


def _validate_completed_leaf_wave_ledger_row(
    request_id: str,
    request_value: Mapping[str, Any],
    *,
    receipt_raw: bytes,
) -> dict[str, str]:
    """Bind one consumed leaf request to its unique successful terminal row."""

    try:
        ledger_lines = RESOURCE_LEDGER_PATH.read_text(
            encoding="utf-8-sig"
        ).splitlines()
    except (OSError, UnicodeError) as exc:
        raise CoordinatorError(f"cannot inspect resource ledger: {exc}") from exc
    matching = [line for line in ledger_lines if f"| {request_id} |" in line]
    parsed: list[tuple[str, str]] = []
    for line in matching:
        fields = line.split("|")
        if len(fields) < 6:
            raise CoordinatorError("leaf wave resource ledger row is malformed")
        status = fields[3].strip()
        if (
            fields[2].strip() != request_id
            or fields[4].strip() != request_value["task"]
            or fields[5].strip() != request_value["repository"]
        ):
            raise CoordinatorError("leaf wave resource ledger identity differs")
        parsed.append((status, line))
    statuses = [status for status, _line in parsed]
    if statuses != ["APPROVED", "EXECUTION_STARTED", "COMPLETED_PASS"]:
        raise CoordinatorError(
            "leaf wave resource ledger lacks one ordered COMPLETED_PASS history"
        )
    terminal_line = parsed[-1][1]
    receipt_digest = sha256(receipt_raw)
    if re.search(
        rf"\b(?:aggregate|receipt|result) bytes {len(receipt_raw)} "
        rf"SHA-256 {receipt_digest}\b",
        terminal_line,
        flags=re.IGNORECASE,
    ) is None:
        raise CoordinatorError(
            "leaf wave COMPLETED_PASS row does not bind the exact receipt bytes"
        )
    return {
        "line": terminal_line,
        "sha256": sha256((terminal_line.rstrip() + "\n").encode("utf-8")),
        "status": "COMPLETED_PASS",
    }


def validate_authorization(
    path: Path,
    *,
    contract_path: Path,
    contract_raw: bytes,
    execution_mode: str,
    plan_path: Path | None = None,
    leaf_union_path: Path | None = None,
    plan_sha256: str | None = None,
    leaf_union_sha256: str | None = None,
    leaf_wave_index: int | None = None,
    leaf_catalog_sha256: str | None = None,
    leaf_wave_manifest_sha256: str | None = None,
    leaf_wave_result_path: Path | None = None,
) -> tuple[Mapping[str, Any], bytes]:
    if execution_mode == "legacy":
        raise CoordinatorError(
            "legacy Stage 4A execution is not authorized by correction 6"
        )
    if execution_mode not in {"leaf-finalizer", "leaf-wave"}:
        raise CoordinatorError("unregistered Stage 4A execution mode")
    value, raw = strict_json_load(path)
    if raw != canonical_bytes(value):
        raise CoordinatorError("execution authorization is not canonical JSON")
    if execution_mode == "leaf-wave":
        if path.resolve() != LEAF_WAVE_AUTHORIZATION_PATH.resolve():
            raise CoordinatorError("leaf wave authorization path differs")
        if (
            not isinstance(value, dict)
            or value.get("schema") != LEAF_WAVE_AUTHORIZATION_SCHEMA
        ):
            raise CoordinatorError("leaf wave authorization schema differs")
        if (
            leaf_wave_index is None
            or plan_sha256 is None
            or leaf_catalog_sha256 is None
            or leaf_wave_manifest_sha256 is None
            or leaf_wave_result_path is None
        ):
            raise CoordinatorError("selected leaf wave authorization inputs are absent")
        return _validate_leaf_wave_authorization_v5(
            path=path,
            value=value,
            raw=raw,
            contract_path=contract_path,
            contract_raw=contract_raw,
            selected_wave_index=leaf_wave_index,
            selected_plan_sha256=plan_sha256,
            selected_leaf_catalog_sha256=leaf_catalog_sha256,
            selected_manifest_sha256=leaf_wave_manifest_sha256,
            selected_result_path=leaf_wave_result_path,
        )
    if (
        execution_mode == "leaf-finalizer"
        and path.resolve() != EXECUTION_AUTHORIZATION_PATH.resolve()
    ):
        raise CoordinatorError("leaf finalizer execution authorization path differs")
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
        execution_mode=execution_mode,
        plan_path=plan_path,
        leaf_union_path=leaf_union_path,
        plan_sha256=plan_sha256,
        leaf_union_sha256=leaf_union_sha256,
        leaf_wave_index=leaf_wave_index,
        leaf_catalog_sha256=leaf_catalog_sha256,
        leaf_wave_manifest_sha256=leaf_wave_manifest_sha256,
        leaf_wave_result_path=leaf_wave_result_path,
    )
    expected_task = (
        "ANYsolver S3 V2A Stage 4A bounded leaf finalizer"
        if execution_mode == "leaf-finalizer"
        else f"ANYsolver S3 V2A Stage 4A bounded leaf wave {leaf_wave_index:02d}"
    )
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
    raise CoordinatorError(
        "legacy Stage 4A preparation is not authorized by correction 6"
    )


def _historical_prepare_wave(
    contract_path: Path,
    output_root: Path,
    *,
    authorization_path: Path | None = None,
) -> dict[str, Path]:
    """Retain the obsolete monolithic preparation for history inspection only."""

    raise CoordinatorError(
        "historical Stage 4A preparation is not executable under correction 6"
    )

    _coordinator_checkpoint()
    contract, contract_raw = validate_contract(contract_path)
    _coordinator_checkpoint()
    if authorization_path is not None:
        validate_authorization(
            authorization_path,
            contract_path=contract_path,
            contract_raw=contract_raw,
            execution_mode="legacy",
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


def _build_stage4a_leaf_wave_manifest(
    *,
    wave: Mapping[str, Any],
    catalog: Mapping[str, Any],
    plan_path: Path,
    candidate_source_root: Path,
    candidate_archive_path: Path,
    candidate_binding_path: Path,
    contract_path: Path,
    wave_root: Path,
) -> dict[str, Any]:
    leaves = {
        str(leaf["leaf_id"]): leaf
        for leaf in _validate_stage4a_leaf_catalog(catalog)
    }
    wave = _exact(
        wave,
        {
            "leaf_assignment_sha256",
            "leaf_ids",
            "logical_record_indices",
            "record_ids",
            "wave_id",
            "worker_count",
        },
        "$.leaf_wave",
    )
    leaf_ids = wave["leaf_ids"]
    assignment_hashes = wave["leaf_assignment_sha256"]
    if (
        not isinstance(leaf_ids, list)
        or not isinstance(assignment_hashes, list)
        or len(leaf_ids) != wave["worker_count"]
        or len(leaf_ids) not in {1, 2}
        or any(leaf_id not in leaves for leaf_id in leaf_ids)
        or assignment_hashes
        != [leaves[leaf_id]["leaf_assignment_sha256"] for leaf_id in leaf_ids]
    ):
        raise CoordinatorError("leaf wave assignment coverage differs")
    grouped = [leaves[leaf_id]["assignment"] for leaf_id in leaf_ids]
    if (
        wave["logical_record_indices"]
        != [assignment["logical_record_index"] for assignment in grouped]
        or wave["record_ids"]
        != [assignment["record_id"] for assignment in grouped]
        or [assignment["computation_role"] for assignment in grouped]
        != [LEAF_V2_ROLE] * len(grouped)
        or wave["logical_record_indices"]
        != list(
            range(
                wave["logical_record_indices"][0],
                wave["logical_record_indices"][0] + len(grouped),
            )
        )
    ):
        raise CoordinatorError("leaf wave consecutive V2 partition differs")
    plan_digest = sha256(plan_path.read_bytes())
    producer_digest = sha256(PRODUCER_PATH.read_bytes())
    candidate_authority = catalog["candidate_authority"]
    common_input_paths = (
        AUTHORITY_PATH.resolve(),
        MANIFEST_PATH.resolve(),
        SCAFFOLD_CONTRACT_PATH.resolve(),
        SOURCE_CONTRACT_PATH.resolve(),
        candidate_archive_path.resolve(),
        candidate_binding_path.resolve(),
        contract_path.resolve(),
        plan_path.resolve(),
    )
    input_hashes = sorted(
        (
            {"path": str(path), "sha256": sha256(path.read_bytes())}
            for path in common_input_paths
        ),
        key=lambda item: item["path"],
    )
    workers: list[dict[str, Any]] = []
    for leaf_id in leaf_ids:
        leaf = leaves[leaf_id]
        worker_root = (wave_root / leaf_id).resolve()
        scientific_path = worker_root / "scientific.json"
        progress_path = worker_root / "progress.jsonl"
        command = [
            str(Path(sys.executable).resolve()),
            str(PRODUCER_PATH.resolve()),
            "--run-flat-leaf",
            str(plan_path.resolve()),
            "--leaf-assignment-sha256",
            str(leaf["leaf_assignment_sha256"]),
            "--selector",
            LEAF_SELECTOR,
            "--candidate-source-root",
            str(candidate_source_root.resolve()),
            "--candidate-archive",
            str(candidate_archive_path.resolve()),
            "--candidate-archive-sha256",
            str(candidate_authority["candidate_archive_sha256"]),
            "--candidate-commit",
            str(candidate_authority["candidate_commit"]),
            "--candidate-tree",
            str(candidate_authority["candidate_tree"]),
            "--producer-program-sha256",
            str(candidate_authority["producer_program_sha256"]),
            "--output",
            str(scientific_path),
            "--progress",
            str(progress_path),
        ]
        workers.append(
            {
                "assignment_id": leaf_id,
                "assignment_sha256": leaf["leaf_assignment_sha256"],
                "command": command,
                "cwd": str(ROOT.resolve()),
                "expected_record_count": 1,
                "expected_selector": LEAF_SELECTOR,
                "input_hashes": input_hashes,
                "plan_path": str(plan_path.resolve()),
                "plan_sha256": plan_digest,
                "program_path": str(PRODUCER_PATH.resolve()),
                "program_sha256": producer_digest,
                "progress_path": str(progress_path),
                "scientific_path": str(scientific_path),
                "scientific_schema": LEAF_SCIENTIFIC_SCHEMA,
                "stderr_path": str(worker_root / "stderr.log"),
                "stdout_path": str(worker_root / "stdout.log"),
                "wall_seconds": LEAF_WORKER_WALL_SECONDS,
            }
        )
    return {
        "lane": "flat-leaf",
        "output_root": str(wave_root.resolve()),
        "schema": "anysolver.e4-pl-s3-v2-bounded-wave-manifest-v1",
        "wave_id": wave["wave_id"],
        "workers": workers,
    }


def prepare_stage4a_leaf_cycle(
    contract_path: Path, output_root: Path
) -> dict[str, Any]:
    """Prepare 81 immutable V2 assignments in 41 executable bounded waves."""

    _coordinator_checkpoint()
    contract, _contract_raw = validate_contract(contract_path)
    funnel = _load_module("_s3_v2_stage4a_leaf_prepare_funnel", FUNNEL_PATH)
    manifest_value, manifest_raw = funnel.strict_json_load(MANIFEST_PATH)
    records = funnel.validate_manifest(manifest_value, manifest_raw)
    plan = funnel.build_phase_plan(records, "4A")
    plan_path = (output_root / "phase4a-plan.json").resolve()
    _write_exclusive(plan_path, funnel.canonical_bytes(plan))
    archive_path = (output_root / "candidate-source.tar").resolve()
    _publish_candidate_archive(archive_path, str(contract["candidate"]["commit"]))
    archive_digest = sha256(archive_path.read_bytes())
    candidate_source_root = _extract_candidate_archive(archive_path, output_root)
    binding = {
        "artifact_path": str(archive_path),
        "artifact_sha256": archive_digest,
        "candidate_id": "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1",
        "commit": contract["candidate"]["commit"],
        "formulation_id": "E4_PL_QUALIFIED_S3_COMPANION_V2",
        "schema": "anysolver.e4-pl-s3-v2-flat-candidate-binding-v1",
        "selector": LEAF_SELECTOR,
        "tree": contract["candidate"]["tree"],
    }
    binding_path = (output_root / "candidate-source-binding.json").resolve()
    _write_exclusive(binding_path, canonical_bytes(binding))
    candidate_authority = _leaf_candidate_authority(
        candidate_commit=contract["candidate"]["commit"],
        candidate_tree=contract["candidate"]["tree"],
        candidate_archive_sha256=archive_digest,
        producer_program_sha256=sha256(PRODUCER_PATH.read_bytes()),
    )
    catalog = build_stage4a_leaf_catalog(
        plan,
        plan_path.read_bytes(),
        **candidate_authority,
    )
    catalog_path = (output_root / "stage4a-leaf-catalog.json").resolve()
    _write_exclusive(catalog_path, canonical_bytes(catalog))
    wave_catalog = build_stage4a_leaf_wave_catalog(catalog)
    wave_catalog_path = (output_root / "stage4a-leaf-wave-catalog.json").resolve()
    _write_exclusive(wave_catalog_path, canonical_bytes(wave_catalog))
    manifests: list[Path] = []
    for wave_index, wave in enumerate(wave_catalog["waves"], start=1):
        _coordinator_checkpoint()
        wave_root = (output_root / "leaf-waves" / f"wave-{wave_index:02d}").resolve()
        manifest = _build_stage4a_leaf_wave_manifest(
            wave=wave,
            catalog=catalog,
            plan_path=plan_path,
            candidate_source_root=candidate_source_root,
            candidate_archive_path=archive_path,
            candidate_binding_path=binding_path,
            contract_path=contract_path,
            wave_root=wave_root,
        )
        manifest_path = (wave_root / "manifest.json").resolve()
        _write_exclusive(manifest_path, canonical_bytes(manifest))
        manifests.append(manifest_path)
    return {
        "archive": archive_path,
        "binding": binding_path,
        "candidate_source_root": candidate_source_root,
        "catalog": catalog_path,
        "manifests": manifests,
        "plan": plan_path,
        "wave_catalog": wave_catalog_path,
    }


def _validate_stage4a_leaf_cycle(
    *,
    contract: Mapping[str, Any],
    contract_path: Path,
    output_root: Path,
    wave_index: int,
) -> dict[str, Any]:
    if (
        isinstance(wave_index, bool)
        or not isinstance(wave_index, int)
        or not 1 <= wave_index <= LEAF_WAVE_COUNT
    ):
        raise CoordinatorError(
            f"leaf wave index is outside 1..{LEAF_WAVE_COUNT}"
        )
    plan_path = _contained_leaf_finalizer_input(
        (output_root / "phase4a-plan.json").resolve(), output_root, "leaf plan"
    )
    plan, plan_raw = _load_validated_stage4a_plan(plan_path)
    binding_path = _contained_leaf_finalizer_input(
        (output_root / "candidate-source-binding.json").resolve(),
        output_root,
        "candidate binding",
    )
    binding, binding_raw = strict_json_load(binding_path)
    if binding_raw != canonical_bytes(binding):
        raise CoordinatorError("leaf candidate binding is not canonical JSON")
    binding = _exact(
        binding,
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
        "$.leaf_candidate_binding",
    )
    archive_path = _contained_leaf_finalizer_input(
        Path(str(binding["artifact_path"])), output_root, "candidate archive"
    )
    archive_raw = archive_path.read_bytes()
    if (
        binding["schema"] != "anysolver.e4-pl-s3-v2-flat-candidate-binding-v1"
        or binding["candidate_id"] != "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1"
        or binding["formulation_id"] != "E4_PL_QUALIFIED_S3_COMPANION_V2"
        or binding["selector"] != LEAF_SELECTOR
        or binding["commit"] != contract["candidate"]["commit"]
        or binding["tree"] != contract["candidate"]["tree"]
        or binding["artifact_sha256"] != sha256(archive_raw)
        or not archive_raw
    ):
        raise CoordinatorError("leaf candidate binding differs from contract/archive")
    candidate_authority = _leaf_candidate_authority(
        candidate_commit=binding["commit"],
        candidate_tree=binding["tree"],
        candidate_archive_sha256=binding["artifact_sha256"],
        producer_program_sha256=sha256(PRODUCER_PATH.read_bytes()),
    )
    catalog_path = _contained_leaf_finalizer_input(
        (output_root / "stage4a-leaf-catalog.json").resolve(),
        output_root,
        "leaf catalog",
    )
    catalog, catalog_raw = strict_json_load(catalog_path)
    expected_catalog = build_stage4a_leaf_catalog(
        plan, plan_raw, **candidate_authority
    )
    if catalog_raw != canonical_bytes(catalog) or catalog != expected_catalog:
        raise CoordinatorError("stored leaf catalog differs from frozen inputs")
    wave_catalog_path = _contained_leaf_finalizer_input(
        (output_root / "stage4a-leaf-wave-catalog.json").resolve(),
        output_root,
        "leaf wave catalog",
    )
    wave_catalog, wave_catalog_raw = strict_json_load(wave_catalog_path)
    expected_wave_catalog = build_stage4a_leaf_wave_catalog(catalog)
    if (
        wave_catalog_raw != canonical_bytes(wave_catalog)
        or wave_catalog != expected_wave_catalog
    ):
        raise CoordinatorError("stored leaf wave catalog differs from leaf catalog")
    candidate_source_root = (output_root / "candidate-source-tree").resolve()
    if not candidate_source_root.is_dir() or candidate_source_root.is_symlink():
        raise CoordinatorError("leaf candidate source tree is absent or aliased")
    wave_root = (output_root / "leaf-waves" / f"wave-{wave_index:02d}").resolve()
    manifest_path = _contained_leaf_finalizer_input(
        (wave_root / "manifest.json").resolve(), output_root, "leaf wave manifest"
    )
    manifest, manifest_raw = strict_json_load(manifest_path)
    expected_manifest = _build_stage4a_leaf_wave_manifest(
        wave=wave_catalog["waves"][wave_index - 1],
        catalog=catalog,
        plan_path=plan_path,
        candidate_source_root=candidate_source_root,
        candidate_archive_path=archive_path,
        candidate_binding_path=binding_path,
        contract_path=contract_path,
        wave_root=wave_root,
    )
    if manifest_raw != canonical_bytes(manifest) or manifest != expected_manifest:
        raise CoordinatorError("stored leaf wave manifest differs from frozen inputs")
    return {
        "archive": archive_path,
        "binding": binding_path,
        "candidate_authority": candidate_authority,
        "catalog": catalog,
        "catalog_path": catalog_path,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "plan": plan,
        "plan_path": plan_path,
        "plan_raw": plan_raw,
        "wave": wave_catalog["waves"][wave_index - 1],
        "wave_catalog": wave_catalog,
        "wave_catalog_path": wave_catalog_path,
        "wave_root": wave_root,
    }


_BOUNDED_WORKER_RESULT_KEYS = {
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


def _validate_stage4a_leaf_wave_result(
    result_path: Path, cycle: Mapping[str, Any]
) -> tuple[Mapping[str, Any], bytes, list[dict[str, Any]]]:
    result, result_raw = strict_json_load(result_path)
    if result_raw != canonical_bytes(result):
        raise CoordinatorError("leaf bounded-wave result is not canonical JSON")
    result = _exact(
        result,
        {"lane", "manifest_sha256", "schema", "terminal", "wave_id", "workers"},
        "$.leaf_wave_result",
    )
    manifest = cycle["manifest"]
    workers = result["workers"]
    if (
        result["schema"] != PRODUCER_RESULT_SCHEMA
        or result["lane"] != "flat-leaf"
        or result["terminal"] != "COMPLETED"
        or result["wave_id"] != cycle["wave"]["wave_id"]
        or result["manifest_sha256"]
        != sha256(cycle["manifest_path"].read_bytes())
        or not isinstance(workers, list)
        or len(workers) != len(manifest["workers"])
    ):
        raise CoordinatorError("leaf bounded-wave result identity differs")
    leaves = {
        str(leaf["leaf_id"]): leaf for leaf in cycle["catalog"]["leaves"]
    }
    plan_members = {
        str(member["record_id"]): member
        for shard in _stage4a_plan_shards(cycle["plan"], cycle["plan_raw"])
        for member in shard["records"]
    }
    accepted: list[dict[str, Any]] = []
    for index, (raw_worker, spec) in enumerate(zip(workers, manifest["workers"])):
        worker = _exact(
            raw_worker,
            _BOUNDED_WORKER_RESULT_KEYS,
            f"$.leaf_wave_result.workers[{index}]",
        )
        leaf_id = str(spec["assignment_id"])
        leaf = leaves[leaf_id]
        proof_path = Path(str(spec["scientific_path"])).resolve()
        if (
            worker["assignment_id"] != leaf_id
            or worker["assignment_sha256"] != spec["assignment_sha256"]
            or worker["status"] != "COMPLETED"
            or worker["returncode"] != 0
            or worker["termination_proven"] is not True
            or worker["plan_sha256"] != spec["plan_sha256"]
            or worker["program_sha256"] != spec["program_sha256"]
            or worker["input_hashes"] != spec["input_hashes"]
            or worker["scientific_record_count"] != 1
            or worker["scientific_schema"] != LEAF_SCIENTIFIC_SCHEMA
            or worker["scientific_terminal"] != LEAF_PROOF_TERMINAL
            or not proof_path.is_file()
            or proof_path.is_symlink()
        ):
            raise CoordinatorError("leaf bounded worker authority/process result differs")
        proof_raw = proof_path.read_bytes()
        proof_sha = sha256(proof_raw)
        proof_value = strict_json_bytes(proof_raw, str(proof_path))
        member = plan_members[str(leaf["assignment"]["record_id"])]
        validate_stage4a_leaf_proof(
            proof_value,
            proof_raw,
            entry=leaf,
            member=member,
        )
        if (
            worker["scientific_byte_count"] != len(proof_raw)
            or worker["scientific_sha256"] != proof_sha
            or worker["scientific_payload_sha256"]
            != proof_value["scientific_payload_sha256"]
            or worker["scientific_record_ids_sha256"]
            != proof_value["record_ids_sha256"]
        ):
            raise CoordinatorError("leaf bounded worker scientific binding differs")
        accepted.append(
            {
                "assignment_sha256": leaf["leaf_assignment_sha256"],
                "leaf_id": leaf_id,
                "proof": _external_file_binding(proof_path, "leaf scientific proof"),
                "status": "COMPLETED",
                "termination_proven": True,
            }
        )
    return result, result_raw, accepted


def validate_stage4a_leaf_wave_receipt(
    receipt_path: Path,
    *,
    contract: Mapping[str, Any],
    contract_path: Path,
    contract_raw: bytes,
    cycle: Mapping[str, Any],
    wave_index: int,
    allowed_root: Path,
    expected_authorization_path: Path,
    expected_authorization_raw: bytes,
) -> dict[str, Any]:
    """Revalidate a consumed wave's immutable request, attempt, result, and proofs."""

    receipt_path = _contained_leaf_finalizer_input(
        receipt_path, allowed_root, "leaf wave receipt"
    )
    receipt, receipt_raw = strict_json_load(receipt_path)
    if receipt_raw != canonical_bytes(receipt):
        raise CoordinatorError("leaf wave receipt is not canonical JSON")
    receipt = _exact(
        receipt,
        {
            "attempt",
            "authorization",
            "candidate_authority",
            "candidate_authority_sha256",
            "contract",
            "leaf_catalog_sha256",
            "manifest",
            "plan_sha256",
            "request",
            "request_command_sha256",
            "request_id",
            "result",
            "schema",
            "terminal",
            "wave_id",
            "wave_index",
            "workers",
        },
        "$.leaf_wave_receipt",
    )
    candidate_authority = _leaf_candidate_authority(
        **receipt["candidate_authority"]
    )
    if (
        receipt["schema"] != LEAF_WAVE_RECEIPT_SCHEMA
        or receipt["terminal"] != "COMPLETED"
        or receipt["wave_index"] != wave_index
        or receipt["wave_id"] != cycle["wave"]["wave_id"]
        or candidate_authority != cycle["candidate_authority"]
        or receipt["candidate_authority_sha256"]
        != _leaf_candidate_authority_sha256(candidate_authority)
        or receipt["plan_sha256"] != sha256(cycle["plan_raw"])
        or receipt["leaf_catalog_sha256"]
        != sha256(canonical_bytes(cycle["catalog"]))
    ):
        raise CoordinatorError("leaf wave receipt identity differs")
    root = allowed_root.resolve(strict=True)
    bound_files: dict[str, tuple[Path, bytes]] = {}
    for name in ("attempt", "authorization", "contract", "manifest", "request", "result"):
        path, raw = _validate_external_file_binding(
            receipt[name], f"$.leaf_wave_receipt.{name}"
        )
        try:
            path.relative_to(root)
        except ValueError:
            if name not in {"attempt", "request", "contract", "authorization"}:
                raise CoordinatorError(f"leaf wave {name} escapes the cycle root")
        bound_files[name] = (path, raw)
    if (
        bound_files["contract"][0] != contract_path.resolve()
        or bound_files["contract"][1] != contract_raw
        or bound_files["manifest"][0] != cycle["manifest_path"]
        or bound_files["manifest"][1] != cycle["manifest_path"].read_bytes()
    ):
        raise CoordinatorError("leaf wave receipt contract/manifest binding differs")
    result_path, result_raw = bound_files["result"]
    _result, made_result_raw, accepted_workers = _validate_stage4a_leaf_wave_result(
        result_path, cycle
    )
    if made_result_raw != result_raw or receipt["workers"] != accepted_workers:
        raise CoordinatorError("leaf wave receipt workers differ from bounded result")

    request_path, request_raw = bound_files["request"]
    request_value = _exact(
        strict_json_bytes(request_raw, str(request_path)),
        {
            "command",
            "estimate_minutes",
            "repository",
            "request_id",
            "requested_at",
            "status",
            "task",
        },
        "$.leaf_wave_receipt.request_file",
    )
    request_id = receipt["request_id"]
    if (
        request_value["request_id"] != request_id
        or request_value["status"] != "PENDING"
        or request_value["estimate_minutes"] != 30
        or request_value["repository"] != str(ROOT)
        or receipt["request_command_sha256"]
        != sha256(request_value["command"].encode("utf-8"))
    ):
        raise CoordinatorError("leaf wave receipt request binding differs")
    attempt_path, attempt_raw = bound_files["attempt"]
    attempt = _exact(
        strict_json_bytes(attempt_raw, str(attempt_path)),
        {"contract_sha256", "request_id", "schema"},
        "$.leaf_wave_receipt.attempt_file",
    )
    if attempt != {
        "contract_sha256": sha256(contract_raw),
        "request_id": request_id,
        "schema": "anysolver.resource-attempt-claim-v1",
    }:
        raise CoordinatorError("leaf wave receipt attempt binding differs")

    authorization_path, authorization_raw = bound_files["authorization"]
    if (
        authorization_path != expected_authorization_path.resolve()
        or authorization_raw != expected_authorization_raw
    ):
        raise CoordinatorError("leaf wave receipt authorization differs from union authority")
    authorization = _exact(
        strict_json_bytes(authorization_raw, str(authorization_path)),
        {
            "contract_path",
            "contract_sha256",
            "formal_execution_authorized",
            "implementation_reviews",
            "leaf_waves",
            "resource_lock_required",
            "schema",
            "user_approval",
        },
        "$.leaf_wave_receipt.authorization_file",
    )
    if (
        authorization["schema"] != LEAF_WAVE_AUTHORIZATION_SCHEMA
        or authorization["contract_sha256"] != sha256(contract_raw)
        or authorization["formal_execution_authorized"] is not True
        or authorization["resource_lock_required"] is not True
        or not isinstance(authorization["leaf_waves"], list)
        or len(authorization["leaf_waves"]) != LEAF_WAVE_COUNT
    ):
        raise CoordinatorError("leaf wave receipt authorization binding differs")
    selected_authorization, selected_authorization_raw = (
        _validate_leaf_wave_authorization_v5(
            path=authorization_path,
            value=authorization,
            raw=authorization_raw,
            contract_path=contract_path,
            contract_raw=contract_raw,
            selected_wave_index=wave_index,
            selected_plan_sha256=receipt["plan_sha256"],
            selected_leaf_catalog_sha256=receipt["leaf_catalog_sha256"],
            selected_manifest_sha256=receipt["manifest"]["sha256"],
            selected_result_path=result_path,
        )
    )
    if selected_authorization_raw != authorization_raw:
        raise CoordinatorError("leaf wave authorization bytes changed during validation")
    authorized_wave = authorization["leaf_waves"][wave_index - 1]
    authorized_request = authorized_wave.get("resource_request", {})
    expected_request_path = (
        RESOURCE_MANAGER_ROOT / "requests" / f"{request_id}.json"
    ).resolve()
    expected_attempt_path = (
        RESOURCE_MANAGER_ROOT / "attempts" / f"{request_id}.json"
    ).resolve()
    execution_paths = selected_authorization["execution_paths"]
    if (
        authorized_wave.get("wave_index") != wave_index
        or authorized_wave.get("plan_sha256") != receipt["plan_sha256"]
        or authorized_wave.get("leaf_catalog_sha256")
        != receipt["leaf_catalog_sha256"]
        or authorized_wave.get("leaf_wave_manifest_sha256")
        != receipt["manifest"]["sha256"]
        or Path(str(authorized_wave.get("leaf_wave_result_path"))).resolve()
        != result_path
        or authorized_request.get("request_id") != request_id
        or authorized_request.get("request_sha256") != sha256(request_raw)
        or authorized_request.get("command_sha256")
        != receipt["request_command_sha256"]
        or request_path != expected_request_path
        or attempt_path != expected_attempt_path
        or authorization_path != Path(receipt["authorization"]["path"]).resolve()
        or receipt_path.resolve()
        != Path(str(execution_paths["aggregate_path"])).resolve()
        or root != Path(str(execution_paths["output_root"])).resolve()
        or selected_authorization["resource_request"] != authorized_request
        or selected_authorization["plan_sha256"] != receipt["plan_sha256"]
        or selected_authorization["leaf_catalog_sha256"]
        != receipt["leaf_catalog_sha256"]
        or selected_authorization["leaf_wave_manifest_sha256"]
        != receipt["manifest"]["sha256"]
        or Path(str(selected_authorization["leaf_wave_result_path"])).resolve()
        != result_path
        or request_value["command"]
        != expected_resource_command(
            python_executable=Path(
                str(authorized_wave["execution_paths"]["python_executable"])
            ),
            contract_path=contract_path,
            authorization_path=authorization_path,
            output_root=Path(str(authorized_wave["execution_paths"]["output_root"])),
            aggregate_path=Path(
                str(authorized_wave["execution_paths"]["aggregate_path"])
            ),
            execution_mode="leaf-wave",
            plan_sha256=receipt["plan_sha256"],
            leaf_wave_index=wave_index,
            leaf_catalog_sha256=receipt["leaf_catalog_sha256"],
            leaf_wave_manifest_sha256=receipt["manifest"]["sha256"],
            leaf_wave_result_path=result_path,
        )
    ):
        raise CoordinatorError("leaf wave receipt is not joined to its exact authority")
    terminal_ledger_row = _validate_completed_leaf_wave_ledger_row(
        str(request_id), request_value, receipt_raw=receipt_raw
    )
    return {
        "path": receipt_path.resolve(),
        "raw": receipt_raw,
        "receipt": receipt,
        "terminal_ledger_row": terminal_ledger_row,
        "workers": accepted_workers,
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
                output = _contained_leaf_output(
                    (root / "checker.json").resolve(),
                    output_root.resolve(),
                    "leaf checker output",
                )
                stdout_path = _contained_leaf_output(
                    (root / "stdout.log").resolve(),
                    output_root.resolve(),
                    "leaf checker stdout",
                )
                stderr_path = _contained_leaf_output(
                    (root / "stderr.log").resolve(),
                    output_root.resolve(),
                    "leaf checker stderr",
                )
                pair.append(
                    (
                        replica_index,
                        pool.submit(
                            _run_checker_process,
                            assignment_id=assignment_id,
                            proof=proof,
                            plan=plan,
                            output=output,
                            stdout_path=stdout_path,
                            stderr_path=stderr_path,
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
    if classifying_count != 81 or v1_count != 0:
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
        "v1_comparator_disposition": LEAF_V1_DISPOSITION,
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
        "v1_comparator_disposition": LEAF_V1_DISPOSITION,
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
    raise CoordinatorError(
        "legacy Stage 4A execution is not authorized by correction 6"
    )


def _historical_run_stage4a_guarded(
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    aggregate_path: Path,
    wall_guard: _CoordinatorWallGuard,
) -> dict[str, Any]:
    """Retain correction-3 incident logic for immutable-history inspection only."""

    raise CoordinatorError(
        "historical Stage 4A execution is not executable under correction 6"
    )

    _coordinator_checkpoint()
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise CoordinatorError("formal Stage 4A requires the registered -I -B launcher")
    contract, contract_raw = validate_contract(contract_path)
    _coordinator_checkpoint()
    authorization, authorization_raw = validate_authorization(
        authorization_path,
        contract_path=contract_path,
        contract_raw=contract_raw,
        execution_mode="legacy",
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
        paths = _historical_prepare_wave(
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
            execution_mode="legacy",
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
    """Reject the obsolete monolithic runner retained only as history."""

    raise CoordinatorError(
        "legacy Stage 4A execution is not authorized by correction 6"
    )


def _historical_run_stage4a(
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    aggregate_path: Path,
) -> dict[str, Any]:
    """Retain correction-3 wall handling for immutable-history inspection only."""

    raise CoordinatorError(
        "historical Stage 4A execution is not executable under correction 6"
    )

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
            return _historical_run_stage4a_guarded(
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


def _contained_leaf_finalizer_input(
    path: Path, output_root: Path, location: str
) -> Path:
    if not path.is_absolute():
        raise CoordinatorError(f"{location} must be absolute")
    try:
        information = path.lstat()
    except OSError as exc:
        raise CoordinatorError(f"cannot inspect {location}: {exc}") from exc
    if (
        not stat.S_ISREG(information.st_mode)
        or path.is_symlink()
        or getattr(information, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    ):
        raise CoordinatorError(f"{location} must be a regular non-reparse file")
    resolved_root = _validated_leaf_output_root(output_root, "leaf output root")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise CoordinatorError(f"{location} escapes the registered output root") from exc
    _validate_leaf_output_ancestors(resolved.parent, resolved_root, location)
    return resolved


def _validated_leaf_output_root(output_root: Path, location: str) -> Path:
    if not output_root.is_absolute():
        raise CoordinatorError(f"{location} must be absolute")
    try:
        information = output_root.lstat()
    except OSError as exc:
        raise CoordinatorError(f"cannot inspect {location}: {exc}") from exc
    if (
        not stat.S_ISDIR(information.st_mode)
        or output_root.is_symlink()
        or getattr(information, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    ):
        raise CoordinatorError(f"{location} must be a non-reparse directory")
    return output_root.resolve(strict=True)


def _validate_leaf_output_ancestors(
    parent: Path, resolved_root: Path, location: str
) -> None:
    current = parent
    while True:
        if current.exists():
            information = current.lstat()
            if (
                not stat.S_ISDIR(information.st_mode)
                or current.is_symlink()
                or getattr(information, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            ):
                raise CoordinatorError(
                    f"{location} has a non-directory or reparse output ancestor"
                )
        if current == resolved_root:
            return
        if current.parent == current:
            raise CoordinatorError(f"{location} escapes the registered output root")
        current = current.parent


def _contained_leaf_output(
    path: Path, output_root: Path, location: str
) -> Path:
    """Resolve a not-yet-created leaf output below a plain cycle directory."""

    if not path.is_absolute():
        raise CoordinatorError(f"{location} must be absolute")
    resolved_root = _validated_leaf_output_root(output_root, "leaf output root")
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise CoordinatorError(f"{location} escapes the registered output root") from exc
    _validate_leaf_output_ancestors(resolved.parent, resolved_root, location)
    if os.path.lexists(resolved):
        try:
            information = resolved.lstat()
        except OSError as exc:
            raise CoordinatorError(f"cannot inspect {location}: {exc}") from exc
        if (
            resolved.is_symlink()
            or getattr(information, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise CoordinatorError(f"{location} is a reparse output")
    return resolved


def _stage4a_leaf_wave_receipt(
    *,
    authorization: Mapping[str, Any],
    authorization_path: Path,
    contract_path: Path,
    cycle: Mapping[str, Any],
    result_path: Path,
    result_raw: bytes,
    workers: Sequence[Mapping[str, Any]],
    wave_index: int,
) -> dict[str, Any]:
    request_id = str(authorization["resource_request"]["request_id"])
    request_path = Path(str(authorization["resource_request"]["request_path"]))
    attempt_path = (
        RESOURCE_MANAGER_ROOT / "attempts" / f"{request_id}.json"
    ).resolve()
    return {
        "attempt": _external_file_binding(attempt_path, "leaf wave attempt"),
        "authorization": _external_file_binding(
            authorization_path, "leaf wave authorization"
        ),
        "candidate_authority": cycle["candidate_authority"],
        "candidate_authority_sha256": _leaf_candidate_authority_sha256(
            cycle["candidate_authority"]
        ),
        "contract": _external_file_binding(contract_path, "leaf wave contract"),
        "leaf_catalog_sha256": sha256(canonical_bytes(cycle["catalog"])),
        "manifest": _external_file_binding(
            cycle["manifest_path"], "leaf wave manifest"
        ),
        "plan_sha256": sha256(cycle["plan_raw"]),
        "request": _external_file_binding(request_path, "leaf wave request"),
        "request_command_sha256": authorization["resource_request"][
            "command_sha256"
        ],
        "request_id": request_id,
        "result": {
            "byte_count": len(result_raw),
            "path": str(result_path.resolve()),
            "sha256": sha256(result_raw),
        },
        "schema": LEAF_WAVE_RECEIPT_SCHEMA,
        "terminal": "COMPLETED",
        "wave_id": cycle["wave"]["wave_id"],
        "wave_index": wave_index,
        "workers": list(workers),
    }


def _run_stage4a_leaf_wave_guarded(
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    receipt_path: Path,
    result_path: Path,
    *,
    wave_index: int,
    plan_sha256: str,
    leaf_catalog_sha256: str,
    leaf_wave_manifest_sha256: str,
    wall_guard: _CoordinatorWallGuard,
) -> Mapping[str, Any]:
    _coordinator_checkpoint()
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise CoordinatorError("formal leaf wave requires the registered -I -B launcher")
    contract, contract_raw = validate_contract(contract_path)
    authorization, authorization_raw = validate_authorization(
        authorization_path,
        contract_path=contract_path,
        contract_raw=contract_raw,
        execution_mode="leaf-wave",
        plan_sha256=plan_sha256,
        leaf_wave_index=wave_index,
        leaf_catalog_sha256=leaf_catalog_sha256,
        leaf_wave_manifest_sha256=leaf_wave_manifest_sha256,
        leaf_wave_result_path=result_path,
    )
    execution_paths = authorization["execution_paths"]
    contained_receipt = _contained_leaf_output(
        receipt_path,
        output_root,
        "leaf wave receipt output",
    )
    if (
        Path(str(execution_paths["output_root"])).resolve() != output_root.resolve()
        or Path(str(execution_paths["aggregate_path"])).resolve()
        != contained_receipt
        or Path(str(execution_paths["python_executable"])).resolve()
        != Path(sys.executable).resolve()
    ):
        raise CoordinatorError("live leaf wave invocation differs from its request")
    validate_resource_execution_state(authorization)
    authorization_digest = sha256(authorization_raw)
    contract_digest = sha256(contract_raw)
    wall_guard.bind_evidence(
        authorization_sha256=authorization_digest,
        contract_sha256=contract_digest,
    )
    process_phase = "LEAF_WAVE_INPUT_VALIDATION"
    result_published = False
    try:
        cycle = _validate_stage4a_leaf_cycle(
            contract=contract,
            contract_path=contract_path,
            output_root=output_root,
            wave_index=wave_index,
        )
        expected_result = (cycle["wave_root"] / "bounded-result.json").resolve()
        if result_path.resolve() != expected_result:
            raise CoordinatorError("leaf bounded result path differs")
        if (
            sha256(cycle["plan_raw"]) != _digest(plan_sha256, "leaf plan hash")
            or sha256(canonical_bytes(cycle["catalog"]))
            != _digest(leaf_catalog_sha256, "leaf catalog hash")
            or sha256(cycle["manifest_path"].read_bytes())
            != _digest(leaf_wave_manifest_sha256, "leaf wave manifest hash")
        ):
            raise CoordinatorError("leaf wave command hashes differ from frozen files")
        wall_guard.bind_producer_result(result_path)
        bounded = _load_module(
            f"_s3_v2_stage4a_leaf_wave_{wave_index:02d}_bounded", BOUNDED_PATH
        )
        process_phase = "LEAF_WAVE_EXECUTION"
        wall_guard.mark_process_phase_active()
        result = bounded.run_wave(cycle["manifest_path"], result_path)
        result_published = result_path.is_file()
        wall_guard.mark_process_phase_terminal(
            proven=_producer_process_trees_proven_terminal(result)
        )
        if result.get("terminal") != "COMPLETED":
            raise CoordinatorError("leaf bounded wave did not complete")
        result, result_raw, accepted_workers = _validate_stage4a_leaf_wave_result(
            result_path, cycle
        )
        process_phase = "LEAF_WAVE_FINAL_AUTHORITY"
        final_contract, final_contract_raw = validate_contract(contract_path)
        final_authorization, final_authorization_raw = validate_authorization(
            authorization_path,
            contract_path=contract_path,
            contract_raw=final_contract_raw,
            execution_mode="leaf-wave",
            plan_sha256=plan_sha256,
            leaf_wave_index=wave_index,
            leaf_catalog_sha256=leaf_catalog_sha256,
            leaf_wave_manifest_sha256=leaf_wave_manifest_sha256,
            leaf_wave_result_path=result_path,
        )
        if (
            final_contract_raw != contract_raw
            or final_authorization_raw != authorization_raw
            or final_contract != contract
        ):
            raise CoordinatorError("leaf wave authority changed during execution")
        validate_resource_execution_state(final_authorization, claim_attempt=False)
        final_cycle = _validate_stage4a_leaf_cycle(
            contract=contract,
            contract_path=contract_path,
            output_root=output_root,
            wave_index=wave_index,
        )
        if (
            final_cycle["manifest_path"].read_bytes()
            != cycle["manifest_path"].read_bytes()
            or final_cycle["plan_raw"] != cycle["plan_raw"]
            or final_cycle["catalog"] != cycle["catalog"]
            or result_path.read_bytes() != result_raw
        ):
            raise CoordinatorError("leaf wave input/result changed before receipt")
        receipt = _stage4a_leaf_wave_receipt(
            authorization=authorization,
            authorization_path=authorization_path,
            contract_path=contract_path,
            cycle=cycle,
            result_path=result_path,
            result_raw=result_raw,
            workers=accepted_workers,
            wave_index=wave_index,
        )
    except _CoordinatorWallExceeded:
        raise
    except Exception:
        producer_digest = (
            sha256(result_path.read_bytes())
            if result_published and result_path.is_file()
            else None
        )
        receipt = blocked_aggregate(
            authorization_sha256=authorization_digest,
            contract_sha256=contract_digest,
            producer_result_sha256=producer_digest,
            reason=(
                "PRODUCER_WAVE_NOT_COMPLETED"
                if result_published
                else "FORMAL_PROCESS_FAILED"
            ),
        )
    _write_exclusive(receipt_path, canonical_bytes(receipt))
    return receipt


def run_stage4a_leaf_wave(
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    receipt_path: Path,
    result_path: Path,
    *,
    wave_index: int,
    plan_sha256: str,
    leaf_catalog_sha256: str,
    leaf_wave_manifest_sha256: str,
) -> Mapping[str, Any]:
    """Execute one registered 1/2-worker leaf wave under 29 minutes."""

    global _ACTIVE_COORDINATOR_GUARD
    if _ACTIVE_COORDINATOR_GUARD is not None:
        raise CoordinatorError("a coordinator wall guard is already active")
    guard = _CoordinatorWallGuard(
        aggregate_path=receipt_path,
        started=time.monotonic(),
        wall_seconds=LEAF_FINALIZER_WALL_SECONDS,
        publication_reserve_seconds=LEAF_FINALIZER_PUBLICATION_RESERVE_SECONDS,
    )
    _ACTIVE_COORDINATOR_GUARD = guard
    try:
        guard.start()
        try:
            return _run_stage4a_leaf_wave_guarded(
                contract_path,
                authorization_path,
                output_root,
                receipt_path,
                result_path,
                wave_index=wave_index,
                plan_sha256=plan_sha256,
                leaf_catalog_sha256=leaf_catalog_sha256,
                leaf_wave_manifest_sha256=leaf_wave_manifest_sha256,
                wall_guard=guard,
            )
        except _CoordinatorWallExceeded as exc:
            receipt = guard.publish_fail_closed()
            if receipt is None:
                raise CoordinatorError(
                    "leaf wave wall elapsed before safe receipt publication"
                ) from exc
            return receipt
    finally:
        _ACTIVE_COORDINATOR_GUARD = None
        guard.close()


def _run_stage4a_leaf_finalizer_guarded(
    contract_path: Path,
    authorization_path: Path,
    plan_path: Path,
    leaf_union_path: Path,
    output_root: Path,
    aggregate_path: Path,
    wall_guard: _CoordinatorWallGuard,
    *,
    expected_plan_sha256: str,
    expected_leaf_union_sha256: str,
) -> dict[str, Any]:
    """Validate/reconstruct leaves and run only the unchanged checker phase."""

    _coordinator_checkpoint()
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise CoordinatorError("formal leaf finalization requires the registered -I -B launcher")
    plan_path = _contained_leaf_finalizer_input(plan_path, output_root, "leaf plan")
    leaf_union_path = _contained_leaf_finalizer_input(
        leaf_union_path, output_root, "leaf union"
    )
    initial_plan_raw = plan_path.read_bytes()
    initial_union_raw = leaf_union_path.read_bytes()
    if (
        sha256(initial_plan_raw)
        != _digest(expected_plan_sha256, "registered finalizer plan hash")
        or sha256(initial_union_raw)
        != _digest(expected_leaf_union_sha256, "registered finalizer union hash")
    ):
        raise CoordinatorError("leaf finalizer plan/union differs from request hashes")
    if plan_path == leaf_union_path or aggregate_path.resolve() in {
        plan_path,
        leaf_union_path,
    }:
        raise CoordinatorError("leaf finalizer inputs and aggregate must be distinct")
    contract, contract_raw = validate_contract(contract_path)
    _coordinator_checkpoint()
    authorization, authorization_raw = validate_authorization(
        authorization_path,
        contract_path=contract_path,
        contract_raw=contract_raw,
        execution_mode="leaf-finalizer",
        plan_path=plan_path,
        leaf_union_path=leaf_union_path,
        plan_sha256=expected_plan_sha256,
        leaf_union_sha256=expected_leaf_union_sha256,
    )
    execution_paths = authorization["execution_paths"]
    if (
        Path(str(execution_paths["output_root"])).resolve() != output_root.resolve()
        or Path(str(execution_paths["aggregate_path"])).resolve()
        != aggregate_path.resolve()
        or Path(str(execution_paths["python_executable"])).resolve()
        != Path(sys.executable).resolve()
    ):
        raise CoordinatorError("live leaf finalizer invocation differs from its request")
    validate_resource_execution_state(authorization)
    authorization_digest = sha256(authorization_raw)
    contract_digest = sha256(contract_raw)
    union_digest = sha256(initial_union_raw)
    snapshot_root = (output_root / "leaf-finalizer-input-snapshot").resolve()
    snapshot_plan_path = _contained_leaf_output(
        (snapshot_root / "phase4a-plan.json").resolve(),
        output_root,
        "leaf finalizer plan snapshot",
    )
    snapshot_union_path = _contained_leaf_output(
        (snapshot_root / "leaf-union.json").resolve(),
        output_root,
        "leaf finalizer union snapshot",
    )
    _write_exclusive(snapshot_plan_path, initial_plan_raw)
    _write_exclusive(snapshot_union_path, initial_union_raw)
    wall_guard.bind_evidence(
        authorization_sha256=authorization_digest,
        contract_sha256=contract_digest,
    )
    # The complete union replaces the legacy producer-wave result as the
    # content-addressed scientific producer input for aggregate binding.
    wall_guard.bind_producer_result(snapshot_union_path)
    process_phase = "LEAF_UNION_VALIDATION"
    try:
        union_envelope = strict_json_bytes(
            initial_union_raw, str(snapshot_union_path)
        )
        if initial_union_raw != canonical_bytes(union_envelope) or not isinstance(
            union_envelope, dict
        ):
            raise CoordinatorError("Stage 4A leaf union is not canonical JSON")
        raw_candidate_authority = union_envelope.get("candidate_authority")
        if not isinstance(raw_candidate_authority, dict):
            raise CoordinatorError("Stage 4A leaf union candidate authority is absent")
        candidate_authority = _leaf_candidate_authority(
            **raw_candidate_authority
        )
        expected_candidate_authority = _leaf_candidate_authority(
            candidate_commit=contract["candidate"]["commit"],
            candidate_tree=contract["candidate"]["tree"],
            candidate_archive_sha256=candidate_authority[
                "candidate_archive_sha256"
            ],
            producer_program_sha256=sha256(PRODUCER_PATH.read_bytes()),
        )
        if candidate_authority != expected_candidate_authority:
            raise CoordinatorError(
                "leaf candidate commit/tree or producer identity differs from contract"
            )
        plan, plan_raw = _validate_stage4a_plan_raw(
            initial_plan_raw, label=str(snapshot_plan_path)
        )
        catalog = build_stage4a_leaf_catalog(
            plan,
            plan_raw,
            **candidate_authority,
        )
        wave_catalog = build_stage4a_leaf_wave_catalog(catalog)
        if (
            wave_catalog["wave_count"] != LEAF_WAVE_COUNT
            or sum(wave["worker_count"] for wave in wave_catalog["waves"])
            != LEAF_CATALOG_COUNT
        ):
            raise CoordinatorError("leaf wave catalog validation differs")
        validated_union = validate_stage4a_leaf_union(
            snapshot_union_path,
            catalog=catalog,
            plan=plan,
            plan_raw=plan_raw,
            candidate_authority=candidate_authority,
            contract=contract,
            contract_path=contract_path,
            contract_raw=contract_raw,
            allowed_root=output_root,
            frozen_union_raw=initial_union_raw,
        )
        process_phase = "DIAGONAL_RECONSTRUCTION"
        documents = reconstruct_stage4a_diagonal_documents(
            plan, plan_raw, validated_union
        )
        producer_proofs = publish_stage4a_diagonal_documents(
            documents, output_root
        )
        proofs = {
            assignment_id: Path(str(binding["proof_path"]))
            for assignment_id, binding in producer_proofs.items()
        }
        process_phase = "CHECKER_WAVE"
        bounded = _load_module("_s3_v2_stage4a_leaf_finalizer_bounded", BOUNDED_PATH)
        replicas = _run_checker_phase(
            bounded=bounded,
            proofs=proofs,
            plan=snapshot_plan_path,
            output_root=output_root,
            deadline=wall_guard.work_deadline,
            wall_guard=wall_guard,
        )
        process_phase = "FINAL_AUTHORITY_REVALIDATION"
        _coordinator_checkpoint()
        _final_contract, final_contract_raw = validate_contract(contract_path)
        final_authorization, final_authorization_raw = validate_authorization(
            authorization_path,
            contract_path=contract_path,
            contract_raw=final_contract_raw,
            execution_mode="leaf-finalizer",
            plan_path=plan_path,
            leaf_union_path=leaf_union_path,
            plan_sha256=expected_plan_sha256,
            leaf_union_sha256=expected_leaf_union_sha256,
        )
        if final_contract_raw != contract_raw or final_authorization_raw != authorization_raw:
            raise CoordinatorError("formal leaf finalizer authority changed during execution")
        validate_resource_execution_state(final_authorization, claim_attempt=False)
        if (
            plan_path.read_bytes() != initial_plan_raw
            or leaf_union_path.read_bytes() != initial_union_raw
            or snapshot_plan_path.read_bytes() != initial_plan_raw
            or snapshot_union_path.read_bytes() != initial_union_raw
        ):
            raise CoordinatorError("leaf finalizer plan/union changed before publication")
        aggregate = aggregate_checker_results(
            replicas,
            producer_proofs=producer_proofs,
            producer_result_sha256=union_digest,
            contract_sha256=contract_digest,
            authorization_sha256=authorization_digest,
        )
        _coordinator_checkpoint()
    except _CoordinatorWallExceeded:
        raise
    except Exception as exc:
        try:
            _write_process_incident(
                (output_root / "stage4a-leaf-finalizer-incident.json").resolve(),
                authorization_sha256=authorization_digest,
                contract_sha256=contract_digest,
                error=exc,
                phase=process_phase,
                producer_result_path=snapshot_union_path,
            )
        except Exception:
            pass
        aggregate = blocked_aggregate(
            authorization_sha256=authorization_digest,
            contract_sha256=contract_digest,
            producer_result_sha256=union_digest,
            reason="CHECKER_WAVE_FAILED",
        )
    _write_exclusive(aggregate_path, canonical_bytes(aggregate))
    return aggregate


def run_stage4a_leaf_finalizer(
    contract_path: Path,
    authorization_path: Path,
    plan_path: Path,
    leaf_union_path: Path,
    output_root: Path,
    aggregate_path: Path,
    *,
    plan_sha256: str,
    leaf_union_sha256: str,
) -> dict[str, Any]:
    """Run leaf validation plus checkers under a strict sub-30-minute wall."""

    global _ACTIVE_COORDINATOR_GUARD
    if _ACTIVE_COORDINATOR_GUARD is not None:
        raise CoordinatorError("a coordinator wall guard is already active")
    guard = _CoordinatorWallGuard(
        aggregate_path=aggregate_path,
        started=time.monotonic(),
        wall_seconds=LEAF_FINALIZER_WALL_SECONDS,
        publication_reserve_seconds=LEAF_FINALIZER_PUBLICATION_RESERVE_SECONDS,
    )
    _ACTIVE_COORDINATOR_GUARD = guard
    try:
        guard.start()
        try:
            return _run_stage4a_leaf_finalizer_guarded(
                contract_path,
                authorization_path,
                plan_path,
                leaf_union_path,
                output_root,
                aggregate_path,
                guard,
                expected_plan_sha256=plan_sha256,
                expected_leaf_union_sha256=leaf_union_sha256,
            )
        except _CoordinatorWallExceeded as exc:
            aggregate = guard.publish_fail_closed()
            if aggregate is None:
                raise CoordinatorError(
                    "leaf finalizer wall elapsed before canonical hashes were bound"
                ) from exc
            return aggregate
    finally:
        _ACTIVE_COORDINATOR_GUARD = None
        guard.close()


def run_prepare_stage4a(contract_path: Path, output_root: Path) -> dict[str, Path]:
    """Reject the obsolete monolithic preparation mode."""

    raise CoordinatorError(
        "legacy Stage 4A preparation is not authorized by correction 6"
    )


def _historical_run_prepare_stage4a(
    contract_path: Path, output_root: Path
) -> dict[str, Path]:
    """Retain correction-3 preparation wall handling for history inspection."""

    raise CoordinatorError(
        "historical Stage 4A preparation is not executable under correction 6"
    )

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
            return _historical_prepare_wave(contract_path, output_root)
        except _CoordinatorWallExceeded as exc:
            raise CoordinatorError(
                "Stage 4A preparation exceeded its coordinator wall"
            ) from exc
    finally:
        _ACTIVE_COORDINATOR_GUARD = None
        guard.close()


def run_prepare_stage4a_leaf_cycle(
    contract_path: Path, output_root: Path
) -> dict[str, Any]:
    """Prepare the correction-6 catalog/manifests under a sub-30-minute wall."""

    global _ACTIVE_COORDINATOR_GUARD
    if _ACTIVE_COORDINATOR_GUARD is not None:
        raise CoordinatorError("a coordinator wall guard is already active")
    guard = _CoordinatorWallGuard(
        aggregate_path=(output_root / "stage4a-leaf-prepare-timeout.json").resolve(),
        started=time.monotonic(),
        wall_seconds=LEAF_FINALIZER_WALL_SECONDS,
        publication_reserve_seconds=LEAF_FINALIZER_PUBLICATION_RESERVE_SECONDS,
    )
    _ACTIVE_COORDINATOR_GUARD = guard
    try:
        guard.start()
        try:
            return prepare_stage4a_leaf_cycle(contract_path, output_root)
        except _CoordinatorWallExceeded as exc:
            raise CoordinatorError(
                "Stage 4A leaf preparation exceeded its registered wall"
            ) from exc
    finally:
        _ACTIVE_COORDINATOR_GUARD = None
        guard.close()


def assemble_stage4a_leaf_union(
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    union_path: Path,
) -> dict[str, Any]:
    """Join all 41 post-terminal receipts into one nonclassifying union."""

    if authorization_path.resolve() != LEAF_WAVE_AUTHORIZATION_PATH.resolve():
        raise CoordinatorError("leaf union assembly authorization path differs")
    contract, contract_raw = validate_contract(contract_path)
    authorization, authorization_raw = strict_json_load(authorization_path)
    if authorization_raw != canonical_bytes(authorization):
        raise CoordinatorError("leaf wave authorization is not canonical JSON")
    authorization = _exact(
        authorization,
        {
            "contract_path",
            "contract_sha256",
            "formal_execution_authorized",
            "implementation_reviews",
            "leaf_waves",
            "resource_lock_required",
            "schema",
            "user_approval",
        },
        "$.leaf_wave_authorization",
    )
    if authorization["schema"] != LEAF_WAVE_AUTHORIZATION_SCHEMA:
        raise CoordinatorError("leaf union assembly requires v5 wave authority")
    raw_waves = authorization["leaf_waves"]
    if not isinstance(raw_waves, list) or len(raw_waves) != LEAF_WAVE_COUNT:
        raise CoordinatorError(
            f"leaf union assembly requires exactly {LEAF_WAVE_COUNT} waves"
        )
    receipt_paths: dict[int, Path] = {}
    for wave_index, raw_wave in enumerate(raw_waves, start=1):
        wave = _exact(
            raw_wave,
            {
                "execution_paths",
                "leaf_catalog_sha256",
                "leaf_wave_manifest_sha256",
                "leaf_wave_result_path",
                "ledger_approval",
                "plan_sha256",
                "resource_request",
                "wave_index",
            },
            f"$.leaf_wave_authorization.leaf_waves[{wave_index - 1}]",
        )
        execution = _exact(
            wave["execution_paths"],
            {
                "aggregate_path",
                "approval_snapshot_path",
                "output_root",
                "python_executable",
            },
            f"$.leaf_wave_authorization.leaf_waves[{wave_index - 1}].execution_paths",
        )
        if wave["wave_index"] != wave_index:
            raise CoordinatorError("leaf union assembly wave order differs")
        receipt_paths[wave_index] = Path(str(execution["aggregate_path"])).resolve()
    cycle = _validate_stage4a_leaf_cycle(
        contract=contract,
        contract_path=contract_path,
        output_root=output_root,
        wave_index=1,
    )
    union = build_stage4a_leaf_union(
        cycle["catalog"],
        receipt_paths,
        candidate_archive_path=cycle["archive"],
        contract=contract,
        contract_path=contract_path,
        contract_raw=contract_raw,
        authorization_path=authorization_path,
        authorization_raw=authorization_raw,
        output_root=output_root,
    )
    union_path = _contained_leaf_output(
        union_path, output_root, "leaf union output"
    )
    _write_exclusive(union_path, canonical_bytes(union))
    return union


def run_assemble_stage4a_leaf_union(
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    union_path: Path,
) -> dict[str, Any]:
    """Bound union assembly to the same sub-30-minute safety envelope."""

    global _ACTIVE_COORDINATOR_GUARD
    if _ACTIVE_COORDINATOR_GUARD is not None:
        raise CoordinatorError("a coordinator wall guard is already active")
    guard = _CoordinatorWallGuard(
        aggregate_path=union_path,
        started=time.monotonic(),
        wall_seconds=LEAF_FINALIZER_WALL_SECONDS,
        publication_reserve_seconds=LEAF_FINALIZER_PUBLICATION_RESERVE_SECONDS,
    )
    _ACTIVE_COORDINATOR_GUARD = guard
    try:
        guard.start()
        try:
            return assemble_stage4a_leaf_union(
                contract_path, authorization_path, output_root, union_path
            )
        except _CoordinatorWallExceeded as exc:
            raise CoordinatorError(
                "Stage 4A leaf union assembly exceeded its registered wall"
            ) from exc
    finally:
        _ACTIVE_COORDINATOR_GUARD = None
        guard.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--prepare-leaf-cycle", action="store_true")
    mode.add_argument("--assemble-leaf-union", action="store_true")
    mode.add_argument("--run-stage4a", action="store_true")
    mode.add_argument("--run-leaf-wave", action="store_true")
    mode.add_argument("--finalize-leaf-union", action="store_true")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--aggregate", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--leaf-union", type=Path)
    parser.add_argument("--plan-sha256")
    parser.add_argument("--leaf-union-sha256")
    parser.add_argument("--leaf-wave-index", type=int)
    parser.add_argument("--leaf-catalog-sha256")
    parser.add_argument("--leaf-wave-manifest-sha256")
    parser.add_argument("--leaf-wave-result", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.prepare_only:
        raise CoordinatorError(
            "legacy Stage 4A preparation is not authorized by correction 6"
        )
    if args.run_stage4a:
        raise CoordinatorError(
            "legacy Stage 4A execution is not authorized by correction 6"
        )
    contract = args.contract.resolve()
    output_root = args.output_root.resolve()
    if args.prepare_only:
        if (
            args.authorization is not None
            or args.aggregate is not None
            or args.plan is not None
            or args.leaf_union is not None
            or args.plan_sha256 is not None
            or args.leaf_union_sha256 is not None
            or args.leaf_wave_index is not None
            or args.leaf_catalog_sha256 is not None
            or args.leaf_wave_manifest_sha256 is not None
            or args.leaf_wave_result is not None
        ):
            raise CoordinatorError("prepare-only does not accept execution outputs")
        run_prepare_stage4a(contract, output_root)
        return 0
    if args.prepare_leaf_cycle:
        if any(
            value is not None
            for value in (
                args.authorization,
                args.aggregate,
                args.plan,
                args.leaf_union,
                args.plan_sha256,
                args.leaf_union_sha256,
                args.leaf_wave_index,
                args.leaf_catalog_sha256,
                args.leaf_wave_manifest_sha256,
                args.leaf_wave_result,
            )
        ):
            raise CoordinatorError("leaf preparation does not accept execution outputs")
        run_prepare_stage4a_leaf_cycle(contract, output_root)
        return 0
    if args.authorization is None or args.aggregate is None:
        raise CoordinatorError("formal execution requires authorization and aggregate")
    if args.assemble_leaf_union:
        if any(
            value is not None
            for value in (
                args.plan,
                args.leaf_union,
                args.plan_sha256,
                args.leaf_union_sha256,
                args.leaf_wave_index,
                args.leaf_catalog_sha256,
                args.leaf_wave_manifest_sha256,
                args.leaf_wave_result,
            )
        ):
            raise CoordinatorError("leaf union assembly does not accept leaf overrides")
        run_assemble_stage4a_leaf_union(
            contract,
            args.authorization.resolve(),
            output_root,
            args.aggregate.resolve(),
        )
        return 0
    if args.finalize_leaf_union:
        if (
            args.plan is None
            or args.leaf_union is None
            or args.plan_sha256 is None
            or args.leaf_union_sha256 is None
            or any(
                value is not None
                for value in (
                    args.leaf_wave_index,
                    args.leaf_catalog_sha256,
                    args.leaf_wave_manifest_sha256,
                    args.leaf_wave_result,
                )
            )
        ):
            raise CoordinatorError(
                "leaf finalization requires exact plan and union paths/hashes"
            )
        aggregate = run_stage4a_leaf_finalizer(
            contract,
            args.authorization.resolve(),
            args.plan.resolve(),
            args.leaf_union.resolve(),
            output_root,
            args.aggregate.resolve(),
            plan_sha256=args.plan_sha256,
            leaf_union_sha256=args.leaf_union_sha256,
        )
    elif args.run_leaf_wave:
        if (
            args.leaf_wave_index is None
            or args.plan_sha256 is None
            or args.leaf_catalog_sha256 is None
            or args.leaf_wave_manifest_sha256 is None
            or args.leaf_wave_result is None
            or args.plan is not None
            or args.leaf_union is not None
            or args.leaf_union_sha256 is not None
        ):
            raise CoordinatorError("leaf wave execution inputs are incomplete")
        aggregate = run_stage4a_leaf_wave(
            contract,
            args.authorization.resolve(),
            output_root,
            args.aggregate.resolve(),
            args.leaf_wave_result.resolve(),
            wave_index=args.leaf_wave_index,
            plan_sha256=args.plan_sha256,
            leaf_catalog_sha256=args.leaf_catalog_sha256,
            leaf_wave_manifest_sha256=args.leaf_wave_manifest_sha256,
        )
    else:
        if any(
            value is not None
            for value in (
                args.plan,
                args.leaf_union,
                args.plan_sha256,
                args.leaf_union_sha256,
                args.leaf_wave_index,
                args.leaf_catalog_sha256,
                args.leaf_wave_manifest_sha256,
                args.leaf_wave_result,
            )
        ):
            raise CoordinatorError("legacy formal execution does not accept leaf inputs")
        aggregate = run_stage4a(
            contract,
            args.authorization.resolve(),
            output_root,
            args.aggregate.resolve(),
        )
    return 0 if aggregate["terminal"] in {PASS, NO_GO, "COMPLETED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
