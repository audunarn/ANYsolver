# Curved native pair: moving nearest-feature switch

Development derivation, 5 October 2026. This records the prospective opt-in
candidate. It is not native engineering acceptance or a change to contact physics.

## The discriminating observation

The archived first-cell-rotation fixture has a remote Voronoi switch: two distinct
interior closest target points, separated by 4.327966 mm, at source coordinate
x=1.0021686121569167 m. Shared physical-junction endpoint ownership cannot admit
that interval. The old rejected result remains rejected. Raw discriminator:
`C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate16/source_curved_ownership_discriminator`.

## Discrete work and switch derivative

For one directional integral use its fixed material station s, reference speed
J, line stiffness k and combined declared radius r. The existing nearest-distance
potential density is

    e(s,q) = (k J(s)/2) min(0, min(d_L(s,q),d_R(s,q))-r)^2.

At an isolated transverse switch a(q), orient labels so D=d_L-d_R is negative
to the left and positive to the right. Then D_s>0 and

    a_q = -(d_L,q-d_R,q)/D_s.

Both branches have the same energy at the switch. Differentiating the two
integrals therefore produces no gradient boundary term. Differentiating their
gradients does produce the geometric Hessian contribution

    H_switch = -k J(a) g(a) outer(d_L,q-d_R,q, d_L,q-d_R,q)/D_s.

This applies for active g<0; open switches contribute zero. The coefficient is
nonnegative. The distance-station derivative follows the envelope theorem:
`d_i,s = n_i dot x_source,s`, including strictly constrained endpoint minima.
Use the same 36 geometric coordinates for both gradients. Add this Hessian before
the existing pullback to all 84 retained/native coordinates. Apply the same
one-half directional weight as the distributed potential exactly once.

At a shared physical target endpoint, coincident position and work maps make the
gradient difference zero. No remote-switch term is then needed. At an active
source-domain endpoint, a switch generally has only a one-sided derivative;
unresolved endpoint switches are rejected rather than assigned a smooth tangent.

## Required bounded admission

Every source interval must have a complete owner certificate or a single-root
certificate. Distance Lipschitz bounds certify root-free intervals. Strong
convexity of each target squared-distance problem supports unique projection
and bounded projection motion. Enclosures of both normals and source tangents
must bound D_s away from zero on a switch bracket. Endpoint signs then inventory
one root completely. Samples alone cannot establish completeness.

Near isolated roots, a factored squared-distance difference evaluated from exact
binary64 polynomial coefficients avoids cancellation between nearly equal
distances. With `phi=(x_target-x_source) dot x_target,t` and squared-distance
curvature lower bound m, projection station error is at most `2 abs(phi)/m` and
squared-distance surplus at most `2 phi^2/m`. Endpoint error is zero only with
the exact constrained stationarity sign. These bounds supply root intervals;
they do not make the floating-point force or tangent exact. Root, projection
and floating-point evaluation uncertainty must also bound variations in gap,
reference speed, gradient difference and the transverse slope. Their contribution
must fit the existing aggregate integration-error budget.

Nonunique target projections, unresolved tangencies/multiple roots, coincident
active normals, exhausted cell/depth/integration budgets and insufficient floating
resolution produce explicit non-success. The algorithm is opt-in and restart
bound; historical V4/V6 defaults remain unchanged.

Independent checks must differentiate a scalar energy reference with a moving
switch, verify complete both-body work and directional tangents, and inspect
root completeness. Same-family review supports development but does not supply
the outstanding different-family engineering acceptance.

## Physical length chart and near-C1 transition bands

The four half-cells have 36 Cartesian position entries, including two copies of
each beam's material junction. A fixed Boolean map B ties these duplicates to
30 independent physical-length coordinates. Both positions and their native
Jacobians obey `x36=B x30` and `J84=B J30` exactly. Error accounting uses
`B.T gradient` and `B.T Hessian B`, preserving N and N/m units. Native rotational
and algebraic coordinates are assessed separately by work and directional checks.
Floating error is bounded before cancellation. The default V4/V6 error chart and
checkpoint identities remain unchanged.

A generic rigid transform exposed a microscopic non-C1 junction in binary64
geometry. The V7 candidate and its first coupled curved run remain NONPASS. V8
adds bounded transition-band integration instead of snapping the geometry.

Let both target tangents lie in a forward cone around axis e, with axial
derivative at least a>0 and perpendicular magnitude at most kappa times the
axial magnitude. Require positive source crossing bound

    beta = (min(e dot source_tangent)
            -kappa max(norm(source_tangent_perpendicular)))/sqrt(1+kappa^2).

