from dataclasses import asdict
import json
import numpy as np
from unittest.mock import patch
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
from examples.stiffened_shell_native_fibre_bl5_material import definition, ACTIONS, CONTROLS

def execute(root):
    owner=ss.create_analysis(definition=definition())
    original=FinitePointDriver._solve_fixed; original_advance=FinitePointDriver._advance
    token=CancellationToken(); observed=[]; amounts=[]
    raw=(root/'failed-prefix-bending-continuation-v1.bin').read_bytes()
    def fixed(self,actions,targets,**kwargs):
        assert len(targets)==1 and abs(targets[0]-.3125)<1e-15, 'one pending comparison only'
        return original(self,actions,targets,**kwargs)
    def advance(self,state,increment,amount):
        amounts.append(float(amount))
        return original_advance(self,state,increment,amount)
    def accepted(result):
        observed.append(dict(factor=result.load_factor, equilibrium=result.free_equilibrium_ratio,
            gap=result.constraint_max, iterations=result.iterations,
            shell=np.asarray(result.shell_layer_alpha).tolist(), beams=np.asarray(result.beam_station_accumulated).tolist()))
        (root/'prefix-pending-comparison-v1.bin').write_bytes(owner.checkpoint())
        token.cancel('one pending comparison accepted')
    try:
        owner.restore(raw)
        with patch.object(FinitePointDriver,'_solve_fixed',fixed), patch.object(FinitePointDriver,'_advance',advance):
            try:owner.solve(ACTIONS,(.65,),on_accepted=accepted,cancellation_token=token,**CONTROLS)
            except BaseException as error:
                outcome=dict(type=type(error).__name__,message=str(error),attempts=[asdict(a) for a in getattr(error,'attempts',())])
            else:outcome=dict(type='returned')
        outcome.update(observed=observed,amounts=amounts,checkpoint_unchanged=owner.checkpoint()==raw)
        (root/'result-pending-comparison-v1.json').write_text(json.dumps(outcome,indent=2))
        return outcome
    finally:owner.close()
