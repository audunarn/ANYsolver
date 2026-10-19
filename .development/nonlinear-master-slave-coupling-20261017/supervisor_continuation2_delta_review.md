# Integrated continuation-2 delta review — 2026-10-18

Routine read-only non-author closure of the new batch kernel/dispatcher and per-failed-interval subdivision repair. No imports, numerical execution, pytest, workers, source/test edits or Git mutations. This does not repeat the completed user-requested Astra review. No new blocking source defect was established in the inspected delta. Numerical acceptance remains open; full-target tests were active at review.

## Batch mechanics and derivatives

`src/anysolver/_corotational_batch.py:189–217` preserves the supplied material term B.T Kref B and computes only the frozen-reference-force geometric derivative. The outer translation widths remain 1e-5 max(spread,1e-3), rotations1e-5; beam frame sensitivities retain the nested translation width1e-6 max(spread,1e-3) and rotation width1e-6. The two-node beam omits second-node translation probes and restores their columns by translation invariance, matching scalar production. Shell rotation columns include both the direct nodal rotation covector and the frame-covector term, as the scalar code does. Final symmetrization is unchanged.

The batch axes are consistent: outer samples have shape(samples,nodes,3); nested beam samples have shape(samples,inner_samples,nodes,3). Beam rotations use the last node axis, preserve the scalar alignment/relative-twist extraction, and average twists along the node axis. The pullback contractions produce D.T f_rot, sum U.T f_rot and G.T times the rigid-frame covector with the same signs as `corotational.py:782–814`. Translation centering and the sensitivity's translation-mean removal use the node axis. No broadcasting error or dropped cross term was found.

The exponential, logarithm and Jacobian small-angle polynomials match scalar coefficients and thresholds. Near-pi logarithms and antiparallel alignment explicitly call the scalar branch. Thus these exceptional branches retain the scalar convention; the optimization does not establish differentiability or objectivity across the pre-existing pi/antipodal branch cut. On the smooth branch, shell frames use cross products and beam aligned frames transform covariantly under a superposed spatial rotation; relative twist is invariant, so batching introduces no new frame choice.

The dispatcher remains lazy, and the original scalar kernel is retained. Native-frame shells have center_dN=None by `_CorotationalReference` construction and immediately fall back; non-two-node beams do likewise. A failed fast-shell sensitivity admission falls back for the complete stencil, rather than mixing scalar and batch columns. The scalar fallback retains its original native-frame support and admission behavior. The new helper does not call constitutive response or commit/recover material state, and its perturbed displacement/rotation arrays are copies; no input-history mutation path was found.

## Subdivision, rollback and finite progress

`nonlinear_static.py:4019–4021` separates cumulative milestone cutbacks, current failed-interval cutbacks and accepted partial-count evidence. Only interval_cutbacks gates retries (`:4412`). It resets after an accepted partial increment (`:4624–4629`), while cumulative counters remain cumulative. This repairs the previous premature limit after several successful subdivisions and does not reset the minimum span, Newton40 limit, original milestone grid or tolerances.

The finite-progress check at `:4435–4456` precedes material commit (`:4481`), record/snapshot construction and progress notification. A partial interval must advance finitely in the direction of the current milestone; nonadvancement restores q/lambda and discards the pending state. At most257 accepted partial intervals are permitted per milestone: the counter starts0, allows counter256, then rejects the next partial at257. A final full remaining interval can complete separately. Each failed interval has at most8 cutbacks, and each corrector has bounded Newton work, so the reset cannot create an unbounded sequence of accepted stationary states. The guarded route is the contact-free rotating-MPC adaptive route, so the new precommit refusal does not omit contact multiplier/tool-pose restoration on an admitted contact route.

The minimum span remains based on the original control increment and original num_steps, not the shrinking remainder. Accepted material candidates alone become committed; rejected intervals restore the last accepted q/lambda/history. Existing snapshot/caller immutability requirements remain in force.

## Focused test strength and limits

`test_nonlinear_beam_shell_slice3.py:879–932` forces oversized intervals to fail while actual smaller-interval assembly/transactions proceed. Requiring more than8 cumulative cutbacks, ordered controls and terminal completion discriminates the old cumulative retry-counter defect. The zero-progress regression at `:935–957` requires refusal before any record/snapshot and exact zero final displacement. The explicit257 accepted-partial bound is source-checked here; it is not directly exercised by these new fixtures.

`test_nonlinear_beam_shell_slice3_batch.py` compares beam/Q4/S3 at0/35/100degrees with nonzero translational/rotational deformation. The S3 fixture explicitly selects legacy-s3, whose LegacyShellElement has center_dN populated and is eligible for the active shell batch; it does not exercise the native-frame fallback. Primitive zero/pi and antiparallel branch comparisons are useful. Consequential coverage not directly established by these fixtures: an explicit fast-shell stencil-admission failure selecting fallback, a non-two-node beam fallback, nested beam stencil near a frame branch, and, at the initial review, scalar/batch caller-input immutability assertions (subsequently closed by the addendum below). Existing independent dp/du tolerances must remain the derivative gate; agreement with the scalar kernel alone cannot establish scientific correctness. No new execution or tolerance change is requested by this report.

## Inspected SHA256

| File | SHA256 |
|---|---|
| src/anysolver/_corotational_batch.py | 2D8C8D9D0CBFF0E7666F06DB1EDC01310958F6CE91E07AC214EECC0C1A997EF3 |
| src/anysolver/corotational.py | 20CF2EC60696AF91C72C0A3133A3339B12511329488FF2BDA5501E6F24200BB9 |
| src/anysolver/nonlinear_static.py | 223083FE90A0CFD03B2FE72BF4A5745FF04DD21ABE5A895A6C771E19F665DA06 |
| tests/test_nonlinear_beam_shell_slice3.py | 17419F137E35A2EC58B0B52649208DB0DD18BBC7F7F52534A703D29217DB073D |
| tests/test_nonlinear_beam_shell_slice3_batch.py | 116DA4CBDC2BDD985E52388134EEB74637E191CD49828DE0B1F26E5773873EAD |
| tests/test_nonlinear_beam_shell_slice3_continuation.py | 1168AF4B41E057B4F0A5B057659E609704CA42910EC227DB27BBF0CBBAFEEC6F |

Parent-provided observations only: nine scalar comparisons reportedly had relative full-K differences<=6.85e-11 and geometric differences<=4.64e-9; original7 plus new11 production checks reportedly passed. This reviewer inspected source/tests and did not execute or independently certify those receipts. The prior initial helper-identity omission was disclosed and supplemented; future final evidence must name the complete current source identity, including the new private helper.


## Narrow correction and safeguarded-search addendum — current source

The original legacy-S3 fallback statement was incorrect and has been corrected above. `tests/test_corotational_work_conjugate.py:66–68` explicitly requests formulation=legacy-s3. `elements.py:5906–5907` returns LegacyShellElement, the alias for the historical ShellElement (`:5668`), which has no corotational_reference_frame method. `_CorotationalReference` therefore populates center_dN at the triangle centre (`corotational.py:238–250`). Three-node identity alone did not justify the earlier fallback inference. The supplied S3 case is eligible for active shell batching; it supplies no direct native-frame fallback coverage. Parent reports its measured batch/scalar ratio near8x, consistent with this source path; no timing claim was independently measured here.

The latest safeguarded interpolation at `nonlinear_static.py:4319–4342` is algebraically correct for the adopted exact augmented-Newton slope and fixed search normalization. With residual r and signed control error c, the augmented direction gives Dr[d]=-r and Dc[d]=-c, hence the directional derivative of the weighted norm-plus-absolute-error merit is phi'(0)=-phi0 (including a zero component by its zero linearized increment). For q(alpha)=phi0-alpha*phi0+b*alpha^2 through the rejected trial, b=(phi(alpha)-phi0+alpha*phi0)/alpha^2; its minimizer is alpha_new=alpha^2*phi0/(2*(phi(alpha)-phi0+alpha*phi0)), exactly the implementation. Finite positive denominator is required; otherwise the next trial halves alpha. The proposal is clipped to[0.1alpha,0.5alpha], so every rejected evaluated trial contracts strictly and the eight-trial bound remains unchanged.

Interpolation is restricted to residual-dominated correction by comparing the two normalized merit components (`residual_norm*target_scale >= constraint_error*reference`). The constraint-dominated branch retains the prior halving and admissible full-control predictor behavior. A typed mapping refusal contracts alpha by0.5 before continuing (`:4241–4248`); it cannot repeat the same refused candidate or fabricate a trial merit. It remains distinct from unrelated ValueError, and the previous rollback/classification checks are retained. Exact slope is a Newton-model statement, not a claim that the finite-difference tangent produces exact numerical descent; acceptance still evaluates actual trial merit. No new blocking source finding was established in this addendum.

The new conservative cubic controller regression (`slice3.py:960–1025`) supplies a consistent synthetic force/tangent while retaining actual constraint maps and state transactions. Its zero-control case discriminates descent below the old1/128 alpha floor; its nonzero-control case requires the full first control predictor and a single completed scheduled interval, guarding the residual-dominance restriction. Batch tests now store and compare all actual array arguments plus reference geometry/frame/shape-derivative preimages (`slice3_batch.py:35–45`), closing the earlier input-array observation gap. The retained fallback/branch coverage limits above are limitations, not newly invented acceptance gates.

Current hashes below supplement, and do not replace, the original inspected-identity table:

| File | SHA256 |
|---|---|
| src/anysolver/_corotational_batch.py | 2D8C8D9D0CBFF0E7666F06DB1EDC01310958F6CE91E07AC214EECC0C1A997EF3 |
| src/anysolver/corotational.py | 20CF2EC60696AF91C72C0A3133A3339B12511329488FF2BDA5501E6F24200BB9 |
| src/anysolver/nonlinear_static.py | 6B04A7B892F8293042BA92F1FBD4206626DFC8EDFF498496DA161EC028A981DA |
| tests/test_nonlinear_beam_shell_slice3.py | A0265FCA4DDF9CEDAB47A893B7338AF134DDE5650C4E13A3C7E3C0F28B71B050 |
| tests/test_nonlinear_beam_shell_slice3_batch.py | DA54CDAB42E0CAF2A7340473F33B671005DEE7BC58BA0F78023806EA1A537CC1 |
| tests/test_corotational_work_conjugate.py | B5CA8D2CCB65E2304357D8B7ED1E66951F1C921AFFDCF205342492E145843574 |
| src/anysolver/elements.py | B3AC0D22E053AA670277C173AA3417F576D161AD132F1CA44C0ADDAA3BE28A08 |

No numerical execution/imports/workers were performed for this addendum. Parent reports41 source checks passed and1 runtime-setting check skipped outside the portable runtime; the full direct target still failed at control-.18359375, lambda2.71755847561325, relative residual1.99e-11 with15 accepted snapshots in approximately106s, with raw accepted states retained. These are parent-supplied observations, not reviewer-certified receipts, and do not establish the required-.20 completion or acceptance.

## Beam precision repair closure — 2026-10-19

Routine non-author source/evidence review, with no imports, numerical execution, tests, workers or product edits. Compared current corotational.py against candidate-identities/overnight-force-entry/snapshot. The substantive delta is confined to beam centering and the algebraically equivalent translational deformation pullback; the batch helper adds a gauge comment only. No blocking mechanics defect was established.

Let C remove the nodal mean. The new beam geometry is C(X)+C(u), while its deformation is R.T C(u)+(R.T-I)C(X), exactly R.T C(X+u)-C(X). For two nodes C is represented by the antisymmetric half-difference, avoiding subtraction of absolute coordinate centroids. The beam frame depends only on its chord and nodal orientations, hence using this translated geometry leaves the mathematical R unchanged. The stable rotation-difference helper retains its original proper-rotation admission and large-angle fallback; it avoids subtracting nearly equal diagonal entries at small rotation. No material law, loading, tolerance or constraint was changed.

