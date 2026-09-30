# D1 interior Q4/S3 shell contact — current handoff

**30 September 2026. Independently accepted D1-interior handoff; not release or full-programme completion.**
The [goal](../GENERAL_CONTACT_GOAL.md) rev2026-09-29.3 and
[plan](../GENERAL_CONTACT_PLAN.md) rev2026-09-30.23 control the scope.
The independently reviewed passes below belong to installed `87c53913`.
SpatialV5/590d and V6/90baf timed out during checkpoint creation; no spatial pass.
Candidate0b2ac9be has independent installed complete checkpointV2 and fresh Q4
timing PASS. SpatialV7 completed all35criteria and current installed public-prefix
comparison is exact. Final independent spatial/installed/profile disposition is PASS.
The historical [c55 installed handoff](GENERAL_CONTACT_D1_INTERIOR_SHELL_HANDOFF.md)
retains its original wheel, fixture and limitations unchanged.

## Implemented route and physical fixture

The ordinary public route uses `ContactSurface`, `ContactInteraction`,
`ContactDefinition`, `ContactSolverSettings`, `ContactPathControl`,
`ContactPathNodalForce`, `ContactPathProgram`, `validate_general_contact` and
`solve_static_nonlinear(model, contact=definition, contact_settings=settings,
contact_path_program=program, record_increment_snapshots=True,
emit_restart_checkpoint=True)`. Saved checkpoints are owner-validated; a changed
definition, analysis contract or incompatible contact revision must reject.

The registered force cycle has **16 Q4 source faces and 32 deformable S3 target
faces**, with source bottom and target top physical skins. Both thicknesses are
0.05 m; the S3 reference-surface offset is 0.01 m, so its top-skin offset is
0.015 m. Source/target Young moduli are 100000/500000 Pa, Poisson ratio 0.3;
the common reference slope is 0.0001 and initial normal gap is 40 micrometres.
Source perimeter `uz` is supported, source rotations remain free, and a lateral
guide/anchor and moving target left-edge constraints remove rigid mechanisms.

Both completed controls select `monolithic_active_set`, `primal_mortar`, fine
nodal Q1 pressure, `jet2_q4_s3_dev`, `overlap_local_dev` and `d1_interior_profile`.
The interaction retains augmented normal-law identity, normal stiffness
10000 Pa/m and 50 micrometre gap budget. Derivative resolution is 1e-5;
coverage/boundary-force admission tolerances are 1e-10 m²/1e-10 N.
Current physical source-normal freedom includes model **and path** constraints;
positive source-face overlap must be wholly covered by the target union, and
active pressure must remain away from source rims/tips. Unsupported trials fail
or use the declared physical cutback; supported pressure modes are not deleted.

Force control uses a normalized physical-bump load of 0.018 N and 0.04 m target
slide through press, slide, opening and recontact (two steps/phase; eight poses).
Displacement control uses the same geometry and target slide, **zero external
nodal loads**, and one weighted source-`uz` functional calibrated from force
press endpoint 2 to −9.340222503369683e-5 m. Individual source normals remain
free subject to this scalar control. Its driver NCP force scale is
0.013376864330719142 N, chosen once from the contact-free elastic predictor;
physical force/moment assessment scales remain 0.018 N / 0.018 N·m.
Half-displacement and half-force intermediate poses are not a duality claim.

## Scoped evidence on the installed 87c artifact

Artifact: `87c53913f96718b350531348d2300314df333491`; isolated target
`C:/ANYworkspaceWork/general-contact-final-87c53913/target`; wheel SHA256
`9de057da10e9cb00b8aa19fe0ad106b170d8fdf91d571656b606104ea961dab5`.
All 433 package files match the frozen artifact. Recorded environment is
Python 3.14.2, NumPy 2.4.6 and SciPy 1.17.1. Passes are independently scoped
dispositions; helper JSON flags remain conservative and capability is developmental.

