from pathlib import Path
import hashlib, json, shutil, xml.etree.ElementTree as ET

raw = Path(__file__).resolve().parent
repo = raw.parents[2]
paths = {
    'report': 'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md',
    'matrix': 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
    'goal': 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md',
    'plan': 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
    'active': 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
}
for name, relative in paths.items():
    backup = raw/(name+'-before-final-v1.bin')
    assert not backup.exists(), backup
    backup.write_bytes((repo/relative).read_bytes())

summary = '''

4 October point zero-reference development delivery (source parent cab437fb):
Opt-in B3_GE_E4_PL_STAGED_ZERO_REFERENCE_V1_DEV freezes a declared nonzero
free-work endpoint only for an exactly zero complete applied vector. Default V1
bytes/nonzero behavior, actual loads, material laws and 1e-8/1e-9 checks remain.
Installed solver wheel dd5fcc44985b0b34f79011bab8f96fafe8c219f92af93dc22740db4687c1d344
and unchanged ANYfem9faed76 wheel626f27b61cfe8ad6dda80e3800e60ecf925fe4d6e1dd55da236a3f27be26c02f
bind 520 checked installed/source files. Five-module campaign:91PASS248.56s.
Public mixed generalized/fibre point example:plastic load/zero-unload/reload,
exact restart; zero equilibrium5.381928125419593e-10 and gap7.798304297352494e-18.
The campaign subsequently failed its consumer filename suffix; preserved as
failed integration execution, not relabelled PASS. Repaired consumer uses the
retained checkpoint without replaying loading:experimental case/project save/
reopen, exact zero restore and reload PASS5.19s. Earlier2binary/JSON test failures
reproduced on prior installed artifact; test helpers repaired without weakened
negatives,8PASS29.68s. Source/baseline harness failures retained as failures.
Algebraic work-dual unit/tiny-load controls and one low-yield physical-fibre
lifecycle example do not establish full equivalent-unit, engineering capacity,
simultaneous shell-J2/fibre chart, line, spectrum or aggregate acceptance.
Supporting same-family review findings on first prepared programme and paired
dissipation history resolved; no remaining actionable finding for this slice.
Raw .qualification/b3-ge-e4-pl/r8-point-zero-reference-dev-20261004-v1; one job,
600s/2GiB, actual numerical affinity/pools1/JIToff. Coupled-chart failure remains
parked. Goal ACTIVE; G0-G6 and different-family/platform/physical gates OPEN.
Next inspect the existing native material displacement-control contract; do not
disable guards, reuse the wrong material codec or retry the failed chart curve.
'''
for name in ('report','matrix','goal','plan'):
    with (repo/paths[name]).open('ab') as stream:
        stream.write(summary.encode('ascii'))

