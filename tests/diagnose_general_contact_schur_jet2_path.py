"""One bounded coupled static probe with analytic Q4/S3 pressure response."""

from dataclasses import replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))

from anysolver import solve_static_nonlinear
from test_general_contact_supported_schur_path import _case


if __name__ == "__main__":
    model, definition, settings, program = _case()
    settings = replace(
        settings,
        general_s3_differentiation="jet2_q4_s3_dev",
        q4_source_support_gradient_tolerance=1e-5,
        q4_source_support_hessian_tolerance=1e-5,
        q4_source_weighted_gap_gradient_tolerance=1e-5,
        q4_source_weighted_gap_hessian_tolerance=1e-5,
        maximum_q4_source_integration_triangles=128,
    )
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=12,
        emit_restart_checkpoint=True,
    )
    print(f"status={result.status} reason={result.failure_reason} "
          f"accepted_steps={len(result.steps)}")
    failure = result.info.get("contact_failure", {})
    trace = failure.get("augmentation_trace", ())
    if not trace and result.steps:
        trace = result.steps[-1].get("augmentation_trace", ())
    for index, entry in enumerate(trace, 1):
        print(f"augmentation={index} "
              f"pressure_change_pa={entry.get('pressure_change')} "
              f"schur_proposed={entry.get('schur_proposed')} "
              f"schur_ineligible={entry.get('schur_ineligible')} "
              f"schur_condition={entry.get('schur_scaled_condition')} "
              f"schur_singular_values={entry.get('schur_scaled_singular_values')} "
              f"weak_rhs_fraction={entry.get('schur_scaled_weak_rhs_fraction')} "
              f"weak_right_mode={entry.get('schur_scaled_weak_right_mode')} "
              f"pressure_gram_rank={entry.get('pressure_gram_scaled_rank')} "
              f"schur_applied={entry.get('schur_applied')}")
    if failure:
        print(f"gap_tolerance_met={failure.get('gap_tolerance_met')} "
              f"active_modes={failure.get('active_pressure_dofs')} "
              f"schur_attempts={failure.get('schur_attempts')} "
              f"schur_applied={failure.get('schur_applied')}")
