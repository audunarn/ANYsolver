# S3 friction first-touch activation — development result

Source parent6fd19c5d plus this checkpoint; plan2026-10-02.9. C5 acceptance and
application admission remain open. Accepted D1/D2 normal profiles are unchanged.

## Discriminator and correction

Independent prescribed slider: initial gap.015m, ux=.1*tau, uz=−.02*tau,
kn=1000Pa/m, mu=.3, kt=1000Pa/m, reference area.08m². Touch occurs at tau=.75;
p=20*(tau−.75), elastic-gap slope.006m and plastic-slip slope.094m/progress.
Exact endpoint reaction is.12N; continuous Coulomb dissipation is.00141J.
The endpoint gap is−.005m in this finite-penalty development fixture; it is not
the programme's1e−3-thickness engineering gap qualification setting.
Baseline endpoint activation failed: reaction−4.62593e−17N and dissipation0J.
It initializes the anchor at the compressed endpoint, losing post-touch sliding.
That run/input is retained; historical endpoint selection remains available.

Explicit `linear_constant_normal_touch_dev` instead locates first touch on the
affine full-FE-coordinate increment path, initializes a material anchor there,
convects it through the target interpolation and performs the endpoint return.
The tangent recomputes event fraction/stage coordinates on one selected event
facet while physical work holds the final returned anchor fixed. This path is
an integration contract, not the exact intervening equilibrium trajectory.

Whole-path quadratic extrema enforce positive facet orientation, convex target
boundary and full source coverage; transverse-normal coefficient bounds use the
minimum represented facet area. Moving normals and mid-path collapse reject.
Stage/return probes are disposable, separately bounded in event fraction and
material coordinates, and cannot commit extrapolated coordinates or cross rims.
Event settings/path/recontact rule bind restart; incompatible continuation rejects.

## Actual checks and step accuracy

- One-step reaction.12N recovered; first-touch fraction.75 at all material points.
- Independent stick reaction.004N, cross derivative−.6N/m and complete
  directional error≤1e−5 at h1e−4/2e−5 include event/anchor sensitivity.
- Independent storage.08*.5*1000*(.00005)²J matches; stick dissipation0.
- Common translation, same-pose restore/force, quadratic mid-path-collapse and
  moving-normal rejection preserve state. Event-seam probes retain the same
  stage facet, return no histories, and enforce their fraction bound.
- Coupled target motion, press/stick/slip/reversal/open/recontact and exact split
  history restart pass for both activation selections at quadrature levels0/3.
- Endpoint/chord work is still first-order: D_N=D_exact*(1+4/N) for N divisible
  by4. Measured relative errors:100%,50%,25%,12.5%,1.5625% at N4,8,16,32,256.
  This demonstrates sensitivity/convergence for this fixture, not exact work on
  coarse steps or general C5 temporal qualification.

Final installed32checks pass, including all affected activation/integration/
anchor/tangent/state checks, legacy static/history and retained-spin work, plus
both example modes. One added seam test initially misplaced the collapse fixture
and failed with NameError; failed input/log retained. Moving that fixture back to
its owning test fixed the test defect without changing equations or tolerances.

## Artifact, environment and resources

Artifact C:/ANYworkspaceWork/contact-friction-activation-package-20261002.
Wheel SHA2560ada7f67b52ff143c0cb55ad9e7a5b224d2fc7f66f2a52252444820c3535b7c5.
457source/wheel/site modules match;239onsite imports. Actual JIToff,
BLAS/Numba1 verified before/after execution. Build14.6105607s/125489152B
sampled process-tree peak; installed selection108.1391011s/187318272B, within
180s/999292928B. No whole-route speedup claim follows.

[Independent review/disposition](independent_review.md). Old accepted normal,
sphere and no-contact evidence reused by impact analysis: changes are inside the
opt-in material-anchor owner and example, not historical structural/default paths.
No no-contact5% regression or release claim. Raw source bindings, input failures,
fixture/XML/execution records and reviews are in raw.zip/raw_index.json.

## Remaining principal work

Actual partial-overlap history integration/repartitioning; moving-normal/finite-
rotation activation, physical rims/creases, beam/native friction, nonlinear
materials, arc length and impact friction. Do not replace those requirements
with this constant-normal, full-coverage candidate. C0–C9 remains active.
