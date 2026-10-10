"""Final combined execution module: adversarial physical-normal witness case
plus the seven real driver checks.

The attempt-2 run of the remaining module stopped after its single failure
(the swept-certify spy defect, repaired and passed in attempt 4), so the
adversarial physical-normal case sorting after it never executed. This
module runs that case first (aliased name) together with the seven authored
driver checks on the real production path, sharing the driver module's
cached references within one process. The sixteen passed witness math
checks, the eight passed caller/public checks and the two passed spy-repair
checks are not repeated.
"""
from test_general_contact_admission_globalization_remaining import (
    test_witness_adversarial_physical_normal_within_tolerance_no_refusal
    as test_adversarial_physical_normal_within_tolerance_no_refusal,
)
from test_general_contact_admission_globalization_driver import (
    test_cancellation_during_substeps_restores_and_propagates,
    test_cancellation_inside_first_macro_attempt_restores_and_propagates,
    test_cutback_chronology_force_ramp_and_gates,
    test_post_commit_boundary_exception_restores_complete_macro_snapshot,
    test_restart_rejects_tampered_and_incompatible_continuation_history,
    test_report_boundary_exception_restores_complete_macro_snapshot,
    test_stagnation_controls_are_validated_before_any_work,
)
