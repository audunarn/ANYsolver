# Non-author source review — rotating MPC/work-conjugate route

2026-10-18. Reviewed the five-file working diff against HEAD
`b0202d335990a1fd1a647b7876ebde001aabe979` (+1226/-146 at inspection), the two
new Slice 1/2 test modules, and the necessary constraint compiler, initial-state,
restart and reaction callers. This was static source review: no imports, solves,
pytest, Git mutations or product/test edits. Existing 22+39 baseline passes are
supervisor-supplied evidence, not checks executed by this reviewer. Mistral owns
implementation and repairs. Line references below identify the inspected source
before further worker changes.

## Confirmed source defects

### R1 — P1: downstream MPCs silently retain the linearized rotating-slave position

Entry: `build_nonlinear_rotating_mpc_map`, corotational.py:1471–1511;
`NonlinearRotatingMPCMap.apply_kinematics`, corotational.py:1312–1321;
`jacobian`, corotational.py:1336–1369.

The ordinary compiler explicitly accepts and topologically resolves cascading
MPC dependencies (assembly.py:201–270). The new map adds its nonlinear correction
only to each descriptor's three slave translations. It does not propagate that
correction to downstream affine dependent DOFs. A permitted generic equation
`u_Cz=u_Bz` downstream of a rotating slave B therefore becomes false in the
returned physical displacement: `u_Bz` gets the finite offset correction but
`u_Cz` remains the original row of Tq+u0. A second rotating coupling using B as
its translational master has the same missing upstream correction. Sorting by
element id does not repair this, because the implementation adds a correction to
the pre-expanded linear slave state rather than reconstructing its translation
from the updated master translations.

`to_linear_displacement` then removes the correction from B alone. Thus the
existing inverse-map linear constraint postcheck can pass while the original
downstream physical affine equation is violated. The map Jacobian and reduced
forces may be internally consistent with this wrong manifold; their standalone
finite-difference checks do not establish composition correctness.

Minimal discriminating test: attach an eccentric beam node B to shell node S
with e=(0,0,e), append another node C with a generic linear `uz_C=uz_B`, and
set a compatible reduced shell rotation ry=alpha. At fixed shell uz=0,
`uz_B=e*(cos(alpha)-1)` but `uz_C=0` after the current map. Check the physical
equation directly; do not use only `constraint_residual_summary(to_linear(u))`.
Also cover a second rotating descriptor downstream of B.

Bounded compatible repair: full nonlinear graph composition is unnecessary for
Slice 3. Fail closed before constitutive activation when any other admitted
affine equation uses a rotating slave *translation* as a nonzero master. Use the
actual normalized constraint equations/coefficients (respecting the compiler's
coefficient filtering), not only a check for another rotating descriptor. Every
downstream chain has such an immediate first edge, so checking direct use is
sufficient to reject all unsupported descendants. Report the slave DOF and
offending equation/element. Reject mixed translation-to-rotation dependencies
too. This permits existing linear-only chains when no active rotating descriptor
is present, and permits upstream shell row ties because those do not depend on a
rotating beam slave translation. Rotating-slave rotations need not be banned
solely because they are downstream: their map remains linear. Tests should prove
both refusals and preservation of an ordinary linear chain/upstream shell tie.

### R2 — P1: initial-field equilibration uses and commits the wrong manifold

Entry: nonlinear_static.py:6098–6113 calls `_equilibrate_initial_fields` with
T and the affine offset but no rotating map. Both helper signatures are at
3454 and 3584. The candidate helper uses raw `T@q+u0` at 3508 and 3557,
`-T.T@F_int` around 3522, and `T.T@K_T@T` around 3537. The commit wrapper
records raw `T@q+u0` at 3626. The initialization-failure recovery similarly
returns the uncorrected affine state around 6122.

