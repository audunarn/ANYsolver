import os, sys, json
from pathlib import Path
sys.path[:0] = [str(Path.cwd()/'src'), str(Path.cwd()/'tests')]
import numpy as np
from threadpoolctl import threadpool_info
from test_stiffened_shell_ge_physical_fibre_finite import _yielding_definition
from test_stiffened_shell_ge_physical_fibre_linear import _definition
from test_stiffened_shell_ge_experimental import _panel
from anysolver.stiffened_shell import create_analysis, NodalAction
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
print(json.dumps({'python':sys.version,'threads':threadpool_info(),'jit':os.environ.get('NUMBA_DISABLE_JIT')}))
for name,definition,load in (
    ('generalized-s3',_panel(),1000.),
    ('physical-s3',_definition(True,True),1000.),
    ('physical-s3-small',_definition(True,True),100.),
    ('yielded-q4',_yielding_definition(),1000.)):
    owner=create_analysis(definition=definition)
    driver=FinitePointDriver(owner)
    original=driver._assemble
    n=[0]
    def traced(*args,**kwargs):
        value=original(*args,**kwargs); n[0]+=1
        print(json.dumps({'case':name,'eval':n[0],'relative':value[2],
            'gap':value[3],'resmax':float(np.max(np.abs(value[0]))),
            'histmax':max((max((sum(getattr(s,'accumulated',(0.,0.))) for s in h.stations),default=0.) for h in value[5]),default=0.)}),flush=True)
        return value
    driver._assemble=traced
    try:
        result=driver.solve((NodalAction('beam',105,(0.,0.,load,0.,0.,0.)),),(.5,1.))
        print(json.dumps({'case':name,'status':'completed','generation':result.generation}))
    except Exception as error:
        print(json.dumps({'case':name,'failure':type(error).__name__,'detail':str(error)}))
