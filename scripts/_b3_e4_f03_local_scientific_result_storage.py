"""Strict saved-composition and physical-balance evidence for F03.

This module only snapshots already-computed observations.  It cannot assemble,
factor, solve, recover, or adjudicate a case.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from scripts import _b3_e4_f03_action_enclosure as enclosure
from scripts import _b3_e4_f03_local_scientific_storage as storage
from scripts import _b3_e4_f03_local_support_recovery as support
from scripts import _b3_e4_f03_saved_interface_checks as interface


MAX_REASON_BYTES = 64 * 1024
MAX_GROUP_BYTES = 2 * 1024**2

SAVED_HASH_NAMES = (
    "compiled_grid", "saved_interface", "saved_work", "saved_norm",
    "work_state_saved", "norm_functional_saved",
)
COMPONENT_NAMES = ("numerical", "interface", "work", "norm")
CROSS_NAMES = (
    "numerical_K_shell", "numerical_K_beam", "numerical_C_root", "numerical_H",
    "numerical_f", "numerical_D", "numerical_q", "numerical_eta", "numerical_z",
    "numerical_b", "numerical_H_z", "numerical_K_shell_plus",
    "numerical_K_beam_plus", "interface_state", "interface_saved", "recovery_q",
    "recovery_eta", "recovery_cuts", "work_state_saved", "norm_functional_saved",
    "norm_functional_type", "functional_chain",
)
DIAGNOSTIC_NAMES = (
    "comparisons", "operation_envelope", "integer_bit_envelope",
    "workspace_envelope_bytes", "owned_snapshot_bytes", "six_block_preflight_upper",
    "actual_comparisons", "recovery_recomputations", "norm_evaluations",
    "equilibrium_solves", "factorizations",
)
COMPOSITION_STATUSES = (
    "COMPONENT_CHECKS_PASSED", "COMPOSITION_FAILED", "HOLD_NUMERICAL",
    "HOLD_UNRESOLVED",
)
COMPONENT_STATUSES = (
    "NUMERICAL_MECHANICAL_CHECKS_PASSED", "HOLD", "PASSED", "FAILED",
    "HOLD_UNRESOLVED",
)

BALANCE_ACTION_NAMES = (
    "force_actual_x", "force_actual_y", "force_nominal_x", "force_nominal_y",
    "moment_physical", "moment_predicted", "moment_represented", "rigid_yaw",
    "load_actual_force", "load_actual_moment", "load_nominal_force",
    "load_nominal_moment", "load_delta_force", "load_delta_moment",
)


def _hash_bytes(value: str) -> np.ndarray:
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("canonical F03 SHA-256 required")
    return np.frombuffer(bytes.fromhex(value), dtype=np.uint8).copy()


def _hash_text(value: np.ndarray) -> str:
    return bytes(value).hex()


def _ordered(mapping: object, names: tuple[str, ...], label: str) -> tuple:
    try:
        value = dict(mapping)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"exact F03 {label} mapping required") from exc
    if tuple(value) != names:
        raise ValueError(f"noncanonical F03 {label} inventory")
    return tuple(value[name] for name in names)


def _status_codes(values: tuple[str, ...]) -> np.ndarray:
    if any(type(value) is not str or value not in COMPONENT_STATUSES for value in values):
        raise ValueError("invalid F03 component status")
    return np.asarray([COMPONENT_STATUSES.index(value) for value in values], dtype="<i8")


def _reason_payload(reasons: tuple[str, ...]) -> bytes:
    if type(reasons) is not tuple or any(type(value) is not str for value in reasons):
        raise ValueError("tuple of F03 composition reasons required")
    payload = (json.dumps(list(reasons), ensure_ascii=True, sort_keys=False,
                          separators=(",", ":")) + "\n").encode("ascii")
    if len(payload) > MAX_REASON_BYTES:
        raise ValueError("F03 composition reasons exceed byte limit")
    return payload


@dataclass(frozen=True, slots=True)
class CompositionSummary:
    status: str
    reasons: tuple[str, ...]
    canonical_snapshot_sha256: str
    canonical_saved_sha256s: tuple[tuple[str, str], ...]
    component_statuses: tuple[tuple[str, str], ...]
    cross_bindings: tuple[tuple[str, bool], ...]
    diagnostics: tuple[tuple[str, int], ...]

    def __post_init__(self):
        if self.status not in COMPOSITION_STATUSES:
            raise ValueError("invalid F03 composition status")
        _hash_bytes(self.canonical_snapshot_sha256)
        _reason_payload(self.reasons)
        for values, names, label in (
            (self.canonical_saved_sha256s, SAVED_HASH_NAMES, "saved hash"),
            (self.component_statuses, COMPONENT_NAMES, "component status"),
            (self.cross_bindings, CROSS_NAMES, "cross binding"),
            (self.diagnostics, DIAGNOSTIC_NAMES, "composition diagnostic"),
        ):
            if type(values) is not tuple or tuple(name for name, _ in values) != names:
                raise ValueError(f"noncanonical F03 {label} inventory")
        if any(_hash_bytes(value).shape != (32,) for _, value in self.canonical_saved_sha256s):
            raise ValueError("invalid F03 saved hash")
        if any(type(value) is not str or value not in COMPONENT_STATUSES
               for _, value in self.component_statuses):
            raise ValueError("invalid F03 component status")
        if any(type(value) is not bool for _, value in self.cross_bindings):
            raise ValueError("invalid F03 cross binding")
        if any(type(value) is not int or value < 0 or value > np.iinfo(np.int64).max
               for _, value in self.diagnostics):
            raise ValueError("invalid F03 composition diagnostic")
        statuses = dict(self.component_statuses)
        if (
            statuses["numerical"] not in ("NUMERICAL_MECHANICAL_CHECKS_PASSED", "HOLD")
            or any(statuses[name] not in ("PASSED", "FAILED", "HOLD_UNRESOLVED")
                   for name in ("interface", "work", "norm"))
        ):
            raise ValueError("component-specific F03 status required")
        cross = dict(self.cross_bindings)
        expected = (
            "COMPOSITION_FAILED" if (not all(cross.values()) or
                any(statuses[name] == "FAILED" for name in ("interface", "work", "norm")))
            else "HOLD_NUMERICAL" if statuses["numerical"] == "HOLD"
            else "HOLD_UNRESOLVED" if any(
                statuses[name] == "HOLD_UNRESOLVED" for name in ("interface", "work", "norm")
            )
            else "COMPONENT_CHECKS_PASSED"
        )
        diagnostics = dict(self.diagnostics)
        if (
            self.status != expected
            or (self.status == "COMPONENT_CHECKS_PASSED") != (not self.reasons)
            or diagnostics["actual_comparisons"] > diagnostics["comparisons"]
            or diagnostics["recovery_recomputations"] != 3
            or diagnostics["norm_evaluations"] != 2
            or diagnostics["equilibrium_solves"] != 0
            or diagnostics["factorizations"] != 0
        ):
            raise ValueError("inconsistent F03 composition result or work inventory")


def composition_summary(value: object) -> CompositionSummary:
    try:
        raw = dict(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("saved F03 composition result required") from exc
    required = {
        "scope", "status", "reasons", "canonical_snapshot_sha256",
        "canonical_saved_sha256s", "component_statuses", "cross_bindings",
        "diagnostics", "components",
    }
    if (
        set(raw) != required
        or raw["scope"] != "SAVED_RECOVERY_COMPONENT_COMPOSITION_ONLY"
        or type(raw["reasons"]) is not tuple
    ):
        raise ValueError("invalid saved F03 composition result inventory")
    _ordered(raw["components"], COMPONENT_NAMES, "composition component")
    saved = _ordered(raw["canonical_saved_sha256s"], SAVED_HASH_NAMES, "saved hash")
    statuses = _ordered(raw["component_statuses"], COMPONENT_NAMES, "component status")
    cross = _ordered(raw["cross_bindings"], CROSS_NAMES, "cross binding")
    diagnostics = _ordered(raw["diagnostics"], DIAGNOSTIC_NAMES, "composition diagnostic")
    return CompositionSummary(
        raw["status"], raw["reasons"], raw["canonical_snapshot_sha256"],
        tuple(zip(SAVED_HASH_NAMES, saved)), tuple(zip(COMPONENT_NAMES, statuses)),
        tuple(zip(CROSS_NAMES, cross)), tuple(zip(DIAGNOSTIC_NAMES, diagnostics)),
    )


def composition_specs() -> tuple[storage.ArraySpec, ...]:
    return (
        storage.ArraySpec("status", (1,), np.dtype("<i8")),
        storage.ArraySpec("snapshot_hash", (32,), np.dtype("|u1")),
        storage.ArraySpec("saved_hashes", (len(SAVED_HASH_NAMES), 32), np.dtype("|u1")),
        storage.ArraySpec("component_statuses", (len(COMPONENT_NAMES),), np.dtype("<i8")),
        storage.ArraySpec("cross_bindings", (len(CROSS_NAMES),), np.dtype("|b1"), finite=False),
        storage.ArraySpec("diagnostics", (len(DIAGNOSTIC_NAMES),), np.dtype("<i8")),
        storage.ArraySpec("reason_size", (1,), np.dtype("<i8")),
        storage.ArraySpec("reason_bytes", (MAX_REASON_BYTES,), np.dtype("|u1")),
    )


def write_composition(path: Path, value: CompositionSummary) -> None:
    if type(value) is not CompositionSummary:
        raise ValueError("validated F03 composition summary required")
    payload = _reason_payload(value.reasons)
    reason_bytes = np.zeros(MAX_REASON_BYTES, dtype=np.uint8)
    reason_bytes[:len(payload)] = np.frombuffer(payload, dtype=np.uint8)
    arrays = {
        "status": np.asarray([COMPOSITION_STATUSES.index(value.status)], dtype="<i8"),
        "snapshot_hash": _hash_bytes(value.canonical_snapshot_sha256),
        "saved_hashes": np.stack([_hash_bytes(item) for _, item in value.canonical_saved_sha256s]),
        "component_statuses": _status_codes(tuple(item for _, item in value.component_statuses)),
        "cross_bindings": np.asarray([item for _, item in value.cross_bindings], dtype="|b1"),
        "diagnostics": np.asarray([item for _, item in value.diagnostics], dtype="<i8"),
        "reason_size": np.asarray([len(payload)], dtype="<i8"),
        "reason_bytes": reason_bytes,
    }
    specs = composition_specs()
    storage.write_group(path, arrays, specs, max_raw_bytes=MAX_GROUP_BYTES)


def read_composition(path: Path) -> CompositionSummary:
    arrays = storage.read_group(path, composition_specs(), max_raw_bytes=MAX_GROUP_BYTES)
    status = int(arrays["status"][0])
    if not 0 <= status < len(COMPOSITION_STATUSES):
        raise ValueError("invalid saved F03 composition status code")
    size = int(arrays["reason_size"][0])
    if not 0 <= size <= MAX_REASON_BYTES or np.any(arrays["reason_bytes"][size:]):
        raise ValueError("invalid saved F03 composition reason padding")
    try:
        payload = bytes(arrays["reason_bytes"][:size])
        decoded = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid saved F03 composition reasons") from exc
    reasons = tuple(decoded) if type(decoded) is list else ()
    if _reason_payload(reasons) != payload:
        raise ValueError("noncanonical saved F03 composition reasons")
    codes = tuple(int(value) for value in arrays["component_statuses"])
    if any(not 0 <= value < len(COMPONENT_STATUSES) for value in codes):
        raise ValueError("invalid saved F03 component status code")
    return CompositionSummary(
        COMPOSITION_STATUSES[status], reasons, _hash_text(arrays["snapshot_hash"]),
        tuple((name, _hash_text(value)) for name, value in zip(SAVED_HASH_NAMES, arrays["saved_hashes"])),
        tuple((name, COMPONENT_STATUSES[code]) for name, code in zip(COMPONENT_NAMES, codes)),
        tuple((name, bool(value)) for name, value in zip(CROSS_NAMES, arrays["cross_bindings"])),
        tuple((name, int(value)) for name, value in zip(DIAGNOSTIC_NAMES, arrays["diagnostics"])),
    )


@dataclass(frozen=True, slots=True)
class BalanceSnapshot:
    display_values: np.ndarray
    action_sha256s: tuple[str, ...]
    endpoint_atoms: np.ndarray
    total_bands: np.ndarray
    line_bands: np.ndarray

    def __post_init__(self):
        arrays = (
            (self.display_values, (len(BALANCE_ACTION_NAMES),)),
            (self.endpoint_atoms, (2, 3)),
            (self.total_bands, (8, 3)),
            (self.line_bands, (8, 3)),
        )
        if any(type(value) is not np.ndarray or value.shape != shape or
               value.dtype != np.dtype("<f8") or not value.flags.c_contiguous or
               not np.isfinite(value).all() for value, shape in arrays):
            raise ValueError("invalid F03 physical-balance arrays")
        if type(self.action_sha256s) is not tuple or len(self.action_sha256s) != len(BALANCE_ACTION_NAMES):
            raise ValueError("invalid F03 physical-balance action inventory")
        for value in self.action_sha256s:
            _hash_bytes(value)
        owned = tuple(
            np.frombuffer(value.tobytes(order="C"), dtype="<f8").reshape(shape)
            for value, shape in arrays
        )
        for name, value in zip(("display_values", "endpoint_atoms", "total_bands", "line_bands"), owned):
            object.__setattr__(self, name, value)


def balance_snapshot(value: support.SupportResult, saved: interface.SavedInterface) -> BalanceSnapshot:
    if type(value) is not support.SupportResult or type(saved) is not interface.SavedInterface:
        raise ValueError("validated F03 support and interface observations required")
    actions = (
        *value.force_balance_actual, *value.force_balance_nominal,
        value.physical_moment_defect, value.predicted_physical_moment_defect,
        value.represented_moment_identity, value.rigid_yaw_functional,
        *value.actual_load, *value.nominal_load, *value.load_actual_minus_nominal,
    )
    if len(actions) != len(BALANCE_ACTION_NAMES):
        raise ArithmeticError("incomplete F03 physical-balance action inventory")
    # These are review displays only.  The exact Action identities below are
    # the persisted evidence binding; the solve-free adjudicator reconstructs
    # and certifies the Actions instead of accepting these rounded numbers.
    values = np.asarray([float(item.decimal_value()) for item in actions], dtype="<f8")
    hashes = tuple(enclosure._identity(item.rational, item.cosine_terms) for item in actions)
    return BalanceSnapshot(
        np.ascontiguousarray(values), hashes,
        np.ascontiguousarray(saved.atoms, dtype="<f8"),
        np.ascontiguousarray(saved.band_analytic, dtype="<f8"),
        np.ascontiguousarray(saved.line_band_analytic, dtype="<f8"),
    )


def balance_specs() -> tuple[storage.ArraySpec, ...]:
    return (
        storage.ArraySpec("display_values", (len(BALANCE_ACTION_NAMES),), np.dtype("<f8")),
        storage.ArraySpec("action_hashes", (len(BALANCE_ACTION_NAMES), 32), np.dtype("|u1")),
        storage.ArraySpec("endpoint_atoms", (2, 3), np.dtype("<f8")),
        storage.ArraySpec("total_bands", (8, 3), np.dtype("<f8")),
        storage.ArraySpec("line_bands", (8, 3), np.dtype("<f8")),
    )


def write_balances(path: Path, value: BalanceSnapshot) -> None:
    if type(value) is not BalanceSnapshot:
        raise ValueError("validated F03 physical-balance snapshot required")
    arrays = {
        "display_values": value.display_values,
        "action_hashes": np.stack([_hash_bytes(v) for v in value.action_sha256s]),
        "endpoint_atoms": value.endpoint_atoms, "total_bands": value.total_bands,
        "line_bands": value.line_bands,
    }
    storage.write_group(path, arrays, balance_specs(), max_raw_bytes=MAX_GROUP_BYTES)


def read_balances(path: Path) -> BalanceSnapshot:
    arrays = storage.read_group(path, balance_specs(), max_raw_bytes=MAX_GROUP_BYTES)
    return BalanceSnapshot(
        arrays["display_values"], tuple(_hash_text(value) for value in arrays["action_hashes"]),
        arrays["endpoint_atoms"], arrays["total_bands"], arrays["line_bands"],
    )
