"""Read-only saved-array arithmetic; deliberately no numerical package imports."""
from pathlib import Path
import ast, hashlib, json, math, struct, zipfile
ROOT=Path(__file__).resolve().parent
SAVED=ROOT/'rejected-trial-state-v1'
inputs={}
def read_bytes(p):
    data=p.read_bytes();inputs[str(p.relative_to(ROOT))]=hashlib.sha256(data).hexdigest();return data
def npy(data):
    assert data[:6]==b'\x93NUMPY'
    version=data[6];offset=10 if version==1 else 12
    count=struct.unpack('<H' if version==1 else '<I',data[8:offset])[0]
    header=ast.literal_eval(data[offset:offset+count].decode('latin1'))
    assert not header['fortran_order']
    payload=data[offset+count:];shape=header['shape'];n=math.prod(shape)
    dtype=header['descr'];endian='<' if dtype[0] in '<|=' else '>'
    codes={'f8':'d','i4':'i','i8':'q','u1':'B','b1':'?'}
    if dtype[1:2]=='S':values=[payload[i*int(dtype[2:]):(i+1)*int(dtype[2:])] for i in range(n)]
    else:values=list(struct.unpack(endian+str(n)+codes[dtype[1:]],payload))
    return dict(shape=shape,dtype=dtype,values=values)
def array(name):return npy(read_bytes(SAVED/name))
def archive(name):
    data=read_bytes(SAVED/name)
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(data)) as z:return {p.removesuffix('.npy'):npy(z.read(p)) for p in z.namelist()}
state=archive('failed-Newton-trial.npz');matrix=archive('failed-Newton-K.npz')
R=array('failed-Newton-R.npy')['values'];d=array('failed-Newton-fullstep.npy')['values']
linear_saved=array('linear-residual.npy')['values']
q=state['q']['values'];count=len(q);size=len(R)
fixed=set(range(6))|set(range(24,30));free=[i for i in range(size) if i not in fixed]
positions=[(x,y,0.) for y in (0.,.2) for x in (0.,1/3,2/3,1.)]+[(x,0.,.0675) for x in (0.,.25,.5,.75,1.)]
mean=[math.fsum(p[i] for p in positions)/len(positions) for i in range(3)]
length=math.sqrt(math.fsum(math.fsum((p[i]-mean[i])**2 for i in range(3)) for p in positions)/len(positions))
e=210e9;g=e/(2*(1+.3))
stiffness=[e*.01,g*.008,g*.008,g*1.6666666666666667e-5,e*8.333333333333333e-6,e*8.333333333333333e-6]
roles=stiffness[:3]*2+[x/length for x in stiffness[3:]]*4
weights=[length,length,length,1.,1.,1.]*13+([1.]*6+roles)*2+[1.]*(size-count)
assert len(weights)==size
assert matrix['format']['values']==[b'csc']
rowterms=[[] for _ in R];entries=[[] for _ in R]
values=matrix['data']['values'];indices=matrix['indices']['values'];indptr=matrix['indptr']['values']
for column in range(size):
    for k in range(indptr[column],indptr[column+1]):
        row=indices[k];rowterms[row].append(values[k]*d[column]);entries[row].append((column,values[k]))
Kd=[math.fsum(row) for row in rowterms]
def norm(v,indices=free):return math.sqrt(math.fsum((v[i]*weights[i])**2 for i in indices))
def channel(i):
    if i<48:return 'shell nodal spatial covector'
    if i<78:return 'beam nodal spatial covector'
    if i>=count:return 'BL5 constraint row '+str(i-count)
    member=(i-78)//24+1;local=(i-78)%24
    if local<6:return f'beam{member} cell spatial rotational covector {local}'
    p=local-6
    return f'beam{member} '+('generalized' if member==1 else 'physical-fibre')+f' retained p{p} '+('axial half-cell compatibility' if p in (0,3) else 'retained compatibility')
outcome=json.loads(read_bytes(SAVED/'outcome.json'))
linear=[math.fsum((a,b)) for a,b in zip(Kd,R)]
report=dict(inputs=inputs,array_dimensions=dict(q=count,KKT=size,fixed=len(fixed),free=len(free)),
    reference_length=length,expected_weighted_norm=norm(Kd),residual_weighted_norm=norm(R),
    actual_saved_linear_relative=norm(linear_saved)/norm(R),fsum_linear_relative=norm(linear)/norm(R),
    saved_vs_fsum_linear_difference=norm([a-b for a,b in zip(linear_saved,linear)]),
    linear_max_constraint_abs=max(abs(x) for x in linear[count:]),
    linear_top=[dict(row=i,channel=channel(i),saved_weighted=linear_saved[i]*weights[i],fsum_weighted=linear[i]*weights[i],
                     residual=R[i],expected=Kd[i],weight=weights[i],sum_abs_Kd_terms=math.fsum(abs(x) for x in rowterms[i]))
                for i in sorted(free,key=lambda i:abs(linear_saved[i]*weights[i]),reverse=True)[:10]],
    derivatives=[])
for branch in outcome['derivatives']:
    if branch['direction']!='Newton':continue
    for step in branch['steps']:
        h=step['h'];errors=array('Newton-h'+str(h)+'-derivative-error.npy')['values']
        total=sum((errors[i]*weights[i])**2 for i in free)
        dominant=(84,87,108,111)
        rows=[]
        for i in dominant:
            terms=entries[i]
            rows.append(dict(row=i,channel=channel(i),weight=weights[i],base_residual=R[i],expected_derivative=Kd[i],
                raw_derivative_error=errors[i],weighted_derivative_error=errors[i]*weights[i],
                reconstructed_plus_minus_difference=2*h*(Kd[i]+errors[i]),
                expected_plus_minus_difference=2*h*Kd[i],difference_error=2*h*errors[i],
                difference_error_over_ulp_quarter_chord=2*h*errors[i]/math.ulp(.25),
                Kd_sum_abs_terms=math.fsum(abs(x) for x in rowterms[i]),
                kinematic_terms=[dict(column=j,coefficient=v,direction=d[j],product=v*d[j]) for j,v in terms if j<108],
                moment_or_force_step_terms=[dict(column=j,coefficient=v,direction=d[j],product=v*d[j]) for j,v in terms if j>=108]))
        report['derivatives'].append(dict(h=h,branch_consistent=step['branch_consistent'],
            reconstructed_relative=math.sqrt(total)/max(norm(Kd),1.),published_relative=step['relative'],
            dominant_four_fraction=math.fsum((errors[i]*weights[i])**2 for i in dominant)/total,
            nodal_error_norm=norm(errors,[i for i in free if i<78]),
            retained_error_norm=norm(errors,list(range(78,count))),
            constraint_error_norm=norm(errors,list(range(count,size))),
            positive_merit=step['positive_merit'],negative_merit=step['negative_merit'],rows=rows))
evaluations=json.loads(read_bytes(SAVED/'evaluations.json'))
report['last_backtrack']=[dict(index=x['index'],relative=x['relative'],gap=x['gap'],
    active_shell=sum(sum(v) for v in x['mask'][0]),active_generalized=sum(x['mask'][1][0]),active_fibre=sum(x['mask'][1][1]))
    for x in evaluations[117:131]]
report['inputs']=inputs
target=ROOT/'owner-diagnosis-v3.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(dimensions=report['array_dimensions'],reference_length=length,expected_norm=norm(Kd),
    saved_linear_relative=report['actual_saved_linear_relative'],
    derivatives=[{k:x[k] for k in ('h','reconstructed_relative','dominant_four_fraction','nodal_error_norm','retained_error_norm','constraint_error_norm')} for x in report['derivatives']])))
