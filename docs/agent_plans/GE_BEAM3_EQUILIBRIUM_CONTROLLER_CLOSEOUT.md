# Equilibrium-recovery nonlinear controller development closeout

Frozen implementation `66774bf4422f4b6e22fd798aa053e6bbdb88c1b3`, tree
`f351fa18c1f824abcfdbd3d78f4ba9729ad03617`, passes the bounded development
transaction gate. The solver is bound to local recovery implementation
`d4611acced1bfbeb11246b6297d33cb69de86ed0`.

This is private development, not production qualification or a speed claim.
Independent review remains pending. The complete GE-B3 objective is unfinished.

## Separate inventories and evidence

- Smoke: 3 passed, 8 deselected; supervised wall 13.437 seconds.
- Complete rehearsal: 11 passed; supervised wall 23.056 seconds.
- Frozen cycle A: 11 passed; supervised wall 23.853 seconds.
- Frozen cycle B: 11 passed; supervised wall 23.654 seconds.

All 24 canonical packets are byte-identical between A and B. The frozen cycles
checked exact Git identity and configured runtime before and after execution;
this is not full dependency-graph qualification. All children terminated within
their existing bounds. No retry was performed.

The straight elastic, curved elastic and plastic load/unload/reversal paths
use 14, 14 and 23 Newton factorizations respectively. None uses the full mixed
fallback. This removes the earlier measured fallback obstruction on these
three paths; it does not prove a general speed improvement or large-mesh scaling.
Recovery has its own factorization, so total cost still requires measurement.

Every accepted mechanical state, constitutive origin/history and residual was
compared with hash-bound archived dense-solver records. Those dense load paths
were not rerun. Largest normalized record difference is 8.166175309749779e-12,
in a plastic unloading residual; corresponding mechanical difference is
7.765822707117565e-12. Both satisfy the unchanged 1e-11 gate. This unloading
step converges with a different iteration count, so cross-backend records are
not bitwise identical. Maximum final physical-recovery difference is
2.220446049250313e-16. Do not relabel this as exact cross-backend parity.

Same-backend paused/resumed capsules are byte-identical to uninterrupted
capsules. Cross-backend restart is rejected. Cancellation before trial and
commit and after factorization, injected factor failure, program mutation,
and iteration exhaustion retain the last accepted state without committing a
trial history. Plastic history is genuinely nonzero in the plastic case.

The new controller loop was checked against its preserved predecessor: only
the solver import, program identity and diagnostic labels differ. This is an
implementation self-check, not an independent review. Element/section/load
operators, globalization, residual tolerances and state transactions did not
change. The predecessor and all prior failures remain immutable.

## Preservation and next work

The canonical status and manifest bind 99 data files plus the manifest copy at
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-equilibrium-controller-66774bf-20260907`.
They include smoke, rehearsal, both frozen cycles, and three frozen source
copies. Original temporary results are preserved as well.

Next, test the recovery/controller on bounded multi-element straight and curved
members, including statically indeterminate supports and preserved history,
before considering general solver adoption. Review production integration
requirements for native rotation/internal-state transactions; do not confuse
this private driver with the existing public GE-B3 facade. Independent review,
general six-resultant nonlinear-section support, complete workflow parity,
standalone qualification and the objective beam-shell joint remain required.

Existing B2/B3, Q4/S3 mechanics, qualification evidence, defaults, aliases and
packages remain unchanged. No public activation, push, merge or release occurs.
