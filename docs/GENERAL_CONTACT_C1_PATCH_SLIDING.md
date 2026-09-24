# General contact C1 development profile: planar patch sliding

The opt-in `PLANAR_Q4_S3_PATCH_RESTRICTED_SLIDING_MORTAR_DEV_V0` profile is
implemented and locally tested. It has **no independent engineering
acceptance** and does not complete C1.

Pass an explicit pair of named planar Q4 or S3 V2D shell surfaces to
`solve_static_nonlinear`, with at least two selected faces on one surface.
Set `ContactSolverSettings(pair_motion="restricted_sliding",
sliding_difference_step=<positive length>)`. Pass the same settings to
`validate_general_contact` to inspect admission. The first named surface is
the integration and pressure side.

The current law uses one globally shared P1/Q1 pressure support on material
nodes of the integration patch. Splitting the target into faces does not add
pressure unknowns. Current projected overlaps are integrated face by face,
then support and weighted gap are accumulated before the frictionless penalty
law is applied. Both patches receive residual and tangent contributions.
Physical top and bottom skins and offset couples use the admitted shell
formulation's conventions. `normal_stiffness` has units Pa/m; `gap_tolerance`
and `sliding_difference_step` are lengths in metres.

This route admits von Karman nonlinear static force and prescribed
displacement control. Structural constraints must enforce one tangential
translation per entire patch, with zero actual shell rotations; nodal normal
displacements may vary. It rejects incompatible candidate motion. The
restricted tangent numerically differentiates the global residual on a smooth
branch and uses a one-sided derivative at an active-set transition. Coincident
projected edges with a non-smooth overlap derivative fail explicitly.

An independent represented-gap check reports the sampled minimum and a
conservative lower bound; planar S3 and exact-parallelogram Q4 use quadratic
extrema, and other planar Q4 shapes use bounded subdivision. A swept path
check limits crossing and may cut back a trial. Initial penetration is
rejected. `maximum_candidate_pairs`, `maximum_patch_normal_dofs` and
`maximum_gap_triangles` impose explicit resource bounds. The dense tangent
and exhaustive face-pair loop are development limitations. Frictionless
penalty contact has no committed contact history; the version-2 restart
contract binds the contact definitions and numerical controls.

The coupled local Q4/two-Q4 target case was pressed to 0.4 N, moved 0.1 m
laterally across the internal target face boundary, and restarted from half
load. Its selected faces have 0.05 m structural thickness, 1 MPa/m normal
regularization and a declared 6 µm development gap budget. The final overlap
was 0.81 m² and the normal forces balanced at ±0.4 N. These are development
checks, not registered qualification results. The earlier 1 µm run stopped
at `contact_gap_exceeded` near 0.301 load factor; that evidence is retained.

This profile has no general in-plane shell deformation or rotation, warped
Q4, exact coincident-edge transition derivative, augmentation, friction,
self-contact, initial disjoint-patch event activation or dynamic response.
Q4/S3 mixed partial-contact and pressure-space stability remain unresolved.
The full nonmatching slide, separation and recontact handoff and the main
plan's refinement, independent-review and package gates remain open.

Focused checks are in `tests/test_general_contact_patch_mortar.py` and
`tests/test_general_contact_pair.py`. Run
`examples/general_contact_patch_sliding.py` for the coupled lateral path.
