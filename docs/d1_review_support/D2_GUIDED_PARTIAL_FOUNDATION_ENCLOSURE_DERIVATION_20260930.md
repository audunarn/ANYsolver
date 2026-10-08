# Saved-field analytical error enclosure

Development assessment of the fixed nx79/nx159 guided partial-foundation cases.
No contact or structural kernel evaluation and no radial failure regrade.
The 0.1% analytical and 2% physical-bin targets remain unchanged. This document
does not establish installed admission or general D2 acceptance.

## Reference arithmetic and the true front

Use the binary input D in each actual case, not a differently rounded nominal D.
All reference midpoint values use Decimal at80digits; only the final values are
converted to binary64. The fixed domain is D between1602and1603N/m, q=.5Pa,
κ=10⁶Pa/m, L=1m, Ls within1e-16m of.9m, g within1e-18m of100µm, width1m.

The independent reference's strictly increasing required-gap function brackets
the true front in[.7,.8]m. β is between24and26/m and its exponential arguments
in this bracket have magnitude at most5.2. Positive cosh denominators exceed1;
division by β, D and a has denominators respectively above24,1602and.7.
At80digits, exponential rounding is below1e-76 here; propagation through the
few dozen operations in the positive required-gap expression is below1e-70m.
The1e-60m function guard is deliberately larger. Update a bracket endpoint only
when the guarded function sign is resolved. Otherwise retain the bracket.
Bisection midpoint rounding changes the proposed endpoint, not the validity of
the sign-tested retained endpoint. No inferred point root replaces the bracket.

The derivative lower bound exceeds2e-4 on this bracket:
`q/D * a * tanh²[β(Ls-a)] >= .5/1603*.7*.98² > 2e-4`.
All omitted derivative terms are nonnegative. The point formulas' front
sensitivity is below1 throughout the fixed domain: the open derivative is
bounded by `g/a²+q/(2D)`; the active terms are bounded by
`q*β/κ+2*q*T/D`; the tail inherits the cut value's bound.
Their arithmetic errors are below1e-60m. The resulting bracket width is checked
against the declared point allowance before assessment. Final binary64 conversion
for displacements below1e-3m has absolute error below2e-19m. The overall point
allowance1e-18m includes that conversion, arithmetic and front uncertainty.

The closed force uses the same guarded root. Its front sensitivity is below2N/m
on this domain. The1e-15N allowance dominates root/arithmetic error and the final
conversion of a force below.5N. These are fixed-domain arithmetic allowances,
not universal assumptions about NumPy transcendental accuracy.

## Field and integral bounds

The actual saved source rows must be exactly tied. For the stored linear field,
`L_FE=max|Δw/h|+1e-12`; the additive budget covers slope and knot-coordinate
rounding. With nx at most159, h above.006m and |w| below1e-3m, coordinate and
interpolation error is below1e-15m; retain the larger1e-14m allowance. This also
covers conversion between the nominal1m parameter and the represented source
abscissae. This allowance does not represent a change to the solved model.

Integrating the ODE from the free tip gives
`w'(s)=[-q(L-s)+integral_s^Ls p]/D` (the integral is zero beyond coverage).
Positivity and the positive clamp reaction give `0<=Fcontact<=qL`, hence
`L_ref<=2qL/D`. Add1e-12 to the computed slope bound for outward rounding.
The field is continuous at the front/cut; derivative jumps do not defeat a
global Lipschitz bound.

Partition[0,1] into1,000,000 cells and evaluate every reference midpoint at80digits.
For cell radius r (rounded outward by1e-15m), set

- `e_radius=(L_FE+L_ref)r+δ_FE+δ_ref`;
- `w_radius=L_ref*r+δ_ref`.

Then squared numerator bounds are
`h*max(|e_mid|-e_radius,0)²` and `h*(|e_mid|+e_radius)²`.
Reference denominator bounds use the corresponding expressions for |w_mid|.
Positive sums are rounded outward using
`gamma=(10N+100)*eps/[1-(10N+100)*eps]`.
For a computed positive sum y, use lower y/(1+gamma) and upper y/(1-gamma),
then round each endpoint outward. Reject a nonpositive lower denominator. The norm-ratio bounds follow by dividing
the outward numerator/denominator bounds and taking square roots. Their reported
endpoints receive additional outward rounding. Thus the result bounds an
integral norm, rather than labelling a sampled norm exact.

The maximum of cellwise error upper bounds encloses the global absolute error.
The reference tip value supplies a positive lower bound on its supremum norm;
no assumption that the tip is its unique maximizer is needed.

The assessment requires the finer mesh's enclosed L2 upper bound to be below the
coarser mesh's lower bound and the existing physical-bin error to improve. This
is a decision check for this refinement pair, not a new universal contact gate.
All original work, gap, pressure-positivity and resource dispositions remain.