G depends on frame changes under geometry perturbations; D contains the nodal centering matrix and U uses centred arms. Therefore they remain derivatives of the new representation. Scalar and batched stencils may perturb one gauge node without explicitly recentering the perturbed array because frame and pullback functions discard common translation; this is equivalent to perturbing C(u). Both stencils receive the same gauge and preserve their prior widths. The work-conjugate force, consistent/rotated baseline routes and recovery deformational state all use the common helper. The baseline arithmetic therefore also changes for beams, but its mathematical mechanics are unchanged. This review does not claim all baseline profiles were numerically reverified.

Input/reference arrays are read only; centering creates new arrays, including copied half-differences. Reference cache signatures/invalidation are unchanged. The third return is now centred beam geometry rather than absolute X+u, and the helper documents that gauge. All inspected mechanics callers require chords or centred arms. An apparent public-recovery compatibility issue was investigated and withdrawn: private _element_recovery_context propagates the centred array as _recovery_coordinates, but recover_stress_result filters those fields on both public return branches (recovery.py3457–3477), and patch recovery excludes BeamElement before consuming coordinates (3525–3528). No supported current consumer requiring the absolute beam origin was found. This withdrawal supersedes the preliminary checkpoint message; it does not justify a recovery edit.

The new five precision cases retain axial force below absolute-coordinate ulps at origins0/.75/1e6, compare translated/reference-shifted deformation/frame/geometry/force/tangent, inspect actual caller/reference preimages, and independently differentiate B and force with h1e-7 at unchanged relative1e-9/1e-7 tolerances. Existing objectivity and batch parity tests are included in the recorded contracts run. The initial bitwise-symmetry assertion failed only at roundoff (max relative difference4.90e-16); replacing it with relative skew<1e-12 matches the existing material-BLAS symmetry contract and does not weaken the derivative tolerances.

Inspected frozen records establish a discriminating improvement at the same first-increment state and material history. Old product residuals over three Newton corrections were2.09360e-8,2.01006e-8,1.49166e-8,1.72348e-8. The centred candidate gave1.47025e-8,4.34079e-9,6.37674e-9,4.53925e-9; the implemented product reproduces that sequence. Constraints pass, actual inputs remain unchanged and linear relative backward errors are approximately3e-14–5e-14. These support a force-evaluation precision obstruction rather than an inaccurate sparse solve. The data do not imply every correction component is below a coordinate ulp.

The nx16 matching e.002/30degree receipt records completion at lambda1 with12 accepted steps,37.3373963s process wall, shell/beam tip errors0.0213864%/0.0214308%, rotation error0.0145758%, and independently reconstructed residual4.42691e-9. This is measured closure of that case only; remaining mesh/arc/global gates are not inferred.

Evidence identity limitation: contracts-2 reports23 passed, but its precision-test fingerprint is737c6fd... whereas the final inspected test isC5E8485... and contains the repaired skew assertion. Product identities match frozen-product and nx16 receipts. Root was notified to reconcile existing preserved test/launcher evidence; no rerun is requested merely to reconstruct identity. Preserve the initial failed evidence and this discrepancy rather than claiming the current test hash was certified by that stale receipt field.

Current inspected SHA256 (supplementing prior tables):

| File | SHA256 |
|---|---|
| src/anysolver/corotational.py | B56EF19E031FEC90F8E55CE076E335EBA050954460F3DDEAE55DA35682515A5A |
| src/anysolver/_corotational_batch.py | AC005ABC5D060951DA75B206F5CCBC122BC93B733F373E06BAF998ED67B2C7E2 |
| src/anysolver/recovery.py | 40528BA5A5419225EBA2084288C40E091A3166F183CA797947B2C27DF77BAE2F |
| tests/test_nonlinear_beam_shell_slice3_precision.py | C5E8485EBD01658A557BF58EE2565BBBEBE37AD3CC24E141607E88F1EE247519 |
| diagnostics/beam_precision_probe.py | 8A1351189A1254AC247BC830820C393F928B41E06FD23C4BF8F91F2F16975744 |

## Beam2 fiber elastic-limit repair — 2026-10-19

Routine integrated non-author Read review; no numerical execution/imports/tests/workers or product/test edits. Compared elements.py with candidate-identities/overnight-precision-entry/snapshot and inspected the focused source/tests/receipts. The sole product delta is the auxiliary shear coefficients in BeamElement._compute_fiber_nonlinear_response. No blocking error was established in the adopted positive-parameter Beam2 formulation. One actionable stress-oracle coverage finding remains below.

### Independent condensation and Jacobian check

For either bending plane let κ=(θ2-θ1)/L and γ=Δv/L∓(θ1+θ2)/2. With S=kGA and EI the corresponding centroid rigidity, the retained one-section energy is

U_b = EI(θ2-θ1)^2/(2L) + S_eff L γ^2/2,
S_eff = (1/S+L^2/(12EI))^-1 = 12EI/[L^2(1+φ)], φ=12EI/(S L^2).

The compliance is independently obtained from a beam's elastic moment-gradient mode plus its shear compliance. Expanding the energy gives the baseline Timoshenko entries12EI/[L^3(1+φ)], signed6EI/[L^2(1+φ)], and rotational entries(4+φ)EI/[L(1+φ)] and(2-φ)EI/[L(1+φ)]. Thus using raw S with the constant-curvature fiber section overconstrained this elastic mode; the new S_eff restores the existing elastic matrix without fitting response data.

The code maps local-y translation/rz to Iz,G12,ky and local-z translation/ry to Iy,G13,kz, with opposite rotation signs in the two γ rows. These match the existing elastic matrix. The fiber grid's weighted A, first moments, Iy/Iz and zero yz moment are explicitly checked in the new fixtures. Force uses the same K_aux*u as the potential gradient and tangent adds the constant K_aux. The existing fiber force L*B.T*σ differentiates to L*B.T*Et*B plus the N/L transverse string terms, so the nonlinear residual and Jacobian remain consistent with the stated von-Karman strain. Torsion is untouched. E1,G12,G13 are taken from the common canonical material service; the anisotropic axis mapping is correct statically, but the new measured matrix cases are isotropic and do not certify an orthotropic/Hill campaign.

The exact compliance identity assumes positive representable L,EI,S. The implementation intentionally shares the baseline max(S*L^2,_SMALL) regularization. At zero shear factor it therefore inherits a tiny nonzero stiffness floor rather than the exact S→0 limit; negative/zero section inputs are not newly validated by this change. Zero inertia removes that plane's curvature/auxiliary stiffness. No broad zero/degenerate-parameter equivalence claim should be made, particularly where the existing fiber-grid moment rescaling threshold collapses a small section's coordinates. These are inherited admission/regularization limits, not a new regression demonstrated for the registered positive sections.

### Constitutive scope, state and callers

Only the two-node von-Karman fiber response changes. Direct BeamElement callers and the generic external corotational wrapper use it. The separate internal elastic corotational route, generalized-section route and QuadraticBeamElement's per-Gauss-point override are not repaired or altered by this delta. No Beam3 equivalence claim follows.

This remains a one-longitudinal-section fiber plastic approximation: average-curvature fibers can yield, while the condensed auxiliary mode retains virgin elastic E and G. It does not integrate a longitudinally varying plastic moment field or perform nonlinear condensation of yielded higher modes. Consequently, after fiber yielding the auxiliary mode remains elastic; elastic-limit agreement does not prove a fully distributed yielding Timoshenko beam theory. This limitation is documented and is consistent with the prospectively adopted scope.

Fiber strain, return map, committed/trial state fields and initial stress/prestrain handling are unchanged. K_aux has no state and cannot itself mutate or commit caller history. Existing restart/rollback machinery is unchanged, but the force at an old displacement/history changes under the corrected formulation: pre-repair accepted states/trajectories are historical evidence, not current-equilibrium or strict-restart proofs. Full-target and restarted current-candidate gates remain required.

### Actionable test gap: beam stress comparison bypasses the actual fiber state

At the final inspected continuation test lines653–667, both plastic and true-elastic cases call BeamElement.compute_stresses on deformational displacement. That method reconstructs elastic axial/bending/shear/torsion quantities (elements.py4738–4764); it does not read result.element_states[eid]['fiber_stress']. Thus changing only a returned plastic fiber_stress array by a factor2 would leave the new distinct-elastic stress assertion passing. Shell comparison correctly uses actual layer_stress.

Add a comparison of the actual unyielded fiber_stress array with E1*(eps0+z*κy+y*κz) independently evaluated from the distinct true-elastic solution at the same fiber coordinates, using the adopted bound. Retain the separate legacy elastic shear/torsion reconstruction comparison as such; it cannot establish the plastic constitutive field. This is a confirmed observation gap, not evidence that current production fiber stresses are wrong. Root was notified before this report. Current tests now require all expected physical element IDs, which closes skipped-element coverage but not this field-selection gap.

### Inspected evidence and limits

- dc-distinct-elastic-control: preserved pre-repair failure,1 failed/2 passed; the high-yield same-algorithm controls missed the genuine elastic-route discrepancy.
- dc-fiber-elastic-limit-oracles:8 passed in19.2782884s process wall (four source regressions, two prior high-yield controls and two distinct-elastic controls). Full12x12 force/matrix comparisons at three lengths, independent conservative energy/dfdu, section moments and objective rigid motion are meaningful checks of the repair.
- dc-fiber-fixed-full-targets is terminal, not still active:56.0093064s,2 strengthened distinct-elastic tests passed; direct full target failed at control-.016666666666666666,lambda1.7393797028091125 with one accepted state, relative residual3.048394210341735e-10 and line_search_no_improvement. Interpolated full target was not run because of -x. No collapse/root-nonexistence or acceptance conclusion follows.

Current inspected SHA256:

| File | SHA256 |
|---|---|
| src/anysolver/elements.py | AE2DA8134C981ED651A58F8B622E99836EB279170861DD5F031E5EE0A3F55A0F |
| src/anysolver/corotational.py | B56EF19E031FEC90F8E55CE076E335EBA050954460F3DDEAE55DA35682515A5A |
| src/anysolver/nonlinear_static.py | 6B04A7B892F8293042BA92F1FBD4206626DFC8EDFF498496DA161EC028A981DA |
| src/anysolver/nonlinear_performance.py | D22FD0F3C29E2E25AC22F306F2F70ACB64A30D0ADB856B30667B6BACD1F7624A |
| tests/test_nonlinear_beam_shell_slice3.py | D0A39E8A7EFA5AD4BEC7D950CA4AF1F7CC1E7C5EF57C6B39432F8EAECBD99E6F |
| tests/test_nonlinear_beam_shell_slice3_continuation.py | C5BAE369DF52F2CFA509309D79DBEA225C0B3D26B8BF0D2B89EB72D9632D4A73 |

The8-pass receipt predates the subsequent stress-test strengthening; the full-target receipt binds continuation hash3B095CC...; the final C5BAE369... additionally requires complete stress element coverage and is not claimed fully exercised by those earlier receipts. Source agreement and this review do not establish final acceptance.

### Prior beam-precision test provenance closure

Root reconciled the earlier test fingerprint discrepancy without rerunning or overwriting evidence: the sole later change was tightening the B derivative assertion from1e-7 to1e-9. Reversing only that line in the current in-memory text reproduces the old737c6fd... hash exactly. A separate strict-B receipt binds the currentC5E8485... precision test and records1 passed/4 deselected in3.4981766s; product hashes match. This closes provenance by focused changed-input verification, and does not assert the full23-test invocation ran on the tightened test hash.

