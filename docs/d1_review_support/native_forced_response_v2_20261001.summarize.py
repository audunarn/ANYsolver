"""Summarize saved outcomes only; no solver imports or numerical reevaluation."""
from pathlib import Path
from hashlib import sha256
import json

support = Path(__file__).parent
prefix='native_forced_response_v2_20261001'
def read(suffix):
    return json.loads((support/(prefix+suffix)).read_text(encoding='utf-8'))
raw=read('.raw.json'); resources=read('.resources.json'); inputs=read('.inputs.json')
assert raw['status']=='PASS' and raw['accepted_steps']==20
assert resources['exit_code']==0 and resources['status']=='completed'
assert raw['criteria']==inputs['criteria']
rows=[row for run in raw['resolutions'].values() for row in run['endpoints']]
assert len(rows)==20 and all(row['passes'] for row in raw['comparisons'].values())
summary=dict(status='DEVELOPMENT_PASS_PENDING_INDEPENDENT_SAVED_ASSESSMENT',
    accepted_steps=20,elapsed_seconds=resources['elapsed_seconds'],
    peak_process_tree_memory_mb=resources['peak_process_tree_memory_mb'],
    source_binding_count=len(inputs['sources']), criteria=raw['criteria'],
    shared_spatial_errors=raw['shared_spatial_match']['errors'],
    maximum_stage_norm=max(row['stage_norm'] for row in rows),
    maximum_endpoint_algebraic_norm=max(row['endpoint_algebraic_norm'] for row in rows),
    maximum_discrete_trajectory_errors={key:max(row['errors_discrete'][key] for row in rows)
        for key in rows[0]['errors_discrete']},
    maximum_step_defects={key:max(row['step_defects'][key] for row in rows)
        for key in rows[0]['step_defects']},
    maximum_cumulative_defects={key:max(row['cumulative_defects'][key] for row in rows)
        for key in rows[0]['cumulative_defects']},comparisons=raw['comparisons'],
    artifacts={suffix:{'path':str(support/(prefix+suffix)),
        'sha256':sha256((support/(prefix+suffix)).read_bytes()).hexdigest()}
        for suffix in ('.inputs.json','.raw.json','.resources.json','.log','.xml')},
    retained_failures={label:json.loads((support/(label+'.resources.json')).read_text(encoding='utf-8'))
        for label in ('native_forced_response_v1_20261001','native_forced_response_startup_v1_20261001')},
    limits='Temporal small-motion control against authenticated shared spatial operators, no C7/continuum/installed acceptance; prior failures unchanged')
out=support/(prefix+'.summary.json')
assert not out.exists()
out.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:summary[key] for key in ('accepted_steps','elapsed_seconds',
    'maximum_stage_norm','maximum_discrete_trajectory_errors','maximum_cumulative_defects')}))
