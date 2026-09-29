# B3-GE / E4-PL / B2 active state

## Revision 8 prospective transition — 29 September 2026

The [Revision 8 plan](B3_GE_E4_PL_REVISION_8_PLAN.md) and
[goal](B3_GE_E4_PL_REVISION_8_GOAL.md) govern forward work after resumption.
The [current acceptance matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md)
keeps milestone and gate claims open until their evidence is adjudicated.
They change milestone order and owner decision rights; the scientific criteria,
historical evidence, consumed authorities and complete release boundary below
remain intact. The current milestone is M1's matching-station elastic GE panel.
M2 connection mechanics and M3 physical B2 remain open parallel paths.

The bounded M1 low-yield ticket restored the existing accepted 40 N checkpoint
and reproduced the 45 N backtrack-budget failure (163 assemblies, best free
ratio 0.1069403). The accepted checkpoint was byte-identical after rejection.
At the final rejected Newton base, the actual-update merit has a negative
directional slope near zero; alpha=1e-4 reduced it, whereas the smallest
permitted backtrack, alpha=2^-12, did not. The free-equation directional
derivative discrepancy was 0.00123 at step 1e-5 and worsened at 1e-6; this
does not establish a sufficiently accurate plastic tangent or a physical limit
point. A single 40→42.5 N cutback hit the Newton iteration limit without
changing the accepted prefix. Raw outputs and the bounded runner are in
`.qualification/b3-ge-e4-pl/r8-f05-45n-ticket-dev-20260929-v1/` and
`scripts/b3_e4_f05_45n_trial_diagnostic.py`. F05/G3 and this material path
remain open. Do not broaden or advertise its material domain from the 40 N
success. Next M1 action: advance the already working elastic public/ANYfem
route and identify a genuinely matched E01 point-connection reference;
resume this plastic ticket only for a specific accepted scope or derivative
repair hypothesis. No formal F03 authority was used.

The current M1 integration screen built solver wheel
`2a458326c52ec19f5a50c86b598e00252d521c956df62e429181a94e24a9cc25`
from `2f3161b3` and ANYfem wheel
`edc1457950fc250e5a283c47b2cf98246e21dfb59198dfc6f697c88c0336c3a8`
from `8c8a4823`. Actual installed imports were verified. Four focused ANYfem
GE panel tests and five B2 batch tests passed on Windows/Python 3.14 with
JIT disabled and one numerical thread; the first B2 collection setup failure
is preserved. See `.qualification/b3-ge-e4-pl/r8-m1-combined-installed-dev-20260929-v1/`.
This confirms the current combined experimental workflow, not M1/M3
acceptance. M1 still needs V01–V06, V17/V18/V28 coverage reconciliation,
matched E01, Linux/platform checks and independent review of the complete
candidate. Do not use the earlier rigid-footprint CalculiX canary as a
matching-station six-row point-bond oracle.

Current E01 decision: keep the inert signed B31/S4 deck and its passed
native-row Jacobian check as development evidence, but do not execute it as
a point-bond reference. CalculiX 2.23 creates no rotational knots at these
flat single-direction stations, so its six rotational MPC terms have no
verified physical expansion map. Source: `gen3dnor.f:830`, `gen3dmpc.f`
and https://www.dhondt.de/ccx_2.23.pdf section 10.3.6. The prior rigid-
footprint canary also failed a related rigid-motion check. This is an
external encoding defect, not a native formulation rejection.

An independent OpenSeesPy 3.8.0/Python 3.12 reference-linear route now
supports matching six-coordinate point links with explicit elastic shear
areas. Two signed offsets at each of 2/4/8 panel intervals completed. Link,
global wrench and virtual-work checks passed; the printed support reaction
required beam-root force and eccentric-arm recovery. Six native source solves
on the same meshes differ from OpenSees by at most 0.077% in tip axial motion,
0.787% in vertical motion and 0.944% in pitch rotation. Secondary lateral,
roll and yaw components differ materially, so neither full physical agreement
nor E01/M1 acceptance follows. Evidence and failed attempts are preserved at
`.qualification/b3-ge-e4-pl/r8-e01-opensees-point-dev-20260929-v1/`.
At eight cells the bonded shell `u_y` agrees closely, while its `r_x` and
`r_z` differ; the exact rigid-arm relation accounts for the beam-tip lateral
difference. Next check matched shell rotational response before adjusting the
point law, and freeze E01 observables, absolute floors and shell idealization
before a formal installed comparison.
No F03 authority was used. The separate ANYmesh heavy job was not interrupted.

