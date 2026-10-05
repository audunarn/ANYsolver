from pathlib import Path
from dataclasses import replace,asdict
import json,hashlib,math,os,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss,b3_ge
from test_stiffened_shell_native_point_displacement import model
root=Path(__file__).resolve().parent;repo=root.parents[2]
previous=root.parent/'r8-native-displacement-adaptive-dev-20261005-v1'
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
reference=ss.create_analysis(definition=definition);owner=ss.create_analysis(definition=definition)
record=dict(scope='Frozen generalized yielding point model; distinct adaptive displacement history, not qualification',source_parent='b53cb296',pools=threadpool_info(),artifacts=identities['artifacts'],accepted=[],status='IN_PROGRESS')
def write(): (root/'result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
def accum(result):
    return np.array([math.fsum(s.accumulated) for e in result.beam_generalized_material for s in e.stations])
try:
    action=lambda f:(ss.NodalAction('beam',105,(0.,0.,f,0.,0.,0.)),)
    linear=reference.solve_linear(action(250.));nominal=float(linear.beam_coordinates[6*reference._beam_index[105]+2])
    record.update(nominal_target=nominal,identity=owner.preflight()['identity'])
    prior=owner.solve(action(0.),(1.,),max_iterations=20,max_backtracks=12)
    (root/'seed-v1.checkpoint').write_bytes(owner.checkpoint())
    def accepted(result):
        global prior
        current=accum(result);before=accum(prior)
        assert current.shape==before.shape and len(current)
        delta=current-before;floor=64.*np.finfo(float).eps*np.maximum(abs(current),abs(before))
        assert np.all(delta>=-floor)
        stations=[s for e in result.beam_generalized_material for s in e.stations]
        d=[math.fsum(s.dissipation_per_length) for s in stations]
        assert all(math.isfinite(x) and x>=0. for x in d)
        plastic=[math.fsum(x) for s in stations for x in s.plastic_increment]
        flow=bool(np.any(delta>floor)) and any(abs(x)>0. for x in plastic)
        assert result.free_equilibrium_ratio<=1e-8 and result.constraint_max<=1e-9
        record['accepted'].append(dict(target=result.target,amplitude=result.amplitude,equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max,alpha_max=float(max(current)),generalized_flow=flow,dissipation_density_sum=math.fsum(d)))
        (root/f'accepted-{len(record["accepted"])}-v1.checkpoint').write_bytes(owner.checkpoint());prior=result;write()
    kw=dict(displacement_control=ss.DisplacementControl('beam',105,2),increment_control=ss.AdaptiveIncrementControl(6,24),max_iterations=20,max_backtracks=12,on_accepted=accepted)
    phase='loading'
    try:
        owner.solve(action(100.),(nominal,),**kw)
        if not any(r['generalized_flow'] for r in record['accepted']): record['status']='COMPLETED_ACTIVITY_INCOMPLETE'
        else:
            phase='signed-history'
            owner.solve(action(100.),(.25*nominal,-nominal,1.1*nominal),**kw)
            record['status']='COMPLETED_GENERALIZED_SIGNED_HISTORY'
    except ss.DisplacementIncrementLimit as error:record.update(status='FAILED_LIMIT_PRESERVED_PREFIX',phase=phase,failure=str(error))
    (root/'prefix-v1.checkpoint').write_bytes(owner.checkpoint())
    if owner._displacement_adaptive is not None:record['attempts']=[asdict(r) for r in owner._displacement_adaptive[0].state.attempts]
    write();print(json.dumps({k:v for k,v in record.items() if k not in ('pools','artifacts','attempts','accepted')}),flush=True)
finally:reference.close();owner.close()
if record['status']!='COMPLETED_GENERALIZED_SIGNED_HISTORY':raise SystemExit(1)
