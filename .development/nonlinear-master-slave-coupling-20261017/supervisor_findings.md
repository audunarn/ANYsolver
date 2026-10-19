# Astra inspection findings (implementation owner to reconcile)

2026-10-18. This is review feedback within the existing assignment, not a new
numerical allowance. Preserve all prior attempts and accounting.

## Harness inspection

1. `harness.py` currently prepends candidate REPO/src to PYTHONPATH regardless of
   --cwd. Clean-HEAD attribution must prove the actual imported anysolver origin
   belongs to head_wt, not just change cwd. Add an explicit source-root argument
   or equivalent exact import routing; record/verify import origin and effective
   source/test hashes of the selected tree for each attribution run.
2. Preflight TimeoutExpired or any Popen/parse/receipt exception currently reaches
   finally without writing a receipt, updating budget or killing a timed-out
   preflight child. Make accounting and process-tree cleanup unconditional for
   every launched process, preserving partial stdout/stderr on every exception.
   Do not rerun completed checks merely to recreate missing accounting; recover
   existing timing evidence and label any uncertainty. No such exception has
   been observed by Astra at this inspection.
3. Receipt test counts should be parsed from JUnit or explicit named fields;
   regex can omit failures if stdout contains '1 failed, 60 passed'. Verify
   effective JIT/thread settings from successful runtime records, not env alone.
   Hash every new diagnostic/test/oracle input used, not just the initial seven.

## Analytical oracle — reserved scientific decision pending

Independent reviewer is assessing load equivalence. A free-width shell tied to
an eccentric beam along one line is not automatically a uniform cylindrical
composite section, even with correct net tip moment. Proposed explicitly scoped
analytical benchmark: exact cross-width plane-section constraints per shell row
(shared ux,uz,ry; uy,rx,rz zero), with actual rotating eccentric beam coupling.
This is a defined verification model, not a claim that the free-width strip
shares its exact solution. Independent derivation/review must establish validity
before adoption. See supervisor_reference_review.md when available; Astra will
record the adopted decision here. Constituent-resolved end forces and moments
must be derived, including their spatial/generalized conventions.

## Astra scientific adoption — before any analytical FE assessment

I independently checked and adopt the derivation and terminal loads in
supervisor_reference_review.md: positive My bends toward negative z;
zbar=Ab*e/(As+Ab), B=E*(Is+Ib+As*Ab/(As+Ab)*e^2), k=Phi/L,
Rs=1/k-zbar, Rb=Rs+e, Ns=-E*As*zbar*k, Nb=-Ns; centroid moments
E*Is*k and E*Ib*k about +y. Apply constituent forces along the final tangent,
with shell consistent tributary weights; do not add another composite moment.
Use explicit exact plane-section row constraints (common ux,uz,ry; uy,rx,rz zero),
clamp root only, and retain the actual eccentric rotating beam map. This scoped
verification model has an independently justified reference. The free-width
strip remains a separate convergence study. Final-tangent dead loading is
terminal-equivalent; intermediate states are not claimed to be circular arcs.

Before results: independent chord analysis predicts slow nonmatching refinement.
Retain required nx8/16/32 evidence. If analytical errors decrease but the last
refinement criterion is unmet, additional nx64,128,256 are permitted in that
order, only within the existing 3600s allowance and reserve. Apply the unchanged
1% accuracy and 0.25% last-refinement thresholds to the final assessed pair;
report every level including any failed planned nx32 criterion. This prospective
resolution extension changes no physics, loading or tolerance and makes no
claim that nx32 is adequate. Stop if errors do not decrease or resources do
not permit the next case; preserve the unmet gate. No external FE or retired
programme execution is authorized.

The first worker checkpoint was inspected: identities match, runtime is Python
3.13.9/numpy2.4.3/scipy1.16.3, baseline22+39 passed with both BLAS pools at1thread.

## Independent inspection of first plastic result

