# First finite mixed-owner implementation: development freeze

Parent: 2cebe4191bc1c1924bb6f69ead265b87b6ce462a. Accepted design review
c7efca597db0739b83eeeda98f55dd714cea1c4a05e35dbfc6a7f269cc8c91e3 binds
5385ebd21db406621627e632ecb3cc231cf02384. No accepted mechanics result yet.

Exact five-new-path extent: this document,
src/anysolver/_ge_beam3_g3c_definition.py,
src/anysolver/_ge_beam3_g3c_owner.py,
tests/test_ge_beam3_g3c_owner_bridge.py and
scripts/run_ge_beam3_g3c_owner_bridge.py. Existing source is unchanged.

This implements closed expansion of all 25 fixture definitions and a separate
finite owner using actual native issued contexts and native stationary solves,
the accepted local B2/B3 and Q4/S3 adapters, complete pose-joint blocks and
prescribed support Hessians. One immutable generation is published only after
all preparation and disposable native commits. No FEModel/state store is
exposed. Local virgin diagnostic states are not relabeled material commits.
Only a diagnostic snapshot API exists; checkpoint import and public restart
remain fail-closed pending the complete strict preflight/replay implementation.

The first executable gate exercises J_B2_PAIR. A smoke pass is one node:
test_b2_pair_zero_equilibrium_commits_actual_native_states. The full development
lane has 12 nodes (nine functions, one parametrized over four failure stages):
25-definition/anchor expansion; command-copy/order; actual zero equilibrium;
finite root and fresh native origin; full KKT directional/nonidentity joint
values; four last-family/late-commit failures; exact input ownership/reentry;
foreign capability; changed dispatch and closed restart admission. It is NOT
all-five-family or full G3c qualification. Do not add smoke and full counts.

Launch with C:/Python/Python314/python.exe -I -S -B followed by
scripts/run_ge_beam3_g3c_owner_bridge.py --smoke, then the same script without
--smoke only after smoke passes. Each lane requires a clean committed candidate,
complete input lease, accepted review and all source/payload/environment hashes
before importing mechanics. Preserve fresh exclusive external logs. One
numerical thread, 600 seconds, 24 GiB process-tree cap, 120-second inactivity
watchdog; no retry. Do not run any historical lane as a substitute.

Before acceptance: independently review actual implementation, assertions and
failure semantics. Remaining categories include every graph family/variant,
all load scales and common-motion preparations, independent full nonzero-load
Schur checks, complete typed restart preflight and every-prefix continuation,
canonical formal evidence, full rehearsal and two formal cycles. Conventional
finite Q4 physical recovery and B2 clamp-domain full recovery remain open.
No G3c/G4/G5, full parity, public default, release or qualification claim follows.
