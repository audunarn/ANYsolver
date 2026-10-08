from pathlib import Path
import json
import numpy as np
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_ge_finite_experimental import _State
from test_stiffened_shell_ge_distributing_material import definition, actions
ROOT=Path(__file__).resolve().parent
owner=ss.create_analysis(definition=definition())
try:
    owner.restore((ROOT/'failed-prefix-v9.bin').read_bytes())
    driver=owner._finite_driver
    with np.load(ROOT/'failed-base-v9.npz') as data:
        state=_State(*(data[name].copy() for name in ('q','frames','cells','resultants','multipliers')))
        direction=data['direction'].copy();pattern=data['pattern'].copy()
    def evaluate(state):
        return driver._assemble(state,1.01,driver._shell_origins,driver._beam_origins,pattern=pattern)
    base=evaluate(state);weights=owner._coordinate_scale[owner._free]
    predicted=(base[1]@direction)[owner._free]*weights
    fd=[]
    for h in (1e-5,1e-6,1e-7):
        observed=(evaluate(driver._advance(state,direction,h))[0]-evaluate(driver._advance(state,direction,-h))[0])/(2*h)
        fd.append(dict(h=h,relative=float(np.linalg.norm(observed[owner._free]*weights-predicted)/np.linalg.norm(predicted))))
    trials=[]
    for alpha in (2.**-16,2.**-17,2.**-18,2.**-19,2.**-20):
        trial=evaluate(driver._advance(state,direction,alpha))
        trials.append(dict(alpha=alpha,relative=trial[2]))
    result=dict(scope='saved-state continuation discriminator, no qualification',base=base[2],free_fd=fd,trials=trials,
        maximum_correction=float(np.max(np.abs(direction[:owner._shell_count+6*len(owner._beam_ids)]))))
    # A separate, explicitly smaller increment exercises lifecycle behavior;
    # it neither replaces nor qualifies the retained failed 1.01 target.
    try:
        continued=owner.solve(actions(),(1.0001,),max_iterations=24,max_backtracks=16)
        result['small_increment']=dict(status=continued.status,factors=continued.accepted_factors,
            equilibrium=continued.free_equilibrium_ratio)
    except ss.FiniteIncrementFailure as error:
        result['small_increment']=error.attempt.__dict__
    (ROOT/'replay-v10.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,allow_nan=False))
finally:owner.close()
