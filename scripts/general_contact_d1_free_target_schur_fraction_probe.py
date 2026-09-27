"""Disposable small-step pressure response check at the 16-Q4 failure."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import time

import numpy as np

from anysolver import solve_static_nonlinear
from anysolver.general_contact import linearized_pivot, static_path
from anysolver.general_contact.supported_schur import SupportedSchurProposal
from scripts.general_contact_d1_free_target_press_probe import build_free_target_case


def main(output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(output_path)
    started = time.perf_counter()
    report = {"candidate": "free_target_16q4_schur_small_fraction_dev",
              "selected_attempt": 2, "initial_fraction": 0.02}
    original_schur = static_path.refined_patch_supported_schur
    calls = 0
    observed: dict[str, object] = {}

    def probe(manager, displacement, tangent, transform, control_rows,
              **kwargs):
        nonlocal calls
        calls += 1
        full = original_schur(manager, displacement, tangent, transform,
                              control_rows, **kwargs)
        if calls != 2 or full is None:
            return full
        source, target = manager._positions(displacement)
        state = manager.law.evaluate(source, target,
                                     manager.normal_multipliers)
        selected = np.flatnonzero(state.reference_support > 0.0)
        active = np.flatnonzero(state.pressure > 0.0)
        H = linearized_pivot._constrained_gap_response(
            manager, displacement, tangent, transform, control_rows,
            selected, active,
            difference_step=kwargs["difference_step"],
            check_cancel=kwargs.get("check_cancel"),
        )
        if H is None:
            raise RuntimeError("small-step gap response was unavailable")
        base_pressure = manager.normal_multipliers.copy()
        base_gap = state.normalized_gap.copy()
        full_step = full.multipliers-base_pressure
        base_signature = manager.law.geometry.evaluate(
            source, target).overlap_signature
        fraction = 0.02
        while fraction >= 0.0003125:
            small_pressure = base_pressure+fraction*full_step
            predicted_gap = base_gap.copy()
            predicted_gap[selected] += H @ (fraction*full_step[active])
            predicted_argument = (small_pressure
                                  -manager.stiffness*predicted_gap)
            predicted_active = tuple(int(i) for i in np.flatnonzero(
                predicted_argument > 0.0))
            if (np.all(small_pressure >= 0.0)
                    and predicted_active == tuple(map(int, active))):
                break
            fraction *= 0.5
        else:
            raise RuntimeError("no small fraction retains the original branch")
        predicted_residual = float(np.max(np.abs(
            np.maximum(0.0, predicted_argument)-small_pressure)))
        observed.update({
            "fraction": fraction,
            "base_pressure": base_pressure,
            "base_gap": base_gap,
            "selected": selected,
            "active": active,
            "H": H,
            "full_step": full_step,
            "small_pressure": small_pressure,
            "predicted_gap": predicted_gap,
            "predicted_active": predicted_active,
            "predicted_residual": predicted_residual,
            "base_signature": base_signature,
            "full_proposal_kind": kwargs.get("diagnostics", {}).get(
                "schur_proposal_kind"),
        })
        original_evaluate = manager.evaluate

        def capture_evaluate(trial_displacement, *args, **options):
            result = original_evaluate(trial_displacement, *args, **options)
            if (np.array_equal(manager.normal_multipliers, small_pressure)
                    and options.get("tangent") is False):
                trial_source, trial_target = manager._positions(
                    trial_displacement)
                observed["actual_gap"] = np.asarray(
                    result[2].normalized_weighted_gap_m, dtype=float).copy()
                observed["actual_active"] = tuple(int(i) for i in
                    np.flatnonzero(np.asarray(
                        result[2].numerical_pressure_pa, dtype=float) > 0.0))
                observed["actual_signature"] = (
                    manager.law.geometry.evaluate(
                        trial_source, trial_target).overlap_signature)
            return result

        manager.evaluate = capture_evaluate
        return SupportedSchurProposal(
            small_pressure, tuple(map(int, active)), full.scaled_condition,
            fraction, full.predicted_residual_before, predicted_residual)

    static_path.refined_patch_supported_schur = probe
    try:
        model, definition, settings, program = build_free_target_case(16)
        settings = replace(settings, augmentation_schur_maximum_attempts=1)
        result = solve_static_nonlinear(
            model, contact=definition, contact_settings=settings,
            contact_path_program=program, max_iterations=18,
            tolerance=1.0e-8, emit_restart_checkpoint=True)
        report["solver_status"] = result.status
        report["failure_reason"] = result.failure_reason
        report["accepted_steps"] = len(result.steps)
        report["schur_calls"] = calls
        if not observed or "actual_gap" not in observed:
            raise RuntimeError("selected small-step equilibrium was not captured")
        selected = observed["selected"]
        actual = observed["actual_gap"][selected]
        predicted = observed["predicted_gap"][selected]
        base = observed["base_gap"][selected]
        report.update({
            "fraction": observed["fraction"],
            "active_indices": [int(i) for i in observed["active"]],
            "predicted_active_indices": list(observed["predicted_active"]),
            "actual_active_indices": list(observed["actual_active"]),
            "overlap_signature_matches": (
                observed["actual_signature"] == observed["base_signature"]),
            "full_proposal_kind": observed["full_proposal_kind"],
            "base_pressure_pa": observed["base_pressure"].tolist(),
            "full_pressure_step_pa": observed["full_step"].tolist(),
            "small_pressure_pa": observed["small_pressure"].tolist(),
            "selected_pressure_ids": selected.tolist(),
            "base_normalized_gap_m": base.tolist(),
            "predicted_normalized_gap_m": predicted.tolist(),
            "actual_normalized_gap_m": actual.tolist(),
            "predicted_gap_change_m": (predicted-base).tolist(),
            "actual_gap_change_m": (actual-base).tolist(),
            "maximum_gap_response_error_m": float(np.max(np.abs(
                actual-predicted))),
            "predicted_projected_residual_pa": observed["predicted_residual"],
            "response_matrix_active_m_per_pa": observed["H"].tolist(),
            "status": "captured",
        })
    except Exception as exc:
        report["status"] = "failed"
        report["probe_failure"] = f"{type(exc).__name__}: {exc}"
    finally:
        static_path.refined_patch_supported_schur = original_schur
    report["elapsed_seconds"] = time.perf_counter()-started
    output_path.write_text(json.dumps(report, indent=2, default=str)+"\n",
                           encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "status", "probe_failure", "solver_status", "failure_reason",
        "accepted_steps", "schur_calls", "fraction",
        "active_indices", "predicted_active_indices", "actual_active_indices",
        "overlap_signature_matches", "maximum_gap_response_error_m",
        "elapsed_seconds") if k in report}, indent=2, default=str))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    main(parser.parse_args().output)
