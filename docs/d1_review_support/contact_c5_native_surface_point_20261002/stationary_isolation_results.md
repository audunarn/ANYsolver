# Bounded stationary-front isolation — development

Added fixed-angle Taylor enclosure from analytic A/B derivatives. C(t) quadratic,
centreline affine, arm Exp: norm bounds on A''' and B''' imply
|N''| <= |A'''B|+|A''B'|+|A'B''|+|AB'''|. Complete time coverage requires
B bounded away from zero and either N sign exclusion or N' strict monotonicity.
Finite budget/resolution/singularities fail explicitly. No production connection.

Saved fold: complete time cover succeeds in1slab. Front coordinates at t=0,
stationary t~.5 and t=1 are .7244844272099441, .7244843413242318,
.7244844234694856. Local geometry/derivative/partition check passes before and after
review correction (1test per changed candidate). Final pytest4.12s/test.22s.

Reviewer confirmed calculus; found product cancellation omitted from padding.
Added coefficient/product-scale arithmetic error propagation. Retain actual root
bracket, numerator residual and a deliberately conservative axial interval based
on plane/relative-position norms and denominator lower bound. This broad interval
is NOT a qualified spatial partition boundary. Product-error arithmetic still needs
independent extreme-scale controls; root endpoint sign uncertainty also needs explicit
admission handling before promotion. No whole-angle or whole-patch completeness claim.

Next tighten and enforce front coordinate uncertainty against an explicit integration
budget, add singular/multiple/endpoint-root controls, then connect fixed-angle moving
axial cuts with angular support. Keep shared resource counters across angular calls.
No full aggregate/coupled rerun until this integrated geometry contract is ready.
