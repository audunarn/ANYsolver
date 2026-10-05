# Native continuous-gap and enforcement discriminator

2 October 2026, base67bce781 plus hashes in continuous_gap_results.json.
Raw runtime/selection/resource evidence, saved configurations and canonical
checkpoints are in continuous_gap_raw.zip. Development only, no C5 acceptance.

## Implementation and review

An independent-of-quadrature extremum calculation admits exactly affine reference
coordinates and identical reference triads. Within each cell, any plane distance
is affine in xi plus a*cos(alpha)+b*sin(alpha). Both cell endpoint traces, patch
angular endpoints and every stationary angle are evaluated. Roundoff allowance is
reported and subtracted for the lower bound. Target ownership uses the same
extrema on each inward edge plane. This is endpoint geometry, not a swept proof.

Optional gap_check=straight_patch is definition-bound and supplies the continuous
lower bound to ordinary owner admission. Historical sampled mode stays unchanged.
Independent OpenAI source review found no extrema-formula defect, but found that
initial penetration between open quadrature samples bypassed the initial check.
Initialization now rejects negative continuous lower bounds, including unresolved
roundoff. The regression demonstrates this case and its rejection. Exact initial
touch is not newly admitted by this conservative profile.

## Results

Four checks pass: cylinder gap between samples, tilted/sheared patch against an
independent station-based numerical minimizer, curved-reference/target-rim rejection,
and an8x8 coupled saved-pose gap screen. Three later checks pass: initialization,
restart selection binding and the stronger-penalty coupled route. Both coupled
cases retain the fixture's1mm gap tolerance; it is not a qualification default.

| Normal regularization Pa/m | Sample penetration mm | Continuous penetration mm |
|---|---:|---:|
| 1e4 | .569885 | .772413 |
| 1e5 | .086618 | .286687 |

Both exceed the programme's radius-based starting qualification budget49um.
Stronger enforcement exposes an integration issue. An independent frozen-pose
reference integrates the piecewise linear-in-xi pressure exactly, then uses a
controlled angular integral split at contact roots. It does not call production
contact force assembly. Quadrature and continuous forces use the same saved pose,
normal, reference measure and stiffness, avoiding a structural-model mismatch.

| Regularization | 8x8 normal force N | Continuous integral N | Relative discrepancy |
|---|---:|---:|---:|
| 1e4 | .003020351301 | .003012680845 | .255% |
| 1e5 | .003092677610 | .002584111466 | 19.6805% |

Estimated scalar integration errors are below3.4e-17N. The reference screen passes
its numerical integration check; its result demonstrates a production quadrature
discrepancy, not a mechanics acceptance pass. No higher-order or penalty sweep is
authorized merely by this observation.

## Selected next action

Implement normal integration that resolves contact boundaries. For this exact
straight profile, integrate the positive-part normal penalty potential analytically
in xi and adaptively in angle, with complete retained/native and target derivatives.
Use explicit algorithm selection and existing contributor/transaction machinery.
Avoid double counting the point normal law; friction history/integration remains
a separately controlled obligation. Reuse the saved poses for initial verification.
