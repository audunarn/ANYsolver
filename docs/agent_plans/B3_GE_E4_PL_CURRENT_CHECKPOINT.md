# Current B3-GE / E4-PL / B2 development checkpoint

22 September 2026. User authorized continued implementation with increased
effort. The active goal remains the complete programme; **G0B is open and
G1 is barred**. This is a continuity checkpoint, not a pause or completion.

- Worktree: `C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling`.
- Branch: `codex/b3-ge-e4-pl-integration`.
- Last executed implementation commit: `f8f8e851e3ce24885005381d9b64873026baa314`;
  subsequent documentation commits do not change the evaluated operators.
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
   execution harness are implemented but not scientifically executed.
   The first integrated unit run passed51 checks. Following independent
   findings,23 focused operator/check tests and48 affected integration tests
   passed. These are overlapping test inventories, not summed coverage.
   Independent preregistration review granted GO contingent on a clean
   source freeze. No reference convergence or G0B acceptance is implied.

Raw roots under `.qualification/b3-ge-e4-pl/` are respectively
`f03-area-axis-v1`, `f03-area-axis-analysis-v1`,
`f03-endpoint-comparison-v1`, `f03-analytical-norm-v1`, and
`f03-joint-refinement-v1`, and `f03-variational-attribution-v1`. Reports retain their
registration/adjudication hashes; raw reviews and execution provenance
are saved with the latter two roots. All these executions are consumed.
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

The next action is a clean source freeze of the independently reviewed
continuous primal reference b=A us, then the single-use
five-level execution in `B3_GE_E4_PL_G0_F03_PRIMAL_RITZ_PROTOCOL.md`.
The independent reviewer draft remains preserved alongside it. Exact
levels are n=4,8,12,16,24; each has one canonical equilibrium and an
assembly-only integration crosscheck. Child limits are900s/8GiB sampled
RSS, with3600s launch cutoff. Planned root is
`.qualification/b3-ge-e4-pl/f03-primal-ritz-v1`, not yet consumed.
No native FE/host-clipping/multiplier assembly is used as the reference
algorithm. Failed settling leaves the reference unresolved; no automatic
degree extension is authorized. No primal reference scientific execution
has occurred at this checkpoint.
This does not replace required executed external comparisons.
Do not automatically add uniform refinement, change
tolerances, drop P1, relabel any HOLD, or promote a production space.
Native full-vector/shear/drilling and all other G0 foundations remain open.

No scientific processes are active at this checkpoint. The implementation
worker has completed its bounded edits. `/root/finite_pad_axis_review`
accepted the final corrections; parent owns integration and execution.
Fourteen new primal source/test/protocol files and this checkpoint await
the clean source freeze. No concurrent writer owns completed evidence.
No release approval is being exercised. Keep main unchanged during G0.