## Rising-shoulder search and physical stored-stress closure — 2026-10-19

Routine integrated non-author Read delta; no imports, numerical jobs, tests, workers or product/test edits. Compared nonlinear_static.py against overnight-precision-entry. The only production change is the residual-dominated, nondecreasing-trial alpha contraction. No new mechanics/Jacobian/state defect was established. One concrete stress-oracle nonfinite-value hole remains at this captured version.

### Bounded globalization contract

The added branch requires residual_norm*target_scale >= constraint_error*reference and merit_trial >= merit_current, then sets alpha*=0.1. It does not accept the rejected trial. Other admissible rejected trials retain safeguarded quadratic/decrease logic; typed SO(3) domain refusal retains alpha*=0.5, and the constraint-dominated predictor retains its previous behavior. There are still at most8 trial evaluations and40 Newton iterations. q/lambda update only after selecting the step; committed material histories/snapshots are unaffected by the contraction. Existing failed-attempt rollback, positive-span subdivision/count limits, cancellation and unrelated-error propagation are unchanged.

All rejection branches contract alpha strictly. The new heuristic can reach a nearby descent basin sooner but cannot guarantee finding every existing descent interval within eight samples; aggressive contraction can also skip a narrow interval. Thus line_search_no_improvement must mean no acceptable step was found in the bounded search, not a proof no improving state exists. The existing source comment near4365 still says 'No admissible improving step exists'; wording should be restricted to the attempted search. This is a claim-precision issue, not a source execution defect or new acceptance gate.

The new conservative piecewise fixture has an exact tangent on each branch, a continuous shoulder, local descent only for0<x<22e-6, and no equilibrium root. Its assertion on the second corrector discriminates finding local descent while the final failure/no-record/no-snapshot/zero-displacement assertions prevent false completion or accepted-state leakage. It does not assert generic global convergence.

The actual dc-fixed-direct-direction record reconstructs the failed RHS exactly, gives augmented linear backward error5.447e-14 and exact map round-trip. The old eight samples end at alpha0.000669887 with no improvement. Separate direction checks show residual5679.0731667 decreases to5679.0562189 at alpha1e-5. At1e-6 the forward derivative relative error is1.602e-5 (central2.765e-6); larger forward probes cross the constitutive shoulder and do not agree with the same local tangent. This supports the bounded search repair, not a claim of a defective linear solve, physical collapse, global root existence or completed target.

### Physical stress observation closure

The prior beam-field-selection finding is closed in source. The test now compares the actual stored plastic fiber_stress array against E*(eps0+z*κy+y*κz) formed from the distinct true-elastic solution at the matching25 fiber coordinates. It retains a separate elastic recovery comparison for shear/torsion. Shell comparison now observes actual stored layer_stress against C_plane_stress*(B_m*v + von-Karman membrane term + z*B_b*v) from the true-elastic mapped solution. This matches engineering-shear convention and integration-point/layer ordering without invoking return mapping. Required shapes, explicit physical element-ID coverage and witness sets catch missing fields, omitted elements and wrong array sizes; this fixture has two shells with20 layer rows each and two/three beams with25 fiber values each. Existing1e-7 bounds are retained.

Remaining actionable oracle hole (continuation.py679–716): norm errors may beNaN and the final Python max(values) assertion need not reject a laterNaN. Counterexample: leave all fields/forces/alpha unchanged but replace only the second beam's stored fiber_stress byNaN. The shape and witness checks pass; its fiber_error becomesNaN, and max([finite_first_error,NaN]) can return the finite first error. The same applies to the second shell's layer_stress. Require finite actual/expected arrays or require every individual error finite and <=the bound. This is a confirmed assertion blind spot, not evidence of observed productionNaNs. Root was notified promptly.

### Evidence and identities

Receipt dc-shoulder-physical-stress-oracles-3 records3 passed/57 deselected,13.0385789s process wall, binding the source/test hashes below. It closes the field-selection regression on finite measured data, subject to the nonfinite assertion gap. Full-target dc-fiber-shoulder-full-targets was still active/no terminal receipt when checked; no target/restart/matrix/regression acceptance is inferred. The earlier failed full-target evidence and states remain valid historical evidence under their own identity.

| File | SHA256 |
|---|---|
| src/anysolver/nonlinear_static.py | 456FE435D8762D4ACA7EDA4D1DD125A10ECF395278C9F6C3368D2A90842EBD81 |
| src/anysolver/elements.py | AE2DA8134C981ED651A58F8B622E99836EB279170861DD5F031E5EE0A3F55A0F |
| tests/test_nonlinear_beam_shell_slice3.py | 7D9120FFAEBC0003C55280AAC0B34F77421D01F19DFF9D324C4BD3090E3CC174 |
| tests/test_nonlinear_beam_shell_slice3_continuation.py | 03A0DC62E56FDE0C6917D777FF6B1458C2057D1407F0CC3919D4E06ED87D2F66 |

No derivative/material/physical tolerances, reference equations or success definitions were changed by this review. The one-section fiber formulation limitations from the preceding review remain unchanged.

## Finite stress guards and optional resolution experiment — 2026-10-19

Compact routine Read delta; no imports, numerical jobs, tests, workers or product/test edits. The previously reported NaN/max hole is closed: continuation tests require finite actual/expected displacement and stress arrays and finite individual displacement/fiber/stress errors before reducing maxima. Missing-field/shape/physical-ID/witness checks remain. dc-fiber-final-source-preyield receipt records52 passed/1 skipped (portable-runtime-only assertion) in63.590041s process wall; its pre-experiment continuation hash85A2387... is retained in dc-resolution-base.

The optional experiment selects16 failed-interval cutbacks and the corresponding positive minimum span only for maximum_iterations_reached/line_search_no_improvement with positive finite committed plastic strain. Classification reads the committed state after failed-candidate discard/rollback. Elastic cases and typed-domain refusals retain8 and their original minimum span. The independent257 accepted-partial bound and precommit directional-progress check remain. No change to Newton40, eight search trials, material equations or accepted-state ownership was found. This is a bounded resolution experiment, not evidence of target completion. Reversion remains root/owner-controlled if the stated strict target condition is not achieved.

One actionable new metadata defect exists in the captured experiment: terminal_control_failure is assigned in the failed-Newton branch and cleared only after acceptance. A partial candidate can instead converge and then fail the nonadvancing/257 guard at nonlinear_static.py4511–4531. That guard sets failure_reason=minimum_control_step_reached without updating terminal_control_failure, leaving the previous failed attempt's reason/span (orNone). Populate the terminal metadata from the current rejected progress/count state in this guard. A discriminating test can extend the existing nonadvancing-partial refusal regression to require the terminal reason/count/span to describe that rejection. This is an evidence-reporting defect, not a new mechanics defect; it disappears if the experiment is reverted. Root was notified.

Captured hashes:

| File | SHA256 |
|---|---|
| dc-resolution-base/nonlinear_static.py | 8C545E86969ED8AB7090E586E59B174F67B7448A409D6D8C361C264D23E91E1F |
| dc-resolution-base/test_nonlinear_beam_shell_slice3_continuation.py | 85A2387F26D40D612C5F0B1D317D56291DD51815910768608CD70E65010A48FE |
| src/anysolver/nonlinear_static.py, experimental | F81929C104467643D184D0F7251D6EBB439DF53B225FF5D289B4143CBF2EA9AA |
| tests/test_nonlinear_beam_shell_slice3.py, experimental | 4A932995AEAFFD42A07F89C08EB0EED106718A56803E99EF2C5C5446EE4E4367 |
| tests/test_nonlinear_beam_shell_slice3_continuation.py, experimental | 998A293A0FD182A9E437A01A3E75E3350AD8ECFABCDFB8D6A697165BC079E1F5 |

No acceptance claim or new gate is introduced. Earlier review entries describe their captured historical candidates; this closure supersedes only the NaN/max finding.

## Beam yield-band positive-update consistency repair — 2026-10-19

Routine non-author Read closure, no imports/jobs/tests/workers or product/test edits. The optional16-cutback experiment was reverted byte-for-byte to its saved base; its terminal-metadata finding is therefore moot on the current candidate. The finite stored-stress guards remain closed.

The return-map counterexample is confirmed: E210GPa, sy355MPa and trial overstress1Pa exceed the0.355Pa yield-entry band but lie inside the3.55Pa closure band. Previously the loop accepted dgamma0, returned unchanged elastic stress/history, and reported EH/(E+H) (zero for perfect plasticity) despite actual branch derivativeE. Tension and compression have the same magnitude defect.

The candidate changes only closure admission to dgamma>0 AND abs(residual)<=the existing tolerance. The initial residual is positive for an entered yield branch; with supported E>0, nonnegative hardening and positive flow, the bracket contains a positive return and the existing safeguarded Newton/bisection update produces it. The next closure evaluates flow and hardening at the updated alpha. Stress sign, ep+=sign*gamma, alpha+=gamma, flow scaling, copies, entry tolerance1e-9, closure1e-8, roundoff allowance and30-iteration refusal remain unchanged. No further blocking branch/sign/history error was found in this bounded delta.

The14 new parameter cases independently check exact affine returns for tension/compression, perfect plasticity and both piecewise-hardening segments, a knot and final flat extension, with fixed nonzero old plastic strain/alpha and scale1.25. The sub-Pa finite-difference samples are explicitly verified to remain inside the previously defective entry/closure interval, so they discriminate the old wrong tangent rather than averaging across the yield gate. Exact stress/history eight-ULP checks, analytic tangent checks, finite shape checks and actual input preimages are meaningful. Boundary factors below entry and inside/above closure retain the original policy. The constant-curve case exercises perfect plasticity; it does not separately execute curve=None, whose sy/H branch is algebraically the same here.

Scope remains approximate nonlinear return-map consistency at the existing finite tolerance. This repair does not prove exact algorithmic differentiation for arbitrary smooth nonlinear curves or a perturbation crossing a hardening knot; no curve/tolerance policy was changed. It also does not establish nonlinear target completion or current-candidate restart/global regression acceptance.

Receipt beam-return-positive-oracles binds the exact hashes below and records14 passed/60 deselected,4.4467351s process wall. This reviewer inspected the receipt/source; no numerical execution was performed.

| File | SHA256 |
|---|---|
| src/anysolver/elements.py | A995FE1B6C21F130AA36E7262A6AE528D07E60228B1F2D67FF18029BD7D1BAF6 |
| tests/test_nonlinear_beam_shell_slice3.py | 9DB4535547E80E09BE22B370F3EC14E33E2A4E27E8E1336E7902A3E00E72195A |
| src/anysolver/nonlinear_static.py, reverted resolution experiment | 8C545E86969ED8AB7090E586E59B174F67B7448A409D6D8C361C264D23E91E1F |

## Plastic-history eligibility and optional full-Newton fallback — 2026-10-19

Routine integrated non-author Read delta, no imports/numerical jobs/tests/workers or product/test edits. No new blocking mechanics/state defect was established. The fallback remains experimental and subject to the root's explicit both-target/current-check keep-or-revert condition; source review is not acceptance.

### Kept eligibility base

At NS45FD0DC5.../testBD3A0899..., residual-merit search is enabled only when the current main-iteration trial or committed history has a positive finite alpha envelope. The current trial is evaluated before the search; persistent storage returns NonlinearStateTrialView, whose values materialize that actual candidate generation. The gate does not commit it or replace committed history. Elastic branches take the first chart-admissible Newton factor, while typed chart refusals still halve through at most8 trials. Synthetic controller tests now explicitly supply positive history when they intend to test postyield behavior. Three eligibility fixtures distinguish elastic, committed-positive and trial-positive sources and inspect caller history. No threshold, state schema, Newton/interval limit or success criterion changed.

