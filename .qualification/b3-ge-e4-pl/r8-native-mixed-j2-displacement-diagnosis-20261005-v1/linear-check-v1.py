"""Captured-state linear accuracy screen; no loading-path retry or product edit."""
from pathlib import Path
import json
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_ge_finite_experimental import _State
from anysolver._b2_physical_linear_batch_dev import _accurate_sparse_residual
from test_stiffened_shell_native_plastic_s3_displacement import definition

root=Path(__file__).resolve().parent
captured=np.load(root/'limiting-state-v1.npz',allow_pickle=False)
diagnostic=json.loads((root/'result-v1.json').read_text(encoding='utf-8'))
owner=ss.create_analysis(definition=definition(True,True))
record=dict(scope='Bounded solve-accuracy discriminator at captured state; not stability or qualification',
            source_parent='189ebb84',candidates=[])
try:
    saved=(root/'accepted-zero.checkpoint').read_bytes();owner.restore(saved)
    driver=owner._finite_driver
    state=_State(captured['q'],captured['frames'],captured['cells'],
                 captured['resultants'],captured['multipliers'],None)
    shell=driver._shell_origins;beam=driver._beam_origins
    amplitude=diagnostic['failure']['detail']['amplitude'];pattern=captured['pattern']
    evaluation=driver._assemble(state,0.,shell,beam,applied_load=amplitude*pattern)
    np.testing.assert_array_equal(evaluation[0],captured['residual'])
    residual,tangent=evaluation[:2];free=captured['free'];weights=captured['weights']
    count=owner._K.shape[0];control=ss.DisplacementControl('beam',105,2).dof(owner)
    direction=np.r_[pattern,np.zeros(len(residual)-count)]
    row=np.zeros(len(free));row[np.flatnonzero(free==control)]=1.
    border=sparse.bmat([[tangent[free,:][:,free],sparse.csc_matrix(-direction[free,None])],
                       [sparse.csc_matrix(row[None,:]),None]],format='csc')
    gap=float(state.q[control]-diagnostic['target'])
    rhs=-np.r_[residual[free],gap]
    row_scale=np.r_[weights[free],1./owner._reference_length]
    energy=float(np.max((abs(owner._K)@owner._coordinate_scale)*owner._coordinate_scale))
    columns=np.r_[owner._coordinate_scale,energy/owner._constraint_scale]
    col_scale=np.r_[columns[free],1.]
    baseline=np.linalg.norm(residual[free]*weights[free])
    for scaled in (False,True):
        factor=splu(sparse.diags(row_scale)@border@sparse.diags(col_scale) if scaled else border)
        def solve(value):
            return col_scale*factor.solve(row_scale*value) if scaled else factor.solve(value)
        solution=solve(rhs)
        for refinements in range(3):
            defect=_accurate_sparse_residual(border,solution[:,None],rhs[:,None])[:,0]
            step=np.zeros(len(residual));step[free]=solution[:-1];delta=float(solution[-1])
            trials=[]
            for amount in (1.,.5,2.**-12):
                response=driver._assemble(driver._advance(state,step,amount),0.,shell,beam,
                    applied_load=(amplitude+amount*delta)*pattern)
                trials.append(dict(amount=amount,merit=float(np.linalg.norm(response[0][free]*weights[free])),
                    equilibrium=float(response[2]),gap=float(response[3])))
            record['candidates'].append(dict(scaled=scaled,refinements=refinements,
                weighted_relative_solve_defect=float(np.linalg.norm(defect*row_scale)/max(np.linalg.norm(rhs*row_scale),np.finfo(float).tiny)),
                relative_direction_change=float(np.linalg.norm((step-captured['step'])*columns)/
                                               max(np.linalg.norm(captured['step']*columns),np.finfo(float).tiny)),
                delta=delta,trials=trials))
            if refinements<2:solution-=solve(defect)
    record['baseline_merit']=float(baseline)
    assert owner.checkpoint()==saved
    record['accepted_prefix_unchanged']=True
    (root/'linear-check-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record),flush=True)
finally:owner.close()
