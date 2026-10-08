# Active development — 8 October 2026

The scoped S3 V2D elastic recovery fix is now a separate **draft PR #65**
against common main: `codex/s3-v2d-surface-recovery` at `974f283a`, based on
`cff55d95`. Its three product/test files are byte-identical to the installed
verified development candidate (`552401b9`). The clean sparse checkout is
`C:/Github/ANYsolver/.perf2-worktrees/s3-v2d-recovery-main`. CI was queued
at PR creation; do not describe it as passing before results are inspected.
This extraction excludes BL5 diagnostics and qualification evidence. Main was
not edited or merged; package publication remains separate.

BL5 source review has now proved that V4's slot 55 is the vertical C3D20
midside node's y displacement. Its shape vanishes exactly on both sampled
beam faces, so its analytical weak-P0 interface column and end-traction load
are structural zeros, independent of multipliers. The old 3.5665e-16 N load
arose in floating face interpolation. A candidate exact-face coordinate
correction and source-only regression now pass for the three top tiny-load
rows, slots 55/58/130 (3 passed, 9 deselected).
This does not repair the saved 9.1302e-13 N high-precision equilibrium
residual or reopen the CLOSED V4 ledger. V4 remains FAILED; no numerical
retry, active-row criterion change, F03 execution, or Fz body retry occurred.
The next solved comparison needs separately valid authority. Astra handled
this reserved source/mechanics decision directly while the recorded Mistral
and local workers remain unavailable for this task.
Main and origin/main still point to `cff55d95`; the main checkout has unrelated
untracked work and was not edited.

Current independent product slice: default elastic S3 V2D recovery now has a
candidate local physical surface-stress mapping for exact isotropic Material,
using its existing N/M/Q resultants and the same top/bottom von Mises convention
as Q4. Generalized sections remain resultants-only. Mixed Q4/S3 public
prescribed-displacement recovery, nonzero bending/shear tensor agreement, and
public committed-state isolation pass 11 focused source tests. Supporting
read-only review found no concrete defect; its consequential coverage requests
were added and passed. Full affected historical file recorded 19 PASS / 1 unrelated
FAIL: its frozen pre-default-activation assertion still expects `legacy-s3`.
Do not change that historical boundary to obtain a pass. Raw source receipts
are in `.development/s3-v2d-surface-recovery-20261008/`. An isolated wheel from
`552401b9` passed a public mixed Q4/S3 installed recovery probe; all 627 Python
modules match source/wheel/site byte-for-byte. Wheel SHA-256 is `07f20642...6ed4d2`.
Cross-platform/consumer and mandatory programme review remain pending. This is an experimental
recovery addition, not G0/G1 or full-programme acceptance. Direct OpenAI edit
uses the already recorded Mistral/local unavailability for this task.

Read-only consumer review found a static packet blocker in the unrun ANYfem
common-main installed packet: its supervisor expects 431 solver Python files,
while its frozen artifact and entry require 627. The packet remains PENDING,
zero attempts; repair and re-freeze before any activation. No sibling edits or
numerical attempt were made for that packet in this slice.

Mz common-density beam-only branch stopped FAILED, without a validated body
comparison. V1 native calculation failed the unchanged active-row equilibrium
check (ratio 3.253606). V2 found a reflection-search bookkeeping defect.
V3 proved the actual discrete reflection of K/C/load/supports and retained
the original equilibrium after projecting forbidden density channels, but
the resolved beam failed on a 3.57e-16 N *symmetry-allowed* load. V4's exact
load-sector projection changed zero and repeated that failure (ratio
2559.993319). No magnitude cutoff, tolerance change or body-law conclusion.
All four attempts, including preflight/calculated data and cumulative
11.6943905 s wall, are in
`.development/bl5-mz-common-beam-20261008/adjudication.md`. The distinct old
Fz shell/body retry remains PENDING and untouched. Further numerical work on
this branch needs focused independent review of load assembly and the strict
active-row assessment; meanwhile advance independent programme work. F03,
M2/G0, external accuracy and release remain open.

