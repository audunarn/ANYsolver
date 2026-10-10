# General contact — usable deliveries and current limits

10 October 2026. Full C0–C9 remains incomplete. This page identifies concrete
handoffs; it does not promote development results into engineering acceptance.

| Delivery | Current status | Entry and evidence |
|---|---|---|
| Planar elastic small-rotation Q4/S3 interior static | Historical independent acceptance. Current registered force/displacement8-stage and2+6 restart workflow tested; current scientific acceptance remains open. | [Current usage](GENERAL_CONTACT_D1_CURRENT_HANDOFF.md); [historical acceptance](GENERAL_CONTACT_D1_INTERIOR_SHELL_HANDOFF_20260930.md); [current evidence](../../contact_d1_current_delivery_20261009/OUTCOME.md). |
| S3 partial-rim Coulomb friction | Fresh installed seven-stage execution and actual restarted stage 7 completed; focused physical/history/safety checks passed. | [Public example](../examples/general_contact_s3_rim_replay.py); [fresh result](../../contact_s3_rim_full_workflow_20261009/OUTCOME.md); [lead audit](../../contact_s3_rim_full_workflow_20261009/LEAD_AUDIT.json). |
| Finite-Q4 tilted relative-motion static | Fresh16 poses, independent saved skin/gap assessment and20 public checks pass; real open→recontact and zero-increment terminal restore distinguished. Development only. | [Guide](GENERAL_CONTACT_TILTED_RELATIVE_HANDOFF.md); [outcome](../../contact_tilted_relative_public_delivery_20261009/OUTCOME.md). |
| Finite Q4-source / S3-V2D-target static | Exact elastic frictionless2+2 fixture, installed16-stage path, independent saved checks, advancing open restart and cancellation tested. Development only; formulation-owned state stays distinct. | [Guide](GENERAL_CONTACT_FINITE_Q4_V2D.md); [evidence](../../contact_finite_q4_v2d_delivery_20261009/FINAL_HANDOFF.md). |
| Finite S3-V2D / S3-V2D static | Exact elastic frictionless2+2-triangle fixture;30 installed successes across staged checks, fresh path, actual restart and state safety. Development only. | [Guide](GENERAL_CONTACT_FINITE_V2D_PAIR.md); [evidence](../../contact_finite_v2d_pair_delivery_20261009/FINAL_HANDOFF.md). |
| Automatic declared-domain finite shell static | Exact2+2-V2D fixture; persisted roles, lifecycle, advancing restart and saved physical checks tested. Evidence comprises19 source successes by impact,7 installed workflow checks and a separate installed inverse matrix. | [Guide](GENERAL_CONTACT_FINITE_AUTOMATIC_SHELL.md); [evidence](../../contact_finite_automatic_shell_delivery_20261009/FINAL_HANDOFF.md). |
| Finite S3-V2D / fixed planar rigid patch static | Exact2-source/2-tool-triangle penalty fixture; matching654-payload package, fresh4/saved mechanics, active2/open3 advancement, separate terminal restore and state/legacy checks pass. Development only. | [Guide](GENERAL_CONTACT_FINITE_V2D_RIGID_PATCH.md); [evidence](../../contact_finite_v2d_rigid_patch_delivery_20261009/FINAL_HANDOFF.md). |
| Broader shell/beam/native/impact/application combinations | See each exact implemented/tested/accepted row. | [Capability ledger](GENERAL_CONTACT_CAPABILITIES.md); [full programme](GENERAL_CONTACT_FULL_PROGRAMME_20260929.md). |

The full-programme independent status review informs the current plan; it does not
accept these development rows. Current artifact acceptance, broad pressure-space
stability, required response/refinement evidence and release remain separate.
The finite V2D/fixed finite planar rigid delivery remains bounded by its guide;
it does not close finite-response or pressure-stability qualification. See the
[review adjudication](../../contact_astra_opus_status_review_20261009/ASTRA_ADJUDICATION.md).

## Partial-rim example contract

The public example uses one S3 source and two conforming S3 target faces. Physical
planes remain parallel with positive Cartesian normal; sliding has one direction.
Source normal motion is prescribed. The elastic target deforms in the sliding
direction. Its normal and other tangential coordinates remain constrained.

