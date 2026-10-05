"""Actual GE reference integration checks; source-only, not qualification."""
from pathlib import Path
import hashlib,json,os,sys,time
import numpy as np
import scipy
import pytest
from threadpoolctl import threadpool_info
import anysolver._stiffened_shell_ge_distributing_reference as adapter
import anysolver._stiffened_shell_distributing_footprint as local
import anysolver._stiffened_shell_ge_experimental as owner

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
started=time.monotonic()
paths=[REPO/'src/anysolver'/name for name in (
    '_stiffened_shell_ge_distributing_reference.py','_stiffened_shell_distributing_footprint.py',
    '_stiffened_shell_ge_experimental.py')]
for module,path in zip((adapter,local,owner),paths):
    if Path(module.__file__).resolve()!=path.resolve():raise ValueError('actual source import differs')
if sys.flags.optimize or os.environ.get('NUMBA_DISABLE_JIT')!='1':raise ValueError('unoptimized JIT-off source checks required')
pools=threadpool_info()
if not pools or any(p['num_threads']!=1 for p in pools):raise ValueError('effective numerical pools1 required')
runtime=dict(identity='PRIVATE_GE_DISTRIBUTING_REFERENCE_SOURCE_CHECKS_DEV_V1',
    source_imports=[str(p.resolve()) for p in paths],
    source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    tests_sha256=hashlib.sha256((REPO/'tests/test_stiffened_shell_ge_distributing_reference.py').read_bytes()).hexdigest(),
    numpy_version=np.__version__,scipy_version=scipy.__version__,pytest_version=pytest.__version__,
    effective_pools=pools,jit_disabled=True,production_qualified=False)
(ROOT/'runtime-v1.json').write_text(json.dumps(runtime,indent=2)+'\n',newline='\n')
status=pytest.main(['-q',str(REPO/'tests/test_stiffened_shell_ge_distributing_reference.py'),'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v1')])
runtime.update(exit_code=int(status),checks_seconds=time.monotonic()-started)
(ROOT/'runtime-v1.json').write_text(json.dumps(runtime,indent=2)+'\n',newline='\n')
raise SystemExit(status)
