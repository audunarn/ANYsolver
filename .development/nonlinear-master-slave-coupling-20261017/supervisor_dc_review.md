# Independent DC lifecycle and continuation-test review

Static review of the in-progress owner edits, 2026-10-18. No imports, numerical
solves, pytest, product/test edits or additional workers. Mistral retains
implementation and numerical-execution ownership. Source was being edited during
review; transient incomplete indentation was not treated as a final defect.
Line numbers identify the inspected version and may move.

## Concrete product findings

### DC1 — P1: zero control span can retry forever

nonlinear_static.py:3961 computes min_control_subincrement from
abs(target_increment)/(num_steps*256). At 4204–4217 a failed attempt is retried
when half the attempted remaining span is >= that minimum. When the requested
target equals the initial controlled displacement, both values are zero. The
condition remains true while attempt_fraction repeatedly halves, even after it
underflows to zero; every retry solves the same target with no progress.

Reachable example: ordinary finite DC restart at its current controlled target,
no contact, rotating MPC, max_iterations=1. The helper starts lambda at zero.
The first Newton correction can recover the prior equilibrium lambda, but the
one-iteration loop ends before reevaluating convergence, reports the iteration
limit, rolls lambda back to zero and retries. The zero-span cutback condition
never terminates. This is independent of whether the physical state itself is
already valid at its known previous lambda.

Require strictly positive finite attempted span and representable target
progress before subdivision, with an explicit bounded minimum. A zero-span
request can run its bounded Newton attempt but must retain a finite failure
exit if it cannot converge. Do not rely on an external timeout to terminate the
loop. Add a focused zero-span restart/forced-iteration-limit regression; it can
use a controlled fake assembler/factorization to verify bounded attempts.

### DC2 — P2: per-step iteration counts accumulate across accepted subdivisions

step_iterations is initialized once per scheduled milestone at 3981 and
incremented after each attempt at 4172. Every accepted subincrement publishes
that same cumulative count in NonlinearStaticStep and history around 4314/4331.
If the first accepted subincrement uses a iterations and the next b, their
records report a and a+b. Summing records double-counts a even though the
separate total_iterations counter increments correctly per actual iteration.

Reset the per-published-increment iteration accumulator after acceptance (or at
the start of the next publication interval). Keep failed-attempt counts and
scheduled-milestone totals in explicitly cumulative fields if desired. Preserve
all failed-attempt work in the solve-wide total and evidence. The similarly
cumulative attempts/cutbacks fields should state their scope, rather than
implicitly appearing to describe only that accepted subincrement.

## Lifecycle and adaptive-loop assessment

The latest inspected loop confines subdivision to an active rotating map with
no contact manager. Legacy/contact routes keep their prior fixed milestones.
Each original milestone is computed from initial_control and target_increment;
an accepted fractional target continues toward that same milestone, and the
loop proceeds to the next scheduled milestone only after the full remaining
interval is accepted. The chosen minimum span gives a geometric refinement
floor; it does not authorize changed tolerances, omitted milestones or an
unbounded retry campaign. DC1 needs correction before this is reliably bounded.

The main inspected state seams are appropriate:

- Each attempt captures q_attempt_start and lam_attempt_start. Failed attempts
  discard the active material candidate and restore both before retrying.
- Only an equilibrated candidate reaches _commit_nonlinear_state_candidate.
  Reaction recovery after commit opens a diagnostic trial, which is explicitly
  discarded before subsequent accepted-state history/snapshots.
- Accepted records have their own monotonically increasing record_step_index;
  snapshots are appended only after commit. NonlinearIncrementSnapshot copies
  displacements and deep-copies material history; persistent-store snapshots use
  owned SAVED_STATE materialization.
- Caller displacement/history is detached by the public owned-input helpers;
  the preparation boundary deep-copies ordinary material state. Persistent
  trial cleanup is also registered in the public solve's finally scope.
- Cancellation safe points occur before Newton evaluation, including the first
  evaluation of a retry. A callback that cancels after two accepted events is
  observed at the next safe point. Do not turn SolveCancelled or validation
  failures into ordinary cutback retries.

These are source checks, not proof that a failed constitutive candidate never
mutates its accepted parent. Tests must still discriminate rollback/history
contamination. Failure before the first accepted ordinary resumed increment also
retains the known lambda=0 initial-guess reporting limitation documented in the
earlier review; do not call that failed result an equilibrium at the half-state
lambda merely because its displacement/history rolled back correctly.

Full12 and half6+resume6 have the same scheduled control grid. Subdivision must
retain that grid and compare physical states at common milestones, with all
accepted between-milestone states independently checked. A fixed slice such as
full.steps[6:] is invalid once subdivisions insert accepted records; the owner
has already replaced that with control-milestone selection. Matching scalar
milestone positions alone does not establish matching material history.

