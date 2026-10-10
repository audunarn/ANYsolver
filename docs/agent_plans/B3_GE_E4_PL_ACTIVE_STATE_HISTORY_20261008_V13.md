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

BL5 remains the Revision 8 physical modelling target; its final connection
law and multiplier policy remain **unaccepted and unqualified**.
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

The fixed-beam, fixed-80-row 16×8×4 C3D20 screen is now resolved at three
separate shell directions. Doubling thickness cells changed work by `+0.1041%`,
doubling transverse cells by `+0.4354%`, and doubling axial cells by `+1.3122%`.
All final runs passed the unchanged physical checks; the thickness
global-wrench result was close to its bound (`9.51e-9` versus `1e-8`). Its
first guard failure and the explicit failed-control diagnostic are preserved.
[Results and receipts](../../.development/bl5-mx-shell-single-axis-20261008-results.md).
The changes are separate and non-additive; axial shell resolution materially
contributes to the earlier ~2.5% matched-level resolved-work shift. **Next**
hold the shell fixed and change beam/interface resolution together under the
declared material trace rule, then compare supported local transfer as well
as work. If both domains converge with a persistent difference, inspect the
continuous native/solid work map. Do not infer BL5 fidelity or select P0
from these one-axis development screens. F03 remains unconsumed and G0/G1
acceptance open.

That fixed-shell beam/interface discriminator also completed. Refine the
resolved beam from 16×8×4 to 32×8×4 while growing exact physical P0 rows
80→160: work changes `−0.63016%`. Holding the *refined* beam fixed and
aggregating pairs of fine segment-integrated rows back to 80 isolates row
resolution: work rises `+0.74836%` relative to 160 rows. Thus beam refinement
at 80 rows alone changes work `+0.11348%`, while 80→160 rows on the same beam
changes it `−0.74280%`. All bounded equilibrium/work/wrench controls passed.
[Results](../../.development/bl5-mx-interface-resolution-20261008-results.md).
This makes interface resolution a material finite-grid response variable,
not a selected P0 policy: extra rows could reduce under-enforcement or cause
locking. Next compare supported local traction/couple work, continuous gaps,
shear/drilling and unresolved modes for these exact two spaces before any
further loaded refinement or formal F03. Preserve the previous failed
thickness attempts and all protected evidence.

The supported same-body local comparison is complete. At fixed 16×8×4
resolved shell and 32×8×4 beam, 80 rows leave a maximum `1.10e-6` fine
segment-mean slope-y gap and up to `2.59e-6 J` segment constraint work that
cancels in paired rows. The 160-row over-resolution control closes those
segment means but its beam-side segment Mx changes sign across 26 interior
boundaries, versus four for 80 rows; both transfer `−10 N·m` in total and
pass KKT/work/wrench checks. [Exact evidence and interpretation](../../.development/bl5-mx-local-transfer-20261008-v1/results.md).
The 160-row supports are half the local shell-trace length and do not meet
Revision 8's initial `c_lambda=1` P0 support rule. Keep 160 as a checkerboard/
over-resolution control; do not select it from smaller gaps. The 80-row rule
matches that support length here but remains unqualified. Stop this loaded
refinement sequence. Next distinguish acceptable weak-line compliance from a
prohibited local motion using a physically matched torque/shear reference,
then develop and independently review the positive norm and actual mixed-system
stability contract for the coherent support rule and controls. Formal F03 remains
unconsumed; G0/G1/M2 acceptance remains open.

Prospective next reference slice: on the already executed matched 8×4×2
C3D20 shell/bar geometry, compare the same 40 physical weak-P0 rows with a
new 45-row, nine-station *strongly sampled* five-channel material-line hinge.
Use the same shell root and area-dual section actions Mx=10 N·m and Fy=100 N;
the strong rows tie three positions and two thickness-director tilts and add
no normal-spin row. First check independent sparse KKT rank, equations,
force/moment/work, work-dual load pairing and local gaps. A passing bounded
operator permits one pinned CalculiX strong-hinge deck per load; a rank,
chart, row, or load mismatch is repaired before external execution. Compare
strong/weak port compliance and local transfer only as development evidence:
the solid thickness secant and section port approximate native director and
B3-GE pose, and a single resolution cannot establish convergence or BL5
fidelity. No finite-area weld substitution, formal F03 use, or line-law
selection follows this slice.

