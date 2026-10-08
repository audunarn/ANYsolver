"""One declared native mixed adaptive history; failed fixed paths remain failed."""
from pathlib import Path
from dataclasses import asdict
import json,os,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from test_stiffened_shell_native_plastic_s3_displacement import definition,compare

root=Path(__file__).resolve().parent;site=root/'site-v3'
assert Path(ss.__file__).resolve().is_relative_to(site)
assert os.environ['NUMBA_DISABLE_JIT']=='1' and not sys.flags.optimize
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
model=definition(True,True)
reference=ss.create_analysis(definition=model);owner=ss.create_analysis(definition=model)
resumed=ss.create_analysis(definition=model)
record=dict(scope='Native mixed adaptive integration history, not parity with failed fixed routes',
    source_parent='4fecd1ea',limits=dict(max_cutbacks=6,max_attempts=24),
    max_iterations=20,max_backtracks=12,pools=threadpool_info(),accepted=[])
def write():
    (root/'program-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
try:
    linear=reference.solve_linear((ss.NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),))
    nominal=float(linear.beam_coordinates[6*reference._beam_index[105]+2])*1.01
    record['nominal_target']=nominal
    direction=(ss.NodalAction('beam',105,(0.,0.,100.,0.,0.,0.)),)
    owner.solve((ss.NodalAction('beam',105,(0.,0.,0.,0.,0.,0.)),),(1.,),max_iterations=20,max_backtracks=12)
    (root/'program-seed-v1.checkpoint').write_bytes(owner.checkpoint())
    def accepted(result):
        assert result.free_equilibrium_ratio<=1e-8 and result.constraint_max<=1e-9
        index=len(record['accepted'])+1
        (root/f'program-accepted-{index}-v1.checkpoint').write_bytes(owner.checkpoint())
        record['accepted'].append(dict(target=result.target,amplitude=result.amplitude,
            equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max,
            q4_alpha=[float(np.max(r.alpha)) for r in result.shell_q4_material],
            s3_alpha=[float(np.max(r.alpha)) for r in result.shell_s3_material],
            beam_fibre_incremental_dissipation=[list(r.incremental_dissipation_j) for r in result.beam_fibre_energy]))
        write()
    try:
        result=owner.solve(direction,(nominal,),displacement_control=ss.DisplacementControl('beam',105,2),
            increment_control=ss.AdaptiveIncrementControl(6,24),max_iterations=20,max_backtracks=12,
            on_accepted=accepted)
        assert result.status=='completed' and result.target==nominal
        assert all(np.max(x.alpha)>0. for x in result.shell_q4_material+result.shell_s3_material)
        record['status']='COMPLETED_DEVELOPMENT_NOT_QUALIFIED'
    except ss.DisplacementIncrementLimit as error:
        result=owner.recover()
        record.update(status='FAILED_LIMIT_PRESERVED_PREFIX',failure=str(error))
    raw=owner.checkpoint();(root/'program-prefix-v1.checkpoint').write_bytes(raw)
    restored=resumed.restore(raw)
    assert resumed.checkpoint()==raw
    if hasattr(result,'history'):compare(result,restored)
    context=owner._displacement_adaptive[0]
    record.update(attempts=[asdict(row) for row in context.state.attempts],exact_prefix_restore=True)
    write()
    summary={k:v for k,v in record.items() if k not in ('pools','accepted','attempts')}
    summary.update(accepted=len(record['accepted']),attempts=len(record['attempts']))
    print(json.dumps(summary),flush=True)
finally:reference.close();owner.close();resumed.close()
if record['status'].startswith('FAILED'):raise SystemExit(1)
