from pathlib import Path
import hashlib,json,shutil,subprocess,xml.etree.ElementTree as ET

raw=Path(__file__).resolve().parent;repo=raw.parents[2]
runtime=json.loads((raw/'installed-runtime-v1.json').read_text(encoding='utf-8'))
execution=json.loads((raw/'installed-v1/execution.json').read_text(encoding='utf-8'))
assert runtime['exit_code']==0 and execution['status']=='completed' and execution['exit_code']==0
assert runtime['consumer']['exact_completed_checkpoint']
xml=ET.parse(raw/'installed-v1.xml');cases=list(xml.iter('testcase'))
assert cases and not list(xml.iter('error')) and not list(xml.iter('failure'))
artifact=runtime['artifacts']['solver']['sha256'];consumer=runtime['artifacts']['fem']['sha256']
sources=[
    'src/anysolver/_stiffened_shell_affine_endpoint.py',
    'src/anysolver/_stiffened_shell_displacement_checkpoint.py',
    'src/anysolver/_stiffened_shell_displacement_control.py',
    'src/anysolver/_stiffened_shell_displacement_corrector.py',
    'src/anysolver/_stiffened_shell_ge_checkpoint_binary.py',
    'src/anysolver/_stiffened_shell_ge_experimental.py',
    'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'tests/test_stiffened_shell_native_point_displacement.py',
    'examples/stiffened_shell_ge_point_displacement.py',
    'docs/stiffened_shell_native_displacement_development.md',
]
for relative in sources:
    dest=raw/'source-v1'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes((repo/relative).read_bytes())
    if relative.startswith('src/'):
        assert hashlib.sha256((repo/relative).read_bytes()).hexdigest()==runtime['sources'][relative[4:]]
paths={
    'report':'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md',
    'matrix':'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
    'active':'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
    'goal':'docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md',
    'plan':'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
}
for name,relative in paths.items():
    assert not (raw/(name+'-before-final-v1.bin')).exists()
    (raw/(name+'-before-final-v1.bin')).write_bytes((repo/relative).read_bytes())
summary=f'''

5 October native POINT displacement development (source parent33c01791):
Implemented fixed-target translational control through the existing sparse
corrector for elastic flat full-map Q4 and generalized/fibre/mixed native members.
Separate native controller/mechanical identities, model-derived accepted/origin
histories, exact replay, physical material recovery and atomic publication.
Ordinary unrebased dead-translation force seed only; staged/external/chart/event/
adaptive/arc combinations fail explicitly. Legacy BL5/curved bytes and criteria
unchanged. Source4PASS33.88s, installed{len(cases)}PASS{runtime['checks_seconds']:.2f}s;
public example and actual ANYfem experimental case/project reopen, exact prefix
restore and continued-checkpoint parity pass. All520 installed/source identities
and actual affinity/pools1/JIToff verified; no release or platform claim.
Solverwheel{artifact}; unchanged consumerwheel{consumer}.
Earlier source screens4FAIL22.31s and3FAIL/1PASS29.21s are retained harness
failures:detached writable observers, nonexistent constant, then fresh-owner
restore restriction. Repaired controls test mutation isolation and actual fresh
corrupt-history rejection; no runtime guard or tolerance was weakened.
Supporting same-family Read review clean after capability seed restriction.
Physical yielding exercised in fibre/mixed controls; generalized-only control
elastic, not a complete generalized-yield or material-combination qualification.
Raw .qualification/b3-ge-e4-pl/r8-native-point-displacement-dev-20261004-v1.
G4A subset IMPLEMENTED_NOT_QUALIFIED; no F/G aggregate closes. Coupled shell-J2/
fibre chart, line mechanics, capacity, total energy, external/platform/scale and
different-family acceptance remain OPEN. Goal ACTIVE. Next inspect the native
shell-J2 displacement history seam before a bounded material-control extension;
do not retry the parked force-chart curve or change physical laws/run budgets.
'''
for name in ('report','matrix','goal','plan'):
    with (repo/paths[name]).open('ab') as stream:stream.write(summary.encode('ascii'))
