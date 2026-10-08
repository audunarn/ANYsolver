# Coupled deformable-target refinement using disposable multilevel guesses

**29 September 2026. Development evidence, not D1 qualification.** Source
commit `2641aa352f546fcad769a87ca7174af9729d8f4d`. The solver source,
mechanics, settings, two-step loading path and acceptance gates are unchanged.
The 8×8-S3 accepted poses and ten source nodal pressure-force values are used
only to initialize the Newton iterates of a separate 16×16-S3 solve. Both fine
increments commit through the normal static driver. No coarse material or
checkpoint state is transferred. The source has four Q4 faces in both cases.

## Decision and guards

The prior ordinary 16×16 route exhausted its 180 s cap after nine contact
linearizations without completing step two. A coarse guess was worth one
bounded attempt only if it preserved fine constraints, controls, physical gap
and force support; its prior-accepted-to-seed sweep had to be certified. The
independently shifted target grids are nonnested, so the measured work-transfer
difference was treated as initial-guess quality, not exact work parity.

The [preflight](d1_multilevel_seed_preflight_20260929.json) took 74.04 s and
399.14 MB peak process-tree memory under the 180 s / 1 GB cap. Both poses
reconstructed the fine constraints and controls to the reported numerical
precision. All seeded forces were finite, nonnegative and supported. The
coarse-to-fine contact work difference was 2.10e-4 relative on each pose.
Independent gap lower bounds were -5.88e-6 and -3.97e-5 m against the
5e-5 m budget. The proxy sweeps passed. The seed free-residual norms were
6.44e-4 and 6.48e-3 N, compared with 4.78e-2 and 9.56e-2 N at **zero pose**
under each load. The second zero-pose value is not the ordinary step-two
starting residual. The actual solve recertified each sweep from its own
previous fine accepted pose; both passed.

## Complete fine path

The [bounded fine result](d1_multilevel_seed_route_20260929.json) completed
both increments in 146.82 s wall time (145.23 s inside the route) with
533.71 MB peak process-tree memory. Each increment used two semismooth Newton
iterations, three candidate evaluations and zero backtracks. The complete
[progress trace](d1_multilevel_seed_route_progress_20260929.jsonl),
[seed decisions](d1_multilevel_seed_route_seed_trace_20260929.jsonl),
[resource envelope](d1_multilevel_seed_route_resource_20260929.json) and
[preflight resource envelope](d1_multilevel_seed_preflight_resource_20260929.json)
are retained. The ordinary 16×16 route did not finish, so these records do not
support a complete-route speed ratio or the twofold speed target.
The executed seed wrapper has SHA-256
`18c18ffd5be4d02b1531e44f14aed51d35c986a383f2d86b01021202c67cebeb`.

| Accepted step | Source force, 8×8 → 16×16 (N) | Relative shift | Source pressure-vector L2 shift | Fine independent gap lower bound (m) | Fine NCP / equilibrium residual |
|---|---:|---:|---:|---:|---:|
| 1 | 1.8318185e-5 → 1.8286761e-5 | -0.17155% | 1.39296% | -6.22374e-6 | 3.91e-14 / 8.47e-16 |
| 2 | 4.3102895e-4 → 4.3076922e-4 | -0.06026% | 2.24471% | -4.51408e-5 | 3.56e-11 / 6.02e-13 |

The force-vector balance between the two bodies is 1.69e-20 N and
1.63e-19 N. Fine source reference supports are positive and pressure values
nonnegative. Both source and target retain their independent constitutive
coordinates. These are path and discretization observations, not a
continuum-reference or pressure-stability verdict.

## Disposition

This closes the narrow resource blocker to obtaining **one** coupled 16×16
deformable-target result at the unchanged cap. It does not close D1. In
particular, a single 8×8→16×16 comparison cannot establish mesh-uniform Q1
pressure-space stability, a saturated structural reference, full lifecycle
state safety, or installed-package acceptance. Retain the previous capped
failures and do not infer that pressure has converged from the small integrated
force shift. The next acceptance decision should use the existing gap map and
independent review; no automatic further refinement is authorized by this
result.

An independent read-only reviewer checked the wrapper, driver, raw path and
resource records and confirmed this bounded coupled-solve interpretation.
The reviewer found no state flaw invalidating this elastic fixture. The
executed wrapper relied on the matching preflight for supported seed forces
and independent endpoint gap instead of recomputing those at injection. A
subsequent source edit added both direct guards for future use; that edited
wrapper has not been timed or used for a second fine solve. The exact executed
version remains available in commit `647e1a52`. The final gap
bound has only 4.86e-6 m margin to the declared tolerance. The saved
4×4→8×8→16×16 final source-force sequence is
4.2820329e-4→4.3102895e-4→4.3076922e-4 N; it supplies no convergence
rate or error bound.

Reproduction scripts: [preflight](d1_multilevel_seed_preflight.py) and
[seeded route](d1_multilevel_seed_route.py). The preflight is a local
discriminator, not an accepted fine step. The seeded route checks the actual
fine accepted-to-seed sweep before each increment and falls back to the
ordinary iterate if a seed is inadmissible.
