# Bounded native adaptive arc control

Base ce97463d1f14b65178cc45ebc16751a0a3410d78. This adds private
AdaptiveArcProgram / solve_adaptive_arc and an authenticated adaptive
checkpoint envelope. Public routes, versions, B2/B3 and all shell mechanics
remain unchanged. Independent scientific review remains PENDING.

## Mechanics and control

Extract one uncommitted attempt_step from the existing native arc loop.
Both fixed and adaptive drivers use the same predictor, analytic parameter
column, frame-chord constraint, GENERAL bordered solves and corrector.
No residual, tangent, constitutive, quadrature or tolerance expression changes.
The fixed driver retains the same event sequence and failure text.

An adaptive programme binds an exact one-step ArcProgram prototype, accepted
step count 1..64, positive min/initial/max step <=.25, at most eight cutbacks
per accepted step and at most 128 total attempts. The caller supplies scale
and bounds. Each new attempt starts from the last committed state.

Freeze the iteration-count policy: double after acceptance in <=3 iterations
only when that accepted step had no cutback; halve after >=7 iterations;
otherwise retain the step. Clamp proposals to caller bounds. These scalar
rules are independent of global coordinate components. On typed native
line-search or iteration-bound exhaustion only, halve subject to all bounds.
Do not catch authority/state, factorization, cancellation, validation-deadline,
observer or other failures as convergence. Never relax the 1e-12 arc merit.

Discard the active trial before a cutback. Verify exact committed-state
identity after rejection. Only fully staged/validated accepted history may
commit. A new external run is never an automatic retry of a consumed run;
bounded internal Newton/arc cutbacks are an explicit part of this programme.

## History and safety

The adaptive envelope binds the programme, model, attempt order and sizes,
accepted origin hashes, accepted iteration counts, typed rejection reasons,
deterministic next step and terminal disposition, plus the complete native
arc checkpoint. The latter retains full state and objective predictor replay.
No accepted snapshot or source prefix is omitted. Keep original 2-MiB and
explicit HISTORY8M capacities, 65 snapshots and existing 60-second validators.

Rejected attempts are authenticated solver diagnostics, not independently
reexecuted mechanical proofs. Replay the control policy and accepted-origin
links exactly; fully validate the accepted inner mechanical history.
Reject duplicate/nonfinite/noncanonical JSON, wrong hashes, missing fields,
programme/model mismatch, forged cursors, exhaustion and malformed histories.
Incoming external SHA-256 is checked before history replay.
An exhausted checkpoint cannot be resumed. Pauses at accepted or attempted
cursors must resume deterministically without forgetting prior cutbacks.
Fatal failures preserve the latest published accepted/cutback capsule.

## Development and frozen evidence

Keep separate test inventories:

- Local policy, exact fixed-inner equivalence, restart, mutation and resource
  preflight; cancellation/authority/factorization/observer failure preservation.
- Natural convergence cutbacks on the off-axis loaded native bar with one
  allowed corrector iteration; no injected mechanics for this case.
- Proper rigid rotation/translation covariance of adaptive response and
  identical step/disposition schedule for the registered noncommuting case.
- Curved plastic translation-source continuation and physical recovery.
- Curved plastic rejection after a real uncommitted trial; compare the final
  accepted inner packet byte-for-byte with direct fixed smaller-step execution.
  This last injected-failure test proves state safety, not a natural failure.

Rehearse first. Freeze implementation, tests and this plan only after they pass.
Run two fresh-directory copies of final local and both curved inventories;
require byte-identical scientific JSON within each inventory. Run fixed-arc
local/safety, source-handoff and accepted seeded sixteen-macro crossing
regressions, comparing scientific bytes to the preserved accepted archives.
A single bounded command may use a test selection; do not combine inventory
counts. Do not rerun historical failed scientific programmes.

Each child: one numerical thread, 24 GiB process-tree memory, 600-second wall,
120-second CPU inactivity. At most three concurrent children, <=1800 seconds
per wave, no automatic worker retry. Preserve raw logs externally, exclusive
fresh outputs, and terminate complete child trees in finally.
Frozen worktree and runtime guards run before and after formal execution.
Failures are preserved and block this gate; they never authorize default or
production changes.

## Scope of a passing gate

A pass establishes private adaptive-control development evidence only.
The accepted three-step arch crossing remains valid historical evidence;
this gate must not reclassify it. Automatic larger-scale arch adaptive
qualification, wider slenderness/postbuckling/spatial-stability, practical
scale, broader load/material/state parity, physical mass and spectra, public
installed-wheel integration, independent review/environment attestation and
objective beam-shell connections remain open.
