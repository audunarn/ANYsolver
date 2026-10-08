from pathlib import Path
import hashlib, json, re, shutil

root = Path(__file__).resolve().parent
repo = root.parents[2]
fem = Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
runtime = json.loads((root / 'installed-runtime-v1.json').read_text())
execution = json.loads((root / 'installed-v1/execution.json').read_text())
assert runtime['exit_code'] == execution['exit_code'] == 0
assert runtime['example']['production_qualified'] is False
assert runtime['example']['accepted_factors'] == [.25, .5, .75, 1., 0., -.25]
stdout = (root / 'installed-v1/stdout.log').read_text()
count = int(re.search(r'(\d+) passed in ', stdout).group(1))
assert runtime['example']['equilibrium'] <= 1e-8 and runtime['example']['gap'] <= 1e-9
docs = repo / 'docs/agent_plans'
report = docs / 'development/r8-distributing-reference-linear-20261004/results.md'
matrix = docs / 'B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'
for name, path in [('report', report), ('matrix', matrix),
                   ('goal', docs/'B3_GE_E4_PL_REVISION_8_GOAL.md'),
                   ('plan', docs/'B3_GE_E4_PL_REVISION_8_PLAN.md')]:
    shutil.copyfile(path, root / (name + '-before-final-v1.bin'))
for version in range(1, 6):
    log = (root / f'source-v{version}.log').read_text(encoding='utf-8-sig')
    record = Path(next(line.split('record=', 1)[1] for line in log.splitlines()
                       if line.startswith('[development]')))
    target = root / f'source-v{version}-runtime'
    target.mkdir(exist_ok=True)
    for p in record.glob('*.json'):
        shutil.copyfile(p, target / p.name)
snapshot = root / 'source-final-v1'
snapshot.mkdir()
for owner, relative in [(repo, p) for p in (
    'src/anysolver/_stiffened_shell_ge_experimental.py',
    'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_ge_checkpoint_binary.py',
    'src/anysolver/_stiffened_shell_ge_distributing_reference.py',
    'src/anysolver/stiffened_shell.py',
    'tests/test_stiffened_shell_distributing_native_material.py')] + [(fem, p) for p in (
    'src/anyfem/solve/stiffened_shell_ge_distributing_material.py',
    'tests/test_stiffened_shell_ge_distributing_native_material_consumer.py',
    'examples/stiffened_shell_ge_distributing_native_material_consumer.py')]:
    target = snapshot / ('solver' if owner == repo else 'fem') / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(owner / relative, target)
review = '''Supporting OpenAI source review,4 October2026; different-family scientific acceptance OPEN.
Reviewer did not implement this slice. No imports/jobs/Git/edits by reviewer.
No blocking code or mechanics defect after routing repairs. Exact selected
checkpoint kind/model/load pattern and native origin/accepted state validated
before publication; public reference binding stays elastic. Mixed generalized
plus fibre yielding initially lacked direct codec coverage; added focused check
passed10.34s, and included in installed suite. Example accumulated-flow label
corrected before execution. No qualified material/connection/aggregate claim.

Retained failures: source-v1 all7 geometry-seam admission failures; v2/v3
4PASS/3FAIL exposed both legacy physical-fibre restore guards and a test
assertion on detached writable observer arrays. Owner arrays were already
immutable. Test now verifies owner immutability and no sharing. Laws, budgets,
tolerances and historical codec identities unchanged. Source-v4 7PASS87.79s;
source-v5 additional simultaneous generalized/fibre yield restart PASS10.34s.
'''
(root / 'review-and-failures-v1.md').write_text(review, encoding='utf-8')
artifact = runtime['artifacts']
section = f'''

## 4 October native physical-fibre distributing material development slice

IMPLEMENTED_NOT_QUALIFIED. Two explicit native cyclic policies require physical
fibres and allow supported mixed generalized/fibre members, with optional Q4 J2.
Native retained variables/local laws persist; shaped generalized/fibre origins
and accepted histories plus shell state use distinct model-bound binary kinds.
Old policies/codecs/public reference binder remain unchanged. Fixed signed/zero
normalization reuses owned reference actions; adaptive/chart/staged/S3/spectra
remain excluded from this route. No equation/default/tolerance/version change.

Source7PASS87.79s plus additional simultaneous generalized/fibre yielding and
byte-exact restart PASS10.34s. Installed{count}PASS{runtime['checks_seconds']:.2f}s;
public coupled four-fibre ANYfem example{runtime['example_seconds']:.2f}s passes
case and Project save/reopen, initial shell/fibre yielding, zero-load snapshot,
signed continuation and byte-identical accepted-path checkpoint. Equilibrium
{runtime['example']['equilibrium']:.9g}, gap{runtime['example']['gap']:.9g}.
Cancellation after recovery before publication and canonical corrupt origin,
accepted, shell, pattern and checkpoint-kind rejection preserve accepted state.
Elastic axial/biaxial full-area parity and physical transfer/work checks pass.
Reverse plastic flow, converged physical torque, every material/attachment
combination, G3/F04/aggregate acceptance and release are NOT established.

Fresh solverwheel SHA{artifact['solver']['sha256']}; consumerwheel
SHA{artifact['fem']['sha256']}. Actual imports/source bytes/dependencies,
affinity1/pools1/JIToff and2GiB/600s supervisor recorded. Different-family
acceptance remains OPEN; supporting review and all failed checks retained.
Raw .qualification/b3-ge-e4-pl/r8-distributing-native-material-dev-20261004-v1.
'''
with report.open('ab') as out:
    out.write(section.encode('ascii'))
with matrix.open('ab') as out:
    out.write(f'''

Finite distributing native cyclic material,4 October: IMPLEMENTED_NOT_QUALIFIED.
Pure axial/biaxial fibres and supported mixed-family histories use separate
origin/accepted codecs; simultaneous generalized/fibre yielding and coupled
Q4J2, exact zero/signed restart, cancellation and corrupt checkpoint guards pass.
Installed{count}PASS plus coupled public ANYfem case/Project example. Existing
laws/defaults/codec identities remain. Full G3/F04/physical/external/independent/
platform/scale/release acceptance stays OPEN. No reverse-plastic-flow claim.
[Evidence](development/r8-distributing-reference-linear-20261004/results.md).
'''.encode('ascii'))
assert report.read_bytes().startswith((root/'report-before-final-v1.bin').read_bytes())
assert matrix.read_bytes().startswith((root/'matrix-before-final-v1.bin').read_bytes())
summary = dict(installed_passes=count, checks_seconds=runtime['checks_seconds'],
    example_seconds=runtime['example_seconds'], example=runtime['example'],
    supervisor=execution, artifacts=artifact,
    report_prefix_preserved=True, matrix_prefix_preserved=True,
    scope='development only; full goal and aggregate acceptance remain open')
(root/'results-v1.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:summary[k] for k in ('installed_passes','checks_seconds','example_seconds')}, indent=2))
