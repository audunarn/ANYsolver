"""Freeze one source-reviewed native temporal development case without imports.

Uses the verified task-cache entry and shared development pytest supervisor.
This is preparation, not execution or scientific acceptance.
"""
import argparse
from pathlib import Path
from hashlib import sha256
import json
import re

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('prefix')
parser.add_argument('namespace')
args=parser.parse_args()
assert re.fullmatch('[a-z0-9_]+',args.prefix)
assert re.fullmatch('NATIVE_[A-Z_]+',args.namespace)
support=Path(__file__).resolve().parent
proposal_path=support/(args.prefix+'.proposal.json')
proposal=json.loads(proposal_path.read_text(encoding='utf-8'))
base_path=support/'native_forced_response_v2_20261001.inputs.json'
record=json.loads(base_path.read_text(encoding='utf-8'))
root=Path(record['workspace'])
digest=lambda path:sha256(path.read_bytes()).hexdigest()
assert root.resolve()==Path(proposal['workspace']).resolve()
assert proposal['status']=='SOURCE_AUTHORED_NOT_EXECUTED'
assert proposal['criteria']==record['criteria']
assert proposal['historical_source_overrides']==record['historical_source_overrides']
for item in record['sources']:
    assert digest(root/item['path'])==item['sha256'],item['path']
for path,expected in proposal['source_sha256'].items():
    assert digest(Path(path))==expected,path
for item in proposal['historical'].values():
    assert digest(Path(item['path']))==item['sha256'],item['path']
cache=Path('C:/ANYworkspaceWork')/(args.prefix+'-cache')
basetemp=Path('C:/ANYworkspaceWork')/(args.prefix+'-tmp')
for path in [cache,basetemp]+[support/(args.prefix+suffix) for suffix in
    ('.inputs.json','.log','.raw.json','.xml','.resources.json')]:
    assert not path.exists(),path
sources={item['path']:item['sha256'] for item in record['sources']}
for relative in proposal['owned_new_paths']:
    path=root/relative
    assert path.resolve().is_relative_to(root.resolve())
    sources[relative]=digest(path)
    record['source_sha256'][str(path)]=digest(path)
record['sources']=[{'path':path,'sha256':value} for path,value in sorted(sources.items())]
record['historical']=proposal['historical']
record['proposal_sha256']=digest(proposal_path)
record['criteria']=proposal['criteria']
record.pop('environmental_correction',None)
for key in list(record['environment']):
    if key.startswith('NATIVE_FORCED_RESPONSE_'):
        del record['environment'][key]
record['environment'].update(NUMBA_CACHE_DIR=str(cache),**{
    args.namespace+'_INPUTS':str(support/(args.prefix+'.inputs.json')),
    args.namespace+'_RAW_OUTPUT':str(support/(args.prefix+'.raw.json'))})
record['pytest_args']=['-q','-s',proposal['selected_test'],
    '--junitxml='+str(support/(args.prefix+'.xml')),'--basetemp='+str(basetemp)]
record['basetemp_admission']={'path':str(basetemp),'must_be_absent_before_execution':True}
record['entry_sha256']=digest(support/'native_forced_response_cache_entry_20261001.py')
record['freeze_sha256']=digest(Path(__file__))
record['base_input_sha256']=digest(base_path)
record['limits']=proposal['bounds']
record['purpose']=proposal['claim_boundary']
record['source_commit']='Exact reviewed sources; main production remains9050dbf3'
out=support/(args.prefix+'.inputs.json')
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'input':str(out),'sha256':digest(out),'source_count':len(sources)}))
