"""Deterministic Stage-4 flat mixed-flexural funnel planning harness.

This research-only module deliberately performs no finite-element work.  It
validates the immutable 252-record QV9 connectivity manifest, selects the
preregistered incremental funnel phases, and emits hash-bound shard plans for
a later mechanics producer.  Importing the module requires only the standard
library and cannot select or instantiate an element.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PLAN_SCHEMA = "anysolver.e4-pl-s3-v2-flat-funnel-plan-v1"
ASSIGNMENT_SCHEMA = "anysolver.e4-pl-s3-v2-flat-funnel-assignment-v1"
RECEIPT_SCHEMA = "anysolver.e4-pl-s3-v2-flat-funnel-phase-receipt-v2"
SCIENTIFIC_AGGREGATE_SCHEMA = (
    "anysolver.e4-pl-s3-v2-flat-funnel-scientific-aggregate-v1"
)
SHARD_SCIENTIFIC_SCHEMA = "anysolver.e4-pl-s3-v2-flat-funnel-shard-scientific-v1"
PROGRESS_SCHEMA = "anysolver.e4-pl-s3-v2-worker-progress-v1"
BOUNDED_MANIFEST_SCHEMA = "anysolver.e4-pl-s3-v2-bounded-wave-manifest-v1"
BOUNDED_RESULT_SCHEMA = "anysolver.e4-pl-s3-v2-bounded-wave-result-v1"
CONTRACT_SCHEMA = "anysolver.e4-pl-s3-v2-flat-funnel-contract-v1"
SOURCE_CONTRACT_SCHEMA = "anysolver.e4-pl-s3-v2-source-equation-contract-v1"
CANDIDATE_BINDING_SCHEMA = "anysolver.e4-pl-s3-v2-flat-candidate-binding-v1"
CANDIDATE_ID = "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1"
FORMULATION_ID = "E4_PL_QUALIFIED_S3_COMPANION_V2"
REGISTERED_FLAT_FUNNEL_CONTRACT_BYTES = 4298
REGISTERED_FLAT_FUNNEL_CONTRACT_SHA256 = (
    "B7F32D1DD8350E10B8C8EF302933EFEC17F21B1DDF19768B59724E2DB7DDBE40"
)
REGISTERED_SOURCE_CONTRACT_BYTES = 8426
REGISTERED_SOURCE_CONTRACT_SHA256 = (
    "754A31C2B03FA3785274F30BF4F2A2FC8C66DF66A76C5D39CD9736E81679513A"
)
FORMAL_EXECUTION_AUTHORIZED = False
SCAFFOLD_RECEIPT_TERMINAL = "VALIDATED_NONCLASSIFYING_SCAFFOLD_FOR_EXPANSION"

FROZEN_INPUT_NAMES = {
    "candidate_artifact",
    "connectivity_manifest",
    "flat_funnel_contract",
    "source_equation_contract",
}

SELECTOR = "e4-pl-s3-v2"
MANIFEST_SCHEMA = "anysolver.e4-pl-s3-mixed-mesh-connectivity-manifest-v1"
MANIFEST_SHA256 = "3EA7ABD0B332831D62B30B3CD52E0DB85EC951B125340FFAF40A891DC37BD589"
DIAGONALS = ("slash", "backslash", "alternating")
LEVELS = (20, 40, 80, 160)
FRACTIONS = (0, 1, 5, 10, 25)
SPLIT_COUNTS = {0: 0, 1: 4, 5: 20, 10: 40, 25: 100}
MASKS = (
    "dispersed",
    "chain",
    "compact_cluster",
    "boundary_band",
    "hole_band",
)
PHASES = ("4A", "4B", "4C")
PHASE_COUNTS = {"4A": 81, "4B": 108, "4C": 63}
PHASE_PREREQUISITES = {"4A": (), "4B": ("4A",), "4C": ("4A", "4B")}
PHASE_SCOPES = {"4A": ("full",), "4B": ("full",), "4C": ("sentinel", "completion")}
SCOPE_COUNTS = {
    ("4A", "full"): 81,
    ("4B", "full"): 108,
    ("4C", "sentinel"): 18,
    ("4C", "completion"): 45,
}
SCOPE_SHARD_COUNTS = {
    ("4A", "full"): 27,
    ("4B", "full"): 36,
    ("4C", "sentinel"): 6,
    ("4C", "completion"): 15,
}
RECEIPT_COUNTS = {"4A": 81, "4B": 108, "4C_SENTINEL": 18, "4C": 63}

SUPPORT_IDENTITY = "HARD_NAVIER_TRANSLATIONS_PLUS_TANGENTIAL_ROTATIONS_V2"
REFERENCE_IDENTITY = "INDEPENDENT_NAVIER_REISSNER_MINDLIN_UNIFORM_PRESSURE_V2"
ENERGY_NORM_IDENTITY = (
    "DISCRETE_STIFFNESS_ENERGY_NORM_OF_UH_MINUS_NODAL_MINDLIN_REFERENCE_V1"
)
SLOPE_IDENTITY = "FIXED_ONE_SIDED_95_PERCENT_LOG_LOG_SLOPE_V1"
FORMAL_THRESHOLDS = {
    "energy_norm_slope_lower_95_percent": "0.90",
    "finest_error_ratio_at_25_percent": "1.50",
    "finest_error_ratio_through_10_percent": "1.25",
    "response_slope_lower_bound": "1.80",
    "response_slope_maximum_deficit_from_all_q4": "0.15",
    "successive_error_factor_maximum": "1.02",
}
ADVISORY_THRESHOLDS = {
    "finest_error_ratio_at_25_percent": "1.35",
    "finest_error_ratio_through_10_percent": "1.15",
}


class FlatFunnelError(RuntimeError):
    """Raised when immutable funnel authority or evidence is inconsistent."""


@dataclass(frozen=True)
class ValidatedShardEvidence:
    """Hash-bound scientific evidence reconstructed from one canonical shard."""

    assignment_id: str
    assignment_sha256: str
    record_count: int
    record_ids_sha256: str
    scientific_payload_sha256: str
    scientific_sha256: str

    def aggregate_binding(self) -> dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "assignment_sha256": self.assignment_sha256,
            "record_count": self.record_count,
            "record_ids_sha256": self.record_ids_sha256,
            "scientific_payload_sha256": self.scientific_payload_sha256,
            "scientific_sha256": self.scientific_sha256,
        }


_VALIDATED_RECEIPT_TOKEN = object()


@dataclass(frozen=True)
class ValidatedReceipt:
    """Opaque, file-validated authority for expansion into a successor phase."""

    phase: str
    plan_sha256: str
    aggregate_sha256: str
    receipt_sha256: str
    receipt_path: Path
    record_ids: tuple[str, ...]
    shards: tuple[ValidatedShardEvidence, ...]
    _token: object

    @property
    def classification_authorized(self) -> bool:
        """The planning receipt can never authorize a scientific terminal."""

        return False

    def plan_binding(self) -> dict[str, str]:
        return {
            "aggregate_sha256": self.aggregate_sha256,
            "phase": self.phase,
            "plan_sha256": self.plan_sha256,
            "receipt_sha256": self.receipt_sha256,
        }


def _reject_constant(value: str) -> None:
    raise FlatFunnelError(f"non-finite JSON constant is forbidden: {value}")


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise FlatFunnelError(f"duplicate JSON key is forbidden: {key}")
        made[key] = value
    return made


def strict_json_bytes(payload: bytes, *, label: str) -> Any:
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise FlatFunnelError(f"{label} is not UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise FlatFunnelError(f"{label} is invalid JSON: {exc}") from exc


def strict_json_load(path: Path) -> tuple[Any, bytes]:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise FlatFunnelError(f"cannot read {path}: {exc}") from exc
    return strict_json_bytes(payload, label=str(path)), payload


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any, location: str) -> None:
        if item is None or isinstance(item, (bool, str, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise FlatFunnelError(f"non-finite value at {location}")
            return
        if isinstance(item, list):
            for index, member in enumerate(item):
                visit(member, f"{location}[{index}]")
            return
        if isinstance(item, dict):
            for key, member in item.items():
                if not isinstance(key, str):
                    raise FlatFunnelError(f"non-string key at {location}")
                visit(member, f"{location}.{key}")
            return
        raise FlatFunnelError(
            f"unsupported canonical value at {location}: {type(item).__name__}"
        )

    visit(value, "$")
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _exact_keys(value: Any, expected: set[str], location: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise FlatFunnelError(
            f"{location} keys differ: expected={sorted(expected)} actual={actual}"
        )
    return value


def _plain_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise FlatFunnelError(f"{location} must be a nonempty trimmed string")
    return value


def record_id(record: Mapping[str, Any]) -> str:
    return (
        f"N{int(record['level'])}:"
        f"{int(record['s3_area_fraction_percent'])}PCT:"
        f"{record['mask']}:{record['diagonal']}"
    )


def validate_contract(value: Any) -> Mapping[str, Any]:
    contract = _exact_keys(
        value,
        {
            "advisory_review_triggers",
            "authority_disposition",
            "candidate",
            "execution",
            "formal_protocol",
            "frozen_inputs",
            "phase_funnel",
            "production_boundary",
            "schema",
            "stage",
        },
        "$contract",
    )
    if contract["schema"] != CONTRACT_SCHEMA or contract["stage"] != "STAGE_4_FLAT":
        raise FlatFunnelError("flat-funnel contract identity mismatch")
    registered = canonical_bytes(contract)
    if (
        len(registered) != REGISTERED_FLAT_FUNNEL_CONTRACT_BYTES
        or sha256(registered) != REGISTERED_FLAT_FUNNEL_CONTRACT_SHA256
    ):
        raise FlatFunnelError("flat-funnel contract differs from registered exact bytes")
    disposition = contract["authority_disposition"]
    if disposition != {
        "artifact_commit_tree_verified": False,
        "formal_execution_authorized": False,
        "independent_scientific_payload_checker_registered": False,
        "receipt_classification": "NONCLASSIFYING_SCAFFOLD_ONLY",
        "registered_producer_identity": False,
    }:
        raise FlatFunnelError("flat-funnel authority disposition differs")
    candidate = contract["candidate"]
    if not isinstance(candidate, dict) or candidate.get("selector") != SELECTOR:
        raise FlatFunnelError("contract does not require the V2 selector")
    protocol = contract["formal_protocol"]
    if not isinstance(protocol, dict):
        raise FlatFunnelError("formal protocol is not an object")
    expected_protocol = {
        "energy_norm_identity": ENERGY_NORM_IDENTITY,
        "reference_identity": REFERENCE_IDENTITY,
        "slope_identity": SLOPE_IDENTITY,
        "support_identity": SUPPORT_IDENTITY,
        "thresholds": FORMAL_THRESHOLDS,
    }
    if protocol != expected_protocol:
        raise FlatFunnelError("formal QV9 protocol was changed")
    advisory = contract["advisory_review_triggers"]
    if not isinstance(advisory, dict) or advisory.get("thresholds") != ADVISORY_THRESHOLDS:
        raise FlatFunnelError("advisory review triggers differ")
    if advisory.get("classification") != "NONCLASSIFYING_INDEPENDENT_REVIEW_TRIGGER":
        raise FlatFunnelError("advisory triggers were made classifying")
    execution = contract["execution"]
    if not isinstance(execution, dict) or execution != {
        "activity_progress_schema": PROGRESS_SCHEMA,
        "inactivity_seconds": 300,
        "lane": "flat-proof",
        "maximum_memory_gib_per_process_tree": 24,
        "maximum_workers": 3,
        "no_automatic_retry": True,
        "numerical_library_threads_per_worker": 1,
        "worker_wall_seconds": 900,
        "wave_wall_seconds": 1800,
    }:
        raise FlatFunnelError("bounded flat-funnel execution policy differs")
    inputs = contract["frozen_inputs"]
    if (
        not isinstance(inputs, dict)
        or not isinstance(inputs.get("connectivity_manifest"), dict)
        or inputs["connectivity_manifest"].get("sha256") != MANIFEST_SHA256
    ):
        raise FlatFunnelError("contract connectivity-manifest binding differs")
    funnel = contract["phase_funnel"]
    if not isinstance(funnel, dict) or funnel.get("complete_gated_record_count") != 252:
        raise FlatFunnelError("contract phase-funnel coverage differs")
    expected_phase_records = {"4A": 81, "4B": 108, "4C": 63}
    if any(
        not isinstance(funnel.get(phase), dict)
        or funnel[phase].get("records") != count
        for phase, count in expected_phase_records.items()
    ):
        raise FlatFunnelError("contract phase record counts differ")
    if funnel["4C"].get("execution_order") != "SENTINEL_18_THEN_REMAINING_45":
        raise FlatFunnelError("contract N160 sentinel gate differs")
    boundary = contract["production_boundary"]
    if (
        not isinstance(boundary, dict)
        or boundary.get("default_s3_formulation_during_development") != "legacy-s3"
        or boundary.get("default_s3_unchanged") is not True
        or boundary.get("q4_mechanics_or_default_change") is not False
        or boundary.get("v1_scientific_fallback") is not False
    ):
        raise FlatFunnelError("production boundary differs")
    return contract


def validate_source_contract(value: Any, raw: bytes) -> Mapping[str, Any]:
    """Require the exact canonical source contract registered for this tranche."""

    if (
        len(raw) != REGISTERED_SOURCE_CONTRACT_BYTES
        or sha256(raw) != REGISTERED_SOURCE_CONTRACT_SHA256
    ):
        raise FlatFunnelError("source-equation contract differs from registered exact bytes")
    if raw != canonical_bytes(value):
        raise FlatFunnelError("source-equation contract is not canonical JSON")
    source = value
    if not isinstance(source, dict) or source.get("schema") != SOURCE_CONTRACT_SCHEMA:
        raise FlatFunnelError("source-equation contract identity mismatch")
    return source


def _validate_manifest_record(raw: Any, index: int) -> Mapping[str, Any]:
    expected = {
        "connectivity_sha256",
        "diagonal",
        "element_count",
        "level",
        "mask",
        "node_count",
        "q4_element_count",
        "s3_area_fraction_percent",
        "s3_element_count",
        "selected_base_cells_sha256",
        "split_base_cell_count",
        "split_refined_cell_count",
    }
    record = _exact_keys(raw, expected, f"$manifest.records[{index}]")
    level = record["level"]
    fraction = record["s3_area_fraction_percent"]
    mask = record["mask"]
    diagonal = record["diagonal"]
    if level not in LEVELS or fraction not in FRACTIONS or diagonal not in DIAGONALS:
        raise FlatFunnelError(f"record {index} has an unregistered coordinate")
    if fraction == 0:
        if mask != "none" or record["split_base_cell_count"] != 0:
            raise FlatFunnelError(f"record {index} has malformed all-Q4 authority")
    elif mask not in MASKS or record["split_base_cell_count"] != SPLIT_COUNTS[fraction]:
        raise FlatFunnelError(f"record {index} has malformed mixed authority")
    for key in ("connectivity_sha256", "selected_base_cells_sha256"):
        digest = record[key]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789ABCDEF" for character in digest)
        ):
            raise FlatFunnelError(f"record {index} has malformed {key}")
    return record


def validate_manifest(value: Any, raw: bytes) -> tuple[Mapping[str, Any], ...]:
    if sha256(raw) != MANIFEST_SHA256:
        raise FlatFunnelError("immutable connectivity-manifest hash mismatch")
    if not isinstance(value, dict) or value.get("schema") != MANIFEST_SCHEMA:
        raise FlatFunnelError("connectivity-manifest schema mismatch")
    records_raw = value.get("records")
    if not isinstance(records_raw, list) or len(records_raw) != 252:
        raise FlatFunnelError("connectivity manifest must contain exactly 252 records")
    records = tuple(
        _validate_manifest_record(record, index)
        for index, record in enumerate(records_raw)
    )
    expected = {
        (level, fraction, "none" if fraction == 0 else mask, diagonal)
        for level in LEVELS
        for fraction in FRACTIONS
        for mask in ((None,) if fraction == 0 else MASKS)
        for diagonal in DIAGONALS
    }
    actual = {
        (
            int(record["level"]),
            int(record["s3_area_fraction_percent"]),
            str(record["mask"]),
            str(record["diagonal"]),
        )
        for record in records
    }
    if actual != expected or len(actual) != len(records):
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise FlatFunnelError(
            f"252-record topology coordinates differ: missing={missing} extra={extra}"
        )
    return records


def _phase_includes(phase: str, record: Mapping[str, Any]) -> bool:
    level = int(record["level"])
    mask = str(record["mask"])
    if phase == "4A":
        return level in (20, 40, 80) and mask in ("none", "dispersed", "chain")
    if phase == "4B":
        return level in (20, 40, 80) and mask in (
            "compact_cluster",
            "boundary_band",
            "hole_band",
        )
    if phase == "4C":
        return level == 160
    raise FlatFunnelError(f"unknown flat-funnel phase: {phase}")


def select_phase_records(
    records: Sequence[Mapping[str, Any]], phase: str, *, scope: str = "full"
) -> tuple[tuple[int, Mapping[str, Any]], ...]:
    if phase not in PHASES:
        raise FlatFunnelError(f"unknown flat-funnel phase: {phase}")
    if scope not in PHASE_SCOPES[phase]:
        raise FlatFunnelError(f"phase {phase} does not permit scope {scope!r}")
    selected = tuple(
        (index, record)
        for index, record in enumerate(records)
        if _phase_includes(phase, record)
    )
    if len(selected) != PHASE_COUNTS[phase]:
        raise FlatFunnelError(
            f"phase {phase} count differs: expected={PHASE_COUNTS[phase]} actual={len(selected)}"
        )
    if phase == "4C":
        sentinel = tuple(
            member
            for member in selected
            if member[1]["mask"] == "none"
            or int(member[1]["s3_area_fraction_percent"]) == 25
        )
        if len(sentinel) != 18:
            raise FlatFunnelError("phase 4C sentinel is not exactly 18 records")
        sentinel_indices = {index for index, _record in sentinel}
        completion = tuple(
            member for member in selected if member[0] not in sentinel_indices
        )
        selected = sentinel if scope == "sentinel" else completion
    if len(selected) != SCOPE_COUNTS[(phase, scope)]:
        raise FlatFunnelError(f"phase {phase}/{scope} incremental count differs")
    return selected


def _uppercase_sha256(value: Any, location: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789ABCDEF" for character in value)
    ):
        raise FlatFunnelError(f"{location} must be an uppercase SHA-256")
    return value


def _absolute_regular_file(value: Any, location: str) -> Path:
    path = Path(_plain_string(value, location))
    if not path.is_absolute():
        raise FlatFunnelError(f"{location} must be absolute")
    if not path.is_file() or path.is_symlink():
        raise FlatFunnelError(f"{location} must name a regular non-link file")
    return path


def _lower_git_object(value: Any, location: str) -> str:
    made = _plain_string(value, location)
    if len(made) != 40 or any(character not in "0123456789abcdef" for character in made):
        raise FlatFunnelError(f"{location} must be a lowercase 40-hex Git object")
    return made


def validate_candidate_binding(path: Path) -> Mapping[str, Any]:
    """Validate the exact frozen candidate artifact used by a formal wave."""

    value, raw = strict_json_load(path)
    if raw != canonical_bytes(value):
        raise FlatFunnelError("candidate binding is not canonical JSON")
    binding = _exact_keys(
        value,
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
        "$candidate_binding",
    )
    if (
        binding["schema"] != CANDIDATE_BINDING_SCHEMA
        or binding["candidate_id"] != CANDIDATE_ID
        or binding["formulation_id"] != FORMULATION_ID
        or binding["selector"] != SELECTOR
    ):
        raise FlatFunnelError("candidate binding identity differs")
    _lower_git_object(binding["commit"], "$.candidate_binding.commit")
    _lower_git_object(binding["tree"], "$.candidate_binding.tree")
    artifact = _absolute_regular_file(
        binding["artifact_path"], "$.candidate_binding.artifact_path"
    ).resolve()
    if artifact.stat().st_size <= 0:
        raise FlatFunnelError("candidate artifact is empty")
    digest = _uppercase_sha256(
        binding["artifact_sha256"], "$.candidate_binding.artifact_sha256"
    )
    if sha256(artifact.read_bytes()) != digest:
        raise FlatFunnelError("candidate artifact hash mismatch")
    return binding


def _receipt_plan_coordinate(receipt_phase: str) -> tuple[str, str, int]:
    coordinates = {
        "4A": ("4A", "full", 81),
        "4B": ("4B", "full", 108),
        "4C_SENTINEL": ("4C", "sentinel", 18),
        "4C": ("4C", "completion", 45),
    }
    try:
        return coordinates[receipt_phase]
    except KeyError as exc:
        raise FlatFunnelError(f"unregistered receipt phase: {receipt_phase}") from exc


def validate_phase_plan(
    value: Any,
    raw: bytes,
    records: Sequence[Mapping[str, Any]],
    receipt_phase: str,
) -> Mapping[str, Any]:
    """Validate a stored plan against the immutable manifest, not its claims."""

    if raw != canonical_bytes(value):
        raise FlatFunnelError("stored prerequisite plan is not canonical JSON")
    plan = _exact_keys(
        value,
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
        "$plan",
    )
    expected_phase, expected_scope, expected_plan_count = _receipt_plan_coordinate(
        receipt_phase
    )
    if (
        plan["schema"] != PLAN_SCHEMA
        or plan["selector"] != SELECTOR
        or plan["manifest_sha256"] != MANIFEST_SHA256
        or plan["phase"] != expected_phase
        or plan["scope"] != expected_scope
        or plan["record_count"] != expected_plan_count
        or plan["formal_thresholds"] != FORMAL_THRESHOLDS
        or plan["advisory_review_triggers"] != ADVISORY_THRESHOLDS
    ):
        raise FlatFunnelError(f"stored {receipt_phase} plan identity differs")

    required = PHASE_PREREQUISITES[expected_phase]
    if expected_phase == "4C" and expected_scope == "completion":
        required = (*required, "4C_SENTINEL")
    raw_prerequisites = plan["prerequisites"]
    if not isinstance(raw_prerequisites, list) or len(raw_prerequisites) != len(required):
        raise FlatFunnelError(f"stored {receipt_phase} plan prerequisites differ")
    for index, (raw_binding, expected_name) in enumerate(
        zip(raw_prerequisites, required)
    ):
        binding = _exact_keys(
            raw_binding,
            {"aggregate_sha256", "phase", "plan_sha256", "receipt_sha256"},
            f"$plan.prerequisites[{index}]",
        )
        if binding["phase"] != expected_name:
            raise FlatFunnelError(f"stored {receipt_phase} prerequisite order differs")
        for key in ("aggregate_sha256", "plan_sha256", "receipt_sha256"):
            _uppercase_sha256(binding[key], f"$plan.prerequisites[{index}].{key}")

    selected = select_phase_records(records, expected_phase, scope=expected_scope)
    expected_indices = {index for index, _record in selected}
    observed_indices: set[int] = set()
    shards = plan["shards"]
    if not isinstance(shards, list) or len(shards) != len(DIAGONALS):
        raise FlatFunnelError(f"stored {receipt_phase} plan shard count differs")
    for shard_index, (raw_shard, diagonal) in enumerate(zip(shards, DIAGONALS)):
        shard = _exact_keys(
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
            f"$plan.shards[{shard_index}]",
        )
        scope_id = "" if expected_scope == "full" else f"_{expected_scope.upper()}"
        expected_assignment = (
            f"S3_V2_FLAT_{expected_phase}{scope_id}_{diagonal.upper()}"
        )
        members = shard["records"]
        if (
            shard["schema"] != ASSIGNMENT_SCHEMA
            or shard["assignment_id"] != expected_assignment
            or shard["diagonal"] != diagonal
            or shard["manifest_sha256"] != MANIFEST_SHA256
            or shard["phase"] != expected_phase
            or shard["selector"] != SELECTOR
            or shard["scope"] != expected_scope
            or not isinstance(members, list)
            or len(members) != SCOPE_SHARD_COUNTS[(expected_phase, expected_scope)]
        ):
            raise FlatFunnelError(
                f"stored {receipt_phase} shard {diagonal} identity differs"
            )
        assignment_core = dict(shard)
        assignment_digest = assignment_core.pop("assignment_sha256")
        _uppercase_sha256(
            assignment_digest, f"$plan.shards[{shard_index}].assignment_sha256"
        )
        if sha256(canonical_bytes(assignment_core)) != assignment_digest:
            raise FlatFunnelError(
                f"stored {receipt_phase} shard {diagonal} hash mismatch"
            )
        previous_sort_key: tuple[int, int, int] | None = None
        for member_index, raw_member in enumerate(members):
            member = _exact_keys(
                raw_member,
                {"manifest_index", "record", "record_id"},
                f"$plan.shards[{shard_index}].records[{member_index}]",
            )
            manifest_index = member["manifest_index"]
            if (
                isinstance(manifest_index, bool)
                or not isinstance(manifest_index, int)
                or manifest_index not in expected_indices
                or manifest_index in observed_indices
            ):
                raise FlatFunnelError(
                    f"stored {receipt_phase} manifest index is invalid or duplicated"
                )
            record = records[manifest_index]
            if member["record"] != record or member["record_id"] != record_id(record):
                raise FlatFunnelError(
                    f"stored {receipt_phase} record differs from immutable manifest"
                )
            if record["diagonal"] != diagonal:
                raise FlatFunnelError(
                    f"stored {receipt_phase} record is in the wrong diagonal shard"
                )
            sort_key = (
                int(record["level"]),
                int(record["s3_area_fraction_percent"]),
                MASKS.index(record["mask"]) if record["mask"] in MASKS else -1,
            )
            if previous_sort_key is not None and sort_key < previous_sort_key:
                raise FlatFunnelError(f"stored {receipt_phase} shard ordering differs")
            previous_sort_key = sort_key
            observed_indices.add(manifest_index)
    if observed_indices != expected_indices:
        raise FlatFunnelError(f"stored {receipt_phase} plan coverage differs")
    return plan


def _receipt_prerequisite_phases(phase: str) -> tuple[str, ...]:
    made = {
        "4A": (),
        "4B": ("4A",),
        "4C_SENTINEL": ("4A", "4B"),
        "4C": ("4A", "4B", "4C_SENTINEL"),
    }
    try:
        return made[phase]
    except KeyError as exc:
        raise FlatFunnelError(f"unregistered receipt phase: {phase}") from exc


def _canonical_file(
    raw_path: Any,
    digest: Any,
    *,
    path_location: str,
    digest_location: str,
) -> tuple[Path, Any, bytes, str]:
    path = _absolute_regular_file(raw_path, path_location).resolve()
    expected_digest = _uppercase_sha256(digest, digest_location)
    value, raw = strict_json_load(path)
    if sha256(raw) != expected_digest:
        raise FlatFunnelError(f"{path_location} hash mismatch")
    if raw != canonical_bytes(value):
        raise FlatFunnelError(f"{path_location} is not canonical JSON")
    return path, value, raw, expected_digest


def _validate_wave_manifest(
    value: Any,
    *,
    plan: Mapping[str, Any],
    plan_path: Path,
    plan_sha256: str,
) -> tuple[Mapping[str, Any], tuple[Mapping[str, Any], ...]]:
    manifest = _exact_keys(
        value,
        {"lane", "output_root", "schema", "wave_id", "workers"},
        "$wave_manifest",
    )
    expected_wave_id = (
        f"S3_V2_FLAT_FUNNEL_{plan['phase']}_{str(plan['scope']).upper()}"
    )
    if (
        manifest["schema"] != BOUNDED_MANIFEST_SCHEMA
        or manifest["lane"] != "flat-proof"
        or manifest["wave_id"] != expected_wave_id
    ):
        raise FlatFunnelError("bounded wave manifest identity differs")
    output_root = Path(_plain_string(manifest["output_root"], "$.output_root"))
    if not output_root.is_absolute():
        raise FlatFunnelError("bounded wave output_root must be absolute")
    output_root = output_root.resolve()
    workers = manifest["workers"]
    shards = plan["shards"]
    if (
        not isinstance(workers, list)
        or len(workers) != 3
        or not isinstance(shards, list)
        or len(shards) != 3
    ):
        raise FlatFunnelError("bounded wave must bind the three registered shards")
    validated: list[Mapping[str, Any]] = []
    output_paths: set[Path] = set()
    first_input_hashes: Any = None
    for index, (raw_worker, shard) in enumerate(zip(workers, shards)):
        location = f"$wave_manifest.workers[{index}]"
        worker = _exact_keys(
            raw_worker,
            {
                "assignment_id",
                "assignment_sha256",
                "command",
                "cwd",
                "expected_record_count",
                "expected_selector",
                "input_hashes",
                "plan_path",
                "plan_sha256",
                "progress_path",
                "program_path",
                "program_sha256",
                "scientific_path",
                "scientific_schema",
                "stderr_path",
                "stdout_path",
                "wall_seconds",
            },
            location,
        )
        expected_count = len(shard["records"])
        if (
            worker["assignment_id"] != shard["assignment_id"]
            or worker["assignment_sha256"] != shard["assignment_sha256"]
            or worker["plan_path"] != str(plan_path)
            or worker["plan_sha256"] != plan_sha256
            or worker["expected_selector"] != SELECTOR
            or worker["expected_record_count"] != expected_count
            or worker["scientific_schema"] != SHARD_SCIENTIFIC_SCHEMA
            or worker["wall_seconds"] != 900
        ):
            raise FlatFunnelError(f"bounded worker {index} differs from its plan shard")
        _uppercase_sha256(worker["assignment_sha256"], f"{location}.assignment_sha256")
        _uppercase_sha256(worker["program_sha256"], f"{location}.program_sha256")
        for path_key in (
            "progress_path",
            "scientific_path",
            "stdout_path",
            "stderr_path",
        ):
            path = Path(_plain_string(worker[path_key], f"{location}.{path_key}"))
            if not path.is_absolute():
                raise FlatFunnelError(f"{location}.{path_key} must be absolute")
            path = path.resolve()
            try:
                path.relative_to(output_root)
            except ValueError as exc:
                raise FlatFunnelError(f"{location}.{path_key} escapes output_root") from exc
            if path in output_paths:
                raise FlatFunnelError("bounded worker output paths are not exclusive")
            output_paths.add(path)
        for path_key in ("cwd", "program_path"):
            path = Path(_plain_string(worker[path_key], f"{location}.{path_key}"))
            if not path.is_absolute():
                raise FlatFunnelError(f"{location}.{path_key} must be absolute")
        cwd = Path(worker["cwd"])
        if not cwd.is_dir():
            raise FlatFunnelError(f"{location}.cwd is not a directory")
        program_path = _absolute_regular_file(
            worker["program_path"], f"{location}.program_path"
        ).resolve()
        if sha256(program_path.read_bytes()) != worker["program_sha256"]:
            raise FlatFunnelError("bounded worker program hash mismatch")
        command = worker["command"]
        if (
            not isinstance(command, list)
            or str(worker["program_path"]) not in command
            or str(worker["scientific_path"]) not in command
            or SELECTOR not in command
        ):
            raise FlatFunnelError(f"bounded worker {index} command binding differs")
        input_hashes = worker["input_hashes"]
        if not isinstance(input_hashes, list) or len(input_hashes) != 4:
            raise FlatFunnelError("bounded worker frozen-input set differs")
        if first_input_hashes is None:
            first_input_hashes = input_hashes
        elif input_hashes != first_input_hashes:
            raise FlatFunnelError("bounded workers do not share one frozen-input set")
        previous_path = ""
        role_counts = {
            "candidate_artifact": 0,
            "connectivity_manifest": 0,
            "flat_funnel_contract": 0,
            "source_equation_contract": 0,
        }
        for binding_index, raw_binding in enumerate(input_hashes):
            binding = _exact_keys(
                raw_binding,
                {"path", "sha256"},
                f"{location}.input_hashes[{binding_index}]",
            )
            bound_path = _absolute_regular_file(
                binding["path"], f"{location}.input_hashes[{binding_index}].path"
            ).resolve()
            if str(bound_path) <= previous_path:
                raise FlatFunnelError("bounded worker input bindings are not sorted")
            previous_path = str(bound_path)
            digest = _uppercase_sha256(
                binding["sha256"], f"{location}.input_hashes[{binding_index}].sha256"
            )
            if sha256(bound_path.read_bytes()) != digest:
                raise FlatFunnelError("bounded worker frozen-input hash mismatch")
            raw_input = bound_path.read_bytes()
            if digest == MANIFEST_SHA256:
                input_value = strict_json_bytes(raw_input, label=str(bound_path))
                validate_manifest(input_value, raw_input)
                role_counts["connectivity_manifest"] += 1
                continue
            try:
                input_value = strict_json_bytes(raw_input, label=str(bound_path))
            except FlatFunnelError:
                input_value = None
            if digest == REGISTERED_FLAT_FUNNEL_CONTRACT_SHA256:
                if len(raw_input) != REGISTERED_FLAT_FUNNEL_CONTRACT_BYTES:
                    raise FlatFunnelError("registered flat-funnel contract byte count differs")
                if raw_input != canonical_bytes(input_value):
                    raise FlatFunnelError("registered flat-funnel contract is not canonical JSON")
                validate_contract(input_value)
                role_counts["flat_funnel_contract"] += 1
            elif digest == REGISTERED_SOURCE_CONTRACT_SHA256:
                validate_source_contract(input_value, raw_input)
                role_counts["source_equation_contract"] += 1
            elif (
                isinstance(input_value, dict)
                and input_value.get("schema") == CANDIDATE_BINDING_SCHEMA
            ):
                validate_candidate_binding(bound_path)
                role_counts["candidate_artifact"] += 1
            else:
                raise FlatFunnelError("bounded frozen input has no registered role")
        if role_counts != {name: 1 for name in FROZEN_INPUT_NAMES}:
            raise FlatFunnelError("bounded worker named frozen-input roles differ")
        validated.append(worker)
    return manifest, tuple(validated)


def _validate_shard_scientific(
    scientific_path: Path,
    *,
    shard: Mapping[str, Any],
    plan_sha256: str,
) -> tuple[ValidatedShardEvidence, tuple[str, ...], int]:
    value, raw = strict_json_load(scientific_path)
    if raw != canonical_bytes(value):
        raise FlatFunnelError("shard scientific output is not canonical JSON")
    science = _exact_keys(
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
        "$shard_scientific",
    )
    expected_ids = tuple(member["record_id"] for member in shard["records"])
    if (
        science["schema"] != SHARD_SCIENTIFIC_SCHEMA
        or science["assignment_sha256"] != shard["assignment_sha256"]
        or science["plan_sha256"] != plan_sha256
        or science["selector"] != SELECTOR
        or science["record_count"] != len(expected_ids)
        or science["record_ids"] != list(expected_ids)
        or science["terminal"] != "ACCEPTED_FOR_AGGREGATION"
    ):
        raise FlatFunnelError("shard scientific identity or coverage differs")
    record_ids_digest = _uppercase_sha256(
        science["record_ids_sha256"], "$.shard_scientific.record_ids_sha256"
    )
    if record_ids_digest != sha256(canonical_bytes(list(expected_ids))):
        raise FlatFunnelError("shard scientific record IDs hash mismatch")
    payload_digest = _uppercase_sha256(
        science["scientific_payload_sha256"],
        "$.shard_scientific.scientific_payload_sha256",
    )
    if payload_digest != sha256(canonical_bytes(science["scientific_payload"])):
        raise FlatFunnelError("shard scientific payload hash mismatch")
    return (
        ValidatedShardEvidence(
            assignment_id=str(shard["assignment_id"]),
            assignment_sha256=str(shard["assignment_sha256"]),
            record_count=len(expected_ids),
            record_ids_sha256=record_ids_digest,
            scientific_payload_sha256=payload_digest,
            scientific_sha256=sha256(raw),
        ),
        expected_ids,
        len(raw),
    )


def _validate_wave_result(
    value: Any,
    *,
    manifest: Mapping[str, Any],
    manifest_sha256: str,
    plan: Mapping[str, Any],
    plan_sha256: str,
) -> tuple[tuple[ValidatedShardEvidence, ...], tuple[str, ...]]:
    result = _exact_keys(
        value,
        {"lane", "manifest_sha256", "schema", "terminal", "wave_id", "workers"},
        "$wave_result",
    )
    if (
        result["schema"] != BOUNDED_RESULT_SCHEMA
        or result["lane"] != "flat-proof"
        or result["wave_id"] != manifest["wave_id"]
        or result["manifest_sha256"] != manifest_sha256
        or result["terminal"] != "COMPLETED"
    ):
        raise FlatFunnelError("bounded wave result is not a completed registered wave")
    raw_results = result["workers"]
    workers = manifest["workers"]
    shards = plan["shards"]
    if not isinstance(raw_results, list) or len(raw_results) != 3:
        raise FlatFunnelError("bounded wave result worker coverage differs")
    evidence: list[ValidatedShardEvidence] = []
    record_ids: list[str] = []
    for index, (raw_result, worker, shard) in enumerate(
        zip(raw_results, workers, shards)
    ):
        location = f"$wave_result.workers[{index}]"
        made = _exact_keys(
            raw_result,
            {
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
                "scientific_schema",
                "scientific_sha256",
                "status",
                "stderr_sha256",
                "stdout_sha256",
                "termination_proven",
            },
            location,
        )
        if (
            made["assignment_id"] != worker["assignment_id"]
            or made["assignment_sha256"] != worker["assignment_sha256"]
            or made["plan_sha256"] != plan_sha256
            or made["program_sha256"] != worker["program_sha256"]
            or made["input_hashes"] != worker["input_hashes"]
            or made["scientific_schema"] != SHARD_SCIENTIFIC_SCHEMA
            or made["status"] != "COMPLETED"
            or made["returncode"] != 0
            or made["termination_proven"] is not True
        ):
            raise FlatFunnelError(f"bounded result worker {index} differs or failed")
        for key in (
            "cpu_100ns",
            "last_progress_sequence",
            "peak_tree_memory_bytes",
        ):
            number = made[key]
            if isinstance(number, bool) or not isinstance(number, int) or number < 0:
                raise FlatFunnelError(f"{location}.{key} is invalid")
        for key in ("stdout_sha256", "stderr_sha256", "scientific_sha256"):
            _uppercase_sha256(made[key], f"{location}.{key}")
        for path_key, result_key in (
            ("stdout_path", "stdout_sha256"),
            ("stderr_path", "stderr_sha256"),
        ):
            log_path = _absolute_regular_file(
                worker[path_key], f"$wave_manifest.workers[{index}].{path_key}"
            ).resolve()
            if sha256(log_path.read_bytes()) != made[result_key]:
                raise FlatFunnelError(f"bounded result {path_key} binding differs")
        scientific_path = _absolute_regular_file(
            worker["scientific_path"], f"$wave_manifest.workers[{index}].scientific_path"
        ).resolve()
        shard_evidence, shard_ids, byte_count = _validate_shard_scientific(
            scientific_path,
            shard=shard,
            plan_sha256=plan_sha256,
        )
        if (
            made["scientific_sha256"] != shard_evidence.scientific_sha256
            or made["scientific_byte_count"] != byte_count
        ):
            raise FlatFunnelError("bounded result scientific file binding differs")
        evidence.append(shard_evidence)
        record_ids.extend(shard_ids)
    return tuple(evidence), tuple(record_ids)


def load_validated_receipt(
    receipt_path: Path,
    records: Sequence[Mapping[str, Any]],
    *,
    _stack: set[Path] | None = None,
    _cache: dict[Path, ValidatedReceipt] | None = None,
) -> ValidatedReceipt:
    """Recursively validate a receipt, completed wave, and canonical science."""

    if not receipt_path.is_absolute():
        raise FlatFunnelError("prerequisite receipt path must be absolute")
    checked_path = _absolute_regular_file(str(receipt_path), "$receipt_path").resolve()
    stack = set() if _stack is None else _stack
    cache = {} if _cache is None else _cache
    if checked_path in cache:
        return cache[checked_path]
    if checked_path in stack:
        raise FlatFunnelError("cyclic prerequisite receipt graph")
    stack.add(checked_path)
    try:
        value, raw = strict_json_load(checked_path)
        if raw != canonical_bytes(value):
            raise FlatFunnelError("prerequisite receipt is not canonical JSON")
        receipt = _exact_keys(
            value,
            {
                "aggregate_path",
                "aggregate_sha256",
                "complete_record_count",
                "manifest_sha256",
                "phase",
                "plan_path",
                "plan_sha256",
                "prerequisite_receipt_paths",
                "schema",
                "terminal",
                "wave_manifest_path",
                "wave_manifest_sha256",
                "wave_result_path",
                "wave_result_sha256",
            },
            "$receipt",
        )
        phase = receipt["phase"]
        if receipt["schema"] != RECEIPT_SCHEMA or phase not in RECEIPT_COUNTS:
            raise FlatFunnelError("phase receipt identity mismatch")
        if receipt["terminal"] != SCAFFOLD_RECEIPT_TERMINAL:
            raise FlatFunnelError(
                f"phase {phase} was not validated as nonclassifying scaffold evidence"
            )
        if receipt["manifest_sha256"] != MANIFEST_SHA256:
            raise FlatFunnelError(f"phase {phase} manifest binding mismatch")
        if receipt["complete_record_count"] != RECEIPT_COUNTS[phase]:
            raise FlatFunnelError(f"phase {phase} receipt count mismatch")

        expected_prerequisites = _receipt_prerequisite_phases(str(phase))
        prerequisite_paths = receipt["prerequisite_receipt_paths"]
        if (
            not isinstance(prerequisite_paths, list)
            or len(prerequisite_paths) != len(expected_prerequisites)
        ):
            raise FlatFunnelError(f"phase {phase} prerequisite receipt paths differ")
        predecessors: list[ValidatedReceipt] = []
        seen_paths: set[Path] = set()
        for index, (raw_predecessor_path, expected_phase) in enumerate(
            zip(prerequisite_paths, expected_prerequisites)
        ):
            predecessor_path = _absolute_regular_file(
                raw_predecessor_path,
                f"$.prerequisite_receipt_paths[{index}]",
            ).resolve()
            if predecessor_path in seen_paths:
                raise FlatFunnelError("duplicate prerequisite receipt path")
            seen_paths.add(predecessor_path)
            predecessor = load_validated_receipt(
                predecessor_path,
                records,
                _stack=stack,
                _cache=cache,
            )
            if predecessor.phase != expected_phase:
                raise FlatFunnelError(f"phase {phase} prerequisite order differs")
            predecessors.append(predecessor)

        plan_path, plan, plan_raw, plan_digest = _canonical_file(
            receipt["plan_path"],
            receipt["plan_sha256"],
            path_location="$.plan_path",
            digest_location="$.plan_sha256",
        )
        validate_phase_plan(plan, plan_raw, records, str(phase))
        expected_bindings = [predecessor.plan_binding() for predecessor in predecessors]
        if plan["prerequisites"] != expected_bindings:
            raise FlatFunnelError(f"phase {phase} plan prerequisite token bindings differ")

        wave_manifest_path, wave_manifest, _wave_manifest_raw, wave_manifest_digest = (
            _canonical_file(
                receipt["wave_manifest_path"],
                receipt["wave_manifest_sha256"],
                path_location="$.wave_manifest_path",
                digest_location="$.wave_manifest_sha256",
            )
        )
        del wave_manifest_path
        validated_manifest, _workers = _validate_wave_manifest(
            wave_manifest,
            plan=plan,
            plan_path=plan_path,
            plan_sha256=plan_digest,
        )
        wave_result_path, wave_result, _wave_result_raw, wave_result_digest = (
            _canonical_file(
                receipt["wave_result_path"],
                receipt["wave_result_sha256"],
                path_location="$.wave_result_path",
                digest_location="$.wave_result_sha256",
            )
        )
        try:
            wave_result_path.relative_to(Path(validated_manifest["output_root"]).resolve())
        except ValueError as exc:
            raise FlatFunnelError("bounded wave result path escapes output_root") from exc
        current_shards, current_ids = _validate_wave_result(
            wave_result,
            manifest=validated_manifest,
            manifest_sha256=wave_manifest_digest,
            plan=plan,
            plan_sha256=plan_digest,
        )

        combined_shards = current_shards
        combined_ids = current_ids
        if phase == "4C":
            sentinel = predecessors[-1]
            combined_shards = (*sentinel.shards, *current_shards)
            combined_ids = (*sentinel.record_ids, *current_ids)
        if len(set(combined_ids)) != len(combined_ids):
            raise FlatFunnelError(f"phase {phase} aggregate has duplicate coverage")
        sorted_ids = tuple(sorted(combined_ids))
        sorted_shards = tuple(sorted(combined_shards, key=lambda item: item.assignment_id))
        if len(sorted_ids) != RECEIPT_COUNTS[phase]:
            raise FlatFunnelError(f"phase {phase} validated science count differs")

        _aggregate_path, aggregate, _aggregate_raw, aggregate_digest = _canonical_file(
            receipt["aggregate_path"],
            receipt["aggregate_sha256"],
            path_location="$.aggregate_path",
            digest_location="$.aggregate_sha256",
        )
        made_aggregate = _exact_keys(
            aggregate,
            {
                "complete_record_count",
                "current_wave_record_count",
                "manifest_sha256",
                "phase",
                "plan_sha256",
                "prerequisite_aggregate_sha256s",
                "record_ids",
                "record_ids_sha256",
                "schema",
                "scientific_payload_sha256",
                "selector",
                "shards",
                "terminal",
                "wave_manifest_sha256",
                "wave_result_sha256",
            },
            "$aggregate",
        )
        expected_shard_bindings = [item.aggregate_binding() for item in sorted_shards]
        expected_payload_binding = [
            {
                "assignment_id": item.assignment_id,
                "scientific_payload_sha256": item.scientific_payload_sha256,
            }
            for item in sorted_shards
        ]
        expected_aggregate = {
            "complete_record_count": RECEIPT_COUNTS[phase],
            "current_wave_record_count": plan["record_count"],
            "manifest_sha256": MANIFEST_SHA256,
            "phase": phase,
            "plan_sha256": plan_digest,
            "prerequisite_aggregate_sha256s": [
                predecessor.aggregate_sha256 for predecessor in predecessors
            ],
            "record_ids": list(sorted_ids),
            "record_ids_sha256": sha256(canonical_bytes(list(sorted_ids))),
            "schema": SCIENTIFIC_AGGREGATE_SCHEMA,
            "scientific_payload_sha256": sha256(
                canonical_bytes(expected_payload_binding)
            ),
            "selector": SELECTOR,
            "shards": expected_shard_bindings,
            "terminal": SCAFFOLD_RECEIPT_TERMINAL,
            "wave_manifest_sha256": wave_manifest_digest,
            "wave_result_sha256": wave_result_digest,
        }
        if dict(made_aggregate) != expected_aggregate:
            raise FlatFunnelError(f"phase {phase} scientific aggregate differs")

        made_receipt = ValidatedReceipt(
            phase=str(phase),
            plan_sha256=plan_digest,
            aggregate_sha256=aggregate_digest,
            receipt_sha256=sha256(raw),
            receipt_path=checked_path,
            record_ids=sorted_ids,
            shards=sorted_shards,
            _token=_VALIDATED_RECEIPT_TOKEN,
        )
        cache[checked_path] = made_receipt
        return made_receipt
    finally:
        stack.remove(checked_path)


def _validate_receipts(
    phase: str,
    scope: str,
    receipts: Iterable[ValidatedReceipt],
) -> tuple[dict[str, str], ...]:
    required = PHASE_PREREQUISITES[phase]
    if phase == "4C" and scope == "completion":
        required = (*required, "4C_SENTINEL")
    accepted: dict[str, ValidatedReceipt] = {}
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, ValidatedReceipt):
            raise FlatFunnelError(
                f"receipt[{index}] was not created by load_validated_receipt"
            )
        if receipt._token is not _VALIDATED_RECEIPT_TOKEN:
            raise FlatFunnelError(
                f"receipt[{index}] was not created by load_validated_receipt"
            )
        made_phase = receipt.phase
        if made_phase not in RECEIPT_COUNTS:
            raise FlatFunnelError("phase receipt identity mismatch")
        if made_phase in accepted:
            raise FlatFunnelError(f"duplicate phase receipt: {made_phase}")
        accepted[made_phase] = receipt
    missing = [item for item in required if item not in accepted]
    if missing:
        raise FlatFunnelError(
            f"phase {phase} prerequisites are incomplete: missing={missing}"
        )
    unexpected = sorted(set(accepted) - set(required))
    if unexpected:
        raise FlatFunnelError(
            f"phase {phase} has unregistered prerequisite receipts: {unexpected}"
        )
    return tuple(accepted[item].plan_binding() for item in required)


def build_phase_plan(
    records: Sequence[Mapping[str, Any]],
    phase: str,
    *,
    scope: str = "full",
    receipts: Iterable[ValidatedReceipt] = (),
) -> dict[str, Any]:
    if phase not in PHASES or scope not in PHASE_SCOPES[phase]:
        raise FlatFunnelError(f"unregistered phase/scope: {phase}/{scope}")
    prerequisites = _validate_receipts(phase, scope, receipts)
    selected = select_phase_records(records, phase, scope=scope)
    shards: list[dict[str, Any]] = []
    for diagonal in DIAGONALS:
        members = [
            {
                "manifest_index": index,
                "record": dict(record),
                "record_id": record_id(record),
            }
            for index, record in selected
            if record["diagonal"] == diagonal
        ]
        members.sort(
            key=lambda item: (
                int(item["record"]["level"]),
                int(item["record"]["s3_area_fraction_percent"]),
                MASKS.index(item["record"]["mask"])
                if item["record"]["mask"] in MASKS
                else -1,
            )
        )
        if len(members) != SCOPE_SHARD_COUNTS[(phase, scope)]:
            raise FlatFunnelError(f"phase {phase}/{scope} shard {diagonal} count differs")
        scope_id = "" if scope == "full" else f"_{scope.upper()}"
        assignment_id = f"S3_V2_FLAT_{phase}{scope_id}_{diagonal.upper()}"
        assignment_core = {
            "assignment_id": assignment_id,
            "diagonal": diagonal,
            "manifest_sha256": MANIFEST_SHA256,
            "phase": phase,
            "records": members,
            "schema": ASSIGNMENT_SCHEMA,
            "selector": SELECTOR,
            "scope": scope,
        }
        shards.append(
            {
                **assignment_core,
                "assignment_sha256": sha256(canonical_bytes(assignment_core)),
            }
        )
    plan = {
        "advisory_review_triggers": ADVISORY_THRESHOLDS,
        "formal_thresholds": FORMAL_THRESHOLDS,
        "manifest_sha256": MANIFEST_SHA256,
        "phase": phase,
        "prerequisites": list(prerequisites),
        "record_count": SCOPE_COUNTS[(phase, scope)],
        "schema": PLAN_SCHEMA,
        "selector": SELECTOR,
        "shards": shards,
        "scope": scope,
    }
    return plan


def progress_record(
    assignment_id: str,
    *,
    sequence: int,
    phase: str,
    completed: int,
    total: int,
) -> dict[str, Any]:
    _plain_string(assignment_id, "assignment_id")
    _plain_string(phase, "phase")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (sequence, completed, total)):
        raise FlatFunnelError("progress sequence and counts must be integers")
    if sequence < 0 or completed < 0 or total < 0 or completed > total:
        raise FlatFunnelError("progress sequence or counts are out of range")
    return {
        "assignment_id": assignment_id,
        "completed": completed,
        "phase": phase,
        "schema": PROGRESS_SCHEMA,
        "sequence": sequence,
        "total": total,
    }


def append_progress(path: Path, record: Mapping[str, Any]) -> None:
    expected = progress_record(
        str(record.get("assignment_id", "")),
        sequence=record.get("sequence"),  # type: ignore[arg-type]
        phase=str(record.get("phase", "")),
        completed=record.get("completed"),  # type: ignore[arg-type]
        total=record.get("total"),  # type: ignore[arg-type]
    )
    if dict(record) != expected:
        raise FlatFunnelError("progress record has extra or altered fields")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, canonical_bytes(expected))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def build_bounded_wave_manifest(
    plan: Mapping[str, Any],
    *,
    plan_path: Path,
    producer_program: Path,
    python_executable: Path,
    cwd: Path,
    output_root: Path,
    input_paths: Mapping[str, Path],
) -> dict[str, Any]:
    if plan.get("schema") != PLAN_SCHEMA or plan.get("selector") != SELECTOR:
        raise FlatFunnelError("cannot launch an unbound flat-funnel plan")
    plan_path = plan_path.resolve()
    producer_program = producer_program.resolve()
    if not plan_path.is_file() or plan_path.is_symlink():
        raise FlatFunnelError("bounded plan path is not a regular non-link file")
    if not producer_program.is_file() or producer_program.is_symlink():
        raise FlatFunnelError("bounded producer path is not a regular non-link file")
    plan_raw = plan_path.read_bytes()
    if plan_raw != canonical_bytes(plan):
        raise FlatFunnelError("bounded plan path does not contain the supplied plan")
    plan_sha256 = sha256(plan_raw)
    program_sha256 = sha256(producer_program.read_bytes())
    if not isinstance(input_paths, Mapping) or set(input_paths) != FROZEN_INPUT_NAMES:
        actual = sorted(input_paths) if isinstance(input_paths, Mapping) else type(input_paths).__name__
        raise FlatFunnelError(
            f"bounded wave frozen-input names differ: expected={sorted(FROZEN_INPUT_NAMES)} actual={actual}"
        )
    resolved_by_name = {name: input_paths[name].resolve() for name in FROZEN_INPUT_NAMES}
    if len(set(resolved_by_name.values())) != len(FROZEN_INPUT_NAMES):
        raise FlatFunnelError("bounded wave frozen inputs must be distinct files")
    candidate_path = resolved_by_name["candidate_artifact"]
    if not candidate_path.is_file() or candidate_path.is_symlink():
        raise FlatFunnelError("candidate_artifact must be a regular non-link binding file")
    validate_candidate_binding(candidate_path)
    connectivity_path = resolved_by_name["connectivity_manifest"]
    connectivity_value, connectivity_raw = strict_json_load(connectivity_path)
    validate_manifest(connectivity_value, connectivity_raw)
    contract_path = resolved_by_name["flat_funnel_contract"]
    contract_value, contract_raw = strict_json_load(contract_path)
    if contract_raw != canonical_bytes(contract_value):
        raise FlatFunnelError("flat_funnel_contract is not canonical JSON")
    validate_contract(contract_value)
    source_path = resolved_by_name["source_equation_contract"]
    source_value, source_raw = strict_json_load(source_path)
    validate_source_contract(source_value, source_raw)
    resolved_inputs = sorted(resolved_by_name.values(), key=str)
    input_hashes: list[dict[str, str]] = []
    for path in resolved_inputs:
        if not path.is_file() or path.is_symlink():
            raise FlatFunnelError(f"bounded input is not a regular non-link file: {path}")
        input_hashes.append({"path": str(path), "sha256": sha256(path.read_bytes())})
    phase = str(plan["phase"])
    scope = str(plan["scope"])
    workers: list[dict[str, Any]] = []
    for shard_index, shard in enumerate(plan["shards"]):
        assignment_id = str(shard["assignment_id"])
        worker_root = output_root / assignment_id
        workers.append(
            {
                "assignment_id": assignment_id,
                "assignment_sha256": str(shard["assignment_sha256"]),
                "command": [
                    str(python_executable),
                    str(producer_program),
                    "--run-flat-assignment",
                    str(plan_path),
                    "--shard-index",
                    str(shard_index),
                    "--selector",
                    SELECTOR,
                    "--output",
                    str(worker_root / "scientific.json"),
                    "--progress",
                    str(worker_root / "progress.jsonl"),
                ],
                "cwd": str(cwd.resolve()),
                "expected_record_count": len(shard["records"]),
                "expected_selector": SELECTOR,
                "input_hashes": input_hashes,
                "plan_path": str(plan_path),
                "plan_sha256": plan_sha256,
                "progress_path": str((worker_root / "progress.jsonl").resolve()),
                "program_path": str(producer_program),
                "program_sha256": program_sha256,
                "scientific_path": str((worker_root / "scientific.json").resolve()),
                "scientific_schema": SHARD_SCIENTIFIC_SCHEMA,
                "stderr_path": str((worker_root / "stderr.log").resolve()),
                "stdout_path": str((worker_root / "stdout.log").resolve()),
                "wall_seconds": 900,
            }
        )
    return {
        "lane": "flat-proof",
        "output_root": str(output_root.resolve()),
        "schema": BOUNDED_MANIFEST_SCHEMA,
        "wave_id": f"S3_V2_FLAT_FUNNEL_{phase}_{scope.upper()}",
        "workers": workers,
    }


def _write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--phase", choices=PHASES, required=True)
    parser.add_argument("--scope", choices=("full", "sentinel", "completion"), default="full")
    parser.add_argument("--prerequisite-receipt", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    contract, _contract_raw = strict_json_load(arguments.contract)
    validate_contract(contract)
    manifest, manifest_raw = strict_json_load(arguments.manifest)
    records = validate_manifest(manifest, manifest_raw)
    receipts = [
        load_validated_receipt(path.resolve(), records)
        for path in arguments.prerequisite_receipt
    ]
    plan = build_phase_plan(
        records,
        arguments.phase,
        scope=arguments.scope,
        receipts=receipts,
    )
    _write_exclusive(arguments.output, canonical_bytes(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