This slice is now executed as development evidence. The same-body weak-P0
versus nine-station sampled-strong KKT solve passed its work/wrench/cross-work
checks; the 45-row strong CalculiX Fy/Mx decks both completed one accepted
increment and agree with independent physical-row KKT displacements within
`5.24e-11`/`1.91e-10`. Strong enforcement changes work relative to weak P0 by
`−1.9921%` (Fy) and `−0.3404%` (Mx) on this grid. It isolates a discrete
enforcement effect, not connection-law fidelity or convergence. The physical
strong-row gaps and corrected support wrenches pass; raw root `RF` omits the
constraint force. [Exact results and receipts](../../.development/bl5-ccx-strong-hinge-20261008-v1/results.md).
The strong station rows and weak P0 integral rows are not nested; station
closure cannot prove continuous gap closure between quadratic C3D20 nodes.
The saved supported 2:1 Fy/rotation mode already has nonzero continuous gap,
actual work-transpose parity and positive physical energy; do not reconstruct
it again. Next compare a physically matched supported off-ratio hinge with
the saved weak mode, including local traction/couple work and port response,
then decide whether one coherent full-channel interface-resolution rule is
needed. A single-grid external parity does not select a law, start F03, or
justify another classical axial refinement. Independent read-only review
found no concrete source/evidence defect and flagged the non-nested trace
limit plus a minor future deck-builder identity guard; the current executed
inputs are bound by exact hashes.

Saved-output reconstruction of the executed nine-station C3D20 hinge shows
station gaps below `1.4e-19`, but between-station director-slope-y reaches
`1.22e-6` under Fy and `2.97e-6` under Mx. Three-point Gauss samples also
show RMS `4.16e-7`/`1.02e-6` in that channel. [Pinned result](../../.development/bl5-ccx-strong-hinge-interior-gap-20261008-v1/results.md).
Thus the nine-station proxy is not a continuous bond on its own quadratic
trace. Before an off-ratio external comparison, test a single exact discrete
quadratic-trace construction on the same body: five channels at 17 endpoints
and midpoints, 85 rows. Independent KKT pivot/work/wrench/gap checks decide
whether to execute two pinned external decks. The outcomes decide whether the
nine-station reference can be used for port behavior only or must be replaced
for both port and local-transfer comparisons. No multiplier selection follows.

The 85-row exact-discrete-quadratic construction has now passed same-body
physical KKT and two pinned CalculiX Fy/Mx comparisons. Its unique physical
pivots have condition `33.36`; external all-node displacement parity is
`1.04e-10`/`2.02e-10`; independent and executed interior five-channel gaps
are at numerical zero. Relative to nine-station sampling, complete-trace work
drops `0.3620%` (Fy) and `1.2455%` (Mx); relative to 40 weak-P0 rows, it is
`2.3468%`/`1.5816%` lower. The saved native Mx work is `2.4714%` above this
solid value, but body/root/end-work idealizations remain different, so the
ratio does not allocate connection error. [Executed result and independent
review limit](../../.development/bl5-ccx-quadratic-trace-20261008-v1/results.md).
Direct row reconstruction shows the 40 weak-P0 integral rows are Simpson
combinations of the 85 exact-trace rows (relative error `9.73e-16`, rank 40);
all 45 sampled rows are exact selections (rank 45). This is same-body
discrete row-space containment, not native stability or fidelity.
This closes the *discrete C3D20 centerline* reference construction on one
grid, not the native law, finite-width transfer, convergence, F03 or M2.
Use it for the next supported local transfer comparison only after matching
the off-ratio physical geometry/load/support contract; do not run another
classical axial sweep. The exact row-space and physical norm/mixed-system
obligations remain before multiplier selection.

