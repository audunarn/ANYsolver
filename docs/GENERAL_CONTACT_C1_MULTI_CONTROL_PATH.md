# C1 development profile: prescribed multi-control shell contact path

`PLANAR_Q4_S3_MULTI_CONTROL_CONTACT_PATH_DEV_V0` keeps several prescribed
translation coordinates in one frictionless, nonlinear static contact
transaction. The conjugate forces are solved as unknowns. This permits a
planar shell patch to press, slide, open and recontact without leaving a
free rigid translation at separation.

Create a `ContactPathProgram` from two or three `ContactPathControl` rows,
piecewise-linear displacement waypoints and a positive number of steps per
segment. A row may address one translation DOF or be an immutable weighted
sum of translation DOFs. The first waypoint is the reference pose. Call
`solve_static_nonlinear(model, contact=definition, contact_settings=settings,
contact_path_program=program, ...)` with an explicitly selected
restricted-sliding Q4/S3 shell pair. The analysis
uses the existing structural residual, candidate material transactions and
contact manager, then commits only accepted increments. Each accepted step
reports the target, generalized reactions, contact forces and gap check.
An [initially disjoint planar patch](GENERAL_CONTACT_C1_FIRST_APPROACH.md)
can enter overlap during the prescribed path.

The program and contact definitions bind a version-2 checkpoint. A run
stopped at a registered step fraction can resume the same path; changing a
waypoint fails checkpoint validation before stiffness assembly. A failed
increment restores the last accepted coordinates and material state. The
profile has a 10,000-step resource cap.

The current admission is planar Q4/S3, von Karman kinematics, elastic
isotropic materials, fixed actual rotations, one tangential translation per
patch, frictionless penalty contact and two or three translational control
rows. The separately selected [augmented path](GENERAL_CONTACT_C1_AUGMENTED_PATH.md)
uses the same restricted geometry. There is no adaptive path-step cutback,
arbitrary callback motion, friction, warped Q4, physical shell rotation or
dynamic response. The public `solve_static_nonlinear` entry point dispatches this
explicit path to its dedicated owner; unrelated historical controls retain
their route. The numerical path is locally tested, not independently accepted.

`examples/general_contact_mixed_path.py` demonstrates Q4 against two S3
V2D faces. The upper patch is pressed to a −0.5 µm average normal motion,
slid 0.1 m, opened to a +1 µm gap and recontacted. Four pressure DOFs are
active while closed; none are active when open. The final overlap is
0.81 m². A midpoint checkpoint resumes to the same final displacement, and
a changed path is rejected. Focused checks are in
`tests/test_general_contact_patch_sliding.py`. This is a local development
case, not the full C1 engineering handoff or a release claim.

The separately selected `--augmented-cycle` uses one corner normal control
and the projected augmented law across those same four phases. It releases
the multiplier at opening and resumes from an open-phase checkpoint. See
[augmented path limits](GENERAL_CONTACT_C1_AUGMENTED_PATH.md).
