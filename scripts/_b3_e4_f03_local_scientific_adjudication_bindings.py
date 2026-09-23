"""Build receipt observations only from solve-free verified F03 evidence.

This adapter performs no assembly, factorization, equilibrium solve, recovery,
quadrature, or retry.  It snapshots values and certified bounds already
returned by ``verify_composition`` and binds them to their exact source
identities.
"""
from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction as F
import math

import numpy as np

from scripts import _b3_e4_f03_action_enclosure as enclosure
from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_scientific_case_receipt as receipt
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_saved_norm_checks as norm
from scripts import _b3_e4_f03_saved_work_checks as work


TIP_ROTATION_LENGTH = 0.46  # Frozen by both scaling producer records.

def _mapping(value: object, label: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise ValueError(f"verified F03 {label} mapping required")
    return value


def _fraction(value: object, label: str) -> F:
    if type(value) is not F:
        raise ValueError(f"exact F03 {label} Fraction required")
    return value


def _outward(value: F) -> tuple[float, float, float]:
    """Nearest value plus the smallest binary64 enclosure of one Fraction."""
    value = _fraction(value, "settling observation")
    try:
        center = float(value)
    except OverflowError as exc:
        raise ValueError("finite binary64 F03 settling observation required") from exc
    if not math.isfinite(center):
        raise ValueError("finite binary64 F03 settling observation required")
    rounded = F.from_float(center)
    lower = math.nextafter(center, -math.inf) if rounded > value else center
    upper = math.nextafter(center, math.inf) if rounded < value else center
    if not math.isfinite(lower) or not math.isfinite(upper):
        raise ValueError("bounded binary64 F03 settling enclosure required")
    return center, lower, upper


def _rational_observation(value: F) -> tuple[float, float, float, str]:
    center, lower, upper = _outward(value)
    source = enclosure.action_identity(recovery.Action(value))
    return center, lower, upper, source


def _comparison_observation(record: Mapping, saved: float) -> tuple[float, float, float, str]:
    record = _mapping(record, "Action comparison")
    bounded = _mapping(record.get("enclosure"), "Action enclosure")
    source = bounded.get("input_sha256")
    if type(source) is not str or len(source) != 64:
        raise ValueError("canonical F03 Action source identity required")
    _, lower, _ = _outward(_fraction(bounded.get("lower"), "Action lower bound"))
    _, _, upper = _outward(_fraction(bounded.get("upper"), "Action upper bound"))
    saved = float(saved)
    if not math.isfinite(saved):
        raise ValueError("finite saved F03 settling value required")
    saved_exact = record.get("saved_exact")
    if type(saved_exact) is not F or F.from_float(saved) != saved_exact:
        raise ValueError("F03 settling value disagrees with certified saved target")
    return saved, min(lower, saved), max(upper, saved), source


def _interface_comparisons(value: interface.InterfaceResult, name: str) -> tuple[Mapping, ...]:
    selected = tuple(
        item for item in value.comparisons
        if item.get("name") == name
    )
    if (
        len(selected) != 24
        or tuple(item.get("index") for item in selected) != tuple(range(24))
    ):
        raise ValueError("complete ordered F03 interface comparison inventory required")
    return selected


def settling_record(
    composed: Mapping,
    grid: topology.CompiledGrid,
    saved_interface: interface.SavedInterface,
    saved_work: work.SavedWork,
) -> receipt.SettlingRecord:
    """Extract the frozen 45 signed observables from one verified composition."""
    composed = _mapping(composed, "composition")
    components = _mapping(composed.get("components"), "composition component")
    if set(components) != {"numerical", "interface", "work", "norm"}:
        raise ValueError("complete F03 composition component inventory required")
    numerical = _mapping(components["numerical"], "numerical component")
    interface_result = components["interface"]
    worked = _mapping(components["work"], "work component")
    if (
        type(interface_result) is not interface.InterfaceResult
        or type(grid) is not topology.CompiledGrid
        or type(saved_interface) is not interface.SavedInterface
        or type(saved_work) is not work.SavedWork
    ):
        raise ValueError("verified F03 interface/work evidence required")
    if (
        interface_result.saved_functional.cuts != saved_interface.cuts
        or saved_work.cuts != saved_interface.cuts
        or grid.station_cuts != saved_interface.cuts
    ):
        raise ValueError("F03 settling evidence partition mismatch")
    canonical = _mapping(composed.get("canonical_saved_sha256s"), "canonical saved identity")
    saved_interface_identity = interface.saved_identity(saved_interface)
    if (
        interface_result.input_sha256.get("saved_interface") != saved_interface_identity
        or canonical.get("saved_interface") != saved_interface_identity
    ):
        raise ValueError("F03 settling saved-interface identity chain mismatch")
    saved_work_identity = work.input_identity(grid, interface_result.recovery, saved_work)
    if (
        worked.get("input_sha256") != saved_work_identity
        or canonical.get("work_state_saved") != saved_work_identity
    ):
        raise ValueError("F03 settling saved-work identity chain mismatch")

    observations: list[tuple[float, float, float, str]] = []
    observations.extend(
        _rational_observation(_fraction(value, "root reaction"))
        for value in interface_result.recovery.root_reaction
    )

    comparisons = _mapping(worked.get("comparisons"), "saved-work comparison")
    for index, saved in enumerate(saved_work.edge_route1):
        key = f"edge_route1/{index}"
        if key not in comparisons:
            raise ValueError("complete ordered F03 edge-route comparison inventory required")
        observations.append(_comparison_observation(comparisons[key], saved))

    tip_pose = interface_result.recovery.tip_pose
    if type(tip_pose) is not tuple or len(tip_pose) != 3:
        raise ValueError("complete exact F03 tip pose required")
    tip_scaled = (
        _fraction(tip_pose[0], "tip translation"),
        _fraction(tip_pose[1], "tip translation"),
        _fraction(tip_pose[2], "tip rotation") * F.from_float(TIP_ROTATION_LENGTH),
    )
    observations.extend(_rational_observation(value) for value in tip_scaled)

    raw = _mapping(numerical.get("raw"), "equilibrium raw")
    shell = _fraction(raw.get("physical_shell_work_exact"), "shell work") / 2
    beam = _fraction(raw.get("physical_beam_work_exact"), "beam work") / 2
    observations.extend(_rational_observation(value) for value in (shell, beam, shell + beam))

    recovered_atoms = interface_result.recovery.interface.atoms
    if len(recovered_atoms) != 2 or any(len(row) != 3 for row in recovered_atoms):
        raise ValueError("complete exact F03 endpoint atom inventory required")
    for exact_value, saved in zip(
        (value for row in recovered_atoms for value in row), saved_interface.atoms.flat,
    ):
        center, lower, upper, source = _rational_observation(
            _fraction(exact_value, "endpoint atom"),
        )
        saved = float(saved)
        observations.append((saved, min(lower, saved), max(upper, saved), source))

    band_comparisons = _interface_comparisons(interface_result, "recovered_band_analytic")
    observations.extend(
        _comparison_observation(record, saved)
        for record, saved in zip(band_comparisons, saved_interface.band_analytic.flat)
    )
    if len(observations) != len(receipt.SETTLING_NAMES):
        raise ArithmeticError("incomplete F03 settling observation extraction")
    values, lower, upper, sources = zip(*observations)
    return receipt.SettlingRecord(
        tuple(values), tuple(lower), tuple(upper), receipt.SETTLING_SCALES,
        tuple(sources),
    )


def _optional_values(value: np.ndarray) -> tuple[float | None, ...]:
    return tuple(None if np.isnan(item) else float(item) for item in value.flat)


def functional_record(composed: Mapping, saved: norm.SavedNorm) -> receipt.FunctionalRecord:
    """Snapshot the exact verified 48/64 saved-norm observation inventory."""
    composed = _mapping(composed, "composition")
    components = _mapping(composed.get("components"), "composition component")
    normed = _mapping(components.get("norm"), "norm component")
    canonical = _mapping(composed.get("canonical_saved_sha256s"), "canonical saved identity")
    if type(saved) is not norm.SavedNorm:
        raise ValueError("verified saved F03 norm evidence required")
    source = normed.get("input_sha256")
    interface_result = components.get("interface")
    if type(interface_result) is not interface.InterfaceResult:
        raise ValueError("verified F03 interface component required")
    observed = norm.input_identity(interface_result.saved_functional, saved)
    if source != canonical.get("norm_functional_saved") or source != observed:
        raise ValueError("F03 norm functional identity chain mismatch")
    value = receipt.FunctionalRecord(
        source,
        _optional_values(saved.channels),
        _optional_values(saved.totals),
        _optional_values(saved.components),
        tuple(bool(item) for item in saved.channel_flags.flat),
        tuple(bool(item) for item in saved.total_flags.flat),
        tuple(bool(item) for item in saved.exact_zero.flat),
        tuple(tuple(record for record in failures) for failures in saved.failures),
    )
    if value.numerically_admissible != bool(normed.get("numerically_admissible")):
        raise ValueError("F03 functional record disagrees with verified norm admission")
    return value


def make_bindings(
    composed: Mapping,
    grid: topology.CompiledGrid,
    saved_interface: interface.SavedInterface,
    saved_work: work.SavedWork,
    saved_norm: norm.SavedNorm,
) -> receipt.AdjudicationBindings:
    """Create the only receipt binding admitted for a completed case."""
    return receipt.AdjudicationBindings(
        settling_record(composed, grid, saved_interface, saved_work),
        functional_record(composed, saved_norm),
    )
