# Vidar — S4 nullspace-semantics proof editor plan

## Objective

Produce the proof-only nullspace partition and topology semantics governed by
`docs/S4_NULLSPACE_SEMANTICS_PROOF_PLAN.md`. Vidar must establish what is
gauge, what is a positive-mass mechanism, and how explicit topology/support /
MPC/coupling/activity/deletion matrices change those subspaces. Vidar must
not select or apply a rank policy.

## Base and owned files

- Worktree: `C:\Github\ANYsolver\.perf2-worktrees\s4-nullspace-semantics`
- Branch: `codex/s4-nullspace-semantics`
- Base: `f5cf8d925f47c816f5fe4857a83c5e38fd599570`

Exclusive write ownership is limited to four new paths:

- `docs/S4_NULLSPACE_SEMANTICS_PROOF.md`
- `docs/reference_cases/s4_nullspace_semantics_oracle.py`
- `docs/reference_cases/s4_nullspace_semantics_cases.json`
- `tests/test_s4_nullspace_semantics_proof.py`

All existing files and coordinator completion paths are read-only.

## Required method

- Read the governing plan completely before acting.
- Use binary64 and exactly the governing metric: `q_phys=S_q q_hat` with
  per-node `S_q=diag(ell,ell,ell,1,1,1)`, positive normalized quadrature rows
  for `B_w`/`H_w`, and post-transform 2-norm normalization for nonzero C rows.
- Use exactly `tau=64*max(m,n)*eps64*sigma_max` and sensitivity multipliers
   `(0.25,1,4)`, including the registered empty/zero-matrix conventions. Never
  tune these after observing results. For each derived restriction `T=A Q`,
  use the governing preregistered inherited parent scale `sigma_max(A)` in its
  SVD threshold, not `sigma_max(T)`; multipliers affect only that threshold.
- Use exactly the governing residual calculus:
  `r_tol(d)=4096*d*eps64`, its frozen dimension rule, `r_zero`/`r_eq` formulas,
  zero-denominator convention, finite-binary64 requirement, projector-trace
  check, and the same checks at all three sensitivity multipliers. Cases may
  copy these constants as metadata but may not override them.
- Define `G=ker(B_w) intersect ker(H_w)` through `H_w Q_N_B` with the inherited
  parent scale of `H_w`;
  represent its positive-mass quotient as `Pi_P=Pi_N_B-Pi_G`, not set
  subtraction or selected SVD vectors. Do not call `Pi_P` a non-rigid
  mechanism projector. Use the governing symmetric augmented-basis primitive
  for all represented-subspace intersections; establish `R_N=R intersect N_B`,
  form `Y_R=Pi_P Q_R_N`, rank-reveal it with the inherited parent scale of
  `Pi_P`, set `Pi_RQ=projector(range(Y_R))`, and then
  `Pi_Z=Pi_P-Pi_RQ`. Require its rank to equal
  `dim(R_N)-dim(R_N intersect G)` at all multipliers. Never use raw
  `R intersect P` or `Pi_P Pi_R Pi_P`.
- Derive canonical bases from projectors using the registered column-pivot /
  two-pass procedure. Serialize JSON values with the exact `.17g` token/exponent
  normalization and sorted compact UTF-8/LF domain. Hash only the exact
  signed-zero-normalized C-order little-endian `<f8` snapshot bytes with the
  registered v2 header bound to the complete environment-manifest SHA-256.
  Never quantize, tune, or treat a snapshot digest as cross-runtime scientific
  identity. Set/verify the six one-thread controls before NumPy import, build
  and hash every exact manifest field/domain—including NumPy RECORD, runtime
  CPU features/dispatch, the Python executable, and all NumPy/NumPy-libs
  `.pyd`/`.dll` binary bytes—and fail closed on violations. Reject the governing
  explicit result-affecting BLAS/MKL/BLIS/OpenMP override names before import,
  bind every recognized-prefix environment entry (including `OMP_STACKSIZE`)
  without deleting it, then bind the warm-loaded one-thread BLAS runtime
  architecture/backend/library identity through threadpoolctl.
- Separate analytic rigid quotient classes through `Pi_RQ`; do not classify
  raw degenerate basis vectors or require principal-angle diagnostics.
