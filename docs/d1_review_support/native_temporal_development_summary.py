"""Compact saved-result reduction; no production/reference kernel calls."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('prefix')
args=parser.parse_args()
support=Path(__file__).resolve().parent
def read(suffix):
    return json.loads((support/(args.prefix+suffix)).read_text(encoding='utf-8'))
raw,resource,inputs=read('.raw.json'),read('.resources.json'),read('.inputs.json')
assert raw['status']=='PASS' and resource['exit_code']==0 and resource['status']=='completed'
assert raw['criteria']==inputs['criteria']
rows=[row for run in raw['resolutions'].values() for row in run['endpoints']]
assert len(rows)==raw['accepted_steps']==raw['criteria']['maximum_accepted_steps']
assert all(row['passes'] for row in raw['comparisons'].values())
tests=ET.parse(support/(args.prefix+'.xml')).getroot()
assert len(tests.findall('.//testcase'))==1 and not tests.findall('.//failure') and not tests.findall('.//error')
summary=dict(status='DEVELOPMENT_PASS_INDEPENDENT_ASSESSMENT_RECORDED_SEPARATELY',
    accepted_steps=len(rows),elapsed_seconds=resource['elapsed_seconds'],
    peak_process_tree_memory_mb=resource['peak_process_tree_memory_mb'],
    source_binding_count=len(inputs['sources']),criteria=raw['criteria'],
    maximum_stage_norm=max(row['stage_norm'] for row in rows),
    maximum_endpoint_algebraic_norm=max(row['endpoint_algebraic_norm'] for row in rows),
    stage_iterations=sum(row['stage_iterations'] for row in rows),
    stage_backtracks=sum(row['stage_backtracks'] for row in rows),
    comparisons=raw['comparisons'],
    artifacts={suffix:{'path':str(support/(args.prefix+suffix)),
        'sha256':sha256((support/(args.prefix+suffix)).read_bytes()).hexdigest()}
        for suffix in ('.inputs.json','.raw.json','.resources.json','.log','.xml')},
    scope=inputs['purpose'],independent_assessment='Separate reviewed disposition; no C7 promotion')
for field in ('errors_discrete','step_defects','cumulative_defects','reaction_errors_discrete',
              'support_impulse_errors_discrete','support_impulse_errors_continuous'):
    if field in rows[0]:
        summary['maximum_'+field]={key:max(row[field][key] for row in rows) for key in rows[0][field]}
if 'support_work_j' in rows[0]:
    summary['maximum_absolute_support_work_j']=max(abs(row['support_work_j']) for row in rows)
out=support/(args.prefix+'.summary.json')
assert not out.exists()
out.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:value for key,value in summary.items() if key.startswith('maximum_')
    or key in ('accepted_steps','elapsed_seconds','source_binding_count','stage_iterations','stage_backtracks')},indent=2))
