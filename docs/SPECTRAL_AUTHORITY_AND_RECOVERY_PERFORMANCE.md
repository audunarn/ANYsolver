# Spectral authority and recovery performance gate

## Scope

This increment starts from ANYsolver `a411e6c563f6a5933a02bdf2e7d366e8bd53587f`
and the integrated ANYstructure adapter contained in master
`a377448dc235463b624226dd230f2fdb849acdd0`. It optimizes solve-scoped
spectral validation, prestress geometric assembly, and modal/buckling residual
evaluation. Qualified Q4/S3 and B3-GE mechanics, tolerances, selectors,
qualification evidence, and defaults are unchanged.

## Accepted spectral changes

- A private spectral lease performs complete lifecycle and authority checks at
  capture, caller-code boundaries, cancellation callbacks, and finalization.
  Callback-free inner loops use the existing monotonic mutation-generation
  check rather than repeating reflective formulation scans.
- Detached reference-prestress states are held in an immutable solve-local
  envelope. Geometric assembly consumes the envelope without repeatedly
  cloning station dictionaries. The envelope is never persisted across a
  changed accepted state.
- Modal and buckling residuals use sparse-matrix/dense-matrix products for the
  complete candidate mode block. Existing filtering, deterministic signs,
  normalization, repeated-root grouping, and original-pencil tolerances are
  retained.
- The already-open spectral lease is reused for geometric assembly. A narrow
  exact-zero tangent route handles captured built-in dead loads. Follower
  pressure, S3 pressure-surface diagnostics, activity controllers, custom
  loads, callbacks, and current-state analysis retain their guarded scalar
  routes.
- Diagnostics expose full/trusted guard counts, residual batch duration and
  column count, packed-prestress use, and dead-load fast-path use.

## Whole-route result

The selected fixture is the actual ANYstructure example girder-panel adapter:
405 nodes, 364 qualified Q4 shells, 274 B2 beams, 2,430 total DOFs, 2,347
reduced DOFs, and five buckling modes. Each process used one numerical-library
thread. Seven pairs were run serially with alternating baseline/candidate
order; every isolated process performed one warm-up before its measured
retained-context run.

| Complete static-plus-buckling route | Median | MAD | p95 | Median CPU |
|---|---:|---:|---:|---:|
| Baseline `a411e6c` | 3.713 s | 0.003 s | 3.722 s | 6.672 s |
| Candidate | 1.846 s | 0.003 s | 1.849 s | 5.141 s |

The candidate is **2.01x faster**, a **50.3% complete-route reduction**. The
maximum sampled RSS across the paired runs was 308.9 MB for the baseline and
307.2 MB for the candidate. The five buckling factors differed by at most
`3.98e-13` in absolute value across the seven matched pairs.

Candidate median solver phases were:

| Phase | Median |
|---|---:|
| Full spectral validation | 0.423 s |
| Geometric stiffness | 0.208 s |
| Dead-load tangent | 0.098 s |
| Residual checks and mode recovery | 0.001 s |
| Complete buckling solver | 1.221 s |

The retained baseline medians were 1.054 s, 0.334 s, 0.215 s, 0.982 s, and
3.080 s respectively. The increment therefore
clears the 10% whole-route promotion threshold with substantial margin.

## Recovery/result-packing prototype

A solve-local Numba prototype fused qualified-Q4 local-to-global membrane
rotation, nodal scatter, prestress aggregation, and public result packing. It
was deliberately not promoted: the three-run static screen changed the cold
median from 1.686 s to 1.716 s and the retained median from 0.338 s to 0.370 s.
Although one inner packing phase became faster, the complete routes did not
improve by 10%. All prototype production code was removed.

The next recovery optimization should begin only after a new complete-route
profile demonstrates that remaining Python object materialization can clear
the same threshold. A C++/pybind11 implementation is not justified by the
current result.

## Verification

- 108 focused modal, buckling, operation-lease, and mutation-epoch tests pass.
- 383 qualified lifecycle, mutation-epoch, operation-lease, prestress, mixed
  Q4/S3, follower-load, and current-state tests pass in the extended bounded
  inventory (including the focused tests).
- The packed geometric matrix is byte-for-byte numerically equal to the scalar
  state-map route in its focused regression.
- Dead and follower loads, cancellation, callbacks, ABA mutation, stale
  sessions, activity, and singular/dense fallbacks are covered by the focused
  and cross-formulation verification sets. Installed-wheel adapter isolation
  remains required before integration.

The reproducible driver is `scripts/benchmark_spectral_authority.py`; its
repeated-factor success check uses `1e-12` relative and absolute agreement,
while the solver's existing original-pencil residual checks remain the
scientific acceptance authority. Raw
timing records remain external evidence under
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\spectral-authority-20260917-acceptance`
and are not production package data.
