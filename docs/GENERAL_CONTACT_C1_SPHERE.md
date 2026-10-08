# C1 development profile: fixed analytic sphere against Q4/S3 shells

`Q4_S3_FIXED_SPHERE_PENALTY_MORTAR_STATIC_DEV_V0` adds one fixed analytic
sphere against an explicitly selected Q4 or S3 V2D shell top or bottom skin.
Use `RigidContactBody(kind="sphere", point=center, radius=...)`, a penalty
`ContactInteraction`, and `ContactSolverSettings(pair_motion="general",
maximum_shell_tilt=...)`. The registered tilt limit must be at most 0.1 rad.
This profile uses von Karman small-rotation structural kinematics and elastic
isotropic materials. It rejects unsupported combinations before solving.

For each physical shell quadrature point (x), the sphere gap is
\(g=\|x-c\|-R\). Contact pressure uses one nonnegative first-order nodal
pressure space on the shell and positive reference-support normalization.
The residual differentiates the weighted gap with respect to shell
translations and rotations; its tangent includes the curvature of sphere
distance. Q4 contact uses fourth-order Gauss integration in each parametric
direction, and S3 uses its formulation's surface integration rule. The
physical director, side and S3 reference-surface offset enter the position
and work map. Pure drill motion generates no contact work.

The independent gap check recursively bounds the represented bilinear Q4 or
linear S3 surface using parametric-cell boxes. Swept checks bound the entire
linear trial path, including interior closest approach to the sphere. A
finite cell budget produces an explicit resource failure for a state being
evaluated. During trial-step control, an unresolved path is shortened and
must be certified before it can be accepted. Initial physical
penetration is rejected. Current and swept element orientation are also
checked; a trial whose endpoints are valid but whose shell collapses between
them fails explicitly. The selected physical shell side remains fixed;
an endpoint behind that side is rejected instead of reinterpreting the
sphere's radial normal after a crossing. Result forces and moments are paired between the
shell and prescribed rigid sphere about the global origin.

`examples/general_contact_sphere.py` demonstrates displacement-controlled
pressing, reaction recovery and a version-2 checkpoint. Focused tests cover
Q4/S3 physical geometry, virtual work, smooth tangent, drill invariance,
force/displacement control, restart, initial interference, interior shell
collapse and a through-crossing trial whose endpoints are both open. Results
label the independently bounded gap, sampled gap and pressure-weighted gap
separately, along with candidate-face, pressure-node and gap-cell counts.

`examples/general_contact_sphere_tight_gap.py` is a force-controlled,
well-resolved large-radius sphere case. It registers a 20 µm gap budget,
equal to (10^{-3}) of its 20 mm shell thickness. The independently bounded
gap is reported alongside sampled and weighted gaps. This is a development
benchmark of dimensional gap control, not a curvature or local-pressure
qualification case.

A two-face Q4 check translated the shell under the fixed sphere and observed
the active contact force transfer across the shared face boundary. A smaller
contact spot produced zero nodal pressure despite physical penetration;
with a tighter declared gap tolerance, the independent bound marked that
state unacceptable. This preserves the pressure-space resolution boundary
instead of treating a small solver residual as contact acceptance.
An exploratory 5 m-radius, 0.5 N force-controlled case with a 20 µm budget
reached the adaptive gap-certificate resource limit at the tolerance
boundary. A separate high-stiffness exploration was stopped after excessive
runtime. Neither is an accepted numerical result; both motivate tighter
geometry and pressure-space resolution before admitting small contact spots.
For its 0.2 m Q4 face at zero approach, the nearest 4×4 Gauss point has a
0.23117 mm sphere gap; the quadrature mean gap is 0.66660 mm. These values
come directly from the analytic sphere distance and Gauss coordinates. They
explain why a 20 µm physical gap budget on that coarse face is much smaller
than its pressure-sampling scale. More penalty stiffness cannot resolve a
contact spot that the pressure space has not activated; shell and contact
resolution must be studied separately.
An additional 40 mm square development control holds the physical sphere and
10 µm uniform approach fixed while changing one Q4 face to a 4×4 Q4 mesh.
Both geometries have a negative physical gap inside the 20 µm budget. The
coarse face has zero active pressure coefficients and zero contact force;
the refined mesh has active pressure and nonzero force. This demonstrates
the discrete pressure-resolution boundary without changing penalty stiffness.

This fixed profile does not admit sphere motion; a separate linear
[prescribed translation profile](GENERAL_CONTACT_C1_RIGID_MOTION.md) is
available for force or prescribed displacement control. This fixed profile does not admit a free rigid body, augmented
enforcement, friction, warped Q4, shell finite rotation, impact or automatic
pairing. A sphere contact spot smaller than the pressure/geometry resolution
can be missed by the weighted law; the independent gap check rejects an
accepted state that exceeds the declared dimensional gap tolerance. Mesh,
integration and enforcement refinement remain required for engineering
acceptance. This is local development evidence, not independent acceptance.
