from pathlib import Path
import hashlib,json,os,sys,time
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss

raw=Path(__file__).resolve().parent;repo=raw.parents[2];site=raw/'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(site)
prior=json.loads((raw/'installed-runtime-v1.json').read_text(encoding='utf-8'))
assert prior['exit_code']==0 and len(prior['consumers'])==2 and all(c['exact_completed_checkpoint'] for c in prior['consumers'].values())
for relative,digest in prior['sources'].items():
    assert hashlib.sha256((site/relative).read_bytes()).hexdigest()==digest
    if relative.startswith('anysolver/'):
        assert hashlib.sha256((repo/'src'/relative).read_bytes()).hexdigest()==digest
assert os.environ['NUMBA_DISABLE_JIT']=='1' and not sys.flags.optimize
import scipy.linalg
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
test=repo/'tests/test_stiffened_shell_native_fibre_s3_displacement_identity.py'
started=time.monotonic()
status=pytest.main(['-q',str(test),'-p','no:cacheprovider','--basetemp',str(raw/'pytest-identity-v1'),
    '-o','junit_family=legacy','--junitxml',str(raw/'identity-v1.xml')])
record=dict(scope='Supporting-review fibre S3 framing and direct corrector negatives on same installed candidate; no main suite replay',
    status=int(status),seconds=time.monotonic()-started,test_sha256=hashlib.sha256(test.read_bytes()).hexdigest(),
    artifacts=prior['artifacts'],pools=pools,production_qualified=False)
(raw/'identity-runtime-v1.json').open('x',encoding='utf-8').write(json.dumps(record,indent=2)+'\n')
raise SystemExit(status)