Receipts bind this kept base: elastic-legacy-eccentric-completion records1 passed in8.3422303s process wall; elastic-merit-final-source records69 passed/1 portable-only skipped in62.8681946s. These are measured scoped results, not full nonlinear-target acceptance.

### Experimental fallback consistency

The current fallback records alpha1 admissibility and finiteness separately. Only a full candidate that was actually mapped and assembled with finite u,lambda,internal/external forces,reduced residual and merit can bypass residual-dominated no-improvement failure after the bounded trial set. A chart-refused or nonfinite full trial cannot supply that permission. It retains the full original delta as the next *uncommitted* q/lambda iterate, rather than committing the constitutive payload from that force-only evaluation.

The last rejected smaller trial may remain the pending state candidate, but the next Newton iteration reassembles from committed history at the selected full q/lambda and replaces that pending generation before equilibrium admission. If the iteration budget ends first, the existing failure path discards the pending candidate and restores the attempt's q/lambda. No new snapshot or history commit occurs merely because the fallback is used. Existing40-iteration,8-cutback,257-partial,positive-progress,cancellation and typed/unrelated-error boundaries remain. This is nonmonotone Newton continuation, not a proof of descent/global convergence or absence of limit cycles. The updated source properly qualifies the Newton merit-slope statement by the selected directional branch.

The irreducible synthetic residual now follows the adopted uncommitted fallback until the bounded outer failure. Its terminal reason is minimum_control_step_reached after maximum-iteration retries; changing the test expectation to that existing outer classification is consistent with the new route. Failure still must retain zero accepted records/snapshots and the original physical displacement/history.

### Focused fixture failure requiring repair

Inspected postyield-full-newton-focused-2 is1 failed/5 passed,17.0730751s. The new conservative-kink fixture's full step ux=-1 collapses an actual Q4 before its wrapper can replace real element forces, causing the legitimate near-zero-Jacobian ValueError. This is a fixture-domain error, not evidence the product should catch arbitrary ValueError. Scale the synthetic coordinate into small physical displacements (e.g kink−1e-4, root−3e-4, slopes scaled by1e4), preserving the same force shape/exact tangent and all nondescending fractions. Keep the nonfinite-full twin and existing failure assertions. Root was notified; no measured pass for that repaired fixture is claimed here.

Captured current source/test hashes:

| File | SHA256 |
|---|---|
| nonlinear_static.py, kept eligibility base | 45FD0DC5C05562AC96683FCCA477E723FBCCD63BF0BF00000F99157832B8D25F |
| slice3 source test, kept eligibility base | BD3A0899C110C03F94FA560E97D3304461DB1FE036437483C95BECAD2A093188 |
| src/anysolver/nonlinear_static.py, experimental fallback | 9D6E608DD2AFC1528134357C6243CDEF30C402D630B75BFC2FCA6B8C1AF10386 |
| tests/test_nonlinear_beam_shell_slice3.py, fixture state inspected | 4403141D0DAA8962416D7108D57CBEC8C3B6B592A8DCA969DFBE364F18A7D05B |

Both failed focused receipts and the exact fallback base are preserved. Remaining required physical targets/restarts/matrix/regression evidence must bind whichever candidate is finally retained; the ongoing experiment does not renew or waive those obligations.

## Frozen nonmatching e.002/60-degree analytical sequence — 2026-10-19

Routine non-author scientific Read assessment of the three integrated-final-arc-nonmatching-e0.002-a60-n{8,16,32}/result.json records, frozen arc builder, oracle and summary. No numerical FE jobs/imports/tests, source variants or source/test edits. No definite equation/build/acceptance implementation error was found. The assessed group fails its registered accuracy and refinement gates.

With As=1e-4,Ab=2e-5,Is+Ib=1.5e-11,E210GPa,e.002, the centroid rigidity is3.15Nm², eccentric addition14Nm², totalB17.15Nm² and zbar=e/6. The signed force pair, centroid moments, reference-length curvature and centroid radii in arc_reference.py are consistent with the adopted engineering-strain continuum. Nu0, exact common ux/uz/ry per shell x-row, fixed uy/rx/rz and root row are implemented. Shell resultant weights sum1 and work through the common row motion. At the final beam station the zero interpolation weight is removed, leaving a direct endpoint map; hence endpoint load equivalence is unaffected by interior nonmatching stations.

At any actual planar tip angleθ, the endpoint pair produces My=λ*φ*[3.15+14cos(θ−φ)] for L1, plus zero net force. Atθ=φ this isBφ=17.9594380030Nm. Recorded moments17.8744834133/17.7531522294/17.9584924837Nm match the respective measured overrotations. Coarse cases therefore carry slightly less torque than the target arc; an accidental load increase does not explain their greater rotation. The sub3e-13 wrench errors establish balance of those actual applied moments. They do not establish curvature/strain-field accuracy or equality toBφ at an inaccurate returned angle.

For the ideal constrained rod, the dead-pair ramp may be parameterized by Bθ/L=λ*κ_target*[3.15+14cos(θ−φ)]; it is notθ=λφ. No path assumption or moment refit is needed for the terminal oracle. Finite-element intermediate/discrete fields need not satisfy that uniform-curvature relation.

One documentation precision issue: analytical_derivation.md says the objective mean may introduce higher-order orientation interpolation error on this commuting family. The retained two-master shortest-geodesic mean is exactly the weighted Ry angle on its admitted single-axis chart. It adds no orientation-interpolation error for the ideal circular field. Translational interpolation still samples shell chords, not arcs, and the beam chords span a different mesh. These kinematic/energy approximations can matter, particularly when chord-strain errors compete with the small eccentric axial strain. That is a plausible discretization mechanism, not an established diagnosis of this sequence.

The records show shell/beam tip errors at nx32 of1.0823619%/1.0831847% and rotation error1.0845401%, all above the strict1% limit. The nx16→32 changes normalized by the finer solution are14.7068441%/14.7192038% in tip vectors and14.7931345% in rotation, far above0.25%. No rounding-to-pass is appropriate. The summary code uses the correct finer normalization and requires both centroid tips/rotation. Completion, tiny independently reconstructed residual and passed constraints are necessary but insufficient for these accuracy gates.

The nonmonotonic8→16→32 errors do not establish an asymptotic order, Richardson error estimate, a monotone convergence trend, oracle invalidity, instability, collapse, or a unique implementation defect. They are consistent with underresolved competing discretization errors or different discrete equilibrium branches; tips and global wrench alone cannot distinguish those possibilities. A matching/nonmatching and e0/e.002 comparison from the already-planned matrix is useful localization evidence without changing inputs. Field-level strain/curvature, state/energy and branch evidence would be needed before attributing a specific cause. No rerun, load correction or new numerical campaign is authorized by this report.

The registered prospective extension predicate checks the latest two assessed levels: nx32 has smaller principal error than nx16 and their refinement change remains unmet, so this group satisfies that particular eligibility condition for the next ordered level. That is neither convergence proof nor permission to bypass remaining execution limits, earlier failures or final gates. The earlier8→16 worsening remains evidence.

Frozen record identities inspected: corotational.pyB56EF19E031FEC90F8E55CE076E335EBA050954460F3DDEAE55DA35682515A5A; elements.pyA995FE1B6C21F130AA36E7262A6AE528D07E60228B1F2D67FF18029BD7D1BAF6; nonlinear_static.py45FD0DC5C05562AC96683FCCA477E723FBCCD63BF0BF00000F99157832B8D25F; arc_reference.pyB9D241FD547DCC9F53ED1D1911C22A81F4AFC62F10B1442820E83A55329059DE. The experimental postyield full-Newton fallback is absent from this retained source. No final acceptance claim follows from this assessment.

## Manufactured nonmatching constant-curvature patch — 2026-10-19

Independent focused Read check, no imports/FE jobs/tests or product edits. The proposed patch derivation is correct and applies to the small-amplitude limit of the retained beam/MPC route. It identifies coupled trace/quadrature compatibility error; it does not by itself prove an incorrect MPC compiler or quantify the computed nonlinear cantilever stiffness.

Take shell stations0,h,2h with v_i=κx_i²/2 and ψ_i=κx_i. The implemented linear translation trace at beam stations0,2h/3,4h/3,2h gives v_b=(0,κh²/3,κh²,2κh²). Rotation interpolation gives ψ_b=(0,2κh/3,4κh/3,2κh), exactly linear. For beam lengthℓ=2h/3, every element has curvatureΔψ/ℓ=κ, but γ=Δv/ℓ−(ψ_i+ψ_j)/2 is(κh/6,0,−κh/6).

The actual elastic Timoshenko matrix decomposes into EI*ℓ*Bκ.T*Bκ plus S_eff*ℓ*Bγ.T*Bγ, where S_eff=12EI/[ℓ²(1+φ)] and φ=12EI/(Sℓ²). Thus the added shear energy over2h is

U_extra = 2*(S_eff*ℓ/2)*(κh/6)^2
        = S_eff*κ²*h³/54
        = EI*κ²*h/[2(1+φ)].

The constant-curvature beam energy over2h is EIκ²h; the imposed-patch increment is therefore1/[2(1+φ)] of that beam energy. For the benchmark's local-z displacement/ry convention, set v=−uz and ψ=ry: the implemented shear strain has the opposite sign, leaving the same positive energy. The other bending plane uses Iz/G12 instead of Iy/G13 and has the identical conclusion.

At e0 the translation MPC is exactly the weighted master displacement; on the admitted commuting rotation field the mean is exactly weightedψ. The generic corotational wrapper has the same linearized energy, so removing the chord frame does not remove this first-order shear mismatch. In the slender-element/preasymptotic rangeφ≪1 the relative patch penalty approaches50% of the beam's imposed bending energy. At fixed physical section, h→0 makesφ grow and the penalty vanish; a small geometric interpolation error need not be a small energetic error before that regime.

The master displacement trace itself is piecewise linear and cannot represent the exact quadratic curve between shell nodes. The MPC faithfully samples that trace. The counterexample therefore demonstrates a compatibility failure of the coupled discrete trace/integration spaces to preserve this no-shear bending patch, not an algebraically false interpolation of its declared master field. Actual retained DOFs may relax through microadjustments, axial strain or finite-geometry effects, and shell energy/load interaction matters. The measured concentric30-degree rotations0.3323223/0.4169868 at nx8/16 are below targetπ/6, consistent with the sign of added energy, but the formula is not an exact stiffness or full-error prediction for those equilibria.

This is a useful next implementation question: should the admitted nonmatching retained trace reproduce a constant-curvature/no-shear patch while preserving rigid motion, work conjugacy and the stated mechanical reference? Adopting a different trace is a root-owned contract/design decision, not authorized here. No benchmark ratio, load, tolerance or failure evidence should be changed to hide the patch defect. All preceding nonmonotonic-refinement/branch-interpretation cautions remain. Further blind refinement alone cannot identify this mechanism as the exclusive cause.

## Final frozen-candidate evidence delta — 2026-10-19

Bounded routine non-author Read reconciliation, not a repeat of the requested Astra-high review. No imports, numerical jobs/tests, workers, source/test edits or Git mutations. Current files match frozen candidate514478af3453a8af17a35cd8cb34ad577d648174f02b071eba9c984c7501d21b. No additional blocking source/lifecycle defect was established beyond the measured open scientific and verification gates. Experimental16-cutback/full-Newton fallbacks are absent. Earlier source findings in this living report must be read with their later closure/reversion entries.