For residual/initial fields that require finite rotations, the initializer
therefore solves the linearized-offset constraint problem and accepts material
history at that state. Subsequent main load iterations expand the same reduced
coordinates through the nonlinear map. The accepted displacement/history pair
then belongs to a different kinematic state, even if the initializer reported a
small residual. This is a separate entry path from the correctly mapped main
force/DC Newton loops.

Required threading, all within owned nonlinear_static.py:

- Add an optional rotating-map argument to both helper signatures and their
  call-through. Preserve the existing path when it is None.
- Expand both ordinary and backtracking candidates through the map.
- Use `-map.reduce_force(u,F_int)` and
  `map.reduce_tangent(u,K_T,F_int)` for the zero-external-load equilibrium.
- Commit the mapped accepted displacement and return mapped initialization
  failure recovery. Keep the existing single accepted transaction/finally
  discard behavior, cancellation safe points and unchanged caller inputs.
- Reconcile subsequent displacement/state activation with the accepted mapped
  initializer output; do not reintroduce the pre-initialization displacement.

Minimal discriminating test: a small coupled strip with an allowed elastic
initial bending/prestrain field that produces nonzero master rotation during
zero-load equilibration. Independently check the returned physical offset and
`J(u).T@F_int` using copied accepted state. Check constitutive state agrees with
that same displacement. Include failed/cancelled initialization to prove caller
history remains intact and failure recovery lies on the correct manifold.

### R3 — P2: fully constrained prescribed finite motion bypasses the rotating map

Entry: nonlinear_static.py:5960–5971 selects `fully_constrained_displacement`.
For a non-checkpoint call it chooses `initial_affine_offset` or raw `u0`, while
the mapped state constructed earlier is used only in the checkpoint branch.
The raw vector then reaches constitutive evaluation/accepted-state recovery and
the returned result at 6006, 6026, 6058–6074.

A model with every shell/master DOF prescribed and all beam DOFs eliminated by
their coupling has n_red=0 and is admissible to the constraint compiler. Give
the shell a finite prescribed rigid rotation and matching rigid translations.
Its eliminated beam must obey the finite rotated lever arm. The current early
return instead returns the linearized lever arm from u0, despite active
corotational rotating coupling. This also risks pairing initially activated
mapped state with uncorrected final recovery.

Minimal test: prescribe a rigid rotation ry=alpha to all shell nodes with
translations `(R-I)X`, constrain all remaining master DOFs, leave beam slaves
defined only by the coupling, then call the fully constrained public route.
Assert finite beam offsets/rotations and zero strain for the rigid motion; do
not require an ordinary completed-load status where the existing contract uses
`empty_reduced_system`. Cover direct and interpolated descriptors. Construct the
full constrained vector through the map before all evaluation/recovery/return
uses, preserving the existing branch's status semantics.

### R4 — P1: follower + auto silently changes the internal force law

Entry: nonlinear_static.py:5344–5359 resolves auto to work_conjugate only under
`and not follower_active`. With any follower pressure it falls through to
`consistent`. In corotational.py:400–413 work_conjugate calls the B.T pullback,
but the legacy consistent path around 435–460 rotates the local force blocks
with E instead. These are different internal forces, not merely alternative
tangent approximations. Follower external tangent assembly and rotating-map
external reduction are otherwise present in the main force/DC loops.

Consequently adding even an arbitrarily small follower pressure to a finite
dead-loaded rotating-MPC model switches its internal mechanics away from the
advertised exact work-conjugate route. The baseline tests use dead nodal loads,
so they do not exercise this discontinuity.

Preferred supervisor-adopted repair: choose work_conjugate for rotating-MPC auto
even when follower loads are present; retain the external follower tangent,
general matrix classification and net-imbalance MPC Hessian. Explicit legacy
`rotated`/`consistent` requests need a conscious compatibility/refusal decision;
do not silently claim they use the exact work-conjugate force. Changing a tangent
request must not accidentally change promised mechanics without declaration.

