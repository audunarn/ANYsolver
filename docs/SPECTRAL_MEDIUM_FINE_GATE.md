# Medium/fine spectral performance gate

Status: profiling and implementation in progress; no optimization accepted yet.

## Frozen comparison scope

The solver baseline is `5883ae1d7ad1b5abea3a660cc8feecc7e65c7154`.
Use the committed current ANYstructure adapter from an isolated checkout and
record its complete commit/tree identities with every campaign. Never use the
active checkout's uncommitted files as benchmark inputs.

Exercise the actual panel and cylinder runtime routes at medium and fine mesh
fidelity. Separate fixture construction, first analysis, retained analysis,
modal-only analysis, and complete static-plus-buckling analysis. Request five
modes for initial profiling; include ten modes in the selected-change gate.
Count actual nodes, element families, total/reduced DOFs, nonzeros, and accepted
modes. An unavailable or failed route is a recorded obstruction, not a timing.

## Execution and evidence

Timing children run serially, with one numerical-library thread, a 600-second
wall bound and 24 GiB process-tree memory bound. A wave lasts at most 1,800
seconds. Terminate complete owned process trees on bound violation. Preserve
partial diagnostics; never write successful canonical evidence for a failed
run. No automatic retries. Use exclusive output paths.

Keep unprofiled timings separate from instrumentation runs. Capture wall/CPU
time, peak RSS, phase diagnostics, call counts and cumulative/self-time profile
leaders. Bind source identities, interpreter, imported package paths, thread
settings and numerical-library versions. Preserve existing public result data
and checks; do not count an incomplete solution as an improvement.

## Candidate and acceptance

Use the new profiles to select a narrow combined validation/geometric-assembly
change. Preserve full validation at capture, caller-code boundaries and
finalization; preserve mutation/ABA detection, malformed-state rejection,
cancellation and current-state restrictions. No element equations, tolerance,
mass policy, public selectors or defaults change.

Screen with three serial order-balanced pairs. Only a screened winner advances
to one warm-up and seven alternating baseline/candidate pairs. Promotion needs
at least 10% complete-route improvement on its target and no unexplained
regression above 5% on retained routes. Report median, MAD and p95, with separate
profile evidence explaining the removed work.

Verify original-pencil residuals, eigenvalues, clustered mode subspaces,
constraints and physical results using existing acceptance tolerances. Run
relevant existing lifecycle, prestress, mutation, callback, current-state,
mixed-element and fallback checks plus focused new regressions. Parent inspects
the complete diff and verifies before a fresh independent read-only review.
Only a `ship` review can accept the change. Record unsuccessful prototypes
without promoting them.

The final report ranks compiled kernels, matrix-solver alternatives and further
Python optimizations from measured complete-route costs. Kernel-only speedups
are insufficient to select a new backend.