Inspected current-identity receipts: integrated-v2-standard364 passed; slice-core-fast87 passed; coupling-fast16 passed; original coupling route force2, direct/interpolatedDC1each and split-restart1each passed; continuation-smoke8 passed. These are scoped current-source/test results. They must not be summed into complete486-ID coverage until root reconciles selected identities, partitions, overlap, failures and terminal pending runs. The manifest records two modified historical coupling function ASTs (reduced tangent FD and cantilever/wrench case); therefore describe passing current regression cases, not universal byte-for-byte preservation of every original test. The adopted fixture/differential changes have been reviewed previously; this is claim precision, not a new gate.

integrated-v2-continuation-full is terminal with2 failures in271.4955942s process wall. Direct returns stopped_at_limit/line_search_no_improvement at control−.16666666666666666,lambda2.7040043630174004,relative residual4.08866593039587e-12 and11 accepted states. Interpolated returns the same computational failure class at−.17160237630208333,lambda3.3625994229175626,relative residual7.763380678425667e-12 and14 accepted states. Source ordering in _assert_completed_dc_case confirms all25 accepted states passed the required achieved-load residual, actual constraint summary, physical wrench and exact reconstruction/snapshot/input immutability checks before the completed-status assertions failed. All25 raw artifact paths named by the receipt stdout exist at review (11direct/14interp).

These results support consistent accepted partial equilibria and honest incomplete-target reporting. They do not establish−.20 attainment, a physical collapse/load limit, root nonexistence or a successful full-history restart to the required target. The legacy public converged flag includes stopped_at_limit; status=='completed' plus target attainment remains essential for success claims. Current tests correctly keep that distinction. Continuation restart/cancellation evidence was still pending in the supplied final delta, and no pass is inferred for it from original coupling restart tests or the smoke suite.

The nonmatching eccentric60-degree analytical group remains an accuracy/refinement failure despite all three levels equilibrating; the prior interpretation/patch assessment in this report remains applicable. The matching concentric30-degree nx32 receipt is TIMEOUT300.2795606s, with empty stdout/stderr and no result, so it supplies neither an accuracy result nor a physical/formulation-failure diagnosis. The provided17/24 analytical completion count and pending mesh matrix are not full analytical/mesh acceptance. No source repair, new oracle, tolerance change or unchanged-case retry is proposed by this review.

Actual current reviewed SHA256:

| File | SHA256 |
|---|---|
| src/anysolver/nonlinear_static.py | 45FD0DC5C05562AC96683FCCA477E723FBCCD63BF0BF00000F99157832B8D25F |
| src/anysolver/elements.py | A995FE1B6C21F130AA36E7262A6AE528D07E60228B1F2D67FF18029BD7D1BAF6 |
| src/anysolver/corotational.py | B56EF19E031FEC90F8E55CE076E335EBA050954460F3DDEAE55DA35682515A5A |
| src/anysolver/_corotational_batch.py | AC005ABC5D060951DA75B206F5CCBC122BC93B733F373E06BAF998ED67B2C7E2 |
| tests/test_nonlinear_beam_shell_slice3.py | BD3A0899C110C03F94FA560E97D3304461DB1FE036437483C95BECAD2A093188 |
| tests/test_nonlinear_beam_shell_slice3_continuation.py | 85A2387F26D40D612C5F0B1D317D56291DD51815910768608CD70E65010A48FE |
| current coupling regression module, manifest | 7B7C880A0E61F0D4AA496C796CBD3185A0517786D650D4667982D708BCF118C5 |

Review limits: this delta inspected source/evidence and carried forward prior independent mechanics derivations; it did not rerun numerical checks or establish final acceptance. Root retains count reconciliation, scientific acceptance and delivery authority. Slice3 remains incomplete under its unchanged gates.

## Final evidence-only cross-summary addendum — 2026-10-19

Read only the five requested final JSON summaries/mapping; no source rereview, numerical jobs/imports/tests, workers or Git mutations. Their gate/coverage/source claims are mutually consistent. No unsupported overall acceptance claim was found; withholding Slice3 acceptance is correct.

Regression:486 collected identities reconcile arithmetically to481 passed/5 failed, with zero skipped/errors/xfail/xpass. The five failures are2full-target,2continuation-restart and1cancellation test. The summary reports exact nonoverlapping ID coverage, terminal matching counts, selected-test/product identity and effective-runtime checks, while explicitly setting both success checks and passed=false. This is complete reported execution coverage with failures, not successful qualification. This bounded addendum checks those summary claims against each other; it does not independently re-audit all underlying test IDs or receipts.

Mesh: all12 requested cases are reported complete/equilibrated under one product/oracle identity; registered R4 linear-envelope, M/P last-change and finest M/P gap checks pass. M/P nonmonotonic earlier sequences are explicitly retained. A passing mesh summary does not resolve the separate analytical or continuation gates.

Analytical: execution index has24 required/attempted cases,20 terminal result records and4 timeouts; the24 rows agree with those totals and all identify the frozen product. The four concentric nx32 timeouts have no terminal result and are consequently absent from the arc summary's assessed levels. The summary's all_assessed_cases_complete=true therefore means the present result records only; base_levels_present=false prevents those incomplete groups from passing. Overall arc passed=false is consistent. Only the two matching/eccentric groups pass; nonmatching eccentric groups fail accuracy/refinement, and concentric groups remain incomplete or additionally inaccurate. No failed/missing case is silently promoted to success. These final20/24 counts supersede the earlier17/24 in-progress observation.

Candidate mapping: numerical514478af3453a8af17a35cd8cb34ad577d648174f02b071eba9c984c7501d21b maps to handoff510cd64921c635f71ff80a8b000b9318531243298968995f8b5cb1f2aecf3f70 with zero changed prior inputs and exactly two added observer scripts (final_arc_trace.py,final_mesh_trace.py), accounting for778→780 selected inputs. The stated unchanged physical product/tests is consistent with the same-frozen-product/identity checks in the other summaries. Do not describe the complete manifest digests as identical; the mapping explains their artifact-only difference.

No new acceptance oracle, tolerance, retry, source change or gate waiver is proposed. Current final evidence supports a passing registered mesh matrix and broad regression execution coverage, while regression/continuation and analytical gates fail or remain incomplete. Scientific acceptance remains withheld.

## Scientific design boundary: nonmatching bending-trace compatibility — resumed Slice3

Independent bounded Read/design consultation; no imports, FE/numerical runs, workers, Git mutations or product/test edits. The current public rotating_eccentricity keyword defaultsTrue, False retains its declared fixed-reference law, and zero eccentricity retains the legacy linear constraint route. These are protected compatibility requirements. This consultation proposes equations for root adoption, not an implementation or permission to change those contracts.

### What is and is not broken

The existing compiler correctly enforces its declared pointwise piecewise-linear translational trace and weighted rotation trace. The manufactured γ=(κh/6,0,−κh/6) follows uniquely from those constraints. Existing Beam2 elastic stiffness is the exact standard Timoshenko stiffness for its supplied endpoint values and assigns positive energy to that γ. Its condensed auxiliary shear term is already consistent; this is not another version of the repaired uncondensed fiber auxiliary defect.

It is impossible to retain those exact constrained endpoint data, retain the same positive Beam2 shear energy, and make this imposed patch's shear energy zero. A universal beam-only subtraction would also remove legitimate isolated-beam shear when that beam is given the identical endpoint displacement/rotation vector. Changing shear quadrature alone cannot erase the nonzero mean γ while preserving constant physical shear. Changing rotations to match each chord sacrifices the linearly exact director/constant-curvature field. Therefore the principal unresolved issue is compatibility of coupled displacement/director traces and their integration spaces, not a demonstrated MPC algebra error.

### Compatible small-rotation candidate

For a straight two-master reference edge of lengthh, material coordinateξ∈[0,1], transverse displacementsv0,v1 and section rotationsψ0,ψ1, use

v_tilde(ξ)=(1−ξ)v0+ξv1−(h/2)ξ(1−ξ)(ψ1−ψ0),
ψ_tilde(ξ)=(1−ξ)ψ0+ξψ1.

Then v_tilde'−ψ_tilde=(v1−v0)/h−(ψ0+ψ1)/2, a constant. It reproduces the quadratic zero-shear bending patch exactly and preserves constant physical shear, axial affine motion, endpoint values and infinitesimal rigid motion. This is a compatible displacement/director enrichment, not automatically a Kirchhoff assumption. Ordinary cubic Hermite displacement tied to rotation slopes instead forces zero endpoint shear and needs additional care for the declared shear-deformable physics.

### Objective finite-rotation candidate

A stronger two-master trace follows by integrating the SAME intrinsic director interpolation. Let current master positions be r0,r1; rotationsR0,R1; ψ=Log(R0.T R1) on the supported unique relative-angle branch; R(ξ)=R0 Exp(ξψ). Define

A(ξ)=∫[0,ξ]R(s)ds = ξ R0 J_l(ξψ),
A1=A(1),
ν=A1^−1(r1−r0)/h,
r_trace(ξ)=r0+h A(ξ)ν = r0+A(ξ)A1^−1(r1−r0).

Here J_l is the left SO(3) Jacobian with the positive-skew convention. A1 is nonsingular on the existing relative-angle<π domain. The derivative is r_trace'=hR(ξ)ν: the local material axial/shear vectorν and body curvatureψ/h are constant on the reference edge. For ν=λa (reference unit tangent a) and planar constant curvature it reconstructs the circular trace exactly, including constant axial stretchλ. Constant director with arbitrary affine axial/shear displacement is also reproduced. Initial zero rotations recover the straight reference edge exactly. Under r_i→Qr_i+c and R_i→QR_i, ψ is unchanged, A→QA, ν unchanged and r_trace→Qr_trace+c. Its small-rotation transverse expansion is precisely the quadratic candidate above.

For a rotating offset e, beam-centroid position would be r_b=r_trace+R(ξ)e and beam rotationR_b=R(ξ). This preserves the declared section offset mechanics, but replaces the interior shell connection trace. It is a new interpolation/discretization candidate, not an exact representation of the old piecewise-linear midsurface field. It is initially scoped to a straight two-master edge with known materialξ and reference geometry; arbitrary multi-master/bilinear surfaces require a separate definition/admission decision.

### Adoption and integration boundary

The enriched/integrated trace changes slave translations even whene=0. Enabling it only fore≠0 would leave the concentric patch unresolved and create a discontinuous connection as e→0. Therefore it cannot transparently replace the protected zero-offset/default linear behavior. A new opt-in trace mode or new coupling type can preserve existing defaults, including rotating_eccentricity=True and False semantics. Selecting that mode in qualification requires explicit root adoption of the reconstructed mechanical trace while retaining benchmark geometry, mesh ratio, loads, materials, reference and tolerances. If all existing public inputs/trace behavior must remain exactly unchanged, this compatibility error cannot be removed by a source-only algebra fix; that is a genuine contract boundary.

A new trace also requires a complete kinematic map implementation: position derivatives are now matrix endpoint weights depending on rotation, not the old scalar weights. Derive forces from its full Jacobian transpose, including new endpoint moments; derive the complete frozen-imbalance Hessian, including translation/rotation cross terms. Current lever-only optimized pullback and rotation-only geometric Hessian cannot simply be reused. Inverse/postchecks, physical reaction transfer, direct endpoint limit, downstream-dependency refusals, linearization at the reference state, model fingerprints and restart admission must describe that same map. Zero-offset opt-in traces would need active nonlinear-map admission even though the legacy zero-offset path remains linear. This entails a connected coupling/compiler/driver/recovery design slice owned by the implementation owner after root adoption.

An alternative retaining pointwise linear MPCs is a coupled variational/assumed-shear projection onto compatible host-edge strain modes. It may suppress the artificial oscillatory γ while retaining constant physical shear, but changes the discrete energy/operator and can introduce null/hourglass modes; it is not a universal Beam2 constitutive repair. Such a design also needs root adoption and independent coercivity/work checks.

### Discriminating evidence before broad execution

