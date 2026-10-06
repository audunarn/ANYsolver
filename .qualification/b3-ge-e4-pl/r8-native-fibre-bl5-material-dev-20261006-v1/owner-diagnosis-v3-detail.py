"""Additional saved-data arithmetic only; no solver/material evaluation."""
from pathlib import Path
import ast, hashlib, json, math
ROOT=Path(__file__).resolve().parent;SAVED=ROOT/'rejected-trial-state-v1'
reader=ROOT/'owner-diagnosis-v3.py'
# Execute only the explicit stdlib reader definitions, before any diagnosis body.
prefix=reader.read_text().split("state=archive('failed-Newton-trial.npz')",1)[0]
scope={'__file__':str(reader)};exec(compile(prefix,str(reader),'exec'),scope)
array=scope['array'];archive=scope['archive'];read_bytes=scope['read_bytes']
old=json.loads((ROOT/'owner-diagnosis-v3.json').read_text());L=old['reference_length']
e=210e9;g=e/(2*(1+.3));stiffness=[e*.01,g*.008,g*.008,g*1.6666666666666667e-5,e*8.333333333333333e-6,e*8.333333333333333e-6]
roles=stiffness[:3]*2+[v/L for v in stiffness[3:]]*4
weights=[L,L,L,1.,1.,1.]*13+([1.]*6+roles)*2+[1.]*20
count=126;size=146;fixed=set(range(6))|set(range(24,30));free=[i for i in range(size) if i not in fixed];qfree=[i for i in free if i<count]
R=array('failed-Newton-R.npy')['values'];d=array('failed-Newton-fullstep.npy')['values'];state=archive('failed-Newton-trial.npz')
matrix=archive('failed-Newton-K.npz');values=matrix['data']['values'];indices=matrix['indices']['values'];ptr=matrix['indptr']['values']
force_slots=set(range(84,102))|set(range(108,126))
rows=[[] for _ in R];p_rows=[[] for _ in R]
for j in range(size):
    for k in range(ptr[j],ptr[j+1]):
        i=indices[k];term=values[k]*d[j];rows[i].append(term)
        if j in force_slots:p_rows[i].append(term)
Kd=[math.fsum(x) for x in rows];Kdp=[math.fsum(x) for x in p_rows]
def norm(v,slots=qfree):return math.sqrt(math.fsum((v[i]*weights[i])**2 for i in slots))
evaluations=json.loads(read_bytes(SAVED/'evaluations.json'));advances=json.loads(read_bytes(SAVED/'advances.json'))
denominator=156.25*L;tip=74;results=[];origin_mask=evaluations[117]['mask'][1][1]
for row in evaluations[117:131]:
    i=row['index'];res=array('evaluation-%03d-R.npy'%i)['values']
    amount=0. if i==117 else advances[103+i-118]['amount']
    if i!=117:assert advances[103+i-118]['preceding_evaluation']==i-1
    predicted=[math.fsum((r,amount*k)) for r,k in zip(R,Kd)]
    defect=[math.fsum((a,-b)) for a,b in zip(res,predicted)]
    top=sorted(qfree,key=lambda j:abs(defect[j]*weights[j]),reverse=True)[:6]
    changed=[dict(station=j//4,fibre=j%4,from_active=before,to_active=after) for j,(before,after) in enumerate(zip(origin_mask,row['mask'][1][1])) if before!=after]
    results.append(dict(index=i,amount=amount,published_merit=row['relative'],
        reconstructed_global_ratio=norm(res)/denominator,reconstructed_active_tip_ratio=abs(res[tip])/156.25,
        predicted_global_ratio=norm(predicted)/denominator,
        defect_work_norm=norm(defect),changed_fibre_bits=changed,
        axial_rows=[dict(row=j,weighted_current=res[j]*weights[j],weighted_linear_prediction=predicted[j]*weights[j],weighted_defect=defect[j]*weights[j]) for j in (84,87,108,111)],
        top_defect=[dict(row=j,weighted=defect[j]*weights[j]) for j in top]))
material_only=[]
for i in (84,87,108,111):
    member=(i-78)//24;half=((i-78)%24-6)//3
    diagonal=state['cells']['values'][member*18+half*9]
    material_only.append(dict(row=i,full_derivative=Kd[i],material_only_derivative=Kdp[i],
        geometry_only_derivative=math.fsum((Kd[i],-Kdp[i])),
        projected_reference_rotation_diagonal=diagonal,
        ulp_diagonal_times_quarter_chord=math.ulp(diagonal)*.25,
        material_only_difference_at_h1e_4=2e-4*Kdp[i],
        geometric_difference_at_h1e_4=2e-4*math.fsum((Kd[i],-Kdp[i]))))
output=dict(reader_sha256=hashlib.sha256(reader.read_bytes()).hexdigest(),inputs=scope['inputs'],
    actual_assembly_equilibrium_denominator_work=denominator,current_work_norm=norm(R),
    saved_linear_residual_work_norm=old['actual_saved_linear_relative']*old['residual_weighted_norm'],
    candidate_rows=results,retained_only_material_discriminator=material_only,
    source_remarks='The retained-only derivative splits use exact saved K columns84:102/108:126. No constitutive or geometry call was made. Aggregate activity masks record accumulated-alpha advancement relative to fixed origins, not explicit branch labels or station boundary margins.')
target=ROOT/'owner-diagnosis-v3-detail.json';assert not target.exists();target.write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(dict(denominator=denominator,current_work_norm=norm(R),linear_work_norm=output['saved_linear_residual_work_norm'],
    smallest_dyadic=results[-1],material_only=material_only)))
