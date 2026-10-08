# B3-GE / E4-PL and B2 — current development state

**8 October 2026.** Worktree `C:/Github/ANYsolver/.perf2-worktrees/stiffened-rev8-20261008`,
branch `codex/stiffened-rev8-resume`. Read Git for the current head. This is the
authoritative current-state note. The preceding 448-line note was copied
byte-for-byte to [history](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_20261008_V12.md)
(SHA-256 `f09b8d490d39b6b3ea528f7a8f91007962607ef82ca2777e2107934132e36f10`).
The [Revision 8 plan](B3_GE_E4_PL_REVISION_8_PLAN.md),
[goal](B3_GE_E4_PL_REVISION_8_GOAL.md) and
[acceptance matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md) retain the
full G0–G6, F01–F13, V01–V28 and B01–B18 scope and all historical failures.

## Decision and next discriminator

The native BL5 connection law and multiplier policy remain **unselected**.
V5's original P0/tip action produced `1.74538504e-6 J` native beam work
versus `2.40980606e-7 J` resolved C3D20 beam work, a ratio of `7.24284`.
V11 found the saved V7 cut-face zero-resultant action changes the bounded
two-sided *solid* response by only `0.155%` under V9 supports. V12 then showed
the original native retained-spin interface action is separately balanced;
removing it on the unchanged native body reduces work by `1.15586949e-7 J`
and leaves `1.62979809e-6 J`, still `6.76319` times the saved resolved work.
Both checks had independent read-only review without blocking findings.
Neither allocates body versus connection error or qualifies a line law.
[V11](../../.development/bl5-mz-common-beam-20261008/v11-cut-warping-adjudication.md)
and [V12](../../.development/bl5-mz-common-beam-20261008/v12-retained-load-adjudication.md)
retain source, exact input, runtime, raw output and limitations.

The frozen V5/V7 records **cannot** supply a full two-sided original-action
reference. The C3D20 bar has axial faces only at `x=0,.5,1 m`, while native
retained half-cell sides also meet at `.25` and `.75 m`. A four-axial-cell
solid with duplicated interior faces would expose those sides, but its extra
relative rigid modes require an independently physical seam traction/jump
law. A full displacement weld removes the sided freedom; an unspecified
hinge fitted to V5 would be circular. This is a missing reference contract,
not a native-formulation failure. Keep V5's `7.24284` ratio unallocated and
stop the V5 causal-decomposition sequence. Advance the plan's physically
matched BL5 torque/shear and work-transfer benchmark under an explicitly
declared continuous connection, with its real geometry, loads and supports.
Do not repeat classical axial refinement or tune channels to one case.
Formal F03 remains unconsumed; G0B and G1 acceptance remain open.

The new resolved C3D20 CalculiX weak-P0 bridge executed the same 20 physical
rows through an exact-pivot `*EQUATION` representation for declared Fy=100 N
and Mx=10 N·m end-face actions. Saved external results match an independently
assembled same-law sparse C3D20 solve within `1.53e-9` and `3.12e-10`
relative displacement. Raw CalculiX root `RF` excludes the weak constraint
force; adding `Cᵀλ` gives balanced physical support. Both saved results pass
the stated development deck-parity checks. Against the native experimental
BL5 owner, the work-conjugate response ratios are Fy `0.95955` and Mx
`1.22489` (native/resolved). See the versioned
[adjudication](../../.development/bl5-ccx-weak-p0-20261008-adjudication.md)
and raw directories named there. Fy/Mx are new actions, not V5's +Fz;
their equal resultants do not establish identical warping work or allocate
body versus connection error. A bounded beam-only Mx comparison now gives
native/resolved `1.13594`, while the coupled result remains `1.22489`.
Both beam-only models balance 10 N·m, but the resolved root clamps its whole
bar face and native B3-GE clamps one section pose; the end torque work fields
also differ in warping. This establishes a body/traction/root discrepancy,
not an additive allocation of the coupled gap. The rigid-shell weak-P0 Mx
counterfactual then gave native/resolved `4.07302`; both KKT/work/wrench
checks passed, and local row-normalized algebraic conditions were `7.30`
(resolved) and `3.08` (native). This fixes the entire shell and restrains
the beam along the line, a distinct boundary problem that amplifies trace
differences. Its algebraic row condition is not an F03 stability metric.
Stop loaded refinements here. Read-only source inspection found that
`test_actual_global_continuum_common_field_and_integrated_dual` and
`test_actual_common_native_weak_work_and_station_dual` already exercise all
five channel densities, including beam x-spin, on the supported globally
affine common subspace. They do not cover arbitrary broken native half-cell
traces. Reuse their existing accepted execution evidence where bound; check
its identity before citing it. The prospective F03 draft also records a
physical-core continuity obstruction for the unsmoothed L1 yaw/P0 pairing on
anisotropic grids; its finite-area patch is a distinct distributing law, not
an accepted bonded-line replacement. Before another loaded solve or generic
growing-space spectrum, identify a supported off-common motion, evaluate its
continuous physical gap and work, and decide whether the declared bond
prohibits it. If prohibited, correct the continuous work map before selecting
an interface space; if admissible, retain its semantics and test physical
transfer. Only a law with a justified work norm advances to the prospective
growing-space F03 assessment. No new common-field helper is needed. Do not
select a line law from the saved ratios.