The next C1 off-ratio physical reference cannot be obtained by relabeling
historical F5: its terminal bond shares plate/bar nodes and has 89,861 nodes
(269,583 displacement DOFs), above the current diagnostic row envelope.
A bounded factor-2 C3D20R **detached** preflight instead produced 5,498
nodes/16,494 displacement DOFs, zero shared interface nodes, the same gross
35 mm plate/67.5 mm beam-axis geometry and left/root supports, and a balanced
100 N·m Mx end-face action. [Exact preflight](../../.development/bl5-c1-detached-feasibility-20261008-v1/results.md).
It is not yet a physical comparison: its legacy straight beam axis omits
the saved 2 µm C1 tangent transition, and it has no terminal five-channel
line equations or matched Fy action. Implement those three changes on this
compact detached geometry, establish stress-free reference and independent
work/wrench parity, then execute one matched screen if the physical contract
holds. A factor-2 screen cannot establish convergence or select a multiplier
space; do not spend formal F03 authority or broaden resource limits here.

The three preparation changes are now present in an unqualified compact C1
deck pair: the actual x=825 mm bar mesh has the 2 µm tangent-axis lift,
25 drill-free centerline rows over x=.9–1 m have measured initial gap
1.11e-16 and full row rank, and area-dual Fy plus retained Mx end actions
have balanced wrenches. The latest deck equations use an equivalent pivot-isolated
basis, audited against the physical row space.
[Versioned preparation](../../.development/bl5-c1-line-reference-20261008-v5/results.md).
The prepared reference alone was not a response comparison. The independent
C3D20R KKT and pinned external comparisons below followed its checks.

That independent reduced-integration KKT/deck check now passed both Fy and Mx
on the compact C1 model with one factorization: 16,494 physical DOFs,
25 multiplier rows, 726 supported DOFs, positive element Jacobians,
common-rigid-motion gaps ≤2.23e-16, equilibrium/work/force/moment checks
below registered development limits and Fy/Mx reciprocity 1.20e-10.
[Exact result](../../.development/bl5-c1-kkt-20261008-v1/results.md).
That first KKT result was not external parity or native connection accuracy.
The subsequent exact-deck correction and external comparison are recorded below.

The exact C1 development comparison now passes on the corrected V7 decks.
Pinned CalculiX 2.23 completed Fy/Mx; binary64 U/RF versus the independently
assembled C3D20R KKT differs by at most 2.17e-9/5.45e-9 relative to each
case's peak displacement, with support reactions, work, balance and reciprocity
inside the declared development limits. The first sandbox launch failed at
process creation; an unsandboxed Fy succeeded while Mx exposed roundoff
`*CLOAD` entries; the next successful solves had ASCII output inadequate for
pointwise parity. All failed/superseded receipts and original bytes are
preserved. [Final exact comparison](../../.development/bl5-c1-ccx-20261008-v4/results.md).
This is a **one-grid detached solid centerline-hinge implementation check**,
not equivalence to the native E4-PL/B3-GE trace, a finite-width weld, mesh
convergence or F03. Next use this now-trusted physical reference to compare
the disputed native off-ratio force/rotation transfer under explicitly
matched supports/loads and to decide whether the law or discrete resolution
needs revision. Do not infer that result from the parity numbers alone.

The saved x8/B3-14 supported Fy case and compact C1 solid proxy both apply
a +100 N resultant at the x=1 m, z=.0675 m beam end and fix the left plate
plus beam root. Their applied works are respectively 4.40575e-5 J and
5.21613e-5 J (native/solid 0.84464). **This is not a BL5 accuracy comparison.**
The saved native case has 44 *six-channel selective-Fz* material-line rows;
the solid proxy has 25 drill-free five-channel terminal rows. Native E4/B3
also uses a section-port force and root pose, while C3D20R uses area-dual
end-face traction and a clamped root face. Body discretizations differ.
First establish the five-channel native C1 work map on this off-ratio body,
or a proven common subspace, before using the solid result as a physical
comparator. Then compare supported transfer and port fields and a same-body
enforcement contrast. The 15.5% difference cannot allocate law, resolution
or body error. The historical F5 shared-node weld remains separate.

