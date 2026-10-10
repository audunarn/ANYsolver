# General contact admission/globalization — Mistral connected work note (2026-10-10)

Living note for the D1 unblock-and-deliver milestone. Owner scope:
`q4_overlap_local_bound.py`, `s3_patch_static.py`, `semismooth_path.py`,
`static_path.py`, new `tests/test_general_contact_admission_globalization_*.py`,
this note only. Source checkpoint 905ea87c. Phase: source-only (no
imports/tests/numerical execution); everything below labeled accordingly.

## Measured obstruction (from LEAD_DISPOSITION_V1.json, FINAL_HANDOFF.md, trace/profile scalar rows)

- Full trajectory TIMEOUT 180.0362354 s / 287.484 MiB at physical increment 2,
  iteration 7, 8 selected corrections, no terminal checkpoint. Last relative
  equilibrium/control/NCP: 0.04664449 / 0.08574712 / 0.11266147.
- Step 1 converges in 3 iterations (merit 2.1e-5). Step 2 stagnates: merit
  0.125 -> 0.1234 -> 0.1155 -> 0.1137 -> 0.1128 -> 0.1127 -> 0.1127 -> 0.1127
  over 7 iterations, ~20-30 s each. Fraction searches grow 1.06 -> 22.0 s;
  each contains multiple swept certificates (0.38-8.3 s), each containing
  point-budget decisions. Nested inclusive times: 59 point-budget decisions
  94.32 s inside 50 swept checks 103.48 s and 8 fraction searches 103.55 s;
  structural assembly 18 calls 6.23 s. Not additive.
- Cost driver: `matching_projection_swept_lower(..., gap_budget, adaptive_depth=7,
  node_budget=1024, overlap_dual=True)` per candidate pair. Terminal boxes that
  refuse the gap budget run the axis dual (up to 3*choose(20,2) candidates) and
  the joint dual (choose(23,4)=8855 active-set solves) — wasted when the box is
  *genuinely* violating, because no dual can raise a valid lower bound above a
  true minimum that is already below -gap_budget.
- Globalization obstruction: `solve_increment` fixes the macro target and
  `reduced_external` for the whole increment; the swept certificate caps the
  admissible Newton fraction (saved search accepted 1/64), so Newton takes
  repeated tiny steps at the full macro target and the merit plateaus.
  max_iterations=18 at ~25 s/iteration (~450 s) would exceed the budget long
  before "iterations_exhausted" ever fires — a failure-triggered cutback alone
  can never trigger inside 180 s.

## Derived discriminating check (the cheap rigorous refusal witness)

The certificate's gap over a represented pair box is the target-plane height
g = N/|T| with N = (s - c0)·T (s = bilinear Q4 source point, c0 = S3 target
corner 0, T = target normal; verified: lower = min(0,N_min)·|P|_upper/(T·P)_lower
<= g everywhere in the box, so the certificate's own admission test is a bound
of exactly this quantity). Therefore:

- If an *enclosed* point (u,v,t) of the pair domain has
  gap_upper = N_upper/|T|_lower < -gap_tolerance, then the certificate's lower
  bound over the box is also < -gap_tolerance: the expensive adaptive/dual
  search would refuse anyway. Skipping it is decision-preserving.
- To keep the refusal *physically* meaningful (invariant: a rigorously enclosed
  violating point inside the represented overlap proves refusal), the witness
  additionally encloses the matching-projection foot y = s - rP,
  r = N/(P·T) (P = parent Q4 corner-0 normal), and requires enclosed barycentric
  coordinates of y in the target triangle: lambda1 >= 0, lambda2 >= 0,
  lambda1+lambda2 <= 1. Both conditions together are a true material violation;
  either alone is not trusted for refusal.
- The witness never returns a lower bound and never admits anything. It
  returns found/not-found plus explicit diagnostics (point, gap upper, foot
  barycentric enclosures). A point upper bound is never masqueraded as a
  domain lower bound.

Wiring (decision-preserving at each site):
1. `s3_patch_static._point_gap_budget_admissible`: after the cheap
   `q4_source_projected_gap_lower` / `overlap_local_lower` gates have already
   left lower < -tolerance, run the witness on the static pose; if found, return
   False immediately, skipping the expensive adaptive matching call. (Full path
   would compute matching <= witness gap < -tol, so max(lower, matching) < -tol
   -> False either way.)
2. `s3_patch_static._swept_admissible.certify.pair_gap_admissible`: after
   `whole_lower < -tolerance` and inside the d1 branch, run the witness on the
   swept pair; if found, skip the expensive matching call and fall through to
   the existing `overlap_local_swept_lower` fallback exactly as a refusing
   matching result does.
3. Endpoint checks inside `admissible_step_fraction`'s bisection become cheap
   for grossly unsafe proposal fractions (the dominant measured waste).

## Derived route (bounded declared physical continuation)

Opt-in (default off, exact current behavior) continuation cutback in the
semismooth branch of `solve_static_contact_path`:

- Per macro step: snapshot material/contact/load/control state. Attempt the
  full increment exactly as today, but with an explicit stagnation bail in
  `solve_increment` (declared reason `contact_semismooth_stagnation`): fires
  when `patience` consecutive iterations each accept a swept fraction <=
  fraction_threshold AND improve the merit by less than merit_threshold
  (defaults patience=2, fraction 1/8, merit 5% — fires at iteration ~4-5 of the
  recorded step-2 trace instead of never within budget).
- On stagnation/failure: restore the snapshot, then solve declared internal
  substeps along the *program's own* segment parameterization:
  target(tau) = (1-tau)*target_{k-1} + tau*target_k, forces likewise — exactly
  on the prescribed macro load/tool path. Adaptive bisection: span 1/2,
  halve on a failed substep (restore to the last committed boundary each time),
  bounded growth after success, minimum span 2^-maximum_halvings (default 6).
  No load fraction is ever inferred from a Newton line-search alpha; the
  continuation parameter is the declared tau.
