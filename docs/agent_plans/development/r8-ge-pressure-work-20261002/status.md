# Pressure candidate — WORK IN PROGRESS, 2 October 2026

This is unfinished development, not installed verification or acceptance.
The source candidate implements typed model-bound shell pressure and restart on
the existing point owner. Existing Q4/S3 reference-dead kernels remain intact;
finite Q4 dead and Q4/S3 current-surface follower paths reuse existing kernels.
Native enhanced-dead S3 finite work remains unimplemented and fails explicitly,
including restored-context driver construction. No translation-only substitution.

Independent review identified a detached mesh-element registry gap; fixed with
constant-time identity checks and four mutation tests. Current-area force retains
its nonsymmetric translation Jacobian and has no invented endpoint potential.
The new context explicitly rejects collapsed Q4 stations; legacy kernels unchanged.

## Executed evidence and failure disposition

- Source focused-v1:29passed,3finite-follower failures (20.27s pytest).
- Parent-frozen follower backtracking comparison: dead1passed, follower3still
  fail (25.85s). Mandatory current-state component/global/gap acceptance unchanged.
- Acceptance guards2passed: first Newton step can advance without false commit;
  the existing tiny independent load remains protected. No tolerance relaxation.
- No wheel build, installed check, completed public example or qualification claim.

The initial follower Newton step lowers global residual1 to6.5375e-4, but newly
active Fy creates a component ratio2029.5, so the old changing-norm comparison
rejects it. For this new follower context only, candidates are now compared using
the parent's actual applied vector. All rows remain in the global norm; each
Newton parent recomputes scales. Commit/restore use the unchanged full current
acceptance. Independent mathematical review endorsed this bounded correction.

After that correction,100Pa Q4 case stalls at row31(shell node6 Fy):
residual -1.589008715698005e-14N / applied -9.271530008042393e-7N =1.713858e-8,
above1e-8. Global ratio2.6958e-14 and gap2.64698e-23 do NOT permit acceptance.
Mixed/S3 follower cases also still fail. Failed tests remain failing in source.

Frozen-state diagnosis identifies row31 with only one Q4 element's internal force
and pressure, not beam/joint/global-summation contributions. Exact-product pullback
improves residual only to-1.569286e-14N. Qualified correction plus exact pullback
still gives-1.517630e-14N. Repeated full local force was first checked byte-equal;
correction-v1 omitted a native hourglass reset and is superseded byv2, preserved
as diagnostic failure. Independent binary64-geometry/product pressure reconstruction
differs from actual pressure by1.05879e-22N. No blanket summation patch is justified.

## Next discriminating action

Capture the same near-converged full trial state and last Newton correction.
Compare accurately accumulated predicted R+K*dq with reevaluated residual and
representable coordinate changes. If solve accuracy is limiting, inspect bounded
refinement; otherwise inspect local Q4 kinematic/material evaluation sensitivity.
Do not change tolerance, use a higher-pressure fixture to hide this failure, or
claim that a small global residual alone closes the current acceptance requirement.

This retained archive binds the current candidate snapshot, commands, observations
and fixed-state arrays. Earlier diagnostic source was not prospectively frozen;
this is development diagnosis, not a formal qualification record. Formal F03 is
unconsumed. Existing scope/resources/legacy defaults remain; no push or publication.

## Resumed Newton diagnosis

New bounded `newton-v1` captures full trial configuration, shell anchors, retained
variables, multipliers and corrections. The accurately accumulated linear
prediction reaches 1.4e-28 maximum free residual on the final correction, while
actual equilibrium remains above its existing threshold. Shell corrections are
about 2.4e-22 and three nonzero shell updates round back to the same coordinates.
At that full correction row31 improves to 2.65e-15, but another component sets the
1.949e-8 acceptance ratio. Linear iterative refinement is not justified by this
case. All records and full states are in diagnostics-v2.zip.

