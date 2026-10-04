"""Focused source development checks; no installed qualification claim."""
from pathlib import Path
import hashlib,json,os,sys,time
import numpy as np
import scipy
import pytest
from threadpoolctl import threadpool_info
import anysolver._stiffened_shell_distributing_footprint as component

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
started=time.monotonic()
expected=REPO/'src/anysolver/_stiffened_shell_distributing_footprint.py'
if Path(component.__file__).resolve()!=expected.resolve():raise ValueError('actual source import differs')
if sys.flags.optimize or os.environ.get('NUMBA_DISABLE_JIT')!='1':raise ValueError('unoptimized JIT-off source checks required')
pools=threadpool_info()
if not pools or any(p['num_threads']!=1 for p in pools):raise ValueError('effective numerical pools1 required')
runtime=dict(identity='PRIVATE_DISTRIBUTING_REFERENCE_LINEAR_SOURCE_CHECKS_DEV_V1',
    source_import=str(expected.resolve()),source_sha256=hashlib.sha256(expected.read_bytes()).hexdigest(),
    tests_sha256=hashlib.sha256((REPO/'tests/test_stiffened_shell_distributing_footprint.py').read_bytes()).hexdigest(),
    numpy_version=np.__version__,scipy_version=scipy.__version__,pytest_version=pytest.__version__,
    effective_pools=pools,jit_disabled=True,production_qualified=False)
(ROOT/'runtime-v1.json').write_text(json.dumps(runtime,indent=2)+'\n',newline='\n')
status=pytest.main(['-q',str(REPO/'tests/test_stiffened_shell_distributing_footprint.py'),'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v1')])
runtime.update(exit_code=int(status),checks_seconds=time.monotonic()-started)
(ROOT/'runtime-v1.json').write_text(json.dumps(runtime,indent=2)+'\n',newline='\n')
raise SystemExit(status)
