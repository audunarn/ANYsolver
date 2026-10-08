"""Saved-state representability analysis only, no chart/response reevaluation."""
from pathlib import Path
from decimal import Decimal as D, localcontext
import json, math
ROOT=Path(__file__).resolve().parent
reader=ROOT/'owner-diagnosis-v3.py';prefix=reader.read_text().split("state=archive('failed-Newton-trial.npz')",1)[0]
scope={'__file__':str(reader)};exec(compile(prefix,str(reader),'exec'),scope)
array=scope['array'];archive=scope['archive']
parent=archive('failed-Newton-trial.npz');candidate=archive('evaluation-130.npz');step=array('failed-Newton-fullstep.npy')['values'];h=1/4096
q=parent['q']['values'];after=candidate['q']['values'];translation=[]
with localcontext() as c:
    c.prec=80
    for i in list(range(48))+[i for i in range(48,78) if (i-48)%6<3]:
        exact=D.from_float(q[i])+D.from_float(h)*D.from_float(step[i])
        translation.append(dict(slot=i,parent=q[i],step=h*step[i],actual_change=after[i]-q[i],
            ulp_parent=math.ulp(q[i]),change_in_ulps=abs(h*step[i])/math.ulp(q[i]),
            actual_minus_exact=float(D.from_float(after[i])-exact)))
rotation=[]
for name,triples in (('frames',[(48+6*n+3,3*n*3) for n in range(5)]),('cells',[(78+24*m+3*c,18*m+9*c) for m in range(2) for c in range(2)])):
    before=parent[name]['values'];after_r=candidate[name]['values']
    for start,offset in triples:
        theta=step[start:start+3];angle=math.sqrt(math.fsum(x*x for x in theta));u=before[offset:offset+9]
        skew=((0.,-theta[2],theta[1]),(theta[2],0.,-theta[0]),(-theta[1],theta[0],0.))
        first=[math.fsum(skew[i][k]*u[3*k+j] for k in range(3)) for i in range(3) for j in range(3)]
        diagonal=[]
        for j in (0,4,8):
            value=u[j];actual=after_r[offset+j]-value
            diagonal.append(dict(entry=j,parent=value,ulp=math.ulp(value),actual_change=actual,
                first_order_change=h*first[j],remainder_vs_first_order=actual-h*first[j],
                first_order_change_in_ulps=h*first[j]/math.ulp(value),
                expected_FD_h1e4_first_order_change_in_ulps=1e-4*first[j]/math.ulp(value)))
        rotation.append(dict(array=name,angular_slot=start,Newton_angle_norm=angle,
            amount=h,second_order_bound=.5*(h*angle)**2*math.exp(h*angle),diagonal=diagonal))
output=dict(inputs=scope['inputs'],geometry_evaluation_not_called=True,
    translation_summary=dict(count=len(translation),min_nonzero_change_ulps=min(x['change_in_ulps'] for x in translation if x['step']),
        max_absolute_rounding=max(abs(x['actual_minus_exact']) for x in translation)),translations=translation,rotations=rotation,
    limitation='Only original last dyadic candidate state was saved. Actual +/-FD state/geometry/material terms were not saved, so their separate rounding cannot be recovered. Rotation remainder includes true second-order terms plus representation/update rounding; the bound does not measure those terms separately.')
target=ROOT/'owner-diagnosis-v3-rounding.json';assert not target.exists();target.write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(dict(translation_summary=output['translation_summary'],cells=[r for r in rotation if r['array']=='cells'])))