ep-attrib-cr-plastic-6k returned stopped_at_limit (legacy converged=True),
lambda=0.9423014322916665, minimum_load_increment_reached, 9 cutbacks.
Independent relative residual=3.2161147722756904e-9 at achieved lambda and
0.05769856722306025 at requested lambda1; all three immutability checks true.
Its 12 accepted snapshots agree with the reported last accepted residual.
This case supports partial-load interpretation, not a state/reporting defect.
The ep_attribution.py introduction/decision-rule prose still incorrectly says
lambda<1 is a solver/reporting bug; correct that prose to the adopted decision.
The first combined CR batch timed out120.2373367s with no case output; preserve
it and its full budget charge. Subsequent per-case output is retained separately.

## Astra adoption of non-author source findings

supervisor_code_review.md R1–R5 are accepted as actionable source defects and
part of the authorized connected route repair. The owner should implement the
specified focused regression cases, preserving baseline behavior outside the
rotating-map path. All helper changes for R2 are inside nonlinear_static.py.

R1: adopt fail-closed refusal for unsupported downstream dependencies on rotating
slave translations; full nonlinear constraint graph composition is outside this
slice. Inspect normalized compiler equations, not just coupling descriptors.
Keep ordinary linear chains and upstream shell row ties supported.

R4: exact rotating-map route requires work-conjugate internal force. Auto must
select it even with follower loads, retaining external load derivative terms.
Explicit legacy rotated/consistent requests on this new route should be refused
before constitutive activation with an informative ValueError, rather than
silently solving a different internal force law. Legacy models without an active
rotating descriptor retain their current explicit-mode semantics. This is an
intentional admission boundary for the new route, not a change to converged.

R2/R3/R5: thread the existing map consistently through initial-field equilibration,
mapped accepted-state commit/failure recovery, n_red==0 return, and finite restart
DC row/load admission. Retain transaction, cancellation and caller-state guards.
For DC admission use full_u(q), not full_u(zeros), at the actual initial state.

The retained weighted rotation-vector map has a noncommuting 3D superposition
limitation. Preserve the adopted formula; document the actual demonstrated scope
(planar finite rotations and tested states), not arbitrary nonuniform 3D objectivity.

## EP diagnostic review

At initial inspection ep_edge_coupling.independent_residual fixes lam=1 and
dc_summary calls it without res.load_factor. DC must reconstruct at its achieved
unknown load factor and normalize consistently, not treat the proportional load
vector as the actual external load. Include explicit force/wrench balance and
deep state immutability in final assertions, not just output dictionary fields.
Full diagnostic output is evidence; acceptance requires automated assertions.
Original-grid node identities are known from the fixture's construction; retain
them directly (or deterministic construction IDs), rather than coordinate search.

Clean-HEAD VK attribution verified independently: actual import origin in head_wt;
elastic lambda0.5278676350911459/uz+0.004311600730850681 and plastic
lambda0.46647135416666663/uz-0.016745015799163078 exactly match candidate.
The candidate source changes therefore did not introduce these VK observations.
Initial clean-head launch failure (relative script path/import) is retained as
ep-attrib-vk-cleanhead; corrected evidence is ep-attrib-vk-cleanhead-2.

## Correction and route decision after full admission review

R2 is NOT an admitted defect: nonlinear_static.py already refuses corotational
initial stress/prestrain fields before reaching the linear helper. Preserve that
guard and add/retain a refusal test; DO NOT broaden initial-field capability or
thread an unreachable initializer merely to close this latent integration gap.
The code reviewer corrected supervisor_code_review.md accordingly. Active source
repairs are R1,R3,R4,R5; reference adoption and harness findings still apply.

Stop the serialized checkpoint detour. The public Slice3 restart contract can
and should use initial_displacements + initial_element_states, with explicit
equilibrate_initial_state=False, emit_restart_checkpoint=False. Use half6steps
to-.10, resumed6steps to-.20, uninterrupted12steps. The initial lambda=0 is a
Newton guess, not a material reset; for these shell-node dead loads its augmented
unknown absorbs the previous lambda without a production API change. Preserve
the frozen Q4 checkpoint validation; do not loosen bindings or claim serialized
restart support. Document the observed pre-existing limitation separately.