active = '''# B3-GE / E4-PL / B2 active state - 4 October 2026

ACTIVE. Canonical worktree C:/Github/ANYsolver/.perf2-worktrees/
stiffened-main-reconcile-20261001; branch codex/stiffened-main-reconcile-20261001.
Source parent cab437fb; current commit from Git HEAD. ANYfem worktree
C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer at9faed76 unchanged.
Full amended G0-G6/F01-F13/V01-V28/B01-B18 binds; no aggregate gate closes.
[Goal](B3_GE_E4_PL_REVISION_8_GOAL.md), [plan](B3_GE_E4_PL_REVISION_8_PLAN.md),
[matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md).

## Delivered behavior and current artifacts

Existing multi-Q4/S3 native POINT owner, physical B2 batch/consumer, finite
distributing elastic/material/cyclic behavior remain. Historical source c5f5d79e,
735e42b9, af4059a9 and cab437fb bind their original installed or diagnostic evidence;
see grouped report/matrix rather than treating old wheels as current source.

Current opt-in staged zero reference:owned finite nonzero free-work endpoint,
exact-zero-only normalization, explicit policy/endpoint result and checkpoint
identity. Default V1 bytes/nonzero behavior, actual load/residual/tangent, native
material laws, retained variables, equilibrium1e-8 and gaps1e-9 unchanged.
Flat POINT only; no other attachments/loads/controls/new material admission.
Installed solverwheel dd5fcc44985b0b34f79011bab8f96fafe8c219f92af93dc22740db4687c1d344;
unchanged consumerwheel626f27b61cfe8ad6dda80e3800e60ecf925fe4d6e1dd55da236a3f27be26c02f.
Site .qualification/b3-ge-e4-pl/r8-point-zero-reference-dev-20261004-v1/site-v2.
All520 package source hashes match installed imports. Five-module91PASS248.56s.
Public2Q4/2native generalized+fibre example:plastic loading, exact-zero unload,
snapshot/reload parity; equilibrium5.381928125419593e-10/gap7.798304297352494e-18.
Actual ANYfem experimental case/project save/reopen, zero restore and reload pass.
Native project is explicitly experimental, not ordinary qualified persistence.

Campaign consumer suffix failure retained. Repair reuses the byte-bound zero
checkpoint without repeating loading. Two old binary/JSON test failures reproduce
on prior artifact; codec-aware test helper preserves old negatives,8PASS29.68s.
Algebraic unit work-map/tiny-component controls are not full unit-model qualification.
Same-family supporting review clean after prepared-context/history fixes; no
different-family scientific acceptance claimed. No new numerical campaign needed
for this verified delivery. No job live; no benchmarks competing.

## Current decision, uncertainty and next action

Next inspect native POINT material displacement control through existing driver,
accepted-state codecs and recovery. Deliver only a proper native state extension;
do not disable BL5/curved admission guards or reuse generalized-only serializers.
Keep existing controls unchanged and actual update, predecessor, atomic acceptance,
failure, cancellation and restart checks. Make the smallest bounded decision from
that contract inspection. No new framework or general planning cycle.

Simultaneous shell-J2/fibre loaded chart remains OPEN and parked:1GPa shell stayed
elastic; admitted200MPa shell activated5stations/maxalpha.0010034863 then exhausted
4cutbacks at .3828125 before fibre flow. Fixed saved-prefix directional check
max3.20491e-6<1e-5 with unchanged active masks/state; one direction only, not general
stability/limit-point proof. STOP curve/load/budget slice; no automatic retry.
Original known-failing fixture retained, ordinary fibre regression not weakened.

Native80 Fy versus pinned solid all6poses<1% (pitch-.864137/work-.030881), but
40->80pitch movement2.032% leaves converged physical accuracy OPEN. STOP further
refinement. Prior adaptive1.01 stop1.0075/fixedresidual.00246153 remain failures.
Physical connection/stability, full F06/G3/total energy, units, platform/scale,
external references, different-family acceptance and complete release remain OPEN.

## Evidence and protected boundaries

[Grouped evidence](development/r8-distributing-reference-linear-20261004/results.md).
Raw r8-point-zero-reference-dev-20261004-v1 below .qualification/b3-ge-e4-pl
retains failures, identities, raw outputs and supporting review. Protected report/
matrix prefixes and prior raw roots stay byte-for-byte. Root owns Git/integration.
No push/main merge/publication/contact-worker communication. Full goal ACTIVE.

FormalF03 UNCONSUMED:never execute/copy/substitute
scripts/b3_e4_f03_c1_fy_supported_reference.py, SHA
c908b1f3e4d9467deb3a96876126d5488cd040503cc6c6ec485b8aeaecef9481.
Never inspect/copy/archive us3-modal-canary(credentials); no Get-CimInstance.
At most3workers/ONE numerical job/100krows/600s/8GiB/8threads; tighter effective
600s/2GiB/affinity1/pools1/JIToff. Optional local/Mistral unavailable; no reprobe.
Frozen G3c graph guard needs reviewed runner lease; no bypass/replay.
BL5 inventory13positive/1unresolved/7unassessed; auxiliary21 not mixed stability.
Inverse/positive-part CLOSED_UNRESOLVED; pressure amendment DECLINED. F5 lacks
retained-sided reference forces. Scientific/history/authority contracts unchanged.
'''
(repo/paths['active']).write_bytes(active.encode('ascii'))

