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

Reuse the already reconstructed **2:1 x8/B3-14 Fy/rotation mode** for that
decision. Historical saved-state checks found a nonzero continuous six-channel
gap, actual L1 work-transpose parity, positive shell/native physical energy,
and substantial unresolved twist under some fixed spaces; they did not find a
sign defect or qualify a multiplier basis. The corrected same-virgin-field
L1/finite-patch comparison attributes their difference to signed shell virtual
work, mainly pitch, without proving a loaded response or physical fidelity.
[Saved projection and limits](<C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/.qualification/b3-ge-e4-pl/r7-f03-fy-saved-projection-dev-20260929-v1/manifest.md>)
and the [historical decision](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_R8_20260929.md)
therefore replace another reconstruction or refinement. The discriminating
next work is a matched physical bond/reference declaration with local slip and
traction/couple work, followed by the justified growing-space norm and mixed
system check. Do not infer the connection law from either saved quotient.

Before reusing the saved 2:1 trace comparison, check its frozen total action
and native beam work at every station. A pass permits using its *signed
virtual-work difference* to design a matched physical reference; a failure
requires repairing the diagnostic before interpreting that difference. This
single saved-state check does not consume formal F03 authority or select a law.
The first CPU0/JIT-off development attempt timed out at its 30-second cap
without output or a guard finding. Preserve its receipt; one 120-second retry
with the same source/input will distinguish preparation cost from a failed
invariant. A second timeout ends this guard-check route for now.
That versioned retry passed in 38.998 seconds on the frozen input. L1 total
work differs from the frozen mean-row action by `1.94e-16 J`; native beam work
agrees at all 16 stations, with zero reported maximum station difference.
Two observed OpenBLAS pools each used one thread, and sampled process-tree RSS
remained below 244 MB. [Failed attempt](../../.development/bl5-saved-work-guard-20261008-v1/receipt.json)
and [passing receipt](../../.development/bl5-saved-work-guard-20261008-v2/receipt.json)
retain exact source/input/output hashes. This removes a possible bookkeeping
explanation for the saved shell-work contrast, not the physical bond-fidelity
uncertainty. The next discriminator is the declared same-action local-slip and
traction/couple-work reference; no further reconstruction is needed.

Next bounded BL5 decision: reuse the already executed, geometrically matched
Fy/Mx C3D20 weak-P0 and native cases. Recover pointwise five-channel gaps and
signed/absolute multiplier work at the same Gauss stations, checking each
side's integrated work against its assembled rows. If local slip is material
despite weak-row closure, investigate one coherent interface-resolution rule
before attributing the tip-response difference to body mechanics. If local
slip is small on both sides, prioritize the known body/traction/root mismatch.
A work-transpose or geometry mismatch invalidates this comparison and requires
repair. This is saved external output plus bounded native development solves,
not a new CalculiX run or formal F03 assessment. Cached worker unavailability
and the coupled physical-contract interpretation keep this slice with Astra.
The first saved-output recovery attempt failed a near-zero signed-work parity
check that used the cancelled signed value as its scale. Preserve the failure;
the revised check uses absolute local station-work contributions as its scale.
One repair attempt remains within this 150-second development allowance, with
the same physical inputs and no changed scientific acceptance threshold.
The corrected v2 completed; v3 added an independent-multiplier check and
passed on both saved loads. At the same eight Gauss stations, native versus
resolved director-gap RMS is `3.08e-6`/`2.31e-7` for Fy and
`6.85e-6`/`7.15e-7` for Mx. Absolute cancelling local work divided by applied
work is `4.91%`/`0.73%` for Fy and `10.86%`/`1.85%` for Mx. Both assembled
weak-row works remain approximately zero. The [bounded result](../../.development/bl5-saved-local-transfer-20261008-v3/results.md)
does not allocate body/traction/connection error. It justifies one complete
five-channel P1 screen on the unchanged native body for both loads; it does
not select P1 or replace the required 2:1 and full-ratio assessment.
The first P1 script attempt used a basis excluded by the native-fibre owner;
its admission failure is preserved. The admitted five-channel P1-coarse
candidate then passed the bounded same-body screen: 25 rows against P0's 20,
identical shell/beam operator and supports, and reconstructed weak work.
Fy P1/P0 position and director gaps are 0.597/0.864; Mx gaps are 0.979/0.977.
Absolute local-work ratios are 0.340/0.619; applied-work ratios are
0.9624/0.9658. [Result](../../.development/bl5-p1-native-screen-20261008-v2/results.md).
Thus resolution matters for Fy but does not explain most Mx local slip.
Stop this isolated basis contrast. Next distinguish body, end traction, root
and connection using a physically matched work-conjugate reference; do not
promote P1 from smaller local work. F03, M2 and full ratios remain open.

