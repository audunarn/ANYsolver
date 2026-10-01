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
work is measured from the configured initial pose. A separate development profile
now admits scalar piecewise-linear dead nodal histories only with exactly zero
represented algebraic base-load projection; other time-varying S3 loads remain
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
physical inertia. At an exact touch or release endpoint this original profile uses
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

A bounded follow-up used the existing tilted-impact probe at 0.2, 0.1 and
0.05 ms steps. Its maximum nullspace Newmark position defects were 1.85,
1.12 and 1.12 µm; velocity defects were 0.0295, 0.0224 and 0.0224 m/s.
At 0.1 ms the maximum occurred when active pressure nodes changed from one
to three at 0.0102 s. Steps with unchanged active counts in this fixture had a maximum
nullspace velocity defect of 9.25e−15 m/s. The result isolates an event-stage
rate/kinematics discontinuity; it does not justify claiming full-coordinate
Newmark consistency at activation. Event-aware algebraic-rate handling must
be designed and verified before this profile can be accepted.

Evidence: `tests/test_general_contact_transient_plane.py`,
`scripts/general_contact_c6_s3_dae_probe.py`, and the retained
`reports/general_contact_c6_s3_*_20260927.txt` and
`reports/general_contact_c6_s3_discrete_kinematics*_20260928.txt` files. The source identity,
command and environment for any claim-bearing qualification still need to be
frozen and independently assessed. General shell descriptor states, moving
tools, multiple elements, general time-varying and non-nodal loads, nonlinear
materials, friction, free rigid bodies, complete work/momentum accounting
and installed package acceptance remain open.

An isolated wheel built from source commit `ee0527e6ccb99bceb15ffec064fc7fd86819d780`
has SHA256 `890fba7b8a8578722854d7b7972f1c01b641db85ddbd06621df1c78b489436ce`.
With only its installation directory on `PYTHONPATH`, the loaded tilted S3
example (`--constant-downward-load-n 0.0002`) completed 60 accepted steps,
zero cutbacks, a −0.000830315 m minimum swept gap within its declared 1 mm
budget, and a 1.11e−14 N maximum residual. This is an installed development
smoke check, not qualification or release.

## Guided dead-load history and cancellation development extension

With `ContactNodalLoadHistory`, the result profile is
`PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_DESCRIPTOR_HISTORY_DEV_V1`.
The complete reduced base load must have `Z.T f_base == 0`, even if the initial
history factor is zero. A tolerance-sized nonzero algebraic component is rejected:
arbitrary finite history amplitudes/slopes could amplify it. For this restricted
profile `G(q,t)=Z.T F_internal(q)` has no explicit time derivative, so the existing
smooth-branch rate reconstruction applies. The original constant-load profile,
its initial force checks and version-1 checkpoints remain unchanged.

History knots split time steps; version-2 restart binds the profile, complete
history, base load and accumulated external work. Work integrates the declared
cubic Hermite path, not a certified continuum trajectory. Event-stage algebraic
kinematics and general C6 acceptance remain open. Run
`python examples/general_contact_s3_plane_impact.py --ramp-downward-load-n 0.0002`.

`solve_transient_contact(..., cancellation_token=token)` admits the exact unmodified
solver `CancellationToken`. It checks safe boundaries before acceptance and raises
`SolveCancelled`, without returning a partial result/checkpoint. Contact scope and
solve-owned pending state trials are cleaned up; completed increments stay
committed. Arbitrary token callbacks/subclasses are rejected. These elastic
development profiles do not establish plastic-history transaction acceptance.

## Right directional rate development extension — 1 October 2026

Set `ContactTransientSolverControls(allow_s3_descriptor_dev=True,
s3_one_sided_rates_dev=True)` to select
`PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_DIRECTIONAL_RATES_DEV_V1`, or
`PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_DIRECTIONAL_HISTORY_DEV_V1` with a scalar
history. Defaults, original profiles and their restart identities are unchanged.
Directional checkpoints bind this control and reject continuation under the
original rate rule. The exact-zero algebraic history-load restriction still applies.

At affine penalty touch, velocity solves the right derivative of the actual
algebraic force. Its active set uses the complete physical-plus-algebraic gap
rate. Acceleration uses the closed branch for closing velocity, the open branch
for opening velocity, and a directional solve at stationary touch, including
structural curvature. The certified physical mass projection is preserved;
massless rotations receive no inertia. They satisfy the algebraic derivative
equations rather than full-coordinate Newmark kinematics across a rate jump.

Touch/stationary ties use a 64-machine-epsilon arithmetic operand budget. This
represents floating-point uncertainty; it is separate from the dimensional gap
tolerance and is not an exact derivative claim for every small nonzero gap.
The finite active-set iteration reports singularity, cycling or exhausted limits
as explicit failure. It does not guarantee convergence or uniqueness in general.

Independent scalar/multiple-constraint oracles, manufactured curved structural
force, physical Newmark checks, tilted active-contact split restart, history
eligibility and injected-failure cleanup are development evidence. Restart parity
uses the identical accepted time partition; a separately rounded end time can
produce a different last step. Historical failures retain their original meaning.
Event timing, incoming/outgoing interval traces and conservative integrated-path
control remain open. Cubic Hermite reconstruction is a declared path only.
This extension is implemented/tested/reviewed development, not C6 acceptance.

Run `python examples/general_contact_s3_plane_impact.py --one-sided-rates`;
combine with `--ramp-downward-load-n 0.0002` for the history extension.
See [results](d1_review_support/contact_c6_directional_rates_20261001/results.md).