For DC cancellation use progress_callback (accepted increment records), not
status_callback, because DC does not emit the latter. Cancel after two accepted
increments; compare deep copies of initial displacement/state inputs and saved
accepted snapshots; reusing those same inputs must reproduce the fresh resume.
The output diagnostics must reconstruct at result.load_factor, and use direct
fixture node IDs. See reviewer addendum for detailed path reasoning.

## Initial worker handoff reconstruction

The initial MaxTurns80 worker ended after a tool read with no final handoff
(turn-bound completion, not service unavailability). Astra inspected evidence:
18 charged attempts, used621.3494068000291s, remaining2978.650593199971s with
900s still reserved. Initial seven owned source/test hashes are unchanged.
Useful delivered artifacts are harness.py, ep_attribution.py, ep_edge_coupling.py,
baseline61 passes, completed seven-case attribution and pre-yield controls.
No new Slice3 test module or product repair exists yet. Numerous checkpoint
probes demonstrated the same pre-existing validation boundary; do not repeat.
Continue the same Mistral owner from these artifacts with the adopted route and
review findings. This is partial implementation, not Slice3 acceptance.

## Prospective analytical assessment metrics

Compare shell and beam tip displacement vectors separately using
norm(u_FE-u_arc)/norm(u_arc), and planar tip ry using abs(ry-Phi)/abs(Phi).
Both centroid tips and rotation must meet1%; report ux/uz component errors too.
Last-refinement displacement-vector and ry changes, normalized by the finer
result, must meet0.25%. Freeze these definitions before analytical FE results.
Use actual equilibrium at the reviewed fixed terminal loads (force control
completed at lambda1). If a displacement-controlled computational route is
necessary, prescribed rotation alone cannot establish the stiffness oracle:
also require its recovered proportional load factor to agree with1 within1%.
No prescribed/corrected nodal displacement may replace a force-equilibrium result.
Request corotational_tangent='work_conjugate' explicitly for every analytical
case, including e=0 (whose descriptor is inactive and whose auto mode otherwise
resolves to the legacy rotated path). Compare the same internal force law.

## Review of first continuation edits

Reviewer recheck: new R3 selector using initial_committed_displacement in all
n_red==0 cases is wrong for fresh force control. That branch deliberately sets
initial_committed_displacement=map(T@q) without u0. With no reduced DOFs it is
zero even when u0 contains finite prescribed master motion. Preserve original
branch selector, mapping raw offsets exactly once: checkpoint_resume -> already
mapped initial state; force_restart -> map(initial_affine_offset); fresh ->map(u0).
The full prescribed-state R3 test should discriminate this. See updated reviewer
report. New R1/R4/R5 edits look statically consistent pending their tests.

Harness recheck: the exception-finally path writes wall_total_final=wall_total
but does not add elapsed time for an interrupted active phase (t0). An exception
after launch can still undercharge that child. Track active phase start/completion
and account its elapsed time after owned-process cleanup unconditionally. Prefer
one precise lifetime record per preflight/main child plus cumulative sum. Current
observed successful/timeout receipts remain valid; do not rerun them unnecessarily.

Current test_r3 fixture first installs zero root supports through its builder,
then appends nonzero root rotations, so audit rejects before reaching n_red==0.
Replace/remove the old root boundary in this fixture; do not append conflicting
supports. Explicitly assert prescribed shell values as well as beam offset to
catch the fresh-force zero-vector R3 regression. See reviewer addendum.

Follower derivative test: in addition to the complete coupled derivative, check
the external reduced-force derivative on its own scale. With pressure200Pa and
steel stiffness, a relative full-K tolerance can hide an absent external load
tangent. Differentiate J(u)^T F_ext(u) and compare to
J.T K_ext J + geometric_tangent(u,F_ext), normalizing by that external matrix.
This reuses the same candidate and FD loop without another model/sweep and makes
the external contribution discriminating. Keep the integrated complete check.

## Parent focused check, preserved failed evidence