Endpoint stationarity functions `phi_L=(junction-source) dot tangent_L` and
`phi_R=(junction-source) dot tangent_R` are strictly decreasing. Exact polynomial
signs bracket their roots. Their ordering distinguishes a shared-endpoint
plateau from an overlap with two interior projections. Plateaus are integrated
normally; only uncertain endpoint-root brackets need a bounded approximation.

At a remote equal-distance root, `Delta n=(target_R-target_L)/d`. The target
separation lies in the forward cone, giving `D_s >= beta norm(Delta n)`. Together
with the monotone stationarity inventory, this admits at most one remote root.
In the physical length chart,

    norm(Delta distance_gradient) <= (3+6*d/a) norm(Delta n),
    norm(H_switch) <= k*J*abs(g)*(3+6*d/a)^2*norm(Delta n)/(2*beta).

Strong convexity bounds the projections' distances from the junction and thus
`norm(Delta n)`. Complete interval bounds, exact unnormalized-axis Gram ratios
and outward conversion protect this certificate.

Microscopic bands retain a midpoint contact contribution. Its error includes the
full integrated-density bound, the absolute returned midpoint contribution,
possible switch Hessian and floating evaluation error. All consume the existing
shared half reserve and aggregate controls. If the bounds do not fit, the regular
partition is attempted; unresolved cases fail explicitly. V8 binds this numerical
policy into the opt-in identity and rejects incompatible V7 continuation.

## V9-V12 complete support and floating activation

Joining exactly adjacent pieces with the same physical owner and support flag
does not remove any target projection cut, but quadrature parity alone cannot
certify activation. V9 missed a thin open strip; its independent directional
tangent failed despite matching potential. V10 requires a complete active
certificate from an admissible affine target-station map: its Q2 difference
Bezier hull bounds distance above. Exact stored-float rational coefficients
and directed conversion enclose the represented polynomial geometry.

Unresolved microscopic strips may be omitted only with absolute whole-interval
energy, force and tangent bounds. Strong target-projection convexity gives
the endpoint-stationarity correction phi^2/(m*d), with F'' >= 2*m. Source reach,
distance floor and all physical point-map multiplicities enter the bounds.
There is no cancellation-based or sample-only omission. Existing shared half
reserve and complete aggregate error checks remain mandatory.

V11 gives each omitted strip at most half the dimensional tolerance divided
by the maximum integration-cell count. Every omitted strip consumes a visited
cell, so the sum cannot exceed the original half reserve. This prevents one
early microscopic strip from spending the entire reserve; it neither changes
the tolerances nor raises the cell cap.

V12 handles a floating evaluation contradicting the exact active certificate
by discarding the entire partial quadrature rule. The complete interval must
fit those same absolute bounds or be subdivided. A single rounded zero-gap
sample never drops its Hessian silently; unrelated failures propagate. The
opt-in V12 identity binds this policy. Historical V4/V6 defaults are unchanged.

## V14 actual-path swept curvature enclosure

The native retained path is defined by context.advance(start,t*increment).
Nodal translations are affine (stored as compensated pairs); retained rotations
are exp(t*[w])R_start. A physical Q2 half-cell has the exact represented shape

    r(s,t)=(1-s)p_left(t)+s*p_right(t)+4*s*(1-s)*R(t)*lift.

Since 0<=4*s*(1-s)<=1, per-body speed is bounded by maximum nodal increment
norm plus maximum cell |w|*|R_start*lift|. Acceleration is bounded by maximum
cell |w|^2*|R_start*lift|. Sum both bodies' bounds to obtain relative V and A,
with outward arithmetic and floating evaluation allowances.

For a time interval width h and endpoint global gap lowers g0,g1, every fixed
material-station pair has endpoint distance at least rho+min(g0,g1). Its speed
is at most V. Therefore a complete-interval distance floor is

    d0=rho+min(g0,g1)-h*V/2-roundoff.

When d0>0, the norm f=|r_a-r_b| satisfies

    f''=(|v|^2-(n dot v)^2)/f+n dot a <= V^2/d0+A = K.

A scalar with f''<=K lies above its endpoint chord minus K*h^2/8. Both endpoints
of every fixed pair exceed their global endpoint lower, hence taking the infimum
over all material pairs gives a complete physical-gap lower

    g(t) >= min(g0,g1)-K*h^2/8-roundoff.

No smoothness of the nearest-material feature is assumed. This remains valid
across projection/ownership switches. Combine with the existing first-order
lower; when the positive floor is unproved, retain ordinary bounded subdivision.
All curved endpoint and midpoint shortcuts use directed lower arithmetic;
historical noncurved behavior remains unchanged. The V14 owner event-policy key
binds this certificate even with secant control disabled. Cancellation, finite
sweep budgets and the dimensional endpoint gap remain required. Supporting
source review checks the equations; development numerical evidence is separate.