Mz density decision: the work-matched native and resolved-continuum five-row
models both exert +1 N m Mz on the shell, but their signed per-edge Fy action
distributions differ. Translation-density difference norm 6.57246 versus
reference 70.89078; director channels differ too and keep separate units.
The previous 1.2418e-6 J beam-dominated work gap therefore cannot be
assigned solely to the body operator. One source-only paired solve passed in
2.8639997 s, CPU0/thread1/JIT-off, sampled RSS 165,920,768 B; see
`.development/bl5-mz-density-20261008/adjudication.md` and raw receipt.
Next discriminator is same-density beam body work; the prior separate
body-port retry remains PENDING and was not run or renewed. No multiplier
selection, external accuracy, formal F03 or M2/G0 acceptance follows.

BL5 Mz development decision: a +1 N m native tip action and a resolved-bar
`t_x=-Mz*y/I_z` traction share the declared five-channel weak material-trace
work on the 1 m specimen. Both exert +1 N m on the shell and balance -1 N m
at the support; equilibrium/gap/body work checks pass. Native tip rotation is
1.88630052e-6 rad versus continuum work-conjugate 6.44524813e-7 rad.
The difference is primarily in beam-side internal work, but different
interface action distributions and body spaces prevent a law-error or
physical-accuracy attribution. Preserve five attempts, including two failed
numerical screens and the corrected exerted-action sign, in
`.development/bl5-mz-work-matched-20261008/`; cumulative wall 12.5824441 s
of 90 s, final CPU0/thread1/JIT-off and peak RSS 165,392,384 B. The original
three-edge probe's `C.T @ lambda` label denotes the algebraic covector; its
physical exerted action is `-C.T @ lambda`, as documented by the new
adjudication. Next: compare beam body/port response under one common physical
interface density before another refinement or external run. F03/M2/G0
remain open. Current-main ANYfem installed verification remains PENDING
distinct authority and unrun.

The human resumed development after PR #63 established common main at
`cff55d95e905ab689efdacdf08742a60614728c1`. Work in the sparse, isolated
`C:/Github/ANYsolver/.perf2-worktrees/stiffened-rev8-20261008` checkout on
`codex/stiffened-rev8-resume`; do not edit main or the older reconciliation
checkout's protected qualification evidence. Mistral/local were already found
unavailable for this task, so OpenAI handled the connected consumer repair and
artifact reconciliation directly.

The experimental ANYfem displacement consumer is at isolated commit
`345db0cb73e7e7683872188b2a5ee4df0fd84b86`. It now rejects a non-JSON
seed-factor tuple before Project canonicalization can turn it into a list.
Frozen source controls passed **53/53** in
`C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/.development/distributing-displacement-consumer-20261008-v9/source-controls-v8`.
The subsequent wheel build and isolated install commands exited zero; wheel and
site receipt exist, but the 30-second `build-install` phase timed out during its
post-install audit. Preserve that outcome as **TIMEOUT**, not a passed installed
gate. Packet v9 charged 269.4988338/360 seconds and retains a 60-second reserve;
no installed controls, public example or affected legacy checks ran. Earlier
pretest dependency-catalog refusals and the one source test failure remain in
the carried ledger; the repaired source result supersedes only the test defect.
The wheel's saved SHA and all 117 isolated site-file hashes match; build and
install subprocesses both exited zero. Installed behavior remains unverified.

The prepared artifact-only packet is
`C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/.development/distributing-displacement-consumer-installed-20261008-v1`.
It is **PENDING** a distinct 240-second authority with 60 seconds reserved; it
binds the v9 source pass and timeout by hash, copies the verified wheel/site,
and admits only 53 installed controls, one public example and 19 affected
legacy controls. Its static source/artifact/runner bindings passed. Do not run
it before the pending authority reply. It does not rewrite or transfer the old
packet's ledger. Its frozen solver wheel predates common main: 22/431 solver
Python files differ at `cff55d95`, including shared nonlinear and arc-length
code. Passing this packet will verify the consumer only against that older
solver artifact. It remains PENDING/unrun and is superseded as the proposed
next check by
`C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/.development/distributing-displacement-consumer-common-main-20261008-v1`.
The latter binds the same consumer wheel/source pass/timeout to the existing
common-main solver wheel `86650929...`, with 627 Python members and all 1,264
installed files frozen; static manifest, source and runner checks passed. Its
solver wheel differs from Git commit `cff55d95` only by CRLF/LF in four named
Python files, recorded in its registration; it is not described as exactly
byte-identical to Git. This changed-artifact 240-second check is PENDING a
separate authority reply, has zero attempts and retains 60 seconds. Do not run
either pending packet before the applicable reply. Complete independent
consumer review before integration.
No F03, E03, body retry, old campaign, release or production qualification is
implied. The programme's G0–G6/F01–F13/V01–V28/B01–B18 obligations remain open.

