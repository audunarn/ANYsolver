from pathlib import Path
import json,os,sys
import numpy,scipy,numba,llvmlite,anysolver,psutil,pytest
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
SITE=Path(os.environ['ANYSOLVER_WEAK_INSTALLED']).resolve()
class Record:
    def pytest_sessionfinish(self,session,exitstatus):
        modules={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items()
            if (n=='anysolver' or n.startswith('anysolver.')) and getattr(m,'__file__',None)}
        pools=threadpool_info()
        errors=[]
        if any(not Path(p).is_relative_to(SITE) for p in modules.values()):errors.append('installed imports escaped')
        if any(p['num_threads']!=1 for p in pools):errors.append('effective pool mismatch')
        if not numba.config.DISABLE_JIT or numba.get_num_threads()!=1:errors.append('Numba mismatch')
        if len(psutil.Process().cpu_affinity())!=1:errors.append('affinity mismatch')
        if errors and session.exitstatus==0:session.exitstatus=1
        (ROOT/'runtime-v1.json').write_text(json.dumps(dict(scope='Continuum weak-P0 development reconstruction/solve; no native/external calibration rerun',
            imports=modules,dependencies={m.__name__:dict(path=m.__file__,version=getattr(m,'__version__',None)) for m in (numpy,scipy,numba,llvmlite,pytest,psutil)},
            pools=pools,affinity=psutil.Process().cpu_affinity(),jit_off=bool(numba.config.DISABLE_JIT),numba_threads=numba.get_num_threads(),
            collected=session.testscollected,failed=session.testsfailed,exit_code=int(session.exitstatus),errors=errors),indent=2)+'\n')
code=pytest.main(['-q','-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-temp-v1'),
    '--junitxml='+str(ROOT/'junit-v1.xml'),str(REPO/'tests/test_r8_bl5_weak_continuum_reference.py')],plugins=[Record()])
raise SystemExit(code)
