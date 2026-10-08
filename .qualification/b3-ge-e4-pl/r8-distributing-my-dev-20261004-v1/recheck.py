from pathlib import Path
import hashlib,json,os,sys
import pytest
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
record=dict(pools=pools,sources={n:hashlib.sha256((REPO/n).read_bytes()).hexdigest() for n in ('scripts/r8_e02_distributing_my.py','tests/test_r8_e02_distributing_my.py')})
(ROOT/'recheck-runtime.json').open('x',encoding='utf-8').write(json.dumps(record,indent=2)+'\n')
raise SystemExit(pytest.main(['-q',str(REPO/'tests/test_r8_e02_distributing_my.py')+'::test_my_reconstruction_and_malformed_identity','-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-recheck')]))