- Every substep passes the same acceptance gates (report/gap re-evaluation,
  D1 admission, coordinated commit) and is declared in the macro history
  record under an additive `continuation` key (mode, cutback reason, substep
  list with exact tau endpoints, per-substep metrics). One history record and
  one NonlinearStaticStep per macro step; the macro waypoint is reached
  exactly; no hidden Newton commits.
- Boundaries: frictionless semismooth reference-linear profiles with plain
  mapping committed states (the fixture profile). Store-backed
  (`NonlinearStateStore`), finite/corotational, and friction paths keep the
  current behavior with a declared reason if cutback is requested.
- Rollback: `copy.deepcopy` of the plain committed-states mapping at the macro
  step start and at each committed substep boundary; restore on every rejected
  trial together with q/multipliers/normal multipliers/normal forces.

## Intended edits

- `q4_overlap_local_bound.py`: new `overlap_violating_point_witness` (pure,
   directed interval arithmetic, endpoint errors enclosed); docstring
   correction in `_overlap_dual_joint_weight_lower` (batched zero-weight
   subtraction is slightly more conservative than the scalar skip, not
   "exactly" mirrored).
- `s3_patch_static.py`: witness wiring at the two sites above; no reported
   bound, default behavior or admission semantics changed.
- `semismooth_path.py`: opt-in stagnation bail parameters (default None =
   unchanged), declared reason and diagnostics; no algorithm switch inside a
   running increment.
- `static_path.py`: opt-in `continuation_cutback` keyword (default None =
   unchanged), acceptance-block extraction reused per substep, declared
   substep records, full restore on rejection, cutback-exhaustion failure path.
- New tests: witness math (rational/geometry controls, refusal-only soundness,
   no-admission property), wiring decision-preservation (mock counts: skipped
   matching calls on witness hits), stagnation bail, cutback substep
  chronology/restore/restart-record shape, cancellation during substeps.

## Proposed contract deltas (parent adoption required; not implemented publicly)

1. New public opt-in setting(s) for the continuation cutback (name/default in
   `ContactSolverSettings` or a `solve_static_contact_path` keyword): default
   off; fixture opt-in is a parent decision.
2. Restart schema: unchanged keys; history records gain an optional additive
   `continuation` block. If the parent prefers a first-class schema field
   (e.g. `path_state["continuation"]`), that is a schema adoption decision; the
   implemented private candidate keeps the schema byte-compatible.
3. Claim-bearing fixture chronology: with cutback opted in, accepted steps may
   carry declared substeps; acceptance criteria and macro waypoints unchanged.

## Status / remaining work / blockers

- [done 2026-10-10 v2] Witness REPAIRED per parent findings: (1) new
  `_divide_positive` directed interval division consumes all four endpoint
  combinations, fixing the inverted negative-numerator radius/barycentric
  endpoints (N=-1, D in [1,2] now gives [-1,-0.5]) and the invalid
  N_upper/norm_lower "upper bound"; (2) the witness quantity is now the
  physical source-normal gap g = r*(P.Ns)/|Ns| with the actual parametric
  Q4 normal Ns = dX/du x dX/dv enclosed at the exact sample point
  (positive norm and P.Ns chart required), plus certified target-foot
  barycentrics — the target-plane height N/|T| is no longer the criterion;
  (3) arbitrary supplied sample weights/times are enclosed (rounded
  factors get outward intervals; dyadic defaults stay exact-width);
  endpoint-error boxes flow through every operation; no strict enclosure
  at a sample skips that sample (complete conservative path retained);
  malformed inputs still raise. Diagnostics key renamed to
  `physical_gap_upper_m`.
- [done 2026-10-10 v5] Adopted public delta implemented and source-checked:
  `ContactSolverSettings.path_continuation_maximum_halvings:int=0`
  (0..12), `path_stagnation_patience:int=2`,
  `path_stagnation_fraction:float=.125`,
  `path_stagnation_merit_rate:float=.05`; default off omits all four from
  canonical settings contracts and request identity; enabled binds all four
  plus revision `declared_macro_path_physical_substeps_v1` into the
  contact_path analysis/restart contract and request identity; enabled
  continuation is refused on non-contact_path calls in real public
  validation before mutation. Stagnation bail in `solve_increment` (reason
  `contact_semismooth_stagnation`); bounded dyadic-tau physical substeps in
  `static_path.py` with full commit/rollback, per-substep complete
  admission gates, history `continuation` block, restart chronology
  validation. No production source file was changed in v5; every v5 repair
  was a test control defect.

## v7 early checkpoint (turn ~11): weak-versus-physical gap discriminator RESOLVED

The v7 delta's first discriminating question — is the coarse caller fixture
trying to activate weak nodal pressure at/beyond its strong 50um gap limit? —
is answered YES by an independent exact-rational computation (no
production-kernel self-oracle; conventions read from the element source only:

- `e4_pl_s3_v2d_element.py`: material mid = reference − offset·director,
  skins at mid ± (t/2)·director; `core.py`/`overlap.py`: side "bottom" →
  normalized thickness coordinate −1, "top" → +1.
- `core.py:1375` / `moving.py:608`: normalized (weak) nodal gap =
  weighted_gap/support = ∫phi·g dA / ∫phi dA; pressure activation when it
  crosses 0.

Actual caller-fixture geometry (exact fractions): source reference plane at
normal-height 0.04004 (the fixture premultiplies by 1/n_z, so the
normal-direction height is exactly 0.04004), source bottom skin − 0.025
(thickness 0.05), target top skin = −0.010 (offset) + 0.025 = +0.015, so
g0 = 0.04004 − 0.025 − 0.015 = 1/25000 m = 40um exactly, uniform over the
patch (both planes share the 1e-4 slope). Independent scalar polynomial
integral of the single interior node's bilinear tent on the 2x2 patch (four
0.5x0.5 elements, corner-hat ∫ = 1/4, ∫hat² = 1/9 per unit element):
∫phi dA = 1/4 m², ∫phi² dA = 1/9 m², ratio = 4/9 exactly (cross-checked by
an independent float midpoint quadrature: 0.44444). Therefore for the
independently guided rigid-target model with tent displacement w:
gbar = g0 + (4/9)w; weak onset at w* = −9g0/4 = −90um, at which the center
physical gap = g0 + w* = −50um = exactly −gap_tolerance (5e-5). The
certificate's admissible domain (enclosed gap ≥ −50um everywhere) forces
w ≥ −90um, so weak onset sits exactly at the admissible boundary: strictly
inside the admissible domain gbar > 0 always — weak nodal pressure can never
activate. This is a HYPOTHESIS-CONFIRMED discriminator for the actual
rotating/deformable fixture (the deformable two-S3 target can only shift the
onset, not the coincidence of the 40um geometry with the 50um strong limit),
not a proof the coupled solution is impossible, and not a source defect: it
separates the fixture's weak-onset/strong-limit coincidence (obstruction
cause) from true point-gap refusal (the witness/certificate mechanics,
unchanged) and from expensive repeated evaluation (cost, unchanged).