| Evidence | Exact records and scope |
|---|---|
| Force/work/path PASS | [Freeze](d1_review_support/d1_final_lifecycle_v1_20260930.freeze.json), [eight poses](d1_review_support/d1_final_lifecycle_v1_20260930_full.json), [body wrench](d1_review_support/d1_final_lifecycle_v1_20260930_body.json), [gap/NCP](d1_review_support/d1_final_lifecycle_v1_20260930_gap.json), [director work](d1_review_support/d1_final_lifecycle_v1_20260930_director_invocation_v2.json); 170.154 s / 437.86 MB. Small-rotation elastic/von-Karman scope. |
| Actual active/open restart PASS | [Active split 2+6](d1_review_support/d1_final_lifecycle_v1_20260930_active_parity.json), [open split 6+2](d1_review_support/d1_final_lifecycle_v1_20260930_open_parity.json): all 11 owner-aware gates each; explicit prefix provenance, all poses, complete committed state, loads/targets and history at 1e-10. Includes subsequent recontact. |
| Weighted-displacement PASS | [Freeze](d1_review_support/d1_final_displacement_v1_20260930.freeze.json), [eight poses](d1_review_support/d1_final_displacement_v1_20260930_full.json), [assessment](d1_review_support/d1_final_displacement_v1_20260930_assess.json); 178.728 s / 426.60 MB. Open pose 6 exactly zero; recontact 7/8 positive. Minimum independent gap −39.025 micrometres; maximum normalized moment defect 8.58e-7. |
| Analytical/code PASS | [Response freeze V2](d1_review_support/d1_final_response_v2_20260930.freeze.json); manufactured Q1 levels [4](d1_review_support/d1_final_response_v2_20260930_analytic4_assess.json), [8](d1_review_support/d1_final_response_v2_20260930_analytic8_assess.json), [16](d1_review_support/d1_final_response_v2_20260930_analytic16_assess.json): 11/11 each under 0.1%. [Matched nonlinear KKT](d1_review_support/d1_final_response_v2_20260930_kkt_assess.json): normalized full 174-coordinate physical/generalized contact work 9.2501e-8 ≤ 1e-6. Offline/guided reference scope remains separate. |
| Finite pressure maps PASS | [V3 freeze](d1_review_support/d1_final_response_v3_20260930.freeze.json), [V4 correction freeze](d1_review_support/d1_final_response_v4_20260930.freeze.json), assessed signed spaces [9](d1_review_support/d1_final_response_v3_20260930_pressure4_assess.json), [25](d1_review_support/d1_final_response_v4_20260930_pressure6_assess.json), [121](d1_review_support/d1_final_response_v4_20260930_pressure12_assess.json) and [actual step-8 recontact](d1_review_support/d1_final_response_v4_20260930_pressurerecontact_assess.json). Eta ≥ .99999754, kappa ≤ 1386.397; 24 independent directions. Finite reference-energy inequality, not mesh-uniform or current-Newton inf-sup stability. |
| Immediate state PASS | [V2 freeze](d1_review_support/d1_final_transaction_v2_20260930.freeze.json): cancellation, exception, rejected candidate (3) and injected precommit admission cleanup (1); [V3 physical freeze](d1_review_support/d1_final_transaction_v3_20260930.freeze.json) and [result](d1_review_support/d1_final_transaction_v3_20260930_physical.log): genuine positive swept cutback (1). Exact retained dictionary owners/payload/published bindings; no native-trial or store-generation claim. V3 isolates external pytest plugins without changing the guard. |
| No-contact PASS | [Q4 V1 freeze](d1_review_support/d1_final_20260930_v1_nocontact.freeze.json), [V1 results](d1_review_support/d1_no_contact_runs/d1_final_20260930_v1_nocontact/summary.json), [separate beam V2 freeze](d1_review_support/d1_final_20260930_v2_beam_confirm36.freeze.json) and [36-pair result](d1_review_support/d1_no_contact_runs/d1_final_20260930_v2_beam_confirm36/summary.json). Exact upper-median 5% gate; beam V2 median 1.04220, upper 1.04672. Earlier beam V1 nonpass remains retained and unpooled. |