Updated 29 September 2026 under Revision 7 and ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1. This is the short working checkpoint. The complete pre-compaction note is preserved byte-for-byte in B3_GE_E4_PL_ACTIVE_STATE_HISTORY_20260929.md (SHA-256 2D5071E8A93FDCF35FC3AF49955E0B85F431A19B1DF2BF3742A8CA560584BCDA). The complete programme, acceptance matrix, frozen registrations, failures, and versioned evidence remain authoritative.

## Decision and gates

Deliver one complete G0–G6 release, with native B3-GE/E4-PL principal and a separate mandatory physical B2 option. Experimental integration is allowed while G0 remains open. G0B/F03 are open, none of F01–F13 is fully accepted, and G1 acceptance and production qualification are barred. Formal F03 execution authority remains unconsumed. Historical one-use authorities are not replayed. The dirty factor-4 Fy fallback script belongs to another ongoing investigation; do not edit, stage, or execute it by default.

Integration branch: codex/b3-ge-e4-pl-integration in this isolated worktree, reviewed through 55e79c19. Element/joint mechanics remain at b702e50d. Preserve concurrent work and check actual process identity before launching a heavy job.

## Delivered experimental behavior

- Sparse GE point owner: multiple Q4/S3 shells and native B3 members, retained variables, reference-linear and finite stepping, physical recovery, atomic accepted state, checkpoint/restore, and continued stepping. A replaceable six-channel L1 line candidate works on bounded fixtures; it is not a qualified bonded line.
- Separate physical B2 profile: immutable operator, compatible 1/10/100 case batching, selected recovery, complete-case cancellation, and eligible factorization reuse. Physical-range admission, new attachments, mass/prestress, practical scale, and full B2 qualification remain open. Historical B2 remains unchanged.
- Experimental ANYfem construction and save/reopen consumer exists in C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer. Its format is distinct from ordinary native-project persistence. The installed solver/consumer milestone and independent review are recorded in .qualification/b3-ge-e4-pl/r7-combined-integration-dev-20260928-v1/.
- Reference-linear and finite residual scales were corrected so zero response to tiny active loads cannot pass. Point/line numerical-dependence preflight is bounded and exposes source provenance; a full nonlinear sparse constraint audit remains open. The detailed installed-wheel identities and regression logs are in the preserved history and their versioned evidence directories.
- Experimental all-S3/J2 V5 checkpoint and accepted-state chart binding are in b702e50d. The source and installed-wheel checks for that product revision passed; the wheel SHA-256 is F32A38F2109FF6AF16EAFBC29550C6340CF1DFAA5295AA2EDA925D690D2D7BEF. The native S3 response is element-local, not a qualified corotational finite-rotation S3 route.
- GE compilation now owns shell coordinates/connectivity and definition collections used by later material, capability and checkpoint decisions. A caller-mutation regression exposed the prior alias; 51/51 impacted source and newly installed-wheel tests pass. A mixed J2 checkpoint written by the preceding wheel restores and continues on the new wheel with the same identity and selected physical/material results. Independent review found no bounded defect. See .qualification/b3-ge-e4-pl/r7-ge-definition-ownership-dev-20260929-v1/. This is experimental V28/G1 progress, not definition-layer or gate acceptance.

## Live mechanical findings

The six-channel native line law and multiplier resolution are undecided. Paired-grid screens show a positive broken-trace diagnostic but no mesh-uniform theorem. At 2:1, vertical coarsening exposes a lateral-force/rotation mode. A direct virgin L1 bridge reconstructs that mode: historical/L1 gaps agree after the translation-sign map to <3e-19, off-quadrature gaps remain nonzero, and three independent work-transpose checks agree to <9e-19. Actual two-point L1 A/B/C projections reproduce the saved three-point projections; B misses almost all Mx in this one field, while other channels and spaces differ. Independent mechanics review found no reconstruction/sign defect. The mode is neither a zero-energy mechanism nor a candidate-selection result. Physical shell/native quadratic energies are 0.0976/6.8324 J for the recovered coordinates; the old auxiliary quotient is not a physical stability score. Raw inputs, output and limits are in .qualification/b3-ge-e4-pl/r7-f03-fy-saved-projection-dev-20260929-v1/. Fixed-row quotients cannot select P0/P1/dual, and a positive-subspace quotient is not the native mixed-system well-posedness test. The native flat rail balances +100 Nm torque and +1000 N shear and has small numerical-completion sensitivity on one grid; that is not accepted physical transfer fidelity.