Choice (per delta instruction, NOT an accepted engineering response): declare
a near-contact caller fixture g0 = 20um — source reference height 0.04002
with the same skins/target — so weak onset sits at w = −45um with center
physical gap −25um, safely inside the unchanged 50um budget. Only the
UNIT/CALLER fixture changes (the owned small-patch test module); material,
load, physical work/state/gates, actual active contact and all required
checks unchanged; no full-300-coordinate/eight-macro/qualification input,
equation, registered gap budget or scientific criterion is touched.

Intended connected source repair (review disposition, source-scoped): tighten
`_validate_continuation_history_record` in `static_path.py` to fail closed on
producer-reachable chronology/settings/counts/finite nonnegative diagnostics:
recorded `maximum_halvings` must equal the enabled settings value; interior
substep spans must be exact dyadic unit fractions 2^-k (1 ≤ k ≤ M) — not
arbitrary integer multiples of the old 2^-(M+1) grid, which admitted spans
below the producer's 2^-M minimum; the final span must be a positive multiple
of 2^-M at most 0.5; per-substep iterations/candidate_evaluations/backtracks
must be nonnegative ints, norms finite nonnegative, work finite;
halvings_used in [1, M], trial_count within the producer's recorded budget
2^(M+1)+2M+2, accepted_substep_count == len(substeps), stagnation settings
valid. Focused cheap pure-reader tamper cases in a new owned module;
compatible actual checkpoints still pass. No physical acceptance/state
change; the unused target_norm degeneracy refusal guard stays.

## v6 driver-checks-v2 execution record (fresh DEV240_V2 scope, 5 attempts, 240 s limit, 40 s reserve)

Early checkpoint (turn 12). Fixture/caller choice: the six v5-authored driver
checks are delivered in the new owned module
`tests/test_general_contact_admission_globalization_driver_small_patch.py`
on the smallest physical 2x2 Q4 patch of the interior-press family
(source_columns=source_rows=2, one interior load node carrying the full
bounded 0.04 N press ramp 0 -> -0.02 -> -0.04 N, perimeter uz support,
lateral uy guide, family two-S3 nonmatching target, monolithic active-set
enforcement with the D1 interior profile, overlap_local_dev certificate,
continuation halvings=6). The family build_case column gate does not admit
two columns, so the fixture is replicated mechanic-for-mechanic inside the
owned test module; no scripts/ file was edited. The module adds the
delta-required explicit fixture check (declared load values, active pressure
DOFs, positive numerical pressure, gap within the 5e-5 family tolerance,
interior-node deflection) and asserts real active contact on the cutback
trajectory and on every transaction rerun. Checks are ordered cheapest-first
so a cap kill still banks completed cases; full/half references are shared
immutable module caches; one declared injected first-refusal reaches real
substeps.

- attempt-01 driver-small-patch-attempt1 (60.07 s, TIMEOUT, peak 222.58 MiB):
  all 7 cases collected; the first case (fixture-explicit half solve, ONE
  macro step) did not complete inside the 60 s job cap. No case result.
- attempt-02 driver-small-patch-phase-probe-attempt2 (60.06 s, TIMEOUT,
  peak 221.44 MiB): faulthandler stack dumps (20 s/40 s) inside the first
  real solve. Both dumps sit inside a CONTINUATION SUBSTEP attempt
  (static_path.py:1311 -> attempt_semismooth -> solve_increment): at 20 s
  in structural assembly (nonlinear_static.py:1415), at 40 s inside the
  jet2 Q4-S3 overlap derivative integration
  (q4_s3_overlap_derivatives.py:911 -> integrate -> rule_many ->
  _rule_batched -> _bnatural/_bmap/_bsum -> __mul__, line 169) under
  NUMBA_DISABLE_JIT=1. So on the 1e-2-slope 2x2 fixture the macro
  attempt genuinely refuses and the driver genuinely cuts back before
  the cap; the pure-Python derivative integration is the hot spot. No
  per-solve timing was invented from the timeout.
- attempt-03 driver-small-patch-flat-attempt3 (60.04 s, TIMEOUT, peak
  223.18 MiB): fixture switched to the family's flat 1e-4 reference
  slope (the recorded family tractability run
  d1_actual_cutback_single_press_20260929 used exactly this value; no
  gate disabled). The incremental phase log measures the real half-solve
  trajectory: macro attempt REFUSED with reason
  contact_semismooth_stagnation after 4 iterations / 14.24 s; then real
  adaptive dyadic substeps: trial tau 0->0.5 refused (7 iterations /
  11.28 s), halving; tau 0->0.25 COMMITTED (3 iterations / 2.00 s); tau
  0.25->1.0 refused (5 iterations / 14.66 s); halving; tau 0.25->0.5
  refused (5 iterations / 7.37 s); halving; tau 0.25->0.375 COMMITTED
  (3 iterations / 2.09 s); killed mid-substep at the 60 s cap. Fraction
  searches cost 0.29-3.80 s each (317 matching_projection_swept_lower
  calls in the window); the v5 witness wiring is active on this fixture
  (overlap_violating_point_witness called inside pair_gap_admissible,
  s3_patch_static.py:1465). One half solve therefore measures roughly
  80-110 s of real work — above the 60 s per-job cap — and the stagnation
  is intrinsic to the mandated coarse 2x2 patch (both the 1e-2 and 1e-4
  slopes stagnate), because the swept certificate over 0.5 m source
  boxes caps the Newton fraction until the merit plateaus. No case
  completed.