**Immediate bounded native decision (development only).** On the exact
x8/B3-14 C1 body, replace the historical six-channel rows with the declared
BL5 five-channel local work and compare four-cell P0 with continuous P1 over
the same four half-cells, supports and Fy/Mx end wrenches. If P1 materially
changes work and physical transfer, discrete resolution is an active source
of the discrepancy; if it does not, body/traction/root and continuous-law
differences need priority. Either result still needs the seven ratios,
growing spaces, matched physical references and mixed-system F03 contract.

The bounded five-channel same-body attempt completed: 20-row P0 and 25-row
continuous P1 on the unchanged x8/B3-14 operator passed equilibrium, weak
compatibility, work and physical-wrench checks. P1/P0 applied work is
0.985295 (Fy) and 0.995628 (Mx), while Mx shell-side transferred Fy is
29.5480 versus 25.1746 N. These spaces are not nested, so this is a local
space-sensitivity result, not monotone convergence or multiplier selection.
The first result misnames all 1,512 primal coordinates `physical_dofs`;
1,344 are physical nodal and 168 are native retained. A separate read-only
review found no mechanics/row defect and noted that thread/JIT settings were
requested rather than observed inside the child. [Exact evidence](../../.development/bl5-c1-native-fivechannel-20261008-v1/results.md).
The next decision now needs a matched body/end-work/root comparison with
physical transfer observables; another isolated P0/P1 solve cannot allocate
the remaining difference. F03, seven ratios and physical accuracy stay open.

Before another loaded external model, one cheaper work-map discriminator will
compare the native BL5 trace with the executed solid hinge on the same
five terminal stations. Prescribe common low-order shell/beam translations,
director tilts and rigid fields, and check the five gaps and their virtual
work after the known sign reversal. A mismatch means the solid hinge is not
an oracle even on that shared subspace and the offending physical channel
must be identified. Agreement permits only low-order work comparisons;
broken native half-cell modes, body/traction/root effects and physical
accuracy remain separate.

That common-field check passed 11 prescribed modes on the exact C1 terminal
stations: the largest five-channel gap difference was 2.71e-16 after
normalization by 1e-5 m/1e-4 rad, and the largest virtual-work difference
was 2.71e-20 J. Six fields respect both roots; five explicitly test the
unsupported local/rigid kinematics. A separate read-only review found no
concrete sign, slot or geometry error. [Exact evidence](../../.development/bl5-c1-common-work-20261008-v1/results.md).
Thus the solid hinge is a defensible low-order work reference for these
fields, but no arbitrary broken-trace or loaded equivalence follows. Prioritize
the body/end-traction/root match and the supported local-transfer observables
over another isolated basis or classical refinement. Do not select P0/P1 or
advance F03 from this bridge.

Next bounded load-map check: the common-field bridge established interface
work, while the native terminal section action and C3D20 end-face tractions
still differ in representation. On the same saved C1 decks, pair both load
maps with the six root-admissible common virtual fields and report five
unsupported controls separately. A mismatch on supported fields requires
correcting the end-work comparison before another loaded solve; a match only
excludes a low-order load-map discrepancy and directs attention to warping,
body, root, and local transfer. This is one source-level development run,
not a new external solve, formal F03 assessment, or physical qualification.
That check is complete with an added root-admissible beam-roll ramp, needed
to excite Mx. The saved face traction and native section port do identical
low-order virtual work: `0.001 J` under the Fy-exciting beam lateral ramp and
`0.01 J` under the Mx-exciting roll ramp. The largest supported difference is
`5.37e-18 J`; actual CPU0/JIT-off/one-thread settings were observed.
[V5 result and preserved V1–V4 limitations](../../.development/bl5-c1-load-work-20261008-v5/results.md).
This removes low-order end-load work mismatch, not arbitrary face-warping
or root/body discrepancy. Next measure supported local transfer and warping
work under a physically matched root/end contract, using saved response
before considering any new solve. No P0/P1 or F03 decision follows.

