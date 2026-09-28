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
average-acceleration Newmark, an optional constant nodal dead load, and the existing bounded
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

For the unloaded initial stress-free rigid approach, zero acceleration satisfies
the mass and algebraic equations. A constant nodal load is admitted only when
its initial reduced force lies in the certified physical mass range. The owner
solves that mass equation, checks the full initial balance, then recovers the
algebraic rates. A nodal moment with unresolved algebraic force fails explicitly.
The load enters every coupled Newmark residual and is bound by name and
assembled vector in the existing version-1 checkpoint. Cumulative dead-load
work is measured from the configured initial pose. Time-varying S3 loads remain
unadmitted because their derivatives enter differentiated algebraic constraints.

At each accepted pose, the algebraic velocity
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
development example; add `--constant-downward-load-n 0.0002` for a compatible
loaded run.

Focused tests cover a flat one-coordinate analytical impact with temporal
improvement and a local energy check, a tilted facet with physical offset
torque, certified nine-dimensional algebraic mass-null basis, final coupled
and algebraic residual, an independent-step smooth-branch rate check with
physical Newmark mass-action invariance, opt-in and initial-state rejection,
active-contact restart, and a large-step run that completes after two cutbacks.
The latter checks every accepted step's gap, equilibrium and physical Newmark
kinematics, then compares a fresh-model repeat of the cutback path. The full
transient file passed 26/26 after the constant-load addition. A separate flat
uniform-load case matches independent free acceleration, displacement and
external work; its active-contact response matches a forced oscillator within
2 µm, and a fresh-model split restart reproduces motion and work. An algebraic
nodal moment is rejected. A nonuniform nodal normal load also matches an
independent initial mass and algebraic acceleration solve. The tilted loaded
example completed 60 steps with
an 8.30e−4 m minimum swept penetration under its 1 mm budget. These checks
do not establish accurate
event timing at the large step or correct one-sided algebraic rates exactly at
activation and release. An early tilted case exceeded its declared 1 mm physical-gap budget;
the failure and a bounded diagnostic with a larger budget are retained. A
separate three-time-step DAE probe found that uncorrected algebraic velocity
and acceleration defects did not improve with time refinement. The current
rate recovery reduced the final smooth-stage defects to numerical roundoff;
the probe uses a different structural derivative step from the solver. The
independent mechanics reviewer agreed with the smooth-branch derivation and
identified exact contact transitions and persistent-state probe transactions
as limits for future expansion. A separate read-only review of constant-load
initialization found no concrete defect in its mass-range, algebraic-force,
work or restart handling. It identified a remaining development concern:
post-equilibrium algebraic rate recovery is not followed by a full discrete
nullspace Newmark kinematics check. The present local tests do not establish
general S3 descriptor loading or C6 acceptance.

Evidence: `tests/test_general_contact_transient_plane.py`,
`scripts/general_contact_c6_s3_dae_probe.py`, and the retained
`reports/general_contact_c6_s3_*_20260927.txt` files. The source identity,
command and environment for any claim-bearing qualification still need to be
frozen and independently assessed. General shell descriptor states, moving
tools, multiple elements, time-varying and non-nodal loads, nonlinear
materials, friction, free rigid bodies, complete work/momentum accounting
and installed package acceptance remain open.

An isolated wheel built from source commit `ee0527e6ccb99bceb15ffec064fc7fd86819d780`
has SHA256 `890fba7b8a8578722854d7b7972f1c01b641db85ddbd06621df1c78b489436ce`.
With only its installation directory on `PYTHONPATH`, the loaded tilted S3
example (`--constant-downward-load-n 0.0002`) completed 60 accepted steps,
zero cutbacks, a −0.000830315 m minimum swept gap within its declared 1 mm
budget, and a 1.11e−14 N maximum residual. This is an installed development
smoke check, not qualification or release.
