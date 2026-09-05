# P5 integrated nonlinear mixed density — 2026-09-06

Author research successor to `04d4748872ea94ea41c1a48a225ec334411f4fa8`.
This integrates the declared directed-hardening section into the beam's
stationary functional. It is not general plasticity, global history/restart
integration, independent review or qualification. Prior code and evidence
remain unchanged.

## Complete mixed variables and fixed origins

The functional has 36 variation coordinates: 18 external nodal coordinates,
six cell-rotation coordinates and twelve material endpoint moments. Nodal and
cell rotations use spatial multiplicative increments. Moments use additive
increments. The geometry, frames, endpoint logarithms and objective lift are
the existing P5 definitions, not legacy beam operators.

At each station, gamma comes from the lifted force strain and moment is the
linear material endpoint interpolation. The nonlinear partial Legendre density
is evaluated with that station's fixed origin history. Its physical section
resultants, curvature, consistent tangent and proposed history are returned.
Signed endpoint rotation/moment work completes the mixed beam potential.
Optional spatial dead line-force work includes the internally rotated curve
offset, not merely nodal interpolation.

The origin tuple is copied and validated at construction and is never advanced
during local Newton iterations or line searches. Every station has an explicit
cell/index/reference-coordinate record. Returned histories are trials only.
There is deliberately no automatic material commit after local convergence:
global convergence and atomic commit across all stations are later obligations.

Default diagnostic quadrature is 24 points per half (48 stations). Explicit
4/8-point development options are also bounded. This does not alter quadrature
or station layout in any earlier implementation or accepted evidence.

## Analytic variations and nonlinear condensation

For station inputs y=[gamma;m], the mixed section supplies density F, gradient
g and Hessian H. The beam composes these with its geometric jets using

```
dF/dq = J^T g
d2F/dq2 = J^T H J + sum_i g_i * d2y_i/dq2.
```

The second term is essential. A mutation test deliberately omits it, leaving
the residual unchanged but changing the Hessian significantly. No numerical
frame differentiation or substitution of a plastic tangent into elastic
F/H/J matrices is used.

The local solve retains all 18 rotation/moment unknowns. It accepts only a
stationary state with local residual infinity norm <=1e-11, a negative-definite
moment block and a positive-definite rotation Schur block. The full local
saddle system is then condensed to the 18 external coordinates using its
actual consistent Hessian. Singular or unstable blocks are errors, not
permission to regularize or use a pseudoinverse.

Bounds are 25 local updates, 12 line-search candidates per update and 64 full
mixed evaluations. Failed admissibility evaluations consume the evaluation
budget. Individual rotation increments are checked before wrapped endpoint
evaluation. No automatic external retry, load cutback or partial accepted
result is supplied. These local algorithmic bounds do not replace the formal
process/resource watchdogs required by a future qualification runner.

This implementation uses ordinary spatial rotation matrices and dense local
algebra. It does not claim the retained high-contrast precision properties of
other P5 experiments, and does not resolve the preserved extreme coupled case.

## Observations

For the existing height-0.4 reference and existing perturbed nodal configuration,
the full coupled elastic matrix and plastic direction
`[1,0.2,-0.1,0.3,-0.4,0.5]` are retained, with y0=0.02 and H=0.4.

| Points per half | Stations | Plastic-active stations | Updates | Evaluations | Local residual | Potential |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 16 | 15 | 4 | 5 | 2.04697e-15 | 0.057915933262625584 |
| 24 | 48 | 41 | 4 | 5 | 7.73904e-16 | 0.05791442682579506 |

These are different station sets. The potential difference and active-station
counts are preserved, not asserted byte-identical or quadrature-equivalent.
The nonlinear yield transitions require dedicated quadrature/history-layout
qualification. No quadrature tuning or station-state transfer is authorized
by this comparison.

An elastic high-yield control at eight points converged in three updates/four
evaluations, with no plastic-active stations. The zero-state 36x36 Hessian
agrees with the earlier analytical elastic mixed Hessian. At finite states,
elimination of moments agrees with the earlier elastic potential/gradient/
Hessian, and subsequent rotation condensation agrees with its nodal response.
Line-load work is included in these comparisons.

## Validation and scope

- New focused suite: **11 passed** (approximately 2.4 seconds).
- Existing fourteen P5 suites: **221 passed in 20.35 seconds**.
- Checks cover the default 48-station layout, elastic full/reduced limits,
  plastic full derivatives, the geometric second-variation mutation, local
  stationarity, physical moment recovery, frozen station origins, condensed
  tangent directional agreement, superposed finite rigid motion, reference
  covariance, reversal of station histories and endpoint moments, budgets,
  invalid inputs and multi-turn increment rejection.
- Condensed directional checks retain one common external increment chart;
  they do not incorrectly compare torque components in different moving charts.
- Smooth branch comparisons use 1e-7 directional checks and 1e-11 algebra,
  symmetry, covariance and moment-recovery checks. Tests verify that the
  compared perturbations do not cross a yield transition.
- Probe SHA-256:
  `CB4FE1724BCAC82B863609523767F67D1BF70245F9EEF599008A7B6D25F0FCE4`.
- Test SHA-256:
  `B5D5ABDB3BACEE65F06DE7DE21ECDE194AAB4762DA36AB35226D8BC0F5DE475F`.

These are same-author checks using the shared SO(3)/AD kernel and the new
research test law, not independent qualification. Only a research module,
its tests and this record are added. No production source, B2/B3/Q4/S3,
defaults, recovery/state laws, dependencies, package metadata, workflows or
accepted evidence changed. No formal authority, resource request, merge,
release or activation was created.

## Next work toward the full goal

Implement all-station transactional commit/discard and accepted-origin replay
around this local solve, then connect it to global nonlinear beam load paths.
Persisting station/model/quadrature identities and history for restart remains
unimplemented. The single-direction test law does not replace general nonlinear
section adapters or their independent verification.

The extreme coupled local failure, nonlinear quadrature, dynamic representation,
multi-element finite assembly, buckling/postbuckling, curved/slender qualification,
independent review, installed-wheel exposure and objective eccentric/curved
beam-shell joints remain open. The full goal remains active and unchanged.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
