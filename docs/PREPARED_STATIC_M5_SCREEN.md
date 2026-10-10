# M5 numeric envelope fields — performance NO_GO

2026-10-08. The experimental extraction is implemented and verified, but the
matched screen does not establish a reliable incremental speedup over M4.
Keep the measured M4 route as the performance reference. M5 remains unmerged
in the isolated candidate; its full M4 predecessor and failed performance
evidence are preserved. No main-repository source was changed by this milestone.

## Change and correctness

The single canonical Q4 staged arithmetic core returns20ordered numeric fields.
Eligible envelope recovery copies these directly into bounded eight-case tiles.
Detailed output uses a detached dictionary wrapper around the same core.
Field selectors are compiled per element/block, not once for the evaluator.
Native formulation and explicitly requested principal-stress envelope paths
retain record-based fallback. All existing load/output capabilities remain;
this is not a new formulation, backend, response basis or approximation.

Product delta: `prepared_static_q4.py`, `prepared_static_shared.py`.
New regressions: `tests/test_prepared_static_numeric.py`.
Independent review found no concrete defect in arithmetic/order, aliases,
schema, authority, bounded workspace or existing transactional publication.
Exact source/review hashes are retained in `evidence/M5_FINAL_MANIFEST.json`.

| Check | Scope | Result | Process-wall seconds |
|---|---|---|---:|
| m5-solver-01 | New numeric/activation/fallback/authority tests |9pass|6.7135382|
| m5-solver-02 | Existing Q4/envelope/shared checks |42pass|23.9642294|
| m5-solver-03 | Evaluator and ANYfem integration/envelopes |29pass|19.5148943|
| m5-root-independent | Public native parity, selection/alias independence, envelope-only block1/8/32 |3pass|18.7964503|

All83checks passed; no M5 correctness failures or timeouts. Historical failures
remain untouched. Worker correctness used50.1926619/120seconds, root18.7964503/60.
Reviewer performed source review and inspected evidence, with no numerical jobs.

## Measured complete workloads

Serial alternating M4/M5, same64-case primary and256-case distinct holdout,
whole-model envelopes and identical selected histories. Model build/meshing
excluded from workload timing; preparation/factor, loads, solve, certification,
recovery and consumed output included. Reused timing includes the same work
except initial preparation. Single-thread effective BLAS/Numba/OpenMP, JIT on,
SciPy backend, one factor per owner; no source changes during any run.

Seconds:

| Family/cases | M4 cold | M5 cold | M4 reused | M5 reused |
|---|---:|---:|---:|---:|
| Free/64 |1.579|1.560|0.759|0.705|
| Supported/64 |1.612|1.641|0.763|0.762|
| Free/256 |2.747|3.068|1.941|2.001|
| Free/256 repeat |2.732|2.892|1.941|2.022|
| Supported/256 |2.769|2.725|1.960|1.965|
| Supported/256 repeat |2.841|2.857|2.034|1.931|

All six comparisons passed bit-for-bit:2,802,528 compared values, zero governing
case/index/time or associated-field differences, zero strict diagnostic failures.
Comparison counts include repeated outputs, not independent physical cases.

Free holdout cold regressions were11.7% and5.8%, reused3.1% and4.2%.
Supported cold differences were approximately1.6%faster and0.5%slower; reused
approximately0.2%slower and5.1%faster. The64-case free gain did not confirm on
holdout. Peak working sets remain about190MiB; no material memory reduction.
No uncertainty bound or statistically significant improvement is asserted.

## Interpretation and stop decision

The initial profile showed modest dictionary/field-discovery work, rather than
the dominant remaining cost. A second charged candidate profile confirmed that
the route activates: only133Q4dictionary wrappers for389numeric recoveries,
including preparation and selected histories. The previous path constructed
records for all389Q4recoveries. Recursive per-case field discovery was replaced
with compiled selectors. Yet this local reduction did not yield a reliable
complete-workload improvement.

The profiled shared-recovery times were0.902s baseline and0.718s candidate, but
other unrelated cumulative times also shifted. These instrumented, overlapping
times are diagnostic evidence, not an end-to-end speed claim. They do not
establish that new computation alone caused the unprofiled cold regression;
preparation and host variation remain mixed with small overhead changes.
The repeatable failed speed screen is sufficient to refuse performance promotion.
Do not weaken checks or broaden the optimization to rescue this result.

**NO_GO for M5 performance promotion.** Preserve the experiment and stop this
campaign. The previous M4 evidence and its limits remain valid for M4 only.
These six-element/eight-node fixtures do not qualify production barge or10000
cases. No new10000-case projection is useful from this unsuccessful increment.

## Resources and evidence

New M5 benchmark allowance120seconds; used **93.142273100seconds**, including
both profiles, all cold/warm runs and repeats.26.857726900seconds left unused.
All14processes completed. Prior M4=115.712200200/120 and legacy590.971911206/600
ledgers remain unchanged. No automatic renewal, further run, commit, merge or push.

Evidence root: `C:/ANYworkspaceWork/prepared-static-20261008`.

- `evidence/M5_BENCHMARK_RESULTS.json`: exact timings, comparisons, runtime,
  commands, counts and separate ledger.
- `evidence/checks/m5-*`: immutable attempts, stdout/stderr, JUnit, manifests.
- `evidence/m5-profile-*.pstats` and breakdown JSON: profiles, retained in full.
- `evidence/M5_REVIEW_DELTA.patch`, `M5_FINAL_MANIFEST.json`: experimental delta.
- `m5-baseline/solver/src`: preserved full M4 source comparator.
- `fem/.prepared-static-evidence/prepared-m5-independent-review.md`: review.
- `solver/.prepared-static-evidence/m5-solver-handoff.md`: implementation handoff.

Exact reproduction commands are recorded in each run.json. They use the required
ANYsolver venv and `run_check.py --kind benchmark --benchmark-epoch m5`, with
the same benchmark script and recorded baseline/candidate PYTHONPATH. No further
execution is implied by retaining unused allowance after this stopped screen.

Disposition update: user selected M4. Active product source is restored exactly
from the frozen M4 comparator. M5 source files, focused test and former guide are
archived in evidence/m5-experiment; this report and all failed performance evidence
remain unchanged. The historical M5 manifest hashes apply to those archived files.
