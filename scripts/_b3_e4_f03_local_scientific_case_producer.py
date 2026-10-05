"""Exclusive, single-attempt producer for one frozen F03 scientific case.

This module only creates evidence.  It does not supervise a process, retry a
case, write terminal or case receipts, register a run, or adjudicate results.
The caller owns those lifecycle operations.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

import numpy as np

from scripts import _b3_e4_f03_local_prolongation as prolongation
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_budgets as budgets
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_child_identity as child_identity
from scripts import _b3_e4_f03_local_scientific_evidence_index as evidence_index
from scripts import _b3_e4_f03_local_scientific_inverse_storage as inverse_storage
from scripts import _b3_e4_f03_local_scientific_lifecycle as lifecycle
from scripts import _b3_e4_f03_local_scientific_numerical_index as numerical_index
from scripts import _b3_e4_f03_local_scientific_numerical_storage as numerical_storage
from scripts import _b3_e4_f03_local_scientific_port_factory as port_factory
from scripts import _b3_e4_f03_local_scientific_port_storage as port_storage
from scripts import _b3_e4_f03_local_scientific_prolongation_storage as prolongation_storage
from scripts import _b3_e4_f03_local_scientific_result_storage as result_storage
from scripts import _b3_e4_f03_local_scientific_saved_observation_factory as saved_factory
from scripts import _b3_e4_f03_local_scientific_saved_storage as saved_storage
from scripts import _b3_e4_f03_saved_recovery_composition as composition
from scripts import _b3_e4_f03_scaled_sparse as scaled_sparse
from scripts import _b3_e4_f03_sparse_factor_candidate as factor_candidate


@dataclass(frozen=True, slots=True)
class ProducedCase:
    """Small lifecycle identity returned after the final exclusive write."""

    case_id: str
    start_sha256: str
    numerical_index_sha256: str
    evidence_index_sha256: str
    evidence_total_bytes: int

    def __post_init__(self):
        digests = (
            self.start_sha256,
            self.numerical_index_sha256,
            self.evidence_index_sha256,
        )
        if (
            type(self.case_id) is not str
            or not self.case_id
            or any(
                type(value) is not str
                or len(value) != 64
                or set(value) - frozenset("0123456789abcdef")
                for value in digests
            )
            or type(self.evidence_total_bytes) is not int
            or self.evidence_total_bytes <= 0
        ):
            raise ValueError("invalid completed F03 case-production identity")


def _operator_evidence(value: assembly.AssembledPrimal) -> numerical_storage.OperatorEvidence:
    if type(value) is not assembly.AssembledPrimal:
        raise ValueError("owned F03 assembled primal required")
    return numerical_storage.OperatorEvidence(
        value.shell, value.beam, value.root, value.load,
    )


def _scaled_evidence(
    primary: scaled_sparse.ScaledSystem,
    alternate: scaled_sparse.ScaledSystem,
    candidate: scaled_sparse.SparseCandidate,
) -> numerical_storage.ScaledEvidence:
    if (
        type(primary) is not scaled_sparse.ScaledSystem
        or type(alternate) is not scaled_sparse.ScaledSystem
        or type(candidate) is not scaled_sparse.SparseCandidate
    ):
        raise ValueError("owned F03 scaled systems and sparse candidate required")
    z = candidate.z
    h = primary.matrix
    h_z = np.ascontiguousarray(h @ z, dtype=np.float64)
    return numerical_storage.ScaledEvidence(
        primary.stiffness,
        primary.root,
        h,
        alternate.stiffness,
        alternate.root,
        alternate.matrix,
        primary.diagonal,
        primary.root_scale,
        primary.rhs,
        alternate.rhs,
        z,
        candidate.q,
        candidate.eta,
        h_z,
    )


def _positivity_evidence(
    value: factor_candidate.FactorCandidate,
) -> numerical_storage.PositivityEvidence:
    if type(value) is not factor_candidate.FactorCandidate:
        raise ValueError("owned F03 positivity-factor candidate required")
    inverse_gather = np.ascontiguousarray(value.permutation, dtype=np.int64)
    return numerical_storage.PositivityEvidence(
        value.matrix,
        value.lower,
        value.upper,
        value.diagonal,
        value.row_map,
        value.column_map,
        inverse_gather,
    )


def _stream_inverse_blocks(
    directory: Path,
    plan: archive.CaseArchivePlan,
    candidate: scaled_sparse.SparseCandidate,
) -> None:
    """Consume the candidate stream once and match every planned block."""
    stream = iter(candidate.inverse_blocks())
    for expected in plan.inverse_blocks:
        try:
            start, value = next(stream)
        except StopIteration as exc:
            raise ArithmeticError("incomplete F03 inverse-column stream") from exc
        if type(start) is not int or start != expected.start:
            raise ArithmeticError("F03 inverse-column stream disagrees with plan")
        inverse_storage.write_block(directory, plan, start, value)
    try:
        next(stream)
    except StopIteration:
        return
    raise ArithmeticError("extra F03 inverse-column block")


def _produce_prolongation(case: cases.ScientificCase, grid):
    source = prolongation_storage.predecessor(case)
    if source is None:
        return None
    capacity = case.physical_dofs * (source.degree + 1) ** 2
    return prolongation.prolongation(
        cases.compile_case(source),
        grid,
        max_entries=capacity,
        max_integer_bits=cases.ASSEMBLY_BUDGET.max_trace_integer_bits,
        max_work_bytes=cases.ASSEMBLY_BUDGET.max_work_bytes,
    )


def _produce_started_case(
    directory: Path,
    envelope: archive.CaseArchivePlan,
    start_sha256: str,
    record: cases.CasePreflight,
    records: tuple[cases.CasePreflight, ...],
    source_commit: str,
    registration_sha256: str,
) -> ProducedCase:
    """Continue one already-consumed attempt; callers own the start boundary."""
    directory = Path(directory)
    # First validate the exact envelope that consumed the attempt.  Then
    # re-read the file and require canonical byte identity, so neither a stale
    # first plan nor a replacement second plan can inherit the other's marker.
    archive.validate_plan(envelope, record, records, source_commit)
    plan = archive.read_plan(
        directory / "plan.zip", record, records, source_commit,
    )
    if archive._payload(plan) != archive._payload(envelope):
        raise ValueError("F03 archive plan changed after start marker")
    scientific_budgets = budgets.make_scientific_budgets()
    budgets.preflight_inventory(scientific_budgets)
    case = record.case
    grid = cases.compile_case(case)
    inverse_storage.prepare_directory(directory)

    primary = assembly.assemble(
        grid, cases.ASSEMBLY_BUDGET, extra_beam_order=False, load_order=48,
    )
    primary_operators = _operator_evidence(primary)
    numerical_storage.write_operators(
        directory / "operators_primary.npz", primary_operators, case,
    )

    alternate = assembly.assemble(
        grid, cases.ASSEMBLY_BUDGET, extra_beam_order=True, load_order=64,
    )
    alternate_operators = _operator_evidence(alternate)
    numerical_storage.write_operators(
        directory / "operators_alternate.npz", alternate_operators, case,
    )

    primary_scaled = scaled_sparse.prepare(
        primary.shell,
        primary.beam,
        primary.root,
        primary.load,
        cases.SYSTEM_BUDGET,
    )
    alternate_scaled = scaled_sparse.prepare(
        alternate.shell,
        alternate.beam,
        alternate.root,
        alternate.load,
        cases.SYSTEM_BUDGET,
        reference=primary_scaled,
    )
    solve_budget = scaled_sparse.SolveBudget(
        cases.SYSTEM_BUDGET,
        cases.MAX_KKT_FACTOR_NNZ,
        cases.MAX_INVERSE_EVIDENCE_BYTES_PER_CASE,
    )
    candidate = scaled_sparse.solve_candidate(primary_scaled, solve_budget)
    scaled_evidence = _scaled_evidence(primary_scaled, alternate_scaled, candidate)
    numerical_storage.write_scaled(directory / "scaled_state.npz", scaled_evidence, case)

    factor_budget = factor_candidate.FactorBudget(
        cases.FACTOR_VALIDATION_BUDGET,
        cases.MAX_COMBINED_FACTOR_NNZ,
        cases.MAX_CANONICAL_FACTOR_BYTES,
    )
    factors = factor_candidate.produce(scaled_evidence.kbar, factor_budget)
    positivity_evidence = _positivity_evidence(factors)
    numerical_storage.write_positivity(
        directory / "positivity.npz", positivity_evidence, case,
    )

    _stream_inverse_blocks(directory, plan, candidate)
    inverse_storage.write_index(directory, plan)

    port_evidence = port_factory.produce_port_evidence(
        grid, scaled_evidence.q, budget=scientific_budgets.trace,
    )
    port_storage.write_ports(directory / "ports.npz", port_evidence, case)

    numerical_evidence = numerical_index.NumericalEvidence(
        primary_operators,
        alternate_operators,
        scaled_evidence,
        positivity_evidence,
        port_evidence,
    )
    assembly_primary = numerical_index.assembly_producer(
        case, primary_operators, primary.diagnostics, alternate=False,
    )
    assembly_alternate = numerical_index.assembly_producer(
        case, alternate_operators, alternate.diagnostics, alternate=True,
    )
    scaling_primary = numerical_index.scaling_producer(
        case, scaled_evidence, primary_scaled.metadata, primary=True,
    )
    scaling_alternate = numerical_index.scaling_producer(
        case, scaled_evidence, alternate_scaled.metadata, primary=False,
    )
    kkt_record = numerical_index.kkt_producer(
        plan, candidate.work, status="SUCCEEDED", reason="completed",
    )
    positivity_record = numerical_index.positivity_producer(
        positivity_evidence, factors.metadata,
    )
    index = numerical_index.build_index(
        plan,
        numerical_evidence,
        assembly_primary,
        assembly_alternate,
        scaling_primary,
        scaling_alternate,
        kkt_record,
        positivity_record,
    )
    numerical_index_sha256 = numerical_index.write_index(
        directory / "numerical_index.json", index,
    )

    prolongation_storage.write(
        directory, _produce_prolongation(case, grid), case,
    )

    saved = saved_factory.produce_saved_observations(
        grid,
        scaled_evidence.q,
        scaled_evidence.eta,
        budget=scientific_budgets.composition,
    )
    saved_storage.write_interface(
        directory / "saved_interface.npz", saved.interface, case,
    )
    saved_storage.write_work(directory / "saved_work.npz", saved.work, case)
    saved_storage.write_norm(directory / "saved_norm.npz", saved.norm)

    composed = composition.verify_composition(
        grid,
        primary_operators.shell,
        primary_operators.beam,
        alternate_operators.shell,
        alternate_operators.beam,
        primary_operators.root,
        primary_operators.load,
        scaled_evidence.d,
        scaled_evidence.h,
        scaled_evidence.b,
        scaled_evidence.q,
        scaled_evidence.eta,
        scaled_evidence.z,
        scaled_evidence.h_z,
        saved.interface,
        saved.work,
        saved.norm,
        budget=scientific_budgets.composition,
    )
    result_storage.write_composition(
        directory / "saved_composition.npz",
        result_storage.composition_summary(composed),
    )
    result_storage.write_balances(
        directory / "balances.npz",
        result_storage.balance_snapshot(saved.support, saved.interface),
    )

    evidence, evidence_index_sha256 = evidence_index.write_index(
        directory, plan, registration_sha256, start_sha256,
    )
    return ProducedCase(
        plan.case_id,
        start_sha256,
        numerical_index_sha256,
        evidence_index_sha256,
        evidence.total_bytes,
    )


def produce_case(
    directory: Path,
    record: cases.CasePreflight,
    records: tuple[cases.CasePreflight, ...],
    source_commit: str,
    registration_sha256: str,
) -> ProducedCase:
    """Produce one supplied frozen case once, leaving partial evidence on error.

    The bounded plan envelope is the only input read before ``start.json`` is
    created. Full inventory, topology and resource validation intentionally
    follow that marker, so every attempt that begins model work is consumed.
    """
    directory = Path(directory)
    envelope = archive.read_plan_envelope(directory / "plan.zip")
    start_sha256 = lifecycle.write_start(
        directory, envelope, registration_sha256, os.getpid(),
    )
    return _produce_started_case(
        directory,
        envelope,
        start_sha256,
        record,
        records,
        source_commit,
        registration_sha256,
    )


def produce_registered_case(
    directory: Path,
    source_commit: str,
    registration_sha256: str,
) -> ProducedCase:
    """Child-process route that constructs the frozen inventory after start."""
    directory = Path(directory)
    envelope = archive.read_plan_envelope(directory / "plan.zip")
    start_sha256 = lifecycle.write_start(
        directory, envelope, registration_sha256, os.getpid(),
    )
    records = child_identity.verify_child_context(
        directory, envelope, source_commit, registration_sha256,
    )
    matches = tuple(
        record for record in records if record.case.case_id == envelope.case_id
    )
    if len(matches) != 1:
        raise ValueError("plan case is absent from frozen F03 inventory")
    return _produce_started_case(
        directory,
        envelope,
        start_sha256,
        matches[0],
        records,
        source_commit,
        registration_sha256,
    )
