"""Final affordable driver check: stagnation-control validation only.

Attempt 5 (admission-globalization-final-checks-attempt5) banked the
adversarial physical-normal witness case but timed out inside the first
real-solve driver check: with JIT disabled, each small-fixture solve costs
roughly 12-15 s, so no multi-solve driver check fits the remaining
executable budget. This module selects the single driver check that needs
no solve: the stagnation controls are validated before any increment
work. The other six driver checks remain unexecuted under the scope's
attempt and time limits and are reported as such.
"""
from test_general_contact_admission_globalization_driver import (
    test_stagnation_controls_are_validated_before_any_work,
)
