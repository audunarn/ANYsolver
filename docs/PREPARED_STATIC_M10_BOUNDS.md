# M10: conservative response-output bounds

2026-10-09. Diagnostic implementation completed. **Conditional usefulness
demonstrated for sampled supported-shell von Mises outputs; production activation
remains INCONCLUSIVE.** Canonical direct execution is unchanged.

## Implemented proof kernel

For the represented operator, the diagnostic verifies a candidate pivoted LU
factorization using exact rational arithmetic. It streams factor-defect columns
through signed triangular solves, retaining their absolute row sums. It does not
form or store a global inverse.

Writing `P A = L U + E`, `S = (L U)^-1`, `m = |S E| 1` and `eta = max(m)`,
`eta < 1` establishes nonsingularity. For any represented candidate `x`, compute
`z = S P (b - A x)` exactly. The component error enclosure is

    |x - x_exact| <= |z| + m * max(|z|) / (1 - eta).

Root independently reviewed the permutation, contraction and component-bound
derivation. The verification approach follows the contraction principles in
[Rump's verification-methods survey](https://www.tuhh.de/ti3/rump/intlab/ActaNumerica2010.pdf);
the signed streaming implementation and the above specialization are task work.

Signed actions preserve cancellations discarded by the first positive comparison
bound. They verify both small original operators: supported 12 DOFs, eta upper
`4.353122899422135e-15`; free-free augmented 54 DOFs, eta upper
`9.154317321596367e-7`. A separate exact power-of-two congruence control also
verified the previously refusing comparison bound. Earlier refusals, partial
field tests, scaling controls and all source identities remain preserved.

## Output results and meaning

The enclosure includes error radii for **both reconstructed and observed direct
solutions**. It then propagates through local transforms and canonical staged
linear recovery with outward scalar arithmetic and conditional dot-product bounds.

- All 112 supported-shell linear values and two free-model beam shear values
  are contained in the final intervals.
- All 14 prepared canonical shell von Mises values are conditionally contained.
  Their per-case maximum interval-width/tolerance ratios are **0.545629** and
  **0.533989**, using the existing `1e-12 + 1e-12 * |reference|` screen.
- All seven paired von Mises station intervals strictly separate for minimum
  and maximum. Of 56 paired linear components, 35 strictly separate.
- Exact self-ties and touching-interval controls remain unresolved. No tolerance
  ties, winner-only replay heuristic or product zero clipping was introduced.
- Near-zero linear fields and free beam shear still have overly wide intervals;
  the beam pairs do not separate. This is quantity-specific evidence, not a
  whole-model stress or free-free envelope qualification.

The VM target is the prepared canonical `_derived_measure('von_mises', native)`
through `results._von_mises_surface`, whose rounded arithmetic differs from the
native S3 stored VM expression. The diagnostic follows the former computation
graph. Square-root brackets are checked by exact rational squaring; the native
square/power/sqrt rounding model remains conditional.

**These are retrospective interval decisions:** both direct solutions have
already been calculated. No unseen canonical contender or solve is skipped.
Contained outputs and a successful script exit do not establish reconstructed
output agreement, a governor certificate, or measured acceleration.

## Unresolved qualifications

Online activation must replace the measured-direct residual term with a sound
bound available without that solve. The existing backward-error limit alone is
not an output-error certificate: checker rounding, conditioning and the unknown
solution magnitude matter. An optimistic norm-gate calculation omitting checker
rounding is recorded but explicitly unqualified; it fails contraction for the
tested augmented bound and is not used for decisions.

BLAS dot arithmetic assumes at most `2*n` rounded primitive operations, finite
intermediates and gradual underflow. Scalar power/sqrt assumptions also need
runtime qualification. Principal eigensolver, complete reactions, source and RHS
construction uncertainty, nonzero offsets and all-production-formulation coverage
remain outside this diagnostic. Exact-system verification does not fill those gaps.

## Verification, evidence and resource accounting

Root's final closed-form rational, pivot-permutation, cancellation/subnormal and
uniaxial/pure-shear VM oracles: **6 tests passed**. Author proof controls: **3
tests passed**. Root separately reproduced the final assembled diagnostic JSON
byte-for-byte, SHA256
`a7841a96b145b3564e73fc08d4f06e21684af937c784e01982ec7ae50b58d49e`.
That reproduction corroborates the diagnostic; it is not another mechanics oracle
or different-model-family review.

Exact commands, source/runtime identities, timing and logs are under the task
root's `evidence/checks/m10-*`. Full derivation, revisions and hashes:
`.prepared-static-evidence/m10-solver-handoff.md`. Final raw outputs:
`.prepared-static-evidence/m10-bounds-06.json` and `m10-root-final-bounds.json`.
Diagnostic sources are `tests/prepared_static_response_m10_bounds.py` and
`tests/prepared_static_response_m10_diagnostic.py`; independent oracles are
`tests/test_prepared_static_response_m10_independent.py`.

Worker checks: **21.21329490005155 / 120** process-wall seconds. Root checks:
**12.0940658999898 / 120**. No benchmarks ran; M8 remains at
**540.0326433999871 / 600** seconds. Correctness and old benchmark ledgers are
separate, including any legacy balance displayed by the runner.

No product changes, tolerance relaxation, commit, merge, push or 10,000-case
claim. Keep the diagnostic proof kernel; keep direct stress/envelope fallback.
The next concrete prerequisite is the unseen-direct solve bound plus qualification
of the requested output arithmetic. Another performance campaign is premature.
