# Classical beam plane impact — development evidence

Parentb8960736; exact source/fixtures/environment/wheels bound in raw.zip.
Implemented and installed-tested development; kernel/selected driver contracts
received independent source review.
not C6 qualification, release, whole-route acceleration or continuum collision claim.

## Integrated outcome

Explicit B2/B3 round-tube von Karman impact now uses the existing Newmark driver,
line-contact work, material transaction and restart. Actual reduced structural
mass/rotary inertia is retained and must be positive definite. Tensor Bernstein
bounds cover every centreline cell and the complete Hermite time path; exact
Fraction arithmetic and outward conversion preserve a lower bound, with finite
refinement/resource failure. No support, force or inertia is substituted or dropped.

Uniform B2/B3 cases match independent scalar Newmark equations/normal impulse,
activate and open, and continue through active/history restart. A straight-reference
B3 develops curvature, partial contact and rotary motion with independently derived
total normal momentum and physical quadratic-gap extrema. Callback failure and
cancellation preserve the last committed state. Zero physical mass is rejected.

The shared load-knot step now integrates to an arithmetically adjacent knot instead
of leaving a phantom sub-minimum step. It never snaps beyond requested t_end.
Actual complete steps are solved; no timestamp-only advancement is introduced.
The shell/event/history compatibility selection passes on the final artifact.

## Retained executions

| Evidence | Actual result / disposition |
|---|---|
| Geometry worker source stages | 38 then40 passed; lead inspected owned diff and independently reran final checks |
| Lead sourcev1 | 2 passed, admission and historical event restart |
| Sourcev2 | 5 passed/1 failed; unresolved arithmetic load knot identified |
| Sourcev3 | 2 passed; beam history work/restart and historical S3 history |
| Sourcev4 | 2 passed/1 failed; curved-reference B3 fixture correctly rejected by structural guard |
| Sourcev5 | 1 passed; deformed straight-reference B3 curvature/partial impact |
| Sourcev6 | 82 passed/1 failed; zero-mass fixture omitted required initial velocity |
| Sourcev7 | 1 passed; corrected zero-mass fixture reaches intended guard |
| Installed stage1 | 106 passed; does not contain subsequent endpoint-edge correction |
| Sourcev8 | 1 failed; one-ULP end-time overstep caught |
| Sourcev9 | 2 passed; endpoint-edge correction and history work/restart |
| Final isolated installed stage2 | 107 passed/0skips; complete selected new/compatibility modules and two CLI examples |

Selections overlap; do not add them. Final installed complete elapsed16.2959196s,
pytest14.41s, sampled peak186486784B;180s/999292928B caps, BLAS/Numba1 and JIT off.
All451 source/wheel/site module bytes match and201 recorded solver imports resolve
to the isolated site. Final wheel SHA256:
`a48a424eed957ca2953f09ff91cc596622f98556262a2cb31fe598dcc096b72e`.
The first-stage wheel and all failures remain retained, not retrospectively passed.

## Review and limits

[Completed Mistral source review/adjudication](review.md) inspected geometry and
driver admission/mass/lower-bound use; no kernel counterexample was found. Its
claimed numerical discrepancy values have no execution record and are excluded
from measured evidence. Independent manufactured tests provide numerical evidence.

The supported reference geometry, scalar elastic law, small-rotation von Karman
profile, plane/radius/line conventions and explicit resource limits remain bounded.
The toy .002m gap budget is not engineering qualification; inherited gap, response,
energy, integration and refinement criteria remain unchanged. General finite-rotation,
cap/pair contact, moving/free bodies, nonlinear materials, friction and common-stage
native coupling remain required. No full C6 or programme completion follows.
