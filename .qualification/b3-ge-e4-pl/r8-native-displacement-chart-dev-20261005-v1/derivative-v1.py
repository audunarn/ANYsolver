from pathlib import Path
import hashlib,json,os,sys
import numpy as np
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer
root=Path(__file__).resolve().parent;repo=root.parents[2];site=root/'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(site) and Path(consumer.__file__).resolve().is_relative_to(site)
assert os.environ['NUMBA_DISABLE_JIT']=='1' and not sys.flags.optimize
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
artifacts=json.loads((root/'artifact-v1.json').read_text())['artifacts']
old=json.loads((root.parent/'r8-native-displacement-adaptive-dev-20261005-v1/installed-result-v1.json').read_text())
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
sources={}
for name in old['sources']:
    checkout=repo if name.startswith('anysolver/') else fem
    digest=hashlib.sha256((checkout/'src'/name).read_bytes()).hexdigest()
    assert hashlib.sha256((site/name).read_bytes()).hexdigest()==digest,name
    sources[name]=digest
for item in artifacts.values():assert hashlib.sha256(Path(item['wheel']).read_bytes()).hexdigest()==item['sha256']
from test_stiffened_shell_q4_pullback_owner import _definition
from examples.stiffened_shell_coupled_s3_adaptive_history import definition as s3_definition
cases=[('q4-generalized-j2',_definition(plastic=True,mixed=False),'native_generalized_q4_j2_history/unloaded-v1.bin'),('s3-fibre-j2',s3_definition(),'native_s3_fibre_history/unloaded-v1.bin')]
record=dict(scope='Actual additive-chart directional derivatives, fixed accepted predecessor, not qualification',cases=[])
for name,model,fixture in cases:
    owner=ss.create_analysis(definition=model)
    try:
        saved=(repo/'tests/data'/fixture).read_bytes();before=owner.restore(saved);owner.rebase_rotations(before.generation)
        checkpoint=owner.checkpoint();driver=owner._finite_driver;state=driver._state
        parents=(driver._shell_predecessors,driver._beam_predecessors)
        evaluate=lambda trial:driver._assemble(trial,0.,*parents,applied_load=owner.recover().applied_dead_load)
        residual,tangent,*_=evaluate(state)
        rng=np.random.default_rng(260105)
        direction=np.zeros(len(residual));rows=direction[:owner._shell_count].reshape(-1,6)
        rows[:,:3]=rng.normal(size=rows[:,:3].shape)*1e-5;rows[:,3:]=rng.normal(size=rows[:,3:].shape)*1e-4
        direction[owner._fixed]=0.;predicted=tangent@direction
        weights=np.r_[owner._coordinate_scale,np.ones(owner._C.shape[0])]
        denominator=max(float(np.linalg.norm(predicted*weights)),np.finfo(float).tiny);errors=[]
        for h in (1e-4,1e-5,1e-6):
            plus=evaluate(driver._advance(state,direction,h))[0];minus=evaluate(driver._advance(state,direction,-h))[0]
            errors.append(float(np.linalg.norm(((plus-minus)/(2*h)-predicted)*weights))/denominator)
        assert owner.checkpoint()==checkpoint
        record['cases'].append(dict(name=name,steps=[1e-4,1e-5,1e-6],relative_errors=errors,plateau_pass=sum(e<=1e-6 for e in errors)>=2,checkpoint_unchanged=True))
    finally:owner.close()
(root/'derivative-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record),flush=True)
if not all(r['plateau_pass'] for r in record['cases']):raise SystemExit(1)