The historical Q6/finite-pad, classical axial, and native six-channel families remain distinct. The saved F5 sided-port attempt lacks a unique conforming extension for native broken port work. Its validated common-field actions can still be used. The folded-shell CalculiX web has different section, root, seam, axis, and attachment extent from the native rail, so it cannot score this law. No new external deck or finer axial sweep is justified without an observable that distinguishes the competing explanations. Independent mathematical review confirms that the proposed H^-1/2 norm fails the current yaw derivative channel; physical L2 scoring still lacks a supported h-uniform six-channel work bound, and same-law compliance scoring lacks a certified reference tail. No P0/P1 candidate is ready for formal scoring. See the preserved history and the F03 prospective assessment draft.

The yielded-S3 development fixture with elastic beam accepts 50 N and then 60 N, restores the V5 state, and preserves the accepted prefix after an advanced candidate assembly is rejected or cancellation arrives. Direct and restored continuation agree in selected shell/beam/retained state, reactions, and S3 material recovery. Focused source and same-process installed-wheel tests pass 2/2; raw evidence is in .qualification/b3-ge-e4-pl/r7-s3-j2-owner-dev-20260929-v3/ and v4/. This is not F05/G3 acceptance.

The first mixed Q4/S3 shell-J2 50 N development solve with a 20 kPa curve exhausted backtracking without accepting an increment. A bounded first-correction check found its virgin full step non-descent, but its half step reduced the residual ratio from 1 to 0.514 while activating Q4 alone; S3 remained elastic. The later failure is not yet allocated to a formulation derivative, finite-step conditioning, or acceptance. Evidence is in .qualification/b3-ge-e4-pl/r7-mixed-q4-s3-j2-dev-20260929-v1/.
With the previously accepted 1 MPa Q4/beam yield curve and 500→1000 N history, a one-Q4/two-S3 shell plus native B3 accepts both increments with Q4 and beam yielding. A focused regression restores the mixed checkpoint, rejects a genuinely advanced candidate without partial commit, and compares a subsequent 1.0→1.05 increment from original and restored owners. Source and installed-wheel checks pass 1/1; independent review found no bounded defect. See .qualification/b3-ge-e4-pl/r7-mixed-q4-s3-j2-accepted-dev-20260929-v1/. This delivers one experimental mixed yielded history, not S3 yielding in the same model, explanation of the low-yield failure, or F05/G3 acceptance.
At that half-step trial, the fixed-predecessor second Newton direction has beam/retained derivative agreement below 1e-7. Global shell-row finite differences show 0.00964 N absolute error at perturbation 1e-4 against a 112.17 N predicted norm. Direct Q4, both native S3 elements, and point-joint physical rows have much smaller local errors. The actual Q4 corotational route reproduces the global error (0.00955 N at 1e-4); its 2/12 active-layer branch mask is stable and its force error is 2.06e-6 relative at 1e-3. Independent review finds an approximately 1/h difference-error trend consistent with a raw-force/coordinate precision floor, but neither tangent exactness nor a cause of the later solve failure is proved. No product tangent or tolerance change is justified by this screen.

A separate all-S3/high-yield-shell fixture has a yielded B3 beam at accepted 500 N. Its first 1000 N Newton step raises scaled residual ratio from 0.5 to 46.45; half, quarter, and sixteenth steps also increase it. Shell alpha stays zero. Actual-update, fixed-predecessor directional derivatives for that Newton direction agree with the tangent at 1e-6 and 1e-7 perturbations: shell error below 1e-8 and beam/retained error below 4e-8. Multiplier-row absolute difference is about 1e-14; its near-zero denominator precludes a useful relative quotient. The 1000 N failure is unresolved, and one directional check does not qualify the full Jacobian or prove a globalization cause. Preserve the failed path; do not alter the tangent or relax equilibrium from this screen. The 4-thread-per-OpenBLAS-pool raw log is in v4.

## Next discriminating action

F03 finite-width line-patch first variation passes 3/3 bounded checks, including six-channel rigid work, native translation cancellation, and a virgin-predecessor guard added after independent review. On the fixed endpoint-yaw field, work falls from 0.4990 to 0.1107 over 8–64 segments; its physical-energy-normalized ratio rises at 8→16 before falling at 16→64. A fixture-bound same-model linear comparison retains rank, virtual work, support balance and positive shell physical work; primary tip response differs from the rail by 0.66% in torque and 0.067% in shear. Independent review confirms this rules out a gross fixed-grid transfer loss but cannot choose the physical connection. The patch remains a distinct distributing law, not a bonded-line selection. Next excite the saved 2:1 Fy/rotation/local-slip mode against a genuinely same-action physical reference with matched section, axis/offset, bond extent and supports; resolve second variation before any nonlinear patch use. Evidence: .qualification/b3-ge-e4-pl/r7-f03-finite-patch-line-dev-20260929-v1/ and r7-f03-patch-vs-rail-dev-20260929-v1/. Formal F03 authority remains unconsumed.

