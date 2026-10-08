from pathlib import Path
from dataclasses import replace,asdict
import json,hashlib,math,os,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss,b3_ge
from test_stiffened_shell_native_point_displacement import native_state
from test_stiffened_shell_q4_pullback_owner import _definition
raw=Path(__file__).resolve().parent;repo=raw.parents[2];root=raw/'transition-outputs-v1';root.mkdir(exist_ok=False)
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
definition=_definition(plastic=True,mixed=False)
reference=ss.create_analysis(definition=definition);owner=ss.create_analysis(definition=definition)
record=dict(scope='Existing yielded generalized/Q4J2 force predecessor to adaptive displacement, not qualification',source_parent='8762744c',pools=threadpool_info(),artifacts=identities['artifacts'],accepted=[],status='IN_PROGRESS')
def write(): (root/'result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
def accum(result):
    return np.array([math.fsum(row) for row in result.beam_station_accumulated])
try:
    action=lambda f:(ss.NodalAction('beam',105,(0.,0.,f,0.,0.,0.)),)
    prior=owner.solve(action(1000.),(.5,1.),max_iterations=20,max_backtracks=12)
    nominal=float(owner._finite_driver._state.q[owner._shell_count+6*owner._beam_index[105]+2])
    assert max(max(r) for r in prior.shell_layer_alpha)>0. and max(max(r) for r in prior.beam_station_accumulated)>0.
    record.update(nominal_target=nominal,identity=owner.preflight()['identity'],seed_force_history=[.5,1.])
    prior_native=native_state(owner)
    (root/'seed-v1.checkpoint').write_bytes(owner.checkpoint())
    def accepted(result):
        global prior,prior_native
        (root/f'callback-{len(record["accepted"])+1}-v1.checkpoint').write_bytes(owner.checkpoint())
        current_native=native_state(owner)
        current=np.array([math.fsum(r) for r in current_native['beam_accumulated']]);before=np.array([math.fsum(r) for r in prior_native['beam_accumulated']])
        delta=np.array([math.fsum((*a,*(-b))) for a,b in zip(current_native['beam_accumulated'],prior_native['beam_accumulated'],strict=True)])
        floor=64.*np.finfo(float).eps*np.maximum(abs(current),abs(before))
        assert np.all(delta>=-floor)
        stations=[s for e in result.beam_generalized_material for s in e.stations]
        d=[math.fsum(s.dissipation_per_length) for s in stations]
        assert all(math.isfinite(x) and x>=0. for x in d)
        plastic=[math.fsum(s.plastic_increment) for s in stations]
        flow=bool(np.any(delta>floor)) and any(x>0. for x in plastic) and not np.array_equal(prior_native['beam_plastic'],current_native['beam_plastic'])
        old={r.element_id:r for r in prior.shell_q4_material}
        shell_flow=False;alpha=0.
        for row in result.shell_q4_material:
            before_alpha=old[row.element_id].alpha
            allowance=64.*np.finfo(float).eps*np.maximum(abs(row.alpha),abs(before_alpha))
            assert np.all(row.alpha>=before_alpha-allowance)
            shell_flow=shell_flow or bool(np.any(row.alpha>before_alpha+allowance));alpha=max(alpha,float(max(row.alpha)))
        errors=[abs(density-4000.*i)/max(abs(density),abs(4000.*i),np.finfo(float).tiny) for density,i in zip(d,plastic)]
        assert max(errors)<=1e-10
        assert result.free_equilibrium_ratio<=1e-8 and result.constraint_max<=1e-9
        record['accepted'].append(dict(target=result.target,amplitude=result.amplitude,equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max,alpha_max=float(max(current)),generalized_flow=flow,shell_j2_flow=shell_flow,simultaneous=flow and shell_flow,shell_alpha_max=alpha,dissipation_density_sum=math.fsum(d),max_density_law_relative_error=max(errors)))
        (root/f'accepted-{len(record["accepted"])}-v1.checkpoint').write_bytes(owner.checkpoint());prior=result;prior_native=current_native;write()
    kw=dict(displacement_control=ss.DisplacementControl('beam',105,2),increment_control=ss.AdaptiveIncrementControl(6,24),max_iterations=20,max_backtracks=12,on_accepted=accepted)
    phase='yielded-controller-transition'
    try:
        owner.solve(action(100.),(.99*nominal,1.01*nominal),**kw)
        record['status']='COMPLETED_YIELDED_CONTROLLER_TRANSITION' if any(r['simultaneous'] for r in record['accepted']) else 'COMPLETED_ACTIVITY_INCOMPLETE'
    except ss.DisplacementIncrementLimit as error:record.update(status='FAILED_LIMIT_PRESERVED_PREFIX',phase=phase,failure=str(error))
    (root/'prefix-v1.checkpoint').write_bytes(owner.checkpoint())
    if owner._displacement_adaptive is not None:record['attempts']=[asdict(r) for r in owner._displacement_adaptive[0].state.attempts]
    write();print(json.dumps({k:v for k,v in record.items() if k not in ('pools','artifacts','attempts','accepted')}),flush=True)
finally:reference.close();owner.close()
if record['status']!='COMPLETED_YIELDED_CONTROLLER_TRANSITION':raise SystemExit(1)
