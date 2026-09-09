# Native generalized conservative current-rest mass/modal development

Base f3bddbdd58c9799df7a6594b6c1018d5815734c9. This extends the current
NativeGeneralizedStaticElement through a new private spectral entry point;
the existing static element, all beam/shell mechanics and public routes stay
unchanged. Freeze this plan, the new module and its test before formal runs.

## Current-state equation map

Reuse the already declared centered two-cell physical field and the existing
retained generalized potential Pi(q,p;history)=p.k(q)-Psi*(p;history).
There are 24 kinematic coordinates (external 18 plus six cell rotations)
and 18 inertia-free generalized resultants.

For current committed history, independently reevaluate the existing operator
at the accepted geometry and resultants. Require unchanged history and an
elastic-interior response at every station, with the existing 64-epsilon
branch-distance guard evaluated in 80-digit Decimal arithmetic. This is
not the previous increment's plastic algorithmic tangent and not a claimed
general plastic vibration law. Yield-boundary/plastic perturbations fail closed.

Let J=dk/dq, G=sum p_i d2k_i/dq2, and C=d2Psi*/dp2. The retained physical
stiffness is K24=G+J^T C^-1 J minus the conservative distributed-line-work
Hessian. Use a two-sided inverse check for the 18-resultant block.
Retain the spatial connection terms when checking consistency with the
accepted 18-coordinate static Jacobian. Only the conservative Hessian enters
the spectrum; no general follower Jacobian is symmetrized.

Rebuild all element operators from validated states without registering a
new material store or committing history. Shared physical nodal rotations,
global displacement, complete section inertia maps, distributed load identity,
support selection and actual nodal spatial dead forces are bound. Require
assembled free equilibrium before interpreting signed roots as current-rest
squared frequencies. Nonconservative distributed couples, nodal moments,
MPC/activity/point masses and partial rotational support contracts remain
explicitly unsupported in this development entry.

## Physical mass

Use the existing centered lifted current-rest kinetic map with fixed 24-point
mass integration, independent of the unchanged stiffness quadrature:

v(s)=(1-t)v_left+t v_right + omega_cell cross (U_cell lift(s));
w(s)=omega_cell; material velocity=[Q(s)^T v(s),Q(s)^T w(s)].

Integrate one half of velocity^T section_inertia velocity over reference
arclength. Section inertia is explicit, exactly symmetric and SPD. Retain all
six physical cell-spin inertias. Nodal rotation traces have exactly zero mass;
eliminate their shared assembled algebraic equations only after assembly.
No static/Guyan removal of cell inertia, invented trace mass, clipping,
stiffness floor or eigenvalue shift is allowed.

The signed stationary kernel remains unchanged. This dense development entry
inherits its 256-coordinate bound; it does not establish extreme-slenderness
accuracy, production scale or finite-velocity nonlinear dynamics.

The preserved local equation maps GE_BEAM3_FIBRE_CURRENT_STATE_SPECTRA.md
and GE_BEAM3_CURVED_P5_MASS_DEVELOPMENT.md document the same kinetic field
and the distinction between exact trace elimination and approximate static
cell elimination. They are background infrastructure, not qualification
of the current generalized material adapter.

## Test and run inventories

Local inventory: stress-free straight/curved stiffness-factor comparison,
mass factor and separately coded 64-point velocity-energy integral, six rigid
modes, positive dynamic mass, exact zero trace mass, connected shared-trace
assembly, proper-frame covariance, reversal, actual conservative loaded
state without history mutation, malformed inertia/state/maps/loads/supports,
input mutation, cancellation and unchanged unsupported public mass route.

Engineering inventory: straight fixed-free axial and torsional chains of
1/2/4/8 macros, compared to omega=pi/(2L)*sqrt(rigidity/inertia). Require
monotonic error reduction and <2% finest error. This does not qualify bending
or curved continuum frequencies.

Run one frozen rehearsal per inventory, then two fresh-directory repeats
only if rehearsals pass. Compare complete scientific JSON bytes within each
inventory. Same-author checks are labelled honestly; independent review
remains PENDING. Preserve failures, make no automatic worker retry.

One numerical thread, 24 GiB process tree, 600 seconds per child, 120-second
CPU-inactivity watchdog, <=3 concurrent workers and <=1800-second wave.
Record distinct resource failure reasons and both process/supervisor exits.
Use exclusive outputs and guard the clean frozen implementation/runtime
before and after execution. Full input hashes at capture, element boundaries
and output; inexpensive cancellation/deadline checks in internal response loops.

Success is development-only current-rest mass/modal evidence, not full beam
qualification, plastic dynamics, critical buckling factors or public activation.
Further work includes prestress/buckling and engineering bending/curved spectra,
extreme contrast/slenderness and larger models, broader state/load/material
parity, independent review, installed selectable integration and objective
beam-shell qualification. The full goal is unchanged.
