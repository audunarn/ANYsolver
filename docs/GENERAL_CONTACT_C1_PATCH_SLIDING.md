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
An additional Q4 integration/two-S3 target case completed coupled pressing
at 0.4 N, a 0.1 m lateral path across the S3 patch and split/restart. A
separate normal-displacement path pressed, opened and recontacted the same
Q4/S3 pair through three checkpoint continuations. The opened state had no
active pressure and a positive certified gap; the recontact force matched
the initial closed state. These are separate local paths, not yet one
combined slide–separate–recontact qualification case. Two S3 integration
faces share four pressure nodes and passed a local physical force/rank check.
Their full and partial-overlap coupled uniform-pressure cases then completed
with independently integrated nodal loads. An earlier uneven-load
exploratory solve was interrupted after exceeding its bounded check time;
its convergence remains unresolved.

This profile has no general in-plane shell deformation or rotation, warped
Q4, exact coincident-edge transition derivative, augmentation, friction,
self-contact, initial disjoint-patch event activation or dynamic response.
Q4/S3 mixed partial-contact and pressure-space stability remain unresolved.
Uniform-pressure checks do not establish pressure-space stability under
partial activation.

One exploratory partial-contact resolution sequence holds the Q4/S3 geometry
and total 0.4 N load fixed while refining the Q4 integration patch. At
1 MPa/m with the declared 10 µm gap budget, one Q4 face stopped at 50% load
and a 2×2 Q4 patch reached 62.5%. With a relaxed 1 mm diagnostic budget,
the full-load conservative gaps were about −15.17 µm for 2×2 and −13.38 µm
for 4×4. A 4×4 patch at 4 MPa/m completed full load under the original
10 µm budget with a −7.92 µm conservative lower bound and balanced ±0.4 N
normal forces. The latter is a focused local regression, not a frozen
qualification case; the relaxed runs are diagnostics. Mesh, enforcement and
integration convergence remain to be established separately.

The full nonmatching slide, separation and recontact handoff and the main
plan's refinement, independent-review and package gates remain open.

Focused checks are in `tests/test_general_contact_patch_mortar.py`,
`tests/test_general_contact_pair.py` and
`tests/test_general_contact_patch_sliding.py`. Run
`examples/general_contact_patch_sliding.py` for Q4/Q4 or
`examples/general_contact_mixed_patch_sliding.py` for Q4/S3 lateral motion.
