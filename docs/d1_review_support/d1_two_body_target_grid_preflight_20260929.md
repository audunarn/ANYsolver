# D1 deformable S3 target-grid route — bounded development preflight

## Decision question

The existing two-S3 deformable target is too coarse to serve as an assumed
spatial reference. Can the current contact route solve generic-position target
meshes with more than two positively overlapped S3 faces, and does the coupled
integrated response begin to settle under separate target x/y refinement?

The [parameterized runner](d1_two_body_refined_target_route.py) keeps the same
physical source/target rectangles, thicknesses, shell sides, S3 offset,
elastic material, source load, two controlled `ux` nodes, target left clamp,
fine nodal Q1 pressure basis and monolithic law. Only the target S3 mesh
changes. Interior target knots are shifted slightly from uniform positions;
the 2×1→2×2→2×4 y and 2×4→4×4 x knot sets are nested. The S3 finite
element spaces need not be nested because each subcell has its own diagonal.
Candidate and integration
triangle *resource ceilings* rise with represented faces; integration/error,
gap, equilibrium and contact settings remain unchanged. The exact-seam
three-face prototype and its rejection guard are untouched.

## Builder control and bounded results

The new one-rectangle/two-S3 builder and the existing standalone example's
original two-S3 builder give **exactly the same** two-step force, gap,
active count and all displacements after the target-node permutation.