Astra ran supervisor-source-repairs-1 through the shared harness (39.695867s;
budget now661.0452738000022s). JUnit:12passed/4failed. Failures:
- R1 positive upstream-tie fixture creates repeated shell node IDs (element1).
- R3 both routes have conflicting old root/new prescribed rotation supports.
- R5 preload only rotates0.003144rad, so its claimed >0.1rad precondition fails.
Full JUnit/stdout/receipts are retained in that evidence directory. The owner
edited nonlinear_static.py/test/harness while this check was running, so input
identities are not stable across execution: this is diagnostic failed evidence,
NOT acceptance of the current candidate. Do not claim its12 passes as current
source verification. Repair the concrete fixtures and run a stable integrated
check after edits; do not rerun for the sole purpose of erasing failed evidence.
Parent will avoid further numerical checks while owner is modifying these inputs.

## EP DC failure discriminant and adopted solver route

ep-dc-limit-probe-1 shows maximum_iterations_reached, not a constitutive exception:
direct reaches uz-.16666666666666666,lambda2.803228281651541,alpha~.02142;
interp reaches uz-.08333333333333333,lambda9.599335430165452,alpha~.00811.
The DC helper aborts a failed fixed increment without any control-step cutback.
The 12 steps in the approved plan are INITIAL increments, not authority to
increase Newton's40 iteration cap or relax tolerance/target.

Astra adopts bounded adaptive control-step subdivision for the new rotating-MPC,
contact-free DC route as a compatible internal solver repair: on failed attempt
discard trial, restore q/lam/history/contact state exactly, subdivide only that
control interval, retry within the existing min-step control and task budget.
Preserve every original scheduled control milestone, so half6+resume6 and full12
trace the same intended targets with any accepted subdivisions inserted. Do not
claim exactly12 accepted steps. Record attempts/cutbacks/stop reason, retain
cancellation safe points, and append snapshots/material history only on acceptance.
Keep contact/moving-tool and legacy routes unchanged unless separately reconciled;
their path factors must not be inferred from a changed accepted-step ordinal.
The owner chooses compatible queue/loop details. If bounded subdivision fails,
preserve that evidence and report the specific obstruction, not physical collapse.

EP wrench test currently sums EVERY internal nodal force, at REFERENCE positions
and with raw rotation covectors, then cancels external loads. That tests neither
the physical support wrench nor spatial self-equilibrium at finite rotation.
For explicit support balance use all physical root-node residuals after rotating
slave imbalance transfer (or include untransferred beam root), DEFORMED force
arms, spatial moments (root rotationszero => covectors equal spatial moments),
and applied loads at their actual deformed loaded nodes. The -.10 direct result's
53.85Nm apparent error from this old formula is not evidence of a solver defect.
Independent reduced residual must use actual achieved lambda as already specified.

## Focused DC continuation delta after product run 60-turn bound

The third wrapper ended with a successful read/edit, no handoff and no launched
ep_dc_step11_probe attempt. Source16 tests passed; EP7failed/4passed remains open.
Continue from that exact manual probe, not broad source investigation.

The augmented DC matrix [K,-F; row,0] is generally NONSYMMETRIC even when K is
symmetric. Adopt MatrixClass.GENERAL for it unconditionally (both DC sites if
applicable). PARDISO symmetric paths consume upper triangle; neither a symmetric
K nor absence of follower forces makes this augmented matrix symmetric. This
is a compatible algebraic correction, but do not assert it causes the observed
stall unless the recorded probe discriminates. The manual probe already uses
GENERAL. Verify actual backend if relevant. Then implement bounded failed-control
interval subdivision as adopted above if still needed; preserve material state,
all original milestones, limits, cancellation and full/half restart consistency.

Final EP assertions must account for inserted accepted subdivisions (not require
exactly6 resumed accepted steps). Match physical control milestones/histories
without dropping accepted records. Reconstruct residual and reactions for EVERY
accepted snapshot using its own copied material state/load, not just final state;
require unchanged saved state on reconstruction. Compare full final material
history arrays full vs resumed with existing restart tolerances in addition to
the scalar alpha maxima. Use max(norm(J.T*(lambda*F)),1) for achieved-load relative
residual. Do not weaken the fixed1e-7 gate. Source identity must stay fixed during
each test invocation. Reserve enough nonreserve budget for mesh/arc assessments;
prefer one cached integrated EP run over serial per-assertion solves.

