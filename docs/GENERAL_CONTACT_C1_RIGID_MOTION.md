# C1 development profile: prescribed radial rigid-tool translation

`RigidContactBody` accepts `path_translation=(dx, dy, dz)` for one analytic
sphere or infinite cylinder. Components are SI metres at continuation factor
one: the rigid point is (c(\lambda)=c_0+\lambda\Delta c). The direction
and speed are constant in factor; no rotation, acceleration or free-body
inertia is implied. The tool's geometry and its path translation are part of
the version-2 restart contract. A zero translation is canonicalized to the
existing fixed-obstacle profile.

The admitted solver route is `solve_static_nonlinear` with force control,
elastic isotropic Q4/S3 V2D shell skins, von Karman kinematics, frictionless
penalty contact, explicit shell side and `pair_motion="general"`. The
structural/contact residual and tangent are evaluated against the tool pose
at the same load factor. Before a trial increment is assembled, a swept check
tests the path from the last accepted shell/tool pose to the trial factor.
The converged increment is checked again using both accepted endpoint poses.
An unresolved crossing or gap over the declared budget triggers the ordinary
load-step cutback. Newton candidates are separately bounded with the tool
held at that factor. Failed trials do not commit tool or material state.

Results give the tool point, paired force and moment, conservative/sampled
gap, search and cutback counters, and a signed contact-work estimate. Rigid
contact work uses a trapezoid over accepted load-factor increments:

\[
W_{\mathrm{rigid}}\approx\sum_k\tfrac12(F_{r,k}+F_{r,k+1})\cdot
       (c_{k+1}-c_k).
\]

`prescribed_actuator_work_trapezoid` is its negative. Each accepted increment
is retained in the ordinary force/displacement history and therefore in the
checkpoint. A split/restart run reproduces this estimate when it follows the
same accepted factor partition. Different adaptive partitions can give
different trapezoidal estimates even when the final equilibrium is the same;
that difference is numerical work-integration error, not physical
dissipation. No exact energy-conservation claim is made.

`examples/general_contact_moving_sphere.py` drives a 5000 m-radius sphere
10 µm toward a supported Q4 patch using eight force-controlled increments.
Its 20 µm gap budget is (10^{-3}) of the 20 mm shell thickness. The radius
makes this a nearly flat, well-resolved development control; it does not
qualify small, highly curved contact spots. Focused tests cover relative
shell/tool motion, a through-crossing path, a solver cutback before an
invalid pose, moving sphere and cylinder equilibrium, work sign, restart
continuation, and incompatible-motion rejection.
Exploratory 8-, 16- and 32-step versions of this same example gave signed
rigid work of approximately −3.29462, −3.28825 and −3.28507 ×10⁻⁸ J.
This measured partition dependence motivates a work-integration tolerance
and path refinement before engineering acceptance.

Prescribed plane motion, displacement-control and arc-length tool motion,
piecewise or rotational tool paths, free rigid-body dynamics, friction,
finite cylinder caps and engineering work/penetration qualification remain
open. The swept certificate covers the linear interpolant of each accepted
increment and the actual fixed-tool Newton trial paths; further event and
path-refinement evidence is required for broader finite sliding.
