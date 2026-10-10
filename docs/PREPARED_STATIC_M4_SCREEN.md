# M4 shared recovery and bounded envelope screen

2026-10-08. Implemented in the isolated prepared-static candidate; not merged.

Shared recovery now evaluates the union of detailed and envelope elements once
per physical case. Full reaction diagnostics are likewise computed once before
independent selection. Eight-case numeric tiles reduce envelope winners while
canonical mechanical stages remain unchanged. Transactions copy only changed
winner modes. Selected histories and public summaries remain detached.

Independent review found and resolved selected-derived-field contamination of
envelope schemas and incomplete helper/constructor authority checks. Guards now
cover first private entry, summary, restart, resume and publication. Failed blocks
leave prior certified envelopes intact. Memory estimates include transaction and
reduction scratch, selected outputs and reaction tiles. Explicit memory limits
retain the existing conservative one-case policy.

## Measured results

Serial same-scope runs measured built-model to consumed whole-model envelopes
and selected histories, including preparation/factorization, loading, solve,
certification, recovery and output. Meshing excluded. Every process used the
specified ANYsolver venv, JIT enabled, one effective BLAS/Numba/OpenMP thread,
and the SciPy route with one factorization per owner. Sources remained stable.
These are six-element/eight-node mixed shell/beam fixtures, not the production
barge. Frozen full M3 source provided the incremental comparator.

Seconds, primary 64 cases and distinct holdout 256 cases:

| Family/cases | Native cold | M3 cold | M4 cold | Native reused | M3 reused | M4 reused |
|---|---:|---:|---:|---:|---:|---:|
| Free/64 | 1.665 | 1.896 | 1.614 | 1.456 | 1.044 | 0.755 |
| Supported/64 | 1.724 | 2.072 | 1.578 | 1.440 | 1.099 | 0.749 |
| Free/256 | 5.609 | 5.077 | 2.746 | 5.461 | 3.411 | 1.935 |
| Supported/256 | 5.558 | 3.922 | 2.791 | 5.522 | 3.302 | 2.034 |
| Supported/256 repeat | 5.550 | — | 2.781 | 5.435 | — | 1.984 |

At 256 cases, M4 versus native cold speedup is 2.043x free and 1.991x supported
(1.996x repeat). Reused speedup is 2.822x free and 2.715x supported (2.739x repeat).
Incremental reused improvement over M3 is 1.762x free and 1.623x supported.
M3 free cold preparation/run variation is retained, not discarded as an outlier.

All nine comparisons passed: 4,114,704 compared binary64 values, zero bit
differences, zero strict diagnostic failures and zero governing identity
differences, including associated fields. This comparison count includes overlap
between comparators and repeats; it is not a count of independent physical cases.

**Decision: INCONCLUSIVE for the strict cold >=2x target in both families.**
Retain the demonstrated improvement. Supported cold performance remains just
below the threshold on both attempts; no tolerance or target is rounded into a
pass. Reused complete workloads exceed 2x on these holdouts. No merge, release,
production-model speed claim or 10,000-case qualification follows from this screen.

## Memory and projection limits

M4 isolated peak working set was approximately 190–191 MiB on the 256-case
fixtures, versus approximately 186–187 MiB native. No 50% memory reduction.
Accumulator storage remained about 4.24 MB with fixed dimensions across 64/256;
the history sink retained zero cases and wrote selected histories to disk.
Output files and caller-retained results are separate from retained evaluator
state. Larger associated-field storage remains model/output dependent.

Two-length warm fits give M4 marginal costs 6.15 ms/free case and 6.69 ms/supported
case, versus native 20.86 and 21.26 ms. Including preparation and fitted constant
overhead projects 10,000 cases to approximately 62.6/68.1 seconds M4 versus
208.7/212.7 seconds native **on these tiny fixtures only**. These are unvalidated
extrapolations: the distinct holdout was also used in fitting, so it does not
independently validate the extrapolation. No measured 10,000-case boundedness.
Raw phase times, preparation, output and unattributed time remain in the JSONs.

## Verification and budget

All checks used the task runner and specified venv. Counts overlap:

| Evidence run | Selection | Result | Process seconds |
|---|---|---|---:|
| m4-solver-01 | Existing envelopes | 18 pass | 9.4017513 |
| m4-solver-02 | Initial shared regressions | 3 pass, 4 fail | 10.3184507 |
| m4-solver-03 | Shared + envelopes | 25 pass | 11.7556004 |
| m4-solver-04 | Shared + envelopes + independent selection | 29 pass | 15.4429210 |
| m4-solver-05 | Evaluator + Q4 + real ANYfem integration | 31 pass | 24.1139243 |
| m4-solver-06 | Authority subset | 5 pass, 6 deselected | 3.5357256 |
| m4-solver-07 | Final shared regressions | 12 pass | 6.8087658 |
| m4-root-independent | Native parity at blocks1/8/32; selections/aliases | 2 pass | 14.8567242 |

Run02 failures were erroneous exact test oracles using decimal2 instead of native
2.0000000000000004. Corrected to canonical values; exact comparison retained.
Failure logs remain. Historical incomplete checks and failures remain unchanged.
The independent reviewer ran no numerical jobs and recorded source findings,
repairs and final hashes; root separately executed the public integration checks.

Worker correctness:81.3771391/120 seconds. Root correctness:14.8567242/60 seconds.
Renewed **M4 benchmark epoch:115.712200200/120 seconds**,4.287799800 unused.
All14 benchmark processes completed; no timeout. Prior benchmark ledger remains
590.971911206/600 seconds, separate and unrenewed. No further campaign launched.
User ended meshing-chat coordination during this epoch; no further messages sent.

## Evidence and reproduction

Root: `C:/ANYworkspaceWork/prepared-static-20261008`.

- `evidence/M4_BENCHMARK_RESULTS.json`: exact results, comparisons, commands,
  runtime, ledgers, check selections and descriptive projections.
- `evidence/checks/m4-*/run.json`, stdout/stderr and JUnit: exact attempts,
  source hashes, effective runtime, elapsed time and failures.
- `evidence/M4_FINAL_MANIFEST.json`, `M4_REVIEW_DELTA.patch`: final source identity
  and product delta against frozen M3.
- `fem/.prepared-static-evidence/prepared-m4-independent-review.md`: review.
- `solver/.prepared-static-evidence/m4-solver-handoff.md`: implementation handoff.

Reproduction commands are recorded verbatim in run.json. They use
`run_check.py --kind benchmark --benchmark-epoch m4` with
`scripts/benchmark_prepared_envelopes.py --route stream|prepared --family
free|supported --cases 64|256 --history primary|holdout --reuse`. Frozen M3 uses
the recorded alternative PYTHONPATH. Do not replay using exhausted authority;
reproduction requires a new explicitly bounded allowance.