D1 regression: add a focused declared-matrix-class spy/fake-backend assertion
on the public DC assembled-augmented path; it must see GENERAL independently
of optional PARDISO availability, while delegating the actual solve unchanged.
Do not require PARDISO installation or count a SciPy pass alone as coverage of
the old symmetric declaration bug. Independent derivation is in
supervisor_assessment_review.md D1.

Ordinary-state DC resume has no public initial-lambda argument; the internal
initial_load_factor currently defaults0 outside checkpoint resume. If that
guess obstructs restart consistency, a compatible internal option is to recover
the equilibrium scalar from copied accepted initial state using reduced forces:
lambda=dot(p, f_int_reduced-f_constant_reduced)/dot(p,p), p=J.T F_prop.
Use only the ordinary supplied initial-state route without re-equilibration,
not an override of explicit checkpoint lambda; evaluate without committing or
mutating caller state. This is a Newton initial guess, not a success definition
or public API change. Report any initial residual inconsistency; no fitting.

Independent review D2 current adaptive-loop bug: target_increment0 gives min0;
the cutback condition becomes0>=0 forever when same-target Newton hits maxiter.
Guard finite positive min/span and representable target progress, and explicitly
bound cuts (currently max_control_cutbacks only scales min, no count check).
Same-target failed Newton must terminate boundedly. Also step_iterations is
initialized once per original milestone but reused cumulatively across accepted
subdivisions: reset per published increment so step reports do not double-count
previous accepted work; keep separate attempt/total iteration accounting.

Read supervisor_dc_review.md before handoff: additional concrete gaps are listed
there (inline rejected-state inputs unobservable, every-snapshot/full history).
Latest two failed attempts are preserved: subdivision1 pytest150s timed out with
only first F printed (no traceback), and limit-probe2 full120s timed out before
its first result. Next obtain the FIRST test failure with -x / a single direct
node ID, not another buffered two-route full rerun; snapshot-enabled test may
fail for a fixture/recording reason before the no-snapshot probe returns. Retain
per-accepted progress on any diagnostic so timeout output is informative. A
focused pytest invocation is a regression (up to600s), not a single diagnostic,
but do not consume the900s final reserve. Remaining nonreserve budget is now
about1455s; preserve enough for independent mesh/arc assessments.

Block-probe-direct1 FD comparison has a SIGN ERROR: residual_at returns
R=lambdaF-fint, so dR/dq=-K_red, not+K_red. Its uniform relative_error2 at both
healthy and terminal states is exactly expected for this sign mistake; it is
not a product tangent defect. Compare fd+K_red. Central differences on a newly
committed yield surface can additionally straddle elastic unloading/plastic
loading: a true consistent-tangent test should use the previous accepted state
and an interior trial on a fixed active branch. Do not repair source based on
the existingFD2 numbers. The recorded terminal state is useful: direct reaches
-.18333333333333335,lambda2.66796710849,14accepts/26attempts/11cuts, min-step stop.
The tiny-step prediction currently uses POSITIVE control displacement, i.e.
unloading; desired continuation is NEGATIVE. Preserve evidence; no blind rerun.

Astra now owns harness timeout admission (reserved execution contract): enforce
max120 diagnostic / max600 pytest or portable regression before launch. Worker
block-probe-direct1 requested180s (outside diagnostic default) but actually
finished88.7512515s. Retain this admission discrepancy; it does not change the
3600s allowance and is not renewed authority. Future oversized diagnostics are
refused. Harness accounting and all original failed evidence stay intact.

Scientific adjudication: an UN SCALED augmented matrix condition number mixes
stiffness (N/m), unit control rows and load-pattern magnitudes, and cannot prove
a physical displacement-control fold. In direct block-probe1 the tiny-step
numbers imply control compliance du_control/dlambda=6.5104e-5/(-.0061407)
about-.01060m per lambda, comparable to the elastic control compliance, not a
near-zero displacement-control derivative. Do not label this a fold/collapse
from dimensional singular values. A discriminating scaled augmented solve or
line-search residual trajectory at the desired NEGATIVE control increment is
needed for that claim; otherwise report unresolved Newton failure only.

