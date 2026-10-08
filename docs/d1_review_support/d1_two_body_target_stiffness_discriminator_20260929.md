# D1 deformable-target structural resolution discriminator

## Question and fixed comparison

The coupled 4-Q4 target-grid press changed integrated source normal force by
−5.93% from 2×4 to 4×4 target cells. Before spending another coupled mesh
budget, test whether the actual S3 target's broad bending compliance changes
substantially under that same mesh change.

The [parameterized offline runner](d1_two_body_target_stiffness_discriminator.py)
extracts the target-only linear stiffness from the unchanged two-body model.
It keeps target material, thickness, offset, rectangle and x=0 clamp fixed.
Three unit-resultant affine normal tractions are integrated with the exact
P1 triangle consistent-load matrix: uniform, free-edge x-biased and
upper-rim y-biased. Their physical total forces and first moments are
identical across 2×4, 4×4, 8×8 and 16×16 meshes. This isolates target-only
linear response for these loads; it does not reproduce the contact traction.

| Target mesh | Uniform compliance (m/N) | Free-edge x compliance (m/N) | Upper-rim y compliance (m/N) |
|---:|---:|---:|---:|
| 2×4 | 0.10505617 | 0.20907783 | 0.10725398 |
| 4×4 | 0.10136550 | 0.20931659 | 0.10488678 |
| 8×8 | 0.09963768 | 0.20833350 | 0.10379708 |
| 16×16 | 0.09930745 | 0.20829228 | 0.10363063 |

The 2×4→4×4 changes are −3.513%, +0.114% and −2.207%, respectively.
The 4×4→8×8 changes are −1.705%, −0.470% and −1.039%; all 8×8→16×16
changes are below 0.332% in magnitude. The largest relative linear-solve
residual is 1.04e−10 and target stiffness asymmetry is about 1e−18.
Positive measured compliances do not establish positive definiteness of
every structural mode.

The [aligned raw record](d1_target_structural_compliance_aligned_20260929.json)
and [resource record](d1_target_structural_compliance_aligned_resource_20260929.json)
bind source, runner hash and imported module. The complete offline batch took
1.75 s at 165.74 MB sampled process-tree peak, within 180 s/1 GB. The
earlier [three-mesh record](d1_target_structural_compliance_20260929.json)
is retained as method history; its lack of the 2×4 comparator was corrected
before interpreting the coupled −5.93% change.

## Interpretation and next action

Broad target-only stiffness is sensitive to the exact 2×4→4×4 change, but
the magnitude depends strongly on traction shape. A target-only compliance
percentage cannot be equated to a coupled contact-force percentage. The
actual moving contact pressure and active front must be held fixed in the
next structural-only comparison before attributing the coupled difference to
target bending or pressure/front coupling. Recover the accepted 4×4 source
Q1 pressure field from the ordinary solver, project that *same physical
field* onto each target mesh with independent quadrature, and compare target
compliance. Do not launch a larger coupled mesh from these affine-load data
alone.

Independent read-only review found no defect in the exact affine load mapping,
target-only stiffness extraction or aligned 2×4→4×4 comparison. It confirmed
the mixed load-shape sensitivity and the limits on attributing the coupled
force difference.

## Fixed contact-shaped load follow-up

The accepted 4×4 two-step press was replayed solely to retain its Q1 pressure
field. Its displacements and final integrated force are exactly unchanged.
Only source nodes 3 and 8 carry pressure, at 0.002231765 and 0.001501456 Pa.
The [pressure record](d1_target_grid_4x4_pressure_20260929.json) and
[bounded resource record](d1_target_grid_4x4_pressure_resource_20260929.json)
bind that field to the ordinary monolithic solve.

The offline runner then held **that same source reference-XY Q1 field** fixed
and independently clipped its overlap against each S3 target mesh. Tensor
Gauss quadrature on the clipped triangle fans mapped pressure into consistent
target nodal force. Its raw resultant is 0.000428203329 N on every mesh,
versus the saved current-pose source reaction of 0.000428203290 N; the small
difference follows from evaluating the fixed field on reference rather than
current geometry. The unit-normalized load's first moments are identical
across meshes: x=0.600000 and y=0.524097 m.

| Target mesh | Compliance to fixed contact-shaped load (m/N) | Change from prior |
|---:|---:|---:|
| 2×4 | 0.06180392 | — |
| 4×4 | 0.06570134 | +6.306% |
| 8×8 | 0.06529432 | −0.620% |
| 16×16 | 0.06534904 | +0.084% |

The [contact-shaped raw record](d1_target_contact_shaped_compliance_20260929.json)
and [resource record](d1_target_contact_shaped_compliance_resource_20260929.json)
capture the source/module identities and solve residuals. The batch took
1.98 s at 170.64 MB sampled peak; the largest contact-shaped relative linear
residual is 3.49e−11.

