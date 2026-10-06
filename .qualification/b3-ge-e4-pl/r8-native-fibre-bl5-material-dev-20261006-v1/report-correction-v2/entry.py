from pathlib import Path
import json, sys
import numpy, scipy, numba, llvmlite, psutil, anysolver, pytest
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent; EVIDENCE=ROOT.parent;REPO=EVIDENCE.parents[2]
CI=EVIDENCE.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
SITE=(EVIDENCE/'installed-wheel-v1').resolve()
dependencies={m.__name__:dict(path=str(Path(m.__file__).resolve()),version=m.__version__)
    for m in (numpy,scipy,numba,llvmlite)}
(ROOT/'dependency-preflight.json').write_text(json.dumps(dependencies,indent=2))
for m,v in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert m.__version__==v and Path(m.__file__).resolve().is_relative_to(CI.resolve())
assert Path(anysolver.__file__).resolve().is_relative_to(SITE)
assert len(psutil.Process().cpu_affinity())==1 and numba.config.DISABLE_JIT and numba.get_num_threads()==1
assert all(p['num_threads']==1 for p in threadpool_info())
class Record:
    def pytest_sessionfinish(self,session,exitstatus):
        modules={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items()
            if (n=='anysolver' or n.startswith('anysolver.')) and getattr(m,'__file__',None)}
        assert all(Path(p).is_relative_to(SITE) for p in modules.values())
        assert all(p['num_threads']==1 for p in threadpool_info())
        (ROOT/'runtime.json').write_text(json.dumps(dict(exit_code=int(exitstatus),collected=session.testscollected,
            failed=session.testsfailed,dependencies=dependencies,imports=modules,pools=threadpool_info(),
            affinity=psutil.Process().cpu_affinity(),jit_disabled=bool(numba.config.DISABLE_JIT)),indent=2))
        reports=list((ROOT/'pytest-report-v2').rglob('accepted-report.json'))
        if reports:
            assert len(reports)==1
            (ROOT/'result-installed-report-v2.json').write_bytes(reports[0].read_bytes())
args=['-q','-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-report-v2'),
    '--junitxml='+str(ROOT/'junit.xml'),str(REPO/'tests/test_stiffened_shell_native_fibre_bl5_material.py')+
    '::test_public_partial_report_matches_final_accepted_state']
raise SystemExit(pytest.main(args,plugins=[Record()]))