review = {
    'role':'Read-only supporting OpenAI review, not different-family acceptance',
    'findings_resolved':[
        'First zero stage now supplies prepared compiled programme before atomic commit.',
        'Accepted unload predecessor history checked with compensated high/low energy pairs.',
        'Per-component sign objection withdrawn: Decimal low component may be negative; paired fsum is the physical quantity.'
    ],
    'final_disposition':'No remaining actionable finding in the scoped current delta/public example.',
    'checks_executed_by_reviewer':[], 'qualification_closed':False,
}
(raw/'supporting-review-v1.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
tree = ET.parse(raw/'installed-v1.xml')
assert len(list(tree.iter('testcase'))) == 91
assert not list(tree.iter('failure')) and not list(tree.iter('error'))
consumer = json.loads((raw/'consumer-result-v1.json').read_text(encoding='utf-8'))
assert consumer['status']=='PASS' and consumer['zero_checkpoint_exact']
adjudication = {
    'source_parent':'cab437fb', 'level':'A experimental development',
    'installed_tests':{'passed':91,'seconds':248.56,'xml':'installed-v1.xml'},
    'public_example':'PASS, actual plastic zero-unload/reload and exact restart',
    'original_integration_execution':'FAILED after passed tests/example: invalid ANYfem filename suffix',
    'repaired_consumer':'PASS, retained checkpoint reused without loading replay',
    'prior_baseline':'Two codec-assumption failures reproduce on previous installed artifact; fixed tests preserve negatives',
    'source_codec_repair':'8 PASS 29.68s',
    'historical_failures_preserved':True, 'scientific_acceptance':False,
    'scope_exclusions':['simultaneous shell-J2/fibre chart','full equivalent-unit models','other attachments/loads','capacity/spectra','full G0-G6','different-family/platform/scale acceptance'],
    'artifacts':json.loads((raw/'artifact-v2.json').read_text(encoding='utf-8'))['artifacts'],
}
(raw/'adjudication-v1.json').write_text(json.dumps(adjudication,indent=2)+'\n',encoding='utf-8')
target=raw/'accepted-zero-history-v1'
shutil.copytree(raw/'pytest-v1/test_point_plastic_zero_unload0',target)
sources = [
    'src/anysolver/_stiffened_shell_ge_experimental.py',
    'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_staged_load_experimental.py',
    'tests/test_stiffened_shell_staged_load_owner_experimental.py',
    'tests/test_stiffened_shell_staged_zero_reference.py',
    'examples/stiffened_shell_ge_point_zero_unload.py',
    'docs/stiffened_shell_staged_zero_load_development.md',
]
for relative in sources:
    dest=raw/'source-v1'/relative
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes((repo/relative).read_bytes())
attrs = ['.qualification/b3-ge-e4-pl/r8-point-zero-reference-dev-20261004-v1/** -text -whitespace']
attrs += [relative+' -text' for relative in sources]
attrs += [paths[name]+' -text' for name in ('active','goal','plan')]
old=(repo/'.gitattributes').read_bytes().replace(b'\r\n',b'\n')
for line in attrs:
    if line.encode('ascii') not in old.splitlines():
        old += line.encode('ascii')+b'\n'
(repo/'.gitattributes').write_bytes(old)
shutil.copyfile(repo/'.qualification/b3-ge-e4-pl/r8-native-coupled-chart-dev-20261004-v1/check-staged-v1.py',raw/'check-staged-v1.py')
(raw/'staged-proof-v1.json').write_text('{}\n',encoding='ascii')
stage = ['.gitattributes',*sources,*paths.values()]
for path in raw.rglob('*'):
    if not path.is_file():
        continue
    parts=path.relative_to(raw).parts
    if any(p.startswith(('site-','solver-dist-','pytest-','baseline-pytest-')) or p=='__pycache__' for p in parts):
        continue
    if path.suffix=='.pyc':
        continue
    stage.append(path.relative_to(repo).as_posix())
stage.append((raw/'stage-inputs-v1.txt').relative_to(repo).as_posix())
(raw/'stage-inputs-v1.txt').write_text('\n'.join(sorted(set(stage)))+'\n',encoding='ascii')
print(json.dumps({'files':len(set(stage)),'bytes':sum((repo/p).stat().st_size for p in set(stage))}))
