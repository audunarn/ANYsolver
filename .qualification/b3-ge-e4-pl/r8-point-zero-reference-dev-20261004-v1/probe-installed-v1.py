from pathlib import Path
import hashlib,importlib.metadata,importlib.util,json,os,sys,time
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer

root = Path(__file__).resolve().parent
repo = root.parents[2]
fem = Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
site = root/'site-v2'
assert Path(ss.__file__).resolve().is_relative_to(site)
assert Path(consumer.__file__).resolve().is_relative_to(site)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT'] == '1'
import scipy.linalg
pools = threadpool_info()
assert pools and all(p['num_threads'] == 1 for p in pools)
sources = {}
for package,checkout in (('anysolver',repo),('anyfem',fem)):
    for path in (site/package).rglob('*.py'):
        relative = path.relative_to(site)
        assert path.read_bytes() == (checkout/'src'/relative).read_bytes(),relative
        sources[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
artifacts = json.loads((root/'artifact-v2.json').read_text(encoding='utf-8'))['artifacts']
for artifact in artifacts.values():
    assert hashlib.sha256(Path(artifact['wheel']).read_bytes()).hexdigest() == artifact['sha256']
tests = [repo/'tests'/name for name in (
    'test_stiffened_shell_staged_load_definition_experimental.py',
    'test_stiffened_shell_staged_load_owner_experimental.py',
    'test_stiffened_shell_staged_zero_reference.py',
    'test_stiffened_shell_staged_material_history.py')]
tests.append(fem/'tests/test_stiffened_shell_staged_load_consumer.py')
record = dict(scope='Installed staged zero-reference/legacy/material/consumer development checks; not aggregate qualification',
    sources=sources,artifacts=artifacts,pools=pools,
    tests={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in tests},
    dependencies={n:importlib.metadata.version(n) for n in ('ANYsolver','ANYfem','ANYmaterial','numpy','scipy','pytest')})
out = root/'installed-runtime-v1.json'
out.open('x',encoding='utf-8').write(json.dumps(record,indent=2)+'\n')
started = time.monotonic()
status = pytest.main(['-q',*[str(p) for p in tests],'-p','no:cacheprovider',
    '--basetemp',str(root/'pytest-v1'),'-o','junit_family=legacy',
    '--junitxml',str(root/'installed-v1.xml')])
record.update(exit_code=int(status),checks_seconds=time.monotonic()-started)
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
if status: raise SystemExit(status)
example = repo/'examples/stiffened_shell_ge_point_zero_unload.py'
spec = importlib.util.spec_from_file_location('point_zero_example',example)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
started = time.monotonic()
public = module.workflow(root/'public-example-v1')
record.update(example_seconds=time.monotonic()-started,example=public,
    example_sha256=hashlib.sha256(example.read_bytes()).hexdigest())

# Real consumer input/case/native experimental project round trip and zero restore.
from anyfem.io.project_file import save_project,load_project
from anyfem.model.project import Project
from anyfem.model.records import AnalysisDefinition
from anyfem.solve.stiffened_shell_project import point_panel_from_analysis
directory = root/'consumer-example-v1'; directory.mkdir()
model = module.definition()
programme = ss.StagedDeadLoadProgramme.deserialize((root/'public-example-v1/load-programme.json').read_bytes())
panel = consumer.ExperimentalGEPointPanel(model.shell,model.beams,model.points,model.fixed,
    q4_pullback_policy=model.q4_pullback_policy,load_programme=programme)
consumer.save_case(panel,directory/'case.json')
assert consumer.load_case(directory/'case.json').load_programme.serialize() == programme.serialize()
project = Project('experimental GE point zero unloading',mesh_only=True)
analysis = AnalysisDefinition.experimental_point_panel('zero unloading',panel)
project.analyses[analysis.id] = analysis
saved = save_project(project,directory/'zero-unload.anyfem')
reopened = point_panel_from_analysis(load_project(saved).analyses[analysis.id])
assert reopened.load_programme.serialize() == programme.serialize()
owner = reopened.create_analysis()
try:
    zero = owner.restore((root/'public-example-v1/zero.checkpoint').read_bytes())
    assert zero.load_equilibrium_reference_used and zero.load_equilibrium_reference_endpoint == 1
    completed = owner.solve(reopened.load_programme,(2.5,3.),max_iterations=20,max_backtracks=12)
    assert completed.status == 'completed' and completed.free_equilibrium_ratio <= 1e-8
    record['consumer'] = dict(native_experimental_project=True,descriptor_exact=True,
        zero_restored=True,positions=completed.accepted_factors,status=completed.status)
finally: owner.close()
record['imported_paths'] = {name:mod.__file__ for name,mod in sys.modules.items()
    if (name == 'anysolver' or name.startswith('anysolver.') or name == 'anyfem' or name.startswith('anyfem.')) and getattr(mod,'__file__',None)}
assert all(Path(path).resolve().is_relative_to(site) for path in record['imported_paths'].values())
for path,digest in record['tests'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
for name,digest in sources.items():
    assert hashlib.sha256((site/name).read_bytes()).hexdigest() == digest
    checkout = repo if name.startswith('anysolver/') else fem
    assert hashlib.sha256((checkout/'src'/name).read_bytes()).hexdigest() == digest
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('Installed public example and ANYfem experimental save/reopen/zero restart completed.',flush=True)
