# Private mixed arc prototype — incomplete

Base 93453654; current dirty source is not accepted or installed-verified.
No public API/default/checkpoint change. New physical chord metric uses explicit
fixed reference weights and length, excludes algebraic variables from the norm,
and returns actual spatial gradients. General sparse border retains all mixed
unknowns. Candidate trials use one accepted material predecessor without commit.
No mesh-uniformity, stability, first-limit-point or capacity qualification.

Checks and failures:
- Initial runner used a doubled tests path: collection failed; retained.
- Geometric gradient/unit/frame/ownership and indefinite-border tests passed.
- Same native coupled seed/radius1e-5/20Newton/12backtracks hit Newton limit.
- Instrumented repeat retained the obstruction. Relative-radius merit scaling
  was replaced by (D²-r²)/(2r), locally physical D-r; acceptance unchanged.
- Same native case still failed: equilibrium1.20063, normalized sphere error
  0.0079974 after20iterations,116evaluations/21solves/94rejected trials.
- Actual driver update gradient with nonzero shell charts/anchors and beam
  multiplicative rotations, chart rebase, algebraic exclusion, stale-driver
  and unrepresentable-radius tests:2passed in the final focused check.

Independent read-only review identified stale driver admission and radius-square
under/overflow; both fixed/tested. Typed chord-domain errors permit backtracking
without catching malformed-input ValueError. Reviewer requested actual-chart
and during-trial cancellation tests: actual-chart test passes; during-trial
cancellation remains to add. Broader shared displacement regressions and installed
artifact verification remain pending. Native failing test remains visible.

Next: inspect predictor/branch and corrector against a physically identical
control, retaining accepted predecessor and a failed candidate snapshot. Do not
reduce radius, enlarge budgets or claim acceptance from the simpler tests.
No numerical process remains live. Do not expose or publish this prototype.

Evidence archive SHA256 `31a19ce325c69f6a7566ab96036207dc5cee49d17fd32596ed63cce8ab919b3a`; safe execution fields only, no environment maps.

## Fixed-target and material-branch discriminator

Same original force seed; unchanged radius1e-5 and20/12budgets. Working
branch-event displacement corrector at the arc predictor's identical target
−67.8372387601um converges18iterations/20evaluations, equilibrium1.7051e−10,
constraint1.38e−17. Its physical chord radius is8.1096591e−6. Accepted owner unchanged.
This proves that predictor target is solvable, not that the larger arc target is.

An independently reviewed frozen physical tangent-plane constraint was then
implemented privately. Homogeneous bordered tangent is normalized using physical
translation/spin velocity; all retained coordinates and amplitude scale together.
Actual shell/beam chart and rebase derivative checks pass (3focused checks).
The same native radius still fails backtracking, at displacement−69.6588014541um,
amplitude2.3843326094, equilibrium0.39754, plane error5.86e−11. No accepted commit.

Saved failed-candidate directional tests show:
- At h1e−4 weighted shell derivative discrepancy263.49 versus expected482.16;
  at h1e−5 it falls to1.43e−6. Beam nodal discrepancy is negligible; retained
  differences grow at tiny h, so no full tangent-qualification claim follows.
- One shell point changes the active mask (candidate alpha > accepted alpha)
  between ±1e−4; none change at±1e−5/±1e−6.
- All generalized beam stations stay PLASTIC at0,1e−6,1e−4,1e−2.
- Existing beam-only event predictor proposes0.12585765. Twelve halvings stop
  at3.07e−5. Actual equilibrium merit decreases near1e−6; no extra halvings run.

Evidence localizes this obstruction to a shell active-set transition not covered
by the beam-only event policy. It does not establish a constitutive defect,
instability, or impossibility of another equilibrium. Next choose shell-event
handling or explicitly bounded adaptive continuation with atomic state; do not
keep tuning spherical/plane rows, relax tolerances, or hide failed radius evidence.

Failure-capture initially had a Python name collision (candidate variable/function);
fixed as trial_snapshot and rerun once. Failed logs retained. ArcTrialFailure now
retains the uncommitted candidate and work for diagnosis/caller cutback. No public
API/controller/checkpoint or installed-artifact claim yet; native test still fails.

Archive `branch-discriminator-v1.zip` SHA256 `24f6dee347c52cf63c3d5fd04e3b1c7eb04f4bfe6caaee723b4b755b634a052e`. Includes failure candidate,
fixed-predecessor runners/raw outputs, whitelisted execution metadata and current
candidate source. No environment maps. No jobs remain active.

Independent saved-evidence review: alpha>accepted-alpha is an active-set proxy;
centered differences do not locate the forward crossing. Evidence supports a
nearby shell transition limiting the Newton step, not a proven tangent defect or
sole explanation of every rejected trial. The displacement and arc constraints
are different; nearby solvability does not prove the original arc-radius solve.
Next decision: prefer bounded adaptive arc cutback with unchanged predecessors,
orientation, acceptance and per-attempt limits, recording failed attempts. A
smaller accepted radius must be reported as such, never as passing the original
radius. Add a shell-event estimator only if repeated failures justify the more
invasive constitutive-margin/derivative work. Review ran no solves or edits.
The diagnostic result.json target is the failed coordinate; events.json target
is the predictor target; the numbers above identify both explicitly.

## Bounded private adaptive selection implemented

Requested radius1e−5 remains failed:39evaluations,7solves,32rejected trials,
12event-cell responses. Retrying from the identical accepted predecessor at5e−6
succeeds:18evaluations,17solves,0rejected trials,32event-cell responses.
Limits4cutbacks/5attempts; unchanged20Newton/12backtracks per attempt. Selection
returns both requested and actual radius and all attempt work. This selects ONE
uncommitted step; it does not complete an accumulated path of length1e−5.

Candidate carries owned load/physical-normal arrays and frozen metric. Only typed
Newton/backtrack failures retry. Unclassified failures, cancellation, ownership
and programming errors propagate. Accepted checkpoint is unchanged throughout.
Reviewer found stale-return/cancellation and representation guards; fixed and
counterexample-tested. Review closure is in the archive, not scientific acceptance.

Source15checks passed in48.96s including existing displacement-corrector cases.
Final11affected checks passed22.28s after cancellation/owned-context changes;
unchanged shared-border checks reuse the preceding run. One intervening test
failed because its mutation probe used an already-readonly input; changed the
probe to an owned caller array and retained the failure. No product defect hidden.
Configured600s/1GiB,1thread/JIT off supervisor. No timing speedup or fresh installed
artifact claim; installed validation belongs to the forthcoming public lifecycle
slice. No public arc facade/default/checkpoint change in this patch.

Next: atomic arc publication with dedicated snapshot/controller identity,
orientation/metric/load binding, cancellation and exact restart; then the installed
public workflow. Full capacity/limit-point, mesh/unit envelope and programme gates
remain open. Preserve all original fixed-radius failures.

Archive `adaptive-selection-v1.zip` SHA256 `789a2de3801686a3dee7fd37f7822eb3dcecbbee5fe8953baaf71634aea8a755`.