- attempt-04 driver-small-patch-partial-attempt4 (7.67 s, PASS, peak
  201.07 MiB): the two propagation halves that fit the remaining
  allowance both PASSED on the flat 2x2 fixture —
  test_cancellation_during_substeps_propagates_partial (0.374 s: declared
  injected first-refusal reaches the real cutback, a cancellation token
  at contact_path.step:1.continuation:1 propagates SolveCancelled, and
  the refused macro attempt publishes no substep Newton work, calls==1)
  and test_cancellation_inside_first_macro_attempt_propagates_partial
  (0.318 s: a token at contact_path.step:1.semismooth.iteration:1
  propagates through the macro attempt). These are PARTIAL checks: the
  restore-vs-pristine-reference halves could not execute.

Ledger final state: 187.84 s of 240 s used, 4 of 5 attempts, 12.16 s
executable remaining (nothing fits; not spent), 40 s reserve intact,
peak memory 223.18 MiB < 953 MiB. Scope stays OPEN with one attempt
slot; no old-scope balance was reused.

## v6 final handoff (truthful)

Changed files this session (all test-owned plus this note; NO product
source file was edited, no defect was found, no repair was made):
- tests/test_general_contact_admission_globalization_driver_small_patch.py
  (new): the 2x2 fixture builder (family interior-press mechanics
  replicated at source_columns=source_rows=2 with the flat 1e-4 slope;
  the family build_case column gate does not admit two columns, so no
  scripts/ file was touched), the explicit fixture check, and the six
  authored driver checks ported to this fixture with added real
  active-contact assertions on the cutback trajectory and on every
  transaction rerun; shared immutable full/half reference caches; one
  declared injected first-refusal; autouse call-through phase logger
  (changes no production behavior).
- tests/test_general_contact_admission_globalization_driver_small_patch_probe.py
  (new): the attempt-02 phase probe (faulthandler dumps plus timing
  wrappers).
- tests/test_general_contact_admission_globalization_driver_small_patch_partial.py
  (new): the two partial propagation checks that passed in attempt-04.
- docs/GENERAL_CONTACT_ADMISSION_GLOBALIZATION_MISTRAL_WORK_20261010.md
  (this note).

Exact checks actually completed and PASSED under the fresh
driver-checks-v2 guard: 2 partial propagation checks (attempt-04,
named above). Zero of the six authored driver checks completed:
test_cutback_chronology_force_ramp_and_gates,
test_report_boundary_exception_restores_complete_macro_snapshot,
test_post_commit_boundary_exception_restores_complete_macro_snapshot,
test_cancellation_inside_first_macro_attempt_restores_and_propagates,
test_cancellation_during_substeps_restores_and_propagates,
test_restart_rejects_tampered_and_incompatible_continuation_history
(all six remain authored in the small-patch module, unexecuted to
completion). The explicit fixture check itself also did not complete
(one half solve exceeds the 60 s job cap), so the small fixture's
active-contact state is evidenced only by the family's recorded runs,
not by a guarded assertion in this scope.

Specific blocked branch (measured, not inferred from a timeout alone):
under the guard-mandated NUMBA_DISABLE_JIT=1 serial environment, one
real 2x2 half solve costs roughly 80-110 s (attempt-03 phase log),
dominated by the pure-Python jet2 Q4-S3 overlap derivative integration
and the matching_projection_swept_lower adaptive cascades; the mandated
smallest 2x2 patch makes the swept certificate conservative enough that
the macro attempt genuinely stagnates into the continuation cutback
(positive real-evidence observation: stagnation reason, cutback, dyadic
halvings and committed substeps all behaved as designed on real
physics). Every one of the six checks needs 2-5 such solves inside a
60 s job; the allowance (200 s executable, 60 s/job, 5 attempts) is
short by roughly an order of magnitude. No source defect is claimed and
none was excluded by the timeouts.

Source review impact: no production source file changed in v6, so the
separate Mistral Read reviewer (session 52193) has no new source delta
to reconcile from this session; the v5 reviewed identity stands. The
real-physics observations above (stagnation/cutback/substep chronology,
witness wiring active) are caller-level evidence only, not source
verification. Engineering acceptance/release remain FALSE; parent
inspects the guard evidence before any adoption decision.

## v5 execution record (all numbers from the guard ledger/raw evidence)

Scope D1_ADMISSION_GLOBALIZATION_SOURCE_DEV180_V1, 6/6 attempts used,
131.9048653 s of 180 s used, 30 s reserve intact, peak 247.19 MiB < 953.
Evidence root: C:/ANYworkspaceWork/contact_mistral_admission_globalization_20261010/source-checks-v1/

- attempt-01 (prior session, preserved unchanged): 16 witness math checks
  passed; test_point_gap_budget_witness_skips_matching_without_admitting
  failed on the spy's adaptive_depth=1 < production depth 3.
- attempt-02 admission-globalization-remaining-attempt2 (13.03 s, NONPASS):
  new owned module with the 9 remaining caller/public checks plus the
  adversarial physical-normal case. 8 passed: contact_path_selection,
  dead_load_request_refuses, point_gap_budget (with the v5 spy fix),
  real_public_validation_refuses[force], [displacement], [arc_length],
  request_identity_default_shape_and_enabled_revision,
  settings_contract_omits_default_and_binds_enabled.
  test_swept_certify_witness_skips_matching failed: the spy's
  node_budget=1 is invalid for the diagnostic refinement-mode matching
  call (gap_budget None) made by the swept subdivision branch through
  _gap_lower, whose validation requires node_budget >= (4**4-1)//3 = 85.
  The -x stop left the adversarial case unexecuted in this attempt.
