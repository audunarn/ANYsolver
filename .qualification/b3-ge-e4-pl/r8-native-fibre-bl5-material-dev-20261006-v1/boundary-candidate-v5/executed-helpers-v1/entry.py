from pathlib import Path
import hashlib, json, os, sys
import numpy, scipy, numba, llvmlite, psutil, anysolver
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent;EVIDENCE=ROOT.parent;REPO=EVIDENCE.parents[2]
phase=os.environ['BOUNDARY_PHASE'];folder=ROOT/phase
CI=EVIDENCE.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2';SITE=(REPO/'src').resolve()
dependencies={m.__name__:dict(path=str(Path(m.__file__).resolve()),version=m.__version__) for m in (numpy,scipy,numba,llvmlite)}
(folder/'dependency-preflight.json').write_text(json.dumps(dependencies,indent=2))
for m,v in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert m.__version__==v and Path(m.__file__).resolve().is_relative_to(CI.resolve()),dependencies
assert Path(anysolver.__file__).resolve().is_relative_to(SITE)
assert len(psutil.Process().cpu_affinity())==1 and numba.config.DISABLE_JIT and numba.get_num_threads()==1
assert all(p['num_threads']==1 for p in threadpool_info())
try:
    if phase.startswith('helpers'):
        import pytest
        status=pytest.main(['-q','tests/test_native_fibre_boundary_proposal.py',
            'tests/test_stiffened_shell_native_fibre_bl5_material.py::test_policy_admission_and_force_only_refusals',
            'tests/test_stiffened_shell_native_fibre_bl5_material.py::test_policy_restore_load_and_envelope_refusals_are_atomic',
            '--basetemp',str(folder/'tmp')])
        (folder/'result.json').write_text(json.dumps(dict(pytest_exit_code=int(status))))
        if status:raise SystemExit(status)
    elif phase=='screen-v1':
        import screen
        result=screen.execute(folder,EVIDENCE)
        print(json.dumps({k:result[k] for k in ('screen_pass','outcome','accepted','work_counts')}))
        if not result['screen_pass']:raise AssertionError('single authorized boundary screen did not pass; stop global campaign')
    else:raise ValueError('unregistered boundary candidate phase')
finally:
    modules={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items()
        if (n=='anysolver' or n.startswith('anysolver.')) and getattr(m,'__file__',None)}
    assert all(Path(p).is_relative_to(SITE) for p in modules.values())
    assert all(p['num_threads']==1 for p in threadpool_info())
    (folder/'runtime.json').write_text(json.dumps(dict(dependencies=dependencies,imports=modules,
        source_hashes={n:hashlib.sha256(Path(p).read_bytes()).hexdigest() for n,p in modules.items()},
        pools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),jit_disabled=bool(numba.config.DISABLE_JIT)),indent=2)+'\n')
