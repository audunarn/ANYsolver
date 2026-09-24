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
Lateral overlap work is integrated over physical faces and distributed to
their material nodes; the patch-wide translation resultant is preserved.
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

The result also reports the smallest and largest positive nodal pressure
support areas, the supported gap-gradient condition estimate, the most
negative normalized weighted gap, the largest *algorithmic* nodal pressure,
and the span from weighted to independently bounded physical gap. These are
resolution diagnostics, not physical shell stress or an automatic stability
pass. A rank-deficient or empty supported gradient reports no condition
estimate. Local small-cut modes can carry pressure even when an integrated
reaction balances; a small reaction residual alone does not resolve the
physical gap.

`pressure_gradient_condition` uses **all supported rows of the unscaled gap
gradient**. It is not the condition number of the active contact tangent.
At one fixed affine opening pose, this field grew from 372 at 4×4 to 40,254
at 6×6 and 69,675 at 10×10, while the active gradient scaled by the square
root of each support had conditions 10, 15 and 28. Use the former as a
small-cut warning, not by itself as proof that the equilibrium linear system
needs a new preconditioner.

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

An independent fixed-pose oracle clips the known triangular Q4/S3 overlap
by an affine opening gap and integrates pointwise penalty force and first
moments exactly. With 4 MPa/m regularization, Q4-pressure mortar force error
fell from 8.64% at 4×4 to 5.80% at 6×6, 2.32% at 10×10 and 1.33% at 12×12;
the 12×12 first-moment errors were below 2%. This is a focused local
resolution check in
`tests/test_general_contact_patch_pressure_resolution.py`, not a coupled
mesh-convergence or engineering-acceptance claim. Putting pressure on the
coarse S3 side reduced the raw condition but increased the force error to
13.6% on the 6×6 opening pose. A corresponding coupled role-exchange solve
was stopped after a bounded run without a mechanics result; it is not counted
as a failure of the pressure law.

On a separate 12×12 Q4-integration coupled partial-contact case, the solver
completed at 0.4 N in 551 seconds with a −8.615 µm independent lower gap
under the unchanged 10 µm budget. The gap and integrated first moment moved
toward a stable value across 6×6, 10×10 and 12×12, but contact potential was
nonmonotone. This is a development trend, not coupled response convergence.
At the fixed opening pose, refining the S3 pressure side to 16 subdivisions
per edge lowered its force and first-moment errors against the same oracle
to about 0.95%; its response and the 12×12 Q4-pressure response differed by
less than 2%. The role check is local and uses explicit diagnostic resource
caps. Coupled role exchange and independent acceptance remain open.

At one accepted coupled 4×4 Q4 bottom-skin/S3 top-skin pose under 0.4 N,
an independent 16×16 tensor-Gauss integration of each analytically clipped
triangle/square cell found 0.28125 m² overlap. It did not call the production
overlap or mortar integration routines. Normalized maximum differences were
2.22×10⁻¹⁶ for nodal support, 4.49×10⁻¹⁵ for weighted gap (scaled by
area×10 µm), 2.22×10⁻¹⁶ for the gap gradient, 3.43×10⁻¹⁴ for nodal normal
force (scaled by 0.4 N), and 1.06×10⁻¹⁴ for integrated moments (scaled by
0.4 N·m). Contact-potential relative difference was 7.09×10⁻¹⁶. A 12×12
oracle agreed with the 16×16 oracle. The force and moment integration
differences meet the registered 0.2% local budget. The focused test and raw
output are `tests/test_general_contact_patch_refinement.py` and
`C:\ANYworkspaceWork\general-contact-evidence\c1-accepted-pose-integration-oracle-final.txt`.
This is a single preserved-pose integration check; it does not establish
coupled response convergence or integration accuracy at other geometries.

At the same 4×4 model, a second check reconstructed the 0.4 N external
nodal loading from the source-square face weights. It assembled the existing
shell structural force and tangent, but solved the free normal coordinates
with contact force and Jacobian from the independent clipped-cell integrator.
Starting 5% away from the ordinary solver pose, the separate equilibrium
solve converged in two iterations: maximum force residual was
2.02×10⁻¹¹ relative to 0.4 N and maximum normal-displacement difference
was 9.13×10⁻¹¹ relative. The raw record is
`C:\ANYworkspaceWork\general-contact-evidence\c1-independent-coupled-response1.txt`.
This cross-check uses the same structural idealization and one mesh. It does
not establish structural mesh convergence, pressure-space stability or
enforcement convergence.