- attempt-03 admission-globalization-swept-repair-attempt3 (45.07 s,
  TIMEOUT): point_gap passed; leaving the refinement-mode call at the
  production 1024-node cap cannot fit the 45 s job on the grossly
  violating subdivision middle pose (the recorded cost driver).
- attempt-04 admission-globalization-swept-repair-attempt4 (12.84 s, PASS):
  final spy caps both production call shapes with their minimum valid
  budgets — admission shape (explicit gap_budget) adaptive_depth=3,
  node_budget=1, counted (the witness wiring target); refinement shape
  (gap_budget None) adaptive_depth=3, node_budget=85, uncounted (existing
  subdivision refusal mechanics). Both spy-using checks passed
  (point_gap 0.47 s, swept_certify 5.42 s). Production caps/mechanics/gates
  unchanged; the 16 passed math checks and 8 passed caller/public checks
  were not rerun.
- attempt-05 admission-globalization-final-checks-attempt5 (45.08 s,
  TIMEOUT): adversarial physical-normal case PASSED (0.0023 s) — source
  A=(0,0,-.1),B=(1,0,-.1),C=(1,1,.9),D=(0,1,-.1) against triangle
  (0,0,0),(1,0,0),(0,1,0) at u=v=.25: target-plane height -.0375 violates
  tolerance .036 but the physical source-normal gap -sqrt(1/800) ≈
  -.0353553 does not, so the witness correctly returns False at .036 and
  True at .035 with physical_gap_upper_m = -sqrt(1/800) (independent
  rational/squared derivation, production kernel never used as oracle).
  The first real-solve driver check then hit the 45 s cap: with JIT
  disabled each small-fixture solve costs roughly 12-15 s, so no
  multi-solve driver check fits one 45 s job.
- attempt-06 admission-globalization-stagnation-check-attempt6 (7.86 s,
  PASS): test_stagnation_controls_are_validated_before_any_work passed
  (0.41 s) — the only driver check needing no solve.

Verified totals on the immutable source snapshot (not installed
artifacts): 16/16 witness math (attempt 1), 9/9 remaining caller/public
(8 in attempt 2 + swept in attempt 4), 1/1 adversarial physical-normal
(attempt 5), 1/7 driver checks (stagnation validation, attempt 6).

Driver checks NOT executed (authored, unverified, no defect evidence):
test_cutback_chronology_force_ramp_and_gates,
test_report_boundary_exception_restores_complete_macro_snapshot,
test_post_commit_boundary_exception_restores_complete_macro_snapshot,
test_cancellation_inside_first_macro_attempt_restores_and_propagates,
test_cancellation_during_substeps_restores_and_propagates,
test_restart_rejects_tampered_and_incompatible_continuation_history.
Each needs multiple real solves (~12-15 s each with JIT disabled) and a
fresh allowance; the v5 scope's 6 attempts and 180 s are exhausted.

Changed files this session (all test-owned; no product source edited):
tests/test_general_contact_admission_globalization_witness_public.py
(_capped_matching spy repair), tests/test_general_contact_admission_globalization_remaining.py,
tests/test_general_contact_admission_globalization_swept_repair.py,
tests/test_general_contact_admission_globalization_final_checks.py,
tests/test_general_contact_admission_globalization_stagnation_check.py
(new owned selection modules), this note. py_compile was used for syntax
checks only; it is not a numerical gate pass.

Final label (v6): partial — the fresh driver-checks-v2 allowance delivered
two PASSED partial propagation checks and measured phase/stack evidence of
the blocked branch (one real 2x2 half solve ~80-110 s under
NUMBA_DISABLE_JIT=1 vs the 60 s job cap; six authored checks each need
2-5 such solves), plus real caller-level observation that the stagnation
bail, cutback, dyadic substep chronology and witness wiring all engage
as designed on the mandated smallest physical fixture. The six authored
driver checks remain unexecuted to completion; no product defect was
found and no production source was changed. Parent inspects evidence
before any engineering acceptance; separate Mistral Read review
reconciles the unchanged v5 source identity; no independent/engineering/
release claim from author verification.
- Open uncertainty (unchanged): whether substep Newton at half-span
  achieves acceptance within budget; witness hit rate on the recorded
  step-2 refusals. The wiring is decision-preserving so a zero hit rate is
  a pure no-op.

## v9 execution record (mechanics-unblock-v3 final: 5/5 attempts, 143.6588709 s of 240 s, 40 s reserve intact)

Correction of prior unsupported claims (required by the v9 delta): the
"roughly 80-110 s of real work" figure for one real 2x2 half solve in
the v6 record above is an EXTRAPOLATION from the attempt-03 phase log of
a job killed at the 60 s cap. No solve ever completed and no physical
commit was ever observed at that or any other duration in this scope;
the figure is not a completion or commit measurement and must not be
cited as one. The only completed numerical evidence in this scope is
the guarded receipts listed here and in the earlier records.

Order of work (per delta): reviewer findings first, then connected
repair, then guard. Findings (MISTRAL_INDEPENDENT_REVIEW_V3.md, read
before any edit): the per-span repair was confirmed correct against the
producer, but the reader still accepted producer-unreachable
chronologies — (1) no inter-span growth bound (a 2^-6 accepted span
followed by a 0.5 accepted span passed; the producer doubles at most
once per acceptance), (2) the halvings identity
halvings_used = 1 + trial_count - accepted_substep_count was unchecked,
(3) halvings_used was not required to be consistent with the spans a
producer can emit, (4) external_nodal_work_trapezoid_j presence did not
agree with program.nodal_forces, (5) stagnation controls were
range-checked only, not bound to the live settings. The suite's own
"deepest producer span ... growth step back to 0.5" positive case had
exactly the unreachable shape of counterexample 1.

Connected repair (src/anysolver/general_contact/static_path.py,
_validate_continuation_history_record plus its single restart call
site; internal signature changed from (record, program,
maximum_halvings) to (record, program, settings); public API,
default-off shape and restart physical law unchanged):