A diagnostic dominant-component reconstruction of the 4x4 Procrustes eigenvector
uses a bounded 3x3 solve with the existing eigenvalue. It changes no production
source. Q4 and mixed remain failed; all-S3 completes its first 0.1 increment.
This is a hypothesis discriminator, not derivative/lifecycle qualification or a
promotable fix. The first attempt (eigen-v1) was correctly rejected by the exact
NumPy runtime guard. Eigen-v2 varied only the private experimental map through
copied function globals and left the guarded NumPy operations untouched. No guard
was disabled. The retained experiment script is the v2 form; v1 execution/error
remain retained, but its earlier script bytes were not frozen.

Next: compare fixed-state Q4 local deformation/strain and force sensitivity using
the saved full states. Determine whether component reconstruction is a justified
kinematic precision correction and identify the remaining Q4 cancellation before
any product patch. Do not add iterative refinement, compensated pullback, a load
floor, larger test pressure or relaxed acceptance without supporting evidence.
All owned jobs are terminal; no installed build or additional acceptance claim.

## Consistent fit correction and source regressions

The saved Q4 correction decomposes into a local deformation contribution error
-7.45e-19N and local force evaluation error -3.40e-16N at row31. This is a
fixed-state sensitivity observation, not a complete causal allocation for all
failed rows. The absent shell-anchor array means identity anchors; the first
sensitivity script failed on that representation and its error is preserved.

Implemented stable-translation-only quaternion reconstruction and a consistent
bordered derivative inverse. Ordinary historical current-coordinate evaluation
is unchanged. Independent source review is in precision-review.md. Focused
verification26passed; owner/legacy regression22passed, including Q4 yielded
unload/reload/rebase/restart and shell objective work/tangents. No installed wheel
has been rebuilt. Raw runs, initial test failures and source snapshots are in v3.
The first broad regression collection failed because its docs oracle requires
repository root on PYTHONPATH; the corrected run preserves src plus root.

Pressure lifecycle remains three failures. Q4 and S3 pass the first accepted0.1
prefix but fail continued stepping; mixed still fails before that prefix. Existing
cancellation/restore checks execute up to those points; this is not a completed
pressure workflow. The original test is unchanged and remains failing.

Next discriminator: record limiting force row and local contributions at the
failed second Q4 increment using this corrected map. Separate local force
cancellation from representable-coordinate and merit effects before selecting
another correction. Do not repeat successful derivative campaigns without new
changes. All jobs terminal; no main/push/publication or formal F03 execution.

## Pressure globalization discriminator

Second Q4 increment: full Newton decreases global imbalance0.5 to0.000327,
but component merit rises to507 from the lateral nonlinear correction. A purely
global work merit removes that barrier but still stalls near final component
acceptance (13passed/3failed lifecycle run). The candidate now selects work-norm
backtracking until global<=1e-8 and gap<=1e-9, then the unchanged component/global
merit for polishing. Parent and candidates use the same selected formula and
frozen parent applied vector. No physical load floor, tolerance or budget changes.
Pressure cannot coexist with nodal/programme loads under this context contract.

Independent reviewer pressure_precision_review found no material blocker for this
bounded experimental search. It is not a globally monotone merit: polishing can
raise global/gap measures and cause stage reversal. Iteration/backtracking budgets
bound that risk; the unchanged current-state commit checks prevent false success.
No stage-cycle evidence currently justifies another safeguard or globalization.

Full Q4 and all-S3 pressure lifecycle now passes: cancellation at0.1, checkpoint
restore, continuation0.2, chart rebase and0.3 continuation. Mixed still fails
before0.1 acceptance. Focused lifecycle/false-commit run4passed/1failed; additional
units, extreme norms, zero load, quiet-component and false-commit guards3passed.
During that lifecycle run only a comment was corrected and not-yet-collected new
guard tests appended; executable candidate logic was unchanged. Earlier candidate
files were not frozen separately; this v4 captures the final source and raw runs.