The saved native C1 P0 response has a maximum lateral line gap of
`1.16e-8 m` under Fy and `1.03e-7 m` under Mx, whereas the terminal solid
reference uses five strong stations and closes its quadratic five-channel
trace on those two solid axial cells. This confounds enforcement resolution
with body/root/warping in the loaded comparison. One bounded same-solid-body
P0 counterfactual will integrate the exact five-channel quadratic trace over
the four terminal half-cell intervals and solve the two saved loads with the
same C3D20R stiffness, root, and face traction. If solid P0 versus strong
work changes materially, quantify enforcement's finite-grid contribution;
if it does not, prioritize body/root/warping. Either outcome remains a
development diagnosis, not physical accuracy or multiplier selection. Keep
formal F03 and external execution untouched.
The same-solid counterfactual now passes its source KKT controls. P0 raises
solid Fy/Mx work by only `0.0920%`/`0.1499%` relative to strong rows, while
native P0 remains `7.61%`/`2.05%` below solid P0 on this C1 grid.
[Exact result and failed V1 rank-check attempt](../../.development/bl5-c1-solid-p0-20261008-v2/results.md).
This rules out the **solid strong-to-P0 enforcement change alone** as the
dominant loaded-work explanation. It does not allocate the remainder to
body/root/face warping or prove native/solid continuous-law equivalence.
Next inspect common supported local transfer and warping-sensitive end
fields on saved responses; a new external solve is not justified by this
counterfactual. A separate read-only review found no concrete row or solve
defect; it identified unasserted physical edge connectivity and absent
per-domain interface transfer as the limits of stronger claims. That review
is not formal independent mechanics acceptance. F03 and all acceptance gates
remain open.

Source inspection found that the saved native and solid result JSON records
omit complete primal solutions and multiplier vectors. Recover them through
bounded re-solves of the unchanged source KKT systems; no new external deck
is needed.
The native P0 rows are interval *integrals*, while the solid P0 rows are
interval *means* over `0.025 m`. Compare interval-integrated physical
tractions/couples and shell/beam virtual work after this dual scaling and
the declared frame/sign maps; raw multiplier values are not comparable.
The preceding one-use diagnostic authority is closed, so this reconstruction
requires its own bounded development execution record. It cannot select
P0, allocate the remaining work difference, or consume formal F03 authority.
That bounded reconstruction now passed on the unchanged C1 Fy/Mx bodies.
Native and solid P0 total shell-side Fy differ by `2.228 N`/`1.128 N`, but
the sums of absolute four-interval Fy differences are `68.953 N`/`252.278 N`;
under Mx, two terminal intervals even transfer Fy with opposite signs.
The source KKT work, equilibrium, interval dual work and physical-wrench
checks pass, and a review-found solid-coordinate identity guard was repaired
and rerun with identical numerical output. [Exact evidence and limits](../../.development/bl5-c1-interval-transfer-20261008-v3/results.md).
This local contrast makes global resultant or tip-work agreement insufficient
for the connection decision. Distinct bodies, root, end-face warping and trace
remain confounded. The requested one-grid state-preserving field comparison is
now complete. Under Mx, the native axis-to-bottom-face mapping yields 78.8-91.7
nm one-sided jumps at four bonded stations, and individual native-side versus
solid-bottom differences of 43.8-48.7 nm; prebond differences reach 172.9 nm.
Under Fy, bonded side differences are 13.8-18.8 nm. The smaller native-side
*mean* difference is not a physical trace or evidence of sidewise agreement.
The [V4 result and failed-attempt inventory](../../.development/bl5-c1-supported-fields-20261008-v4/results.md)
bind the saved states, fixture/port source and raw physical fields. The bounded
sequence establishes a representation distinction, not causal allocation or
connection selection. Stop this C1 field sequence. The next substantive
experiment needs a declared common bond, matched body/root/end loading and a
supported side-sensitive work/traction observable whose outcomes distinguish
continuous-law deficiency from discrete resolution; specify this before
another solve. Formal F03 stays unconsumed and G0B/M2 acceptance remains open.
The supplementary saved-state [face-node audit](../../.development/bl5-c1-supported-fields-20261008-v5/results.md)
passed on eight stations and two loads without another solve. It binds unique
plate/bar face node IDs, the prebond 2 µm lift, and the V4 sample coordinates;
the solid secant/director and body/root/load interpretation limits remain.

