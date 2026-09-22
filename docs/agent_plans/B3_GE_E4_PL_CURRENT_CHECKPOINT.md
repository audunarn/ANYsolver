# Current B3-GE / E4-PL / B2 development checkpoint

22 September 2026. User authorized continued implementation with increased
effort. The active goal remains the complete programme; **G0B is open and
G1 is barred**. This is a continuity checkpoint, not a pause or completion.

- Worktree: `C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling`.
- Branch: `codex/b3-ge-e4-pl-integration`.
- Latest bounded operator source: `7cb7b77491ef3343b72a231a6bb443e0474ddec1`.
- Latest bounded assembly/probe source: `66b6e109516296bbf8c4ff4155f2aa96c3701d1a`.
- Latest bounded sparse-numerical/recovery source: `ade088e99e3108969baf70b27e7f7cc450351229`.
- Last scientific diagnostic source: `59753d97964795bbe0599c8fa02d44170b2fa8a4`
  (saved-state spatial residual diagnostic). Last equilibrium source remains
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
8. Exact saved-pose attribution at `d0b6d090`:3/3 cases PASSED, exit0;
   independent review accepted diagnostic integrity and attribution.
   Coefficient reconstruction explains the endpoint discrepancy; floating
   evaluation and direct action are much smaller. Original failures and
   physical HOLD remain. See `B3_GE_E4_PL_G0_F03_PRIMAL_EXACT_POSE_V1_RESULTS.md`.
   Its25-file immutable inventory SHA is
   `e7f0b5c8a8a403d7785ddba793e8061628b8b1b163ba4251338b63c3f0e5de0a`.
   All29 integrated synthetic/mock tests and the five affected final
   runner mocks passed (overlapping inventories); raw logs are preserved.
9. Spatial residual diagnostic at `59753d97`: 3/3 cases PASSED, exit 0.
   Independent postreview accepted integrity and descriptive localization,
   reproducing all 126 metrics and canonical summaries with no field/rule
   rerun. Largest metric `1.1651611328125e-13` against `1e-10`.
   The complete serial run took 21.5181126 s, with maximum sampled child
   RSS 105,488,384 bytes. Zero new equilibria or native element operations.
   See `B3_GE_E4_PL_G0_F03_SPATIAL_RESIDUAL_V1_RESULTS.md`.
   Completed 35-file inventory SHA:
   `43a9e2f5064f87b4e32f5e36e6158ae70fd6e0a01617765e5af5c1c3516bcbc7`.
   All 46 integrated checks passed; the 34/28 final affected checks also
   passed (overlapping inventories). All 13 raw development logs, including
   initial failures, and pre/post reviews are sealed with the evidence.
10. Local classical operator foundation at `7cb7b774`: 79 distinct current
    synthetic checks pass across final affected groups (30 foundation,
    19 corrected norm/cross-method, 30 unchanged Decimal oracle). Independent
    reviews accepted the bounded foundation and separately authored oracle.
    The earlier 75-pass run missed Duffy-weight underflow; the independent
    probe, two red regression tests and all fixes are preserved. Exact pad
    moments, membrane patches, C0 trace continuity, free root slope, shared
    ownership/resource guards and full piecewise Green norm are implemented.
    Zero new equilibria/native operations; physical HOLD remains. See
    `B3_GE_E4_PL_G0_F03_LOCAL_OPERATOR_PROOFS_V1_RESULTS.md`. New immutable
    39-file proof inventory SHA:
    `b26d4595f6b883d76ad9f2c66cb04f822e3cd8c9b97997ac2cce1f30c870206a`.
11. Sparse classical assembly and exact-transfer/work/numerical probes at
    `66b6e109`: 37 distinct current tests pass (assembly10, transfer6,
    work7, condition14), with independent final source/mechanics review.
    Sparse global KKT assembly performs no physical solve. Exact P preserves
    full sparse membrane/beam/root/load operators on admitted nested spaces.
    Work identities cover constant line densities and both atoms. Two
    condition-bound methods have a <=64 synthetic exact-Fraction prototype;
    neither scientific method is selected. Five malformed sparse-buffer
    regressions failed before validation was fixed; all raw logs remain.
    See `B3_GE_E4_PL_G0_F03_LOCAL_ASSEMBLY_PROOFS_V1_RESULTS.md`. New closed
    26-file archive `f03-local-assembly-proof-v1` inventory SHA:
    `d02087acd268b0c55cf173582ff0d08a79d20cf71b9b4f7cbb1cc1fd4bfdbf46`.
