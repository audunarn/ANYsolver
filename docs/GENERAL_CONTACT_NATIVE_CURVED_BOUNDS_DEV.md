# Curved native material patch search bounds — development

Source5818670d adds current_bounds and swept_bounds to NativeRoundSurfaceRule.
They use the existing formulation-owned Q2 reference/material geometry and return
read-only lower/upper coordinates and a six-coordinate box for ContactAABBIndex.

Current geometry is current chord + Uc*b*t*(t-1)/2 + Uc*R0(xi)*rho(alpha).
Its Q2 centreline Bernstein hull, restricted at exact rational material endpoints,
is expanded by a circumscribed whole round section. Transported frame Gram error
and floating evaluation are included. Both half-cell traces are represented.
Quadrature order never determines the box. This envelope does not replace the
declared material surface with a centreline contact law.

The swept box encloses affine nodal translations and the existing spatial
Exp(alpha*omega) retained rotations. Four affine chord corners plus a circumsphere
of the reference lift and radial arm cover the entire path. The unchanged
angular increment<0.9*pi guard remains. The box may be loose; it is for search,
not physical-gap acceptance, orientation or event-time certification.

Installed checks cover independent parabolic/twisted geometry, retained motion
at fixed external nodes, a rotating path outside both endpoint boxes, actual
ANYgeometry query/refit, coordinate low parts/common rigid transform, exact
sub-ULP parameter shifts, admissible near-limit frames and malformed identity/
rotation/coordinate rejection.26checks pass in3.876s/180490240B;520package files
and204imports match, JIT0/pools1. No solve speedup or engineering acceptance claim.
[Evidence](d1_review_support/contact_native_material_s3_20261004/curved_bounds_summary.json),
[supporting scrutiny](d1_review_support/contact_native_material_s3_20261004/curved_bounds_review.md).

Existing straight material-plane/S3 contact owners retain their guards. Curved
normal force/tangent integration and continuous orientation/gap/path controls
must pass before curved coupled solves are admitted. No new public solver stack,
mandatory dependency, default or existing restart identity is introduced.
