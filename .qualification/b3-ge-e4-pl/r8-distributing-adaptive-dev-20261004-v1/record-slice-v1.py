"""Retain the completed development slice without rewriting protected history."""
from pathlib import Path
import hashlib, json, shutil

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
artifact = json.loads((ROOT / 'artifact-v1.json').read_text())
runtime = json.loads((ROOT / 'installed-runtime-v1.json').read_text())
execution = json.loads((ROOT / 'installed-v1/execution.json').read_text())
physical = json.loads((ROOT / 'physical-result-v1.json').read_text())
physical_execution = json.loads((ROOT / 'physical-v1/execution.json').read_text())
assert runtime['exit_code'] == 0 and execution['exit_code'] == 0
assert '91 passed' in (ROOT / 'installed-v1/stdout.log').read_text()
assert physical_execution['exit_code'] == 0 and physical['status'] == 'INCOMPLETE_ADAPTIVE_LIMIT'
files = (
    'src/anysolver/_stiffened_shell_ge_experimental.py',
    'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_increment_control.py',
    'tests/test_stiffened_shell_distributing_adaptive.py',
    'tests/test_stiffened_shell_accepted_observer_experimental.py',
)
snapshot = ROOT / 'source-v1'
for name in files:
    destination = snapshot / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.exists()
    shutil.copyfile(REPO / name, destination)
    assert sha(destination) == sha(REPO / name)
record = dict(scope='IMPLEMENTED_NOT_QUALIFIED development slice', source_parent='70ab0597',
    sources={name:sha(REPO / name) for name in files}, artifact=artifact,
    installed_checks=91, installed_execution=execution,
    physical_status=physical['status'], physical_execution=physical_execution,
    physical_result_sha256=sha(ROOT / 'physical-result-v1.json'),
    physical_script_sha256=sha(ROOT / 'probe-physical-v1.py'),
    original_fixed_1_01_failure='UNCHANGED; adapted histories do not replace it')
(ROOT / 'slice-v1.json').open('x').write(json.dumps(record, indent=2) + '\n')

review = '''# Supporting source review, 4 October 2026

OpenAI Read reviewer finite_material_consumer did not implement the changes,
import modules, run tests, edit files or perform Git operations. This does not
satisfy different-family scientific acceptance.

Finding closed: generic controller replay admitted future decreasing targets.
The distributing profile now checks the full validated target sequence before
driver construction/restoration; canonical-envelope atomicity control passes.
Review of the delta found no additional admission/atomicity defect. Strict
binary-inner admission, fixed predecessors, prospective checkpoint preparation,
accepted publication, observer propagation and prefix-preserving exhaustion
remain consistent. New and affected lifecycle checks passed in the installed
wheel. Observer test helper's two exact binary layouts match current writers.

Inherited controller limitation is explicitly documented: rejected attempts
after the last acceptance are not durable. Retrying a prefix may repeat them.

Actual probe is retained as executed historical evidence, not a reusable runner.
Its unexecuted FiniteIncrementFailure fallback omits accepted_factors and uses
an inaccurate label; a prefix/timeout/programming/I/O failure may lack terminal
JSON. These paths require correction before reuse. They did not execute here:
the expected AdaptiveIncrementExhausted handler wrote the complete attempt
inventory and accepted prefix, and the supervisor independently records exit0.
An absent JSON or supervisor failure must never be interpreted as success.
No rerun is justified solely to replace this completed historical diagnostic.
'''
(ROOT / 'review-v1.md').open('x').write(review)
(ROOT / 'failures-v1.md').open('x').write('''# Preserved development failures

v1: 3 failed/5 passed, checkpoint rejected adaptive wrapper.
v2: 3 failed/5 passed, owner restore rejected adaptive wrapper.
v3: 3 failed/5 passed, lifecycle/inner-byte parity passed but result test used
nonexistent q field. Early terminal summaries were observed; portable runner
did not save pytest stdout. Retained failed-checks-v1/v2/v3 contain runtime,
selection and resource records, not raw pytest logs.
v4: focused 13 passed; full stdout and runtime/resource/selection retained.
v5: nonexistent affected-test filename; no numerical job started. Log retained.
v6: 67 passed/11 failed; old observer helper wrongly required shell-material
codec for stable elastic point binary snapshots. Log/runtime records retained.
v7: corrected observer helper 16 passed. Installed current candidate:91 passed.
Actual adaptive probe: requested1.01 incomplete at cutback limit, complete
accepted prefix through1.0075 saved. Numerical incompletion is separate from
the supervisor's successful process execution. No extra budget or retry.
''')

