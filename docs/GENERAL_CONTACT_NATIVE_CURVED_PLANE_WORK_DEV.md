# Curved native material plane work — development

Source dfd884aa adds NativeCurvedMaterialPlaneWork as a local geometry/work
kernel. It owns no analysis, constitutive history, restart or dynamics. Existing
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
plus circumscribed radius gives a whole-patch plane slab. Only wholly open/fully
compressed poses are currently admitted; mixed fronts reject pending segmentation.
Sample positivity never supplies admission. A conservative rejection does not
prove physical inversion. No event-time or full-path claim follows.

Tensor Gauss8/16 estimates control energy, normalized force and spatial tangent
within existing dimensioned StraightNormalIntegrationSettings and a finite
interval budget. They are numerical error estimates, not rigorous certificates.
Scalar gap projects exact binary products before conversion; tangential origin
translations cannot destroy differences. Lost nonzero gaps, quadrature/reference
measure underflow, nonfinite estimates and exhausted limits fail explicitly.

12installed checks pass19.314s/182038528B;522source files/208imports match,JIT0/pools1.
Independent parabolic/twisted area, force and moment references, full native
virtual work/tangent, common rigid transform, hidden inversion, open state,
mixed rejection, source mutation and resource/arithmetic limits are checked.
Energy error8.88e-16J; force8.53e-14N; moment1.49e-13Nm; tangent errors1.16e-9/1.01e-8.
These are fixed-pose code checks, including intentional deep compression; they
are not accepted engineering analyses or relaxation of dimensional gap gates.

[Evidence](d1_review_support/contact_native_material_s3_20261004/curved_work_summary.json),
[supporting scrutiny](d1_review_support/contact_native_material_s3_20261004/curved_work_review.md).
Next: moving curved contact-front integration and its gap/support controls, then
integration with the existing retained static owner. Friction/dynamics, continuum
convergence, independent acceptance and application admission remain required.