- The validator now simulates the producer's span state machine: the
  nominal span starts at 0.5, halves on failure and doubles capped at
  0.5 on acceptance. An accepted interior span must equal the live
  nominal span, so it can be reached from the previous accepted span
  only through halvings — never by more than the one doubling per
  acceptance. This rejects the 2^-6 -> 0.5 jump and every >2x growth,
  including growth into the final span.
- Accounting identity enforced:
  halvings_used == 1 + trial_count - accepted_substep_count.
- The failures implied by the accepted spans must fit the recorded
  halvings_used, and at the final truncated interval the remaining
  recorded halvings must fit the nominal span at the final acceptance.
  Producer-permitted repeated failures on the same final interval are
  explicitly admitted (new positive test); a halvings_used no span
  sequence can produce is rejected.
- external_nodal_work_trapezoid_j must be present and finite (any
  sign) exactly when the program declares nodal forces.
- Recorded stagnation_patience/fraction/merit_rate must equal the live
  settings at the validator caller, and the live maximum_halvings is
  read from the same settings object (fail-closed on both).
- Every refusal fires in the restart reader before any Newton work or
  mutation; disabled runs (maximum_halvings == 0) still never run the
  check.

Test repair (tests/test_general_contact_admission_globalization_
restart_reader.py, same owned module): the false positive trace
(2^-6 -> 0.5 growth) was replaced by the producer-reachable dyadic
ladder 2^-6 .. 2^-1 with a 2^-6 final span. The deepest span cannot
repeat at the budget limit (a further failure at halvings == M would
exhaust the budget); my first repaired fixture repeated it and the
guard correctly failed it in attempt-04 before the fix. The
non-power-of-two final-span positive was rebuilt as the reachable
0.25 / 0.125 / 0.25 -> 0.375 tail; the M=12 positive was rebuilt as the
full 13-substep ladder (eleven failures, halvings_used = 12). New
adversarial checks: growth beyond producer doubling (the reviewer's
exact counterexample), halvings identity mismatch, halvings inconsistent
with spans (both directions), work-key/program mismatch (both
directions plus signed-finite positive), stagnation settings mismatch,
and a repeated-final-interval-failure positive. Prior guarded passes
remain source-bound evidence for their snapshot, not universal
correctness.

Guarded evidence (exact existing mechanics-unblock-v3 guard only;
serial, NUMBA_DISABLE_JIT=1, immutable source snapshot, no installed
artifact, no manual test loop, no coupled solve, no audit):

- attempt-04 v9-restart-reader-repair-attempt4 (7.0443018 s, NONPASS,
  peak 202.39 MiB, exit 1, inputs unchanged): 17 cases collected; the
  first positive case failed on my own unreachable fixture (two
  consecutive 2^-6 spans at M=6); -x stopped the run. Evidence:
  C:/ANYworkspaceWork/contact_mistral_admission_globalization_20261010/
  mechanics-unblock-v3/attempt-04-v9-restart-reader-repair-attempt4
- attempt-05 v9-restart-reader-repair-attempt5 (6.8014224 s, PASS,
  peak 196.81 MiB, exit 0, inputs unchanged): all 17 collected cases
  passed (junit counts tests=17 failures=0 errors=0 skipped=0):
  test_reader_accepts_producer_reachable_chronology,
  test_reader_accepts_repeated_final_interval_failure,
  test_reader_accepts_non_power_of_two_final_span,
  test_reader_rejects_span_below_producer_minimum,
  test_reader_rejects_non_dyadic_unit_interior_span,
  test_reader_rejects_oversized_final_span,
  test_reader_rejects_interior_span_growth_beyond_producer_doubling,
  test_reader_rejects_halvings_identity_mismatch,
  test_reader_rejects_halvings_inconsistent_with_spans,
  test_reader_rejects_work_key_program_mismatch,
  test_reader_rejects_stagnation_settings_mismatch,
  test_reader_rejects_negative_and_nonfinite_diagnostics,
  test_reader_rejects_incompatible_recorded_halvings_budget,
  test_reader_rejects_out_of_budget_accounting,
  test_reader_rejects_invalid_cutback_reason_and_endpoint,
  test_reader_accepts_minimum_budget_chronology,
  test_reader_ignores_absent_continuation_block. Evidence:
  C:/ANYworkspaceWork/contact_mistral_admission_globalization_20261010/
  mechanics-unblock-v3/attempt-05-v9-restart-reader-repair-attempt5

Ledger final state: 143.6588709 s of 240 s used, 5 of 5 attempts,
40 s reserve intact, peak memory 196.81-202.39 MiB < 953 MiB. Scope
OPEN with zero attempt slots left; no renewal is claimed.

Changed files this session: src/anysolver/general_contact/static_path.py
(validator and its restart call site only),
tests/test_general_contact_admission_globalization_restart_reader.py,
and this note. No other product file, no DELTA/brief/lead doc, no Git
operation, no scripts/ or config file was touched.

Remaining physical gaps (unchanged by this repair): the coupled 2x2
driver solves, the six authored driver checks, the real-checkpoint
restart compatibility and the joint-dual prefix branch remain
unexecuted to completion (no allowance left in this scope); the
80-110 s extrapolation above remains unverified by any receipt.
Engineering acceptance/release remain FALSE; the attempt-05 PASS is a
pure-reader source-bound check on the immutable snapshot, not a
coupled physics qualification.

## D1 initial-contact seed — early checkpoint (tool-call 15, 2026-10-10)

Operator/ownership choice (concrete, before coding):

