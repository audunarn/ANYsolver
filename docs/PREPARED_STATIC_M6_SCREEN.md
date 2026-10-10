# M6 bounded preparation screen

User renewed120 cumulative process-wall seconds. Twelve serial benchmark processes
used108.679695200 seconds, leaving11.320304800 stopped/unspent. Every run completed
successfully with unchanged source identities; no numerical failures/timeouts or
unaccounted warm-ups. No further campaign is scheduled.

The comparator is the frozen M4 source in `../m6-baseline/solver/src`; candidate
changes only prepared_static_loads.py (source hash in the implementation report).
The same scripts, Python interpreter, NUMBA_DISABLE_JIT=0 and single-thread runtime
settings were used. Measured threadpool metadata confirms one OpenBLAS thread;
complete controls each used one SciPy factorization and no PARDISO factorization.
Imports/startup/fixture loading and warm execution are charged to the allowance,
even where excluded from the reported built-model workload interval.

## Representative acceleration preparation

Full saved barge:4349 solver nodes,5349 elements, complete fixture geometry;
no meshing or model truncation. These measurements compile only the acceleration
load capability, retain its native full-F oracle and consume four full load vectors
with signed/general accelerations and case-added mass. They do not time stiffness,
solve, recovery, application load definitions or an entire barge workflow.

| Order | Baseline preparation | M6 preparation | Reduction |
| --- | ---: | ---: | ---: |
| baseline then M6 |17.1911s|10.1240s|41.1%|
| M6 then baseline |17.1390s|10.0147s|41.6%|

Repeat gain is approximately7.1seconds and1.70–1.71x for this preparation stage.
All four full-load SHA256 digests agree; native oracle residual is0.0 in each run.
Four-case load evaluation stayed0.155–0.159s. Build/BC time stayed0.495–0.515s.
No runtime-loading speedup is attributed to this preparation-only change.

Load-map retained bytes fell18617896 to18197424 (420472bytes removed). Isolated
process peak working sets:baseline270.79/254.03MiB, candidate253.27/252.57MiB.
The repeat does not establish a large peak-memory gain. Other startup/import time
remains included in the process ledger; it is not assigned to preparation.

## Complete mixed-model controls

Each run consumes64 arbitrary nonlinear-time cases, selected histories and
whole-model stress/resultant/reaction envelopes, then repeats on the same evaluator
for warm timing. Free-free control has two disconnected mixed bodies(12elements);
supported control has6elements. These are controls, not representative barge sizes.
A distinct holdout history was run in reverse candidate/baseline order.

| Workload | Baseline cold | M6 cold | Baseline warm | M6 warm |
| --- | ---: | ---: | ---: | ---: |
| free-free primary |2.5248s|2.4839s|1.2925s|1.2687s|
| free-free holdout |2.4890s|2.4064s|1.2441s|1.2333s|
| supported primary |1.6202s|1.4873s|0.7629s|0.7267s|
| supported holdout |1.5461s|1.5682s|0.8153s|0.7675s|

Cold intervals include preparation/factorization through serialized histories and
envelopes; warm intervals include loading through output with existing preparation.
Phase timings, output bytes and retained-state diagnostics remain in each result;
unattributed overhead is not removed from complete times.

Free-free cold improvement1.6–3.3%; supported primary8.2% improvement failed to
repeat (holdout1.4%slower). Warm differences cannot be attributed to M6 because its
runtime code is unchanged. No repeatable slowdown above5% is observed. Peak memory
is effectively unchanged:free approximately198–199MiB; supported189–190MiB.

All histories, governing case/time/index identities and associated envelope fields
match. Recursive comparison checks2,443,712 binary64 values exactly, including signed
zero. Barge vectors have identical byte digests. This augments, not replaces, prior
canonical independent correctness checks.

## Decision

Keep M6 as a demonstrated preparation optimization. The complete-workload2x or
50%memory promotion screen is NO_GO for this incremental change; the small effects
are not a new general batch-speed claim. No10,000-case projection or qualification,
full-barge solve speedup, publication or merge is established here. M5 remains
inactive and all failed historical evidence is preserved.

Evidence relative to `C:/ANYworkspaceWork/prepared-static-20261008`:

- `evidence/M6_BENCHMARK_RESULTS.json`: ledger, exact comparisons, measurements.
- `evidence/checks/m6-{barge,free,supported}*`: exact commands, source hashes,
  effective environments, complete stdout/stderr and process-wall accounting.
- `evidence/m6-*.json`: phase times, runtime/backend facts, memory and output paths.
- `evidence/m6-*.jsonl`: consumed selected histories and normalized envelopes.
- `evidence/m6_mass_benchmark.py`: representative preparation reproduction harness.
- `solver/scripts/benchmark_prepared_envelopes.py`: complete-control harness.

Reproduction requires a separately available execution allowance. Do not infer
permission to run from these paths or the declared runner epoch.
