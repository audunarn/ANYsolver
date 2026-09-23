"""Read one replayed F03 case for solve-free cross-case adjudication.

The returned values come from one byte-checked retained evidence snapshot.  The
context keeps the source handles live until the caller has finished comparing
them, then checks every external identity again.  No mechanical operator is
assembled and no equilibrium or recovery operation is performed here.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat

import numpy as np

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_case_adjudicator as adjudicator
from scripts import _b3_e4_f03_local_scientific_case_receipt as receipt
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_cross_math as cross_math
from scripts import _b3_e4_f03_local_scientific_evidence_index as evidence_index
from scripts import _b3_e4_f03_local_scientific_inverse_storage as inverse_storage
from scripts import _b3_e4_f03_local_scientific_lifecycle as lifecycle
from scripts import _b3_e4_f03_local_scientific_numerical_index as numerical_index
from scripts import _b3_e4_f03_local_scientific_prolongation_storage as prolongation_storage
from scripts import _b3_e4_f03_local_scientific_registration as registration
from scripts import _b3_e4_f03_local_scientific_saved_storage as saved_storage
from scripts import _b3_e4_f03_local_prolongation as transfer
from scripts import _b3_e4_f03_saved_interface_checks as interface_checks
from scripts import _b3_e4_f03_saved_norm_checks as norm_checks


@dataclass(frozen=True, slots=True)
class CaseSnapshot:
    case_id: str
    receipt: receipt.CaseReceipt
    receipt_sha256: str
    plan_archive_sha256: str
    evidence_index_sha256: str
    numerical_index_sha256: str
    inverse_index_sha256: str
    saved: numerical_index.NumericalEvidence
    functional: object
    prolongation: object
    rederived_prolongation: object

    @property
    def prolongation_sha256(self) -> str | None:
        return exact_prolongation_sha256(self.prolongation)

    def case_data(self) -> cross_math.CaseData:
        if self.receipt.settling is None or self.receipt.functional is None:
            raise ValueError("passing F03 case lacks settled observations")
        primary = self.saved.operator_primary
        ports = self.saved.port_evidence
        return cross_math.CaseData(
            self.case_id, self.receipt.settling, self.receipt.functional,
            self.functional, self.saved.scaled.q, primary.shell, primary.beam,
            primary.root, primary.load, ports.samples, ports.root, ports.tip,
            ports.free_slope,
        )


def exact_prolongation_sha256(value: transfer.ExactProlongation | None) -> str | None:
    """Hash dimensions, ordered indices and exact rational interpolation."""
    if value is None:
        return None
    if type(value) is not transfer.ExactProlongation:
        raise ValueError("validated exact F03 prolongation required")
    digest = hashlib.sha256(b"f03-exact-prolongation-v1\0")
    for number in (value.source_dofs, value.target_dofs,
                   len(value.weights), value.integer_bits):
        digest.update(int(number).to_bytes(8, "little", signed=False))
    for array in (value.rows, value.columns):
        digest.update(np.asarray(array, dtype="<i8").tobytes(order="C"))
    for weight in value.weights:
        for number in (weight.numerator, weight.denominator):
            encoded = str(number).encode("ascii")
            digest.update(len(encoded).to_bytes(8, "little"))
            digest.update(encoded)
    return digest.hexdigest()


def _verified_prolongation(case: cases.ScientificCase, saved: object):
    """Rebuild the frozen topology map and compare exact stored entries."""
    source = prolongation_storage.predecessor(case)
    if source is None:
        if saved is not None:
            raise ValueError("coarsest F03 case has an unexpected prolongation")
        return None, None
    if type(saved) is not transfer.ExactProlongation:
        raise ValueError("saved exact F03 prolongation required")
    capacity = case.physical_dofs * (source.degree + 1) ** 2
    expected = transfer.prolongation(
        cases.compile_case(source), cases.compile_case(case),
        max_entries=capacity,
        max_integer_bits=cases.ASSEMBLY_BUDGET.max_trace_integer_bits,
        max_work_bytes=cases.ASSEMBLY_BUDGET.max_work_bytes,
    )
    if (
        saved.source_dofs != expected.source_dofs
        or saved.target_dofs != expected.target_dofs
        or saved.integer_bits != expected.integer_bits
        or not np.array_equal(saved.rows, expected.rows)
        or not np.array_equal(saved.columns, expected.columns)
        or saved.weights != expected.weights
    ):
        raise ValueError("saved F03 prolongation disagrees with frozen topology")
    return saved, expected


def _owned_receipt_digest(directory: Path) -> str:
    path = directory / "case_receipt.json"
    before = path.lstat()
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or before.st_size <= 0
        or before.st_size > receipt.MAX_BYTES
        or evidence_index._is_reparse(before)
    ):
        raise ValueError("bounded owned F03 case receipt required")
    with evidence_index._open_no_follow(path) as stream:
        opened = os.fstat(stream.fileno())
        if not evidence_index._same_file(
            opened,
            evidence_index._FileIdentity(
                path.name, before.st_size, before.st_dev, before.st_ino,
                before.st_mtime_ns, before.st_ctime_ns,
            ),
        ):
            raise ValueError("F03 case receipt changed during open")
        payload = stream.read(receipt.MAX_BYTES + 1)
        if len(payload) != before.st_size:
            raise ValueError("F03 case receipt changed during read")
    after = path.lstat()
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (
        before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns,
    ):
        raise ValueError("F03 case receipt changed after read")
    return hashlib.sha256(payload).hexdigest()


@contextmanager
def open_case_snapshot(
    directory: Path,
    record: cases.CasePreflight,
    records: tuple[cases.CasePreflight, ...],
    source_commit: str,
    registration_sha256: str,
    replayed_receipt: receipt.CaseReceipt,
    receipt_sha256: str,
    *,
    run_root: Path,
    plan_archive_sha256: str,
):
    """Yield one checked saved-data view and recheck its sources on exit."""
    directory = Path(directory)
    run_root = Path(run_root)
    if (
        type(record) is not cases.CasePreflight
        or type(records) is not tuple
        or records != cases.preflight_inventory()
        or record not in records
        or type(replayed_receipt) is not receipt.CaseReceipt
        or replayed_receipt.status != "PASSED_CASE_NUMERICAL_SCREEN"
        or replayed_receipt.case_id != record.case.case_id
        or replayed_receipt.source_commit != source_commit
        or replayed_receipt.registration_sha256 != registration_sha256
        or not receipt._digest(receipt_sha256)
    ):
        raise ValueError("passing replayed F03 case and frozen inventory required")
    registered, registered_sha256 = registration.read_registration(
        run_root, registration_sha256,
    )
    if (
        registered_sha256 != registration_sha256
        or registered.source_commit != source_commit
        or directory != run_root / "cases" / record.case.case_id
        or tuple(item.case_id for item in registered.cases)
            != tuple(item.case.case_id for item in records)
        or next(item for item in registered.cases
                if item.case_id == record.case.case_id).plan_archive_sha256
            != plan_archive_sha256
    ):
        raise ValueError("F03 snapshot disagrees with immutable registration")
    if _owned_receipt_digest(directory) != receipt_sha256:
        raise ValueError("F03 case receipt changed after independent replay")
    plan_path = directory / "plan.zip"
    adjudicator._verify_registered_plan_bytes(plan_path, plan_archive_sha256)
    plan = archive.read_plan(plan_path, record, records, source_commit)
    if replayed_receipt.plan_sha256 != lifecycle.plan_sha256(plan):
        raise ValueError("F03 replayed case plan identity mismatch")
    start, start_sha256 = lifecycle.read_start(directory, plan, registration_sha256)
    terminal, terminal_sha256 = lifecycle.read_terminal(directory, plan, registration_sha256)
    if (
        terminal["reason"] != "completed" or terminal["exit_code"] != 0
        or terminal["start_sha256"] != start_sha256
        or not lifecycle.terminal_owns_start(terminal, start)
        or replayed_receipt.start_sha256 != start_sha256
        or replayed_receipt.terminal_sha256 != terminal_sha256
    ):
        raise ValueError("F03 replayed lifecycle identity mismatch")
    index, evidence_sha256 = evidence_index.read_index(
        directory, plan, registration_sha256, start_sha256,
    )
    if (
        replayed_receipt.evidence_index_sha256 != evidence_sha256
        or replayed_receipt.evidence_total_bytes != index.total_bytes
    ):
        raise ValueError("F03 replayed evidence index identity mismatch")
    with evidence_index.materialized_snapshot(
        directory, plan, index,
        (("start.json", start_sha256), ("terminal.json", terminal_sha256),
         ("stdout.log", terminal["stdout_log_sha256"]),
         ("stderr.log", terminal["stderr_log_sha256"])),
    ) as snapshot:
        if (
            lifecycle.read_start(snapshot, plan, registration_sha256) != (start, start_sha256)
            or lifecycle.read_terminal(snapshot, plan, registration_sha256)
                != (terminal, terminal_sha256)
        ):
            raise ValueError("F03 retained lifecycle identity mismatch")
        numerical_header, numerical_sha256 = numerical_index.read_index(
            snapshot / "numerical_index.json", plan,
        )
        saved_header, saved = numerical_index.read_saved(snapshot, plan)
        _, inverse_sha256 = inverse_storage.read_index(snapshot, plan)
        if (
            numerical_header != saved_header
            or replayed_receipt.numerical_index_sha256 != numerical_sha256
            or replayed_receipt.inverse_index_sha256 != inverse_sha256
        ):
            raise ValueError("F03 replayed numerical evidence identity mismatch")
        saved_interface = saved_storage.read_interface(
            snapshot / "saved_interface.npz", record.case,
        )
        functional = interface_checks._saved_functional(saved_interface)
        saved_norm = saved_storage.read_norm(snapshot / "saved_norm.npz")
        if (
            replayed_receipt.functional is None
            or norm_checks.input_identity(functional, saved_norm)
                != replayed_receipt.functional.functional_sha256
        ):
            raise ValueError("F03 replayed functional input identity mismatch")
        prolongation, rederived_prolongation = _verified_prolongation(
            record.case, prolongation_storage.read(snapshot, record.case),
        )
        value = CaseSnapshot(
            record.case.case_id, replayed_receipt, receipt_sha256,
            plan_archive_sha256, evidence_sha256, numerical_sha256, inverse_sha256,
            saved, functional, prolongation, rederived_prolongation,
        )
        try:
            yield value
        finally:
            if _owned_receipt_digest(directory) != receipt_sha256:
                raise ValueError("F03 case receipt changed during cross-case comparison")
            if (
                lifecycle.read_start(directory, plan, registration_sha256) != (start, start_sha256)
                or lifecycle.read_terminal(directory, plan, registration_sha256)
                    != (terminal, terminal_sha256)
            ):
                raise ValueError("F03 lifecycle changed during cross-case comparison")
            final_index, final_sha256 = evidence_index.read_index(
                directory, plan, registration_sha256, start_sha256,
            )
            if final_index != index or final_sha256 != evidence_sha256:
                raise ValueError("F03 evidence changed during cross-case comparison")
            if archive.read_plan(plan_path, record, records, source_commit) != plan:
                raise ValueError("F03 plan changed during cross-case comparison")
            adjudicator._verify_registered_plan_bytes(plan_path, plan_archive_sha256)
            final_registration, final_registration_sha256 = registration.read_registration(
                run_root, registration_sha256,
            )
            if (
                final_registration != registered
                or final_registration_sha256 != registered_sha256
            ):
                raise ValueError("F03 source or registration changed during cross-case comparison")