- Operator: ONE factorization of the control-constrained structural map
  [[K_c, -C],[rows, 0]] (K_c = T.T K_struct T at the committed origin,
  C = control reaction columns, rows = control rows). Free response and each
  pressure right-hand side reuse that single factorization. Equilibrated gap
  response H = G K_c^{-1} G.T (m x m, m = supported pressure modes), g_free =
  normalized gap at the free constrained response. Seed pressures solve
  min 0.5 z^T H z + g_free^T z s.t. z >= 0 via a bounded primal active-set
  route (working set on the zero face, exact stationary solves on the free
  face, first-blocking-clamp line search; iteration cap 4m+16, explicit
  refusal on cap). Symmetry/positivity of the reference work map is checked
  explicitly (symmetrized H eigenvalues); singular/indefinite/ill-conditioned
  (explicit condition cap) refuses the seed. No diagonal/stiffness/regularization.
- Signs/dimensions derived from the live residual convention in
  semismooth_path.solve_increment (R = reduced_external + C mu - T.T(internal
  + contact.force); Newton row kqq dq - C dmu + kqz dz = R with kqz = -(G T).T),
  so the QP is assembled from the same G/gap objects the Newton path uses.
- Ownership: new src/anysolver/general_contact/initial_contact_seed.py owns
  proposal+refusal records and the bounded QP; core.py owns the
  default-none `initial_contact_seed` selector, its D1-route validation and
  the legacy contract omission of "none"; request_identity.py binds
  `contact_initial_seed_revision` only when enabled; static_path.py owns
  cold-start eligibility (fresh solve, step 1, semismooth D1 overlap-local
  frictionless reference-linear route, stress-free zero origin) and wiring;
  semismooth_path.py owns seed admission before iteration 1 (actual-mechanics
  reevaluation from the committed origin, full scaled merit comparison,
  conservative swept/path admissibility, nonnegative supported forces,
  finite check; refusal keeps the untouched origin).
- First intended edit: core.py — add `initial_contact_seed: str = "none"`
  field to ContactSolverSettings with validation mirroring the path
  continuation D1 route gate, and omit "none" in _contact_settings_contract.

This is an early checkpoint, not approval. Reading stops at fixture level.

## D1 initial-contact seed — final connected handoff (2026-10-10, continuation of terminal exec45446)

Same ownership as the early checkpoint above: initial_contact_seed.py,
core/request_identity/semismooth_path/static_path wiring, the owned
initial-seed tests/example and this note. Prior terminal session's
working source/tests/example and all failed evidence are preserved
unchanged; this section completes its milestone, it is not another audit.

### Deliverable 1 — REAL seed-admission capture (attempt-08, PASS 15.1542703 s, peak 208.88 MiB)

One bounded real capture on the unchanged coupled 2x2 / joint-overlap-
dual-True / 20um / 0.04 N / 50um fixture, using the captured current
operator (no fresh geometry, no sweep). A private compatible diagnostics
hook (`semismooth_path._INITIAL_SEED_DECISION_HOOK`, None in production,
no acceptance/transaction gate changed) receives the production decision
payload after the unchanged admission predicates ran and raises
SolveCancelled through the proven-propagating channel, so the solve
stops before any Newton iteration with the origin untouched.

Production's unchanged decision: **REFUSED**, reason
`seed_not_swept_admissible`, actual swept-certificate admissible
fraction **0.25** (the seed is all-or-nothing: fraction != 1.0 refuses).

Exact captured evidence (attempt-08 temp
`initial-seed-admission-capture-v1.json`, source-bound by the attempt's
install.json payload SHA256, settings contract and program binding):

- Origin: q = 0 (49 reduced coordinates), control reactions 0, z = 0;
  origin scaled merit 0.5 (residual norm 0.02 N over the 0.04 N scale);
  all 9 normalized gaps 20um (the declared g0).
- Proposal (production `propose_linearized_kkt_seed`, revision
  origin_linearized_kkt_nonnegative_pressure_v1): QP optimal in 1
  iteration, single active pressure mode z = 6.194576195748144e-4 N,
  pressure force 0.0006194576195748144 N, H eigenvalues
  [7.910455691915304e-17, 1.3312770852064464] m/N, linearized free-gap
  minimum -86.4820234727039um, cost 0.0012832 s.
- Candidate re-evaluated through the actual mechanics (tangent=False):
  scaled merit 0.006010285576782569 (vs origin 0.5 — an 83x improvement,
  so the merit gate would have passed), residual norm 2.404114230713028e-4
  N, constraint max 4.931527882576436e-24 (satisfied), NCP sum
  1.4556915387288326e-06 N (scaled 3.6392288468220814e-05), candidate
  normalized gaps from -5.822766125801499e-10 m to 1.3445543218863456e-4
  m (no sampled gap is treated as safety proof; the swept fraction and
  the production decision are the proof channel).
- Proposed pose: displacement norm 0.0018902233600173002 m, control
  reactions (1.7072660873502528e-07, -1.0878084708734556e-07).

Concrete obstruction (physically refused, so no "why completion fails"
claim is needed): the origin-linearized KKT proposal is a single full
step of 1.89 mm displacement whose straight origin-to-proposal segment
leaves the swept certificate's admissible domain at 25% of the step —
a certificate-budget obstruction, not a QP, merit, force or constraint
obstruction (all of those passed). The seed's conservative all-or-nothing
admission gate then refuses and leaves the origin untouched, after which
the solve is exactly the default-none run that already diverged
(attempt-05, 174.4023164 s) or timed out (attempt-06, 180.0397 s cap).
The single next necessary observation for the physical milestone is
therefore the first Newton iteration's own line-search acceptance from
this same refused origin (does the unchanged path admit any
certificate-limited fraction toward the same pressure mode?); it is a
bounded capture of the same kind as attempt-08 and is NOT executed here.

### Deliverable 2 — F2 eligibility closed; no counterexample exists

Both halves of the review's F2 are unreachable with the enabled seed,
now with one focused guarded test module as empirical discrimination:

- Friction half: every friction route requires jet2_s3_dev or
  nested_augmented or physical_sides_dev, each conflicting with the
  seed-pinned settings (jet2_q4_s3_dev, monolithic_active_set, legacy).
  Repair (fail closed, mirroring the core.py driver refusal pattern):
  `static_path.solve_static_contact_path` now refuses
  `initial_contact_seed != "none"` with friction explicitly at entry,
  before any route preparation or Newton work — no silent drop can be
  reintroduced by a future friction route.