| Target cells | S3 faces | Final contact force (N) | Change from prior | Active modes | Solver minimum gap (µm) | Complete route (s) | Sampled RSS (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1×1 original control | 2 | 0.0001700501 | — | 1 | −2.333 | 8.70 | 275.00 |
| 1×1 new builder | 2 | 0.0001700501 | 0% | 1 | −2.333 | 8.85 | 275.48 |
| 2×1 | 4 | 0.0002677037 | +57.43% | 2 | −10.322 | 9.33 | 280.51 |
| 2×2 | 8 | 0.0003887202 | +45.21% | 3 | −10.486 | 14.05 | 299.32 |
| 2×4 | 16 | 0.0004552098 | +17.10% | 2 | −11.596 | 22.04 | 340.93 |
| 4×4 | 32 | 0.0004282033 | −5.93% | 2 | −26.730 | 27.22 | 386.99 |

Every route completed two accepted increments within the existing 180-second
and 1-GB development caps. Independent read-only review found no builder
defect but noted that the initial 1×1/2×1 runs predated an added control mode
in the runner. Both were replayed once with the final runner hash: their
forces and complete displacement vectors are exactly unchanged. All six rows
above now share that final runner hash. The more refined target meshes run through the
ordinary monolithic static solver without entering the guarded exact seam-tie
case. This establishes a practical route for a later two-body mesh comparison.

The force is **not** within the retained 2% representative-response target
between any adjacent comparison shown here. The changing active modes and
minimum gap show that this is a coupled contact-path response, not an isolated
target stiffness measurement. The minimum gaps above are solver reports;
independent physical-gap and integration-error checks were not run for these
new meshes. The sampled timings have different represented mesh sizes and do
not measure a solver speedup.

## Saved-pose independent geometry discriminator

At the accepted 4-Q4/32-S3 final pose, the [bounded saved-pose probe](d1_two_body_multiface_saved_pose.py)
reconstructed the same model and integrated current-skin overlap with the
existing independent clipping quadrature. Positive-area target overlaps per
source Q4 were **16, 8, 15 and 15**, for 54 pairs total. This confirms actual
multi-face overlap, rather than inferring it from selected topology.
Production versus independent reference support differs by 5.72e−14 relative
L2, pressure Gram by 2.03e−13 relative Frobenius, normalized gap by at most
6.96e−13 m, and total reference area by 1.48e−14 m². The probe completed in
3.29 s at 158.73 MB sampled process-tree RSS under the existing 180 s/1 GB
cap. The captured [raw output](d1_target_grid_multiface_log_20260929.txt) and
[resource record](d1_target_grid_multiface_resource_20260929.json) bind the
saved-pose hash, probe hash and imported source module.

This resolves the narrow concern that the observed target-grid response shifts
are caused by a disagreement in smooth-pose overlap, support or pressure Gram
at the saved 32-S3 state. It does not establish independent physical-gap or
integration-error bounds throughout the path, smooth derivatives, mesh
convergence or acceptance. The exact zero-area three-face seam guard is a
different branch and remains in force.
Read-only independent review found no concrete defect in the pose binding,
offline quadrature or scoped interpretation. The smallest counted overlap is
3.85e−5 m²; the positive pair areas sum to the offline projected area. The
count uses the same offline clipper as the quadrature, so it is independent of
production geometry but not a second independent clipping implementation.

## Both accepted press poses: independent dimensional gap and quadrature

The same 4×4 target case was rerun once with accepted displacement snapshots.
Final displacement coordinates and integrated contact force are **bitwise
identical** to the earlier record. Its complete route took 27.56 s with
362.59 MB sampled process-tree RSS under the unchanged 180 s/1 GB caps.
The [snapshot record](d1_target_grid_4x4_path_gap_20260929.json),
[resource record](d1_target_grid_4x4_path_gap_resource_20260929.json) and
[captured log](d1_target_grid_4x4_path_gap_log_20260929.txt) bind source
`366f69f9` and runner hash
`2c4a6621ba506fb81500a3ede4984d2c78bf3a3d64184c60cc44e0c3dacfea83`.

| Accepted press step | Independent projected target-normal gap lower bound (µm) | Registered budget (µm) | Independent support error | Independent Gram error | Maximum normalized-gap difference (m) |
|---:|---:|---:|---:|---:|---:|
| 1 | −4.256 | 50 | 2.84e−15 | 4.35e−15 | 2.19e−13 |
| 2 | −22.938 | 50 | 5.72e−14 | 2.03e−13 | 6.96e−13 |

Both poses have 54 positive-area pairs. The independent physical-gap checker
from the existing deformable-target example bounds target-normal distance
over projected overlap. This is a different normal convention from the
solver's reported source-normal sampled minimum, so their numerical minima
must not be equated. Both independent bounds satisfy the dimensional budget.
The [first-pose quadrature output](d1_target_grid_first_pose_geometry_log_20260929.txt)
and [second-pose output](d1_target_grid_second_pose_geometry_log_20260929.txt)
were obtained offline from the saved snapshots with the same probe version;
their corresponding resource records are alongside them. This narrows
accepted-pose geometry and integration uncertainty for this two-step press.
It does not certify gap along rejected trials or swept solver paths,
directional derivatives, independent coupled response or the full D1
integration-error budget.
An independent read-only follow-up found no defect in applying the existing
projected target-normal bound to this finer S3 grid or in the saved-pose
identity. It endorsed only the two accepted-pose dimensional-gap and smooth
quadrature evidence, with the path, derivative and full integration limits
above unchanged.

## Evidence and decision

### Refined-target eight-step workflow

The parameterized runner was extended with an opt-in `--four-phase` path that
uses the original example's five waypoints and load factors. The 4-Q4/32-S3
case completed all eight press/slide/open/recontact steps in **96.19 s** at
**433.61 MB** sampled process-tree peak, within the unchanged 180 s/1 GB
development caps. Its first two step displacement vectors and integrated
contact forces match the earlier two-step press exactly. [Raw cycle](d1_target_grid_4x4_cycle_20260929.json),
[captured log](d1_target_grid_4x4_cycle_log_20260929.txt), and
[resource record](d1_target_grid_4x4_cycle_resource_20260929.json) preserve
the source, runner hash, snapshots and diagnostics.

| Step | State | Active pressure modes | Source normal contact force (N) | Independent projected target-normal gap lower bound (µm) | Positive-area Q4/S3 pairs |
|---:|---|---:|---:|---:|---:|
| 1 | press | 2 | 0.0000183951 | −4.256 | 54 |
| 2 | press | 2 | 0.0004282033 | −22.938 | 54 |
| 3 | slide | 3 | 0.0003632720 | −24.190 | 55 |
| 4 | slide | 4 | 0.0002852520 | −25.692 | 55 |
| 5 | release | 2 | 0.0000158944 | −4.373 | 55 |
| 6 | open | 0 | 0 | +40.000 | 55 |
| 7 | recontact | 2 | 0.0000158944 | −4.373 | 55 |
| 8 | recontact | 4 | 0.0002852520 | −25.692 | 55 |

Every accepted pose satisfies the registered 50 µm independent projected-gap
budget. Independent current-skin clipping and quadrature at steps 3–8 agree
with production support within 5.11e−14 relative L2, pressure Gram within
1.95e−13 relative Frobenius and normalized gap within 7.19e−13 m maximum.
The six [pose logs and resource records](d1_target_grid_cycle_pose_3_log_20260929.txt)
use the same offline probe and saved-cycle hash; steps 1–2 have the separate
checks above. Integrated source/target contact-force imbalance is at most
1.09e−19 N in these six later steps. The changing positive-overlap count
exercises a smooth clipping-topology change, but these saved-pose values do
not check generalized derivatives through its transition.

This establishes a refined, generic-position deformable-target development
workflow with accepted-pose independent gap and quadrature checks. It does
not establish a converged two-body spatial response, a full integration-error
budget, swept/rejected-path geometry, moment work, pressure-space stability
or D1 qualification. Timings across different mesh sizes do not measure an
optimization speedup.
Independent read-only review found no concrete defect in the optional
four-phase path, old/new first-step identity or saved-pose quadrature binding.
Its endorsement is limited to the completed generic-position development
cycle and accepted-pose checks stated here.

Each case has a raw result, bounded resource record and captured log under
`docs/d1_review_support/d1_target_grid_<case>_20260929.*`, where `<case>` is
`original_control`, `baseline_final`, `2x1_final`, `2x2`, `2x4` or `4x4`.
The earlier `baseline` and `2x1` records remain as source-identity history.
The final raw records
bind the imported worktree module and source base commit `9a42f42d`; runner
SHA-256 is `69A7DED8200EB009434301FEE7C5B10987902BD8FC7CDC40130763C243ABE359`.

**Decision:** The old two-S3 target cannot be used as a spatial reference for
this press. Both target directions still affect integrated response above 2%
at the tested resolutions. Stop this exploratory sequence here. Design a
claim-bearing two-body case and paired mesh/front reference with independently
checked geometry, response, integration and gap budgets before spending a
larger coupled refinement authority. Retain the exact-seam guard and the
original failed three-face prototype separately.