Physical-reference lane, independent of the pending consumer run: the pinned
CalculiX 2.23 executable used by E02 is present and its recorded SHA-256
matches. E01's saved cross-work review allocates the torque discrepancy mainly
to membrane/normal-spin work, while the later material-frame control shows a
nodal `theta_z` motion changes the six-row point port but leaves the recovered
polar-spin port fixed. Thus an expanded-face material-spin comparison cannot
score the six-row nodal law as the *same* connection. Before another external
solve, define an executable, work-conjugate six-row reference or explicitly
declare a distinct matched footprint/material-spin comparison. A finer axial
mesh does not distinguish those laws. E01 physical accuracy and the connection
decision remain open; no existing comparison is relabeled.

Bounded BL5 development discriminator, independent of the pending consumer
packet: use the existing three-edge cantilever with finite eccentric bond and
apply a pure +1 N m beam-tip moment about the shell normal. Distinguish (a)
finite, balanced transfer through distributed line force with released local
normal spin, (b) an unsupported physical/mechanical mode, and (c) numerical
failure. Record effective runtime, work, equilibrium, global support wrench
and distributed interface action. Outcome (a) advances only to matched physical
reference design; (b) requires a law/support decision; (c) requires numerical
diagnosis. One source development probe, CPU0/thread1/JIT-off, 2 GiB, 60-second
process cap; no formal F03, ratio sweep, tolerance change or acceptance claim.

---

# Common-main consolidation — 8 October 2026

Human authorizes consolidation and coordination with contact task `01a0d278-3e81-77b1-a9b6-e6c1dc764a38`. Both feature programmes remain paused.
The common checkout is `C:/Github/ANYsolver/.perf2-worktrees/common-main-20261008`;
branch `codex/common-main-20261008`, PR #63. See
`docs/development/COMMON_MAIN_CONSOLIDATION_20261008.md` for source/artifact checks
and merge prerequisites. This prospective authority supersedes historical
no-coordination/no-main-merge instructions only for consolidation. It does
not resume development, consume old allowances, qualify incomplete gates
or authorize publication. Original checkpoint follows unchanged.

---

# PAUSED restart point - 7 October 2026

Revision 8 remains the complete programme: G0-G6/F01-F13/V01-V28/B01-B18,
external references, practical scale, platforms, consumers, reviews and release.
Goal PAUSED by explicit human request. Human approval covers pending checks, compatible repairs and
prospective bounded checks; scientific criteria and consumed authority remain.
No communication with the contact task. Mistral/local remain unavailable;
OpenAI supporting review does not satisfy final different-family acceptance.

Canonical checkout: C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001
Branch: codex/stiffened-main-reconcile-20261001; integrated source 2c3b3779.
No main merge, push or release. Unrelated ANYfem main edits remain untouched.

## Decision, facts, uncertainty and next action

Deliver the verified finite distributing displacement route through the existing
experimental ANYfem consumer while assessing saved E03 reference applicability.
No replacement framework or automatic refinement campaign.

The GE displacement candidate a990de12 (product 6399be68) has been integrated
as four commits ending at 2c3b3779. All 431 canonical solver modules now match
the tested installed site byte-for-byte. Sixteen checkout-only line-ending
differences were diagnosed and reconciled; initial mismatch evidence is retained.
Numerical checks were not repeated for this byte-identical integration.

Source controls: 17 new PASS (116.3260553s), 13 affected legacy PASS
(31.0507396s), final observer control PASS (17.8700295s). Replay uses independent
scratch-owner bindings; observer tests honor the detached-copy contract.
The source 300s follow-up used 182.7547355s, remaining 117.2452645s, reserve 60s.
Earlier 180s failures and sandbox/host visibility failures remain recorded;
no old allocation is transferred or silently renewed.