Next bounded Mx body discriminator: retain the exact saved C3D20 beam body,
section geometry and 10 N m resultant. The earlier beam-only native/resolved
ratio `1.13594` confounds full-face root clamp with one-section pose restraint
and end-face traction with a section moment. Construct an area-L2 projection
of each resolved end face onto six rigid section modes; verify its rigid-motion
identity and work dual. Cross saved traction/section-dual torque with full-face/
section-pose root restraint in four beam-only solves from one unchanged body.
If the ratio changes materially, those boundary work definitions explain part
of the existing body difference and must be matched before judging BL5. If it
does not, examine body kinematics/section idealization. A rank, work, or wrench
failure invalidates the experiment. This is one saved-input development batch,
not a new CalculiX solve, F03 assessment, or connection qualification.
The section-port contrast passed in its third, strongest saved-input attempt.
Saved traction and section-dual load differ by only `6.77e-16` relative L2;
the end load is therefore already work matched on this fixture. Replacing the
full-face root clamp with six area-L2 pose constraints raises resolved work
from `0.001449918650` to `0.001474597704 J`, while native beam-only work is
`0.001647014034 J`. Native work matches the prismatic Saint-Venant `M²L/GJ`
prediction to roundoff; resolved port-root work is `10.47%` below it.
[Result](../../.development/bl5-mx-section-port-20261008-v3/results.md).
Root warping restraint explains only a small part of the old body contrast.
Next perform one same-port C3D20 torsion refinement series to distinguish
coarse solid discretization from a port/body idealization mismatch. Preserve
the old loaded BL5 and F03 decisions until a converged physical reference
exists; no new connection law or multiplier policy follows from this result.
The same-port C3D20 beam-only refinement passed 2×2×1, 4×4×2 and 8×8×4.
Work relative to analytical Saint-Venant changes from `-10.47%` to `-1.17%`
to `+0.14%`; the coarse operator and ports independently match the earlier
assembly. [Exact three-level receipt](../../.development/bl5-mx-torsion-refinement-20261008-v1/receipt.json).
This strongly identifies coarse resolved beam discretization as a body
comparator limitation, without proving the full coupled reference converged.
Next bounded discriminator: hold the old solid shell, 20 weak-P0 rows, 10 N m
load and supports fixed; replace only the resolved beam body/trace by those
three nested meshes. Coarse must reproduce the saved CalculiX work. If the
native/resolved coupled difference collapses, refine the external reference
before judging BL5; if it persists, inspect shell/connection representation
with the body bias controlled. This remains development evidence, not F03.
The fixed-shell coupled comparison passed all three beam levels and exactly
reproduced coarse CalculiX work. Native/resolved Mx work ratios fall from
`1.22489` to `1.12320` to `1.10994` as only the resolved beam is refined.
[Result](../../.development/bl5-mx-coupled-beam-refinement-20261008-v1/results.md).
Thus the coarse solid beam materially contaminated the original connection
comparison, while an approximately 11% difference persists. Next hold that
fine beam, physical weak law and supports fixed while refining only the solid
shell; then decide whether native shell/connection comparison is meaningful.
That fixed-beam shell contrast passed three levels. Native/resolved Mx work
ratios change `1.10994 → 1.02092 → 0.95190` as only the resolved C3D20 shell
is refined; work still moves `7.25%` at the last step. The middle near-match
is not convergence. [Result](../../.development/bl5-mx-coupled-shell-refinement-20261008-v1/results.md).
The physical decision is now clear: neither the original coarse CalculiX body
nor an isolated refined level can qualify BL5. Stop component-by-component
refinement. Next construct one matched native/resolved reference series with
both bodies and the five-channel interface resolution growing under the same
geometry, root, offsets, loads and physical work maps. Audit old native
refinement fixture root/line policies before reuse. G0/F03/M2 remain open;
historical failures and formal authority are unchanged.
One bounded matched refinement will now compare native Q4/physical-fibre B3
and the independent C3D20 shell/bar on the same 1 m geometry. Use 4×2,
8×4 and 16×8 shell surface grids, corresponding native half-cell counts,
solid thickness refinements, and one five-channel P0 multiplier interval per
beam half-cell on both sides. Freeze material, section, offset, shell-root
restraint and section-dual Mx load. The coarse native definition must equal
the saved one; the coarse solid assembly uses the independently checked
C3D20 operators. If both responses and connection work approach a stable
common limit, advance the registered ratios and external execution. If a
persistent matched difference remains, inspect the exact physical work maps
and BL5 law; if convergence is unsettled, do not choose a basis from this
sequence. This is a development discriminator, not formal F03 or a replacement
for executed external reference acceptance.
The matched native/C3D20 P0 Mx screen passed 4×2, 8×4 and 16×8 surfaces
with matching body/interface refinement. Native/resolved work ratios are
`1.11311 → 1.00851 → 0.98283`. Native work moves below `0.1%` between the
last two levels, while resolved work still moves about `2.5%` and the ratio
crosses unity. [Result](../../.development/bl5-mx-matched-refinement-20261008-v1/results.md).
This rejects the coarse or middle-level tip response as a BL5 fidelity
decision; it does not reject the continuous law. Next prepare one executed
finer matched external deck with exact weak-row, root and section-torque work
and a resolved-shell convergence check. Do not spend formal F03 authority or
select P0 from these linear development results. No broad refinement sweep.
Immediate external smoke comparison: use the matched 8×4×2 solid model and
its 40 exact five-channel P0 rows, same shell root and area-dual Mx traction.
Row-reduce only for CalculiX `*EQUATION` elimination and prove the serialized
rows span the original constraints; bind the independent sparse KKT result.
Execute the pinned CalculiX binary once under the existing one-job CPU0,
thread/JIT and memory/time ceilings, then parse DOUBLE U/RF and check all-node
displacements, weak gaps, multipliers, physical support wrench and work.
Parity permits using the independently assembled matched series as a credible
development reference and motivates a still-finer executed case; a row, load,
solver or parser mismatch is repaired before any physical inference. Neither
outcome closes the full external/refinement or F03 gate.

The pinned 8×4×2 CalculiX deck now executed one accepted increment with 40
exact five-channel rows. Parsed DOUBLE U/RF and independently reassembled
physical-row KKT passed every declared development check: relative all-node
displacement `1.803e-9`, scaled weak gap `3.05e-20`, corrected support
comparison `5.98e-9`, and applied work `0.000984473175680 J` versus saved
independent `0.000984473175779 J`. The first sandboxed CalculiX launch failed
before process creation (`WinError 623`); its evidence remains intact. The
successful new attempt and [complete result](../../.development/bl5-ccx-matched-mx-8x4x2-20261008-v2/results.md)
establish same-law external parity at this resolution, not native accuracy.
The matched resolved work still moves about 2.5% between 8×4×2 and 16×8×4.
Next distinguish resolved-shell discretization from beam/interface change by
one bounded shell-only refinement at fixed 16×8×4 beam and 80-row action,
using the existing indexed operators. Its possible outcomes are: substantial
work movement → refine/qualify the physical reference; stable work but a
persistent native difference → inspect connection/body work maps. No automatic
broader sweep, F03 assessment or line-law selection follows this parity.

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
