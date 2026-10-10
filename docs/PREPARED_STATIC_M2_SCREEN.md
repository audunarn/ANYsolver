# Prepared whole-model envelopes: M2 implementation and screen

**Disposition: NO_GO for performance promotion.** The additive candidate is
implemented and remains unmerged. Its correctness and output capabilities improve,
but the measured screen does not demonstrate 2x complete-workload speed or 50%
lower peak memory with at most 5% slowdown. Barge performance is INCONCLUSIVE.
No 10,000-case numerical qualification, commit, merge or publication was performed.

## Implemented scope

Both preparation factories accept `envelope_recovery_config` independently of
`recovery_config`. The former selects whole-model envelopes; the latter selects
detailed histories. `envelope_result()` returns a detached summary with signed
min/max, signed absolute extrema, exact earliest-input ties, governing case/time/
position, coherent associated fields, snapshot provenance and completion state.

Canonical staged native recovery executes for every envelope sample. Full-load
pressure and acceleration accumulation, overlapping structural/case masses and
native derived measures preserve canonical arithmetic. The old cases000/048/576
counterexamples now have exactly matching full loads, displacements, stresses
and governing identities. Full-load tests also cover constrained-load differences.

Authority is checked around owned numerical blocks, including post-operation
checks. No scope spans user iteration, callbacks or yields. Independent review
found two issues: unpinned native scope factories and completion after reentrant
input cleanup. Both were repaired and independently rechecked. Factory replacement
and in-place code mutation, cleanup/exhaustion closure and cancellation now have
regression tests. Publication of envelope state is transactional per certified
block. Incomplete/failed streams retain the previous certified summary.

Recovery is grouped by native formulation but presently uses **one-element by
one-case canonical fallback tiles**. No vectorized recovery-kernel speed claim is
made. Whole-model affine matrices and per-case whole-model result dictionaries
are not used for envelope output. Selected histories still construct selected
results. Accumulators, associated arrays, transactional copies, owned recipes,
factor storage, input packets and numerical tiles enter memory accounting.
One-case memory refusal and stable accumulator/reset behavior are tested.

## Frozen comparison and runtime

Isolated solver base: `cff55d95e905ab689efdacdf08742a60614728c1`.
Isolated ANYfem base: `3e4eb7f206042931d496b98f39af5e2a40b5951f`.
The previous candidate is preserved in `../evidence/m2-baseline-candidate.zip`
with its manifest. Every execution records source hashes, exact command, effective
environment, process-tree timeout, process-wall duration and complete logs.
The final16/64/256 comparison source hashes match. The initial4-case smoke preceded
the final authority repairs and is not used to fit the projection.

Interpreter: `C:/Github/ANYsolver/.venv/Scripts/python.exe`. JIT enabled;
Numba/OpenMP/OpenBLAS effective threads1, verified in output. Both routes used
the existing SciPy backend and one actual numerical factorization per owner,
including the reused run; no PARDISO stale rebuilds. PARDISO is not qualified by
these measurements. Default APIs and pinned formulation sources are unchanged.

The driver lazily defines 10,000 distinct nonlinear/discontinuous time samples.
Metadata validation confirms10,000 unique samples in each history and no overlap
between primary and holdout. This is not a10,000-case FE run. Free cases combine
self-equilibrated pressure, nonproportional nodal loads and acceleration with
balancing forces. Supported cases use the same mixed beam/shell model with support.
Both small models contain6elements/8nodes; their timings are not barge predictions.

Built-model-to-consumed-output timing includes preparation, factorization, loading,
certification, all-model stress/reaction envelopes, identical selected histories
and output serialization. Meshing/model construction is excluded from workload
time but included in process-wall charges and process peak memory. Histories are
streamed to JSONL, never accumulated in a caller list. Output-file bytes are reported
separately. Comparisons are serial with route order alternated; cold and reused
measurements are distinguished. This bounded screen is not a repeated statistical
qualification campaign.

## Measured results

Times are seconds. Each cold result includes preparation and final consumed output.

| Family / cases | Stream cold | Prepared cold | Stream reused | Prepared reused |
|---|---:|---:|---:|---:|
| Free /16 |0.7171|1.5724|0.5239|0.6771|
| Free /64 |1.7799|2.1101|1.4984|1.4982|
| Free /256 distinct holdout |5.8186|5.2405|5.4380|4.9356|
| Supported /16 |0.7495|1.4463|0.5787|0.7790|
| Supported /64 |1.6956|2.1105|1.4804|1.4469|
| Supported /256 distinct holdout |5.4451|5.3936|5.3153|4.9025|

Holdout complete-workload speedups: **1.1103x free,1.0096x supported**.
Reused-owner speedups:1.1018x and1.0842x. These do not meet promotion. Small-history
regressions include roughly0.8s of candidate preparation plus accumulator copying,
canonical selected/envelope recovery and final output. The original profile
identified repeated authority scans as the old bottleneck (3.1606/3.7894 profiled
seconds); eliminating that overhead did not establish a2x end-to-end gain.