Independent objective-map derivation (reviewer, pending full report at
supervisor_objectivity_review.md): for an interpolated entry let
D=sum(w_i*Jl(theta_i)^-1)-Jl(theta_bar)^-1 and
A=d[R(theta_bar)*r]/d(theta_bar). A common physical rigid spin Omega gives
slave orientation error D*Omega and translation error A*D*Omega. Current
slave-to-master transfer changes physical moment by EXACTLY
DeltaM=D.T*(m_b + A.T*f_b), with m_b the slave rotation-vector force covector.
Sum this over entries and compare physical root+applied moment imbalance;
separate constituent global internal wrench and remaining free residual. This
is a discriminating attribution at the completed interp-.10 state, not a new
load sweep; direct/identical rotations give D0. A corrected map must remove
BOTH orientation and offset defects, with connected Jacobian/geometric tangent
and inverse/postcheck treatment. Do not fit or subtract DeltaM from the reaction
oracle to obtain a pass. Use it to identify the mechanics defect.

Full independent derivation and integration checklist is now saved in
supervisor_objectivity_review.md. In particular subtract the original linear
theta_lin lever in the forward correction (not the nonlinear mean lever),
preserve bad slave perturbations in the inverse, include m_b-weighted mean
second derivatives in the geometric tangent and refuse downstream nonlinear
slave ROTATION dependencies as well if orientation is corrected. Do not silently
clip weights or select inconsistent quaternion signs. A proper polar mean of
sum(w_i*R_i) is a compatible objective candidate where that proper polar factor
is unique/nonsingular; direct/identical limits and linearized weights must agree.
Handle ambiguity/chart boundaries explicitly; no arbitrary global3D chart claim.

## Adoption of the owner's intrinsic mean proposal / immediate integration repair

Checkpoint's intrinsic SO(3) weighted mean is adopted for the new ACTIVE
interpolated rotating-offset route, within a unique local convex neighborhood,
with nonnegative normalized existing weights and explicit refusal on unsupported
ambiguity/chart/weight cases. Direct and zero-offset legacy routes retain their
existing meaning. No weight clipping or re-fitting. Complete the connected
orientation+translation/J/Hessian/force-transfer/inverse/postcheck/descendant
guards and objective rigid-spin regressions together. The independent moment
defect identity must explain the old physical-wrench failure; repaired support
balance is assessed directly, never corrected by subtracting a diagnostic error.
See supervisor_objectivity_review.md full derivative/refusal obligations.

Parent single direct check supervisor-dc-direct-globalized-1 failed in4.519s
BEFORE mechanics: the public driver passes recover_initial_load_factor into
nonlinear_performance._solve_static_displacement_control_block, whose signature
does not accept/forward it. Repair that shared wrapper (inside owned five files),
then rerun the single -x case with trace/progress rather than broad sweeps. Tests
and globalization changes remain unverified. Five wrappers have ended without
handoff; provide a concrete end-to-end candidate and saved handoff this time,
with realistic sustained turn capacity rather than restarting investigation.

Frame-convention clarification for the rigid-spin probe: in PHYSICAL current
positions x_b=sum(w_i*x_i)+R_mean*r0. In DISPLACEMENTS it is
u_b=sum(w_i*u_i)+(R_mean-I)*r0 (assuming X_b=sum(w_i*X_i)+r0).
The checkpoint's physical-x formula with (R-I) omitted that initial offset.
Superpose rigid rotation using u_i^Q=Q*(X_i+u_i)-X_i, not Q*u_i alone. A direct
control must pass at roundoff; the noncommuting interp failure should match D.

