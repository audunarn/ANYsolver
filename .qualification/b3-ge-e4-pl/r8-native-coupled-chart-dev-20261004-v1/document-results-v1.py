from pathlib import Path

root = Path(__file__).resolve().parent
repo = root.parents[2]
report = repo/'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md'
matrix = repo/'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'
for name,path in (('report',report),('matrix',matrix)):
    assert path.read_bytes() == (root/(name+'-before-final-v1.bin')).read_bytes()
report.open('ab').write(b'''

## Coupled loaded point chart controls: bounded negative exit, 4 October

Product remains c5f5d79e/installed solver f31527d54afd93d1a334dbbda545cb9affce847cfac94676fe9e8a2f6718847b,
consumer 9faed76/wheel626f27b61cfe8ad6dda80e3800e60ecf925fe4d6e1dd55da236a3f27be26c02f.
Parent af4059a9. All520 product source files and both artifact hashes were checked;
no source product change or wheel rebuild. Raw root:
`.qualification/b3-ge-e4-pl/r8-native-coupled-chart-dev-20261004-v1`.

V1 DNVC208(1/1.05/1.1GPa,.005/.01plasticstrain,4GPa,.2) completed .125/.5/.75/1
but shell alpha stayed zero. FAIL29.77s, whole31.880s/179920896B. This is missing
simultaneous coverage, not a chart or constitutive defect. V2 used the exact
already-admitted 200/220/230MPa,.005/.01,1GPa,.2 control, not fitted to stresses.
Same geometry/supports/forces/FY250MPa-H210GPa fibres/20Newton/12backtracks/
4cutbacks/64attempts. It accepted .125/.3125/.359375/.3828125 then exhausted
cutbacks after finite mixed backtrack budget exhaustion. FAIL75.36s,
whole77.614s/187371520B. Five shell integration stations active at the last
accepted prefix; maximum alpha .0010034863. Fibre accumulated states remained
zero. No reset or simultaneous loaded transport was reached. Accepted snapshots,
actual predecessors, plane-stress plastic work, physical balance, failure details
and controller-bearing checkpoints are retained in failed-states-v1/v2.

One saved-prefix actual-update derivative discriminator reused precisely the
V2 checkpoint and predecessor, with no solve/new loads. Three steps1e-4/1e-5/1e-6,
separate shell/beam/retained/constraint groups, fixed origin histories, same
chart/spatial updates and checkpoint byte identity. All masks unchanged, five
active shell stations/zero active beam histories. Maxrelative error3.20491e-6;
adjacent steps pass1e-5. Whole3.219s/167825408B, pools/affinity1/JIToff.
This is one seeded direction at one state, not a matrix certificate, a stability
test, or a limit-point conclusion. The first diagnostic checkpoint reader failed
because it expected the unstaged format; its logs remain, and the corrected
probe reads actual driver predecessor histories directly. It changes no product.

Decision: STOP the curve/load/budget slice. Full coupled loaded-chart obligation
remains OPEN. No observed mismatch justifies an operator rewrite. Restore the
prior passing ordinary fibre-only regression byte-for-byte; retain test-v3.py
as an explicitly invoked failed development fixture. No XFAIL or hidden pass.
Next bounded development decision: explicit physical normalization at zero load
for the point route, preserving legacy nonzero/default/checkpoint contracts.
No artificial residual floor or relaxation of1e-8 equilibrium/1e-9 compatibility.
Supporting review is bound separately below; different-family acceptance remains
OPEN. Full G0-G6/material/physical/release obligations and formal F03 unchanged.
''')
matrix.open('ab').write(b'''

F06/V18 simultaneous shell-J2/native-fibre loaded POINT chart transport,4 October:
OPEN/FAILED_DEVELOPMENT_CONTROLS. V1 fibre-active/shell-inactive; V2 shell-active
but cutback exhausted at .3828125 before fibre flow/reset. No aggregate disposition
changed. One saved-prefix directional derivative passes1e-5 in all four row groups
with unchanged active masks and owned checkpoint; does not establish continuation
or a limit point. Both failures and candidate fixtures retained; ordinary prior
fibre regression restored exactly. No curve/load/budget campaign follows.
Point zero-load physical normalization/compatibility remains OPEN.
[Evidence](development/r8-distributing-reference-linear-20261004/results.md).
''')
for name in ('GOAL','PLAN'):
    path = repo/f'docs/agent_plans/B3_GE_E4_PL_REVISION_8_{name}.md'
    text = path.read_text()
    text += '''
4 October coupled-chart exit: two bounded controls did not reach simultaneous
shell-J2/fibre transport (inactive shell, then active shell but cutback exhausted
at .3828125). A fixed saved-prefix actual-update directional check passes all
four row groups without active-branch/history changes; no limit-point or general
tangent claim. Preserve both failures and stop that curve/load/budget slice.
Next bounded action is the smallest explicitly selected physical zero-load
normalization contract for point stepping, with unchanged acceptance limits,
nonzero legacy behavior and restart identity. No implementation is accepted by
this choice; coupled loaded-chart/full F06/G3 remains open. Reuse the active note
and matrix instead of launching a replacement campaign or planning framework.
'''
    path.write_bytes(text.replace('\r\n','\n').encode())
