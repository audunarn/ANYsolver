from pathlib import Path
import hashlib,json,subprocess,sys,time
import pytest
from anysolver import stiffened_shell as ss
from threadpoolctl import threadpool_info
root = Path(__file__).resolve().parent
repo = root.parents[2]
previous = root.parent/'r8-distributing-native-material-dev-20261004-v1'
site = previous/'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(site)
old = json.loads((previous/'installed-runtime-v1.json').read_text(encoding='utf-8'))
for name,digest in old['sources'].items():
    assert hashlib.sha256((site/name).read_bytes()).hexdigest() == digest
for artifact in old['artifacts'].values():
    assert hashlib.sha256(Path(artifact['wheel']).read_bytes()).hexdigest() == artifact['sha256']
test = repo/'tests/test_stiffened_shell_staged_load_owner_experimental.py'
assert test.read_bytes().replace(b'\r\n',b'\n') == subprocess.check_output(['git','show','cab437fb:tests/'+test.name],cwd=repo).replace(b'\r\n',b'\n')
targets = [str(test)+'::'+name for name in (
    'test_single_stage_matches_legacy_and_keeps_legacy_checkpoint_contract',
    'test_stripped_tampered_and_changed_future_checkpoint_are_atomic')]
started = time.monotonic()
status = pytest.main(['-q',*targets,'-p','no:cacheprovider','--basetemp',str(root/'baseline-pytest-v2')])
pools = threadpool_info()
assert pools and all(p['num_threads'] == 1 for p in pools)
(root/'baseline-result-v2.json').open('x').write(json.dumps(dict(
    scope='Two old binary/JSON test assumptions on prior unchanged installed product; not candidate acceptance',
    exit_code=int(status),seconds=time.monotonic()-started,targets=targets,
    test_sha256=hashlib.sha256(test.read_bytes()).hexdigest(),artifacts=old['artifacts'],pools=pools),indent=2)+'\n')
raise SystemExit(status)
