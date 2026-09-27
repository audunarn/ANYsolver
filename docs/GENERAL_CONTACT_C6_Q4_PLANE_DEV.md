# Fixed-plane Q4 impact development profile

`solve_transient_contact` provides a narrow opt-in C6 development slice. It
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
The result stores sampled displacement, velocity, acceleration, contact reaction
and endpoint gap. Its swept-gap and equilibrium-residual entries bound every
accepted step since the preceding saved sample; iteration counts cover every
accepted step. Event checks and committed state always advance at every step,
including steps omitted from output by `save_every`.
Run `python examples/general_contact_q4_plane_impact.py` from an installed
package or a source environment.

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
rejection of unsupported settings. These are local development tests, not
registered C6 qualification or independent review.

Prescribed loads, moving tools, free rigid bodies, shell descriptor dynamics,
beam impact, general finite sliding, plasticity, friction, damping, dynamic
restart, work/energy accounting, cancellation and common-stage native
coupling remain outside this profile. Contact result records retain the
static plane kernel identity; the surrounding transient result declares the
distinct Newmark development profile. Full C6 and programme acceptance remain
open.