Mixed limiting row12 (shell node3 X) has residual2.07324e-14N against pressure
-1.095318e-6N, componentratio1.89282e-8. S3 spatial force16.288461878184N balances
the point-interface contribution. Exact local elastic force/pullback arithmetic
changes this by only-3.55e-15N, insufficient to establish acceptance. Do not claim
a scalar summation patch resolves it. The split diagnostic's residual_blas/exact
fields subtract pressure from SHELL force only and omit the joint force; they are
not assembled equilibrium residuals. best_global_ratio in that helper is actually
the maximum acceptance ratio, not a global norm; use diagnosis.json for the latter.

Next bounded action: recover the point-joint work contribution and its accurate
row12 pullback at the saved mixed state, separating local-force precision from
configuration representation. No further broad test campaign before that choice.
No installed pressure artifact, completed mixed workflow or aggregate acceptance.
All owned runs terminal; formal F03 untouched.

## Mixed point-row diagnosis and stopping decision

At the saved mixed state, exact shell and joint product reductions each change
row12 by-3.5527e-15N. The resulting frozen assembled residual1.3627e-14N still
exceeds the1.0953e-14N current component limit. Re-solving with exact-product
translation force arithmetic fails before the first commit; no product patch.

Two diagnostic value-only oracles use60-digit Decimal Procrustes/local translation,
then also local rotations, while retaining native double gradients/Hessians and
converting local values back to float. Both fail before commit. They are NOT a
consistently high-precision residual/Newton oracle and do not prove the criterion
unattainable. The first all-value script failed on Decimal0**0; v2 handles its
series constant explicitly. The initial script bytes were not separately frozen;
its error and final script remain. These are private experiments, not changed
qualified numerical kernels or production algorithms.

Independent read-only review recommended tracing the actual mixed correction
rather than another substitution. That trace predicts free residual2.899e-29,
but row12's1.00624e-24m coordinate correction rounds to0, as does the
1.09077e-15N axial multiplier correction. Six nonzero shell coordinate corrections
round away. The joint row remains-16.288462973502206N; reevaluated shell force
changes16.288461878184 to16.288461878183952N. Actual row12 residual becomes
-2.54529e-14N and overall acceptance ratio3.24805e-8. Full state/correction and
separate shell/joint contributions are retained in mixed-newton-v1.

Decision: stop blind local precision substitutions. Next design must address the
identified state representation/response resolution, or propose a separately
reviewed prospective pressure assessment amendment. Neither evidence nor failure
permits automatic relaxation. Independent review notes CartesianR/F is coordinate
dependent for tilt-induced components of one scalar pressure, but replacing the
mandatory test changes assessment and must follow the goal's explicit scientific
criteria authority. Legacy tiny independent nodal-load protection remains binding.
No normalization change has been made. G4A and the mixed pressure row remain open.
Unrelated permitted development need not wait for this numerical design decision.
All jobs terminal; no additional product edits in this diagnostic turn.

## Installed Q4 development example

Built isolated wheel ac2ea592e6316af7fa2d2ea5a4c1d5d7e6a5acc041c2b290abff815ea5199772
without network/dependency rebuild/version change;396source modules match wheel
and installed site. The public Q4 two-shell/two-GE pressure example completes
0.25/0.5/1 with identical checkpoint-restored continuation, equilibrium3.600566e-9
and compatibility5.717472e-21.217solver imports all resolve inside the isolated
site; actual1numericalthread/JIToff. Full route6.900489s, sampledpeak156184576B.
This is a development-artifact example, not an installed full pressure suite or
mixed-mesh acceptance. Wheel/site retained under Temp/r8-ge-pressure-installed-v1;
raw commands/runtime/source hashes/fixtures are in installed-example-v1.zip.
ANYfem pressure input/persistence extension is proceeding independently; it must
preserve explicit solver failure and finite S3 enhanced-dead rejection.