12. Sparse numerical building blocks and full classical recovery at
    `ade088e9`: 48 distinct current tests pass (interval certificate22,
    scaled sparse8, positivity6, recovery12); independent final review is
    closed for the bounded batch. The mocked negative-square-root regression
    failed before correction; the initial source and all ten raw logs are
    retained. Exact scalar root guards, sparse full-residual positivity,
    physical dual scaling and polynomial/cosine work recovery are verified.
    Six p>=2 support lift residual actions are implemented; p1 lifts remain
    unavailable. No physical reference equilibrium or native evaluation ran.
    See `B3_GE_E4_PL_G0_F03_LOCAL_NUMERICAL_PROOFS_V1_RESULTS.md`. The closed
    23-file proof archive `f03-local-numerical-proof-v1` inventory SHA is
    `43f9a1c950acc315c6fed28548f5f6e40a822b934d566ae5f4eb6b1185817100`.

Raw roots under `.qualification/b3-ge-e4-pl/` are respectively
`f03-area-axis-v1`, `f03-area-axis-analysis-v1`,
`f03-endpoint-comparison-v1`, `f03-analytical-norm-v1`, and
`f03-joint-refinement-v1`, `f03-variational-attribution-v1`, and
`f03-primal-ritz-v1`, `f03-primal-saved-audit-v1`, and
`f03-primal-exact-pose-v1`, and `f03-spatial-residual-v1`. Reports retain their
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
Their only failing component is transverse b'' at s=1. Exact independent
reconstruction now attributes it to the saved coefficient route, while
retaining all floating arithmetic and exact endpoint triangle bounds.
This does not identify every operation inside that reconstruction or
waive either failure. The exact diagnostic changed no saved state.
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

The completed spatial study localizes persistent defects near root pads
(cells 12/30) and right supported/free corners. Its volume-squared totals
are 21.69397, 17.02412, 11.53795 and free-edge-squared totals are 0.0264247,
0.00961514, 0.00454445 for n12/n16/n24. At n24, rightmost free-edge segments
contain 85.4% of that squared edge defect. These are descriptive measures,
not physical-error percentages, acceptance bounds or production-space choices.

The local-reference mechanics foundation and its limitations passed
independent review. Draft SHA:
`36ce310a99df390fa95c83fd2e346315fb46cc795665f6e5de1ba747ddb4bc3b`;
see `B3_GE_E4_PL_G0_F03_LOCAL_REFERENCE_DESIGN_REVIEW.md`.
The operator contract and bounded synthetic proofs are now accepted; see
`B3_GE_E4_PL_G0_F03_LOCAL_OPERATOR_CONTRACT.md` and its results report.
Their raw archive is `.qualification/b3-ge-e4-pl/f03-local-operator-proof-v1`
(39 bound files plus inventory); it is closed and must not be extended.
The sparse eliminated-primal assembly, exact nested transfer and bounded
manufactured work identities are now implemented and independently reviewed.
The latest closed proof root is `f03-local-numerical-proof-v1` (23 bound files
plus inventory); it must not be extended. The scaled candidate solve,
streamed interval condition certificate, supplied-factor sparse positivity
proof and complete polynomial/cosine work recovery are now implemented and
reviewed on synthetic/manufactured inputs. The exact next action is a bounded
sparse positivity-factor producer and the connected numerical acceptance,
integration/rank/work checks, saved-state bindings and independent adjudicator.
Then complete and independently review a frozen numerical protocol and new
registration. No scientific case family or certificate method is selected.
The <=64 exact-rational probe remains a synthetic oracle, never a dense
scientific fallback. Factor peak memory needs external supervision; streamed
inverse columns still require 8*N*N raw saved bytes. p1 support lifts remain
unavailable; Decimal cosine displays are not certified error bounds.
Preserve the same physical operator, held J/gamma, three root
constraints/free slope, signed reaction and full-functional criteria.
Mesh/degree inventories, integration, conditioning, resource and convergence
gates remain to be resolved before any new scientific registration. In
particular: preserve the implemented positive exact intervals whose endpoints
collapse in binary64, retain shared tensor conformity, and bound actual
footprint incidence/nnz/fill/workspace growth. Hanging nodes remain outside
the new helper's scope and require their own conformity proof if introduced.
The complete piecewise norm is synthetically checked; its input bounds and
active normal-weight guard must remain part of numerical admission.
The stress-jump and support-lift signs are independently verified on bounded
manufactured fields; retain them in the general recovered-field implementation.
Numerical-admission design is in `B3_GE_E4_PL_G0_F03_LOCAL_NUMERICAL_ADMISSION_DRAFT.md`:
same held energy-diagonal scaling, full stored H, true condition upper bound,
safe backward denominator, explicit positivity/integration/resource checks.
All-column certification has quadratic evidence/work; triangular comparison
can be pessimistic. Compare/select before registration, never as a fallback
after a failed scientific bound. No automatic uniform/global-degree run.

No scientific process is active. Both specialists finished their independent
assembly/work/prolongation/certificate reviews. Parent owns the next scalable
numerical implementation and recovery/protocol work. The accepted proofs grant no scientific execution
authority. Current sources and tests are committed; the results/checkpoint
commit preserves the restart boundary.
All consumed diagnostic sources and completed inventories stay frozen.
No release approval is being exercised. Keep main unchanged during G0.
