"""Read-only standard-library analysis of the terminal changed-source capture."""
from pathlib import Path
import ast,json,math,array,struct,zipfile,io
ROOT=Path(__file__).resolve().parent;F=ROOT/'candidate-screen-v1'
# Reuse pure readers/classifiers, excluding the first analysis's top-level run.
tree=ast.parse((ROOT/'analyze.py').read_text())
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) or
    isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='roles' for t in n.targets)]
exec(compile(ast.Module(body=selected,type_ignores=[]),'saved-reader-functions','exec'))
result={}
for number,failed in enumerate(load('A-failures'),1):
    name='A-failure-%d-parent'%number;b=load(name);base=arrays(name);linear=arrays('A-failure-%d-linear'%number)
    records=[];last=None
    for i in range(failed['saved_candidates']):
        name='A-failure-%d-candidate-%02d'%(number,i);c=load(name);data=arrays(name)
        displacement=[a-z for a,z in zip(v(data,'q'),v(base,'q'))]
        states={field:max((abs(a-z) for a,z in zip(v(data,field),v(base,field))),default=0.) for field in ('q','frames','cells','resultants','multipliers')}
        close=[r for r in labels(c) if r['key']=='q4-0-layer-10'][0]
        records.append(dict(index=i,role='terminal_iteration_24_reevaluation' if i==failed['saved_candidates']-1 else 'actual_candidate_trial',
            amount=c['amount'],relative=c['relative'],relative_change=c['relative']-b['relative'],gap=c['gap'],q4_layer10=close,
            branch_changes=compare(b,c),max_actual_state_changes=states))
        last=data
    free=v(linear,'free');step=v(linear,'fullstep');kd=mv(base,step);R=v(base,'R')
    close=[r for r in labels(b) if r['key']=='q4-0-layer-10'][0]
    result[str(number)]=dict(attempt=failed['attempt'],parent_relative=b['relative'],parent_q4_layer10=close,
        proposal=failed['proposal'],saved_records=records,original_global_linear_max_abs=max(map(abs,v(linear,'linear_residual'))),
        maximum_rhs=max(map(abs,v(linear,'rhs'))),original_parent_tip_R=R[74],original_parent_tip_Kd=kd[74],
        actual_accepted_trial_tip_R=v(last,'R')[74],actual_accepted_trial_shell_row6_R=v(last,'R')[6])
evaluations=load('evaluations');trace=[dict(factor=r['factor'],amount=r['amount'],relative=r['relative'],gap=r['gap']) for r in evaluations if r['stage']=='resume']
payload=dict(outcome='NO_ACCEPTED_COMMIT; pending target1 failed under unchanged controls',attempts=result,
    scalar_trace_count=len(trace),scalar_trace=trace,final_prefix=load('result')['A'],
    limitation='Final saved group includes actual candidate trials plus the next iteration-24 parent reevaluation; metadata candidate names do not imply every saved record is a new candidate. Margins are reconstructed from callback inputs/outputs; output alpha advancement confirms executed switch. No additional constitutive/assembly/solve evaluations.')
(ROOT/'candidate-obstruction-v1.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps({n:dict(proposal=r['proposal'],parent_margin=r['parent_q4_layer10']['switch_margin'],
    records=[dict(role=x['role'],amount=x['amount'],relative_change=x['relative_change'],margin=x['q4_layer10']['switch_margin'],
        alpha=x['q4_layer10']['candidate_alpha'],changed=[y['key'] for y in x['branch_changes']],max_q=x['max_actual_state_changes']['q']) for x in r['saved_records']]) for n,r in result.items()}))