First show the old/new prescribed patch operator energy, constant shear/stretch preservation, exact endpoints and finite circular-trace reproduction without a nonlinear solve. Check arbitrary SE(3) covariance, mixed-axis virtual work, Jacobian/Hessian and physical wrench transfer, unsupported-chart/topology refusal and input/state ownership. Then retain matching/direct/zero-offset/False default regressions and assess the unchanged registered mesh/arc matrix under the explicitly adopted formulation. Do not infer exact global stiffness or sole causality from the imposed patch; free DOF microadjustment, axial relaxation, finite geometry and possible discrete branches remain relevant to the measured nonmonotonic sequence. No load/material/tolerance fit or blind finer-mesh recommendation follows.

## Adopted director-integrated trace: analytic position differential — 2026-10-19

Read/design support only for root's explicitly adopted opt-in straight two-master trace; implementation remains with the connected owner. No imports, tests, FE/numerical jobs, product/test edits, workers or Git mutations. Equations were sent directly to the owner. This is not another Astra-high progress review or an implementation/acceptance claim. Existing default/zero-offset linear trace and rotating_eccentricity semantics remain protected; opting into the reconstructed trace is the adopted contract change.

Use [v]w=v cross w, Ri=Exp([theta_i]), Ji=Jl(theta_i), psi=Log(R0.T R1), H=Jl(psi)^-1 and material xi in [0,1]. The existing _rotation_right_jacobian(-v) supplies the positive-skew Jl(v); _rotation_left_jacobian_inverse has the corresponding convention. Put F=xi Jl(xi psi) H, Q=R0 F R0.T, d=r1-r0, a=R0.T d and rxi=r0+Qd. For additive rotation coordinates, spatial spins are wi=Ji delta_theta_i, and

    delta_psi = H R0.T (w1-w0),
    DF[eta] = xi { DJl(xi psi)[xi eta] H
                    - Jl(xi psi) H DJl(psi)[eta] H }.

Let M have columns DF[e_j]a, and P=R0 M H R0.T. The exact position differential is

    delta_rxi = (I-Q) delta_r0 + Q delta_r1
                + (Q[d]-[Qd]-P) w0 + P w1.

Thus the additive rotation blocks are (Q[d]-[Qd]-P)J0 and PJ1. The positional blocks are matrix weights I-Q,Q; Q is generally neither symmetric nor orthogonal. For the SAME geodesic director Rm=R0 Exp(xi[psi]), its spatial spin is exactly wm=(I-Q)w0+Qw1. Consequently, for rotated eccentricity b=Rm e, the complete rotational blocks of rb=rxi+b are

    C0 = {Q[d]-[Qd]-P-[b](I-Q)} J0,
    C1 = {P-[b]Q} J1.

This is equivalent to adding the existing offset derivative -[b]Jl(theta_m)G_i, with G_i=Jl(theta_m)^-1 W_i Ji and W0=I-Q,W1=Q. The equivalence is an independent algebraic check on orientation/position integration, not permission to omit the new mixed translation/rotation Hessian terms or reuse scalar-weight reaction transfer.

For stable DJl, set s=psi dot psi, t=sqrt(s), W=[psi], E=[eta]. Then Jl=I+A W+B W^2 and

    DJl[eta] = A E+B(WE+EW)
               +(psi dot eta)(Astar W+Bstar W^2),
    A=(1-cos(t))/t^2, B=(t-sin(t))/t^3,
    Astar=(t sin(t)-2(1-cos(t)))/t^4,
    Bstar=(3 sin(t)-t(2+cos(t)))/t^5.

The removable-zero series are

    A     = 1/2-s/24+s^2/720-s^3/40320+O(s^4),
    B     = 1/6-s/120+s^2/5040-s^3/362880+O(s^4),
    Astar = -1/12+s/180-s^2/6720+s^3/453600+O(s^4),
    Bstar = -1/60+s/1260-s^2/60480+s^3/4989600+O(s^4).

A direct small-W cross-check is F=xi I+c1 W+c2 W^2+c3 W^3+..., where c1=xi(xi-1)/2, c2=xi(xi-1)(2xi-1)/12, c3=xi^2(xi-1)^2/24. At psi=0, P=xi(1-xi)[d]/2 and Q[d]-[Qd]=0. At the undeformed reference,

    delta_rxi=(1-xi)delta_r0+xi delta_r1
               +xi(1-xi)[d](delta_theta1-delta_theta0)/2.

For d=h ex and positive relative ry, this correction is positive uz, hence negative v=-uz: it matches the previously derived compatible bending enrichment. The rotational blocks vanish exactly at xi=0,1; explicit endpoint branches avoid cancellation. Equal finite master rotation also gives Q=xi I but retains nonzero differential response to unequal endpoint rotation increments: a shortcut returning a constant-Q Jacobian there would be incorrect.

Jl(psi) has singular values 1 and 2sin(t/2)/t twice. On 0<=t<pi its condition number is below pi/2, so the integration inverse has no hidden singularity approaching pi. The Log cut locus remains a distinct admission boundary; retain relative-angle/principal input-output chart refusals and domain-safe derivative stencils. Close-to-pi matrix-to-log extraction can still require the existing stable branch. No widened chart, deformed-coordinate re-projection of material xi or extrapolation is adopted here.

The fixed analytical terminal loads and continuum reference remain applicable to this explicitly reconstructed host trace. Constant planar director curvature and constant material axial stretch integrate to the same shell circle; adding Rm e produces the same offset circle. Endpoints and endpoint directors are unchanged, so final-tangent dead constituent forces, centroid moments, neutral-axis section properties, radii and terminal work equivalence require no fitting or rescaling. The dead-load ramp is still not a circular-arc continuation path. Finite Beam2 chords/strain interpolation and shell discretization remain approximations, so exact continuum reproduction by the trace does not prove the analytical error/refinement gates or erase prior failed legacy-trace evidence. The benchmark must explicitly select the adopted opt-in mode; no silent replacement of legacy/default behavior is justified.

## Integrated opt-in director trace: non-author source/evidence review — 2026-10-19

Bounded Read review of the integrated candidate and entry-baseline diffs, not another Astra-high progress review. No imports, tests/FE jobs, workers, product/test edits or Git mutations. Root retains adoption and final acceptance. Reviewed SHA256: _director_trace.py EB2CECE1AC8FDC008CB7FB75878FBA7319867CE7D7F57405A97C9575FDB9A337; corotational.py FB0BAEEA6D7A55E4BBBDFE00241A5F723D93D8E33D39A28593F80511205DE248; mesh_gen.py 18DA64E0DB1AB1C6BA947DE29B0A81792704F53A19E24D07C4BA0C66B67775CA; nonlinear_static.py 1A7510F2D44EB400B3758641932B09825B5FCA1F3DD5337347891FCD8689B292; tests/test_director_integrated_trace.py CBB913C61A07CFAF39299F44511C89DC95DB3B7779C23032D5E091C1EAE5BECF.

### Actionable compatibility finding

The new unconditional public self.connection_trace='linear' at mesh_gen.py173 changes V1 model fingerprints for otherwise-identical newly reconstructed legacy/default interpolated couplings. nonlinear_restart.py501-537 serializes every public vars entry, and1112-1113 rejects a mismatched model fingerprint. Entry-baseline objects lack this field. Therefore an existing baseline checkpoint cannot be consumed by the same default model reconstructed through the new constructor solely because a mechanically inactive default attribute was added. This is a confirmed fingerprint delta; whether historical checkpoint compatibility is mandatory is root's public-contract decision. No explicit adoption of this default-route refusal was found. Preserve legacy canonical identity (while binding the opt-in policy), or explicitly adopt/document migration/refusal. A discriminating test compares baseline/default model fingerprints or an actual baseline checkpoint against the newly reconstructed identical default model, plus retention of opt-in/wrong-policy refusal. The current same-source checkpoint test does not distinguish this regression. Sent directly to owner and root before handoff.

### Integrated mechanics checked

No additional concrete mechanics defect established. The helper differentiates both endpoint rotations to second order with forward jets; its analytic mixed u/theta blocks have the required -dQ/+dQ signs and symmetric placement. Reference constraints use the same six-output reference Jacobian, including zero-offset rotational contributions. The nonlinear-minus-reference correction, full B-B0 Jacobian, complete contracted six-output Hessian and upstream T pullback are consistently connected at corotational.py1543,1588,1681. reduce_force deliberately falls back to full J.T when any new trace exists; physical reaction transfer uses the full B.T before zeroing slave entries, rather than scalar translation weights. Inverse correction observes unchanged masters; existing downstream translation/nonlinear-rotation guards remain applicable. The old linear/default and rotating_eccentricity=False mechanical branches remain untouched apart from the public attribute/fingerprint issue above.

Geometry admission copies reference inputs, requires distinct one/two masters, nonnegative unit weights, positive two-master span and slave/edge/offset agreement. Interior zero-offset opt-in maps stay active; endpoint limits use the existing direct law. The descriptor cache keys the exact master state and keeps private read-only reference arrays, without constitutive history. The caller checks the existing shortest-relative-geodesic and principal input/output charts before the private helper, then checks finite value/J/H; the helper alone is not a public domain-admission API. Non-corotational nonlinear execution explicitly refuses this mode. I found no changed material commit/rollback service in this delta.

### Evidence and limits

Saved evidence/director-trace-final-invariants-2/receipt.json matches all five reviewed hashes above and records45 passed, exit0,8.87905150000006s process wall, source import rooted in this checkout, single worker and JIT off. Inspected tests include actual Beam2 imposed-patch energy, affine physical shear/axial preservation, exact circular trace/endpoints, independent fourth-order value/J differential checks, mixed Hessian symmetry, SE(3) covariance, master-order reversal, inverse, full force reduction/geometric tangent/wrench, reference T0, invalid topology/policy/reference geometry, input no-mutation, public elastic solve and copied/serialized restart with wrong-policy refusal. They support these scoped invariants; they do not establish the arc matrix, postyield continuation or Slice3 acceptance.

The near-pi derivative parameterization sets BOTH masters to the same near-pi absolute rotation; it exercises the output absolute log chart, with relative angle zero. It does not independently exercise the new relative-log Hessian near its pi boundary. A focused additional witness can choose theta0=-(pi-epsilon)/2*a and theta1=+(pi-epsilon)/2*a, so the relative angle is near pi while absolute inputs and the interior mean remain well inside their charts. This is a specific coverage limit on any claim that both near-pi logarithms were tested, not a newly invented acceptance gate or a proven failure. Cancellation coverage in the new public fixture is pre-cancelled elastic restart; no new mid-iteration/plastic-history proof is inferred. The paired registered arcs were active during review; no paired success or final acceptance is claimed here.

Root subsequently adopted the narrow compatibility repair: class default connection_trace='linear', with an instance attribute only for nondefault policy; baseline-style checkpoint compatibility and opt-in wrong-policy refusal must be checked after the active paired arc. No general fingerprint relaxation or migration was adopted. This review's named hashes precede that repair, so the finding is decision-resolved but not yet source/evidence-closed here. Root reports nx8 completed/equilibrated with approximately17.1% tip/rotation error; nx16 remained pending. That result does not satisfy the unchanged accuracy gate and supplies no authority for a broad matrix or reference/tolerance change.

## Closure of two trace-review deltas — 2026-10-19

Narrow Read closure only; no new full review, imports/jobs/tests/workers or product edits. Legacy fingerprint finding CLOSED for the new policy addition: mesh_gen.py155 provides class default connection_trace='linear', and constructor only stores a nondefault instance value. Implicit and explicit linear construction therefore retain the entry-baseline public namespace used by V1 fingerprinting, while director_integrated remains fingerprint-bound. Current test_baseline_style_linear_checkpoint_and_explicit_linear_identity actually creates a checkpoint from the baseline-style namespace, reconstructs default-constructor elements, verifies identical fingerprints and consumes the native checkpoint to completed displacement agreement. This is scoped preservation of the prior namespace, not an assertion that an independently archived historical binary checkpoint was exercised. Existing opt-in/wrong-policy checkpoint refusal remains covered.