report = REPO / 'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md'
matrix = REPO / 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'
active = REPO / 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'
previous = active.read_bytes()
(ROOT / 'active-before-v1.bin').open('xb').write(previous)
section = '''

## Optional adaptive finite distributing execution, 4 October 2026

IMPLEMENTED_NOT_QUALIFIED. Existing adaptive halving now admits selected elastic,
generalized beam-material and coupled-Q4-J2 distributing profiles. Fixed defaults,
laws, physical tolerances,12 adaptive/16 material-fixed backtrack limits and
checkpoint schemas remain unchanged. Controller envelope keeps the dedicated
binary inner state; full future target monotonicity is checked before restore
publication. Chart/staged/external/displacement/arc exclusions remain.

Injected scheduling controls: all three material domains cancel, restore and
continue to exact fixed-oracle inner checkpoint bytes. Exhaustion preserves
accepted bytes; malformed envelopes fail atomically; observer/programming/memory
errors propagate without cutback. Rejected attempts after the last accepted
snapshot are nondurable; retry may repeat those attempts. This inherited limit
is documented, not silently represented as a durable complete-run budget.

Focused13PASS26.85s; affected67PASS/11FAIL exposed an outdated observer test
codec assumption, corrected16PASS22.04s. Consolidated installed91PASS108.25s,
whole110.53s/sample209203200B, actual affinity/pools1/JIToff. Every imported
solver source byte matches the candidate wheel. WheelSHA256
7b75d8f10ab9a466f5f6353da4241001f9beda6ffa5da4d28441bef297a39a0c.
ANYfem source and prior consumer artifact unchanged; no repeated consumer campaign.

One non-injected installed continuation rebuilt the current coupled quarterstep
prefix. Target1.01 with24Newton/12backtracks/max_cutbacks4/max_attempts8 rejected
five attempts and accepted1.005,1.00625,1.0075 before cutback exhaustion.
Final accepted equilibrium2.91381e-12/gap8.21400e-18; both materials active.
All seven accepted prefixes are immutable. Whole121.79s/sample167694336B,
actual affinity/pools1/JIToff. Process exit0 reports numerical INCOMPLETE,
not success at1.01. Changed material path is not fixed-history parity or general
convergence benefit. Fixed1.01 failure remains; no automatic budget extension.

Raw .qualification/b3-ge-e4-pl/r8-distributing-adaptive-dev-20261004-v1 binds
source snapshot, wheel/import identities, commands, actual outputs, failures,
all attempts, checkpoints and supporting review. Historical diagnostic fallback
reporting defects are documented; runner is not reusable until corrected.
Independent different-family/material/physical/capacity acceptance remains open.

### Combined reference interpretation; no additional numerical execution

Retain declared reference-linear mean/secant-director/curl distributing law for
development: its reduced work/offset map is reproduced by the admitted shell
field. Symmetric 3D shear distinguishes secant director from polar spin; local
zero-mean-pose warping is intentionally free. This is not welded/rigid/bonded-line
equivalence, and finite projected-director/polar evidence remains separate.

Four native Mx levels and three Fy levels plus solid in-plane and thickness
checks support direct-work mesh-pair convergence. Fine work differences are
-0.220599% Mx/-0.395443% Fy; no asymptotic tail estimate is established.
The small native40 Fy pitch is -8.440439020782232e-8rad versus binary solid
-8.68704917967043e-8rad (2.838825% relative discrepancy). Do not hide it using
an invented absolute floor or total-work norm. Symmetric flat elastic geometry
separates membrane and bending reflection parity; Fy pitch corresponds to the
eccentric -0.5Mx bending action. This helps interpret the saved refinement but
does not constitute an executed native80 Fy comparison. The full six-pose
accuracy decision remains open; further refinement requires its own specific
question. Supporting OpenAI review does not close required scientific acceptance.
'''
old = report.read_bytes()
report.write_bytes(old + section.encode('ascii'))
assert report.read_bytes().startswith(old)
old = matrix.read_bytes()
matrix.write_bytes(old + b'''

Finite distributing adaptive execution,4 October: IMPLEMENTED_NOT_QUALIFIED.
Selected elastic/generalized/coupled-Q4-J2 profiles reuse existing controller;
91 installed checks pass including identical accepted-path checkpoint oracle,
atomic restore/rejection and cancellation. Actual non-injected1.01 continuation
accepts through1.0075 then exhausts; failure and all accepted prefixes retained.
No general convergence, full material, F04/G0/G2/capacity or release closure.
Reference full-six-pose accuracy remains open despite close direct work: small
Fy pitch discrepancy2.838825% cannot be hidden by retrofitted normalization.
[Evidence](development/r8-distributing-reference-linear-20261004/results.md).
''')
assert matrix.read_bytes().startswith(old)
active.write_text('''# B3-GE / E4-PL / B2 active state - 4 October 2026

ACTIVE. Canonical worktree C:/Github/ANYsolver/.perf2-worktrees/
stiffened-main-reconcile-20261001; branch codex/stiffened-main-reconcile-20261001.
Source parent70ab0597; current commit is determined from Git HEAD. Complete
amended G0-G6/F01-F13/V01-V28/B01-B18 remains binding. No aggregate gate closes.
[Goal](B3_GE_E4_PL_REVISION_8_GOAL.md), [plan](B3_GE_E4_PL_REVISION_8_PLAN.md),
[matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md).

## Delivered behavior

Persistent multi-Q4/S3/native-B3 point owner and separate physical B2 routes
remain. Selected multi-Q4 finite distributing elastic/generalized/coupled-J2
profiles have physical recovery, fixed accepted predecessors and atomic binary
restart. Material consumer source ANYfem aaccbaa is unchanged in this slice.

Existing isolated SO3 evaluation repairs selected material Q4 value accuracy;
policy is model-bound. Previous47 installed checks/public example remain valid.
Current optional adaptive halving reuses existing controller, without changing
fixed defaults, laws, tolerances, schemas or trial limits. Full decreasing future
targets reject before restore publication. Snapshot inner state remains dedicated
binary. Chart/staged/external/displacement/arc combinations remain excluded.

Current91 installed checks passed108.25s, whole110.53s/sample209203200B. Actual
affinity/pools1/JIToff; imported bytes match wheel/source. Scheduling injections
produce exact fixed-oracle accepted inner bytes across all three profiles.
Rejected attempts after the latest acceptance are not durable; retry can repeat
them. This inherited budget limitation is explicit. Supporting source review
findings resolved; different-family scientific acceptance remains open.
Solverwheel7b75d8f10ab9a466f5f6353da4241001f9beda6ffa5da4d28441bef297a39a0c.
Prior material consumerwheel716ac11f89336ec2a84b54b580ea1367ff6ce456d797497118e87b1b596bca49.

## Current decisions and next action

One actual installed adaptive1.01 continuation accepted1.005,1.00625,1.0075
before cutback exhaustion (five rejected/eight total attempts). Final accepted
equilibrium2.91381e-12/gap8.21400e-18, both materials yielding. All seven prefixes
saved. Whole121.79s/sample167694336B; actual affinity/pools1/JIToff. Requested1.01
remains incomplete. Original fixed1.01 failure/residual0.00246153 is unchanged;
adapted history is not a fixed-path oracle or general improvement claim.
Stop this bounded run; no automatic retries, budget increase or curvature sweep.
Next development should advance a separately admitted missing workflow rather
than repeat this incomplete trajectory. Relevant future diagnostics must identify
the precise unresolved derivative/curvature question first.

Pinned CCX2.23 DOUBLE output resolved saved40x16/nz4 reaction-print precision:
scaled balances2.64164e-10/2.05791e-11, identical DATs. Reference-linear mean/
secant-director/curl law is retained for development, not welded/rigid equivalence.
Fine Mx/Fy direct-work differences0.220599%/0.395443%; no asymptotic bound claimed.
Small native40 Fy pitch differs2.838825%; full six-pose accuracy remains open.
Symmetry connects this bending component to eccentric Mx, but does not create
an unexecuted fine-Fy result. No automatic reference refinement or F04 closure.

## Evidence and ownership

[Grouped evidence](development/r8-distributing-reference-linear-20261004/results.md).
Latest raw .qualification/b3-ge-e4-pl/r8-distributing-adaptive-dev-20261004-v1:
source snapshots, wheel/import hashes, failed checks, installed outputs,
actual attempts/prefixes and supporting review. Prior note bytes preserved in
active-before-v1.bin. Material/output records retain their historical identities.
No numerical jobs remain; all review workers terminal. Source/Git owned by root.
No push/main merge/publication/contact-worker communication. ANYfem worktree
C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer remains unchanged.

## Preserved boundaries

FormalF03 UNCONSUMED: never execute/copy/substitute
scripts/b3_e4_f03_c1_fy_supported_reference.py, SHA
c908b1f3e4d9467deb3a96876126d5488cd040503cc6c6ec485b8aeaecef9481.
Never inspect/copy/archive us3-modal-canary (credentials); no Get-CimInstance.
At most3 workers/ONE numerical job/100krows/600s/8GiB/8threads. Effective tighter
600s/2GiB/affinity1/pools1/JIToff. Optional local/Mistral unavailable; no reprobe.
Frozen G3c graph guard requires reviewed runner lease; no bypass/replay.
BL5 actual inventory13positive/1unresolved/7unassessed; auxiliary21 is not
mechanical stability. Inverse/positive-part certificates CLOSED_UNRESOLVED;
pressure amendment DECLINED. F5 lacks retained-sided reference forces.
Full material/attachment/load/spectral/capacity/scale/installed-platform/consumer/
external/independent/release obligations remain open. No completed-goal claim.
''', encoding='utf-8')
print('Recorded bounded slice; historical report/matrix prefixes preserved.')
