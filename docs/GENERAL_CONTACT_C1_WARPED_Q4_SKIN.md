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

Before solver admission, derive and verify the work map for authoritative
nodal displacements and shell rotations, current-pose and swept gap checks,
the selected mortar integration and its tangent, transaction/restart
behavior, coupled response and independent acceptance. The existing warped
Q4 rejection remains appropriate until then.
