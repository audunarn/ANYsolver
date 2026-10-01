"""Prospective environmental correction only; consumed V1 is retained."""
from pathlib import Path
import hashlib
import json

support = Path('C:/ANYworkspaceWork/ANYsolver-general-contact/docs/d1_review_support')
prefix = 'native_forced_response_v2_20261001'
old = support/'native_forced_response_v1_20261001.inputs.json'
record = json.loads(old.read_text(encoding='utf-8'))
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for item in record['sources']:
    assert digest(Path(record['workspace'])/item['path']) == item['sha256']
for item in record['historical'].values():
    assert digest(Path(item['path'])) == item['sha256']
cache = Path('C:/ANYworkspaceWork/general-contact-native-forced-v2-cache-20261001')
basetemp = Path('C:/ANYworkspaceWork/general-contact-native-forced-v2-tmp-20261001')
for path in [cache,basetemp]+[support/(prefix+suffix) for suffix in
                           ('.inputs.json','.log','.raw.json','.xml','.resources.json')]:
    assert not path.exists(), path
record['environment'].update(NUMBA_CACHE_DIR=str(cache),
    NATIVE_FORCED_RESPONSE_INPUTS=str(support/(prefix+'.inputs.json')),
    NATIVE_FORCED_RESPONSE_RAW_OUTPUT=str(support/(prefix+'.raw.json')))
record['pytest_args']=['-q','-s','tests/test_ge_beam3_native_forced_response.py',
    '--junitxml='+str(support/(prefix+'.xml')),'--basetemp='+str(basetemp)]
record['basetemp_admission']={'path':str(basetemp),'must_be_absent_before_execution':True}
record['entry_sha256']=digest(support/'native_forced_response_cache_entry_20261001.py')
record['environmental_correction']={
    'prior_input_sha256':digest(old),
    'prior_result':'TIMEOUT180.0286147s before test entry metadata; no raw/XML/steps',
    'probe_resource_sha256':digest(support/'native_forced_response_startup_v1_20261001.resources.json'),
    'probe_log_sha256':digest(support/'native_forced_response_startup_v1_20261001.log'),
    'reason':'Trace localizes to tempfile NamedTemporaryFile in numba.core.caching inside anysolver import',
    'change':'Task-owned writable NUMBA_CACHE_DIR verified in target process; no source/mechanics/criteria/limit change'}
out = support/(prefix+'.inputs.json')
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'input':str(out),'sha256':digest(out),'sources':len(record['sources'])}))
