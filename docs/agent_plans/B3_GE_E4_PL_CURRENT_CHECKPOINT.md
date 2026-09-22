# Current B3-GE / E4-PL / B2 development checkpoint

22 September 2026. User authorized continued implementation with increased
effort. The active goal remains the complete programme; **G0B is open and
G1 is barred**. This is a continuity checkpoint, not a pause or completion.

- Worktree: `C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling`.
- Branch: `codex/b3-ge-e4-pl-integration`.
- Last executed source: `c8b2f78d3ace4e23ed8f636fd6b474ef250ccda6`
  (saved-only audit). Last equilibrium source remains
  `e7908c1ad3dcff1cf9bc957ba8fd0fe1fe49b5b5`. Neither the comparator
  correction nor saved-only audit changed a mathematical operator.
- Main was observed clean at `be41a77a62e1cd7e1767bda6e955253af0819f91`,
  version 0.4.7. No product promotion or publication occurred.
- Controlling programme: `B3_GE_E4_PL_B2_COMPLETE_PROGRAMME.md`, revision 4.
  B3-GE remains principal; the distinct physical B2 option remains required.

## Latest completed work

1. Finite-pad independent-axis screen: 18 supervised cases completed and
   passed their algebraic/resource checks at source `584835f1`. Owned
   snapshots enabled separate endpoint diagnostics at `bfff7f0d`.
   Both evidence sets passed independent integrity/descriptive review.
   See `B3_GE_E4_PL_G0_F03_FINITE_PAD_AXIS_RESULTS.md`.
2. Endpoint-space comparison at `2b64174b`: ten meshes times P1/hybrid/
   enriched = 30 complete equilibria, preserving each family's partial
   states. **All ten decisions remain UNRESOLVED_AUXILIARY_NORM** because
   enriched's registered 32/64 squared-norm change exceeded 0.001.
   All other frozen metrics passed. Independent review accepted evidence
   integrity and retained HOLD. See
   `B3_GE_E4_PL_G0_F03_ENDPOINT_COMPARISON_V1_RESULTS.md`.
3. Separate pure analytical norm study at `45d3f1aa`: all nine comparisons
   passed against independent Decimal Green quadrature; maximum relative
   operator error `1.66524e-13`. Independent final review accepted this
   norm validation only. See
   `B3_GE_E4_PL_G0_F03_ANALYTICAL_NORM_V1_RESULTS.md`.
4. Joint shell/beam/interface refinement at `707cb39d`: six complete
   supervised cases, comprising 12 fresh equilibria and six reused middle
   states. All numerical checks passed and reused physical arrays/metrics
   matched exactly. **UNRESOLVED_JOINT_REFINEMENT**: every family/topology
   trend and every final topology/family comparison remains open. The
   registered execution is consumed; final adjudication exit1 is the
   intended failure disposition, not a reason to retry. See
   `B3_GE_E4_PL_G0_F03_JOINT_REFINEMENT_V1_RESULTS.md`. Independent review
   accepted the evidence and retained HOLD on mechanics, reproducing all
   saved spectra, physical-force recovery and trend predicates without
   structural or norm-constructor reruns.
5. Saved-state variational attribution at `f8f8e85`: all three Q4
   middle/fine family checks passed, with no equilibrium or Schur solve.
   Independent review accepted raw integrity and bounded interpretation.
   See `B3_GE_E4_PL_G0_F03_VARIATIONAL_ATTRIBUTION_V1_RESULTS.md`.
   The continuous eliminated-primal derivation also passed independent
   mechanics review; that acceptance is not numerical qualification.
6. The independent polynomial Ritz reference, exact root constraints,
   physical recovery, continuous Green norm, bounded archive and five-level
   execution harness were frozen at `e7908c1a` and all five registered
   equilibria completed. Canonical adjudication is **FAILED_EVIDENCE** due
   to a Python/NumPy numeric-type comparison after JSON serialization.
   The first integrated unit run passed51 checks. Following independent
   findings,23 focused operator/check tests and48 affected integration tests
   passed. These are overlapping test inventories, not summed coverage.
   Independent postreview verified215 arrays and exact numerical metric
   parity, but retained two saved-action failures and unresolved physical
   settling. The comparator is corrected;25 affected tests and independent
   scoped code review passed. See `B3_GE_E4_PL_G0_F03_PRIMAL_RITZ_V1_RESULTS.md`.
   No reference convergence or G0B acceptance is implied.
