"""Adjudicate saved F03 balance evidence without another recovery."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from scripts import _b3_e4_f03_action_enclosure as enclosure
from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_local_scientific_result_storage as storage
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_saved_recovery_composition as composition


BALANCE_COMPARISONS = (
    "force_actual/0", "force_actual/1",
    "force_nominal/0", "force_nominal/1",
    "moment_actual", "moment_nominal", "moment_represented",
    "moment_prediction_identity",
)


@dataclass(frozen=True, slots=True)
class BalanceAdjudication:
    status: str
    reasons: tuple[str, ...]
    action_sha256s: tuple[str, ...]
    display_values_are_acceptance_evidence: bool = False

    def __post_init__(self):
        if (
            self.status not in ("PASSED", "FAILED", "HOLD_UNRESOLVED")
            or type(self.reasons) is not tuple
            or any(type(value) is not str or not value for value in self.reasons)
            or type(self.action_sha256s) is not tuple
            or len(self.action_sha256s) != len(storage.BALANCE_ACTION_NAMES)
            or any(
                type(value) is not str
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
                for value in self.action_sha256s
            )
            or type(self.display_values_are_acceptance_evidence) is not bool
            or self.display_values_are_acceptance_evidence
            or (self.status == "PASSED") != (not self.reasons)
        ):
            raise ValueError("invalid F03 balance adjudication")


def _same_array(first, second) -> bool:
    return first.shape == second.shape and first.dtype == second.dtype and first.tobytes() == second.tobytes()


def _adjudicate_comparisons(comparisons: object) -> tuple[str, tuple[str, ...]]:
    if not isinstance(comparisons, Mapping) or any(name not in comparisons for name in BALANCE_COMPARISONS):
        raise ValueError("complete F03 balance comparison inventory required")
    statuses = []
    for name in BALANCE_COMPARISONS:
        comparison = comparisons[name]
        if not isinstance(comparison, Mapping):
            raise ValueError("invalid F03 balance comparison record")
        status = comparison.get("status")
        if status not in ("PASSED", "FAILED", "HOLD_UNRESOLVED"):
            raise ValueError("invalid F03 balance comparison status")
        statuses.append(status)
    if "FAILED" in statuses:
        return "FAILED", tuple(
            f"balance comparison failed: {name}"
            for name, status in zip(BALANCE_COMPARISONS, statuses)
            if status == "FAILED"
        )
    if "HOLD_UNRESOLVED" in statuses:
        return "HOLD_UNRESOLVED", tuple(
            f"balance comparison unresolved: {name}"
            for name, status in zip(BALANCE_COMPARISONS, statuses)
            if status == "HOLD_UNRESOLVED"
        )
    return "PASSED", ()


def verify_balance(
    composed: composition.CompositionResult,
    saved_interface: interface.SavedInterface,
    saved: storage.BalanceSnapshot,
) -> BalanceAdjudication:
    """Bind exact Action identities and saved arrays; displays remain non-authoritative."""
    if (
        type(composed) is not composition.CompositionResult
        or type(saved_interface) is not interface.SavedInterface
        or type(saved) is not storage.BalanceSnapshot
    ):
        raise ValueError("factory composition, saved interface and balance snapshot required")
    canonical = composed["canonical_saved_sha256s"]
    if canonical.get("saved_interface") != interface.saved_identity(saved_interface):
        raise ValueError("F03 balance saved-interface identity chain mismatch")
    worked = composed["components"]["work"]
    actions = worked.get("balance_actions")
    if (
        type(actions) is not tuple
        or len(actions) != len(storage.BALANCE_ACTION_NAMES)
        or any(type(value) is not recovery.Action for value in actions)
    ):
        raise ValueError("complete factory-owned F03 balance Action inventory required")
    sources = tuple(enclosure.action_identity(value) for value in actions)
    if sources != saved.action_sha256s:
        raise ValueError("F03 balance Action identities disagree with saved snapshot")
    if (
        not _same_array(saved.endpoint_atoms, saved_interface.atoms)
        or not _same_array(saved.total_bands, saved_interface.band_analytic)
        or not _same_array(saved.line_bands, saved_interface.line_band_analytic)
    ):
        raise ValueError("F03 balance arrays disagree with saved interface")
    status, reasons = _adjudicate_comparisons(worked.get("comparisons"))
    return BalanceAdjudication(status, reasons, sources)
