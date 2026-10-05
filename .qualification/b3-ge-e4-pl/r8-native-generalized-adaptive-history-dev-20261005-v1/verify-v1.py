from pathlib import Path
from dataclasses import replace,asdict
import json,hashlib,math,os,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss,b3_ge
from test_stiffened_shell_native_point_displacement import model
raw=Path(__file__).resolve().parent;repo=raw.parents[2];root=raw/'verified-v1';root.mkdir(exist_ok=False)
previous=raw.parent/'r8-native-displacement-adaptive-dev-20261005-v1'
site=previous/'site-v3'
assert Path(ss.__file__).resolve().is_relative_to(site)
assert os.environ['NUMBA_DISABLE_JIT']=='1' and not sys.flags.optimize
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
identities=json.loads((previous/'installed-result-v1.json').read_text())
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
for name,digest in identities['sources'].items():
    checkout=repo if name.startswith('anysolver/') else fem
    assert hashlib.sha256((checkout/'src'/name).read_bytes()).hexdigest()==digest,name
    assert hashlib.sha256((site/name).read_bytes()).hexdigest()==digest,name
base=model('generalized');beams=[]
for native in base.beams:
    element,inertia=native.instantiate();ref=element.operator.reference
    section=b3_ge.EllipsoidalGeneralizedSection(element.section.elastic,element.section.metric,5.,1e6)
    beams.append(b3_ge.define_beam('b3-ge',element.element_id,element.node_ids,ref.coordinates,ref.nodal_triads,section,inertia,quadrature=element.operator.order))
definition=replace(base,beams=tuple(beams))
from dataclasses import fields
from anysolver.control import CancellationToken,SolveCancelled
from test_stiffened_shell_native_point_displacement import native_state,compare
result=json.loads((raw/'outputs-v3/result-v1.json').read_text())
assert result['status']=='COMPLETED_GENERALIZED_SIGNED_HISTORY'
def exact(a,b):
    compare(a,b)
    assert len(a.beam_generalized_material)==len(b.beam_generalized_material)
    for left,right in zip(a.beam_generalized_material,b.beam_generalized_material,strict=True):
        assert left.element_id==right.element_id
        for ls,rs in zip(left.stations,right.stations,strict=True):
            for field in fields(ls):
                lv,rv=getattr(ls,field.name),getattr(rs,field.name)
                if isinstance(lv,np.ndarray):np.testing.assert_array_equal(lv,rv)
                else:assert lv==rv,field.name
first=ss.create_analysis(definition=definition);second=ss.create_analysis(definition=definition)
rows=[]
try:
    seed=(raw/'outputs-v3/accepted-1-v1.checkpoint').read_bytes()
    prior=first.restore(seed);other=second.restore(seed);exact(prior,other)
    assert first.checkpoint()==second.checkpoint()==seed
    kw=dict(displacement_control=ss.DisplacementControl('beam',105,2),increment_control=ss.AdaptiveIncrementControl(6,24),max_iterations=20,max_backtracks=12)
    direction=(ss.NodalAction('beam',105,(0.,0.,100.,0.,0.,0.)),)
    cancelled=CancellationToken();cancelled.cancel('before continued generalized history')
    try:first.solve(direction,(result['accepted'][1]['target'],),cancellation_token=cancelled,**kw)
    except SolveCancelled:pass
    else:raise AssertionError('cancellation required')
    assert first.checkpoint()==seed
    for index,row in enumerate(result['accepted'][1:],2):
        before=native_state(first)
        current=first.solve(direction,(row['target'],),**kw)
        again=second.solve(direction,(row['target'],),**kw)
        exact(current,again);assert first.checkpoint()==second.checkpoint()
        after=native_state(first)
        for name in after:np.testing.assert_array_equal(after[name],native_state(second)[name])
        alpha=np.array([math.fsum(r) for r in after['beam_accumulated']])-np.array([math.fsum(r) for r in before['beam_accumulated']])
        assert np.any(alpha>0.)
        assert not np.array_equal(before['beam_plastic'],after['beam_plastic'])
        stations=[s for e in current.beam_generalized_material for s in e.stations]
        increments=[math.fsum(s.plastic_increment) for s in stations]
        assert any(i>0. for i in increments)
        density=[math.fsum(s.dissipation_per_length) for s in stations]
        assert all(d>=0. for d in density)
        # Frozen yield strength5: consistent law-specific incremental density.
        errors=[abs(d-5.*i)/max(abs(d),abs(5.*i),np.finfo(float).tiny) for d,i in zip(density,increments)]
        assert max(errors)<=1e-10
        assert current.free_equilibrium_ratio<=1e-8 and current.constraint_max<=1e-9
        rows.append(dict(target=current.target,amplitude=current.amplitude,equilibrium=current.free_equilibrium_ratio,gap=current.constraint_max,accumulation_growth_max=float(max(alpha)),changed_native_plastic=True,max_dissipation_law_relative_error=max(errors)))
        (root/f'continued-{index}-v1.checkpoint').write_bytes(first.checkpoint())
        prior=current
    final=first.checkpoint()
    (root/'final-v1.checkpoint').write_bytes(final)
    record=dict(status='PASSED_GENERALIZED_RESTART_NOT_QUALIFIED',model_identity=first.preflight()['identity'],artifacts=identities['artifacts'],exact_checkpoint=True,complete_generalized_recovery=True,cancel_before_trial=True,rows=rows,source_hashes={str(f.relative_to(repo)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (repo/'tests/test_stiffened_shell_native_point_displacement.py',repo/'tests/test_stiffened_shell_ge_experimental.py')})
    (root/'result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k not in ('artifacts','source_hashes','rows')}),flush=True)
finally:first.close();second.close()
