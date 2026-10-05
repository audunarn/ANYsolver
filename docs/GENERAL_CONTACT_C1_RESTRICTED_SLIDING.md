# General contact C1 development profile: restricted planar sliding

This opt-in profile is implemented and locally tested. It is **not independently
accepted**, and it does not complete C1. Its public identity is
`PLANAR_Q4_S3_PAIR_RESTRICTED_SLIDING_MORTAR_DEV_V0`.

## Use and exact boundary

Set `ContactSolverSettings(pair_motion="restricted_sliding",
sliding_difference_step=<positive length>)` and pass it as `contact_settings`
to `solve_static_nonlinear`. Pass the same settings to
`validate_general_contact` to inspect this profile. The older guided-pair
route remains the default.

- Two named, disjoint planar Q4 or S3 V2D physical shell surfaces, one face
  on each side, must have a positive projected overlap in the reference
  pose. Physical top/bottom orientation is checked. The integration side is
  fixed by the explicit pair definition.
- Each face may translate uniformly in its tangent plane. Its nodal normal
  displacements may differ. Candidate rotations are fixed at zero; physical
  top/bottom offset couples still enter the shell rotational residual.
  Structural constraints must enforce the movement restriction.
- Contact is frictionless, penalty-enforced, and available through von Karman
  nonlinear static force or displacement control. `normal_stiffness` is Pa/m,
  `gap_tolerance` and `sliding_difference_step` are lengths in metres.
- A current-overlap mortar law transports P1/Q1 support and weighted gap.
  The restricted tangent uses numerical differentiation of its transported
  residual; at first-touch active-set boundaries it uses the matching
  one-sided branch. Coincident projected edges with non-smooth overlap
  derivatives cause an explicit failure.
- A conservative subdivision check certifies the represented physical gap
  against the declared tolerance. A swept convex-overlap check inspects the
  linear trial path, including cases with no overlap at either endpoint.
  Planar S3 and exact-parallelogram Q4 projections use quadratic interior
  and edge extrema with a floating-point guard; other admitted Q4 outlines
  use bounded subdivision. Results identify the method as
  `gap_check_method` and report its independent lower gap bound.
  For a path with exactly fixed projected overlap, certified endpoint gaps
  also certify the entire path because the pointwise gap is affine in the
  trial parameter.
  Unresolved paths are cut back with a finite iteration bound; exhausted
  limits fail rather than accepting a missed crossing. Initial penetration
  beyond geometric roundoff is rejected.
- Version-2 static restart binds this profile, contact definition, numerical
  step and resource settings. The frictionless penalty law has no committed
  physical contact history.

This profile has no general shell in-plane deformation, shell rotation,
warped Q4, multiple-face transfer, edge/corner contact, augmentation,
friction, self-contact or dynamic response. It cannot initialize a pair
without projected reference overlap. Force/reaction and gap results are
development evidence only; engineering acceptance still requires the C1
patch, sliding, refinement and independent-review gates in the main plan.
Q4/Q4 coupled pressing, relative lateral motion and restart, plus S3/Q4
coupled pressing, have completed local checks. A Q4 integration/S3 target
case stopped at a declared 10 µm gap budget. Exploratory full-load solves
with a deliberately relaxed 1 mm budget measured pointwise gaps of about
−19.2, −16.6 and −15.0 µm at normal regularization values of
1×10⁶, 4×10⁶ and 1.6×10⁷ Pa/m. Only one of its four weighted pressure
gaps was compressive at 1.6×10⁷ Pa/m;
the pointwise violation remained. These relaxed solves are diagnostics, not
passes. Partial-contact pressure-space and mesh refinement are still open,
as are S3/S3 coupled results. Validation reports the structural profile,
not independent engineering acceptance.

Run `examples/general_contact_restricted_sliding.py` for a prescribed
lateral path under constant normal loading. Focused checks are in
`tests/test_general_contact_sliding_static.py`,
`tests/test_general_contact_sliding_map.py`,
`tests/test_general_contact_moving.py` and
`tests/test_general_contact_overlap.py`.

The exploratory Q4/Q4 press case used a 6 µm declared gap budget for a
0.05 m thick shell and 0.4 N load. Earlier 1 and 3 µm runs stopped at
their declared limits; their failed outputs remain in
`C:\ANYworkspaceWork\general-contact-evidence`. These settings and outcomes
are not a formal qualification tolerance or a universal recommendation.
