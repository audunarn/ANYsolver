"""Preserve completed development evidence; not a qualification adjudicator."""
from pathlib import Path
import hashlib
import json
import shutil

raw = Path(__file__).resolve().parent
repo = raw.parents[2]
installed = json.loads((raw / 'installed-prefix-result-v1.json').read_text())
program = json.loads((raw / 'program-result-v1.json').read_text())
assert installed['status'] == 'PREFIX_VERIFIED_FULL_HISTORY_OPEN'
assert installed['pytest_exit_code'] == 0 and installed['case_project_roundtrip']
assert program['status'] == 'FAILED' and len(program['accepted']) == 1
fixture = repo / 'tests/data/native_mixed_j2_displacement/quarter-prefix-v1.bin'
assert fixture.read_bytes() == (raw / 'program-accepted-1-v1.checkpoint').read_bytes()
assert fixture.read_bytes() == (raw / 'program-prefix-v1.checkpoint').read_bytes()
test = repo / 'tests/test_stiffened_shell_native_mixed_j2_displacement_snapshot.py'
assert hashlib.sha256(test.read_bytes()).hexdigest() == installed['test_sha256']
for item in installed['artifacts'].values():
    assert hashlib.sha256(Path(item['wheel']).read_bytes()).hexdigest() == item['sha256']
for name, digest in installed['sources'].items():
    owner = repo if name.startswith('anysolver/') else Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
    assert hashlib.sha256((owner / 'src' / name).read_bytes()).hexdigest() == digest, name

paths = [
    'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
    'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md',
]
archive = raw / 'before-final-v1'
assert not archive.exists(), 'do not overwrite protected archive'
for name in paths:
    target = archive / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repo / name, target)
note = '''

5 October 2026 - mixed yielded-prefix evidence, full history still OPEN
Raw: .qualification/b3-ge-e4-pl/r8-native-mixed-j2-displacement-diagnosis-20261005-v1.
No product equations, laws, tolerances, defaults or source changed from189ebb84.
Single nominal target diagnosis: actual-update shell differences decrease with
finite-difference magnitude, but no passing plateau established. Local merit slope
is descending; smallest allowed step still increases merit. Compensated/scaled
border solves improve accuracy without resolving rejection. Ancillary
relative_direction_change is mis-scaled and excluded; preserve executed bytes.
The four-quarter fixed programme accepted only the first target, then FAILED
at half target. STOP; do not automatically refine that programme. First quarter
has actual Q4/S3 flow (alpha9.23834e-6/1.07599e-5/8.06036e-6), equilibrium
5.61421e-10/gap2.92921e-21. Fibres remain elastic, not simultaneous fibre flow.
Unchanged installed wheel4e9bb8b: new prefix test1PASS plus actual ANYfem
experimental case/project roundtrip and exact recovery/checkpoint restoration.
Forged Q4 history and cancellation preserve atomicity; all520 source hashes match.
Installed4.27s/185315328B, one numerical job, actual pools1/JIToff/2GiB.
Prefix is IMPLEMENTED_NOT_QUALIFIED; full loading history FAILED/OPEN.
No aggregate gate closes, no formalF03 use, no release or physical acceptance.
Next implementation contract: assess reuse of the existing adaptive displacement
controller for native POINT histories, with bounded cutback and checkpointed work.
This is a declared integration-history extension, not parity with failed single
or quarter steps, and not a new globalization law. Current admission remains fixed
targets only until implemented and verified. Preserve chart/event/external
exclusions, all accepted predecessors and legacy checkpoint defaults.
Full Revision8 programme and its unmet gates remain ACTIVE and unchanged.
'''
for name in paths[1:]:
    with (repo / name).open('ab') as stream:
        stream.write(note.encode('ascii'))
(raw / 'results-v1.md').write_bytes(note.encode('ascii'))
print(json.dumps({'preserved_files': len(paths), 'verified_source_files': len(installed['sources']),
                  'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
                  'prefix_verified': True, 'full_history': 'FAILED_OPEN'}))