Relative-near-pi coverage delta CLOSED: the new witness uses opposing half-angle rotations with relative angle pi-2e-6, tests value/J and J/H directional derivatives with tangential perturbations avoiding the cut, and exercises compiled map admission. The new mode performs its own stable jet-domain admission and translates DirectorTraceDomainError into the driver's typed SO3MeanDomainError; the legacy SO(3) mean remains unchanged. Both absolute endpoint vectors, the computed relative vector and returned mean retain principal/relative chart limits. This closes the specific missing near-pi relative-log witness, without claiming exhaustive boundary directions.

Reviewed final identity manifest director-trace-owner-final-identity.json and actual closure inputs: mesh_gen.py84D79D14E8DDF7FDEAFB6B5DF7BE631BC3307CC708440934DA1974A896E9BB11; corotational.py798C194A1D4FE00518E397E222A289D2432CCCD3E0FB9BEF2B56F5C878B2EF80; _director_trace.pyAA02F34D31F2FFC849EDD545851BFACBE51A624DA5110C2CB53373E37716A764; tests/test_director_integrated_trace.py8359A1DEDB5610E3FAE9020A624653B2B968D1BE435E3FF615766DCB099ACDF7; guide115DEAF28BA19908A4CDC0B87537F6AA17FB70E70B1EF2B6FFBC5D59CEE68A57. Actual hashes of the changed mesh/helper/test files matched that manifest at review. No inspection of the distinct precision work in progress was undertaken.

Saved receipt and terminal stdout evidence/director-trace-two-repairs records50 passed, exit0,8.249111800047103s process wall, at the same product hashes with earlier test hashF1F7334A3F464D0E8ABC98EC757F5237A0A89807094F97FB73C68CC0E70BF31B. Later director-trace-checkpoint-and-guide-final records2 passed, exit0,8.153051499975845s, binding the final test/guide hashes above and strengthening native checkpoint/default consumption. Do not describe all50 as rerun on the final test hash. These receipts close the two review deltas only; unchanged arc accuracy, matrix and postyield gates remain independent. No Slice3 acceptance is inferred.

## Restricted circular-family chord-strain derivation — 2026-10-19

Independent bounded Read derivation only: no jobs/imports/tests, edits to product, numerical fitting or inspection of the separate precision investigation. This is a hypothesis discriminator for the unchanged analytical oracle, not a new law or acceptance claim.

For uniform reference-length curvature k, host spacing h, beam spacing l=2h/3 and common shell arc stretch lambda, set a=sinc(kh/2), b=sinc(kl/2), sinc(x)=sin(x)/x. Corotational pullback aligns a circular shell rectangle and each Beam2 chord with its midpoint tangent. The resulting local transverse displacement gradient vanishes, so the element's von Karman quadratic gradient correction also vanishes. Shell B_m[0] differentiates axial nodal displacement (elements.py1956); Beam2 axial response uses chord extension/reference length with the documented von Karman correction (4592 onward). Thus the proposed restricted-family engineering strains are compatible with those definitions:

    eps_s = a lambda-1,
    eps_b = b(lambda+e k)-1.

Endpoint rotation differences/reference lengths give bending curvature k. On the cylindrical Q4 field, the MITC transverse-shear sampling at edge midpoints gives zero shear. The Beam2 antisymmetric endpoint bending rotations likewise give zero mean shear and energy EI k^2/2 per reference length. This establishes the axial mechanism without treating all possible stabilization, nonuniform fields or solved equilibria as identical to the restricted family.

Let A=As, B=Ab, I0=Is+Ib, C=Aa^2+Bb^2, g=b-a+e k a b. The candidate elastic energy per original length is

    u(lambda,k)=E/2 [A(a lambda-1)^2
                       +B(b(lambda+e k)-1)^2+I0 k^2].

An essential correction to an unqualified 'zero total axial force' elimination: stationarity with respect to THIS common arc stretch is a Ns+b Nb=0, not Ns+Nb=0, where Ns=EA eps_s and Nb=EB eps_b are chord-conjugate constitutive resultants. The sinc factors follow from differentiating the actual strain measures. Then

    lambda*=[Aa+Bb(1-e k b)]/C,
    eps_s=-B b g/C,     eps_b=A a g/C,
    u_min(k)=E/2 [I0 k^2+AB g^2/C].

The restricted work-conjugate internal moment is

    M_int=du_min/dk
         =E[I0 k+AB(g g'/C-g^2 C'/(2C^2))],
    g'=b'-a'+e a b+e k(a' b+a b'),
    C'=2Aa a'+2Bb b'.

Primes mean differentiation with respect to k at fixed h,l,e. This includes the derivative of the relative chord bias b-a and the curvature-dependent condensation denominator. Replacing it by centroid bending plus e Nb alone drops genuine work terms. No division singularity exists at k=0: a=1-k^2 h^2/24+..., a'=-k h^2/12+..., and similarly for b.

For fixed section/offset and small h,l, put T=A+B, D=(h^2-l^2)/24 and F=(B h^2+A l^2)/(24T). Expansion about the unchanged continuum moment M_cont=E[I0+AB e^2/T]k gives

    M_int-M_cont = E AB/T [3e D k^2-4e^2 F k^3]+O(h^4).

For the concentric case e=0 the first nonzero term is instead

    M_int-E I0 k = 2E AB/T D^2 k^3+O(h^6).

Thus unequal finite chords produce a positive O(h^4) concentric axial penalty on this imposed family, and an O(e h^2) eccentric term competing with an O(e^2 h^2) term. For h>l and sufficiently small positive e,k the leading eccentric term is positive. Slender-section area/inertia ratios can amplify these terms relative to bending energy. This is an unfitted order/sign prediction, not a numerical estimate or an explanation fitted to the measured17.1%.

The final dead constituent forces are equal and opposite, so common lambda variation does zero external work. Under k variation their common shell-tip position contributions also cancel; the surviving external generalized moment is M_s,prescribed+M_b,prescribed+e Nb,prescribed cos(kL-Phi). At kL=Phi this is exactly the original prescribed composite target moment. Away from that terminal angle, the dead-load path is not a uniform pure-moment family. No internal resultant should be substituted for the prescribed force to manufacture load equivalence.

Limits: actual retained equilibria can have station-dependent curvature/stretch and additional discrete modes; the restricted two-variable stationarity is necessary along that family, not sufficient stationarity of the full model. Even a prescribed uniform state may require local balance that this energy derivative cannot establish. Therefore this supplies a concrete constitutive/kinematic counterexample to continuum equivalence at finite spacing and an expected error order/sign; it cannot uniquely attribute the solved coarse arc error or establish physical failure. A discriminating future authorized check would compare prescribed-circle recovered strains/energy and their independent k derivative against these formulas before attributing the observed solution discrepancy. No new execution/refinement authority or oracle/tolerance change follows. Equations were sent to root and the connected owner.

## Stable director displacement arithmetic delta — 2026-10-19

Narrow independent Read review only; frozen stall-capture script untouched, no jobs/imports/tests or product edits. Reviewed actual helper10917826C00673B8BC0C5AFB8BCABA28AF921A37B2180DDC99F795A162AED0DD, test60DF13B36FB461006717F2BE00957A5A088715A16B80B2A49F0D400EF2FAFD68 and guide990BF2F4DBB10EEF94E9E9BAF86967E03ED07132D52F0D666AA28B5268A8A909 against director-displacement-final-identity.json; the other six manifest entries retain the prior trace-closure identities.

No concrete same-map or derivative defect established. For exact rotations, the factored QminusXiI=xi R0[Jl(xi phi)-Jl(phi)]Jl(phi)^-1 R0.T equals Q-xi I. The coefficient factors (xi-1)sum(xi^k,k=0..power-1) correctly compute xi^power-1 for each skew/skew-squared term without subtracting identity parts. RminusI=(R0-I)+R0(Exp(xi phi)-I) is the same R-I. The resulting displacement expression expands exactly to X0+u0+Q[(X1-X0)+(u1-u0)]+R e-Xslave. Replacing cancellation-prone absolute sums and numerical R0 R0.T identity defects changes floating evaluation, not the adopted analytical trace law.

Fraction arithmetic observes the original supplied binary-float reference coordinates, xi, offset and slave; it preserves the actual reference closure X0+xi(X1-X0)+e-Xslave, including a nonzero sub-ulp value. Chord hi/lo retains the reference subtraction remainder before multiplication. No closure is set to zero, no slave coordinate is reanchored and no new geometry fit is introduced. The nonzero-closure witness explicitly expects -2^-54. Complete rotation AD passes through the factored Q/R and both chord parts; manual translation and mixed Hessian blocks remain the same I-Q/Q and -dQ/+dQ. Unchanged mesh compiler and nonlinear-reference subtraction still use this helper's reference Jacobian; a nonzero reference closure remains in the forward correction.

Actual saved director-displacement-stable-contracts receipt/stdout records55 passed, exit0,10.172381999960635s process wall and matches the reviewed helper/test and unchanged product identities. New sub-world-coordinate-ulp witnesses at origins0,.75,1e6 and the explicit nonzero closure complement the retained J/H/work/wrench coverage. This is scoped measured evidence, not an independent high-precision FE oracle.

Actual director-displacement-observed-n16 result/receipt: completed at load1 with12 accepted states,65 observed iterations,51.66222639998887s process wall; independent relative residual1.4791280105755532e-9, passed constraint postcheck, unchanged state inputs and physical My balance4.5116863682694153e-14. Shell u/ry errors0.053043059719240664/0.0530127171843061 and beam u error0.05306014398761937 retain accuracy_passed=false. Guide correctly distinguishes improved completion/equilibrium from the unchanged failed analytical accuracy gate. No trace/refinement/plastic/Slice3 acceptance follows from this arithmetic delta or from the separate capture preparation.

## Fixed-history constitutive-map consultation — 2026-10-19

Bounded independent Read consultation only, not a repeated Astra-high progress review. No Python/imports, numerical jobs, workers, product/test/authority edits, event-ray localization or geometric/arc investigation. Reviewed current candidate e13e9a6b0f78f0697929b7fea2351e8026dbd8cca161e45323071ffe92dec3ca manifest and actual source identities: elements.py4C9F8546E0B0FEDF50C2B918A07C8A5101A47A9635EE9AB4DCAF3A7FAAC5273C; plasticity.py88EF58CAD6C0FBE98A0570F0A7627745BBD3EEADFB313EE11A56A8363381C841; corotational.py798C194A1D4FE00518E397E222A289D2432CCCD3E0FB9BEF2B56F5C878B2EF80. No source repair is authorized or proposed by this consultation.

### Concrete exactness limitation: beam tolerance-band non-idempotence

BeamElement._uniaxial_return_map (elements.py4202 onward) uses trial=E(epsilon-ep_old), enters yield for abs(trial)-s(alpha_old)>1e-9*max(s,1), and accepts a positive return increment once abs(abs(trial)-E*dgamma-s(alpha_old+dgamma))<=1e-8*max(s,1), augmented only by a roundoff floor. The prior positive-dgamma repair prevents the old zero-update/plastic-tangent defect. It does not make a committed approximate return exactly idempotent: a positive accepted closure residual between entry and closure thresholds re-enters yield when the IDENTICAL total strain is evaluated using that just-committed ep/alpha.