As a *development predictor*, scaling the saved 4×4 coupled force by inverse
target-only compliance predicts a 2×4 force of 0.00045520622 N, versus the
observed 0.00045520984 N. The corresponding force-change percentages differ
by 0.00075 percentage points. The same fixed-load predictor gives
0.00043087256 N at 8×8, 0.623% above the saved 4×4 force. This close 2×4
match supports target structural resolution under the actual pressure shape
as a leading hypothesis; it does not prove the nonlinear coupled law or
pressure front stays fixed as the target mesh changes. Freeze this prediction
before one capped 8×8 coupled press. If that solve shifts materially beyond
the fixed-load estimate, inspect pressure/front changes before further mesh
refinement. A match would still require independent reference, pressure-space
and integration qualification for D1.
Independent read-only review found no concrete defect in the fixed-Q1
pressure reconstruction, overlap quadrature or mesh-to-mesh load identity.
It endorsed one capped 8×8 two-step coupled press as a discriminator, while
retaining the nonlinear coupling and spatial-convergence limitations.

## One predicted 8×8 coupled press

The pre-recorded 8×8 target two-step press completed within the unchanged
development limits: **69.05 s**, **432.55 MB** sampled process-tree peak,
two accepted steps and no contact failure. Its source normal contact force is
**0.00043102895 N**, 0.660% above the saved 4×4 result and 0.0363% above
the fixed-pressure structural prediction of 0.00043087256 N. The same source
pressure nodes 3 and 8 remain active, although their pressure values shift
by +7.69% and −12.11% (9.29% active-pressure L2 change). The
[coupled raw record](d1_target_grid_8x8_prediction_20260929.json),
[log](d1_target_grid_8x8_prediction_log_20260929.txt) and
[resource record](d1_target_grid_8x8_prediction_resource_20260929.json)
retain settings, accepted poses, pressure and source identity.

Independent target-normal projected-gap lower bounds are −5.524 and
−36.170 µm against the unchanged 50 µm budget. At both accepted poses,
independent clipping finds 156 positive-area Q4/S3 pairs, with up to 47
target faces per source Q4. [Pose 1](d1_target_grid_8x8_pose_1_log_20260929.txt)
and [pose 2](d1_target_grid_8x8_pose_2_log_20260929.txt) independent
quadrature agree with production support within 6.60e−14 relative L2,
pressure Gram within 2.38e−13 relative Frobenius and normalized gap within
6.61e−13 m maximum. Their bounded resource records are retained alongside
the logs.

The force and active-node prediction succeeded for this one refinement.
The pressure redistribution, nonlinear coupling and lack of a further
coupled target refinement prevent a spatial-convergence or pressure-stability
claim. The result supports designing a finer two-body reference under the
resource cap; it does not by itself promote D1.
Independent read-only review found no concrete defect in the pre-registered
comparison or generalized saved-pose checker. It confirmed the force/front
prediction under this source identity and advised a separate resource
preflight before attempting a direct 16×16 coupled reference.

## 16×16 local-cost preflight and bounded next case

An accepted 8×8 final pose and its nodal pressure forces were reconstructed,
then the target displacement field was interpolated to the nested 16×16
knot grid. The triangulated S3 spaces are not strictly nested, but reference
support differs by at most 9.7e−17 m² and normalized gap by at most
3.70e−11 m at this fixed pose. The [bounded preflight](d1_target_16x16_linearization_20260929.json)
and [resource record](d1_target_16x16_linearization_resource_20260929.json)
measure:

| Local operation | 8×8 target | 16×16 target |
|---|---:|---:|
| S3 faces / structural DOFs | 128 / 546 | 512 / 1,794 |
| Structural assembly | 0.064 s | 0.214 s |
| Contact manager preparation | 3.60 s | 11.52 s |
| One active contact linearization | 4.55 s | 13.16 s |
| Contact tangent nonzeros | 62,500 | 442,225 |

The preflight took 34.59 s and 218.9 MB sampled process-tree peak. It does
not include repeated equilibrium iterations, coupled factorization, rejected
work or full solve memory. Independent read-only review found no defect in
the interpolation or fixed-pose cost comparison and judged one 16×16
two-step attempt under the unchanged hard cap reasonable, with completion
uncertain.

**Prospective development prediction before that run:** scaling the observed
8×8 source normal force by the fixed-load target compliance ratio predicts
**0.00043066804 N** at 16×16 (−0.0837%), with source pressure nodes 3 and 8
still active. Preserve the 180 s/1 GB cap. If it finishes, compare integrated
force against the retained 2% response target as a *development
discriminator*, record pressure redistribution and independently check both
accepted-pose gaps and geometry. If it hits a cap, retain the failure and
identify the measured limiting phase before another attempt. Neither outcome
alone establishes a converged continuum reference or D1 acceptance.

## First 16×16 attempt and one instrumented replay decision

The first [resource record](d1_target_grid_16x16_prediction_resource_20260929.json)
reports a **180.087 s time-cap non-success** and 495.067 MB sampled peak;
the [buffered log](d1_target_grid_16x16_prediction_log_20260929.txt) is
empty and no result record was written. The runner wrote only after the
solver returned, so this record cannot identify an accepted-step count,
limiting phase, force, pressure, gap or predictor error. The local-cost
preflight excluded repeated Newton work and factorization; its full-route
estimate was deliberately uncertain. No memory or spatial-convergence
conclusion follows from the terminated prefix.