- Profile half: the Q4/Q4-monolithic profile requires jet2_q4_q4_dev,
  which the enabled seed forbids; a Q4-target definition is refused by
  real validation (D1 interior-profile gate: "D1 interior profile
  requires a refined augmented Q4/S3 fine-Q1 Jet2 general patch"), and
  the fixture's own validating route selects exactly
  REFINED_Q4_S3_OVERLAP_LOCAL_AUGMENTED_PROFILE. No silently skipped
  profile shape validates.

Guarded evidence: attempt-09 initial-seed-eligibility-v1 (7.6092196 s,
NONPASS, preserved: my first assertion expected the overlap-local issue
label, the actual fail-closed label is the D1 interior-profile one;
1 passed, 1 failed, -x stopped the run) and attempt-10
initial-seed-eligibility-v2 (7.1937366 s, PASS, peak 201.77 MiB, all 4
cases: explicit friction refusal, Q4-target validation refusal,
seed-eligible profile selection, truthful example prose). No new
scientific admission and no silent settings fallback were added.

### Deliverable 3 — example/status prose truthful; contract re-bound

The example docstring no longer claims "implemented and locally tested";
it now states the coupled example is UNVERIFIED to completion, that the
default-none reference half diverged and the seeded run reached its
execution cap, that the passing source-bound checks are not installed
testing, and retains the original completion obligations (one completed
coupled solve with the enabled seed, truthful comparison against the
default-none reference). No pytest duration is used as process-wall
evidence. The static example contract was re-bound on the changed
snapshot: attempt-11 initial-seed-example-contract-rebind-v1 (7.1129661 s,
PASS, peak 200.73 MiB).

### Changed files (this continuation)

- src/anysolver/general_contact/semismooth_path.py: private
  `_INITIAL_SEED_DECISION_HOOK` (None in production) and its call site
  after the unchanged seed decision; no predicate or gate changed.
- src/anysolver/general_contact/static_path.py: explicit fail-closed
  refusal of the enabled seed with friction at path entry.
- examples/general_contact_initial_contact_seed_dev.py: truthful
  UNVERIFIED-to-completion prose.
- tests/test_general_contact_initial_seed_admission_capture.py (new),
  tests/test_general_contact_initial_seed_eligibility.py (new): the
  capture and F2/prose checks above.
- This note. No Git operation, no sibling/other docs, no harness,
  evidence, ledger or artifact modification, no worker/config/chat
  messaging.

### Ledger final state and remaining gates

initial-seed-dev600-v1: 429.2218930000381 s of 600 s used, 11 of 12
attempts, 90 s protected reserve intact (80.7781069999619 s executable
remained at close; one attempt slot left). All numbers above are guard
receipts, not pytest durations.

Remaining gates, unchanged and still required:

- Physical: the coupled prefix (one completed solve with the enabled
  seed and the truthful default-none comparison) remains UNVERIFIED;
  diagnostic/test passes do not replace it. The next specific
  implementation action is the bounded first-Newton-iteration
  line-search capture from the refused origin described above.
- F1 (QP ratio test) remains SUSPECTED with no counterexample; per the
  review and the fixture's actual QP-optimal result it was not
  redesigned and no randomized sweep was run.
- Installed testing: no installed end-to-end execution exists; every
  passing check is source-bound to an immutable snapshot.
- Review: the independent review's F4 (physical completion) stays
  unmet; F2 is closed here; F3 diagnostic labels are retained unchanged.

Engineering acceptance/release r

## Integrating-lead reconstruction — terminal owner, 10 October

The author tail above was incomplete. Author8819 wrote the reviewer partial-note
file outside ownership instead of finishing this note; unexpected bytes retained,
original restored from immutable reviewer log. Final independent report unaffected.
See ../contact_mistral_admission_globalization_20261010/INITIAL_SEED_V3_OWNERSHIP_RECONCILIATION.json.
All owned worker/check handles are terminal. DEV600 CLOSED443.8948618s;
DEV45 repaired export PASS17.2018184s, then CLOSED. All unused balances CLOSED.
Last original attempt NONPASS on evidence-export NameError; typo repair verified.
Recorded10witness calls (2endpoint/8path),0enclosed violations; safety and actual
penetration are BOTH unproven. Actual seed still refusedfraction0.25 despite merit
0.5→0.00601028557678257. No accepted physical checkpoint/installed verification.
Next action is independent controlling-gap enclosure on saved literal geometry,
then targeted feasibility or certificate repair; the earlier proposed first-Newton
capture is superseded. FullD1/C0–C9 and all numerical gates remain required.
Handoff state: implemented experimental initializer, focused source/diagnostic
checks completed, coupled physical outcome unverified; not accepted or released.

## Prospective next slice — direct Mistral coordination

Previous turn progressed by correcting active role authority; no GPT-Astra agent
is active or will be assigned work. This chat coordinates Mistral directly.
Question: does the literal seed path violate 50um within represented overlap, or
is the current degree7/node1024 certificate too conservative? Saved point-witness
absence cannot decide this. Mistral owns the independent gap discriminator and
compatible caller repair; genuine violation selects feasibility/globalization,
enclosed safety selects certificate repair, unresolved enclosure returns the exact
region/equation rather than an unchanged complete-solve rerun.
Fresh D1_SEED_GAP_DISCRIMINATOR_DEV420_V1:420s total/60s reserve/max8 serial
attempts/953MiB, focused60s; named changed coupled prefix180s. Standing user
authorization applies; no old closed balance reused. Brief and guarded receipts:
../contact_mistral_seed_gap_delivery_20261010/IMPLEMENTATION_BRIEF_V1.md.
Mistral owns only the specified source/reference/test boundary and its exact
GENERAL_CONTACT_SEED_GAP_MISTRAL_WORK_20261010.md note. All prior evidence,
reviewer files, scientific inputs, gates and unrelated deletions are protected.
