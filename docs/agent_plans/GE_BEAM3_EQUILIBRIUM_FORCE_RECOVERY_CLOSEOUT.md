# Equilibrium-first force-recovery local development closeout

Frozen implementation `d4611acced1bfbeb11246b6297d33cb69de86ed0`, tree
`973c92e1356d1be3d1cde193fdc07455ae706c59`, has passed its local gate.
This is **not production qualification, controller adoption, or a speed claim**.
Independent review remains pending. The overall GE-B3 task is incomplete.

## Separate inventories

- Rehearsal: 9 passed; supervised wall 5.820 seconds.
- Frozen cycle A: 9 passed; supervised wall 6.020 seconds.
- Frozen cycle B: 9 passed; supervised wall 6.018 seconds.

Both frozen cycles checked the exact commit and configured runtime before and
after execution. This guard is not a complete dependency-graph qualification.
All eight canonical scientific packets are byte-identical between A and B.
Every case passed without refinement or a full mixed-system fallback. Maximum
componentwise backward error is 8.851692551561641e-15, below the unchanged
1e-11 threshold; maximum relative difference from a full-system solve is
9.411714643950617e-15. The curved initial 36-by-36 system additionally has an
independent standard-library rational solution with exact matrix multiplication;
its relative binary64 increment difference is 1.4540057786364309e-16.

The tests cover initial exactly unloaded equilibrium rows, three local trials
reconstructed from immutable accepted elastic/plastic histories, two-macrocell
cantilever and doubly clamped force recovery, multiple right-hand sides,
deterministic reuse, immutable ownership, and malformed-input rejection.
They ran zero native nonlinear load paths and zero eigensolves. Reconstructing
an accepted history validates that history; it is not a new load-path solve.

The replacement recovery solves all geometric equilibrium rows and completes
them with original compatibility rows where required. The geometric Schur
factor remains unchanged. No clipping, added absolute tolerance, full mixed LU
fallback, mechanical-law change, or rank-qualification claim is introduced.
The new recovery factor is additional work: an end-to-end speed improvement
must be measured, not inferred from the absence of a full mixed fallback.

## Preservation and next gate

The companion canonical status and archive manifest bind 37 data files: three
separate test inventories, their packets/logs, and four frozen source copies.
Archive root:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-equilibrium-recovery-d4611ac-20260907`.
It also contains a byte-identical manifest copy. Original temporary results and
all historical failure evidence remain preserved. All supervised children
terminated; no retry or consumed-request reuse occurred.

Next: review the private recovery implementation, then prepare a separately
frozen bounded nonlinear-controller comparison. Verify complete accepted-state
origins/history, physical recovery, reactions, cancellation, rejected-step
rollback, and same-backend pause/restart before adopting this solve path.
Preserve the existing fallback-heavy controller and its negative optimization
conclusion. Do not rerun historical qualification campaigns to make this gate.

Existing B2/B3, Q4/S3 mechanics, aliases, defaults, packages, and qualification
evidence are unchanged. No push, merge, tag, release, or activation is performed.
