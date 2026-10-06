from dataclasses import asdict
import json
import numpy as np
from unittest.mock import patch
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, cancellation_safe_point
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver, FiniteIncrementFailure
from anysolver._ge_beam3_fibre_cell import FibreCellConjugate
from anysolver._ge_beam3_generalized_cell import GeneralizedCellConjugate
from examples.stiffened_shell_native_fibre_bl5_material import definition, ACTIONS, CONTROLS


def execute(folder,evidence):
    owner=None
    token=CancellationToken(); accepted=[]; amounts=[]; proposals=[]; evaluations=[]; material=[]; terminal=[]
    work=dict(fixed_attempts=0,assemblies=0,advances=0,boundary_proposals=0,physical_cell_responses=0,
              generalized_cell_responses=0,captured_preparations=0,cell_evaluations=0,cell_line_trials=0)
    raw=(evidence/'failed-prefix-bending-continuation-v1.bin').read_bytes()
    original_fixed=FinitePointDriver._solve_fixed;original_advance=FinitePointDriver._advance
    original_assemble=FinitePointDriver._assemble;original_boundary=FinitePointDriver._native_boundary_amount
    original_physical=FibreCellConjugate.response;original_generalized=GeneralizedCellConjugate.response
    stage='compile'
    def fixed(self,actions,targets,**kwargs):
        if work['fixed_attempts']:
            cancellation_safe_point(token,'boundary-screen.stop-after-first-fixed-outcome')
            raise AssertionError('only one changed-source .3125 attempt permitted')
        assert targets==(.3125,) and self._load_factor==.28437500000000004
        work['fixed_attempts']+=1
        try:return original_fixed(self,actions,targets,**kwargs)
        except FiniteIncrementFailure as error:
            terminal.append(dict(type=type(error).__name__,message=str(error),attempt=asdict(error.attempt)))
            token.cancel('boundary screen first terminal rejection captured')
            raise
    def advance(self,state,increment,amount):
        work['advances']+=1;amounts.append(float(amount))
        return original_advance(self,state,increment,amount)
    def boundary(self,state,increment):
        work['boundary_proposals']+=1
        amount=original_boundary(self,state,increment)
        proposals.append(dict(amount=amount,generation=owner._generation,cache_state=self._native_boundary_trial[0] is state))
        return amount
    def assemble(self,state,factor,*args,**kwargs):
        work['assemblies']+=1
        response=original_assemble(self,state,factor,*args,**kwargs)
        evaluations.append(dict(stage=stage,factor=float(factor),relative=float(response[2]),gap=float(response[3])))
        # Retain every actual physical cell branch in material callback records;
        # no second callback/recovery is used for diagnostics.
        return response
    def response(family, original):
        def capture(self,*args,**kwargs):
            out=original(self,*args,**kwargs)
            key='physical_cell_responses' if family=='physical' else 'generalized_cell_responses'
            work[key]+=1;work['cell_evaluations']+=out['evaluations'];work['cell_line_trials']+=out.get('line_trials',0)
            work['captured_preparations']+=int('_trial_state' in out)
            branches=([dict(station=i,fibres=[dict(id=f.fibre_id,branch=f.branch,delta=f.plastic_increment) for f in row['fibres']])
                       for i,row in enumerate(out['stations'])] if family=='physical' else [])
            material.append(dict(stage=stage,family=family,iterations=out['iterations'],evaluations=out['evaluations'],
                line_trials=out.get('line_trials',0),branches=branches))
            return out
        return capture
    def observe(result):
        accepted.append(dict(factor=result.load_factor,equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max,
            iterations=result.iterations,generation=result.generation,shell=np.asarray(result.shell_layer_alpha).tolist(),
            beams=np.asarray(result.beam_station_accumulated).tolist()))
        assert result.load_factor==.3125
        (folder/'accepted.bin').write_bytes(owner.checkpoint())
        token.cancel('boundary screen first .3125 accepted commit')
    outcome={}
    try:
        with patch.object(FinitePointDriver,'_solve_fixed',fixed),patch.object(FinitePointDriver,'_advance',advance),\
             patch.object(FinitePointDriver,'_assemble',assemble),patch.object(FinitePointDriver,'_native_boundary_amount',boundary),\
             patch.object(FibreCellConjugate,'response',response('physical',original_physical)),\
             patch.object(GeneralizedCellConjugate,'response',response('generalized',original_generalized)):
            owner=ss.create_analysis(definition=definition())
            stage='restore'
            owner.restore(raw)
            assert owner.checkpoint()==raw and owner._generation==5
            control_before=asdict(owner._finite_driver._adaptive_state)
            stage='screen'
            try:owner.solve(ACTIONS,(.65,),on_accepted=observe,cancellation_token=token,**CONTROLS)
            except BaseException as error:
                outcome=dict(type=type(error).__name__,message=str(error),attempts=[asdict(a) for a in getattr(error,'attempts',())])
            else:outcome=dict(type='returned')
        screen_pass=(len(accepted)==1 and accepted[0]['factor']==.3125 and accepted[0]['equilibrium']<=1e-8 and accepted[0]['gap']<=1e-9)
        result=dict(screen_pass=screen_pass,outcome=outcome,accepted=accepted,terminal_rejections=terminal,
            amounts=amounts,proposals=proposals,evaluations=evaluations,material_callbacks=material,work_counts=work,
            controller_before=control_before,controller_after=asdict(owner._finite_driver._adaptive_state),
            checkpoint_unchanged=owner.checkpoint()==raw,accepted_factor=owner._finite_driver._load_factor,
            generation=owner._generation,fixture='unchanged original 500N; exact restored pending controller',
            equations_and_acceptance='unchanged 1e-8/1e-9, max_iterations24/max_backtracks12, full-first13 candidates')
        (folder/'result.json').write_text(json.dumps(result,indent=2))
        (folder/'terminal.bin').write_bytes(owner.checkpoint())
        return result
    finally:
        if owner is not None: owner.close()
