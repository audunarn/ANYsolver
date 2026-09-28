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
development slice reports cumulative constant-nodal-load work in joules as
`external_nodal_work_j = F_nodal · (u - u_initial)` at each saved state. The
work is measured from the configured initial pose, including after restart.

An optional immutable `ContactNodalLoadHistory` now scales that same dead
nodal `LoadCase` by a piecewise-linear time history. Its points start at zero,
have strictly increasing physical times and cover `t_end`; the driver splits
steps at history knots. Adjacent knots below the declared minimum step or
floating time resolution are rejected before solving; a residual sub-minimum
knot step also fails explicitly. The load at zero enters initial acceleration, and
the load at each candidate's end time enters its Newmark residual. At each accepted step, reported
external work is the exact integral of the linear load over the declared
cubic Hermite displacement path, evaluated by two-point Gauss quadrature.
This is discrete path work, not an exact continuum-energy claim. Rejected
trials add no work. A history-enabled version-2 checkpoint binds the history
and stores cumulative work; version-1 constant-load checkpoints retain their
original contract. Restart at a history knot reproduces the uninterrupted
path; changed history or work tampering is rejected. This route remains Q4
fixed-plane development only and does not admit a moving tool, follower load
or S3 descriptor load.
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
exercise the bounded constant-nodal-load branch; add
`--ramp-duration-s 0.012` to ramp that load from zero.

At each candidate, the coupled residual is
`M a + F_structural + F_contact - F_nodal`, with `F_nodal = 0` in the
historical unloaded case.
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
same-load restart and changed-load rejection. The free-motion check compares
reported work with analytical force times displacement and kinetic-energy
change; the impact check verifies work at an active-contact state. The
complete focused transient file passed 19/19 before the work-field addition.
The full file also passed 19/19 after it (21.46 s, source environment).
Independent read-only review found no concrete defect in load sign,
projection, initial/resumed balance, restart binding or rollback ownership.
The tests directly check initial/resumed acceleration and changed load name
and vector. A subsequent focused check forced a loaded Q4 trial to fail under
one Newton iteration and no cutbacks, then reused the same model and load for
a successful solve; displacement, velocity, acceleration and cumulative work
matched a fresh model to 1e−12. A nontrivial reduced projection remains
untested. This check is local development evidence, not C6 qualification.
The history checks compare a free guided ramp with independently integrated
acceleration and energy, verify work-error improvement under time refinement,
split and resume at an internal load knot, reject a changed history and
tampered work checkpoint, and compare an active-contact ramp with an
independent forced-oscillator solution. The first coarse work check failed a
2% tolerance by 0.13 percentage points; the check now records its actual
2.13% defect and requires improvement on a finer step. This historical
development failure is retained in the task record; no impact-energy
acceptance is inferred from the revised local check. Independent read-only
review found that the first knot search could skip an arbitrarily close
allowed knot, invalidating the exact-work claim across it. The search and
admission were corrected, and a near-coincident-knot rejection test passes.
The same reviewer rechecked the correction and found no remaining crossing
or work inconsistency in this bounded path. The focused transient file passed
24/24 before that final guard; the three affected history/contact tests passed
after it.

An isolated wheel built from source commit `1d8f8ca3` has SHA256
`500137d0ac8c4de0d85b782f9ccff6485015b8cc939d1eec0154ccd13f27f8ca`.
Its installed import resolved under `reports/installed_history_dev/anysolver`,
and the installed example with 0.02 N load and 0.012 s ramp completed 80
steps, reporting 5.92083517e−6 J external nodal work. Build, install and
example logs are retained in `reports/general_contact_c6_history_*_dev_20260928.log`.
The first wheel attempt failed because the default pip cache was inaccessible
in the sandbox; the `--no-cache-dir` retry succeeded. This is a bounded
installed-package development check, not C6 package acceptance.

General time-varying spatial loads, moving tools, free rigid bodies, descriptor dynamics in this Q4 branch,
beam impact, general finite sliding, plasticity, friction, damping, general
dynamic restart, complete work/energy accounting, cancellation and common-stage native
coupling remain outside this profile. Contact result records retain the
static plane kernel identity; the surrounding transient result declares the
distinct Newmark development profile. Full C6 and programme acceptance remain
open.