Minimal tests: inspect effective mode under auto with nonzero follower pressure;
check the complete derivative of reduced net internal-minus-external force at a
finite state against central differences, including external load derivatives
and MPC geometric contribution. Add a limiting small-pressure comparison to
ensure internal-force dispatch does not jump as pressure tends to zero. This
requires a caller-level test as well as the existing map helper derivative test.

### R5 — P2: displacement-control admission still uses the initial linear row

Entry: nonlinear_static.py:3861–3864 checks `row_full@T` and rejects when it is
zero. The actual Newton row later correctly uses `row_full@map.jacobian(u)`
around 4088–4092. These can differ even at an admissible finite restart.

Example: master uz is fixed, ry is free, e=(0,0,e), and control the beam slave
uz. The linear MPC gives zero linear control row, while the nonlinear position
is `uz_B=e*(cos(ry)-1)` and its finite-state derivative is `-e*sin(ry)`.
At a restart with ry nonzero the control coordinate is usable, but the current
preflight rejects it before considering that Jacobian. At ry=0 the derivative
really is zero, so refusal there remains appropriate.

There is a second origin-state admission check immediately afterward:
`initial_u=full_u(zeros(n_red))` at 3866 is used to reduce the proportional load
and reject a zero result around 3892–3898. A force in the same nonlinear-only
slave uz direction has zero reduced force at ry=0 but nonzero reduced force at
the finite restart. Fixing the control row alone would leave this false refusal.

Use the actual initial mapped state `full_u(q)` for both control-Jacobian and
proportional-load admission (including the supplied finite reduced initial
state); preserve the old linear admission when the map is absent. If this class
of nonlinear-dependent controls is outside
the adopted scope, state that limitation explicitly rather than reporting it as
fixed. Add a finite-state admission test and a zero-Jacobian refusal test.

## Confirmed limitation requiring scoped claims, not an unapproved map redesign

The interpolated law averages additive rotation vectors, not rotations. It is
not equivariant under arbitrary superposed rigid rotations when master rotations
differ. The existing rigid-motion test starts with all masters sharing one
rotation, where this issue is invisible.

An exact algebraic counterexample: two equally weighted master orientations
Rx(+pi/2), Rx(-pi/2) have zero mean rotation vector and mean orientation I.
Superpose Q=Ry(pi/2). Principal logs of Q*Rx(+/-pi/2) have y components
`2*pi/(3*sqrt(3))`; their x/z components cancel. Averaging gives
Ry(1.209199576...), whereas the superposed original mean is Ry(pi/2). Thus the
beam director and finite lever arm do not undergo the same Q. The common
single-axis planar analytical family does not have this noncommuting-rotation
obstruction.

The Path 1 average-vector law was explicitly adopted. This review does not
authorize replacing it with another SO(3) interpolation or changing public
compatibility. Restrict objectivity claims accordingly and retain this as an
explicit general-3D limitation/reserved architecture decision. A regression
documenting refusal or admitted scope would be useful if a general objectivity
claim is intended.

## Optimized pullback and state/reaction review

No separate confirmed algebraic defect was found in the inspected optimized
pullback. The precomputed translational projection and cross-product term match
`D.T@f + G.T@(U.T@f)`; the shell analytic G follows the normalized tangent-frame
derivative; two-node beam translation columns may be negatives by exact
translation invariance. The shell rotation-column shortcut freezes a shell frame
that is independent of nodal rotations, as required. These statements are static
algebra checks, not new runtime evidence. Finite-difference G/Hessians and forced
symmetrization mean that the implementation's word “exact” denotes the intended
derivative, not exact arithmetic or an independent tangent certification.

The main force/DC iterations, line-search promotion and reaction assemblies
thread mapped full displacements and the appropriate net-imbalance Hessian.
The DC performance implementation delegates to the checkpoint-capable ordinary
route whenever a rotating map exists (nonlinear_performance.py:1520), avoiding
an unmodified block fast path. Map apply/inverse helpers copy input arrays.
I found no new mutation/cancellation defect in those inspected seams, but did
not execute cancellation/rejected-step/restart scenarios.

