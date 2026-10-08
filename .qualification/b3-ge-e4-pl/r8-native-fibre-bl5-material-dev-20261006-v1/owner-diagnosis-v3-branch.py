"""Compare saved candidate tangents/residuals; no calls into solver code."""
from pathlib import Path
import hashlib, json, math
ROOT=Path(__file__).resolve().parent
reader=ROOT/'owner-diagnosis-v3.py';prefix=reader.read_text().split("state=archive('failed-Newton-trial.npz')",1)[0]
scope={'__file__':str(reader)};exec(compile(prefix,str(reader),'exec'),scope)
array=scope['array'];archive=scope['archive']
detail=json.loads((ROOT/'owner-diagnosis-v3-detail.json').read_text())
d=array('failed-Newton-fullstep.npy')['values']
def action(name):
    m=archive(name);vals=m['data']['values'];indices=m['indices']['values'];ptr=m['indptr']['values']
    terms=[[] for _ in d];pterms=[[] for _ in d]
    pslots=set(range(84,102))|set(range(108,126))
    for j in range(len(d)):
        for k in range(ptr[j],ptr[j+1]):
            term=vals[k]*d[j];terms[indices[k]].append(term)
            if j in pslots:pterms[indices[k]].append(term)
    return [math.fsum(r) for r in terms],[math.fsum(r) for r in pterms]
base,basep=action('failed-Newton-K.npz')
L=json.loads((ROOT/'owner-diagnosis-v3.json').read_text())['reference_length']
e=210e9;g=e/(2*1.3)
stiffness=[e*.01,g*.008,g*.008,g*1.6666666666666667e-5,e*8.333333333333333e-6,e*8.333333333333333e-6]
roles=stiffness[:3]*2+[x/L for x in stiffness[3:]]*4
weights=[L,L,L,1.,1.,1.]*13+([1.]*6+roles)*2+[1.]*20
records=[]
for candidate in detail['candidate_rows'][1:]:
    i=candidate['index'];h=candidate['amount'];kd,kdp=action('evaluation-%03d-K.npz'%i)
    defect={x['row']:x['weighted'] for x in candidate['top_defect']}
    inferred=[]
    for row in (108,115,116,118,119):
        jump=(kd[row]-base[row])*weights[row]
        pjump=(kdp[row]-basep[row])*weights[row]
        error=defect.get(row,0.)
        inferred.append(dict(row=row,full_slope_jump_work=jump,material_only_slope_jump_work=pjump,
            geometry_slope_jump_work=jump-pjump,actual_nonlinear_defect_work=error,
            piecewise_linear_crossing_amount=h-error/jump if jump else None))
    records.append(dict(index=i,amount=h,changed=candidate['changed_fibre_bits'],channels=inferred))
output=dict(reader_sha256=hashlib.sha256(reader.read_bytes()).hexdigest(),inputs=scope['inputs'],records=records,
    interpretation='For a one-branch affine constitutive gradient, R(h)-R(0)-hK(0)d=(h-h*)[K(h)-K(0)]d, up to geometric curvature. Inferred crossing is a saved-data consistency test, not a solved branch boundary or new evaluation.')
target=ROOT/'owner-diagnosis-v3-branch.json';assert not target.exists();target.write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(records[-4:]))
