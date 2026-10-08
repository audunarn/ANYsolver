# Fixed-plane hemisphere support — development profile

`CLASSICAL_B2_B3_HEMISPHERE_SUPPORT_PLANE_STATIC_DEV_V1` is implemented and
locally tested, including a private installed artifact. It has no independent
engineering acceptance, application admission or release.

Run `examples/general_contact_hemisphere_plane.py` with the solver installed.
Select `ContactSolverSettings(pair_motion="general",
beam_end_cap_work="hemisphere_support_dev")`, explicitly declared round radius,
`beam_end_caps="hemisphere"`, line stiffness in N/m², endpoint stiffness in N/m
and dimensional gap tolerance. The default remains `owned_point`.

## Decision and equations

The old owned-point law loses 0.0125 J across an active ownership switch in a
fixed-endpoint rotation fixture while its endpoint does zero work. That law and
its strict switch rejection are preserved. A generalized tangent cannot remove
the finite jump. This candidate is a separately identified geometry and endpoint
potential, with no empirical blending.

For cap centre c, actual outward centreline tangent unit vector d, fixed plane
unit normal n, h=(c−p)·n and β=n·d, the minimum hemisphere gap is

\[
g=\begin{cases}h-R,&\beta\le0,\\
h-R\sqrt{1-\beta^2},&\beta>0.\end{cases}
\]

The support point is c−Rn on the spherical branch and
c−R(n−βd)/sqrt(1−β²) on the rim branch. Endpoint storage is
½kₑ min(g,0)². Its residual is kₑg Dg and active tangent is
kₑ[Dg⊗Dg+gD²g]. Normal force and its physical moment come from the same
work map. Rim derivatives generate couples through all centreline nodes,
including B3 midnode arms. At β=0 gap and first derivatives are continuous;
the spherical one-sided Hessian is selected. Smooth central differences are
not valid across that kink.

The existing distributed line potential and its reference length measure are
reused. This is a frictionless centreline-envelope support spring. It is not
cap-surface pressure integration or a material-surface profile with section spin,
friction, cross-section deformation or Hertz pressure accuracy.

## Admission, geometry and state

- One explicit B2/B3 selection against one fixed analytic plane. Concentric
  isotropic elastic scalar sections and von Karman kinematics only.
- Genuine ends use incidence of all material beam nodes, including unselected
  members and B3 midnodes. Artificial selection boundaries do not gain caps.
- Gap tolerance must be smaller than radius. Positive endpoint height and
  regular physical curves are required; unresolved geometry fails explicitly.
- Exact binary-input fractions choose support branches and activation signs.
  Conjugate subtraction retains small nonzero gaps; unrepresentable gaps fail.
- Entire B2/B3 plane height uses exact polynomial minima and an outward normal
  norm enclosure. The radius envelope contains each actual hemisphere. Along
  the affine static path, each material height is affine, so endpoint envelopes
  plus exact curve regularity certify the admitted sweep. This does not certify
  transient or rotating-plane paths.
- Sparse local blocks include all cap node mappings. Reactions are recovered
  after assembly. Restart binds profile, cap work revision, true-end topology,
  law, geometry and swept settings. Old-law checkpoints are incompatible.

## Checks actually run

The private installed run passed **35 checks in 5.181 s**, with **343,699,456 B**
peak process-tree memory, JIT disabled and all measured thread pools at one.
237 loaded modules and all 502 package files matched candidate bytes.

Checks include independent scalar support/work, smooth directional tangents at
the retained 10⁻⁵ target, skin-point force/moment balance, B3 midnode terms,
closed-seam continuity and solver traversal, independently derived bar response
at 10⁻⁶, force/displacement controls, support reactions, split restart through
the seam, opening/recontact geometry, exception/cancellation replay, rigid
covariance, connectivity reversal, collapse/hidden crossing rejection, capability
non-admission, transient rejection and inherited legacy/no-contact routes.

[Evidence](d1_review_support/contact_cap_transition_20261004/summary.json) contains
nine measured runs and 54 raw records. Initial fixture defects and the old-law
discriminator remain recorded. [Supporting review](d1_review_support/contact_cap_transition_20261004/support_review.md)
closed setting/control admission, body-kind and candidate-vector checks; it is
same-family source scrutiny, not independent engineering acceptance.

Beam-pair, radial-obstacle and shell-boundary cap transitions remain open.
Structural mesh/enforcement qualification, general finite rotation, materials,
beam surface friction, native contact, dynamics and full C0–C9 completion remain
required. There is no whole-programme speed-up or delivery-date claim here.