## Existing executable entry points

Run from the matching worktree with the declared installed target first on
`PYTHONPATH` and the worktree root after it; never silently import `solver/src`.
The commands below document existing interfaces, **not renewed authority** for
consumed formal runs. Use unused output paths and the applicable supervisor:
routine checks 180 s / 1 GB; registered integrated/reference runs 900 s / 4 GB.

```powershell
$env:PYTHONPATH='C:/ANYworkspaceWork/general-contact-final-87c53913/target;C:/ANYworkspaceWork/ANYsolver-general-contact'
python -m examples.general_contact_d1_interior_controls_dev --output NEW-example.json
python -m scripts.general_contact_d1_interior_press_dev NEW-force.json --source-columns 4 --source-rows 4 --target-columns 4 --target-rows 4 --force-n 0.018 --reference-slope 0.0001 --target-young-multiplier 5 --source-support perimeter --load-shape physical_bump --slide-body target --target-reference-full-left-clamp --target-left-edge-motion --four-phase --slide-distance-m 0.04 --q4-gap-certificate overlap_local_dev --record-accepted-poses --record-swept-fractions
python -m scripts.general_contact_d1_displacement_cycle_dev NEW-displacement.json --force-reference docs/d1_review_support/d1_cycle_force018_slide040_v5_20260930.json --preflight-record docs/d1_review_support/d1_displacement_cycle_preflight_v1_20260930.json
python -m scripts.general_contact_d1_displacement_cycle_dev NEW-displacement-assess.json --assess-saved docs/d1_review_support/d1_final_displacement_v1_20260930_full.json
```

The compact public example has its own two-S3/0.04 N defaults; it is not the
32-S3 formal cycle. Exact registered arguments, hashes and assessment commands
are authoritative in the linked freezes and [command inventory](d1_review_support/D1_FINAL_CHECK_INVENTORY_20260930.md).
The force CLI supports `--max-path-fraction 0.25` or `0.75` and
`--restart-checkpoint PREFIX.json`; complete comparison uses the existing
`d1_cycle_restart_check_dev.py` with an explicit matching prefix. Revision-mismatched
historical checkpoints must reject, not be resealed. Both cycle scripts retain
actual import identity, complete accepted snapshots/history and restart payloads.

## Retained precursor artifacts and impact evidence

`590d7a42d35585105842fb696a0ea14f87db170b` changes only the conservative padded
projected-box rejection in `_touching_projected_boundaries`, including strict
NumPy-error-policy fallback. Equations, derivatives, tolerances and drivers are
unchanged. [Twenty controls](d1_review_support/d1_touch_bounds_controls_v2_20260930.log)
plus [strict-policy control](d1_review_support/d1_touch_bounds_strict_policy_v3_20260930.log)
pass; independent review and [saved-report parity](d1_review_support/d1_saved_report_touch_probe_v2_20260930.json)
retain every force component/certificate. The local 38.925→33.998 s result is
12.66% reporting improvement, not a whole-route or twofold speed claim.

Precursor590d wheel SHA256 `b257388fd7b86b7e69006baa73464c56cc66cbb1901b2ad4d49d27c75272b96c`,
target `C:/ANYworkspaceWork/general-contact-final-590d7a42/target`: 433 source/target
files match. [Spatial V5 freeze](d1_review_support/d1_final_spatial_v5_20260930.freeze.json)
binds the unchanged guided 12/12 radial fixture and all 35 response predicates.
Its one 900 s / 4 GB execution timed out during checkpoint creation; it is NONPASS.
Historical serialization successor90baf01a has independent scoped PASS for complete
new-installed active/open producer/consumer byte/hash parity (35.829s/251.77MB).
SpatialV6 is terminal NONPASS900.077s/570.73MB; checkpoint began525.788s.
## Current installed artifact and final disposition

