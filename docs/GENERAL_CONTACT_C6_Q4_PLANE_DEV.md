# Fixed-plane Q4 impact development profile

This page describes the Q4 branch of `solve_transient_contact`; the separate
[guided S3 V2D descriptor branch](GENERAL_CONTACT_C6_S3_DESCRIPTOR_DEV.md)
has its own admission and evidence. The Q4 branch is a narrow opt-in C6 development slice. It
combines the existing nonlinear shell residual with the planar-Q4 penalty
contact owner in an implicit average-acceleration Newmark step. The currently
admitted model contains only qualified planar E4-PL Q4 shell elements with
isotropic elastic materials, one declared physical shell skin and one fixed
rigid plane. The reduced mass must be positive definite. Constraints must be
fixed at zero, and the initial velocity must satisfy them.

The caller supplies pressure-law normal stiffness and dimensional gap tolerance
in `ContactInteraction`. The ordinary `TransientConfig` now owns `dt`, `t_end`,
initial displacement and velocity, and `save_every`. Optional
`ContactTransientSolverControls` owns Newton and cutback limits. The former
`TransientContactSettings` remains a thin compatibility adapter for existing
development callers. Only undamped average-acceleration Newmark is admitted;
unsupported integration, selected recovery and resource options fail explicitly.
The optional `base_load_case` admits one time-independent `LoadCase` containing
nodal forces and moments only in this Q4 branch. Gravity, element/pressure or
follower loads, added nodal mass and loads in the S3 descriptor branch fail
explicitly. The reduced dynamic residual is
`M a + F_structural + F_contact - F_nodal`; the same assembled load enters
initial acceleration and restart balance. A contact checkpoint binds its load
name and generalized vector, so changing either rejects continuation. This
development slice does not yet report external work or admit varying loads.
The result stores sampled displacement, velocity, acceleration, contact reaction
and endpoint gap. Its swept-gap and equilibrium-residual entries bound every
accepted step since the preceding saved sample; iteration counts cover every
accepted step. Event checks and committed state always advance at every step,
including steps omitted from output by `save_every`.
An opt-in development checkpoint is available with `save_every=1`:
`emit_restart_checkpoint=True` returns a JSON-serializable
`restart_checkpoint`, which a fresh compatible solve accepts through its
`restart_checkpoint` argument with a later `t_end`. It binds the model,
contact definitions, integration settings, initial state and nonlinear
controls, and verifies an integrity hash and resumed acceleration balance.
The original configured initial pose is still checked for unresolved
penetration; the saved active-contact pose is checked against its accepted
gap budget.
Export requires at least one accepted step and a final step that was not
shortened merely to reach `t_end`; an off-grid split is rejected because it
would change the uninterrupted Newmark path.
The resumed result begins at the checkpoint time; concatenate it with the
first result after omitting that duplicate state. A focused split during
active contact matched the uninterrupted Newmark path within declared
floating-point tolerance. Sparse-output restart remains unadmitted.
Run `python examples/general_contact_q4_plane_impact.py` from an installed
package or a source environment. Add `--constant-downward-load-n 0.02` to
exercise the bounded constant-nodal-load branch.

At each candidate, the coupled residual is `M a + F_structural + F_contact`.
Its tangent includes the Newmark mass term and the structural/contact tangent.
Material trials originate from the last accepted step and are committed only
after equilibrium and gap checks. The event check minimizes each physical Q4
corner gap over the cubic Hermite path defined by the Newmark endpoint
positions and velocities. For a planar Q4 against a fixed plane, the skin gap
is bilinear over a face, so its spatial minimum occurs at a corner along this
declared interpolation path. Unresolved trials halve the time step or fail
with the last accepted state retained.

The uniform guided-plate test compares the response with an independently
derived one-coordinate mass–spring impact solution. It also checks an
interior path crossing with open endpoints and reuses the model after a
rejected trial. Configuration tests cover nonzero admissible initial
displacement, sparse output with conserved event diagnostics, and explicit
rejection of unsupported settings. Active-contact split restart, tampering,
changed time-step/contact-definition and off-grid export rejection are also covered. These are local
development tests, not
registered C6 qualification or independent review.
The constant-nodal-load checks also compare free guided motion and loaded
impact with independent one-coordinate mass–spring solutions, and test
same-load restart and changed-load rejection. The complete focused transient
file passed 19/19 after this addition.
Independent read-only review found no concrete defect in load sign,
projection, initial/resumed balance, restart binding or rollback ownership.
The tests directly check initial/resumed acceleration and changed load name
and vector. A nontrivial reduced projection and a loaded rejected step remain
untested; neither is claimed as separately qualified here.

General prescribed or varying loads, moving tools, free rigid bodies, descriptor dynamics in this Q4 branch,
beam impact, general finite sliding, plasticity, friction, damping, general
dynamic restart, work/energy accounting, cancellation and common-stage native
coupling remain outside this profile. Contact result records retain the
static plane kernel identity; the surrounding transient result declares the
distinct Newmark development profile. Full C6 and programme acceptance remain
open.
