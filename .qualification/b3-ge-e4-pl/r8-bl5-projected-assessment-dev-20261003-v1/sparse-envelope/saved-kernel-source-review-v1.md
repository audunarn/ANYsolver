# Saved-kernel source review v1

Supporting OpenAI Read review only. No numerical jobs, tests, source edits, Git operations or workers were launched by this reviewer. Reviewed repository: C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001.

No blocking false-positive mathematical defect was identified in the reviewed source. The two saved assessments correctly remain HOLD; neither supplies a positive mechanical-kernel certificate. This review does not accept the formulation or qualify a larger envelope.

Reviewed SHA256:
- scripts/r8_bl5_sparse_kernel_saved_dev.py: 515c6fae18de3dc6b4022d50ad2a110425935c0dcd8a0799d797cb960bc54e38
- scripts/r8_bl5_sparse_kernel_interval_dev.py: 109742c759d19e48b0641bccafd37486dce065a4ca59116744692694a1f80301
- tests/test_r8_bl5_sparse_kernel_saved_dev.py: b7aaba09f74ebf13bc90b42710926cb37ba5f2050c4059f73cc026aaeb677104
- tests/test_r8_bl5_sparse_kernel_interval_dev.py: fc606be5acd6eea93787db4d29c164d665739540ebb7897305799d10f9ec4cda

## Mathematical checks

1. The graph proof targets actual C scaled by the declared stored row/physical scales. Elementary boxes at saved source lines139–159 include the scaling rounding. Lines162–214 establish every constraint row, unique disjoint pivot columns, absence of foreign-support pivot coupling, and all active true coefficients, including coefficients hidden by rounded zeros. The local inverse residual at lines76–95 proves invertibility for every D in its box; it does not infer rank from LU pivots. The exact graph Z*=[I;-D^-1 E] therefore spans the complete constrained physical space. The bounded residual gives ||Zhat-Z*||F. Both roots and released variables remain in the predecessor's physical inventory; only the local resultant roles are eliminated.

2. The saved-K stationary map at lines217–254 uses distinct Kxp and Kpx and does not assume complete-K symmetry/SPD. Local inverse/lift residuals, rounded couplings, each Schur update, accumulated sparse additions, and mismatch against saved S are enclosed. Thus the target is the exact-real Schur of saved binary64 K, rather than the rounded reduced S or a repaired tangent. The predecessor binding at lines283–306 is material: complete physical/resultant inventory semantics are inherited from the accepted bounded dense assessment, not independently re-established here.

3. Sparse product error at lines105–128 is a conservative gamma bound against the positive absolute product; the maximum row count bounds each dot length. The helper refuses possible underflowing elementary products. The claim remains conditional on ordinary IEEE sparse accumulation; the FTZ/DAZ check is correctly invoked before local residual proofs (lines168 and268). Local directed operations include absolute underflow enclosures. The exact Fraction square-root endpoint check is inherited from the unchanged dependency.

4. Lines325–338 correctly combine graph perturbation, exact Schur perturbation, both sparse products and triangle/skew replacement into epsilon. With the interval proof of representative-2*epsilon*I positive, the actual quadratic work is bounded below by (shift-epsilon)||y||². Lines355–360 divide by the upper graph metric ||Z*||², giving a bound in the declared scaled physical Euclidean norm. This is not an orthonormal-coordinate eigenvalue equality or an inertia statement about nonsymmetric full K.

5. New interval helper lines187–227 builds complete structural elimination closure. The ascending neighbour clique adds every generated lower-triangle edge regardless of numerical cancellation. The subsequent primitive still independently rejects missing initial/clique entries. Numeric LU contributes ordering only; its omitted zero fill no longer controls the proof. Fixed order/fill/update/workspace ceilings remain explicit. Native factorization and overall process memory/time require the external supervisor; the Python workspace estimate is not a total RSS measurement.

## Observed retained evidence

I read changed-test-v3/stdout.log and execution.json: 28 passed, exit0, sampled numeric/unresolved maximum1. These are root-run results, not reviewer-run tests. Earlier saved-test-v1 retains 11 passed/1 failed; saved-test-v2 retains the affected control's pass. whole_half-saved-proof-v1 retains FAILED because numeric LU fill omitted required entries.

Both current assessment JSONs match the reviewed source/dependency hashes and their supervised jobs exited0:
- physical625/kernel585: epsilon1.1379229439889624e-7, graph metric1870.3100323113947, shift2.275845887977925e-7. Interval pivot576 crosses zero after577 completed pivots; HOLD_CERTIFICATE.
- physical1057/kernel1017: epsilon2.9553960060682144e-5, graph metric120728.71516530291, shift5.9107920121364295e-5. NONPOSITIVE_REPRESENTATIVE at shifted pivot836; caller correctly reports HOLD_CERTIFICATE. The stationary contribution2.9528179823744e-5 dominates. This is failure of this conservative shifted representative, not a counterexample to the actual mechanical kernel.

The bounds and graph/representative arrays are now retained before the interval verdict (saved source339–349). Original failed evidence and positive dense-reference results remain distinct.

## Conditional next repair

Fixed positive column equilibration is mathematically permissible, but the future implementation is not covered by the hashes above. Treat a finite strictly positive stored diagonal T as exact chosen coordinates and target W*=Z* T. Bound rounded-W error by max(T)*eZ plus scaling-rounding error; recompute all graph/operator/product/triangle terms and Gupper=(||What||+eW)². Identity-row smin>=1 no longer applies after T; completeness follows invertibility of T. A rounded positive A diagonal selects coordinates only, not actual positivity. Powers-of-two scaling can avoid ordinary normal-range scaling rounding, with explicit overflow/underflow guards.

Directed higher-precision elimination is also permissible if entries and shift are imported exactly from binary64, every endpoint product/division/update is rounded outward, and any exported endpoints are converted outward. More precision alone with round-to-nearest is not an interval proof. Keep the derived error/shift contract and zero-crossing HOLD distinction unchanged.

These saved cases do not demonstrate scalability or stability over the seven-ratio/three-level envelope. Existing order/resource ceilings, mandatory external acceptance, and different-family scientific review remain open.