active=(repo/paths['active']).read_bytes()
start=active.index(b'## Current decision, uncertainty and next action')
end=active.index(b'Simultaneous shell-J2/fibre loaded chart remains OPEN and parked:')
active=active[:start]+('''## Current decision, uncertainty and next action

Native fixed-target translation displacement control delivered for elastic flat
full-map Q4 POINT and generalized/fibre/mixed native members. Ordinary unrebased
dead-translation force seed; no staged/external/chart/event/adaptive/arc admission.
Model-derived accepted/origin histories, exact native replay and material recovery
with atomic publication. Source4PASS33.88s; installed'''+str(len(cases))+'''PASS;
public example + ANYfem experimental project exact prefix/reload parity pass.
Current source parent33c01791; solverwheel'''+artifact+'''.
Current site .qualification/b3-ge-e4-pl/r8-native-point-displacement-dev-20261004-v1/site-v1;
520 package/source identities, numerical affinity/pools1/JIToff verified.
Earlier harness failures retained; supporting same-family review clean. This
material/control slice is implemented/tested, not qualified. Generalized-only
control elastic; fibre/mixed controls genuinely plastic. Full material scope OPEN.

Next inspect native shell-J2 displacement state/recovery contracts, then choose
the smallest bounded extension using the existing owner and histories. Preserve
isolated replay, no partial commit, native laws/defaults, typed failures and all
criteria. No new framework, automatic failed-curve replay or load/budget changes.

''').encode('ascii')+active[end:]
# Drop the superseded prospective tail; its exact bytes are archived above.
tail=b'\nCurrent bounded implementation: native fixed-target translational displacement control,'
if tail in active:active=active[:active.index(tail)]
active=active.replace(b'active state - 4 October 2026',b'active state - 5 October 2026')
(repo/paths['active']).write_bytes(active)
review=dict(role='Read-only supporting OpenAI, not different-family acceptance',
    findings=['Native mixed histories and full-map arithmetic must be codec-bound; implemented.',
              'Generalized recovery requires explicit native scratch/retrieval; implemented.',
              'Exclude event/adaptive/chart and staged/external seeds; implemented.',
              'Expose effective seed restriction in capabilities; implemented.'],
    final='No remaining meaningful source-review defects in the stated scope.',
    checks_run_by_reviewer=[],qualification_closed=False)
(raw/'supporting-review-v1.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
adjudication=dict(status='PROGRESS',installed_cases=len(cases),runtime=execution,
    source_screen='4 PASS 33.88s',prior_screens=['4 FAIL 22.31s','3 FAIL 1 PASS 29.21s'],
    failures_preserved=True,public_example=runtime['public_example'],consumer=runtime['consumer'],
    artifacts=runtime['artifacts'],qualification_closed=False,goal='ACTIVE')
(raw/'adjudication-v1.json').write_text(json.dumps(adjudication,indent=2)+'\n',encoding='utf-8')
for directory in (raw/'pytest-v1').iterdir():
    if directory.is_dir() and directory.name.startswith('test_native_fixed_displacement') and not directory.is_symlink():
        shutil.copytree(directory,raw/'accepted-history-v1'/directory.name)
attrs=['.qualification/b3-ge-e4-pl/r8-native-point-displacement-dev-20261004-v1/** -text -whitespace']+[p+' -text' for p in sources]
old=(repo/'.gitattributes').read_bytes().replace(b'\r\n',b'\n')
for line in attrs:
    if line.encode('ascii') not in old.splitlines():old+=line.encode('ascii')+b'\n'
(repo/'.gitattributes').write_bytes(old)
shutil.copyfile(raw.parent/'r8-point-zero-reference-dev-20261004-v1/check-staged-v1.py',raw/'check-staged-v1.py')
(raw/'staged-proof-v1.json').write_bytes(b'{}\n')
stage=['.gitattributes',*sources,*paths.values(),
    '.qualification/b3-ge-e4-pl/r8-point-zero-reference-dev-20261004-v1/committed-source-proof-v1.json']
for path in raw.rglob('*'):
    if not path.is_file():continue
    if any(p.startswith(('site-','solver-dist-','pytest-')) or p=='__pycache__' for p in path.relative_to(raw).parts):continue
    if path.suffix=='.pyc':continue
    stage.append(path.relative_to(repo).as_posix())
stage.append((raw/'stage-inputs-v1.txt').relative_to(repo).as_posix())
(raw/'stage-inputs-v1.txt').write_text('\n'.join(sorted(set(stage)))+'\n',encoding='ascii')
print(json.dumps(dict(files=len(set(stage)),bytes=sum((repo/p).stat().st_size for p in set(stage)),installed_pass=len(cases))))
