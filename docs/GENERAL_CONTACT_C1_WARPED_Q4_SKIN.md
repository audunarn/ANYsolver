# C1 development ingredient: warped Q4 physical reference skin

`WarpedQ4Skin` is an internal geometry adapter for the qualified
`varying_frame` Q4. It is **not an admitted contact profile**. Public
`validate_general_contact` continues to reject warped Q4 contact.

For Q4 shape values (N_i(\xi,\eta)), the adapter retains the original
bilinear midsurface (r=\sum_i N_i X_i). It obtains the physical director
from the qualified Q4 varying-frame route, including the formulation's
reference-normal and polarity rules. The represented reference skin is

\[
x_{\rm skin}=r+z_{\rm side}d,
\qquad z_{\rm side}\in\{-t/2,0,t/2\}.
\]

With (c=r_{,\xi}\times r_{,\eta}) and
(m=r_{,\xi\eta}), the unnormalized director derivatives are
(c_{,\xi}=r_{,\xi}\times m) and
(c_{,\eta}=m\times r_{,\eta}). Projecting those derivatives perpendicular
to the normalized director gives the exact parametric skin tangents and
reference surface measure. No triangulation substitutes for Q4 geometry.

The adapter's axis-aligned bounds contain the whole reference skin because
the bilinear midsurface lies inside its nodal convex hull and each director
component has magnitude at most one. A reference plane-gap certificate
subdivides the parametric square. On each cell, the midsurface's normal
projection reaches its minimum at a cell corner; the affine (c\) field
provides a lower norm bound and hence a Lipschitz bound for director change.
Subdivision stops only when the sampled minimum and conservative lower gap
differ by the requested dimensional accuracy. The cell and depth limits fail
explicitly. This certificate applies to the **reference skin only**.

Focused tests compare position with an independent bilinear-normal formula,
tangents with finite differences, top/bottom separation, rigid transforms,
director-polarity equivalence and dense samples against the conservative
bounds. An independent warped example has an edge-interior plane-gap minimum
more than 10 mm below its corner minimum; its certificate closes within a
declared 2 mm accuracy. Six further mild warped samples check lower-bound
containment. The result is `c1-warped-q4-skin-local3.txt` in
`C:\ANYworkspaceWork\general-contact-evidence` (5 passed).

Before solver admission, extend the local work map to authoritative global
coordinates and verify current-pose and swept gap checks, transaction/restart
behavior, coupled response and independent acceptance. The existing warped
Q4 rejection remains appropriate until then.

## Local plane-contact work kernel

`WarpedQ4PlaneMortar` adds an internal small-rotation, frictionless Q1
pressure-space kernel against an analytic plane. It integrates on the
physical reference skin with explicitly selected Gauss orders and a
separately specified relative integration tolerance. The higher-order
integral is used for the result; disagreement beyond the tolerance fails.

For plane normal (n), skin offset (z_{\rm side}), local nodal translation
(u_i) and rotation (\theta_i), its linearized normal-gap variation is

\[
\delta g=\sum_i N_i\left[n\cdot\delta u_i+
z_{\rm side}(d\times n)\cdot\delta\theta_i\right].
\]

The same integrated weighted gap and gradient define the nodal-pressure
penalty potential, residual and smooth-branch tangent. This map gives zero
work for a station-local drill rotation and includes the physical offset
couple. Independent 20×20 surface integration, directional energy/tangent
checks, global force and moment balance, a common rigid-rotation virtual
mode, opposite top/bottom offset couples and deliberate integration-budget
failure passed in `c1-warped-q4-plane-local2.txt` (8 focused geometry/work
tests including the skin checks).

The kernel holds the reference director fixed inside a linearized increment.
The matching `certify_linearized_plane_gap` now bounds the represented pose
(r+Nu+z_{\rm side}[d+(N\theta)\times d]). Its cell lower bound combines
the exact corner minimum of the bilinear translated midsurface, the earlier
varying-director bound and a convex-hull bound on interpolated nodal
rotation. `certify_linearized_swept_plane_gap` checks both endpoints of a
linear coordinate and plane-translation path; the represented gap is affine
in path fraction at each material point, so those endpoint lower bounds
contain the whole path. Resource limits fail explicitly. An independent
dense current-pose oracle, zero-increment reference equivalence, rigid-mode
check and sampled interior path passed in
`c1-warped-q4-current-gap-local2.txt` (10 geometry/work tests).

This is still a linearized model using the reference director. It has no
global static contact owner, transaction/restart route or demonstrated
compatibility with the qualified Q4's coupled nonlinear displacement and
rotation equations. The endpoint argument does not apply to finite SO(3)
director motion. Warped Q4 remains rejected by `validate_general_contact`;
the local kernel is not an accepted contact capability.