active = '''# B3-GE / E4-PL / B2 active state - 4 October2026

ACTIVE. Canonical worktree C:/Github/ANYsolver/.perf2-worktrees/
stiffened-main-reconcile-20261001; branch codex/stiffened-main-reconcile-20261001.
Source parent af4059a9; current commit from Git HEAD. ANYfem worktree
C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer at9faed76, unchanged.
Full amended G0-G6/F01-F13/V01-V28/B01-B18 remains binding; no aggregate gate
closes. [Goal](B3_GE_E4_PL_REVISION_8_GOAL.md), [plan](B3_GE_E4_PL_REVISION_8_PLAN.md),
[matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md).

## Delivered behavior and exact reusable product

Persistent multi-Q4/S3/native-B3 point owner, material histories, separate physical
B2 batches/consumers and finite distributing elastic/material/cyclic routes remain.
Product c5f5d79e:204installed solver/consumer controls and ANYfem save/reopen/
zero/signed native distributing histories. Native retained variables/laws/defaults
and typed origin/accepted codecs unchanged. ANYfem9faed76; selected domains only.
Solverwheel f31527d54afd93d1a334dbbda545cb9affce847cfac94676fe9e8a2f6718847b;
consumerwheel626f27b61cfe8ad6dda80e3800e60ecf925fe4d6e1dd55da236a3f27be26c02f.
Site .qualification/b3-ge-e4-pl/r8-distributing-native-material-dev-20261004-v1/site-v1.
All520 product files/hashes checked before reuse; no rebuild for diagnostic edits.

735e42b9:2installed fixed-yielded-predecessor tangent cases PASS18.12s; max2.5753e-7
by row group. Fourteen-position biaxial fibre reversal PASS81.71s;8same station
keys reverse at restarted-1, positiveD.01431495J, exact source/installed histories.
af4059a9:loaded native-fibre POINT chart installed1PASS149.48s. Control/reset/
chart-restored share12positions; same-cell flow/noncommutation at1.125 in both
cells/all3branches, physical .05rad/1e-5rad floors. Exact reset history/gen4->5,
typed1e-9 material/paired-energy/reaction/restart parity; stale/cancel guards.
Elastic Q4/generalized member only. Stronger same-cell assertions verified from
byte-bound retained states; no duplicate mechanics. Full F06/G3 remains OPEN.

Actual native80 Fy versus original pinned binary solid: all6nonzero poses<1%,
pitch-.864137%, work-.030881%, exact reflection0. Pitch40->80movement2.032%
leaves converged accuracy OPEN. STOP physical diagnostic slice; no automatic
refinement/curvature/load-budget campaign. Earlier adaptive1.01 stopped1.0075,
original fixed1.01residual.00246153 preserved. Not physical/F04/G0 qualification.

## Current decision, facts, uncertainty and next action

Simultaneous shell-J2/fibre loaded POINT chart remains OPEN. Two bounded controls
now retained:1GPa shell completed prefix1 but stayed elastic; existing200MPa
shell control activated5shell stations (maxalpha.0010034863) yet exhausted
4cutbacks at .3828125 before fibre flow/reset. Same load/path/budgets. Failure
details, accepted balances, actual predecessor work and checkpoints retained.
Known-failing coupled fixture kept under raw/test-v3.py; ordinary prior fibre
regression restored byte-for-byte, not XFAILed or silently weakened.

One saved-prefix derivative check passes: h1e-4/1e-5/1e-6, actual chart/spatial
updates, separate shell/beam/retained/constraint groups, fixed predecessors and
unchanged masks/checkpoint. Maxerror3.20491e-6<1e-5. Whole3.219s/167825408B,
affinity/pools1/JIToff. One direction, not all columns/stability/limit-point proof.
Initial unstaged-reader harness failure retained. No product defect identified;
STOP curve/load/budget slice, do not infer a physical limit or formulation failure.

Next bounded development decision: select the smallest explicit physical zero-load
normalization contract for point stepping. Inspect existing staged/cyclic scales,
freeze force/moment/retained roles, preserve nonzero/default/legacy restart,
keep1e-8 equilibrium and1e-9 gaps, reject false equilibrium and unsupported scope.
Only after contract/review implement the narrow owner change and meaningful
zero/unload/restart/unit controls. No invented residual floor, new globalization,
coupled-chart retry, or silent qualification change. Coupled chart, total energy,
physical/different-family/platform/scale acceptance remains OPEN.

## Evidence, ownership and protected boundaries

[Grouped evidence](development/r8-distributing-reference-linear-20261004/results.md).
Raw .qualification/b3-ge-e4-pl/r8-native-coupled-chart-dev-20261004-v1 binds this
negative exit/diagnosis. Prior native-material/tangent/reverse/plastic-chart and
Fy80 roots remain immutable for their original claims. Archived active/goal/plan/
report/matrix preserve history. Root owns integration/Git/evidence; no live jobs.
No push/main merge/publication or contact-worker communication. Goal ACTIVE.
Supporting same-family review cannot close different-family scientific acceptance.

FormalF03 UNCONSUMED: never execute/copy/substitute
scripts/b3_e4_f03_c1_fy_supported_reference.py, SHA
c908b1f3e4d9467deb3a96876126d5488cd040503cc6c6ec485b8aeaecef9481.
Never inspect/copy/archive us3-modal-canary (credentials); no Get-CimInstance.
At most3workers/ONE numerical job/100krows/600s/8GiB/8threads; tighter effective
600s/2GiB/affinity1/pools1/JIToff. Optional local/Mistral unavailable; no reprobe.
Frozen G3c graph guard requires reviewed runner lease; no bypass/replay.
BL5inventory13positive/1unresolved/7unassessed; auxiliary21 not mixed stability.
Inverse/positive-part CLOSED_UNRESOLVED; pressure amendment DECLINED. F5 lacks
retained-sided reference forces. Full G0-G6 obligations and scientific criteria stay.
'''
(repo/'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md').write_bytes(active.encode())
