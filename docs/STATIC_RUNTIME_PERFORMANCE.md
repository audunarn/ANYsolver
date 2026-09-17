# Static runtime performance programme

## Scope

This report covers the complete ANYstructure-to-ANYsolver linear-static path.
It does not change element equations, qualification tolerances, recovered
quantities, default formulations, or legacy B3 routing.  Measurements use one
numerical-library thread and exclude application import time.

The representative flat-panel fixture contains 405 nodes, 364 qualified Q4
shells and 274 B2 beams.  The medium fixture contains 1,218 nodes, 1,148 Q4
shells and 515 beams.  The pre-change measurements were captured from clean
ANYsolver commit `d04199ac851c0d0f61430c2bc40136582aa8d659` before applying this
programme.

## Results

| Route | Before | After | Speedup |
| --- | ---: | ---: | ---: |
| Representative complete static run, median of 7 | 6.7025 s | 1.6860 s | 3.98x |
| Representative retained load-only run, median of 7 | 6.7025 s | 0.3376 s | 19.85x |
| Medium complete static run, screening median of 3 | 19.84 s | 4.7830 s | 4.15x |

Representative complete-run after-times were 1.6936, 1.7158, 1.6650,
1.6809, 1.7335, 1.6808 and 1.6860 seconds (MAD 0.0075 s, maximum
1.7335 s).  Retained load-only times were 0.3347, 0.3376, 0.3332, 0.3375,
0.3400, 0.3381 and 0.3385 seconds (MAD 0.0009 s, maximum 0.3400 s).
The before complete-run times were 6.7025, 6.7277, 6.6727, 6.7663, 6.6847,
6.7681 and 6.6968 seconds (MAD 0.0252 s).

The engineering objectives of 3x complete-run and 5x repeated-load speedup
were therefore met on the representative fixture.  These are internal matched
measurements, not a comparison with DNV Sestra.

## Promoted changes

- Qualified-shell observation guards now validate fully at owned-operation
  capture and finalization, with identity/generation checks in trusted loops.
- One accepted-state recovery feeds prestress, physical resultants, display
  stresses, statistics and visualization.
- `RuntimeAnalysisContext` retains a prepared model and `AnalysisSession` for
  eligible linear-static load families, with structural-key and live-revision
  invalidation.
- `AnalysisSession` retains exact proportional dead-load vectors as well as
  stiffness, constraint reductions and direct factors.  Prescribed affine
  corrections remain owned by the existing constraint plan.
- Linear solution returns its already assembled load vector for resultant
  calculation, eliminating a second load traversal.
- Static-only cylinder runs no longer enter the buckling fallback or install
  buckling-only gauge constraints.
- Public diagnostics report phase timings, backend, effective thread policy,
  recovery count and cache hits.

## Acceleration screen

The retained representative profile records direct factorization/solve at
about 0.0023 seconds, while recovery is about 0.19 seconds and result packing
and visualization about 0.09 seconds.  PARDISO ordering, Cholesky, PETSc and
cuDSS cannot currently deliver the required 10% complete-runtime improvement
on this workload, so no new solver dependency or GPU path is promoted.

Existing compiled Numba element/assembly routes remain active.  A new
C++/pybind11 toolchain is not promoted without a whole-run win.  The next
candidate is a coarse compiled recovery/result-packing call over contiguous
accepted-state arrays, because that is now the dominant measurable work.
PARDISO, exact substructuring, elasticity-aware AMG and cuDSS remain appropriate
screens for larger models where factorization or fill becomes material.

## Correctness and lifecycle

The final focused ANYsolver performance, runtime, guard, assembly, recovery,
follower-load and session suite passed 151 tests.  The focused ANYstructure
adapter/format/authority suite passed 26 tests.  Regressions cover static-only
cylinder routing, one shared recovery, load-only reuse and structural
invalidation.  The ANYstructure adapter owns one context per FEM window and
releases it when the window closes.  Failed solves, stale live models and
structural-key changes invalidate retained state.

Fresh wheels were installed together outside both repositories and exercised
through the real ANYstructure adapter.  The installed run produced the 405
node/364 shell/274 beam fixture, then reused one model and direct factor for a
second pressure load.  The tested wheel hashes were:

- ANYsolver 0.4.6: `9E524C7E5D82132C5200482D443DBCE6B45104F67F0FC5FB3466E37F0F6C2696`
- ANYstructure 6.4.1: `BAF041B5C17CC610F7B078EB0FF0AEA11D37DD7EBA9A9A17C8FDFDE5555E0C70`

No qualification evidence, shell/beam coefficients, public defaults or
historical mechanics were changed.