7. The registered saved-only audit at `c8b2f78d` completed5/5 children
   with zero new equilibria/assemblies. Integrity PASSED; canonical status
   **FAILED_NUMERICAL_SCREEN**, exit1, retaining n16/n24 action failures.
   Independent postreview accepted integrity with numerical/physical HOLD.
   All21 focused mock tests passed after review fixes. See
   `B3_GE_E4_PL_G0_F03_PRIMAL_SAVED_AUDIT_V1_RESULTS.md`. The new32-file
   immutable inventory SHA is
   `5073230a813bf9acef534d756ac05fb7deb29d1f7cf7caae507db94afc99014d`.

Raw roots under `.qualification/b3-ge-e4-pl/` are respectively
`f03-area-axis-v1`, `f03-area-axis-analysis-v1`,
`f03-endpoint-comparison-v1`, `f03-analytical-norm-v1`, and
`f03-joint-refinement-v1`, `f03-variational-attribution-v1`, and
`f03-primal-ritz-v1`, and `f03-primal-saved-audit-v1`. Reports retain their
registration/adjudication hashes; raw reviews and execution provenance
are saved with the latest roots. All these executions are consumed.
Do not overwrite, retry or relabel them. Earlier failed/aborted evidence
remains intact, including finite-pad feasibility v1's adjudication failure.

## Physical finding and exact next action

The earlier attachment-only tip plateau did not establish structural
convergence. Joint refinement from (8,16,16,8) to (16,32,32,16) changes
endpoint-space tip displacement by4.69-5.42%, energy by6.65-8.51% and the
full multiplier functional by4.62-5.09%. Enriched gap RMS/motion is only
0.14-0.16% on the finest meshes, but reactions/energy/band transfers remain
unsettled. Hybrid/enriched fine tips nearly coincide while terminal-band
force/moment differs about10%. P1 remains much further from endpoint
spaces. All finite Schur modes are positive; no continuum stability claim.

The attribution identity is now verified. Enriched's potential change is
mostly shell energy distance (0.77136 J), with beam distance 0.01472 J and
small net constraint work 0.00003296 J. This is a discrete-state split,
not causal continuum-error attribution; cancellation and endpoint error
remain possible. P1 and hybrid have substantial negative constraint work.

The primal reference root `.qualification/b3-ge-e4-pl/f03-primal-ritz-v1`
is now consumed: n=4,8,12,16,24, five equilibria,10 integration assemblies,
60.9037s overall and220.77MiB maximum sampled child RSS. Original
registration/adjudication and all36 completed evidence files are preserved.

The saved-evidence audit is complete and consumed. Its32-file inventory
and the original36-file parent inventory are frozen. Retain the original
FAILED_EVIDENCE and the audit's FAILED_NUMERICAL_SCREEN with n16/n24
saved-action failures (1.49057e-11 and1.15333e-10 against1e-11).
Their only failing component is transverse b'' at s=1; endpoint
amplification of projection roundoff is plausible, not a waiver.
Independent diagnostic settling also fails: last energy changes4.52%,
2.60%, and full-functional changes2.87%,3.16%; only16/45 scalar sequences
pass. The reference is not ready for FE-as-reference comparisons.
No automatic degree extension or physical rerun is authorized by this
checkpoint. Diagnose and review the next numerical formulation before
any new scientific registration.
This does not replace required executed external comparisons.
Do not automatically add uniform refinement, change
tolerances, drop P1, relabel any HOLD, or promote a production space.
Native full-vector/shear/drilling and all other G0 foundations remain open.

The next action is implementation and independent review of
`B3_GE_E4_PL_G0_F03_PRIMAL_EXACT_POSE_PROTOCOL.md`, then one registered
three-case saved-state representation diagnostic. The mechanics draft is
`B3_GE_E4_PL_G0_F03_PRIMAL_NEXT_DIAGNOSTIC_DRAFT.md`. It proposes exact
rational reconstruction of the three saved n12/n16/n24 states, with
separate floating evaluation, coefficient and direct-action discrepancies.
It preserves represented geometry and its non-unit yaw factor where
applicable. The new protocol distinguishes the original full saved-action
metric from the replayed derivative submetric and freezes rational
encoding limits. Spatial residual analysis is a later, separate diagnostic.
No actual three-state execution has been registered or performed yet.
The independent Fraction operator, attribution checks and supervised
runner are implemented. The integrated29 synthetic/mock tests passed;
independent review corrections cover bounded serialization, exact
represented geometry, and exact copying of inherited evidence. Final
scoped review and the clean source freeze precede the registered run.

No registered scientific process is active. Parent owns the new protocol,
runner and evidence; f03_port_mechanics owns only the new exact-pose module
and synthetic tests. finite_pad_axis_review supplies independent review.
No worker owns completed evidence. The previous audit source stays frozen.
No release approval is being exercised. Keep main unchanged during G0.
