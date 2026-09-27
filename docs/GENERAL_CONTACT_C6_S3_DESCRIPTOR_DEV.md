# Guided S3 V2D plane-impact development profile

`solve_transient_contact` has an opt-in, single-element S3 V2D development
profile: `PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_DESCRIPTOR_DEV_V0`. It is separate
from the [Q4 fixed-plane profile](GENERAL_CONTACT_C6_Q4_PLANE_DEV.md) and is
not C6 acceptance.

The admitted model has one qualified S3 V2D shell element, one declared
physical skin against one fixed rigid plane, isotropic elastic material and
zero prescribed in-plane displacement at all three nodes. Normal translation
and all three rotations remain free. The initial displacement is zero, the
initial skin is strictly open, and all nodes have the same rigid velocity
parallel to the plane normal, with zero rotational velocity. Only undamped
average-acceleration Newmark, no external load, and the existing bounded
Newton/cutback controls are admitted. Select it with
`ContactTransientSolverControls(allow_s3_descriptor_dev=True)`; the opt-in is
rejected on the Q4 route. The normal stiffness and dimensional gap tolerance
are declared in `ContactInteraction`.

The formulation-owned S3 director and reference-surface offset determine the
physical skin and rotational contact work. The owner certifies the reduced
mass-null basis and its nullity, then retains every structural coordinate in
the nonlinear Newmark equilibrium. Its effective Jacobian contains physical
mass and the current structural/contact tangent; massless rotations receive
no assigned inertia and are not condensed using a contact-free stiffness.

For the initial stress-free rigid approach, zero acceleration satisfies the
mass and algebraic equations. At each accepted pose, the algebraic velocity
is recovered from `Z.T K(q) v = 0`, where `Z` spans the declared mass nulls.
The algebraic acceleration satisfies
`Z.T (K(q) a + F''(q)[v,v]) = 0`. The current contact-plane penalty is
piecewise quadratic in its affine gap, so its smooth-branch directional second
derivative is zero. The structural directional second derivative is evaluated
by a bounded central difference of its tangent, using the explicitly exposed
`s3_descriptor_difference_step_s` control (default `1e-5 s`). These rate
corrections lie in the certified mass-null space and are checked not to change
physical inertia. At an exact touch or release endpoint the current code uses
the closed-side tangent; the correct one-sided algebraic rate at that event has
not been established. This limits the profile to development use even though
the accepted endpoint gap and equilibrium checks run at every step.

Each accepted step checks coupled residual, independent endpoint gap and the
minimum physical corner gap along its declared cubic Hermite path. The
`save_every=1` checkpoint can resume a compatible, grid-aligned active-contact
step on a fresh model. Run
`python examples/general_contact_s3_plane_impact.py` for the tilted-skin
development example.

Focused tests cover a flat one-coordinate analytical impact with temporal
improvement and a local energy check, a tilted facet with physical offset
torque, certified nine-dimensional algebraic mass-null basis, final coupled
and algebraic residual, an independent-step smooth-branch rate check with
physical Newmark mass-action invariance, opt-in and initial-state rejection,
and active-contact restart. An early tilted case exceeded its declared 1 mm physical-gap budget;
the failure and a bounded diagnostic with a larger budget are retained. A
separate three-time-step DAE probe found that uncorrected algebraic velocity
and acceleration defects did not improve with time refinement. The current
rate recovery reduced the final smooth-stage defects to numerical roundoff;
the probe uses a different structural derivative step from the solver. The
independent mechanics reviewer agreed with the smooth-branch derivation and
identified exact contact transitions and persistent-state probe transactions
as limits for future expansion.

Evidence: `tests/test_general_contact_transient_plane.py`,
`scripts/general_contact_c6_s3_dae_probe.py`, and the retained
`reports/general_contact_c6_s3_*_20260927.txt` files. The source identity,
command and environment for any claim-bearing qualification still need to be
frozen and independently assessed. General shell descriptor states, moving
tools, multiple elements, loads, nonlinear materials, friction, free rigid
bodies, successful cutback recovery, work/momentum accounting and installed
package acceptance remain open.