Remaining acceptance coverage in the two reviewed tests:

- Restart test at test_nonlinear_beam_shell_coupling.py:618 uses a direct
  initial-displacement/material restart with dead elastic load. It does not
  establish serialized checkpoint replay, DC split restart, plastic history,
  cancelled/rejected-step atomicity or bit-exact nonlinear-map round trips.
  The inverse helper test asserts allclose, while public checkpoint code uses
  array_equal: floating round-trip representability remains a hypothesis to
  test, not a confirmed defect from this review.
- Wrench test around lines 569–615 checks each slave-to-average rotation torque
  identity and total support *force*. It does not check total spatial moment
  including deformed force arms, different interpolated-master rotation duals,
  or nonzero prescribed support rotation. `_support_reaction_resultants` sums
  additive rotation covectors; do not label those raw sums spatial moments in
  a general finite-rotation configuration without the appropriate conversion.
- Tangent tests validate matching, one-level direct/interpolated maps at selected
  states. They do not cover R1 composition, R2 initial fields, R3 fully prescribed
  state, R4 follower dispatch or R5 nonlinear-only control admission.
- No full final 25-module regression or new Slice 3 gate result was available to
  this static reviewer. Baseline passes do not close these entry-path findings.

The implementation owner should repair the bounded confirmed defects, preserve
failed evidence and unchanged acceptance tolerances, then return actual focused
test evidence for supervisor acceptance. No additional numerical authority is
conferred by these suggested tests.

## Follow-up correction and bounded DC restart recommendation

### Correction: R2 is not reachable under current capability admission

Later entry-path inspection found nonlinear_static.py:5683–5689 rejects any
corotational solve whose committed state contains initial stress/prestrain
fields, with NotImplementedError. A rotating map exists only for corotational
kinematics. Therefore R2 above is **withdrawn as an admitted-route defect**:
the raw helper is a latent integration gap if that future capability is adopted,
not an active Slice 3 repair requirement. The existing refusal should be retained
and can be tested without implementing new initial-field mechanics. The earlier
report should be read as four confirmed admitted-route findings (R1/R3/R4/R5),
not five. This reviewer missed that preflight in the initial assessment.

### Recommendation: use supported ordinary state restart for this DC gate

The task requires displacement/plastic-history restart and caller-input
integrity, not serialization. Stop the optional serialized-checkpoint probe
detour, preserve its failures as a separately identified pre-existing limitation,
and use:

1. Original dead shell-node reference load; target uz=-0.10, six DC steps.
2. Same model/load/control coordinate; target uz=-0.20, six DC steps, supplying
   copied `initial_displacements=half.displacements` and
   `initial_element_states=half.element_states`, with
   `equilibrate_initial_state=False` and `emit_restart_checkpoint=False`.
3. Compare with target uz=-0.20 in twelve uninterrupted steps under unchanged
   iteration/tolerance settings and existing restart tolerances.

Prefer reuse of the original model/load for the resumed route; use a separate
identically configured model for the uninterrupted control. No field stripping,
manual constitutive-state alteration, tolerance relaxation or private load-factor
injection is needed. Ordinary returned corotational Q4 states can be unsealed:
the ordinary-restart branch around 2260–2274 explicitly admits their migration
when displacement/history are supplied together and re-equilibration is false.
Do not remove valid seals from caller data to bypass a validator.

Source reasoning: `_prepare_initial_states` deep-copies material history
(3012–3046); `_prepare_qualified_q4_states_for_nonlinear_solve` independently owns
another copy; DC q is recovered from inverse-mapped initial displacement
(5873–5888); the DC helper copies q, computes initial_control from its mapped
state, and spaces subsequent targets between that initial value and the new
absolute target (3839–3915, 3960). Committed alpha/plastic strain is not reset.
The public helper call supplies initial_load_factor=0 unless restoring a
serialized path (6444–6448). This zero is a Newton guess, not a plastic-state
reset. It does reset step numbering/history metadata: the resume result has six
new records, not twelve automatically restored records.

