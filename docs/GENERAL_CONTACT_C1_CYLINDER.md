# C1 development profile: fixed infinite cylinder against Q4/S3 shells

`Q4_S3_FIXED_INFINITE_CYLINDER_PENALTY_MORTAR_STATIC_DEV_V0` admits one
fixed analytic infinite cylinder against an explicitly selected Q4 or S3 V2D
top or bottom shell skin. The public definition is
`RigidContactBody(name, "cylinder", point=axis_point, normal=axis_direction,
radius=radius)`. The axis direction is normalized. Its sign and the choice of
point along the same axis do not change the physical cylinder. The rigid body
is prescribed and has no structural or inertial coordinates.

For unit axis (a), axis point (c), and physical shell point (x), let
(P=I-aa^T), (r=P(x-c)), and (d=\|r\|). The separation-positive gap is
(g=d-R). Where (d>0), its position gradient is (n=r/d) and Hessian is
((P-nn^T)/d). The shell residual and tangent use the same physical
position/virtual-work map and primal nodal pressure normalization as the
fixed-sphere profile. The analytic curvature term is included in the smooth
branch tangent. Q4 and S3 use their admitted physical director and offset.
Drill changes that leave the physical skin unchanged create no contact work.

The represented physical gap is bounded in the radial projection of each
bilinear Q4 or linear S3 parametric cell. The swept check includes the full
linear trial path and cuts back through-crossing attempts. Current and swept
shell orientation, shell tilt (explicit limit at most 0.1 rad), physical side,
initial penetration and finite geometry budgets retain the sphere profile's
fail-closed controls. Cylinder-axis points have undefined radial normals and
are rejected. The infinite cylinder has no end caps or endpoint reactions.

The profile admits elastic isotropic material, small-rotation von Karman
nonlinear static force or displacement control, frictionless penalty normal
enforcement and version-2 restart. The restart contract binds the cylinder
axis, radius and point. `examples/general_contact_cylinder.py` is a
force-controlled installed-package smoke example with an explicitly loose
4 mm development gap budget. Focused Q4/S3 checks cover virtual work,
directional tangent, axis invariance, balanced wrenches, physical offsets,
side rejection, swept crossing and split/restart.

This fixed profile does not admit finite cylinder caps; a separate linear
[prescribed translation profile](GENERAL_CONTACT_C1_RIGID_MOTION.md) is
available for force control. This fixed profile does not admit
free rigid-body motion, friction, augmentation, warped Q4, finite shell
rotation, automatic pairing or impact. The Q4/S3 pressure space can still
miss a spot smaller than its resolved support; a separate represented-gap
check reports that failure. Local development tests and a package smoke run
do not constitute independent engineering acceptance.
