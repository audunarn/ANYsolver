"""One declared four-step engineering programme; no law or budget sweep."""
from pathlib import Path
from dataclasses import asdict
import json, os, sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_displacement_corrector import DisplacementCorrectorFailure
from test_stiffened_shell_native_plastic_s3_displacement import definition

root=Path(__file__).resolve().parent
assert os.environ['NUMBA_DISABLE_JIT']=='1' and not sys.flags.optimize
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
model=definition(True,True);reference=ss.create_analysis(definition=model)
owner=ss.create_analysis(definition=model)
record=dict(scope='Fixed quarter-target mixed shell-J2 programme; not qualification',
            source_parent='189ebb84',fractions=[.25,.5,.75,1.],pools=threadpool_info(),accepted=[])
out=root/'program-result-v1.json'
def write():out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
try:
    linear=reference.solve_linear((ss.NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),))
    nominal=float(linear.beam_coordinates[6*reference._beam_index[105]+2])*1.01
    record['nominal_target']=nominal
    direction=(ss.NodalAction('beam',105,(0.,0.,100.,0.,0.,0.)),)
    owner.solve((ss.NodalAction('beam',105,(0.,0.,0.,0.,0.,0.)),),(1.,),
                max_iterations=20,max_backtracks=12)
    (root/'program-seed-v1.checkpoint').write_bytes(owner.checkpoint())
    def accepted(result):
        index=len(record['accepted'])+1
        (root/f'program-accepted-{index}-v1.checkpoint').write_bytes(owner.checkpoint())
        record['accepted'].append(dict(target=result.target,amplitude=result.amplitude,
            equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max,
            q4_alpha=[float(np.max(r.alpha)) for r in result.shell_q4_material],
            s3_alpha=[float(np.max(r.alpha)) for r in result.shell_s3_material],
            beam_fibre_incremental_dissipation=[list(r.incremental_dissipation_j) for r in result.beam_fibre_energy]))
        write()
    try:
        result=owner.solve(direction,tuple(nominal*f for f in record['fractions']),
            displacement_control=ss.DisplacementControl('beam',105,2),
            max_iterations=20,max_backtracks=12,on_accepted=accepted)
        assert len(record['accepted'])==4 and result.free_equilibrium_ratio<=1e-8
        assert result.constraint_max<=1e-9
        record['status']='COMPLETED'
    except DisplacementCorrectorFailure as error:
        record.update(status='FAILED',failure=dict(message=str(error),detail=asdict(error.detail)))
        (root/'program-prefix-v1.checkpoint').write_bytes(owner.checkpoint())
    write();print(json.dumps(record),flush=True)
finally:reference.close();owner.close()
if record['status']!='COMPLETED':raise SystemExit(1)