**Prospective diagnostic action:** Add development-only unbuffered timestamps
around each monolithic step, structural assembly, contact linearization and
sparse factorization/solve, plus periodic stack snapshots. Retain the exact
solver call, mechanics and 180 s/1 GB limit. The traced 4×4 control completed
in 28.04 s/385.58 MB with the same two accepted steps and exactly the same
final source normal force (0.0004282032901014092 N) as the untraced case;
its 90 trace events include both step boundaries. Make **one** traced 16×16
replay. If it reaches step 2 near the cap, consider a specific cost reduction
before attempting a finer reference. If it remains in step 1, attribute time
to the measured phase and address that phase. Do not raise the cap, launch
another blind replay, or promote an incomplete result.

### Instrumented outcome and measured limiting work

The single [instrumented replay](d1_target_grid_16x16_traced_progress_20260929.jsonl)
also reached the [180.025 s cap](d1_target_grid_16x16_traced_resource_20260929.json)
(470.37 MB sampled peak). Step 1 began at 23.95 s and its three-iteration,
five-evaluation equilibrium solve completed at 105.76 s. Step 2 began at
115.38 s and was interrupted during a structural assembly following several
contact evaluations. The runner had not returned, so it emitted no 16×16
result, checkpoint, final reaction, pressure or gap. Entry into step 2 shows
step 1 advanced within the terminated process; no durable accepted state was
written for restart or response assessment.

Among completed traced operations, contact linearization occupied **119.83 s
across nine calls**, structural assembly 12.83 s across nine calls, and sparse
factorization plus solve 0.28 s across ten calls. The unfinished operations
and preparation/recovery time are outside those totals. The corresponding
[4×4 trace](d1_target_grid_4x4_traced_progress_20260929.jsonl) has 16.48 s
in ten contact linearizations; its mechanics and final force match the
untraced case exactly. These are development timings on different target
meshes, not a paired speedup measurement.

A separately [profiled accepted 8×8 pose interpolated to 16×16](d1_target_16x16_profile_summary_20260929.txt)
completed under the same cap ([raw profile](d1_target_16x16_profile_20260929.pstats),
[resource record](d1_target_16x16_profile_resource_20260929.json)). Its
profiled wall time includes profiler overhead and must not be compared with
unprofiled route time. It identifies repeated `q4_source_overlap_integrals`
sampling and Q4/S3 Jet2 derivative work as principal contact-kernel costs;
`PlanarFace.shape_values_and_gradient` and small-array `numpy.cross` calls
are prominent within the scalar overlap path. The [periodic stack record](d1_target_grid_16x16_traced_progress_20260929.stack.txt)
also samples that overlap path during the capped nonlinear solve. This
supports one targeted contact-kernel cost slice, with unchanged adaptive
integration and parity gates, before another large coupled solve. It does
not diagnose a mechanics defect or justify a larger resource cap.

## Bounded prepared-shape cost slice

The scalar overlap path previously rebuilt the same projected face corners
at every quadrature point. The changed Q4-source integrand prepares those
corners once per overlap evaluation. The general `shape_values` method keeps
its historical projected-Jacobian check; the prepared path is limited to
validated convex faces, with source projected-Jacobian positivity and S3
barycentric inversion checked by the existing kernel. Adaptive refinement,
pressure support, moving geometry and Jet2 differentiation remain unchanged.

The [first same-pose comparison](d1_value_only_shape_20260929.json) isolated
a value-only method experiment: old/new 16×16 contact linearization medians
were 13.302/12.841 s, a **1.036× local** ratio. Independent review identified
an edge-case failure-behavior difference in general value-only calls, so that
general method change was **reverted**. The [second balanced comparison](d1_prepared_shape_20260929.json), which includes prepared face projection,
measured 13.626/12.706 s, a **1.072× local** ratio. This latter benchmark
was recorded before the general-method revert; the Q4-source integrand under
test uses the prepared path and is unchanged by the revert. In each
comparison, support, weighted and normalized gap, pressure Gram, full force,
gap gradient and tangent matched **exactly** at the saved pose; overlap
branch, integration triangle count and evaluation count also matched. Both
ran under 180 s/1 GB, with [first](d1_value_only_shape_resource_20260929.json)
and [second](d1_prepared_shape_resource_20260929.json) resource records.
The focused [overlap/Q4-source tests](d1_prepared_shape_tests_20260929.txt)
passed 21/21. A [two-step coupled 4×4 control](d1_prepared_shape_coupled_20260929.json)
completed with exactly the previous displacements, final force and pressure;
it was recorded before the general-method revert and exercises the same
prepared Q4-source integrand. Its single 32.73 s wall time versus the
earlier 28.15 s is not a balanced whole-route comparison.

The local gain is too small to justify another 16×16 complete-solve attempt.
No twofold complete-route improvement or D1 acceptance follows. Return to
the D1 gaps using the existing 8×8 bounded coupled result and independent
references. A further production optimization requires a specific measured
mechanism and a plausible whole-route benefit; do not repeat the capped
16×16 solve or broaden a mesh sweep under the same resource limit.