Supporting F03 norm review rechecked the historical broken-port feature:
its rank is 51 on 150 retained beam coordinates, leaving 99 dimensions that
the feature alone cannot norm. A nonzero half-cell jump also has divergent
continuous `H^(1/2)` seminorm. The conditional positive algebraic metric in
the K2 review is not yet a justified physical graph norm, and `|K_rr|` is not
automatically invariant under retained-coordinate basis changes. **Decision:**
do not compute or threshold another BL5 inf-sup quotient yet. First derive
independent positive control of the feature kernel and jumps, with physical
work scaling, unit/basis controls, then assess the signed mixed KKT separately.
The present reviewer is same-model supporting input, not the mandatory
different-family mechanics acceptance. F03 authority remains unconsumed.
Next bounded graph-norm discriminator: on the existing supported 4-shell/8-beam
BL5 fixture, assemble the native virgin mixed kinematic Jacobian `J` and
positive complementary block `C` from the actual 24+18 local contract.
Compare ranks of the independent surface-pose feature alone, feature plus
`J`, and those plus all 18/member resultant directions. Full controlled rank
would permit derivation of a physically weighted graph norm and unit/basis
tests; a remaining kernel identifies the missing kinematic observable.
This is one source-level feasibility check, not a multiplier quotient, formal
F03 execution, or evidence of uniform refinement stability.
The bounded V1 graph-rank result is **invalid**: the probe subtracted a shell
offset from already beam-local element slots, causing negative-index wrap.
Its raw evidence is preserved. Corrected V2 on the same fixture gives ranks
51 (physical feature), 78 (feature plus native compatibility), and 150
(after the 72 independent resultant directions), exactly spanning the
78 kinematic plus 72 force-like coordinates. Four local complementary blocks
are symmetric positive. V1/V2 used 5.5280923 process-wall seconds in total;
effective CPU0, one thread, JIT off and 2 GiB were verified. This establishes
finite-fixture graph observability only. Next decision: derive physical
weights for the trace, compatibility and resultant terms with unit/basis
controls and a different-family mechanics review, then test the signed KKT
and growing interface spaces. Do not infer uniform stability or select a
multiplier basis. [V2 receipt and analysis](../../.development/bl5-graph-norm-feasibility-20261008-v2/results.md);
[V1 invalidation](../../.development/bl5-graph-norm-feasibility-20261008-v1/INVALID_RESULT.md).
A separate bounded check of the same supported virgin-elastic fixture found
the 48-free-DOF shell reference block positive after the owner's coordinate
scaling (minimum eigenvalue 13374.46 versus diagnostic zero floor 2.80e-5,
relative skew 8.41e-17). Together these facts support a finite-fixture graph
form using shell reference energy, a physically weighted six-component broken
beam trace, native compatibility weighted by inverse complementary compliance,
and resultants weighted by complementary compliance. The internal-basis
covariance is algebraic; the trace weight, half-cell jump treatment, unit
controls, other supports/formulations and signed KKT remain unreviewed.
[Shell receipt and candidate mathematical seam](../../.development/bl5-shell-positive-part-20261008-v1/graph_contract_candidate.md).
No physical BL5 law, multiplier space, aggregate gate or F03 threshold follows.
The actual virgin local 42×42 spatial tangent also passed the needed
cross-block work-duality check on all four B3 members: `K_qp=K_pqᵀ`,
zero reported scaled skew and zero reference residual. This supports
the conditional `[[Kqq,Jᵀ],[J,-C]]` expression on this chart only.
Finite rotation, plastic and full signed-KKT checks remain open.
[Exact source diagnostic](../../.development/bl5-native-mixed-dual-20261008-v1/results.md).
A single physically dimensioned six-pose broken-trace/DG candidate now
passes finite-fixture rank, jump-detection and algebraic m/mm/internal-basis
covariance controls. It uses a provisional `W0=1 J`, 864 interior and
126 jump rows; the graph rank remains 150. Its owner-scaled eigenvalue
ratio is about 1.04e-13, with the minimum only 3.1 times the diagnostic
roundoff floor. This is not robust enough for a direct quotient or basis
selection. Derive and independently review the work scale, BL5 dual pairing,
jump/refinement equivalence and a stable inverse action before signed-KKT
and full-ratio F03 assessments. [Exact candidate and limits](../../.development/bl5-broken-graph-candidate-20261008-v1/results.md).
Formal F03 authority remains unconsumed.
A factored-row oracle on the unchanged candidate avoids forming its direct
Gram: smallest singular value 0.119 versus 9.30e-8 numerical zero floor,
row condition 3.10e6, QR backward residual 5.11e-18 and sample forward
error 2.31e-6. The direct-Gram eigenfloor proximity is therefore partly
a representation issue, not a demonstrated physical null mode. The sampled
forward error means the inverse action is not accuracy-qualified by its small
backward residual. Dense QR
is a bounded oracle only; the trace work scale, five-channel dual pairing,
sparse inverse-action accuracy, signed KKT and growing-space behavior
still require review. Stop this finite-fixture numerical sequence here.
[Factored result](../../.development/bl5-broken-graph-factor-20261008-v1/results.md).
BL5's declared bond is a centerline; the 0.1 m transverse trace used in
the first graph candidate is not part of BL5 constraint work. It can remain a
separately justified auxiliary beam norm or surface/footprint diagnostic, but
cannot be treated as an additional BL5 rotational restraint. A bounded source
bridge now proves the centerline six-pose
beam derivative projects exactly to the actual five-channel BL5 beam-side
work at all 22 compiled stations, with zero reported arm/reference gap
error. The centerline graph remains full rank 150 with J and resultants.
**Decision:** use the centerline trace for BL5 work/dual-norm design. A
finite-width contribution to an auxiliary beam norm needs its own physical
scale and refinement argument; the existing width result is diagnostic only.
Six-pose primal observation does not create a sixth BL5 multiplier. The
existing single-support/span-2 test demonstrates that a positive graph norm
can observe free beam yaw that the signed constrained owner rejects; rank
therefore does not establish mixed-system well-posedness. The existing local
test verifies released normal spin about the eccentric attachment point,
including beam-axis translation. It is a local finite-motion check, not a
growing-space stability result. Next derive an explicit five-channel
physical-work and multiplier-norm contract, including the released-spin
annihilator and unit-consistent force/couple density scales; obtain independent
mechanics review before another quotient or formal F03 run.
The physical work scale, shell-side work, refinement equivalence,
signed KKT, multiplier policy and external transfer remain open.
[Centerline bridge](../../.development/bl5-centerline-work-bridge-20261008-v1/results.md).
The [five-channel F03 contract draft](B3_GE_E4_PL_BL5_F03_CONTRACT_DRAFT.md)
records the required work/units, proposed graph and dual norms, and explicit
counterexamples for review. Supporting same-family review found and prompted
corrections to reference measure, graph variables, spectral length, rigid-mode
handling and control definitions. Physical scales, primal/dual comparability,
supported positivity, numerical floors and different-family mechanics review
remain open. The draft does not adopt a metric or consume F03 authority.
The existing M2 independent reference norm uses cell-constant directors in
L2. A supporting review supplied an alternating-director counterexample:
the provisional DG jump penalty grows like `h^-2` relative to that reference.
**Decision:** remove jump penalization from the prospective native positive
graph; keep jump amplitude diagnostic, with the signed KKT assessed separately.
The bounded no-jump centerline run retained ranks `51/78/150` for trace,
trace+native compatibility and complete graph on the unchanged 150-coordinate
fixture. This keeps the no-jump candidate alive without repairing a rank loss.
It does not establish uniform equivalence to the existing M2 reference norm,
positive inverse accuracy, signed KKT stability or physical transfer.
The 4/8/16-half-cell alternating-director check now resolves that next
question. Against the old `h_B=.1625 m²`, the physically scaled no-jump trace
ratio is `1.000` at all three levels; adding native `J^T C_p^-1 J` raises
the graph/reference ratio `3.878 -> 6.832 -> 18.647`. The full native
energy graph is **not** the prospective F03 primal norm. The BL5 local port
uses only two nodal translation vectors and one cell rotation vector, so restrict the
interface inf-sup to actual trace-active shell/beam kinematics and the
existing independent `h_B+h_S`/`M_ref` spaces. Keep all inactive native
variables in the separate full signed-KKT and physical-response assessment.
This is a prospective numerical-contract correction, not a change to BL5
physics or any frozen F03 predicate. Source inspection confirms the current
isolated BL5 line assembly uses 21 local slots (12 shell, nine beam) in both
reference and finite-chart paths; current fixed supports only select columns.
This does not cover mixed attachments or future affine support coupling.
The new isolated Q4/BL5 P0 and discontinuous-P1 assembled-column controls
passed 2/2: inactive native beam columns remain exactly zero after current
coordinate-selection supports. The process used `4.186353 s`; cumulative
graph-development use is `29.0652932/105 s`, retaining 60 s. This does not
cover S3, mixed attachments, future affine support maps, positive norm or
signed-KKT stability. [Evidence](../../.development/bl5-active-slots-20261008-v1/results.md).
Verify the broader supported work maps and independently review the restricted
norm before formal F03. The [no-jump rank](../../.development/bl5-centerline-no-jump-20261008-v1/results.md)
and [weak-director result](../../.development/bl5-cell-director-norm-20261008-v1/results.md)
remain separate development evidence. Formal F03 remains unconsumed.

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
- The saved simultaneous all-S3-J2/native-fibre unload prefix now has a
  focused source-level chart-rebase, checkpoint-restore and signed-continuation
  PASS. Direct, rebased and reopened owners completed the same three remaining
  targets and four accepted steps; maximum free-equilibrium ratio was
  `2.054e-12`. Physical poses, resultants, reactions and material states passed
  the established Q4-J2/fibre `1e-9` scaled comparison. Rebased and reopened
  owners retained byte-exact same-chart checkpoint identity; accepted material
  origins did not change during rebase. Four preceding test-comparison failures
  remain preserved, including the first exact cross-chart amplitude difference
  of `3.84e-12`. Source check V5 consumed `18.407047` process-wall seconds;
  cumulative use of its `180`-second allowance is `101.6246682` seconds, with
  `60` reserved. An isolated installed wheel at source `bad4c84d` then passed
  the same scenario 1/1; all 627 installed Python modules match source and
  wheel. The first packaging attempt timed out before testing and remains
  failed evidence. Combined build/install/test attempts used `65.0774029/180 s`,
  retaining the 60 s reserve. Finite-angle sensitivity, broader F06/V18/G3
  and independent acceptance remain open.
  [Source evidence](../../.development/f06-s3-fibre-chart-20261008-v5/results.md)
  and [installed evidence](../../.development/f06-s3-fibre-chart-20261008-installed-v2/results.md).
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
