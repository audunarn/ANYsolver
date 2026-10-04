# Supporting factor-residual integration review V1

Read-only review in C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001. No numerical job, test, source edit, Git operation or worker was run by this reviewer. This is supporting OpenAI input, not scientific qualification, different-family acceptance or F03 authority. Earlier interval/factor evidence remains unchanged.

Verdict: no correctness blocker identified in the helper's directed comparison/residual proof or current driver integration under the unchanged stated ordinary IEEE sparse-arithmetic assumptions. The actual same-target case returned RESOURCE_REFUSAL before comparison or residual assessment. It supplies no new positivity, factor-quality or negative-mode evidence.

## Helper correctness

r8_bl5_sparse_factor_residual_dev.py:142–164 owns canonical finite buffers, checks matching square order, complete plain-int symmetric permutation, nonzero factor diagonal and exact lower triangularity (including refusing stored zero upper entries). It refuses asymmetric target input instead of repairing it. These enforce the consequential counterexample conditions from factor-residual-design-review-v1.md.

The positive recurrence at54–78 encloses each product before summation, rounds the numerator/division outward and refuses product/division underflow or overflow. The forward traversal and actual-transpose reverse traversal at166–179 bound infinity/one norms of the comparison inverse; upward norm product and downward reciprocal give mu_lower. No global inverse, backend condition estimate or backend inertia is used.

The exact-real shifted target is enclosed at181–193. Each nearest diagonal subtraction is surrounded by downward/upward endpoints; an outward maximum radius bounds the diagonal operator discrepancy. The independently enclosed stored F F.T product and rounded target/product difference at195–201 are combined with that shift error. Strict downward mu-rho positivity is required at203–206. F construction rounding needs no extra error because F is treated as exact stored and its residual is independently enclosed.

Resource refusals and direct arithmetic-domain refusals return HOLD. Validation/programming/MemoryError propagate rather than being mislabeled numerical failure (208–215). A later deadline refusal can turn an otherwise computed margin into HOLD; the driver accepts only the actual positive status, so resource status cannot accidentally pass.

## Resources and controls

Workspace checks precede target transpose work and native product allocation. Complete symbolic column cliques at81–118 count original supports, including cancellation, and bound product/residual nnz, clique/update work and combined storage. The conservative workspace model explicitly requires external supervision for unexposed/native overhead. The default 2400-order admission is unchanged; this case receives the already-declared 15585-order/768MiB proof budget. No old default is widened.

Tests actually read cover exact Fraction inverse/comparison recurrences, nonunit signed diagonal and asymmetric transpose norms; exact factor-work/shift/residual containment; zero/negative/bad-factor margins; wrong symmetric permutation; upper-entry counterexample; missing/nonfinite/duplicate inputs; exact symmetry and invalid shapes; symbolic cancellation and resource refusals before multiplication; explicit-budget admission; sparse-product underflow; all-ones comparison growth; owned arrays; and propagation of injected RuntimeError/MemoryError. No tests were run by this reviewer.

Saved test-v1: 25 passed in 2.31s; supervised terminal exit 0, elapsed 2.7197335s, sampled peak 94,330,880 bytes, numeric-or-unresolved maximum 1. These small controls substantiate the primitive; they do not establish success of the mechanical candidate.

## Driver/API/source identity

Final probe e6f6ba64... pins helper cd562724... and retains earlier immutable v9/pair/predecessor-source guards, exact outward 2epsilon shift, positive graph metric, nonempty pools 1, product-free/fresh-output guards and pinned supervision. Every returned ndarray is moved into NPZ under proof_ prefix, matching actual comparison_forward_upper/comparison_transpose_upper and diagonal enclosure API. Accepted status matches the helper's actual POSITIVE_SHIFTED_FACTOR_RESIDUAL and requires a finite positive physical graph-margin transfer.

Helper/test/probe/wrapper bytes match sources-v1/{helper,tests,probe,run}.py. Recorded helper, saved primitive, interval, caller and sparse-certificate dependency hashes match current source. The factor-v1 JSON binds predecessor 59a87afe1e805880c442a5446291887ca53addd13078727a48fd6309b3819741 and predecessor NPZ a9931adc9e200884e67ed812f7c292fa3cf362ee798b826e693b37389b2fe7f5. Its paired NPZ hash matches recorded be681f798c07cacdee15aab2fb13a81749efa21147721d7d8442e45f8d904194. Producer diagonal/permutations and owned F CSR buffers are present. No comparison arrays exist because their stage was never reached.

## Actual same-target result

factor-v1.json is terminal HOLD_MECHANICAL_KERNEL; helper HOLD_FACTOR_RESIDUAL / RESOURCE_REFUSAL, positive=false. Matrix order 2745, target nnz 222429, candidate factor nnz 170206. Initial/copy workspace estimate 897,634,560 bytes exceeds frozen proof 805,306,368 bytes, so the helper stops before check_arithmetic/comparison/product. mu_lower, rho_upper and margin_lower are absent; physical lower bound is null. This is a resource-admission result, not failure of the comparison recurrence or mathematical factor-residual inequality.

The target epsilon 5.855229651277453e-9, shift 1.1710459302554907e-8 and graph metric 75.71919020532987 remain unchanged. Helper elapsed 0.0196523s, driver 0.079462s; supervisor terminal exit 0, elapsed 0.5929524s, sampled peak 73,240,576 bytes, numeric-or-unresolved maximum 1 under 600s/1GiB/8-thread cap. The low sampled peak does not validate the estimated live footprint of phases that did not run, and supplies no measured full-assessment savings. No silent budget increase or automatic rerun is justified by this artifact.

Final reviewed hashes:

- helper cd56272435d4df22de7a08ff27362faf453c35ac1f97f138976d1f3aa70359f1
- tests c7f422fdc1c522333283d8ceea580f1a276ccd69d592e10c6d70e4cea17f79a4
- probe e6f6ba64da0dd51cf5314ef4fa9f5f4401d365db22a3f251492a8e51c7279a3f
- wrapper 9367ed1ef7d5abe7f9f1c78e97f9b523a07632ec0c4925e6718d8460760ab5af

A revised resource model, budget or streaming residual implementation would be a new bounded source contract with its own review; it must preserve this refusal. Current actual-kernel sign remains unresolved.