# Exact rational Action enclosure

This bounded verifier evaluates the existing represented-law Action; it
does not change that law, execute equilibrium or qualify a physical case.
`decimal_value()` remains unchanged and display-only.

Inputs have an exact rational contribution and a bounded inventory of
integrals `integral_a^b p(tau)*cos(Omega*s) ds`, where tau=(s-a)/(b-a) and
p has at most six coefficients. An exact event sweep restricts overlapping
polynomials to the union partition and cancels them before numerical
enclosure. Positive intervals are never converted to floating coordinates.
Source and normalized representations have separate exact-byte hashes.

The user declares one fixed Taylor degree m, from 0 through 128, in the
resource budget. For each retained interval, put h=b-a, x=Omega*a and
delta=Omega*h. The degree-m Taylor polynomials at zero approximate cos(x)
and sin(x), each with the rigorous Lagrange remainder bound
`abs(x)^(m+1)/(m+1)!`, since every derivative has magnitude at most one.

Expand `cos(x+delta*tau)` through degree m in tau. Integrating its even and
odd terms against p gives exact rational weights C and S multiplying
cos(x) and sin(x). The contribution is enclosed by center
`h*(C*cos_polynomial(x)+S*sin_polynomial(x))` and radius

```
h * ((abs(C)+abs(S))*abs(x)^(m+1)/(m+1)!
     + abs(delta)^(m+1)/(m+1)! * sum_j abs(p_j)/(j+m+2)).
```

The second term bounds the integrated local Taylor remainder directly in
tau; it introduces no negative powers of a tiny interval width. Centers,
radii, partition restrictions, summation and final comparisons use exact
Fractions. No libm sine/cosine value or quadrature estimate supplies a bound.

Saved comparisons divide the interval error by a positive declared scale.
The entire error interval must satisfy the supplied frozen limit. Definite
failure is FAILED; an interval straddling the limit is HOLD_UNRESOLVED.
There is no automatic order, precision or method retry. A separately
registered higher-order request would have a different execution identity.

Explicit caps cover union intervals, fraction sizes, cumulative checked
integer bits, exact operations and estimated workspace, including fixed
scalar scratch. Saved value, scale and limit are checked and
charged before enclosure, reducing the remaining shared arithmetic budget.
Small or cancelling results cannot conceal oversized comparison operands.
These estimates do not replace supervised peak-memory qualification. The existing Action
constructor bounds and owns input polynomials; returned values are immutable
exact scalars, strings and a fresh diagnostic record. The verifier makes no
equilibrium or quadrature call.

Tests compare against independently integrated high-precision analytical
primitives, exercise signed overlaps and different-partition cancellation,
retain intervals with equal floating endpoints, and distinguish exact-limit
acceptance, definite failure and unresolved bounds. The high-precision
primitive oracle is a diagnostic crosscheck, not itself a scientific
certificate. Resource, malformed-scalar and ownership checks are separate.
Physical work/reaction admission still requires bound recovery inputs,
independent routes and the complete frozen observation inventory.