The bounded saved-mode screen now distinguishes the trace laws on the same virgin 2:1 field and common multiplier action. The first output used mean-row dual coefficients as line densities and is retained as a mis-scaled development result; corrected v2 divides by physical P0 row measure. Reconstructed L1 work is 0.132809353489 J, matching the frozen mean-row action to roundoff. Its shell/native split is 0.101298630920/0.031510722569 J; the fixed 0.1 m patch split is 0.038308332396/0.031510722569 J. The difference is signed shell virtual work, mainly the pitch-moment channel; it is not energy, compliance, a loaded response, or physical-fidelity ranking. Read-only independent review found no mechanics blocker and recommends explicit L1-total and station-by-station native-work guards before using the runner for further comparisons. Next decide the physical bond's permitted longitudinal distribution through a matched same-action reference of local slip and traction/couple work, or an explicit physical bond declaration. Do not select either trace or spend formal F03 authority from this screen. Evidence: .qualification/b3-ge-e4-pl/r7-f03-saved-mode-patch-work-dev-20260929-v1/ (comparison.json is mis-scaled; comparison-v2.json is corrected).

F05 mixed-owner discriminator: an accepted 1 MPa mixed Q4/S3/B3 predecessor has fixed-predecessor, actual-update directional agreement at two adjacent steps; this is not a full branch proof. Evidence: .qualification/b3-ge-e4-pl/r7-mixed-assembled-derivative-dev-20260929-v1/. The separate 20 kPa case failed from virgin at 5 and 10 N; the elastic-shell 10 N control reproduced the same dominant Q4 residual rows, localizing a small-load precision floor rather than plastic flow. An algebraically equivalent shell pullback using displacement differences accepted both 10 N controls. The 5 N-step J2 path accepted through 40 N, with shell yield active by 25 N, then failed at 45 N (best ratio 0.107, 163 assemblies). The first linear comparison omitted stored beam frames; even the corrected additive-chart comparison is not a valid finite residual oracle and must not be scored. A scoped product precision edit now passes 49/49 focused source and 5/5 installed-wheel checks; imported wheel SHA-256 E773502C97EC9DF9026FA41A53445EADC717F089C714C9781B8D0B85EAB0D5A7. Independent read-only review found no algebraic/objectivity blocker but notes that tangent frame arms still form from rounded deformed coordinates; existing actual-update and rigid checks passed, while high-precision shell tangent claims remain open. This does not resolve the 45–50 N plastic-branch failure or accept F05/G3. Evidence: .qualification/b3-ge-e4-pl/r7-f05-low-yield-step-path-dev-20260929-v1/ and r7-q4-small-load-precision-installed-dev-20260929-v1/.

1. For F03, use the now-bridged 2:1 mode and corrected patch comparison to decide physical bond semantics against a genuinely same-action reference with matched section, axis/offset, bond extent, supports and representable local work. Add the two recommended evidence guards before reusing the diagnostic. The remaining gap is physical fidelity and complete-space stability, not a virgin work-map sign error. Resolve the h-uniform physical L2 work bound (or certified same-law reference tail) on the admitted mesh family before formal scoring. Do not tune channels or refine automatically.
2. Continue independent F05–F13 and B2 foundations where their inputs are stable. For the distinct 45 N plastic-branch failure, compare the accepted 40 N predecessor with one bounded 45 N trial, material active sets and actual-update derivative before changing a tangent or stepping rule. The earlier direct virgin 50 N failure (ratio 0.259) and all-Q4 nonconvergence remain separate observations. Integrate a selected line/footprint law only after its own mechanics checks, then run the full seven ratios, growing spaces, three refinements, installed/consumer, external, scale, and independent acceptance gates.
3. Assess the separate 500→1000 N beam-yielded/S3-elastic path only against a specific required physical history or acceptance case. Its local derivative result rules out a change based solely on that diagnostic.

One formulation/metric design batch and one targeted candidate comparison batch precede the F03 decision review. Complete scope remains G0–G6, F01–F13, V01–V28, B01–B18, mandatory executed external comparisons, GE 10,000-shell/1,000-beam and B2 10,000-shell/1,000-beam workloads, consumers, and one authorized coordinated release.

## Execution boundary

At most three workers and one heavy numerical job at a time. Prospective diagnostics: 100,000 rows, 600 seconds per run, eight numerical threads, and 8 GiB process-tree memory. Verify effective settings in the target process. Preserve failed evidence, physical tolerances, frozen registrations, and source/installed identity. Existing scientific criteria and release authority are unchanged.
