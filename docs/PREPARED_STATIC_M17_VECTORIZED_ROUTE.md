# M17 — whole-model vectorized certified route (opt-in)

2026-10-09. Owner: Claude (Anthropic). Started on the user's instruction after
the M16 barge NO_GO; benchmark allowances were delegated to the owner.
**Outcome: formal holdout GO under the frozen M16 criteria; on the barge the
vectorized route evaluates cases 3.4-3.7x faster than the canonical response
route on matched runs, about 2.5x per case including harness output, for +21 s
preparation and no extra memory. The 2x complete-workload criterion is not yet
measured on a long history; see "What is and is not established".** Not merged,
committed or published.

## Why M17

A profiled canonical barge history (four cases) attributed case time to envelope
transaction bookkeeping (about 30%), load evaluation with per-element routing
authority checks (22%), element recovery (16%), reactions (12%) and record deep
copies (9%). The M16 library only replaced element arithmetic, which explains
its 1.03x.

## Implementation

Opt-in `prepare_static_response_evaluator(..., stress_execution="certified_vectorized")`.
Defaults and the `canonical` and `certified_library` modes are unchanged.

- `prepared_static_vectorized.py` (new): each recovered element's affine map H
  is probed once from its owned canonical recipe (unit probes) and verified with
  a random and a rigid-offset probe, constant stability and vectorized
  derived-measure reproduction (1e-9, normalised by |H||v| + |r0|). Elements are
  grouped by schema. Per block, each case column is evaluated by one identically
  shaped batched product, so results do not depend on block size or neighbours.
  Von Mises, equivalent, Hill and principal measures are vectorized. A new array
  envelope accumulator keeps the earliest-input exact tie rule, signed absolute
  maxima, associated fields, copy-on-write transactions and the same result
  order and shapes as the per-entity accumulator.
- `prepared_static.py`: one overridable `_new_envelope` factory; no other change.
- `prepared_static_loads.py`: the native routing authority check runs once
  before and once after the pressure loop instead of around every element.
  Scatter order is unchanged and a failed check still discards the vector, so
  loads are bitwise identical (pressure-verification suite passes) and fail
  closed. This benefits every route.
- Reactions keep the canonical Ku-F diagnostics (criterion C4).

## Defects found and fixed during M17

1. A batched product over several case columns rounded differently from one
   column, so identical cases in different blocks did not tie exactly. Fixed
   by evaluating each column with an identically shaped product; a regression
   test covers ties across blocks.
2. The first barge run refused one beam (element 4807) axial field. A diagnostic
   over all 4,245 elements showed every field affine to 4.3e-16 of its internal
   magnitude; the refusal was rigid-offset cancellation judged against the
   observed value. Verification now uses the internal-magnitude scale.

## Formal holdout assessment (frozen M16 criteria C1-C6)

`.prepared-static-evidence/m17-assessment-01.json`, run `m17-claude-03-assessment`.

| Holdout | Cases | Worst linear / limit | Worst derived / limit | Envelope entries | Identity differences (all near ties) |
|---|---:|---:|---:|---:|---:|
| A1 supported S3 | 12 | 0.0050 | 0.000085 | 630 | 0 |
| A2 rotated S3 | 6 | 0.0021 | 0.000091 | none requested | none |
| A3 free-free Q4/beam | 8 | 0.00097 | 0.000042 | 1,368 | 16 |
| A4 beam with offset | 4 | 0.00011 | 0.000034 | 24 | 0 |

The fix to verification (defect 2) came after this assessment; it changes
admission only, not emitted values. The assessed module is preserved as
`../evidence/m17-prepared_static_vectorized-assessed.py`.

## Barge screen (matched, same source and settings)

| Measure | Vectorized | Canonical |
|---|---:|---:|
| Preparation end | 127.1 s | 105.9 s |
| Warm case evaluation, four cases | 2.16 s | 7.92 s |
| Warm recovery phase | 0.91 s | 5.82 s |
| Warm history incl. harness serialization | 7.91 s | 14.03 s |
| Peak RSS, warm | 1,255 MB | 1,339 MB |

Cold and holdout histories give 3.53x and 3.41x on case evaluation. All 12
cases reconstructed with zero fallbacks. Output comparison against the canonical
route: displacement 5.1e-13 relative to the largest displacement, selected
stresses 1.6e-11 relative to element maximum, envelope values 2.1e-8 relative to
entity maximum (the same figure as M16, so it comes from the reconstructed state
versus the direct solve), and zero governing-identity differences in 276,246
envelope values per history.

A 40-case vectorized history (ten blocks) kept case evaluation flat at 2.20 s
per four cases (first two blocks 2.32 s, last two 2.22 s). It stopped while
writing the tenth block because the harness's 256 MiB output cap was reached;
evaluation of all ten blocks had completed and is recorded.

## What is and is not established

- Established: recurring case evaluation about 0.55 s versus about 1.98 s per
  barge case; about 1.0 versus 2.47 s including the harness's per-case
  selected-history serialization (about 0.45 s, identical for both routes).
- Projection only, not measured: for 10,000 cases about 2.8 h versus 6.9 h
  (about 2.4x) including preparation, assuming per-case costs stay flat as
  they did over ten blocks.
- Not established: a measured long-history complete-workload 2x, 10,000-case
  memory boundedness, independent review, and barge-scale evaluation of the
  frozen criteria (which needs per-element probing at the barge).

## Resources

Benchmarks: m17 748.336 / 900 s (profile 149.675, refused run 119.096,
diagnostic 178.860, vectorized 151.996, canonical 148.709); m17b 164.602 / 300 s
(40-case history, output-cap stop). Correctness checks 80.551 / 150 s. Regression:
80 of 83 base tests pass; the three failures are the pre-existing authority-test
failures recorded in M16. No Git operation.

Final source SHA256: prepared_static.py 539ff357..., prepared_static_loads.py
cbd03a2b..., prepared_static_response.py 5f12065a..., prepared_static_vectorized.py
95d33d01... (full hashes in ../evidence/M17_FINAL_SOURCE_SHA256.txt).

## M18 long-history screen (300 cases, primary and distinct holdout)

Complete workload, built model to consumed output: **2.21x primary
(281.8 s versus 622.9 s) and 2.05x holdout (299.2 s versus 612.5 s)**. Both meet
the adopted 2x criterion; the holdout margin is thin. Peak memory is unchanged.
Recovery phase falls from about 400 s to about 58 s per history; original-time
load evaluation (about 88 s) is now the largest remaining recurring cost.
All 600 cases reconstructed without fallback. Governing-identity differences
versus the canonical route are all between samples at the same phase of the
period, where the route's values tie exactly and the earliest input wins. Full
numbers in the living note and evidence/m18-analysis.json.
