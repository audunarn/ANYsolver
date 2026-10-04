# Curved native material plane work — development

Current source8b3671c9 adds guarded simple axial fronts and reuses actual reference
area preparation in the local kernel introduced atdfd884aa. It owns no analysis,
constitutive history, restart or dynamics. Existing
native owners and straight material profiles retain their guards.

It uses the actual formulation-owned material surface:
x=(1-t)pL+t*pR+Uc*(reference half-cell lift+R0(xi)*rho(alpha)).
Normal storage is0.5*k*integral(min(g,0)^2 dA0), with explicit k in N/m³ and
the actual fixed reference material area. Both native cell rotation blocks and
all42authoritative coordinates remain. Algebraic nodal traces/resultants carry
no contact position work. Local Jet2 work maps convert to the spatial tangent
once after assembly. Pressure and line/endpoint regularization remain distinct.

Before quadrature, a continuous sufficient cofactor/frame bound proves positive
outward area for the whole declared patch. Direct oriented Q2 Bernstein projection
plus circumscribed radius gives a whole-patch plane slab. Originaldfd884aa admitted
only wholly open/fully compressed poses; current partial admission is below.
Sample positivity never supplies admission. A conservative rejection does not
prove physical inversion. No event-time or full-path claim follows.

Tensor Gauss8/16 estimates control energy, normalized force and spatial tangent
within existing dimensioned StraightNormalIntegrationSettings and a finite
interval budget. They are numerical error estimates, not rigorous certificates.
Scalar gap projects exact binary products before conversion; tangential origin
translations cannot destroy differences. Lost nonzero gaps, quadrature/reference
measure underflow, nonfinite estimates and exhausted limits fail explicitly.

Originaldfd884aa:12installed checks pass19.314s/182038528B;522source files/208imports match,JIT0/pools1.
Independent parabolic/twisted area, force and moment references, full native
virtual work/tangent, common rigid transform, hidden inversion, open state,
mixed rejection, source mutation and resource/arithmetic limits are checked.
Energy error8.88e-16J; force8.53e-14N; moment1.49e-13Nm; tangent errors1.16e-9/1.01e-8.
These are fixed-pose code checks, including intentional deep compression; they
are not accepted engineering analyses or relaxation of dimensional gap gates.

[Evidence](d1_review_support/contact_native_material_s3_20261004/curved_work_summary.json),
[supporting scrutiny](d1_review_support/contact_native_material_s3_20261004/curved_work_review.md).
## Historical partial angular contact — 78c622de

Existing PreciseNormalAngles segments negative circular arcs at each native axial
station. Its50-digit roots, coordinates and scalar values use the same exact
binary projection. Complete Jet2 interior work retains all physical section
couples. At regular g=0, potential and its first variation vanish, so moving
angular boundaries add no terms through the potential Hessian.

Each accepted axial band needs continuous sign enclosures for angular minimum,
maximum and both endpoints. These use the exact projected Q2 center derivative
and reference-owned frame derivative bound. Exact zero residual roll contributes
zero axis-rotation derivative; historical whole-patch geometry bound stays.
The guards catch thin hidden axial pockets even beside broad sampled contact,
and angular endpoint transitions despite an everywhere-negative angular minimum.
Unresolved axial fronts/topology transitions subdivide or explicitly exhaust the
finite budget. Generic axial fronts are not yet admitted. There is no silent
zero-force fallback or interval-cap increase.

17fresh installed checks pass75.871s/180441088B;522files/208imports match,JIT0/pools1.
The unchanged partial fixture uses.012m height/.03m radius and64interval cap:
energy/force/moment errors5.83e-16J/6.39e-14N/1.33e-14Nm against independent analytic
area/root integration; full spatial tangent errors1.96e-10/1.68e-11.
30visited intervals/10240integrand evaluations. This is code verification with
intentional compression; no engineering gap, initial-condition or speedup claim.
Review found and resolved zero-only/minimum-only support gaps; an incorrect test
depth assertion was corrected against its independent polynomial, with failed
evidence retained. Supporting same-family scrutiny is not independent acceptance.

[Evidence](d1_review_support/contact_native_material_s3_20261004/curved_partial_summary.json),
[review](d1_review_support/contact_native_material_s3_20261004/curved_partial_review.md).
Next: certified genuine axial fronts in the same kernel and full path controls, then
integration with the existing retained static owner. Friction/dynamics, continuum
convergence, independent acceptance and application admission remain required.

## Simple axial fronts and prepared reference area — 8b3671c9

Four scalar endpoint/circular-extremum equations now isolate simple axial roots.
Continuous first/second derivative bounds, amplitude positivity and unclipped
transport controls guard isolation; representation uncertainty is retained in
root brackets. Root bands keep their work and consume the same energy/force/
tangent error budgets. Isolation and integration share64intervals. A sin-squared
axial variable change regularizes square-root contact-width onset with its actual
Jacobian; no contact law, dimensional tolerance or resource limit is changed.
Degenerate roots and unresolved clipping/precision/resource cases fail explicitly.

Actual reference frame/derivative/lift preparation is reused once per axial
station. The same material-area formula and signed outward check stay, verified
against full geometry for twisted and rigidly transformed references. Independent
literal curvature and analytic second-derivative controls protect the cancellation
fix identified by supporting Read scrutiny.

27fresh installed checks pass58.273s/183021568B;522files/209imports match,
JIT0/pools1. The independent affine-gap/curved-area fixture has four retained
root brackets,60visited intervals and40296integrand evaluations. Errors:
3.109e-15J,9.379e-13N,2.747e-13Nm; full directional tangent5.00e-10/1.79e-9.
A previously hidden thin pocket now returns positive work; the broad-plus-thin
counterexample still rejects explicitly at root precision exhaustion.

One cProfile-instrumented evaluation takes51.586s before preparation reuse and
11.135s after. Reference geometry cost drops34.885s to1.560s reference-area cost.
This is a local single-fixture profile, not balanced complete-solve performance
or a general speedup claim. Full-route measurement remains required.

[Evidence](d1_review_support/contact_native_material_s3_20261004/curved_axial_front_summary.json),
[supporting scrutiny](d1_review_support/contact_native_material_s3_20261004/curved_axial_front_review.md).
Next: whole material-patch orientation/side/gap control along the actual native
update, then the existing retained-owner curved cycle, rollback and split restart.
No new solver stack or silent expansion of historical guards/defaults.
