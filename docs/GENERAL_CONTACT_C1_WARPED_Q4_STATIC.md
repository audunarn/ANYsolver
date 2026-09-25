# C1 development profile: warped Q4 against a rigid plane

The opt-in `WARPED_Q4_RIGID_PLANE_SMALL_ROTATION_PENALTY_MORTAR_STATIC_DEV_V0`
profile assembles one qualified Q4 face against one analytic rigid plane through
`solve_static_nonlinear`. It uses von Karman small-rotation coordinates, the
qualified varying-frame physical director, Q1 primal pressure support and a
penalty normal law. Both top and bottom skins use structural half-thickness
offsets. A fixed-normal translating plane is admitted. Restart binds the
contact definition and declared numerical settings.

Set `ContactSolverSettings(warped_q4_plane=True, ...)`, provide all six
`warped_q4_*` quadrature and gap controls explicitly, and declare a
`maximum_shell_tilt` in radians for the represented small-rotation path. The runnable
`examples/general_contact_warped_q4_plane.py` shows the full call. Other
geometry and kinematic combinations fail validation. Ordinary contact settings
continue to reject warped Q4 faces.

The local law evaluates weighted gaps using the reference physical-skin area.
The independent gap result is a conservative lower bound over the represented
current physical skin. Its `minimum_gap` is that bound; the separately reported
`independent_gap_sample`, `independent_gap_cells` and
`independent_gap_accuracy` explain its quality. The integration report gives
the low/control quadrature discrepancy. Both trial and prescribed-tool paths
use gap certificates for affine small-rotation increments. Incomplete
certification stops with a resource failure; no candidate is dropped.

The focused coupled example uses a deliberately mild warped face. At 1 N
downward load it reports an approximately 1.296 N upward contact reaction and
a 2.655 mm conservative lower gap against a declared 3 mm **development**
budget. That budget is far above the programme's prospective 0.08 mm
thickness-scaled benchmark for this 80 mm shell. A 1 mm budget stopped at
about 9.8% of the load path because physical corner penetration occurred
before the averaged pressure gap closed. That failure is retained as
`c1-warped-q4-static-local2.txt`; it is evidence that the one-face pressure
resolution cannot certify this partial-contact case at 1 mm.

This profile is implemented and locally tested, not independently accepted.
The next mechanics gate is partial-contact pressure-space resolution and
physical-gap convergence under mesh and enforcement refinement. Finite
rotations, deformable paired warped faces, friction and broader C1
qualification remain open. No acceptance claim follows from a completed
solver status under a development gap budget.
