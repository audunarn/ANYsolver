# C1 development profiles: prescribed analytic rigid-tool translation

`RigidContactBody` accepts `path_translation=(dx, dy, dz)` for one analytic
sphere, infinite cylinder or plane. Components are SI metres at path factor
one: the rigid point is \(c(s)=c_0+s\Delta c\). The direction
and speed are constant in the path factor; no rotation, acceleration or free-body
inertia is implied. The tool's geometry and its path translation are part of
the version-2 restart contract. A zero translation is canonicalized to the
existing fixed-obstacle profile.

The admitted solver route is `solve_static_nonlinear` with force or prescribed
displacement control, elastic isotropic Q4/S3 V2D shell skins, von Karman kinematics, frictionless
penalty contact and explicit shell side. Sphere/cylinder use
`pair_motion="general"`; the planar profile uses `pair_motion="guided"`. The
structural/contact residual and tangent are evaluated against the tool pose
at the same path factor. Under force control, \(s\) is the load factor. Under
displacement control, \(s\) is the commanded control displacement divided by
its final nonzero target. The tool stays at the commanded pose while the
augmented structural/load-factor system equilibrates; the solved load factor
does not drive tool motion. Before a trial increment is assembled, a swept check
tests the path from the last accepted shell/tool pose to the trial factor.
The converged increment is checked again using both accepted endpoint poses.
An unresolved crossing or gap over the declared budget triggers the ordinary
load-step cutback under force control. Displacement control uses fixed
commanded steps and stops explicitly if a sweep cannot be certified. Newton
candidates are separately bounded with the tool held at that factor. For the
plane, the physical Q4/S3 nodal gap is affine in both shell pose and plane
point, so its endpoint corner check bounds the
full linear accepted path. Failed trials do not commit tool or material state.

Results give the tool point, paired force and moment, conservative/sampled
gap, search and cutback counters, and a signed contact-work estimate. Rigid
contact work uses a trapezoid over accepted path increments:

\[
W_{\mathrm{rigid}}\approx\sum_k\tfrac12(F_{r,k}+F_{r,k+1})\cdot
       (c_{k+1}-c_k).
\]

`prescribed_actuator_work_trapezoid` is its negative. Each accepted increment
is retained in the ordinary force/displacement history and therefore in the
checkpoint. A force-controlled split/restart run reproduces this estimate
when it follows the same accepted factor partition. Different adaptive
partitions can give different trapezoidal estimates even when the final equilibrium is the same;
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

`examples/general_contact_moving_plane.py` drives a plane 10 µm into the
same supported Q4 scale with a 20 µm gap budget. Local controls cover its
Q4/S3 physical gap and force map, coupled Q4 and S3 force paths, work sign,
swept load-step cutback and split/restart.

The displacement-control checks prescribe one Q4 control displacement while
the plane or sphere moves on the same normalized command path. They verify
the coupled equilibrium, final tool pose, gap, work sign, checkpoint identity
and rejection of a too-large plane sweep. A completed checkpoint can be
loaded without resetting the final tool pose or accumulated work. Continuation
from an intermediate displacement-control checkpoint has not yet been
demonstrated.

`examples/general_contact_moving_plane_displacement.py` exercises the installed
route at a 20 µm gap budget. The solved proportional load factor can be
negative while the commanded tool path factor reaches one; the two values
are reported separately.

Exploratory 8-, 16- and 32-step versions of the force-controlled sphere
example gave signed rigid work of approximately −3.29462, −3.28825 and
−3.28507 ×10⁻⁸ J.
This measured partition dependence motivates a work-integration tolerance
and path refinement before engineering acceptance.

Arc-length tool motion, piecewise or rotational tool paths, free rigid-body
dynamics, friction, finite cylinder caps and engineering work/penetration qualification remain
open. The swept certificate covers the linear interpolant of each accepted
increment and the actual fixed-tool Newton trial paths; further event and
path-refinement evidence is required for broader finite sliding.
