"""Affected-check repair module for the capped-matching spy.

Attempt 2 (admission-globalization-remaining-attempt2) passed eight of the
nine remaining caller/public checks and failed
test_swept_certify_witness_skips_matching_without_admitting: the spy's
node_budget=1 is invalid for the diagnostic refinement-mode matching call
(gap_budget None) that the swept subdivision branch makes through
_gap_lower, whose validation requires a node budget covering the complete
initial partition. Attempt 3 confirmed the point-gap check still passes
and that leaving the refinement call at the production 1024-node cap
cannot fit the bounded job on the grossly violating subdivision middle
pose. The spy now caps both call shapes with their minimum valid budgets
(admission shape: node_budget=1; refinement shape: node_budget=85) and
counts only the admission-shaped calls the witness wiring bypasses. This
module reruns only the two checks that use that spy helper; the eight
unaffected passed checks and the sixteen passed witness math checks are
not repeated.
"""
from test_general_contact_admission_globalization_witness_public import (
    test_point_gap_budget_witness_skips_matching_without_admitting,
    test_swept_certify_witness_skips_matching_without_admitting,
)
