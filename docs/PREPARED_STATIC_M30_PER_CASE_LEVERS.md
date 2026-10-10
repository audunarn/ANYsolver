# M30 — per-case levers (bitwise identical)

2026-10-10. Owner: Claude (Anthropic). Not merged, committed or published. Owner
request: "Proceed as recommended" (the M29 recommendation). Pre-M30 comparator:
`../../m30-prefix` (solver and ANYfem sources).

## Changes

| Lever (M29) | Change | File |
|---|---|---|
| Lean reaction maps | `_planned_compact` tests all rows for non-zeros with one vectorised operation instead of one `np.any` per node; same rows copied in the same order | `prepared_static_recovery.py` |
| Products with K | removed again after the platform check (see "Platforms"): the block-wide residual `K @ U - F` relied on two scipy loops agreeing bit for bit, verified only on Windows; reactions use the pre-M30 single products | - |
| Vector maps | `evaluate_groups` processes elements in chunks of 512 (`GROUP_ELEMENT_CHUNK`), reusing each chunk of the map for every column of the block; each element's product per column is unchanged (M31b/M31c, after review: only under NumPy's default error state with round to nearest and no flush-to-zero, with the pre-M30 column order whenever a value is non-finite, so warnings and exceptions are those of the pre-M30 code) | `prepared_static_vectorized.py` |
| Backward error | `_certified_backward_error` reproduces `assembly._backward_error` for one solve with the operator's row-sum data computed once at preparation (`_operator_norm_data`, the same expressions), used only for the exact matrix it was computed for; the evaluator's `_backward_error` attribute is still honoured (a replaced function, for example a test's fault injection, is called as is); the shared `assembly._backward_error` is unchanged (M31b/M31c, after review: the row-sum data is computed per block after its solve, and again after a canonical solve inside a block, and used only for an immutable CSR matrix whose parts are unchanged; "the original" is the function captured at import, so a rebound module attribute is called as is; the maximum is taken only of finite sums, as in the original) | `prepared_static.py`, `prepared_static_response.py` |
| ANYfem wet-element cache | the prepared load context keeps its wet-element sets for its lifetime (they depend only on the owned project, mesh and wet surfaces) with their bytes still reserved; the other case caches stay per case; a failure while a request is resolved clears everything (M31b/M31c, after review: keyed by surface identity and checked against the surfaces' content on every use, so entries left after other failures stay valid; dropped if the reserve shrinks) | `fem/src/anyfem/solve/prepared_static.py` |

Not done: checking the response authority once per block instead of per
`_require_open` call (M29 lever 5, about 0.6 ms per case). Those checks sit right
after caller-code windows (the request iterator and the cancellation token), so
moving them would change the authority model; not worth it without a separate
review.

## Verification

- New tests `tests/test_prepared_static_response_m30.py` (23 after the removal of
  the block residual and its 4 tests): each changed function against a copy of
  its pre-M30 form or the shared implementation it reproduces, bitwise: compact
  maps (empty, zero rows, NaN, signed zero), backward error (random, zero, empty and overflowing matrices,
  non-finite solutions, foreign matrix, multi-column, non-finite matrix data,
  injected implementation), chunked vector maps (chunks 1, 3, 7, 512 x 1, 5, 32
  columns), the certification norm's operator. M31b extends them (see the M31
  report): exceptions and warnings under six NumPy error states, the per-block
  norm in a running evaluator, the error-state guard of the vector maps.
- ANYfem `tests/test_prepared_static_wet_cache.py` (2): the set is kept across
  cases with reserved bytes, other caches stay per case, a failed case clears
  everything; the existing cache test (`test_case_caches_have_reserved_bound_...`)
  passes unchanged.
- Suites: regression set 172 passed, 1 skipped on the final M30 source
  (`m30-claude-01d`; the 176 of `m30-claude-01b` included the four block-residual
  tests removed afterwards); base suites 112 of 115, the three known pre-existing
  failures (`m30-claude-02c`); ANYfem 60 of 60 (`m30-claude-03c-fem`). A first run caught that
  `test_failed_certificate_falls_back` injects a failing backward error through
  the evaluator attribute; the helper now honours it.
- Cross-version probe `../../evidence/m26_vector_probe.py` (317 recovered elements,
  pressure and nodal patterns, envelopes): pre-M30 and M30 identity sections equal
  (`m30-vector-probe-pre/new`).

## Barge, 10,000 cases (epoch m30)

Measured with the block-wide K product, which was removed afterwards (about 0.5 ms
per case, so the final code is expected at about 23 ms per case). The final code
was checked on 600 barge cases (`m30-barge-600-final`): histories and envelope
byte-identical to M28 (its timing overlapped a test run and is not used).

Same harness and case list as M28 (`m28_case_parallel.py`, the 600 saved cases
cycled to 10,000, block 32, lean, default mode), run `m30-caseparallel-10k`:

| Route | M28 | M30 |
|---|---:|---:|
| serial, preparation | 81.8 s | 82.4 s |
| serial, cases | 381.1 s (38.1 ms/case) | 226.4 s (22.6 ms/case) |
| serial, total | 464.9 s | 310.7 s (1.50x) |
| 8 workers, wall incl. merge | 229.7 s | 193.6 s |
| 8 workers, per-worker cases (1,250) | 94-98 s | 55-57 s |
| 8 workers, per-worker preparation | 97-115 s | 116-120 s |

Identity: the M30 serial and 8-worker per-case digests equal the M28 serial digest
(all 10,000 cases); the merged envelope equals M28's; the M30 serial envelope file
is byte-identical to the M28 serial file. Peak memory of the 8-worker group 9.3
GiB (as before).

Per case (product phase timers, serial, ms):

| Phase | M28 | M30 | Saved |
|---|---:|---:|---:|
| recovery (reaction maps, vector maps, K products) | 16.64 | 7.90 | 8.74 |
| outside solver phases (ANYfem wet cache) | 11.05 | 8.63 | 2.42 |
| solve (backward error) | 3.64 | 1.53 | 2.11 |
| certification (backward error) | 3.41 | 1.40 | 2.01 |
| load evaluation | 2.21 | 2.13 | 0.09 |
| total | 37.18 | 21.79 | 15.39 |

The M29 estimate was 15-18 ms. Under 8-way contention a case still takes about
2x longer per worker (45 vs 22.6 ms), so the levers did not loosen the
contention; the 8-worker run is now 62% preparation.

## What remains (per case, 21.8 ms)

ANYfem load construction and glue 8.6 ms (wet-pressure expression evaluation and
fluid side per element, about 4.6 ms; per-case authority checks at caller-code
windows), recovery 7.9 ms (vector maps about 3.2, envelope fold about 2.2),
load evaluation 2.1, solve 1.5, certification 1.4.

## Effect on the options for long histories

| 10,000 barge cases | Time |
|---|---:|
| serial, M28 | 465 s |
| serial, M30 | 311 s |
| 8 independent workers (option A), M30 | 194 s measured |
| prepare once and send the state to 8 workers (option B) | about 150 s, estimate |
| option B with M27 parallel preparation | about 115 s, estimate |

With faster cases, the replicated preparation is now the larger cost of option
A, which makes preparing once (option B) relatively more attractive, at the
complexity and trust cost described in M27/M28.

## Platforms (Linux, macOS)

Static checks: the solver lines added since the pre-M16 baseline (1,701) and the
new ANYfem prepared-static files contain no OS-specific code; all 61 changed
product and test files compile under Python 3.11 and 3.14 (declared range
3.11-3.14); no numpy-2-only API is used in them. OS-specific material exists
only outside the product: the benchmark harness (`run_check.py` with a Windows
interpreter path; CRLF-aware file comparisons) and the M27 prototype and its
requirements (a Windows job object; Linux/macOS need process-group or
parent-death equivalents).

Linux run (WSL Ubuntu 24.04, Python 3.12.3, kernel 6.6; sources and pure-Python
ANY* packages copied to the Linux file system; logs in
`../../evidence/linux-m30` and `../../evidence/linux-m30-run2`):

| Environment | Regression set | Base suites | ANYfem |
|---|---|---|---|
| numpy 2.4.3, scipy 1.16.3 (as Windows) | 172 passed, 1 skipped | 112 of 115 (the three known failures) | 60 of 60 |
| numpy 1.26.4, scipy 1.11.4 (declared minimum) | import fails | import fails | import fails |

- With numpy 1.26 `anysolver` cannot be imported: the pinned `boundary.py`
  imports `numpy._core._ufunc_config`, which exists only in numpy 2. This import
  is already in the pre-M16 baseline, so the declared `numpy>=1.26` was wrong
  before this work; the effective minimum is numpy 2. Not fixed here (pinned
  file; the declaration is the owner's call).
- First Linux run: two further failures. One was the harness (the ANYfem example
  directory was not copied). The other, M25's
  `test_initialization_makes_no_keyed_reads_of_other_modules_globals`, failed
  because Python 3.12's import system reads the source module's `__name__` for
  every `from .boundary import ...` statement (also the pre-M25 ones), which the
  planted key observes; Python 3.13 does not. Import statements were outside the
  opt-in review's scope, so the test now ignores reads made while the caller
  executes `IMPORT_NAME`/`IMPORT_FROM` and still fails on the round-8 source
  (`m25n-prefix`, explicit `dict.get` reads). Second run: all as in the table.
- The two numerical identities M30 relied on were the chunked vector maps (same
  per-element numpy kernel; passes on Linux) and the block-wide K product (two
  different scipy loops; passed on Windows and Linux, but a compiler that fuses
  multiply-adds in one loop and not the other, as can happen on Apple Silicon,
  would break it). macOS could not be tested here, so the block-wide product was
  removed (about 0.5 ms per case).

Not covered: macOS (no Mac here; ANYfem CI runs Ubuntu and Windows only).

## Dependency floor (owner decision 2026-10-10)

"Keep to numpy above 2": `solver/pyproject.toml` and `fem/pyproject.toml` now
declare `numpy>=2.0` and `scipy>=1.13` (scipy releases before 1.13 do not support
numpy 2). The new floor itself (numpy 2.0 with scipy 1.13) has not been tested.

## Further levers (assessment 2026-10-10)

Barge, default mode, block 32, after M30: preparation about 82 s, about 23 ms per
case; 10,000 cases about 5.3 minutes serial.

Measured not to help: numba JIT enabled (`m30-barge-600-jit`: preparation 82.4 s,
about 22.7 ms per case, outputs byte-identical to the JIT-disabled runs); block
size beyond 32 (64: about 4%).

| Lever | Expected gain | Output identity | Needs |
|---|---|---|---|
| ANYfem: fluid side, centroid and normal per wet element cached once (fixed geometry) | about 1-2 ms/case | bitwise (same function, computed once) | ANYfem change |
| Structural copy instead of `copy.deepcopy` for per-case recovery metadata | about 1 ms/case | identical objects | small solver change |
| Envelope fold micro-work (mode skipping, fewer temporaries) | about 0.5-1 ms/case | bitwise | small solver change |
| Cheaper authority checks (same facts, memoised class-state facts with change detection) | about 1-2 ms/case | not numerical | authority review |
| ANYfem: wet-pressure expressions evaluated over all elements at once | about 2-3 ms/case | only where elementwise numpy equals the scalar evaluation bit for bit (not guaranteed for sin/cos/exp) | verification per expression kind |
| Vector maps as one product per element over the block's columns | about 2.5 ms/case | rounding changes; block-size invariance must be re-established | owner decision (M17 exact-tie lesson) |
| Case-parallel option A (ANYfem) | 10,000 cases 311 s -> about 200 s (measured 194 s) | identical (shown in M28/M30) | implementation |
| Prepare once, share with case workers (option B) | about 150 s (115 s with M27) | identical if transported by value | M27 trust requirements |
| M27 parallel preparation | preparation 82 -> about 45 s | identical | M27 requirements |
| Trusted capture opt-in (available) | preparation -13 to -19 s | identical | caller opts in |
| S7 digest by array bytes; sampled oracle verification | preparation -2 s; -8 s | provenance format; weaker verification | owner decisions |
| Free-threaded Python for in-process case parallelism | large, unmeasured | - | thread safety and authority-model work; long term |

The bitwise-identical serial items together are worth roughly 4-6 ms per case
(about 20%); parallelism remains the larger lever for long histories.

