from pathlib import Path
import hashlib,importlib.util,json,os,sys,time
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer
from anyfem.io.project_file import save_project,load_project
from anyfem.model.project import Project
from anyfem.model.records import AnalysisDefinition
from anyfem.solve.stiffened_shell_project import point_panel_from_analysis
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
original = json.loads((root/'installed-runtime-v1.json').read_text(encoding='utf-8'))
assert original['exit_code'] == 0
for name,digest in original['sources'].items():
    assert hashlib.sha256((site/name).read_bytes()).hexdigest() == digest
    checkout = repo if name.startswith('anysolver/') else fem
    assert hashlib.sha256((checkout/'src'/name).read_bytes()).hexdigest() == digest
for artifact in original['artifacts'].values():
    assert hashlib.sha256(Path(artifact['wheel']).read_bytes()).hexdigest() == artifact['sha256']
for path,digest in original['tests'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
example = repo/'examples/stiffened_shell_ge_point_zero_unload.py'
spec = importlib.util.spec_from_file_location('point_zero_example',example)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
model = module.definition()
programme = ss.StagedDeadLoadProgramme.deserialize((root/'public-example-v1/load-programme.json').read_bytes())
panel = consumer.ExperimentalGEPointPanel(model.shell,model.beams,model.points,model.fixed,
    q4_pullback_policy=model.q4_pullback_policy,load_programme=programme)
directory = root/'consumer-example-v2'; directory.mkdir()
consumer.save_case(panel,directory/'case.anyfem-ge.json')
assert consumer.load_case(directory/'case.anyfem-ge.json').to_dict() == panel.to_dict()
project = Project('experimental GE point zero unloading',mesh_only=True)
analysis = AnalysisDefinition.experimental_point_panel('zero unloading',panel)
project.add_analysis(analysis)
saved = save_project(project,directory/'zero-unload.anyfem')
reopened = point_panel_from_analysis(load_project(saved).analyses[analysis.id])
assert reopened.to_dict() == panel.to_dict()
started = time.monotonic()
owner = reopened.create_analysis()
try:
    raw = (root/'public-example-v1/zero.checkpoint').read_bytes()
    zero = owner.restore(raw)
    assert owner.checkpoint() == raw
    assert zero.load_equilibrium_reference_used and zero.load_equilibrium_reference_endpoint == 1
    assert not zero.applied_dead_load.any()
    completed = owner.solve(reopened.load_programme,(2.5,3.),max_iterations=20,max_backtracks=12)
    assert completed.status == 'completed' and completed.free_equilibrium_ratio <= 1e-8
    public = json.loads((root/'public-example-v1/result.json').read_text(encoding='utf-8'))
    assert list(completed.accepted_factors) == public['positions']
    imports = {name:mod.__file__ for name,mod in sys.modules.items() if
        (name == 'anysolver' or name.startswith('anysolver.') or name == 'anyfem' or name.startswith('anyfem.')) and getattr(mod,'__file__',None)}
    assert all(Path(path).resolve().is_relative_to(site) for path in imports.values())
    result = dict(scope='Installed continuation of retained public zero checkpoint through unchanged ANYfem experimental project; no campaign replay',
        status='PASS',seconds=time.monotonic()-started,positions=completed.accepted_factors,
        descriptor_exact=True,zero_checkpoint_exact=True,zero_reference_reported=True,
        production_qualified=False,previous_campaign_status='91 tests passed; original consumer suffix error retained',
        checkpoint_sha256=hashlib.sha256(raw).hexdigest(),example_sha256=hashlib.sha256(example.read_bytes()).hexdigest(),
        imports=imports,sources=original['sources'],artifacts=original['artifacts'],pools=pools,public_example=public)
    (root/'consumer-result-v1.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2)+'\n')
    (directory/'completed.checkpoint').write_bytes(owner.checkpoint())
    print('PASS: actual installed ANYfem case/Project reopen, exact zero restore, completed reload.',flush=True)
finally: owner.close()
