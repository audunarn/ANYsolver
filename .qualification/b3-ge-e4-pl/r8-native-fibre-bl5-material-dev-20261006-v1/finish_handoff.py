from pathlib import Path
import ast, hashlib, json, zipfile
import xml.etree.ElementTree as ET
import psutil
root=Path(__file__).resolve().parent;repo=root.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
owned=('src/anysolver/_stiffened_shell_ge_experimental.py',
       'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
       'src/anysolver/_stiffened_shell_ge_point_buckling.py','src/anysolver/stiffened_shell.py',
       'examples/stiffened_shell_native_fibre_bl5_material.py',
       'tests/test_stiffened_shell_native_fibre_bl5_material.py',
       'docs/reference_cases/stiffened_shell_native_fibre_bl5_material.md')
for name in owned:
    if name.endswith('.py'):ast.parse((repo/name).read_text())
artifact=json.loads((root/'artifact-binding-v1.json').read_text())
wheel=Path(artifact['artifact']);assert sha(wheel)==artifact['sha256']
with zipfile.ZipFile(wheel) as archive:
    for name,digest in artifact['source'].items():
        portable=name.replace('\\','/')
        assert hashlib.sha256(archive.read(portable.removeprefix('src/'))).hexdigest()==digest
        assert sha(repo/name)==digest
finite=repo/owned[1];before=root/'executed-source-admission-v4'/owned[1]
assert finite.read_bytes()==before.read_bytes()
assert 'material_backtracking' not in finite.read_text()
assert '.5**backtrack' in finite.read_text()
assert 'newton_backtracking_policy' not in (repo/owned[0]).read_text()
runtime=json.loads((root/'runtime-installed-partial-v1.json').read_text())
assert all(Path(p).is_relative_to((root/'installed-wheel-v1').resolve()) for p in runtime['imports'].values())
processes=[]
for p in psutil.process_iter(['pid','cmdline']):
    try:
        args=p.info['cmdline'] or []
        if any(str(root/'entry.py').replace('\\','/').lower() in s.replace('\\','/').lower() for s in args):
            processes.append(p.info)
    except (psutil.AccessDenied,psutil.NoSuchProcess):pass
checks={}
for p in root.glob('junit-*.xml'):
    suite=ET.parse(p).getroot().find('testsuite')
    checks[p.stem.removeprefix('junit-')]=dict(tests=int(suite.get('tests')),failures=int(suite.get('failures')),
        errors=int(suite.get('errors')),cases=[c.get('classname')+'::'+c.get('name') for c in suite.findall('testcase')])
resources={p.parent.name:json.loads(p.read_text()) for p in root.glob('*/execution.json')}
record=json.loads((root/'handoff.json').read_text())
record.update(state='partial implementation; fibre-active public source/installed workflow verified; full material milestone FAILED/unmet, not integration-accepted or merge-ready',
    changed_files=list(owned),source_sha256={n:sha(repo/n) for n in owned},
    adopted_completed=['new material identity and native retained force/moment roles','exact CI access restored with root-authorized escalation','four outer/linear restore admission repairs','honest runnable partial example and isolated installed wheel'],
    candidate_replay=dict(resource=resources.get('rejected-trial-v1'),outcome=json.loads((root/'rejected-trial-state-v1/outcome.json').read_text()),
        helper_current_sha256=sha(root/'rejected_trial_probe.py'),helper_binding_limitation='This unchanged helper hash was recorded at handoff; original phase binding omitted helper hash, and did not save a final imported-root inventory. Exact CI preflight, executed product snapshot and sampled resource logs were recorded during execution.'),
    quadratic_candidate=dict(outcome=json.loads((root/'result-pending-comparison-v1.json').read_text()),
        resource=resources.get('pending-comparison-v1'),retained_evidence='executed-source-pending-comparison-v1 and binding-pending-comparison-v1.json',
        product_rollback='finite driver byte-equal to executed-source-admission-v4; dyadic .5**backtrack restored; candidate capability label absent'),
    focused_test_inventory=checks,resource_records=resources,
    installed_artifact=dict(path=str(wheel),sha256=artifact['sha256'],source_binding_count=len(artifact['source']),
        actual_imported_solver_modules=len(runtime['imports']),installed_root=str(root/'installed-wheel-v1'),
        build_provenance='build_isolated.py; copied current package source+metadata; Python314 pip wheel --no-deps --no-build-isolation; pip target install --no-deps; no dependency downloads/rebuilds',
        source_current_wheel_equal=True,public_result=json.loads((root/'result-installed-partial-v1.json').read_text())),
    pending=['both strict full(.5,1) lifecycle cases remain product tests without skip/xfail; V1 two historical failures unsupported runtime, no current full-file pass',
        'simultaneous shell/fibre advancing same accepted increment and actual shell plastic recovery',
        'yielded mixed generalized/native recovery; original generalized1e20 member remains elastic',
        'complete failed-trial smooth directional tangent <=1e-5: observed2.76e-4/2.91e-3/9.74e-3 unresolved',
        'global equilibrium obstruction at pending .3125; quadratic candidate also exhausted24Newton and was removed',
        'full lifecycle/material/physics/chart/stability/programme acceptance remain root obligations'],
    runtime_limitation='Historical V1 unsupported global dependencies preserved. All corrected source/installed phases fail-fast exact CI2.5.3/1.18.1/0.68.0/0.50.0, pools1/JIToff/affinity1. Installed run binds244 imported solver modules; wheel manifest binds424 source files.',
    owned_numerical_processes=processes,numerical_slot='RELEASED after terminal checks; no owned numerical child remains' if not processes else 'ACTIVE: do not release',
    final_static_checks='All six owned Python sources AST parse; scoped product git diff --check passed; shipped424 source hashes equal current and wheel payload; finite candidate rollback byte-verified')
(root/'handoff.json').write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')
excluded={'installed-wheel-v1','wheel-v1','wheel-source-v1','__pycache__','.pytest_cache'}
manifest={}
for p in root.rglob('*'):
    if p.is_file() and not any(part in excluded for part in p.relative_to(root).parts) and p.name!='raw-artifact-sha256.json':
        manifest[str(p.relative_to(root))]=dict(bytes=p.stat().st_size,sha256=sha(p))
(root/'raw-artifact-sha256.json').write_text(json.dumps(dict(excluded_directories=sorted(excluded),artifacts=manifest),indent=2)+'\n')
print(json.dumps(dict(state=record['state'],raw_artifacts=len(manifest),source_files=len(owned),owned_processes=len(processes),checks={k:dict(tests=v['tests'],failures=v['failures']) for k,v in checks.items()})))