Current source `0b2ac9be8d069d6708068c8b2ff2b638b1ae70e1`, installed target
`C:/ANYworkspaceWork/general-contact-final-0b2ac9be/target`, wheel SHA
`97c3f4ca49c7b82a7efc06f03fdae9e2051126814faed8be34f56605b7e7867d`.
All433 source/wheel/installed Python files match. Only3files differ from87c:
`s3_patch_augmented.py` (reviewed conservative reporting bound),
`e4_pl_s3_state.py` (small inert immutable-signature cache), and
`nonlinear_restart.py` (proven pure mapping/array/Node observations).
Mechanical equations, structural/contact derivatives, settings and restart
semantics remain unchanged; mutable/custom observations and complete owner
validation stay live. Reuse older science only through final explicit impact.

| Current0b2 evidence | Result and exact record |
|---|---|
| Installed complete checkpoint boundary | Independent scoped PASS,23.565s/248.975MB; [two complete roots](d1_review_support/d1_saved_checkpoint_roundtrip_v2_20260930.json), full canonical/hash parity. |
| Fresh named Q4 no-contact | Independent scoped PASS;12balancedpairs,98.071%coverage uppermedian1.040529<=1.05; [summary](d1_review_support/d1_no_contact_runs/d1_final_0b2_20260930_q4_nocontact/summary.json). Unchanged genericBeam prior scoped timing is impact-reused separately. |
| Spatial response | [V7freeze](d1_review_support/d1_final_spatial_v7_20260930.freeze.json), [complete run](d1_review_support/d1_final_spatial_v7_20260930_radial.json):733.119s/568.046MB; checkpoint187.212s. [All35criteria](d1_review_support/d1_final_spatial_v7_20260930_radial_assess.json) pass,0remaining; independent scoped PASS. |
| Installed public-solver workflow | [Frozen2pose replay](d1_review_support/d1_final_installed_workflow_v1_20260930.freeze.json), [result](d1_review_support/d1_final_installed_workflow_v1_20260930_prefix.json):52.218s/408.805MB. [Complete current-owner comparison](d1_review_support/d1_final_installed_workflow_v1_20260930_assess.json):8.653s/251.658MB,0difference/0failure in both poses, reactions, loads, histories and full committed state. Independent scoped PASS. |

Spatial physical-bin L1/L2 errors including uncertainty are0.9303%/0.9536%;
maximum target-displacement error1.8873%; independent penetration0.1244micrometre
against50micrometres. Earlier V5/V6 timeouts remainNONPASS. Successful current
completion is not a reliable complete-solve speed ratio; four balanced saved
checkpoint-route runs support only28.37% median reduction on that saved route.
Public exact-model evidence/application-admission/release flags remainfalse;
profile-family qualification belongs to the source-scoped ledger, not arbitrary
models. D1-interior is independently accepted through the explicit final source-impact
disposition in [review](d1_review_support/D1_CHECKPOINT_SUCCESSOR_REVIEW_20260930.md).
The eight-pose87c force/displacement/restart, immediate elastic transaction and
finite pressure/reference rows keep their original execution identities;430of433
packagefiles are unchanged and the three affected joins have reviewed/fresh
evidence. Acceptance is bounded elastic small-rotation/vonKarman with the listed
interior admission conditions and controls. General mesh-uniform stability and
arbitrary models are not qualified by these finite registered cases.

Preserve historical pressure/cut-front failures, invalid uncertainty references,
0.04 N work/moment failures, near-coincident geometry failures, parser/import
failures, V1 observer failure and V2 annotation-guard failure. No arbitrary tie,
finite-rotation, nonlinear-material, rim, prescribed-normal-edge or partial-target
cut admission follows. [D2 and the full programme](GENERAL_CONTACT_FULL_PROGRAMME_20260929.md)
remain required: boundary/partial-overlap pressure method, broader shell pairs,
warped/rotating geometry, rims and search; then beams, friction/material continuation,
impact/dynamics and application/package delivery. D1 does not complete C0–C9.

