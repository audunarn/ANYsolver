"""Self-describing counts, producer settings, and object hashes for F03 evidence."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_evidence_index as evidence_index
from scripts import _b3_e4_f03_local_scientific_numerical_storage as numerical
from scripts import _b3_e4_f03_local_scientific_port_storage as ports
from scripts import _b3_e4_f03_local_scientific_sparse_storage as sparse_storage
from scripts import _b3_e4_f03_sparse_factor_candidate as factor_candidate


SCHEMA = "f03_local_scientific_numerical_index_v1"
MAX_INDEX_BYTES = cases.NUMERICAL_INDEX_BYTES
DIGEST = frozenset("0123456789abcdef")


def _digest(value: object) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= DIGEST


@dataclass(frozen=True, slots=True)
class KKTProducerRecord:
    ordering: str
    pivot_threshold: float
    equilibration: bool
    symmetric_mode: bool
    iterative_refinement: str
    factorization_count: int
    factor_nnz: int
    candidate_rhs_solves: int
    certificate_solve_calls: int
    certificate_rhs_attempted: int
    certificate_rhs_completed: int
    recovery_factorizations: int
    recovery_solves: int
    qualification_status: str
    status: str
    reason: str

    def __post_init__(self):
        if (
            self.ordering != "COLAMD"
            or type(self.pivot_threshold) is not float
            or self.pivot_threshold != 1.0
            or type(self.equilibration) is not bool
            or self.equilibration
            or type(self.symmetric_mode) is not bool
            or self.symmetric_mode
            or self.iterative_refinement != "NOREFINE"
            or any(
                type(value) is not int or value < 0
                for value in (
                    self.factorization_count, self.factor_nnz,
                    self.candidate_rhs_solves, self.certificate_solve_calls,
                    self.certificate_rhs_attempted, self.certificate_rhs_completed,
                    self.recovery_factorizations, self.recovery_solves,
                )
            )
            or self.factorization_count != 1
            or self.factor_nnz <= 0
            or self.candidate_rhs_solves != 1
            or self.certificate_solve_calls <= 0
            or self.certificate_rhs_attempted <= 0
            or self.certificate_rhs_completed != self.certificate_rhs_attempted
            or self.recovery_factorizations != 0
            or self.recovery_solves != 0
            or self.qualification_status != "NOT_QUALIFIED"
            or self.status != "SUCCEEDED"
            or self.reason != "completed"
        ):
            raise ValueError("invalid frozen F03 KKT producer record")


def kkt_producer(
    plan: archive.CaseArchivePlan,
    work: object,
    *,
    status: str,
    reason: str,
) -> KKTProducerRecord:
    if type(plan) is not archive.CaseArchivePlan:
        raise ValueError("validated F03 archive plan required")
    try:
        raw = dict(work)
    except (TypeError, ValueError) as exc:
        raise ValueError("exact F03 KKT producer work record required") from exc
    keys = {
        "factorizations", "factor_nnz", "candidate_rhs_solves",
        "certificate_solve_calls", "certificate_rhs_attempted",
        "certificate_rhs_completed", "qualification_status",
    }
    if set(raw) != keys:
        raise ValueError("invalid F03 KKT producer work inventory")
    record = KKTProducerRecord(
        "COLAMD", 1.0, False, False, "NOREFINE",
        raw["factorizations"], raw["factor_nnz"], raw["candidate_rhs_solves"],
        raw["certificate_solve_calls"], raw["certificate_rhs_attempted"],
        raw["certificate_rhs_completed"], 0, 0, raw["qualification_status"],
        status, reason,
    )
    if (
        record.factor_nnz > cases.MAX_KKT_FACTOR_NNZ
        or record.certificate_solve_calls != len(plan.inverse_blocks)
        or record.certificate_rhs_attempted != plan.kkt_order
        or record.certificate_rhs_completed != plan.kkt_order
    ):
        raise ValueError("F03 KKT producer work disagrees with frozen plan")
    return record


def successful_kkt_producer(
    plan: archive.CaseArchivePlan, factor_nnz: int,
) -> KKTProducerRecord:
    return kkt_producer(
        plan,
        {
            "factorizations": 1,
            "factor_nnz": factor_nnz,
            "candidate_rhs_solves": 1,
            "certificate_solve_calls": len(plan.inverse_blocks),
            "certificate_rhs_attempted": plan.kkt_order,
            "certificate_rhs_completed": plan.kkt_order,
            "qualification_status": "NOT_QUALIFIED",
        },
        status="SUCCEEDED",
        reason="completed",
    )


@dataclass(frozen=True, slots=True)
class PositivityProducerRecord:
    ordering: str
    pivot_threshold: float
    equilibration: bool
    symmetric_mode: bool
    iterative_refinement: str
    factor_preparation: str
    factorization_count: int
    rhs_solve_count: int
    factor_nnz: int
    factor_storage_bytes: int
    status: str
    reason: str | None
    qualification_status: str
    matrix_sha256: str
    lower_sha256: str
    upper_sha256: str

    def __post_init__(self):
        if (
            self.ordering != "MMD_AT_PLUS_A"
            or type(self.pivot_threshold) is not float
            or self.pivot_threshold != 0.0
            or type(self.equilibration) is not bool
            or self.equilibration
            or type(self.symmetric_mode) is not bool
            or not self.symmetric_mode
            or self.iterative_refinement != "NOREFINE"
            or self.factor_preparation != "validated stable index permutation; no value arithmetic"
            or self.factorization_count != 1
            or self.rhs_solve_count != 0
            or type(self.factor_nnz) is not int
            or not 0 < self.factor_nnz <= cases.MAX_COMBINED_FACTOR_NNZ
            or type(self.factor_storage_bytes) is not int
            or not 0 < self.factor_storage_bytes <= cases.MAX_CANONICAL_FACTOR_BYTES
            or self.status not in ("CANDIDATE_CREATED", "HOLD")
            or (self.reason is not None and (type(self.reason) is not str or not self.reason))
            or (self.status == "CANDIDATE_CREATED") != (self.reason is None)
            or self.qualification_status != "NOT_QUALIFIED"
            or any(not _digest(value) for value in (
                self.matrix_sha256, self.lower_sha256, self.upper_sha256,
            ))
        ):
            raise ValueError("invalid frozen F03 positivity producer record")


@dataclass(frozen=True, slots=True)
class ObjectDigest:
    name: str
    sha256: str

    def __post_init__(self):
        if type(self.name) is not str or not self.name or not _digest(self.sha256):
            raise ValueError("invalid F03 numerical object digest")


@dataclass(frozen=True, slots=True)
class NumericalIndex:
    schema: str
    case_id: str
    source_commit: str
    plan_sha256: str
    operator_primary: numerical.OperatorCounts
    operator_alternate: numerical.OperatorCounts
    scaled: numerical.ScaledCounts
    positivity: numerical.PositivityCounts
    port_counts: ports.PortCounts
    kkt_producer: KKTProducerRecord
    positivity_producer: PositivityProducerRecord
    objects: tuple[ObjectDigest, ...]

    def __post_init__(self):
        if (
            self.schema != SCHEMA
            or type(self.case_id) is not str
            or type(self.source_commit) is not str
            or len(self.source_commit) != 40
            or set(self.source_commit) - DIGEST
            or not _digest(self.plan_sha256)
            or type(self.operator_primary) is not numerical.OperatorCounts
            or type(self.operator_alternate) is not numerical.OperatorCounts
            or type(self.scaled) is not numerical.ScaledCounts
            or type(self.positivity) is not numerical.PositivityCounts
            or type(self.port_counts) is not ports.PortCounts
            or type(self.kkt_producer) is not KKTProducerRecord
            or type(self.positivity_producer) is not PositivityProducerRecord
            or type(self.objects) is not tuple
            or tuple(item.name for item in self.objects) != _object_names()
            or any(type(item) is not ObjectDigest for item in self.objects)
        ):
            raise ValueError("invalid complete F03 numerical index")


@dataclass(frozen=True, slots=True)
class NumericalEvidence:
    operator_primary: numerical.OperatorEvidence
    operator_alternate: numerical.OperatorEvidence
    scaled: numerical.ScaledEvidence
    positivity: numerical.PositivityEvidence
    port_evidence: ports.PortEvidence


def _object_names() -> tuple[str, ...]:
    result = []
    for group in ("operators_primary", "operators_alternate"):
        result.extend(f"{group}.{name}" for name in ("shell", "beam", "root", "load"))
    result.extend(
        f"scaled_state.{name}" for name in (
            "kbar", "cbar", "h", "kbar_alternate", "cbar_alternate",
            "h_alternate", "d", "r", "b", "b_alternate", "z", "q", "eta", "h_z",
        )
    )
    result.extend(
        f"positivity.{name}" for name in (
            "kbar", "lower", "upper", "diagonal", "row_map", "column_map",
            "inverse_gather",
        )
    )
    for index in range(ports.PORTS):
        result.extend((f"ports.port_{index:02d}_operator", f"ports.port_{index:02d}_action"))
    result.extend(("ports.root", "ports.tip", "ports.free_slope"))
    return tuple(result)


def _hash_parts(kind: str, shape: tuple[int, ...], dtype: str, parts) -> str:
    digest = hashlib.sha256()
    digest.update(b"F03_NUMERICAL_OBJECT_V1\0")
    for value in (kind, dtype, *(str(item) for item in shape)):
        encoded = value.encode("ascii")
        digest.update(len(encoded).to_bytes(4, "little") + encoded)
    for part in parts:
        payload = np.ascontiguousarray(part).tobytes()
        digest.update(len(payload).to_bytes(8, "little") + payload)
    return digest.hexdigest()


def _hash_sparse(value, spec: sparse_storage.SparseSpec) -> str:
    sparse_storage._check_matrix(value, spec)
    arrays = sparse_storage.encode({spec.name: value}, (spec,))
    return _hash_parts(
        spec.format, spec.shape, "<f8,<i8,<i8",
        (
            arrays[spec.name + "_data"], arrays[spec.name + "_indices"],
            arrays[spec.name + "_indptr"],
        ),
    )


def _hash_array(value: np.ndarray) -> str:
    if type(value) is not np.ndarray or not value.flags.c_contiguous:
        raise ValueError("owned contiguous F03 numerical array required")
    if value.dtype == np.dtype(np.float64):
        if not np.isfinite(value).all():
            raise ValueError("finite F03 numerical array required")
        canonical = np.asarray(value, dtype="<f8").copy()
    elif value.dtype == np.dtype(np.int64):
        canonical = np.asarray(value, dtype="<i8").copy()
    else:
        raise ValueError("native float64 or int64 F03 numerical array required")
    return _hash_parts("dense_c", value.shape, canonical.dtype.str, (canonical,))


def positivity_producer(
    value: numerical.PositivityEvidence, metadata: object,
) -> PositivityProducerRecord:
    if type(value) is not numerical.PositivityEvidence:
        raise ValueError("typed F03 positivity evidence required")
    try:
        raw = dict(metadata)
    except (TypeError, ValueError) as exc:
        raise ValueError("exact F03 positivity producer metadata required") from exc
    fields = tuple(PositivityProducerRecord.__dataclass_fields__)
    if set(raw) != set(fields):
        raise ValueError("invalid F03 positivity producer metadata inventory")
    record = PositivityProducerRecord(**{name: raw[name] for name in fields})
    if (
        record.factor_nnz != value.lower.nnz + value.upper.nnz
        or record.matrix_sha256 != factor_candidate._digest_owned(value.kbar)
        or record.lower_sha256 != factor_candidate._digest_owned(value.lower)
        or record.upper_sha256 != factor_candidate._digest_owned(value.upper)
    ):
        raise ValueError("F03 positivity producer hashes or factor count disagree")
    return record


def successful_positivity_producer(
    value: numerical.PositivityEvidence,
) -> PositivityProducerRecord:
    metadata = {
        "ordering": "MMD_AT_PLUS_A",
        "pivot_threshold": 0.0,
        "equilibration": False,
        "symmetric_mode": True,
        "iterative_refinement": "NOREFINE",
        "factor_preparation": "validated stable index permutation; no value arithmetic",
        "factorization_count": 1,
        "rhs_solve_count": 0,
        "factor_nnz": value.lower.nnz + value.upper.nnz,
        "factor_storage_bytes": factor_candidate._bytes(value.lower) + factor_candidate._bytes(value.upper),
        "status": "CANDIDATE_CREATED",
        "reason": None,
        "qualification_status": "NOT_QUALIFIED",
        "matrix_sha256": factor_candidate._digest_owned(value.kbar),
        "lower_sha256": factor_candidate._digest_owned(value.lower),
        "upper_sha256": factor_candidate._digest_owned(value.upper),
    }
    return positivity_producer(value, metadata)


def _counts(value: NumericalEvidence, case: cases.ScientificCase):
    if type(value) is not NumericalEvidence:
        raise ValueError("typed complete F03 numerical evidence required")
    primary = numerical._operator_counts(value.operator_primary, case)
    alternate = numerical._operator_counts(value.operator_alternate, case)
    scaled = numerical._scaled_counts(value.scaled, case)
    positivity = numerical._positivity_counts(value.positivity, case)
    port_matrices, _ = ports._validate(value.port_evidence)
    port_counts = ports.PortCounts(
        tuple(port_matrices[f"port_{index:02d}"].nnz for index in range(ports.PORTS)),
        port_matrices["root"].nnz, port_matrices["tip"].nnz,
        port_matrices["free_slope"].nnz,
    )
    return primary, alternate, scaled, positivity, port_counts


def _digests(value: NumericalEvidence, case: cases.ScientificCase, counts) -> tuple[ObjectDigest, ...]:
    primary, alternate, scaled, positivity, port_counts = counts
    result = []
    for prefix, group, group_counts in (
        ("operators_primary", value.operator_primary, primary),
        ("operators_alternate", value.operator_alternate, alternate),
    ):
        sparse_specs, array_specs = numerical.operator_specs(case, group_counts)
        for spec in sparse_specs:
            result.append(ObjectDigest(f"{prefix}.{spec.name}", _hash_sparse(getattr(group, spec.name), spec)))
        numerical._array_values(group, array_specs)
        result.append(ObjectDigest(f"{prefix}.load", _hash_array(group.load)))
    for prefix, group, specs_and_arrays in (
        ("scaled_state", value.scaled, numerical.scaled_specs(case, scaled)),
        ("positivity", value.positivity, numerical.positivity_specs(case, positivity)),
    ):
        sparse_specs, array_specs = specs_and_arrays
        for spec in sparse_specs:
            result.append(ObjectDigest(f"{prefix}.{spec.name}", _hash_sparse(getattr(group, spec.name), spec)))
        numerical._array_values(group, array_specs)
        for spec in array_specs:
            result.append(ObjectDigest(f"{prefix}.{spec.name}", _hash_array(getattr(group, spec.name))))
    port_specs, _ = ports.port_specs(case, port_counts)
    port_matrices, actions = ports._validate(value.port_evidence)
    for index, spec in enumerate(port_specs[:ports.PORTS]):
        result.append(ObjectDigest(f"ports.port_{index:02d}_operator", _hash_sparse(port_matrices[spec.name], spec)))
        result.append(ObjectDigest(f"ports.port_{index:02d}_action", _hash_array(actions[index].copy())))
    for spec in port_specs[ports.PORTS:]:
        result.append(ObjectDigest(f"ports.{spec.name}", _hash_sparse(port_matrices[spec.name], spec)))
    return tuple(result)


def build_index(
    plan: archive.CaseArchivePlan,
    value: NumericalEvidence,
    kkt_producer: KKTProducerRecord,
    positivity_producer_record: PositivityProducerRecord,
) -> NumericalIndex:
    if (
        type(plan) is not archive.CaseArchivePlan
        or type(kkt_producer) is not KKTProducerRecord
        or type(positivity_producer_record) is not PositivityProducerRecord
    ):
        raise ValueError("validated F03 plan and producer records required")
    case = cases.case_by_id(plan.case_id)
    counts = _counts(value, case)
    numerical.operator_specs(case, counts[0])
    numerical.operator_specs(case, counts[1])
    numerical.scaled_specs(case, counts[2])
    numerical.positivity_specs(case, counts[3])
    ports.port_specs(case, counts[4])
    if (
        kkt_producer.factorization_count != 1
        or kkt_producer.factor_nnz > cases.MAX_KKT_FACTOR_NNZ
        or kkt_producer.candidate_rhs_solves != 1
        or kkt_producer.certificate_solve_calls != len(plan.inverse_blocks)
        or kkt_producer.certificate_rhs_attempted != plan.kkt_order
        or kkt_producer.certificate_rhs_completed != plan.kkt_order
        or positivity_producer(value.positivity, _count_payload(positivity_producer_record))
            != positivity_producer_record
    ):
        raise ValueError("F03 numerical producer records disagree with frozen plan or evidence")
    return NumericalIndex(
        SCHEMA, plan.case_id, plan.source_commit,
        hashlib.sha256(archive._payload(plan)).hexdigest(),
        *counts, kkt_producer, positivity_producer_record,
        _digests(value, case, counts),
    )


def _count_payload(value) -> dict:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}


def _payload(index: NumericalIndex) -> bytes:
    if type(index) is not NumericalIndex:
        raise ValueError("validated F03 numerical index required")
    value = {
        "schema": index.schema,
        "case_id": index.case_id,
        "source_commit": index.source_commit,
        "plan_sha256": index.plan_sha256,
        "counts": {
            "operator_primary": _count_payload(index.operator_primary),
            "operator_alternate": _count_payload(index.operator_alternate),
            "scaled": _count_payload(index.scaled),
            "positivity": _count_payload(index.positivity),
            "ports": _count_payload(index.port_counts),
        },
        "producers": {
            "kkt": _count_payload(index.kkt_producer),
            "positivity": _count_payload(index.positivity_producer),
        },
        "objects": [{"name": item.name, "sha256": item.sha256} for item in index.objects],
    }
    payload = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    if len(payload) > MAX_INDEX_BYTES:
        raise ValueError("F03 numerical index exceeds declared bound")
    return payload


def write_index(path: Path, index: NumericalIndex) -> str:
    payload = _payload(index)
    with Path(path).open("xb") as stream:
        stream.write(payload)
    return hashlib.sha256(payload).hexdigest()


def _exact_dict(value, keys: tuple[str, ...], label: str) -> dict:
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError(f"invalid F03 numerical {label} inventory")
    return value


def _decode(payload: bytes, plan: archive.CaseArchivePlan) -> NumericalIndex:
    if type(payload) is not bytes or len(payload) > MAX_INDEX_BYTES:
        raise ValueError("invalid bounded F03 numerical index payload")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid F03 numerical index JSON") from exc
    _exact_dict(
        value,
        ("schema", "case_id", "source_commit", "plan_sha256", "counts", "producers", "objects"),
        "index",
    )
    counts = _exact_dict(
        value["counts"],
        ("operator_primary", "operator_alternate", "scaled", "positivity", "ports"),
        "count",
    )
    def construct(cls, raw, label):
        fields = tuple(cls.__dataclass_fields__)
        return cls(**_exact_dict(raw, fields, label))
    primary = construct(numerical.OperatorCounts, counts["operator_primary"], "primary count")
    alternate = construct(numerical.OperatorCounts, counts["operator_alternate"], "alternate count")
    scaled = construct(numerical.ScaledCounts, counts["scaled"], "scaled count")
    positivity = construct(numerical.PositivityCounts, counts["positivity"], "positivity count")
    port_raw = _exact_dict(counts["ports"], tuple(ports.PortCounts.__dataclass_fields__), "port count")
    if type(port_raw["ports"]) is not list:
        raise ValueError("invalid F03 numerical port count inventory")
    port_counts = ports.PortCounts(tuple(port_raw["ports"]), port_raw["root"], port_raw["tip"], port_raw["free_slope"])
    producers = _exact_dict(value["producers"], ("kkt", "positivity"), "producer")
    kkt_producer = construct(KKTProducerRecord, producers["kkt"], "KKT producer")
    positivity_record = construct(
        PositivityProducerRecord, producers["positivity"], "positivity producer",
    )
    if type(value["objects"]) is not list:
        raise ValueError("invalid F03 numerical object inventory")
    objects = tuple(
        ObjectDigest(**_exact_dict(item, ("name", "sha256"), "object"))
        for item in value["objects"]
    )
    index = NumericalIndex(
        value["schema"], value["case_id"], value["source_commit"], value["plan_sha256"],
        primary, alternate, scaled, positivity, port_counts,
        kkt_producer, positivity_record, objects,
    )
    case = cases.case_by_id(plan.case_id)
    numerical.operator_specs(case, primary)
    numerical.operator_specs(case, alternate)
    numerical.scaled_specs(case, scaled)
    numerical.positivity_specs(case, positivity)
    ports.port_specs(case, port_counts)
    if (
        index.case_id != plan.case_id
        or index.source_commit != plan.source_commit
        or index.plan_sha256 != hashlib.sha256(archive._payload(plan)).hexdigest()
        or index.kkt_producer.factorization_count != 1
        or index.kkt_producer.factor_nnz > cases.MAX_KKT_FACTOR_NNZ
        or index.kkt_producer.candidate_rhs_solves != 1
        or index.kkt_producer.certificate_solve_calls != len(plan.inverse_blocks)
        or index.kkt_producer.certificate_rhs_attempted != plan.kkt_order
        or index.kkt_producer.certificate_rhs_completed != plan.kkt_order
        or _payload(index) != payload
    ):
        raise ValueError("stale or noncanonical F03 numerical index")
    return index


def read_index(path: Path, plan: archive.CaseArchivePlan) -> tuple[NumericalIndex, str]:
    path = Path(path)
    with evidence_index._open_no_follow(path) as stream:
        payload = stream.read(MAX_INDEX_BYTES + 1)
    if len(payload) > MAX_INDEX_BYTES:
        raise ValueError("F03 numerical index exceeds declared bound")
    return _decode(payload, plan), hashlib.sha256(payload).hexdigest()


def read_saved(directory: Path, plan: archive.CaseArchivePlan) -> tuple[NumericalIndex, NumericalEvidence]:
    directory = Path(directory)
    index, _ = read_index(directory / "numerical_index.json", plan)
    case = cases.case_by_id(plan.case_id)
    value = NumericalEvidence(
        numerical.read_operators(directory / "operators_primary.npz", case, index.operator_primary),
        numerical.read_operators(directory / "operators_alternate.npz", case, index.operator_alternate),
        numerical.read_scaled(directory / "scaled_state.npz", case, index.scaled),
        numerical.read_positivity(directory / "positivity.npz", case, index.positivity),
        ports.read_ports(directory / "ports.npz", case, index.port_counts),
    )
    if build_index(
        plan, value, index.kkt_producer, index.positivity_producer,
    ) != index:
        raise ValueError("mismatched F03 saved numerical object digest")
    return index, value