For this specific EP gate all applied proportional forces act on shell nodes
(diagnostics/ep_edge_coupling.py:119–122). Their rotating-slave force entries are
zero, so map reduction of that load is independent of q and its MPC external
geometric tangent is zero. There is no follower pressure, moving tool or staged
load. At the half equilibrium let reduced internal force be lambda_h*f. The
first resumed augmented Newton equation started at lambda=0 is

    K*dq - f*dlambda = -lambda_h*f + small_half_residual,
    control_jac*dq = next_target-current.

Writing dlambda=lambda_h+dLambda makes it the same first displacement equation
as starting with lambda_h, up to the half solve's residual tolerance. The tangent
is the same because the external follower and MPC geometric derivatives vanish
for these shell-node dead loads. Later iterations have the normal absolute
lambda. Thus the default-zero guess is compatible with the same accepted DC
target sequence and does not consume/reset material history. This argument does
not extend automatically to follower loads, load-dependent contact/tool paths,
or loads on rotating beam slaves, whose external MPC Hessian depends on lambda.

One limitation must remain explicit: if an ordinary resumed solve rejects its
first new step, its rolled-back displacement/history can be the valid half state
while the returned lambda remains the helper's zero initial guess. Do not claim
that such a failed result has the half state's physical load factor. Check
caller-state integrity using the known half result; cancellation raises instead
of returning a complete resumed result. This does not prevent the required
successful ordinary restart or input-integrity checks.

### Diagnostic/helper conflicts to fix before another bounded run

- `dc_solve` hardcodes `emit_restart_checkpoint=True` at diagnostic line 190.
  Remove that requirement for full/split/cancel stages; passing the opposite
  keyword through `**extra` would duplicate the keyword rather than override it.
- `stage_dc_split` currently consumes checkpoint bytes and compares complete
  step dictionaries/bytes (229–249). Replace with ordinary displacement/history
  inputs. Compare half records followed by resume records against the twelve
  uninterrupted physical records. Account for local resumed indices 1–6
  prospectively in the comparison only; do not falsify the returned records.
- `independent_residual` (139–154) hardcodes lambda=1. DC solves for lambda,
  generally different from one. Evaluate residual at the actual result or
  snapshot lambda, with the same reference load and copied state. Its reference
  scale should also reflect the actual applied load convention, rather than
  silently reporting a unit-load residual as a DC equilibrium test.
- `stage_dc_cancel` installs `status_callback`, but the DC helper does not call
  that force-control-only observer. Use `progress_callback` filtered to
  event_type `nonlinear_static_step` / stage `nonlinear_static.displacement`.
  Cancel the token after two accepted new steps; the next DC cancellation safe
  point raises SolveCancelled. Merely raising inside the progress observer is
  unreliable because progress callback exceptions are normally suppressed.
- `dc_summary` hardcodes target_error relative to -0.20. Parameterize the target
  when reporting the half solve as well.

### Necessary evidence under the existing execution allowance

- Both routes: half/full/resume status is completed; controlled targets agree;
  positive plastic strain; final u/lambda and all physical plastic histories
  agree within the unchanged existing restart tolerances.
- Stitch half+resume accepted control/load/alpha histories and compare with the
  twelve uninterrupted steps. The half solve's achieved -0.10 can differ from its
  exact target by its stated constraint tolerance; report that error rather than
  silently resetting the displacement to an exact target.
- Retain deep before/after copies of supplied displacement, every nested material
  history array/metadata, and half accepted snapshots. Prove unchanged after a
  successful resume, a deliberately rejected resume and token cancellation;
  then reuse the same untouched input for a clean successful resume.