The ordinary `solve_static_nonlinear` route receives explicit contact definitions,
solver settings, friction settings and the path programme. Fine-P1 projected
penalty normal pressure and material-frame friction replay use the shared reference
partition. The example sets normal/tangential regularization explicitly, physical
skins and offsets, and a 50-micrometre gap budget. Source bottom offset is −0.035 m,
target top +0.015 m. Checkpoint identity rejects an incompatible method/definition.

The seven stages are press, small stick motion, partial slip, rim exit, reverse
outside overlap, opening and recontact. Saved output contains status, diagnostics
and the committed checkpoint. Report whether execution is a fresh full path or an
actual restarted suffix. A terminal restore with zero new increments is not a
recontact run. The fresh installed invocation completed all seven stages in
167.7614299 s, peak 212.027 MiB. Its saved-output checks took 32.5086081 s and
confirmed every phase reaction/work, exact physical gap bounds, immutable material
history and terminal force/wrench balance. Equilibrium error is 1.70536e-11;
maximum phase-work difference from the authenticated restart chain is 2.0871e-18 J.
The installed restarted stage-7 run separately completed in 213.4900471 s.
These are different complete invocations, not a controlled speed comparison.

Verified development wheel SHA256:
`6f4f4023f0193b8c1c52fc788258091c5e6664107460b26079b97cc75680df66`.
[Wheel](../../contact_s3_rim_recontact_delivery_20261009/candidate-final/wheel/anysolver-0.4.7-py3-none-any.whl)
and [private install manifest](../../contact_s3_rim_recontact_delivery_20261009/current-install.json)
bind all 648 Python payloads. Use this exact private artifact and the source-bound
public example. Its CLI arguments are `--through-step 7 --output <new-output.json>`;
no `--restart` was supplied for the fresh result.

The [exact consumed invocation and environment](../../contact_s3_rim_full_workflow_20261009/attempt-01-fresh-cli/input.json),
[seven-stage output](../../contact_s3_rim_full_workflow_20261009/outputs/fresh-cli.json),
[saved-state verification](../../contact_s3_rim_full_workflow_20261009/outputs/verify-saved.json)
and [runtime/import record](../../contact_s3_rim_full_workflow_20261009/attempt-01-fresh-cli/runtime.json)
are preserved. JIT was disabled, Numba used one thread and observed BLAS pools used
one thread, with a serial 953 MiB process-tree limit. Closed guards are evidence,
not reusable execution authority. A future run uses a new output and prospective
scope under the standing approval. Engineering acceptance, release and a measured
complete-route speedup are not claimed.

This narrow model does not admit source bending/free normal motion, general vector
sliding, changing normals or arbitrary shell contact. Discrete work and local
verification do not establish continuum convergence, pressure-space stability or
full friction engineering acceptance. Use exact capability status in applications.

## Accepted shell artifact recovery

The historic accepted installed directories are absent from permitted paths.
Metadata recovery matched 422 of 433 registered Python payloads; eleven hashes and
several registered helper/entry inputs remain unresolved. The private partial
restore must not be imported as the accepted package. Historical science remains
recorded, while a current usable accepted artifact requires the complete original
payload or explicit current-source impact and installed verification.

See the [goal](../GENERAL_CONTACT_GOAL.md), [plan](../GENERAL_CONTACT_PLAN.md) and
[restart](../GENERAL_CONTACT_RESTART.md) for the active delivery route.

## Current D1 installed handoff

The [current guide](GENERAL_CONTACT_D1_CURRENT_HANDOFF.md) supplies exact commands
for sixteen Q4 source faces and32 S3 targets, explicit physical skins, 0.018 N
force/weighted displacement controls and0.04 m target slide. Both fresh eight-stage
cycles and an actual2+6 continuation completed. Complete split pose/history/state
differences are zero; fresh terminal equilibrium/reaction defects are below
5.6e-11 relative. Independent projected gaps meet the50 μm budget. This closes
current usability as tested development, not scientific acceptance transfer.
The same verified648-payload wheel is reused; all remaining science/provenance
limits are explicit in the guide.