An analytic counterexample to exact idempotence of the inspected scalar function is the smooth monotone concave flow law s(alpha)=S*sqrt(1+2E*alpha/S), S>1, old ep=alpha=0, and trial=1.0002S. Initial H=E gives first positive dgamma=1e-4*S/E. The remaining residual is S*(1.0001-sqrt(1.0002)), approximately4.9995e-9S: inside closure tolerance and outside entry tolerance. Returned stress is1.0001S. Commit and evaluate the same strain: the same overstress now triggers another positive update, changing stress, ep and alpha. This is an equation-level counterexample accepted by the scalar return-map interface, not a claimed executed public material fixture or a change to the benchmark law. The same mechanism is possible on a concave supported hardening branch whenever its first accepted residual occupies this band; no claim is made that the captured case does so.

At fixed committed H, finite entry tolerance also means exact all-scale continuity is unavailable: the elastic branch retains overstress up to its entry band, while an entered plastic branch projects toward the yield surface. For perfect plasticity the one-sided stress jump at the entry boundary is approximately1e-9*max(s,1). For nonlinear hardening, reporting E*H_final/(E+H_final) differentiates the converged root; a return stopped after one Newton correction actually used H_old in that correction. Thus the implemented finite-tolerance map has approximate, branch-dependent consistency rather than an exact derivative everywhere. This limitation is bounded by local physical closure accuracy; it is not a demonstrated large zeroth-order force error or an explanation of the recorded stall. Dividing small stress/termination effects by tiny directional steps can nevertheless spoil an all-scale derivative claim. Preserving the two physical thresholds, curve and original solver controls was explicit; any change to them remains root-reserved. A useful future authorized witness would distinguish same-strain post-commit idempotence within the declared local tolerance from exact state equality, and compare fixed-H one-sided tangents inside a single branch. No new execution authority follows.

### Transport and consistent-branch equations checked

No concrete committed-versus-kinematic strain mismatch established in the inspected active plastic paths. Beam fiber input is current total epsilon0+z*kappa_y+y*kappa_z minus initial eigenstrain plus initial stress/E; the return map subtracts only committed ep and starts alpha from committed alpha. Stored fiber_strain/kinematic_fiber_strain are recovery fields, not an extra strain increment added to the current state. The force is L*sum(w sigma B), with B the derivative of that kinematic fiber strain. Tangent includes L*sum(w Et B^T B), the axial-force transverse geometric term and the retained constant elastic condensed shear/torsion terms. A copied H is observed and new ep/alpha arrays are returned; no old plastic array assignment was found.

Layered shell input similarly recomputes current membrane von Karman strain plus z*curvature, adds elastic initial-stress strain and subtracts initial eigenstrain before plane_stress_return_map. It passes committed ep/alpha; it does not add stored layer_strain to the current total strain. Orthotropic material-axis transformations and inverse elastic initial-stress offsets are paired in the inspected path. Resultant/tangent integration uses the same sigma/Ctan and weights through N,M,C0,C1,C2, with B_eff membrane derivative, bending and geometric terms.

For the isotropic shell kernel (plasticity.py280 onward), the invariant stress modes q=[b1/(1+c_a*d),b2/(1+2G*d),b3/(1+2G*d)] and alpha=alpha_old+2d*sqrt(phi2/3) are solved against f=phi2-s(alpha)^2/3. The analytical tangent differentiates this discrete consistency equation, including hardening and multiplier dependence, with convergence refusal and a numerical fallback for invalid analytic rows. Unlike the beam, the shell entry and closure tests use the same normalized tolerance1e-10; the specific factor-ten beam entry/closure counterexample does not directly transfer. Physical yield/unloading and hardening corners retain different one-sided tangents; no single classical Jacobian should be claimed exactly at those corners. Under finite stopping tolerance, the exact implicit derivative still describes the converged equation only to that accuracy.

The corotational work-conjugate adapter recomputes current deformational DOFs, passes committed material-frame history unchanged to the element, and returns p=B^T f_ref plus material/geometric chain-rule tangent. Under superposed rigid motion those deformational DOFs are invariant, so rotating the stored material ep again would double-transport it. No extra rotation or additive committed-strain reuse is required by these inspected small-strain material-frame equations. This is not a finite-strain plasticity certification. The canonical ANYmaterial curve implementation is re-exported by material_curves.py; its entire provider implementation and Hill48 route were not independently requalified here.

### Saved evidence does not isolate a constitutive defect

The named direct-frozen-new-fiber-2 result binds copied-history/displacement immutability, zero RHS reconstruction error and approximately1.05e-12 augmented solve backward error. Directional error changes greatly with probe scale: forward relative error26.45 at1e-5 but0.0003604 at1e-8, with backward0.0006047 at1e-8. continuation-direction-consistency reports a self-consistent selected branch, exact captured augmented-matrix equality, unchanged inputs and forward error0.0003124, while all finite eight-step trials still fail merit decrease. These facts show strong finite-scale/branch dependence but neither identify a zeroth-order jump nor prove the material map wrong at the captured point. They also do not establish nonexistence, physical collapse or convergence of a different solver. Owner's distinct material-event ray diagnostic is the appropriate place to attribute actual local points/events; it was not duplicated here. No additional concrete force/state/tangent defect beyond the explicit tolerance-scale exactness limitation was established by this Read review.

Applicability clarification requested by root: the active fixture constructs scaled canonical DNVC208MaterialCurve from dnv_c208_steel_curve('S355',T), preserving strain breakpoints and exponent. Static inspection of the installed provider .venv/Lib/site-packages/anymaterial/curves.py227-295 confirms two continuous affine hardening parts followed by a continuity-offset power branch, with the <= breakpoint convention matched by solver plasticity.py's JIT flow/H functions. Inside one affine part, exact arithmetic Newton solves the beam consistency equation in one step, so the concave-flow residual counterexample does NOT apply there. Crossing a hardening knot or occupying a concave power segment can leave an accepted nonzero residual; branch occupancy of the actual failed points was not established here and belongs to the owner's independent event diagnostic. The analytic example above is therefore a qualified map/tolerance limitation, not an established S355 stall mechanism. At knots the flow remains continuous but H need not; one-sided derivatives differ without a zeroth-order constitutive jump in the exact return solution. No threshold,30-local-iteration, curve or solver-control change is adopted.

Finally, immutable-input reconstruction and stress-map idempotence are distinct: copied H/u remaining bitwise unchanged proves the evaluation observed its inputs; it does not prove that committing the returned H_new and reevaluating identical total strain yields exactly identical stress/H_new. The named saved evidence establishes the former. This consultation establishes only the explicit local-tolerance limit on the latter, and no missing large-force consistency defect or physical-collapse conclusion.

## Production material-event globalization delta review — 2026-10-19

Bounded independent Read assessment of the consequential new delta, not a repeated Astra-high full progress review. No jobs/imports, product/test/authority edits, workers or duplicate event-ray localization. Actual read/recheck hashes match event-candidate-review-entry.json: _nonlinear_events.py410E6892F90B8BB3B7F08F3ADEE29906A0AF2933F003DC52252A5A7B9085198D; nonlinear_static.py7AD99DFF9000D8317BE82EB7A415844FE0158B3E9E603301AEB276E91454B8F8; tests/test_nonlinear_beam_shell_slice3.py233F9DCC62756D2C8B5E15984847D9F98FAC302709A80D7047250D4882CF998F. Later observer-only continuation test hashD3335AFDFE8C942CC9B5088584E22324AE2F8ED48BB265BAD21B268E0A7A6F3A was also read. No blocking source defect established in this delta.

Indicator equations/admission: helper34-77 observes the real returned constitutive fiber_strain/layer_strain and committed ep/alpha. For isotropic beams, flow_scale=1 and the scalar trial E*(strain-ep_old) with normalized1e-9 entry margin matches the constitutive branch equation. For isotropic layered shells it uses the plane-stress trial elastic stress and phi2-s^2/3 with1e-10 normalized margin. Returned alpha relative to the two actual DNV hardening breakpoints supplies hardening indicators. The helper refuses unknown history/layouts, nonisotropic materials and non-DNVC208 curves by returning None; it neither replaces a force law nor adopts Hill48/other-curve support. Initial prestrain/stress is already included in the real constitutive strain field and is not added twice. These equations are algebraically equivalent, not bitwise guaranteed identical to the kernels at an individual floating-point entry boundary: normalized subtraction/quadratic grouping differ. The resolved-offset and measured-force checks are consequential here; the existing +/-1Pa fiber test alone does not prove bitwise shell margin equivalence.

Integration/lifecycle: nonlinear_static.py4239-4248 freezes copied base indicator arrays before ordinary probes replace the pending candidate. The last admissible rejected trial supplies the upper observation before localization starts. Every event assembly evaluates the same committed H at a new uncommitted u; begin_state_evaluation replaces its trial token (nonlinear_state.py2675 onward), and material_events immediately copies numeric indicators before the next replacement. No event candidate is committed. A successful candidate only scales the current Newton delta; the next outer Newton assembles and checks equilibrium normally. Failed attempts use the existing discard/rollback path. The extension is confined to residual-dominated, positive-history, contact-free rotating-map DC globalization after the original bounded ordinary search has rejected its candidates.

Bounds/admissibility: helper97-112 uses at most48 bisection evaluations and137 at most2 flank evaluations, with finite midpoint checks. The final offset combines indicator roundoff, q representability and strain resolution; it verifies distinct q, a base-signature left state, and a changed-signature right state. Rejected/unsupported/domain-refused probes return None; unrelated exceptions are not swallowed. Cancellation is checked before every production event probe and model observation guards remain in place. The original residual/control merit, reference/target scales and1e-4 Armijo factor are preserved; an event candidate additionally needs residual decrease greater than128*eps times the observed force/residual/reference scale. No tiny equilibrium step becomes accepted material history solely because a signature changed. Event probes do not increment Newton iteration count, and there is still only one candidate event correction per iteration of the unchanged range(1,max_iterations+1). Original cutback, accepted-subdivision and failure reporting remain intact; event step/evaluation counts are added.

Bounded method limits: the signature predicate can be nonmonotone on a ray with recrossing or several events. The code establishes a resolved transition in the last rejected interval, not a general guarantee of the earliest material event; equal endpoint signatures deliberately cause ordinary failure even if an interior excursion exists. Global maximum q/strain spacing estimates can conservatively refuse mixed-scale events. Repeated crossings cannot create an unbounded inner search (50 probes max), and repeated outer corrections remain under the original40-iteration/cutback bounds, but neither fact proves progress to the target. These are algorithm limits, not new physical failure diagnoses or requests to change tolerances/authority.

Evidence actually inspected: continuation-material-events-focused-2 receipt and terminal stdout record8 passed, exit0,14.47036360000493s process wall with the reviewed source/test hashes. Tests cover helper bound/domain/unrepresentable/unrelated-error behavior, actual fiber entry and input copies, and a production-connected synthetic event correction with rollback/no accepted snapshots and cancellation during observation. An independently exercised actual-shell entry-margin witness is not present in these added tests; shell equation equivalence above was checked statically. The named continuation-first-material-event diagnostic records event alpha6.464360722468357e-8, event_crossed/post_event_armijo true, residual decrease0.0015411562635563314 above noise7.093095421302465e-10 and unchanged inputs. This is a positive single-ray witness, not a full target/campaign result.

The continuation test delta against the frozen base adds only an eight-line terminal.pkl observer after _full_case and before the original _assert_completed_dc_case(case,-.20). It preserves returned u/history/load/status/reason/info without changing any scientific assertion or acceptance predicate. Full-target jobs were active during review; no full-target, restart, analytical or Slice3 acceptance is inferred here. Earlier qualified local constitutive tolerance/idempotence limits remain distinct from this globalization mechanism and were not repaired or reattributed by this review.
