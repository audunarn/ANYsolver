"""Declared all-S3/fibre unload-reverse-reload extension of accepted nominal state."""
from pathlib import Path
from dataclasses import replace,asdict
import hashlib,json,math,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_q4_algorithmic_pullback import HISTORICAL_POLICY
from stiffened_shell_coupled_plastic_history import definition as base_definition,_shell_activity

root=Path(__file__).resolve().parent
previous=root.parent/'r8-native-displacement-adaptive-dev-20261005-v1'
assert Path(ss.__file__).resolve().is_relative_to(previous/'site-v3')
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
screen=json.loads((root/'all-s3-result-v1.json').read_text())
assert screen['status']=='COMPLETED_SIMULTANEOUS_FLOW'
base=base_definition()
model=replace(base,shell=replace(base.shell,q4_elements=(),s3_elements=((1,2,5),(1,5,4),(2,3,6),(2,6,5))),
              q4_pullback_policy=HISTORICAL_POLICY)
owner=ss.create_analysis(definition=model)
nominal=screen['nominal_target'];targets=(nominal*.25,-nominal,nominal*1.1)
direction=tuple(ss.NodalAction('beam',node,(0.,0.,150.,0.,0.,0.)) for node in (105,205))
record=dict(scope='Declared all-S3 physical-fibre signed displacement history, not capacity qualification',
    artifacts=screen['artifacts'],model_identity=screen['model_identity'],source_parent='8e9121e1',
    targets=targets,limits=dict(max_cutbacks=6,max_attempts=24),accepted=[])
def write():
    (root/'reversal-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
try:
    previous_result=owner.restore((root/'all-s3-prefix-v1.checkpoint').read_bytes())
    def accepted(result):
        global previous_result
        assert result.free_equilibrium_ratio<=1e-8 and result.constraint_max<=1e-9
        _,alpha,families=_shell_activity(result,previous_result)
        increments=[math.fsum(f.plastic_increment) for r in result.beam_fibre_material for f in r.fibres]
        dissipation=[math.fsum(r.incremental_dissipation_j) for r in result.beam_fibre_energy]
        assert all(math.isfinite(d) and d>=0. for d in dissipation)
        record['accepted'].append(dict(target=result.target,amplitude=result.amplitude,
            equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max,shell_alpha_max=alpha,
            shell_active_by_family=families,fibre_increment_min=min(increments),fibre_increment_max=max(increments),
            last_increment_dissipation_j=math.fsum(dissipation)))
        (root/f'reversal-accepted-{len(record["accepted"])}-v1.checkpoint').write_bytes(owner.checkpoint())
        previous_result=result;write()
    try:
        result=owner.solve(direction,targets,displacement_control=ss.DisplacementControl('beam',105,2),
            increment_control=ss.AdaptiveIncrementControl(6,24),max_iterations=20,max_backtracks=12,on_accepted=accepted)
        assert result.status=='completed' and result.target==targets[-1]
        record['status']='COMPLETED_UNLOAD_REVERSE_RELOAD'
    except ss.DisplacementIncrementLimit as error:
        record.update(status='FAILED_LIMIT_PRESERVED_PREFIX',failure=str(error))
    raw=owner.checkpoint();(root/'reversal-prefix-v1.checkpoint').write_bytes(raw)
    record.update(attempts=[asdict(row) for row in owner._displacement_adaptive[0].state.attempts],
                  checkpoint_sha256=hashlib.sha256(raw).hexdigest())
    write();print(json.dumps({k:v for k,v in record.items() if k not in ('artifacts','accepted','attempts')}),flush=True)
finally:owner.close()
if record['status'].startswith('FAILED'):raise SystemExit(1)
