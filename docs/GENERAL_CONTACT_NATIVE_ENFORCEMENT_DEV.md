# Native multiple-S3 tighter enforcement — development profile

**4 October 2026. Implemented/tested; not independently accepted or released.**
Source parent `3084a6081791ee5740e0a938433b867689d3957a`; the containing local
commit binds this slice. Raw source/import identities remain with the evidence.

## Explicit use and inherited scope

```python
# From examples/general_contact_native_multiple_s3_static.py
owner = tight_gap_analysis(beams=2)
run = owner.solve()
assert run.status == "completed", run.failure
```

Public `create_native_contact_analysis(..., activation_settings=...)` selects
`NATIVE_B3_GE_MULTIPLE_S3_ACTIVATION_NEWTON_STATIC_DEV_V1` only when supplied exact
`NativeContactActivationSettings(activation_gap_m, maximum_geometry_queries)`.
Absent settings preserve the existing algorithm/profile/schema and example defaults.
The dedicated native owner retains physical internal unknowns, full coupled cross
blocks and all [multiple-S3 scope limits](GENERAL_CONTACT_NATIVE_MULTIPLE_S3_DEV.md).
It does not admit generic FEModel native insertion, rims, target unions, caps,
beam-beam, friction, dynamics, nonlinear shell materials or new section families.

The example explicitly uses line regularization1.2e6N/m2 and every-pair physical
gap limit5e-5m, corresponding to1e-3 of its50mm radius/thickness. Four equal force
targets and original loads/supports/geometry remain. Activation control is1e-7m
for one beam,1e-6m for two;64 geometry queries per Newton controller,128 swept
intervals per pair,24 Newton iterations and8 backtracks remain bounded. These
are fixture settings, not automatic stiffness or universal application defaults.

## Mechanics and conservative path

The line penalty and physical increment transaction are unchanged. Previous10k/
40kN/m2 responses suggested approximately inverse-square-root penetration. The
explicit1.2e6 candidate derives from40k*(0.2689mm/0.05mm)^2, not a hidden law.
Fixed-target failure probes matched the tangent/Newton system but showed a merit
jump when another pair activated. The new controller restricts Newton fractions;
it creates no extra physical load increments or commits.

For previously strictly open pairs, endpoint bracketing and a conservative whole-
prefix certificate limit penetration by the smaller activation budget. Open
endpoints still require certification. All pairs subsequently pass full work/
integration, physical gap/path, equilibrium and transaction checks. Nonmonotone
bracketing is not a first-event guarantee. Unresolved domains, bounds, queries or
intervals fail explicitly. No algorithm switch occurs in a failed increment.

Geometry-only queries use the same retained quadratic curves, physical S3 vertices,
ordered moving normal, scalar extrema and Bernstein rim guards as force work.
Derivative/integration construction is omitted only where unused. The opt-in gap
bound uses g=n.(r-C)-R with target centroid C. A lower bound on triangle area and
cross-product rate bound normal motion. Projected translation/angular rates,
normal excursion and centroid-relative radius bound gap speed. All rim bounds
remain; original-profile helper defaults are unchanged.

`activation_queries` is cumulative on that owner, including failed controllers;
it counts controller endpoint/prefix queries, excludes regular physical sweeps,
and is neither physical history nor checkpoint state. Every controller query
shares its explicit cap. Reduced certificate budgets reserve queries for shorter
prefixes; they cannot admit unresolved paths.

Restart has a separate activation schema/profile and binds exact settings plus
revision `counted_open_endpoint_prefix_projected_normal_v2`. Draft v1 controller
capsules, old profiles and incompatible settings fail identity checks. Only the
original accepted targets and committed physical histories are saved. Rejected
trials, query exhaustion, cancellation and later-pair failure preserve that state.

## Evidence and retained nonpasses

Raw evidence: `C:/ANYworkspaceWork/contact_native_enforcement_20261004`.
[Compact summary](d1_review_support/contact_native_enforcement_20261004/summary.json),
[supporting review](d1_review_support/contact_native_enforcement_20261004/support_review.md),
[decision record](d1_review_support/contact_native_enforcement_20261004/decision.md)
retain raw paths/hashes and failures. Installed28pass139.665s/354353152B plus the
specific independent-path follow-up1pass3.105s/185548800B;207 imported modules and
511 Python files match. Effective JIT disabled, Numba/BLAS1;180s/953MiB process cap
and native120s owner deadline. Private wheel
`bbdfb2346fe932002662308f1f198df6643a4111985fc035b5b8a39eb897bc23`.

Independent final gaps49.2952/49.2958 micrometres for one/two beams are below50.
One coupled tangent direction at h=1e-4,1e-5,1e-6 gives maximum errors2.6502e-6/
2.4368e-6 against1e-5. Equilibrium metrics are below5.53e-13 against1e-8.
Checks cover independent retained-curve energy/minimum gap, actual deformation of
both skins, force/moment/support reactions, full-prefix rejection and independent
dense path crosscheck, split restart, cancellation, later-child exception, changed
identity, explicit query failure, legacy owners and ordinary static import behavior.
Doubling explicit penalty1.2e6 to2.4e6 reduces one-beam gap49.2952 to34.8663um;
halving target spacing preserves final response within recorded tolerance.
Two-setting sensitivity is not spatial/enforcement convergence.

Preserve source01/02 fixed-target stronger-penalty failures;source03 activation
candidate120s/24-iteration failure;source05 preflight runner-option error (no solver
launch);source06/07 hidden-path64-query failures;source08 two-beam1e-7 activation
budget Newton-limit failure;source10 wrong test attribute failure. The corrected
hidden-path test demands full-path resource rejection and certification of a
separately shorter prefix. One-beam1e-7 and two-beam1e-6 successes have distinct
explicit settings; old nonpasses are not regraded.

Supporting source scrutiny closed controller, counter and identity findings. The
lead corrected the dense crosscheck to the independent scalar oracle and reran
that affected check. This is not independent engineering acceptance. Native mesh,
section/material, physical boundaries and broader load-path qualification remain
open. No universal speedup, release or programme completion follows from this slice.