A bounded 1:1, five-channel BL5 source check now supplies one concrete
off-common witness: alternating lateral translations of `±1e-4 m` at the five
native beam nodes respect the fixed supports. The actual sampled continuous
gap exceeds `5e-5 m`, while every P0 weak row is below `1e-13`; the same law
with continuous-P1 rows detects it above `1e-6`, and the physical operator
after stationary-resultant elimination has positive strain energy. Thus this
motion is prohibited by the declared continuous translation law but invisible
to that P0 projection. It is not a zero-energy mechanism, the saved 2:1
Fy/rotation mode, or evidence for six-channel L1/P1 selection. The changed
focused test passed 1/1 in 2.55 s (5.45 s process wall); preserve both
[attempts](../../.development/bl5-off-common-20261008-v2/receipt.json), with
v1 superseded by the added actual-gap/weak-row parity check. CPU affinity 1
was observed; one thread/JIT-off were requested, not independently observed.
The sampled parent RSS field is not a reliable process-tree peak. The next
decision still requires physical work and a justified norm for the disputed
off-ratio mode before any formal F03 comparison.

## Delivered experimental behavior and open acceptance

- The sparse multi-element Q4/mixed Q4-S3/all-S3 GE point workflow, physical
  recovery, checkpoint/restore, and continued stepping exist. Separate B2
  batch execution and an ANYfem consumer exist. These are experimental
  capabilities, not G0/G1/G6 acceptance.
- The pinned ANYfem `345db0c` and solver installed sites pass 54/54 affected
  plus 19/19 legacy development controls. Earlier exact packet V2/V3
  pre-pytest timeouts remain failed evidence. Effective numerical thread
  pools were not independently audited in the successful consumer smoke.
  [Evidence](<C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/.development/distributing-displacement-consumer-common-main-20261008-v1/installed-development-adjudication-v1.md>).
- The simultaneous Q4-J2/native-fibre chart-rebase source and installed
  checks passed for a small-angle, three-increment, two-stiffener history.
  Finite-angle sensitivity, S3, broader F06/V18/G3 and different-family
  acceptance remain open. [Evidence](../../.development/f06-j2-fibre-chart-20261008/evidence-index-v1.json).
- B2's coarse external compliance comparison remains failed/not converged;
  the continuum-versus-plate/beam idealization is unresolved. It is separate
  from the principal GE connection decision. Other G2–G6 mechanics, scale,
  external comparisons, platforms, consumer completion and release remain open.
- B2 selected local member-resultant envelopes now report signed extrema and
  first governing case IDs for requested stations and all six components,
  using complete cases only. Exact-source focused controls passed 21/21;
  an isolated wheel (SHA-256 `2c73683ab355a3b1f2d8c5b172bed1db75db0c2b47c6460f9ba86ae780f69e08`)
  ran the public ten-case physical-footprint batch with one factorization and
  18 requested envelopes. [Receipt and failed first build attempt](../../.development/b2-member-envelope-20261008-artifact/receipt-v2.json).
  The first build failed because sandbox temp was unwritable; the corrected
  task-local-temp build passed. This is B07/F13 experimental development,
  not material, scale, external-accuracy, or aggregate gate acceptance.

## Execution and restart boundaries

No owned numerical job is in flight. V11 and V12 each completed one distinct,
bounded development attempt; their unused time does not authorize another
question. V5–V10 and older closed one-use evidence remain unchanged. The
historical body retry is pending, formal F03 unconsumed, and protected
`us3-modal-canary` material must not be inspected or copied. For current
bounded diagnostics, use one numerical job, CPU0, one thread, JIT disabled,
2 GiB and the case-specific process/cumulative limits. Preserve exact
receipts and failures. The user's prospective approval supports needed work
within these contracts; it does not relax scientific criteria or publish a
partial release.

Mistral/local workers were unavailable for this task; Astra directly owned
the tightly coupled physical diagnostics and their Git integration. Do not
communicate with the separate contact worker. On resumption, verify actual
Git and process state, read this note and the relevant evidence only, then
advance the off-common trace-space decision while independent capability work
continues where prerequisites permit. Do not rerun passed campaigns merely
to reconstruct their accounting.
