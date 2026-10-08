"""Capture one pending same-law failed trial; no sweep or physics changes."""
from pathlib import Path
from dataclasses import replace, asdict
import json, math
import numpy as np
from scipy import sparse
from unittest.mock import patch
from anymaterial import DNVC208MaterialCurve
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
from examples.stiffened_shell_native_fibre_bl5 import definition


def execute(root):
    folder=root/'rejected-trial-state-v1';folder.mkdir(exist_ok=False)
    model=definition(yield_stress=1e5)
    curve=DNVC208MaterialCurve(1e6,1.05e6,1.1e6,.005,.01,4e6,.2)
    model=replace(model,shell=replace(model.shell,j2_curve=curve),bl5_material_policy=ss.BL5_NATIVE_FIBRE_MATERIAL_V1)
    owner=ss.create_analysis(definition=model)
    raw=(root/'failed-prefix-bending-continuation-v1.bin').read_bytes()
    prefix=owner.restore(raw);driver=owner._finite_driver
    assert owner.checkpoint()==raw and prefix.load_factor==.28437500000000004
    original_assemble=FinitePointDriver._assemble;original_advance=FinitePointDriver._advance
    original_fixed=FinitePointDriver._solve_fixed
    evaluations=[];advances=[];failed={};token=CancellationToken()
    def save_state(name,state):
        arrays={key:getattr(state,key) for key in ('q','frames','cells','resultants','multipliers')}
        if state.shell_anchors is not None:arrays['shell_anchors']=state.shell_anchors
        np.savez(folder/(name+'.npz'),**arrays)
    def mask(value):
        shell=[(np.asarray(a['alpha'])>np.asarray(b['alpha'])).tolist()
               for a,b in zip(value[4],driver._shell_origins)]
        beams=[]
        for a,b in zip(value[5],driver._beam_origins):
            item=[]
            for x,y in zip(a.stations,b.stations):
                if hasattr(x,'rows'):
                    item.extend(float(p[2]+p[3])>float(q[2]+q[3]) for p,q in zip(x.rows,y.rows))
                else:item.append(sum(x.accumulated)>sum(y.accumulated))
            beams.append(item)
        return shell,beams
    def assembled(self,state,factor,*args,**kwargs):
        value=original_assemble(self,state,factor,*args,**kwargs)
        if self is driver:
            assert abs(factor-.3125)<1e-15,'replay load boundary'
            i=len(evaluations);stem='evaluation-%03d'%i
            save_state(stem,state);np.save(folder/(stem+'-R.npy'),value[0])
            sparse.save_npz(folder/(stem+'-K.npz'),value[1])
            evaluations.append(dict(index=i,relative=float(value[2]),gap=float(value[3]),mask=mask(value)))
            (folder/'evaluations.json').write_text(json.dumps(evaluations,indent=2))
        return value
    def advanced(self,state,increment,amount):
        value=original_advance(self,state,increment,amount)
        if self is driver:
            i=len(advances);np.save(folder/('advance-%03d-step.npy'%i),increment)
            advances.append(dict(index=i,amount=float(amount),preceding_evaluation=len(evaluations)-1))
            (folder/'advances.json').write_text(json.dumps(advances,indent=2))
        return value
    def fixed(self,actions,targets,**kwargs):
        assert len(targets)==1 and abs(targets[0]-.3125)<1e-15,'one pending trial only'
        try:return original_fixed(self,actions,targets,**kwargs)
        except BaseException as error:
            trace=error.__traceback__
            while trace:
                if trace.tb_frame.f_code.co_name=='_solve_fixed':
                    local=trace.tb_frame.f_locals
                    for key in ('trial','candidate','residual','matrix','full','changed','old_merit','iteration','factor','relative','gap'):
                        if key in local:failed[key]=local[key]
                trace=trace.tb_next
            raise
    outcome={}
    try:
        with patch.object(FinitePointDriver,'_assemble',assembled),patch.object(FinitePointDriver,'_advance',advanced),patch.object(FinitePointDriver,'_solve_fixed',fixed):
            try:
                owner.solve((ss.NodalAction('beam',105,(0.,0.,500.,0.,0.,0.)),),(.65,),
                    max_iterations=24,max_backtracks=12,increment_control=ss.AdaptiveIncrementControl(4,64),
                    cancellation_token=token,on_accepted=lambda r:token.cancel('one requested replay trial accepted'))
            except BaseException as error:
                outcome=dict(type=type(error).__name__,message=str(error),attempts=[asdict(a) for a in getattr(error,'attempts',())])
            else:outcome=dict(type='unexpected return')
        outcome.update(evaluations=len(evaluations),advances=len(advances),checkpoint_unchanged=owner.checkpoint()==raw)
        (folder/'outcome.json').write_text(json.dumps(outcome,indent=2))
        if not failed:
            raise AssertionError('missing failed Newton state: '+str(outcome))
        state=failed['trial'];save_state('failed-Newton-trial',state)
        save_state('last-backtrack-candidate',failed['candidate'])
        np.save(folder/'failed-Newton-R.npy',failed['residual'])
        sparse.save_npz(folder/'failed-Newton-K.npz',failed['matrix'])
        np.save(folder/'failed-Newton-fullstep.npy',failed['full'])
        for key in ('iteration','factor','relative','gap','old_merit'):
            outcome[key]=float(failed[key])
        factor=failed['factor'];step=failed['full'];residual=failed['residual'];matrix=failed['matrix']
        free=np.r_[owner._free,np.arange(owner._K.shape[0],matrix.shape[0])]
        weights=np.r_[owner._coordinate_scale,np.ones(owner._C.shape[0])]
        linear=matrix@step+residual
        outcome['linear_weighted_relative']=float(np.linalg.norm(linear[free]*weights[free])/max(np.linalg.norm(residual[free]*weights[free]),np.finfo(float).tiny))
        np.save(folder/'linear-residual.npy',linear)
        def evaluate(q):return original_assemble(driver,q,factor,driver._shell_origins,driver._beam_origins,pattern=driver._pattern)
        base=evaluate(state);branch=mask(base)
        direction=np.zeros(len(residual));direction[:owner._shell_count:6]=np.linspace(0.,1e-4,len(owner._shell_ids))
        direction[3:owner._shell_count:6]=np.linspace(0.,2e-4,len(owner._shell_ids))
        direction[4:owner._shell_count:6]=np.linspace(0.,-3e-4,len(owner._shell_ids))
        for i in range(len(owner._beam_ids)):
            start=owner._shell_count+6*i;direction[start+2]=.001*(i+1);direction[start+3:start+6]=(2e-4,-1e-4,3e-4)
        for i in range(len(owner._beam_parts)):
            start=owner._shell_count+driver._beam_nodal+24*i
            direction[start:start+6]=(2e-4,-3e-4,1e-4,-2e-4,1e-4,3e-4)
            direction[start+6:start+24]=owner._coordinate_scale[start+6:start+24]*1e-6
        direction[owner._fixed]=0.;direction[len(state.q):]=np.linspace(1.,2.,len(state.multipliers))
        reports=[]
        for name,vector in (('rich',direction),('Newton',step)):
            expected=matrix@vector;rows=[]
            for h in (1e-4,1e-5,1e-6):
                positive=evaluate(original_advance(driver,state,vector,h));negative=evaluate(original_advance(driver,state,vector,-h))
                actual=(positive[0]-negative[0])/(2*h);error=actual-expected
                np.save(folder/(name+'-h'+str(h)+'-derivative-error.npy'),error)
                top=np.argsort(np.abs(error[free]*weights[free]))[-10:][::-1]
                active_slot=owner._shell_count+6*owner._beam_index[105]+2
                rows.append(dict(h=h,relative=float(np.linalg.norm(error[free]*weights[free])/max(np.linalg.norm(expected[free]*weights[free]),1.)),
                    branch_consistent=mask(positive)==mask(negative)==branch,
                    top_error_slots=free[top].tolist(),top_weighted_errors=(error[free[top]]*weights[free[top]]).tolist(),
                    active_tip_derivative_expected=float(expected[active_slot]),active_tip_derivative_actual=float(actual[active_slot]),
                    positive_merit=max(float(positive[2]),float(positive[3])),negative_merit=max(float(negative[2]),float(negative[3]))))
            reports.append(dict(direction=name,steps=rows))
        outcome['derivatives']=reports;outcome['failed_trial_mask']=branch
        outcome['checkpoint_unchanged_after_probe']=owner.checkpoint()==raw
        (folder/'outcome.json').write_text(json.dumps(outcome,indent=2))
        return outcome
    finally:owner.close()