- Validate constant and checkerboard candidates algebraically. Never label a
  positive-mass vector gauge.
- Assemble proof matrices independently from numeric element operators and
  connectivity; do not call shared ANYsolver assembly.
- Follow the governing deletion order exactly: retain the declared global
  node/DOF universe and indices, validate C references, delete element rows and
  incidence, identify/report orphan-coordinate gauge intersections, then apply
  supports/MPC/couplings without pruning, compaction, or remapping.
- Treat constraints/couplings/activity/deletion as explicit proof inputs and
  report their rank effects without claiming production validity. Separate
  affine RHS from homogeneous tangent `C_hat`, scale matching RHS rows with the
  same registered row norm, and report pseudoinverse feasibility separately;
  compute and report `G_C=ker([B_w;C_hat]) intersect ker(H_w)` and `Pi_P_C`.
  For constrained rigid semantics form `L_C=N_C intersect (R_N+G)`, then
  `Y_R_C=Pi_P_C Q_L_C`, `Pi_RQ_C=projector(range(Y_R_C))`, and
  `Pi_Z_C=Pi_P_C-Pi_RQ_C`, with expected quotient dimension
  `dim(L_C)-dim(L_C intersect G_C)`. Never use a raw rigid intersection or
  project a rigid vector excluded by the homogeneous constraints. Report these
  projectors without
  conflating local/free/constrained rank or affine feasibility.
- Keep local rank, assembled free rank, and constrained/reduced rank distinct.
- Load quarantined formulation modules only through the governing hash-checked
  synthetic `ModuleType`/`ModuleSpec` procedure; ordinary `import anysolver`
  and all real package initializers are forbidden. Compute module identity only
  from the exact canonical domain: raw bytes, reject UTF-8 BOM, strict UTF-8
  decode, CRLF-to-LF replacement, reject any remaining CR, UTF-8/no-BOM
  re-encode, then SHA-256. The recorded Windows raw-byte hashes are audit
  observations only, not accepted portable identities. Enforce the governing
  exact six-name case-folded allowlist; reject every pre-existing case-folded
  `anysolver`/`anysolver.*` key; never overwrite; and transactionally restore
  and identity-check the complete pre-load `sys.modules` key-to-object mapping
  and order on any loader failure.

## Exclusions

No edit to existing formulation modules/tests/docs, contract, package exports,
elements, serialization, recovery, assembly, activity/deletion, hot paths,
handoff/native-hybrid, integration worktrees, or siblings. No geometry import,
document parse, penalty, stabilization, stiffness invention, gauge application,
constraint application to production, option choice, or gate relaxation.

## Tests and handoff

The focused test must independently verify case-schema validation, exact
matrix dimensions, same-manifest deterministic output/hashes and cross-manifest
numerical-only comparison semantics, SVD rank decisions, projector
residuals, gauge/positive-mass/rigid/non-rigid partition, topology/connectivity,
constraint-rank and ordering behavior, abstract coupling semantics, and
activity/deletion topology changes. Include hostile cases: dependent MPCs,
permutations, disconnected/deleted components, threshold-near synthetic
matrices, exact zero/empty matrices, signed-zero snapshot normalization,
environment-manifest drift, invalid /
nonfinite inputs, preloaded-package import rejection, and repeat runs.
Permanently include the two-dimensional quotient counterexample, the unit-square
Rz/gauge coset with `P=7,RQ=6,Z=1`, augmented-intersection commutativity/full
containment/disjointness, rank/containment/idempotence/orthogonality at all
three multipliers, constrained `L_C` semantics, and a preregistered scale
family `A_delta=diag(1,delta)`, `Q=[0,1]^T` for
`delta in {0,2^-60,2^-40,1}`, with stable expected ranks `(0,0,1,1)`, proving
that a near-zero restriction inherits its parent scale. The residual tolerance
is identical at every SVD multiplier.

Only lightweight proof commands may run without a lease. Before commit, report
the exact diff, hashes, commands, results, and any interpretation blocker.
Pause for coordinator freeze and independent Heimdall audit before staging.
After authorization, make one atomic commit of the three registered plans plus
the four owned proof files—never coordinator packet files—and do not integrate.