Progress currently emits completed=local_step_index even for an accepted
subdivision before that milestone is reached (4368). This can report the final
progress fraction1 before the final target is reached. It does not change the
solver state or current cancellation test, but should be labelled milestone
index or replaced by monotone fractional milestone progress. The accepted event
step_index should remain the actual accepted record index.

## Continuation-test findings and coverage gaps

### T1 — reaction oracle correction is now sound for this fixture

The original helper summed all-node imbalance plus all-node applied load,
which algebraically tested only internal self-equilibrium. It also used reference
force arms/raw rotation covectors. The latest source at
test_nonlinear_beam_shell_slice3_continuation.py:307–375 corrects this: it transfers
beam-slave imbalance, gathers only fixed shell root nodes, uses deformed force
arms, and balances that root wrench against applied tip loads. Root rotations
are fixed zero, and this EP load has zero nodal moments, so the used moment
covectors are legitimate spatial moments. No further false reaction oracle was
found in this revised fixture.

### T2 — P1 acceptance gap: only final accepted state is independently checked

_assert_completed_dc_case at 378 calls _independent_equilibrium once on the final
result. Snapshot assertions compare only count and control_value, so an earlier
accepted subincrement with a large independently reconstructed residual or bad
constraint can pass if the final solve recovers.

Parameterize the reconstruction over an explicit accepted displacement,
snapshot.element_states and snapshot.load_factor. Check every accepted snapshot
for the unchanged <=1e-7 residual criterion and appropriate constraint tolerance,
including inserted adaptive states, and require the final snapshot to agree with
the public final state. Reuse the already assembled model/load/transformation
for these checks without changing constitutive truth. Deep-copy before the
independent reassembly and assert both the stored snapshot and supplied copy
remain unchanged.

The helper currently divides by norm(J.T F_prop), not norm(J.T lambda*F_prop).
For an achieved-load relative-residual claim use max(norm(J.T F_actual),1), as
the reviewed assessment_support helper already does. Unit-load normalization
is stricter when lambda>1 but weaker when lambda<1; early accepted states cannot
be assumed to have lambda>=1. Preserve the <=1e-7 tolerance.

### T3 — P1 acceptance gap: scalar alpha maxima are not full plastic history

The restart test around 451–525 compares final u/lambda and common-milestone
control/lambda/max_equivalent_plastic_strain. It does not compare per-element
plastic_strain tensors, alpha arrays or fiber histories between resumed and
uninterrupted paths. Equal maxima can conceal a changed distribution or a
partially reset state. Monotone maxima do not prove local hardening/history
continuity either.

Use the corresponding accepted snapshots to compare the physical material
fields for every shell/beam element at the split, common milestones and final
state, retaining the existing strict restart tolerances. Compare shapes/IDs and
all integration-point/fiber entries, not only peaks. Compare the half-run prefix
with the uninterrupted prefix too. Keep derived caches/origin bookkeeping
separate from physical tensors when those records legitimately depend on trial
iteration details; do not strip or weaken physical state checks to obtain a pass.
If adaptive substeps differ, preserve/report that fact and still meet the adopted
milestone/final material-state criteria without tolerance relaxation.

This is distinct from caller immutability: success/cancellation tests correctly
use exact before/after equality for the caller-owned arrays/metadata. That proves
inputs were preserved; it says nothing about the accuracy of the newly returned
resumed material history versus uninterrupted history.

### T4 — P2: rejection/cancellation snapshot integrity is not fully observed

The malformed-restart refusal test retains/checks only the displacement input;
its material input is copied inline and cannot be compared after refusal. The
stopped-resume test similarly passes displacement/history inline and then checks
only the rolled-back control coordinate and snapshot count. A contaminated
plastic parent could pass those assertions.

Retain named deep copies of both input objects and compare them exactly after
refusal/rejected-step termination. For an actual failed trial, compare returned
physical displacement/material fields with the last accepted snapshot (or the
half input if no new step was accepted), not only probe uz. Preserve/freeze the
half result's exposed snapshots before successful, failed and cancelled reuse,
then compare their complete contents afterward. To observe snapshots accepted
inside a run that later raises cancellation, a focused capture of
_increment_snapshot outputs can expose them to the test without changing
mechanics. Check retained snapshot displacement/history after later rejected
trials/cancellation.

The intentionally max_iterations=1 stopped test is a useful rejection scenario,
but completion is a behavior to assert from the bounded fixture, not a general
mathematical fact: an already converged zero-change candidate could complete in
one evaluation. The nonzero plastic increment used here should discriminate the
intended failed trial, and must not trigger DC1's zero-span retry edge.

## Handoff

D1's GENERAL classification is present in the current augmented factorization.
No further existing-loop lifecycle defect beyond DC1/DC2 was confirmed in this
read-only pass. T2/T3/T4 remain missing acceptance evidence, not proof of product
failure. Owner repairs and stable focused checks must establish them within the
remaining shared allowance. No numerical authority or tolerance change is added.