At that fixed 4×4 geometry and 0.4 N load, explicitly increasing the
penalty stiffness from 4 to 8 to 16 MPa/m improved the independently
certified lower gap from −7.916 to −7.085 to −6.173 µm. Mean source
normal displacement changed from −24.964 to −23.805 to −22.730 µm.
Integrated normal reactions remained ±0.4 N and all three states met the
unchanged 10 µm gap budget. Penalty storage was nonmonotone:
3.733, 3.145 and 3.385×10⁻⁷ J. The two added solves and the original pose
are recorded in `c1-fixed-mesh-enforcement-final.txt` in the evidence
directory. This is a bounded fixed-mesh enforcement sensitivity, not a
universal stiffness prescription or evidence of asymptotic convergence.

The full nonmatching slide, separation and recontact handoff and the main
plan's refinement, independent-review and package gates remain open.

## Projected patch search

The restricted planar patch profiles now use a deterministic two-dimensional
AABB tree on the target's physical reference faces. Candidate queries move
the source footprint by the current relative tangential translation. The
same candidates feed mortar or pointwise integration, independent gap
certification, and the mortar lateral-force transport. Polygon overlap still
decides whether contact exists. The reported `candidate_pairs` counts AABB
pairs processed at the current pose; `overlapping_pairs` counts pairs with
positive projected polygon overlap. An actual candidate limit fails without
discarding pairs. The patch's normal-coordinate limit remains separate.

Exhaustive small-scene comparisons covered translated grids and a rotated
contact plane. The affected 36-test patch suite passed on this source in
`C:\ANYworkspaceWork\general-contact-evidence\c1-patch-broadphase-affected1.txt`.
One search-only sparse-box measurement at 10³/10⁴/10⁵ features observed
tree builds of 0.0059/0.0902/0.9591 s and 1,000 local queries of
0.1015/0.1248/0.1449 s. The process RSS snapshots increased by roughly
0.14/2.50/18.75 MB during those builds. Raw inputs and measurements are
`benchmark_patch_broadphase.py` and `c1-patch-broadphase-search-only1.json`
in the evidence directory. These are search-kernel measurements for sparse
scenes, not complete solver timing, peak-memory, dense-contact, or general
complexity evidence.

## Separate pointwise penalty verification route

Set `normal_discretization="pointwise_penalty"` in `ContactSolverSettings`
to select the distinct
`PLANAR_Q4_S3_PATCH_RESTRICTED_SLIDING_POINTWISE_PENALTY_DEV_V0`
profile. This route is admitted only for a multi-face restricted planar Q4/S3
shell pair with the penalty normal law. It integrates the negative physical
gap point by point on the current common refinement. It has no mortar
pressure basis or pressure-rank result; those fields are null in its output.
The primal-pressure mortar remains the default.

`pointwise_integration_subdivisions` controls triangle subdivision and
`maximum_pointwise_triangles` is a hard resource limit. The result reports
the number of integration triangles and quadrature-estimated active area.
The physical gap still uses the separate conservative certificate. The
translation force includes moving-overlap boundary work and is distributed
to physical face nodes. The mapped tangent is checked on smooth branches.
Projected-boundary transitions must be subdivided along the load path.

In one exploratory 6×6 Q4/S3 partial-contact comparison at 0.4 N and
4 MPa/m, the certified physical lower gap improved from −9.620 µm with
the default mortar law to −7.355 µm with the pointwise law. Depth-two to
depth-three quadrature changed accepted-pose energy by 2.02×10⁻⁶ relative
and normal reaction by 6.63×10⁻⁵ relative. This is a development comparison,
not pressure-space acceptance or a mesh-convergence result. An initial
patch-wide distribution of lateral force failed the registered wrench
target. Both patch laws now distribute lateral overlap work at physical
face nodes and include shell-offset rotation couples. Rechecking the saved
pointwise pose gave a normalized net moment of 2.21×10⁻⁹; re-solving the
same 6×6 mortar case retained its −9.620 µm gap and balanced the integrated
body moments to about 9.2×10⁻¹¹ N·m in x/y and roundoff in z. These
development checks resolve that measured wrench defect. Partial-contact
pressure stability, broader geometry and independent acceptance remain open.

Focused checks are in `tests/test_general_contact_patch_mortar.py`,
`tests/test_general_contact_pair.py` and
`tests/test_general_contact_patch_sliding.py`. Run
`examples/general_contact_patch_sliding.py` for Q4/Q4 or
`examples/general_contact_mixed_patch_sliding.py` for Q4/S3 lateral motion.
