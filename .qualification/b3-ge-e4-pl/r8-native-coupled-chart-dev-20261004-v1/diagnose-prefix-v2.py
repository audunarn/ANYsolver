from pathlib import Path
import hashlib, importlib.util, json, os, sys
from math import fsum
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_beam_history import arrays as native_history_arrays

root = Path(__file__).resolve().parent
repo = root.parents[2]
previous = root.parent/'r8-distributing-native-material-dev-20261004-v1'
site = previous/'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(site)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT'] == '1'
original = json.loads((previous/'installed-runtime-v1.json').read_text())
for name, digest in original['sources'].items():
    assert hashlib.sha256((site/name).read_bytes()).hexdigest() == digest
    owner_repo = repo if name.startswith('anysolver/') else Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
    assert hashlib.sha256((owner_repo/'src'/name).read_bytes()).hexdigest() == digest
for artifact in original['artifacts'].values():
    assert hashlib.sha256(Path(artifact['wheel']).read_bytes()).hexdigest() == artifact['sha256']
sys.path.insert(0,str(repo/'tests'))
fixture = root/'test-v3.py'
spec = importlib.util.spec_from_file_location('failed_fixture',fixture)
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)
model = fixture_module.definition(coupled=True)
owner = ss.create_analysis(definition=model)
checkpoint = root/'failed-states-v2/prefix-failed-prefix.checkpoint'
before = checkpoint.read_bytes()
try:
    saved = owner.restore(before)
    assert owner.checkpoint() == before
    assert saved.load_position == .3828125
    assert owner.preflight()['identity'] == json.loads((root/'failed-states-v2/input.json').read_text())['model_identity']
    driver = owner._finite_driver
    def evaluate(state):
        return driver._assemble(state, driver._load_factor, driver._shell_predecessors, driver._beam_predecessors)
    response = evaluate(driver._state)
    residual, tangent = response[:2]
    repeated = evaluate(driver._state)
    np.testing.assert_array_equal(residual,repeated[0])
    np.testing.assert_array_equal(tangent.toarray(),repeated[1].toarray())
    kind, generation = 'staged native coupled point', owner._generation
    arrays = dict(native_history_arrays(owner._beam_parts,driver._beam_predecessors,'origin'))
    def branches(value):
        beam = dict(native_history_arrays(owner._beam_parts,value[5],'trial'))
        return (np.array([fsum((*a[2:], *-b[2:])) > 0. for a,b in zip(beam['trial_fibres'],arrays['origin_fibres'])]),
            np.array([fsum((*a,*-b)) > 0. for a,b in zip(beam['trial_accumulated'],arrays['origin_accumulated'])]),
            np.concatenate([trial['alpha']-origin['alpha'] > 0. for trial,origin in zip(value[4],driver._shell_predecessors)]))
    base_branches = branches(response)
    count = owner._K.shape[0]
    beam_end = owner._shell_count+6*len(owner._beam_ids)
    rng = np.random.default_rng(818)
    direction = np.zeros(len(residual))
    direction[:beam_end] = rng.normal(size=beam_end)*1e-4
    for index in range(len(owner._beam_parts)):
        base = beam_end+24*index
        direction[base:base+6] = rng.normal(size=6)*1e-4
        resultants = direction[base+6:base+24].reshape(3,6)
        resultants[:,:3] = rng.normal(size=(3,3))*1000.
        resultants[:,3:] = rng.normal(size=(3,3))*30.
    multipliers = direction[count:].reshape(-1,6)
    multipliers[:,:3] = rng.normal(size=multipliers[:,:3].shape)*1000.
    multipliers[:,3:] = rng.normal(size=multipliers[:,3:].shape)*30.
    direction[owner._fixed] = 0.
    weights = np.r_[owner._coordinate_scale,np.ones(owner._C.shape[0])]
    predicted = (tangent@direction)*weights
    groups = dict(shell=owner._free[owner._free < owner._shell_count],
        beam=owner._free[(owner._free >= owner._shell_count)&(owner._free < beam_end)],
        retained=np.arange(beam_end,count),constraints=np.arange(count,len(residual)))
    norms = {name:float(np.linalg.norm(predicted[rows])) for name,rows in groups.items()}
    assert all(value > 0. for value in norms.values())
    errors = {name:[] for name in groups}
    masks = []
    steps = (1e-4,1e-5,1e-6)
    for h in steps:
        plus = evaluate(driver._advance(driver._state,direction,h))
        minus = evaluate(driver._advance(driver._state,direction,-h))
        masks.append(all(np.array_equal(a,b) for value in (plus,minus) for a,b in zip(base_branches,branches(value))))
        difference = ((plus[0]-minus[0])/(2*h))*weights-predicted
        for name,rows in groups.items():
            errors[name].append(float(np.linalg.norm(difference[rows])/norms[name]))
    assert owner.checkpoint() == before and owner._generation == generation
    pools = threadpool_info()
    assert pools and all(p['num_threads'] == 1 for p in pools)
    passes = any(masks[i] and masks[i+1] and all(errors[name][i] <= 1e-5 and errors[name][i+1] <= 1e-5 for name in groups) for i in range(2))
    outcome = dict(scope='One saved-prefix actual-update directional diagnostic; not qualification or a limit-point certificate',
        status='PASS' if passes else 'MISMATCH_OR_BRANCH_CHANGE', source_parent='af4059a9',
        fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(), checkpoint_sha256=hashlib.sha256(before).hexdigest(),
        load_position=saved.load_position, kind=kind,generation=generation,
        steps=steps, active_branch_counts=[int(np.count_nonzero(b)) for b in base_branches],
        branch_masks_unchanged=masks, weighted_prediction_norms=norms,relative_errors=errors,
        physical_rows=beam_end,retained_rows=count-beam_end,multiplier_rows=len(residual)-count,
        checkpoint_unchanged=True,thread_pools=pools,artifacts=original['artifacts'])
    (root/'diagnose-prefix-v2.json').open('x').write(json.dumps(outcome,indent=2)+'\n')
    print(json.dumps(dict(status=outcome['status'], errors=errors, branch_masks_unchanged=masks)),flush=True)
finally:
    owner.close()