Early helper review (_so3_mean_block.py): implicit G_i formula agrees with
delta psi_i=Jl(psi_i)^-1 Rm.T*(delta alpha_i-delta alpha_m). However normpsi<pi
and detB>0 do NOT enforce the adopted unique local convex mean: equal masters
Rx(+pi/2),Rx(-pi/2) admit two means I andRx(pi), and pass those checks. Restrict
the supported local convex neighborhood explicitly (e.g. each relative rotation
strictly withinpi/2, with boundary refusal), and handle the absolute principal
rotation-vector mean chart boundary. Exact-identical shortcut at raw theta>pi
would otherwise differ discontinuously from the principal-log perturbed path.
Keep direct legacy behavior, but do not claim unsupported active-interp chart
continuation. Add focused ambiguous/chart refusal regression. No new FE sweep.

Independent updated EP test review (full report supervisor_globalization_review.md
forthcoming): apply_kinematics(to_linear_displacement(u)) is an ambient inverse
identity for ANY bad slave perturbation, so it is NOT manifold membership.
Run constraint_residual_summary(model, to_linear_displacement(snapshot_u)) or
explicit physical relations at existing tolerances for EVERY snapshot. Preserve
deep pre-reconstruction copies, not aliased state references, for immutability.
The resumed snapshots start AFTER-.10; current material comparison loop includes
-.10 and calls _snapshot_at_control(resumed,-.10), which must fail. Compare split
state using half vs full split, then only later resumed milestone snapshots.

Mean-domain resolution from independent review: adopt a conservative equivariant
anchor ball around the FIRST master, strict radiuspi/4, for active multi-master
means. All master orientations AND returned mean must be inside that ball;
distances use Log(R_first.T R_i), invariant under common left rotation. This
gives an explicit convex local domain instead of treating detB as uniqueness.
Check the symmetric B part is positive definite before solve. Enforce supported
absolute principal rotation-vector chart for multi-master inputs/mean BEFORE
the identical shortcut (reject boundary/out-of-chart); preserve one-master
direct legacy handling separately. Add the small noncommuting admissible
rigid-spin case and ambiguous/chart refusal cases. Required planar benchmark
neighbor rotations are inside this local domain; actual EP states still need
measurement. No arbitrary chart continuation claim.

Immediate SO3 FD failure diagnosis: debug_so3_map.py computes J at the MANUALLY
modified u_lin, but FD at T@(old q +/- dq)+u0. Those are DIFFERENT centers.
_interp_map_with_distinct_master_rotations explicitly says its manual state is
not inimageT (it even changes fixed root rotations); this cannot test du/dq.
Use a single admissible q (e.g. seeded independent coordinates in[-.15,.15]) and
u_lin=T@q+u0 for BOTH J andFD, ensuring distinct noncommuting free rotations.
Do not repair correct mean G_i based on this mismatched-state comparison.
The finite rigid-spin test also updates shared master nodes repeatedly while
looping couplings; transform each unique master ONCE from original state, then
rebuild all slave linear rows. Repeated Q applications are a fixture defect.

Existing original coupling test module has been edited outside the prior
new-test-only boundary. Astra prospectively admits the NECESSARY updates to its
old weighted-rotation expectation to reflect the adopted objective mean, while
preserving every original test and tolerance and protected backup. New objective
regressions may remain there (the final selection includes this module). Use an
independent two-master geodesic reference R1*Exp(w2*Log(R1.T*R2)), not a call to
the production mean as the sole oracle; independent FD/spatial wrench tests also
remain. Do not edit the original work-conjugate module. Record original-module
changes explicitly; the final manifest must not claim its hash unchanged.

Performance/precision discriminant after full coupling module240s timeout:
all relevant edge interpolations have TWO masters. Their intrinsic mean has
the exact closed form Rm=R1*Exp(t*Log(R1.T*R2)), t=w2/(w1+w2). It satisfies
the adopted Karcher equation, keeps the same implicit G_i derivation and avoids
iteration stopping noise1e-14 being amplified by stiff EA/short elements, as
well as repeated fixed-point work inside Hessian probes. This is a compatible
internal algorithm, not a load/reference/tolerance fit. Consider this exact
two-master branch before repeating a slow unchanged large-angle solve. Retain
the direct analytic lever-arm Hessian where possible; no unmeasured speed claim.