Both barge4-case attempts hit25s process-tree limits. The stream created an empty
history sink; the candidate had not created its history sink. Neither delivered a
certified output block before termination. Both process trees were confirmed dead,
and partial logs/files remain. No barge speedup, memory benefit or extrapolation
can be inferred. Do not spend further time automatically.

All seven completed matched comparisons (cold and reused) checked **2,959,664
numeric values**, including associated fields: zero IEEE754 binary64 differences,
zero strict diagnostic failures and zero governing-identity differences. These
counts include repeated associated values and are not independent physical trials.
The unchanged conservative stress diagnostic remains distinct from formulation/
quantity-specific acceptance in `../evidence/ACCEPTANCE_MAP.md`.

Holdout isolated process peak: free186.04MiB stream versus190.84MiB candidate;
supported186.47MiB versus190.57MiB. This includes imports/model build and shows no
50% reduction. Candidate retained accumulator estimates vary from4,228,358 to
4,229,996bytes free and4,228,436 to4,230,698bytes supported across16/64/256cases.
Array dimensions stay fixed; small variation comes from governing label/time
objects. Histories retained by the sink:0. This supports bounded design and the
tested range only; it does not establish measured10,000-case boundedness or peak
memory on the production barge.

## Projection, with its limits

Fit warm marginal cost from the primary16/64 runs; retain fixed output overhead
and the measured cold-first-use increment. Stream factories defer factorization,
so their near-zero constructor times must not be treated as total preparation.
All unattributed cold time is retained in the measured totals (holdout0.57–0.68s).

| Family / route | Marginal ms/case | Projected10,000 s | Holdout prediction error |
|---|---:|---:|---:|
| Free stream |20.301|203.4|−0.77%|
| Free prepared |17.108|172.4|−3.09%|
| Supported stream |18.785|188.3|−4.29%|
| Supported prepared |13.915|140.4|−15.99%|

These are **small-model projections**, not measured10,000-case results. The
supported candidate fit underpredicts the holdout materially and is not confirmed;
governing-update work and timing variation are not separately resolved by this
single bounded screen. Even these optimistic projections do not support2x.
No general production scaling claim follows, and no automatic campaign extension
is justified by the unused allowance.

## Verification and evidence

- `m2-integrated-solver`:66passed,31.8322335process seconds. Files:
  test_prepared_static_evaluator, contracts, independent, qualification, envelopes.
- `m2-integrated-fem`:60passed,17.5599613seconds. Files:
  test_prepared_static_adapter, integration, envelopes.
- `m2-existing-impact`:110passed,1failed,33.6904948seconds. Files:
  test_static_batch, static_envelopes, recovery_batches, analysis_session,
  static_batch_recovery_lease_scope, coupled_acceleration_guards, backend_counts,
  activity. Failure: `test_compiled_isotropic_s4_matches_scalar_oracle_for_warped_global_output`
  expected `compiled_isotropic_s4`, received `scalar_chunk_thread_pool`.
- `m2-existing-recovery-baseline`: same failure on unmodified main,7.8426180seconds.
  Main had independently advanced to`da1ba2e9`; changes from frozen base are only
  modal classification/test and CI files, not this recovery path or test.
- Worker failure/repair records remain in`../evidence/checks/m2-*`. Current
  examples cover supported/free selected histories and envelopes, early close
  and cancellation; the application worker's successful/intentional-exit logs
  are indexed in`../fem/.prepared-static-evidence/prepared-m2-handoff.md`.
- Independent review and repaired disposition:
  `../fem/.prepared-static-evidence/prepared-m2-independent-review.md`.
- Machine-readable results, projection arithmetic, phase/unattributed times,
  effective runtime and metadata checks:`../evidence/M2_SCREEN_RESULTS.json`.
  Per-run logs/manifests/JUnit and source identities:`../evidence/checks/`.

Paths above are relative to the isolated solver root unless explicitly stated.
Exact commands are in each run.json. Benchmark reproduction uses
`scripts/benchmark_prepared_envelopes.py --route stream|prepared --family free|supported|barge
--cases N --history primary|holdout --reuse --output PATH` through the existing
budget runner; barge additionally needs the frozen built-model fixture. Reproduction
is documentation, not renewed execution authority.

Benchmark total: **524.545961906/600 process-wall seconds**, including the prior
milestone, profiling, warm runs, failures and timeout cleanup. M2 consumed
154.246348600s: profile7.004610, comparisons59.802707100, confirmation62.368828200,
contingency paired barge25.070203300. **75.454038094s remain unused.** Campaign stopped.
Root correctness checks consumed90.925307600/120s; solver worker90.4013583/180s;
application worker73.4583128/90s. No prior authority was renewed.

Remaining limits: qualified grouped/vectorized staged recovery, production-model
whole-envelope preparation/output cost, production peak memory, and full10,000-case
qualification. Response patterns, approximation and new backends remain deferred.
Keep the candidate opt-in and unmerged; any further implementation or campaign
should use a new bounded decision rather than presenting this screen as accepted.
