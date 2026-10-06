from collections import Counter
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
folder=ROOT/'cohort-v1'
histories=json.loads((folder/'accepted-histories.json').read_text())
work=json.loads((folder/'work.json').read_text())
result=json.loads((folder/'result.json').read_text())
failures=[]
for case in ET.parse(folder/'junit.xml').iter('testcase'):
    failure=case.find('failure')
    if failure is not None:
        failures.append(dict(test=case.attrib['name'],message=failure.attrib.get('message'),
                             exact_traceback=failure.text))
groups={}
for name in dict.fromkeys(row['test'] for row in work):
    rows=[row for row in work if row['test']==name]
    counts=Counter(row['method'] for row in rows)
    physical=[row for row in rows if row['method']=='physical_cell']
    generalized=[row for row in rows if row['method']=='generalized_cell']
    counts['physical_original_compliance_preparations']=len(physical)
    counts['added_owned_station_linearizations']=sum(row['capture_trial'] for row in physical)
    counts['added_material_response_calls']=0
    counts['added_compliance_solves']=0
    counts['physical_local_evaluations']=sum(row['evaluations'] for row in physical)
    counts['physical_local_line_trials']=sum(row['line_trials'] for row in physical)
    counts['generalized_local_evaluations']=sum(row['evaluations'] for row in generalized)
    proposals=[i for i,row in enumerate(rows) if row['method']=='boundary_amount']
    last=rows[proposals[-1]:] if proposals else []
    groups[name]=dict(counts=dict(counts),last_boundary=last[0] if last else None,
        last_amounts=[row['amount'] for row in last if row['method']=='advance'],
        last_assembly_factor=next((row['factor'] for row in reversed(rows) if row['method']=='assemble'),None))
inventories=[]
for label in ('[False]','[True]'):
    entries=[row for row in histories if 'lifecycle' in row['test'] and label in row['test']]
    prior_s=prior_f=None
    for row in entries:
        shell=[value for layer in row['shell'] for value in layer]
        fibre=row['beams'][-1]
        before_s=prior_s or [0.]*len(shell);before_f=prior_f or [0.]*len(fibre)
        inventories.append(dict(test=row['test'],factor=row['factor'],generation=row['generation'],
            equilibrium=row['relative'],gap=row['gap'],shell_alpha_max=max(shell) if shell else None,
            fibre_station_alpha_max=max(fibre),shell_layers_advancing=sum(a>b for a,b in zip(shell,before_s)),
            fibre_stations_advancing=sum(a>b for a,b in zip(fibre,before_f))))
        prior_s=shell;prior_f=fibre
summary=dict(state='PARTIAL source candidate; strict full cohort FAILED; no new installed candidate',
    tests=result['call_reports'],failures=failures,strict_accepted_inventories=inventories,
    work_by_test=groups,total_accepted_commits=len(histories),total_recorded_work=len(work),
    terminal_j2_failure=dict(type='AdaptiveIncrementExhausted',cause='finite backtrack then cutback exhaustion',
        factor=.90625,accepted_prefix=.875,equilibrium=None,gap=None,
        missing='failed trial R/K and terminal attempt equilibrium/gap not serialized; no new evaluations'),
    limitations=['False test branch assertion fails before directional error calculation',
                 'partial simultaneous advancement does not satisfy full lifecycle gate',
                 'local response consistency does not eliminate assembly/chart derivative bias',
                 'final J2 proposal absent and all13 historical dyadics used; no tiny-event starvation conclusion',
                 'postterminal programming fixes have focused evidence only; scientific cohort not repeated'])
(ROOT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(failed=len(failures),passed=sum(r['outcome']=='passed' for r in result['call_reports']),
    accepted_commits=len(histories),terminal_factor=.90625,strict_inventories=inventories),indent=2))