- Verify accepted snapshots have their own stable displacement/history contents.
  If cancellation throws before exposing the cancelled run's local snapshots,
  a focused test can capture `_increment_snapshot` outputs without changing
  mechanics, then compare their deep-frozen copies after later trials/cancellation.
  At minimum preserve/check the exposed half-result snapshots after all reuse.
- Independently reconstruct the final/snapshot reduced residual at its own lambda
  and retain actual constraints/reactions. Do not infer restart success from
  unchanged input data or merely from the public converged property.

No numerical execution or product/diagnostic edit was performed for this follow-up.

## Static recheck of owner continuation edits

The following reflects the in-progress source at this recheck, not a final
verified patch; no imports/tests/solves were executed.

- **R1:** the new guard in corotational.py:1471–1512 checks normalized admitted
  equations for direct use of rotating-slave translations as masters. This is
  sufficient to reject the first edge of every unsupported downstream chain.
  Upstream shell ties and ordinary linear-only chains are preserved. The guard
  is called at map construction before constitutive-state activation.
- **Support-on-slave hypothesis is unreachable:** skipping support equations in
  that downstream-master guard does not admit a fixed rotating beam slave.
  constraint_audit.py:409–419 rejects support/MPC multiple definitions of one
  dependent DOF; assembly.py:177–180 independently rejects a DOF both fixed and
  used as an MPC slave before the map can be built. This remains true even when
  the prescribed value happens to equal the linear relation at the initial
  state. Standard shell-root supports constrain master DOFs and remain allowed.
  No additional support-composition feature or refusal guard is warranted.
- **R4:** current dispatch selects work_conjugate for rotating-MPC auto with
  follower pressure and explicitly refuses legacy rotated/consistent requests
  on that route. External follower derivatives remain assembled/reduced in the
  existing loops. This addresses the static force-law dispatch inconsistency;
  runtime derivative/equilibrium evidence remains pending.
- **R5:** current preflight uses `initial_u=full_u(q)`, its map Jacobian for the
  initial control row, and that same state for proportional-load admission.
  This addresses both reported origin-state false refusals. No runtime success
  or zero-Jacobian-refusal evidence is claimed by this review.

### Actionable remaining R3 defect in the first attempted repair

The first R3 edit selects `initial_committed_displacement` unconditionally at
the n_red==0 return (nonlinear_static.py:5997). Its comment says that vector
equals map(u0) outside restart cases, but the fresh **force-control** path at
5858–5870 explicitly sets

    force_affine_path_mode = PROPORTIONAL_PRESCRIBED_FIELD
    initial_committed_displacement = map(T@q)

with no u0 term. When n_red==0 this is zero, even when u0 contains nonzero
prescribed master translations/rotations. Thus the attempted fix now discards
the prescribed motion completely in the fresh public force route instead of
returning map(u0). This is confirmed by the actual entry branches, not a
numerical hypothesis.

Bounded repair: preserve the prior fully constrained branch selection while
mapping only the vectors that are still linear. A checkpoint/ordinary force
restart can use its already mapped `initial_committed_displacement`; the fresh
prescribed-state path must use map(u0), with the identity behavior when the map
is None. Do not apply the map twice to a physical restart vector. Preserve the
existing empty_reduced_system status and all displacement/history binding rules.
The prescribed rigid-motion R3 test must assert the shell prescribed values as
well as the beam relation, so an all-zero returned state cannot pass merely
through self-consistency or zero strain. Final new-test review/execution is
deferred to the implementation owner and supervisor.

One entry-fixture conflict was visible in the in-progress R3 test: its shared
builder adds zero root supports at test_nonlinear_beam_shell_slice3.py:152–159,
then test_r3 appends nonzero ry=alpha supports to every shell node, including
those roots (around 342–363). The audit rejects the conflicting prescribed root
ry before reaching the intended branch. The prescribed-motion fixture should
replace/omit the original root supports instead of appending conflicting ones.
This is a static fixture finding only; no new test was executed.
