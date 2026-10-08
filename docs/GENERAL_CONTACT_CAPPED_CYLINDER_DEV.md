# Classical round beams against a finite capped cylinder

3 October 2026. Implemented and tested development profile; **not independently
accepted, admitted for normal application use, or released**. This advances D2/D3
rigid geometry and classical static contact without completing either milestone.

## Use and supported scope

The public immutable `RigidCappedCylinder(name, point, normal, radius,
half_length, path_translation=None)` describes a closed cylinder with flat caps.
`point` is the centre, `normal` its fixed axial direction, and all lengths are
metres. The descriptor is additional; the existing `RigidContactBody` plane,
sphere and infinite-cylinder fields and serialization remain unchanged.

Use one explicit round B2/B3 surface, one line interaction with separately
dimensioned `line_stiffness` in N/m² and an explicit gap tolerance smaller than
the beam radius. The beam endpoint policy is `none`. The cylinder's flat caps
and circular rims are physical obstacle features, not beam endpoint springs.
Prescribed cylinder translation is optional; axis rotation and free-body inertia
are unsupported. Existing concentric elastic scalar/von-Karman classical-beam
restrictions apply. No shell/native/friction or finite-rotation structural
admission follows from this profile. Selected cells retain separate reference
line measures; a B3 reference cell must be straight with its middle node at the
midpoint. Its deformed curve retains the actual quadratic displacement interpolation.

```python
from anysolver import RigidCappedCylinder

tool = RigidCappedCylinder(
    'finite tool', point=(0., 0., 0.), normal=(1., 0., 0.),
    radius=.01, half_length=.1,
)
```

The runnable [example](../examples/general_contact_round_beam_capped_cylinder.py)
constructs a guided B3 beam and executes the ordinary force-controlled nonlinear
static route. Its gap budget is a development input, not a universal application
recommendation. Force/displacement control, prescribed translation, integrated
tool work and fresh active restart have focused checks. Changed half-length or
geometry revision makes a checkpoint incompatible.

## Discrete geometry and work

In the stored cylinder frame let `rho` be radial distance, `z` axial coordinate,
`u=rho-R`, and `w=abs(z)-h`. The solid's signed distance is `max(u,w)` inside
and `hypot(max(u,0),max(w,0))` outside. Tube gap is this distance minus the
declared beam radius. Side, cap and exterior-rim positional gradients/Hessians
are differentiated from this closest-point geometry and pulled through the
same B2/B3 interpolation as the line potential
`integral(0.5*k_line*min(g,0)**2 ds_reference)`.

The exterior-rim Hessian includes radial curvature and the derivative of the
combined radial/axial normal. Contact maps to all translational beam coordinates;
the inherited owner assembles sparse blocks and equal/opposite rigid reactions
and moments about global zero. Tool work uses that same physical reaction.
No secondary contact engine or new mandatory numerical dependency is used.

The admitted owner first certifies the **whole centreline outside the solid**.
Interior medial seams are rejected before force evaluation: differentiating
only local smooth branches there would miss a moving-interface tangent term.
The `gap_tolerance < beam_radius` condition is necessary but not itself this
whole-curve certificate. Initial unresolved penetration is rejected.

## Conservative geometry and bounded integration

Physical B2/B3 controls, including negative quadratic interpolation weights,
are transformed into exact rational Bernstein lanes. Restricted curves use the
degree-one/two blossom, and directed square roots yield outward gap bounds.
The returned minimum gap is a conservative whole-curve lower bound, labelled
as such; its enclosure accuracy is one tenth of the declared gap tolerance.

Affine static trial paths include both beam displacement and tool translation.
An exact relative-control speed upper bound and the signed distance's
1-Lipschitz property certify the entire path through bounded subdivision.
Unresolved enclosure returns failure/cutback, not sampled admission. This is
not a dynamic integration-stage or rotating-director certificate.

Floating polynomial roots propose integration partitions. Exact algebraic gap
signs isolate sign-changing activation fronts, and exact branch-checked Bernstein
positivity proves inactive panels, retaining radial/axial correlation. Extraneous
squared-equation roots do not prove activation or inactivity. Rationalized gap
evaluation avoids subtractive cancellation at grazing contact.

Active panels use the same adaptive 8/16-point Gauss controls for energy, residual
and tangent. An all-zero sampled panel requires an exact inactivity proof or
subdivision/failure. **Mixed panels still use an adaptive error estimate, not a
rigorous general integration-error certificate.** Two separated quadratic pockets,
a narrow rim pocket and a repeated grazing root have independent focused checks;
these do not prove completeness for all arbitrary curves. Broader integration,
mesh/enforcement refinement and the programme's independent acceptance gates
remain open. Finite budgets and tolerances were not increased to obtain passes.

## Evidence and remaining acceptance

[Summary](d1_review_support/contact_capped_cylinder_20261003/summary.json),
[raw records](d1_review_support/contact_capped_cylinder_20261003/raw.zip) and
[supporting review](d1_review_support/contact_capped_cylinder_20261003/review.md)
bind base `999bcaea` and candidate file hashes. Source 34 checks passed.
The installed final run passed 37 installed checks plus one historical lazy
source-child compatibility check in 13.877 s, peak 350388224 bytes. A subsequent
actual installed-root lazy/no-contact check passed in 3.329 s; an additional
owner-enforced nonmidpoint-reference rejection passed in 2.099 s. Limits were
180 s / 953 MiB, effective JIT off and numerical pools one. All 237 imported
solver modules and 490 packaged source files byte-match the tested candidate.
The solver wheel SHA256 is
`4233daa198dee7859f38c8aeb75b7b06bd22f08ff0d17f002d71748d41fb704c`.

Independent scalar closest-point/integral references, virtual work and tangent
checks, rigid covariance, both-body wrench, repeated roots, multiple pockets,
through-crossing rejection, budget failure, actual static routes and restart are
covered. Sphere/infinite-cylinder compatibility passed. Earlier fixture errors,
lost-correlation/front failures, grazing roundoff and the wrong actuator field
are retained in 122 raw records across 23 bounded runs. A provisional duplicate
reference guard was removed when the test confirmed that the structural owner
already rejects curved/nonmidpoint reference B3 cells. The additional lazy test
initially demanded no package import at all after solving; the existing driver
loads its runtime facade. The corrected check requires no geometry kernel.

The independent-looking supporting scrutiny is same-model-family source review,
not engineering acceptance. Capability reporting identifies `capped_cylinder`
and the exact development profile but keeps tested/accepted/released/application
admission flags false for arbitrary submitted models. Historical D1/D2 evidence
and the complete C0–C9 goal retain their existing scopes and requirements.
