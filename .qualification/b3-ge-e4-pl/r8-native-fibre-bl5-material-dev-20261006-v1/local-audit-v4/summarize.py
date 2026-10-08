"""Combine only already evaluated paired responses; no mechanics imports."""
from pathlib import Path
from decimal import Decimal as D, localcontext
import hashlib, json, math
ROOT=Path(__file__).resolve().parent;folder=ROOT/'audit-v1';data=json.loads((folder/'result.json').read_text())
def pair(values):return [D.from_float(float(a))+D.from_float(float(b)) for a,b in zip(*values)]
def action(matrix,vector):return [sum((a*b for a,b in zip(row,vector)),D(0)) for row in matrix]
def norm(vector,weights):return sum(((a*b)**2 for a,b in zip(vector,weights)),D(0)).sqrt()
summary=[]
with localcontext() as c:
    c.prec=80
    h=D.from_float(1e-4);last_amount=D.from_float(1/4096)
    reference=D.from_float(.3783465619944815);e=D.from_float(210e9);g=e/(D(2)*(D(1)+D.from_float(.3)))
    # Use the exact binary64 frozen scales from the recorded cell response norms:
    # the scalar values below reproduce the compiled roles, not a new material law.
    stiff=[210e9*.01,(210e9/(2*(1+.3)))*.008,(210e9/(2*(1+.3)))*.008,
           (210e9/(2*(1+.3)))*1.6666666666666667e-5,210e9*8.333333333333333e-6,210e9*8.333333333333333e-6]
    weights=[D.from_float(x) for x in stiff[:3]*2+[x/float(reference) for x in stiff[3:]]*4]
    for item in data['results']:
        responses={k:json.loads((folder/f"member-{item['member']}-{k}.json").read_text()) for k in ('base','positive','negative','last')}
        grad={k:pair(v['gradient']) for k,v in responses.items()}
        H0=[pair(row) for row in responses['base']['hessian']];Hl=[pair(row) for row in responses['last']['hessian']]
        vector=[D.from_float(x) for x in item['direction']]
        delta=[D.from_float(a)-D.from_float(b) for a,b in zip(item['points']['last'],item['points']['base'])]
        actual=[-(a-b-c) for a,b,c in zip(grad['last'],grad['base'],action(H0,delta))]
        jump=[-(a-b) for a,b in zip(action(Hl,vector),action(H0,vector))]
        branches=item['branch_rows'];changes=[]
        if item['family']=='FibreCellConjugate':
            for station,(base,last) in enumerate(zip(branches['base'],branches['last'])):
                for b,l in zip(base['fibres'],last['fibres']):
                    if b['branch']!=l['branch']:changes.append(dict(station=station,fibre_id=b['fibre_id'],before=b['branch'],after=l['branch']))
            assert changes==[dict(station=0,fibre_id='1',before='ELASTIC',after='PLASTIC_NEGATIVE')]
            margins={k:D(branches[k][0]['fibres'][1]['signed_trial_yield_margin']) for k in responses}
            slope=(margins['positive']-margins['negative'])/(2*h)
            crossing=-margins['base']/slope
            prediction=[(last_amount-crossing)*x for x in jump]
            difference=[a-b for a,b in zip(actual,prediction)]
            channels=[dict(local_resultant_row=i,global_row=108+i,signed_defect_work=str(actual[i]*weights[i]),
                predicted_signed_defect_work=str(prediction[i]*weights[i]),difference_work=str(difference[i]*weights[i]),
                inferred_crossing=item['inferred_crossing_amounts'][i]) for i in (0,7,8,10,11)]
            cross=dict(margins={k:str(v) for k,v in margins.items()},old_branch_margin_directional_derivative=str(slope),
                crossing_from_margin=str(crossing),weighted_defect_norm=str(norm(actual,weights)),
                weighted_consistency_error_norm=str(norm(difference,weights)),
                signed_secant_relative_consistency=str(norm(difference,weights)/norm(actual,weights)),channels=channels)
        else:
            assert all(row['branch']=='ELASTIC' for point in branches.values() for row in point)
            cross=dict(weighted_secant_defect_norm=str(norm(actual,weights)),
                weighted_endpoint_compliance_jump_norm=str(norm(jump,weights)))
        summary.append(dict(member=item['member'],family=item['family'],smooth_pass=item['smooth_pass'],
            smooth_relative_error=item['smooth_relative_error'],effective_input_relative_error=item['effective_input_relative_error'],
            explicit_branch_stable=item['explicit_branch_stable'],explicit_last_changes=changes,cross_boundary=cross))
record=dict(local_calls=8,compile_owners=1,fresh_restores=1,passed_smooth_criterion=all(x['smooth_pass'] for x in summary),results=summary,
    call_counts={f"{r['stage']}:{r['method']}":sum(x['stage']==r['stage'] and x['method']==r['method'] for x in data['calls']) for r in data['calls']},
    limitation='Signed secant consistency is an observed comparison, not a new global convergence criterion. Passing local compliance does not prove whole-chain FD noise. Endpoint tangent change is not a bound on geometric finite residual.',
    result_sha256=hashlib.sha256((folder/'result.json').read_bytes()).hexdigest())
target=ROOT/'summary.json';assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