Installed wheel: abc87da6987961edc4eec35f641be018aa148103eb319af0b2a876288ad61087.
Built and installed once; 431 Python modules and 441 site files are bound.
Installed 17 new + 13 legacy + 2 cyclic controls PASS, and the public example
PASS after its preserved first timeout. Final equilibrium 1.162664177e-12;
compatibility 1.002599187e-17; checkpoint/restore/continue parity passed.
The separate 400s allowance used 223.8072112s, remaining 176.1927888s,
reserve 60s. There is no in-flight numerical job.

Supporting independent product review found no concrete correctness defect.
The added generalized/coupled cyclic controls close that coverage gap. Physical
accumulated history is the high+low compensated scalar, independently reconstructed
with Decimal at 80 digits; its two compensation terms are not separate channels.
Actual-zero-load and signed yielded reversal remain open G3 obligations.
This is a verified experimental slice, not programme or production acceptance.

Evidence: isolated ge-distributing-displacement-20261007/.development/
distributing-displacement-installed-20261007/root-terminal-result-v1.json;
canonical .development/distributing-displacement-integration-20261007/source-parity-v2.json.

E03 force observability is resolved in next-force-output-v1/saved-adjudication-v3.
Pinned RF/FORC semantics are uncondensed element nodal gradients, not raw support
reactions. The original unconsumed coarse external follow-up is now consumed.
Recovered balance 1.4974177636511776e-10 <= 1e-8; eight compatible point ports;
positive work 4.210950351426983e-5J. Engineering accuracy remains unscored.
The original ROOT-only balance failure 3.9905884 and all failed scalar runs remain.
Original 150s accounting used 44.1285582s, remaining 105.8714418s, reserve 60s;
this remainder grants no new physical comparison or refinement scope.
Saved-data review and root inspection now adopt FAILED / NOT CONVERGED as
the coarse B2 compliance screen: external/native work 2.78978, relative gap
64.1549%. No concrete section/axis/unit error was found; continuum versus
plate/beam idealization and convergence remain unresolved. This is distinct
from the principal GE connection. No new physical campaign is launched.

ANYfem source milestone committed at 8ecb8b42 in its isolated experimental
checkout. Existing elastic/material panels now persist v2 displacement requests;
v1 force formats stay unchanged. Source review repaired flat shell-output indexing
and refusal of bad callbacks/iteration controls before force seeding. Root also
corrected its overnarrow unit-seed assumption: actual cyclic seed factors are
preserved. Supporting independent review has no remaining blocking source finding.

Runtime remains UNVERIFIED. Static packet preparation completed before pause.
The packet covers 53 framing/dispatch controls, 19 affected legacy controls and
one actual public helper/checkpoint/restore/continue example. Prospective 360s,
reserve 60s; CPU0/thread1/JIT off/2GiB/job1. No old allocation transfer or solver
wheel rebuild. Authority/ledger remain PENDING, used 0s, remaining 360s, no attempts or in-flight
process. Manifest c31184cbe0ff9e0d4435cd113dc25f461e67dbb74f3a302ea317eaa41e8ce53f.
Root reviews final JSON bindings and activates only after explicit resumption.
Existing programme approval persists; this is a pause, not a fresh approval need.
Unrelated ANYfem main edits and protected historical evidence remain untouched.

## Resume action and protected boundaries

No workers or numerical jobs remain running. Consumer handoff is saved in its
.development/distributing-displacement-consumer-20261007/handoff.md; supporting
review found no runner-code blocker but final frozen JSON records are unreviewed.
On explicit resume, read this note, confirm source/packet identities and actual
Git state, finish the frozen-record review, then activate bounded checks. Do not
rerun completed solver checks or the consumed E03 physical comparison.

Formal F03 UNCONSUMED; body retry PENDING; bridge38 UNRUN; closed campaigns unchanged.
Never inspect, traverse or copy protected us3-modal-canary evidence. No automatic
physical retry, criterion relaxation or release claim. Other remainders remain
nontransferable. One numerical job, CPU0, one thread, JIT off, 2GiB for current
packets. Root owns ledgers, execution, scientific adoption and Git integration.
Historical active records are preserved; one acceptance matrix retains failures.
Resume actual artifacts without repeating passed checks or copying historical plans.
