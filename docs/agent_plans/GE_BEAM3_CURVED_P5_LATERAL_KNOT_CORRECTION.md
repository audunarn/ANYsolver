# P5 lateral propagation — coefficient-knot correction

Failed first comparison preserved at
`d3f1d9fe133b776eb4f70fdf1cc750169ff22e19`, tree
`dfb176395623f0462135d2976e5b97be9951f1c7`. That command is not retried
unchanged; the empty attempt directories and failure record remain intact.

## Diagnosis before correction

Separately labeled diagnostics restored the same hash-bound continuum fields.
For stride one the independently propagated mode differed from the saved
transfer prediction by 4.78127667934467e-9; for stride two it differed by
6.658328924167148e-8, failing the fixed 1e-8 guard. Recomputing the old full
transfer from its restored fields reproduced it exactly, so JSON/state loss
was not the cause. No diagnostic was classified as a successful comparison.

The coefficients use piecewise cubic Hermite base interpolation. Its third
derivatives can jump at known knots. Independent adaptive full-matrix and
single-mode solves took different steps across those knots. A bounded probe
forced DOP853 steps to end at every coefficient knot, at the **same** rtol
1e-11 and atol 1e-13. On the failing stride-two case:

- 129 versus 257 half-grid matrix propagation relative error:
  7.406203839844283e-14.
- Knot-resolved matrix/vector propagation disagreement:
  1.50555516394589e-14.
- Knot-resolved vector versus the old saved prediction:
  3.696672587137466e-8.
- RHS counts: 3328, 6656 and 3328; each stayed inside the existing 10000 cap.

This identifies underresolved coefficient-knot propagation in the old
numerical reference, not an altered rod energy, element mechanics or lost
qualification. The old adaptive transfers remain preserved research records;
they cannot be substituted silently when the tighter vector guard fails.

## Successor computation and unchanged limits

Revalidate the already saved left/right root endpoint **base fields**, with
new full transfers on 129 and 257 nodes per half. Do not solve a base state or
repeat root bisection. Require matrix refinement error <=1e-11, opposite
endpoint determinant signs and the original <=1e-8 bracket width. Failure
stops; it never expands the interval or replaces old files.

The new records bind their legacy input byte/hash identity and new propagator/
revalidator source hashes. They are successor numerical evidence, not edits to
the original roots or their original adaptive iteration traces. The fine
transfer is used for mode reconstruction. The mode integrator now also stops
at the 129-node-per-half coefficient grid, while preserving all 33 requested
samples, continuous u,p, actual clamp residuals and the seventh-state energy
integral. The 1e-8 transfer, 1e-7 end, and 1e-9 work guards are unchanged.

All operations remain bounded by thirty cooperative seconds and 10000 RHS
calls each. No discrete path, production operator, nonlinear base/root solve,
resource-heavy campaign or consumed request is executed. The follow-up mode
comparison must use the newly bound successor transfer files in fresh output
directories; it cannot read the old transfers and waive their failed guard.

Regression tests require a boundary at every known coefficient knot, matrix/
vector linearity, unchanged integration tolerances and input/profile guards.
No qualification is granted by this numerical correction. B2/B3/Q4/S3
mechanics, defaults, accepted evidence and the broader goal are unchanged.
