# Fixed-plane Q4 impact development profile

`solve_transient_contact` provides a narrow opt-in C6 development slice. It
combines the existing nonlinear shell residual with the planar-Q4 penalty
contact owner in an implicit average-acceleration Newmark step. The currently
admitted model contains only qualified planar E4-PL Q4 shell elements with
isotropic elastic materials, one declared physical shell skin and one fixed
rigid plane. The reduced mass must be positive definite. Constraints must be
fixed at zero, and the initial velocity must satisfy them.

The caller supplies a pressure-law normal stiffness and dimensional gap
tolerance in `ContactInteraction`, plus `dt`, `t_end`, initial structural
velocity and bounded Newton/cutback controls in `TransientContactSettings`.
The result stores accepted displacement, velocity, acceleration, contact
reaction, endpoint gap, swept gap, equilibrium residual and iteration counts.
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
rejected trial. These are local development tests, not registered C6
qualification or independent review.

Prescribed loads, moving tools, free rigid bodies, shell descriptor dynamics,
beam impact, general finite sliding, plasticity, friction, damping, dynamic
restart, work/energy accounting, cancellation and common-stage native
coupling remain outside this profile. Contact result records retain the
static plane kernel identity; the surrounding transient result declares the
distinct Newmark development profile. Full C6 and programme acceptance remain
open.
