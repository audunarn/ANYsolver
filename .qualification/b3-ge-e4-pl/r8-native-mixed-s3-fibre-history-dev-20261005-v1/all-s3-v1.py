"""One installed, fixed-law simultaneous mixed-shell/fibre development screen."""
from pathlib import Path
from dataclasses import replace,asdict
import hashlib,json,math,os,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_q4_algorithmic_pullback import HISTORICAL_POLICY
from stiffened_shell_coupled_plastic_history import definition as base_definition,_shell_activity

root=Path(__file__).resolve().parent;repo=root.parents[2]
previous=root.parent/'r8-native-displacement-adaptive-dev-20261005-v1'
site=previous/'site-v3'
assert Path(ss.__file__).resolve().is_relative_to(site)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
installed=json.loads((previous/'installed-result-v1.json').read_text())
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
for name,digest in installed['sources'].items():
    checkout=repo if name.startswith('anysolver/') else fem
    assert hashlib.sha256((checkout/'src'/name).read_bytes()).hexdigest()==digest,name
for item in installed['artifacts'].values():
    assert hashlib.sha256(Path(item['wheel']).read_bytes()).hexdigest()==item['sha256']
base=base_definition()
model=replace(base,shell=replace(base.shell,q4_elements=(),s3_elements=((1,2,5),(1,5,4),(2,3,6),(2,6,5))))
model=replace(model,q4_pullback_policy=HISTORICAL_POLICY)
reference=ss.create_analysis(definition=model);owner=ss.create_analysis(definition=model)
record=dict(scope='Fixed-law native all-S3 two-stiffener simultaneous-flow screen, not qualification',
    source_parent='8e9121e1',artifacts=installed['artifacts'],pools=threadpool_info(),
    definition_source_sha256=hashlib.sha256((repo/'examples/stiffened_shell_coupled_plastic_history.py').read_bytes()).hexdigest(),
    shell_q4=model.shell.q4_elements,shell_s3=model.shell.s3_elements,
    limits=dict(max_cutbacks=6,max_attempts=24),accepted=[])
def write():
    (root/'all-s3-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
try:
    actions=tuple(ss.NodalAction('beam',node,(0.,0.,1500.,0.,0.,0.)) for node in (105,205))
    linear=reference.solve_linear(actions)
    nominal=float(linear.beam_coordinates[6*reference._beam_index[105]+2])
    direction=tuple(ss.NodalAction('beam',node,(0.,0.,150.,0.,0.,0.)) for node in (105,205))
    zero=tuple(ss.NodalAction('beam',node,(0.,0.,0.,0.,0.,0.)) for node in (105,205))
    previous_result=owner.solve(zero,(1.,),max_iterations=20,max_backtracks=12)
    record['nominal_target']=nominal;record['model_identity']=owner.preflight()['identity']
    (root/'all-s3-seed-v1.checkpoint').write_bytes(owner.checkpoint())
    def accepted(result):
        global previous_result
        assert result.free_equilibrium_ratio<=1e-8 and result.constraint_max<=1e-9
        shell_active,alpha,families=_shell_activity(result,previous_result)
        increments=[math.fsum(fibre.plastic_increment) for station in result.beam_fibre_material for fibre in station.fibres]
        dissipation=[math.fsum(row.incremental_dissipation_j) for row in result.beam_fibre_energy]
        assert all(math.isfinite(d) and d>=0. for d in dissipation)
        fibre_active=any(abs(math.fsum(f.plastic_increment))>64.*np.finfo(float).eps*max(map(abs,f.plastic_increment))
                         for station in result.beam_fibre_material for f in station.fibres)
        record['accepted'].append(dict(target=result.target,amplitude=result.amplitude,
            equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max,shell_alpha_max=alpha,
            shell_active_by_family=families,fibre_active=fibre_active,
            simultaneous_all=all(families.values()) and fibre_active and math.fsum(dissipation)>0.,
            fibre_increment_min=min(increments),fibre_increment_max=max(increments),
            last_increment_dissipation_j=math.fsum(dissipation)))
        (root/f'all-s3-accepted-{len(record["accepted"])}-v1.checkpoint').write_bytes(owner.checkpoint())
        previous_result=result;write()
    try:
        result=owner.solve(direction,(nominal,),displacement_control=ss.DisplacementControl('beam',105,2),
            increment_control=ss.AdaptiveIncrementControl(6,24),max_iterations=20,max_backtracks=12,
            on_accepted=accepted)
        record['status']='COMPLETED_SIMULTANEOUS_FLOW' if any(row['simultaneous_all'] for row in record['accepted']) else 'COMPLETED_ACTIVITY_INCOMPLETE'
    except ss.DisplacementIncrementLimit as error:
        record.update(status='FAILED_LIMIT_PRESERVED_PREFIX',failure=str(error))
    (root/'all-s3-prefix-v1.checkpoint').write_bytes(owner.checkpoint())
    if owner._displacement_adaptive is not None:
        record['attempts']=[asdict(row) for row in owner._displacement_adaptive[0].state.attempts]
    write();print(json.dumps({k:v for k,v in record.items() if k not in ('artifacts','pools','accepted','attempts')}),flush=True)
finally:reference.close();owner.close()
if record['status']!='COMPLETED_SIMULTANEOUS_FLOW':raise SystemExit(1)
