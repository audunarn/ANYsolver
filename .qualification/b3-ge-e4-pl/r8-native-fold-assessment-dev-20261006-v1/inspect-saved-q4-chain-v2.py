"""Arithmetic inspection of fixed saved g14 records; no solver imports/evaluations."""
from pathlib import Path
import sys, os, json, hashlib, math, time, threading
from decimal import Decimal as D, localcontext
RAW=Path(__file__).resolve().parent
FOLDER=RAW/sys.argv[1]
CI=RAW.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
sys.path.insert(0,str(CI))
import psutil
p=psutil.Process();p.cpu_affinity([0])
assert p.cpu_affinity()==[0]
assert os.environ['NUMBA_DISABLE_JIT']=='1'
assert all(os.environ[name]=='1' for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMBA_NUM_THREADS'))
stop=threading.Event(); peak=[0]
def monitor():
    while not stop.is_set():
        tree=[p]+p.children(recursive=True)
        rss=sum(q.memory_info().rss for q in tree if q.is_running())
        peak[0]=max(peak[0],rss)
        if rss>2147483648:
            for q in reversed(tree):q.kill()
        stop.wait(.02)
thread=threading.Thread(target=monitor,daemon=True);thread.start()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,data):
    path=FOLDER/name;tmp=path.with_suffix(path.suffix+'.part')
    with tmp.open('w',encoding='utf-8') as out:
        json.dump(data,out,indent=2,allow_nan=False);out.write('\n');out.flush();os.fsync(out.fileno())
    os.replace(tmp,path)
def load(path):return json.loads(path.read_text())
def dec(v):
    out=D.from_float(float(v))
    if not out.is_finite():raise ValueError('nonfinite saved scalar')
    return out
def vec(v):return [dec(x) for x in v]
def mat(v):return [vec(row) for row in v]
def mv(a,x):return [sum((v*t for v,t in zip(row,x)),D(0)) for row in a]
def tv(a,x):return [sum((a[i][j]*x[i] for i in range(len(x))),D(0)) for j in range(len(a[0]))]
def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
base=RAW/'installed-remaining-endpoints-v1/g14'
try:
    result=load(base/'local-result.json');inventory=load(base/'evaluation-inventory.json')
    assert result['generation']==14 and result['difference_steps']==[3e-6,1e-6]
    assert result['diagnostic_completion']=='COMPLETED_BOUNDED_DIAGNOSTIC'
    hashes={str(base/'local-result.json'):sha(base/'local-result.json')}
    captures=[]
    for entry in inventory['evaluations']:
        path=base.parent/entry['path'];assert sha(path)==entry['sha256']
        hashes[str(path)]=entry['sha256'];captures.append(load(path))
    assert len(captures)==5 and all(len(c['Q4'])==16 for c in captures)
    names=('coordinate_chain','local_force_chain','midpoint_D','D_derivative',
           'geometric_midpoint_force','returned_pullback_arithmetic','scatter_vs_saved_Q4')
    n=len(result['row_scales']);weights=result['row_scales']
    # Coordinate covectors equal spatial forces on these translation rows.
    rows=[i for i in result['free_rows'] if i<162 and i%6<3]
    reports=[]
    with localcontext() as ctx:
        ctx.prec=60
        for number,hvalue in enumerate(result['difference_steps']):
            h=dec(hvalue);scale=2*h
            b=captures[0]['Q4'];m=captures[1+2*number]['Q4'];q=captures[2+2*number]['Q4']
            assert [x['element_id'] for x in b]==[x['element_id'] for x in m]==[x['element_id'] for x in q]
            terms={key:[D(0)]*n for key in names};returned_global=[D(0)]*n;maximum_identity=D(0)
            splits={key:[D(0)]*n for key in ('local_translation','local_rotation','actual_input_quantization')}
            coordinate_records=[]
            for zero,minus,plus in zip(b,m,q):
                slots=zero['slots'];assert slots==minus['slots']==plus['slots'] and len(slots)==24
                t=vec([result['actual_mixed_direction'][i] for i in slots])
                d0=mat(zero['deformation_differential']);dm=mat(minus['deformation_differential']);dp=mat(plus['deformation_differential'])
                k=mat(zero['local_tangent']);f0=vec(zero['local_force']);fm=vec(minus['local_force']);fp=vec(plus['local_force'])
                df=[(x-y)/scale for x,y in zip(fp,fm)]
                dd=[(x-y)/scale for x,y in zip(vec(plus['local_coordinates']),vec(minus['local_coordinates']))]
                dbar=[[(x+y)/2 for x,y in zip(rp,rm)] for rp,rm in zip(dp,dm)]
                dfd=[[(x-y)/scale for x,y in zip(rp,rm)] for rp,rm in zip(dp,dm)]
                fbar=[(x+y)/2 for x,y in zip(fp,fm)]
                d0t=mv(d0,t);kd0t=mv(k,d0t)
                s=zero['deformation_second']
                st=[[sum((dec(s[i][j][l])*t[l] for l in range(24)),D(0)) for j in range(24)] for i in range(24)]
                rd=sub(dd,d0t);rlaw=sub(df,mv(k,dd))
                actual_fd=[(x-y)/scale for x,y in zip(vec(plus['displacement']),vec(minus['displacement']))]
                rdinput=mv(d0,sub(actual_fd,t))
                rdt=[x if j%6<3 else D(0) for j,x in enumerate(rd)]
                rdr=[x if j%6>=3 else D(0) for j,x in enumerate(rd)]
                for key,values in (('local_translation',rdt),('local_rotation',rdr),('actual_input_quantization',rdinput)):
                    pulled=tv(dbar,mv(k,values))
                    for j,index in enumerate(slots):splits[key][index]+=pulled[j]
                for j in range(24):
                    coordinate_records.append(dict(element_id=zero['element_id'],component=j%6,node=j//6,
                        unit='m' if j%6<3 else 'rad',derivative_discrepancy=float(rd[j]),
                        signed_pair_discrepancy=float(scale*rd[j]),mapped_actual_input_quantization=float(rdinput[j])))
                coordinate=tv(dbar,mv(k,rd));law=tv(dbar,rlaw)
                midpoint=tv([[x-y for x,y in zip(a,z)] for a,z in zip(dbar,d0)],kd0t)
                map_derivative=tv([[x-y for x,y in zip(a,z)] for a,z in zip(dfd,st)],fbar)
                geometric=tv(st,sub(fbar,f0))
                exact_fd=[(x-y)/scale for x,y in zip(tv(dp,fp),tv(dm,fm))]
                exact_expected=add(tv(d0,kd0t),tv(st,f0))
                exact_error=sub(exact_fd,exact_expected)
                split=[sum(values,D(0)) for values in zip(coordinate,law,midpoint,map_derivative,geometric)]
                maximum_identity=max(maximum_identity,max(abs(x-y) for x,y in zip(split,exact_error)))
                rf=[(x-y)/scale for x,y in zip(vec(plus['returned_residual']),vec(minus['returned_residual']))]
                recorded_expected=mv(mat(zero['returned_tangent']),t)
                recorded_difference=sub(rf,recorded_expected)
                arithmetic=sub(recorded_difference,exact_error)
                for key,values in zip(names[:6],(coordinate,law,midpoint,map_derivative,geometric,arithmetic)):
                    for j,index in enumerate(slots):terms[key][index]+=values[j]
                for j,index in enumerate(slots):returned_global[index]+=recorded_difference[j]
            target=vec(result['checks'][number]['Q4_only_original_difference'])
            terms[names[-1]]=sub(target,returned_global)
            reconstructed=[sum(values,D(0)) for values in zip(*(terms[name] for name in names))]
            assert max(abs(reconstructed[i]-target[i]) for i in rows)<D('1e-40')
            assert max(abs(splits['local_translation'][i]+splits['local_rotation'][i]-terms['coordinate_chain'][i]) for i in rows)<D('1e-40')
            assert maximum_identity<D('1e-40')
            denominator=result['checks'][number]['Q4_only_witness']['full_unit_factor_load_reference_norm']
            def norm(values):return math.sqrt(math.fsum((weights[i]*float(values[i]))**2 for i in rows))/denominator
            target_norm=norm(target)
            reports.append(dict(step=hvalue,translation_rows=len(rows),translation_Q4_relative_error=target_norm,
                terms={key:norm(value) for key,value in terms.items()},
                coordinate_split={key:norm(value) for key,value in splits.items()},
                coordinate_internal_or_truncation_remainder=norm(sub(terms['coordinate_chain'],splits['actual_input_quantization'])),
                largest_translation_coordinates=sorted([row for row in coordinate_records if row['unit']=='m'],key=lambda row:abs(row['signed_pair_discrepancy']),reverse=True)[:4],
                largest_rotation_coordinates=sorted([row for row in coordinate_records if row['unit']=='rad'],key=lambda row:abs(row['signed_pair_discrepancy']),reverse=True)[:4],
                identity_max_absolute=float(maximum_identity),
                signed_sum_not_sum_of_norms=True,
                original_all_mechanical_Q4_error=result['checks'][number]['Q4_only_witness']['equilibrium_relative_full_load_error']))
    assert not any(name.startswith(('anysolver','numpy','scipy','numba')) for name in sys.modules)
    assert all(sha(Path(path))==digest for path,digest in hashes.items())
    write('saved-chain-result.json',dict(status='SAVED_BINARY64_RECORD_ARITHMETIC_ONLY',generation=14,
        decimal_precision=60,inputs=hashes,results=reports,
        equation='FD(D.T f)-H0 t = Dbar.T rlaw + Dbar.T K0 rd + (Dbar-D0).T K0 D0t + (FD(D)-S0t).T fbar + (S0t).T(fbar-f0); rd=FD(d)-D0t; rlaw=FD(f)-K0FD(d)',
        extra_terms='Returned-pullback arithmetic plus saved-Q4 scatter/reconstruction; only translational rows are asserted equal to spatial forces.',
        limitations='Saved data expose total local forces, not inherited force and qualified correction separately. No internal roundoff bound, local constitutive/kinematic reevaluation, tangent-defect exclusion or new FD step.',
        affinity=p.cpu_affinity(),effective_numerical_library_modules=[],solver_evaluations=0,
        jit_environment=os.environ['NUMBA_DISABLE_JIT'],scientific_acceptance=False))
finally:
    stop.set();thread.join(timeout=1)
    write('resource-summary.json',dict(peak_tree_rss=peak[0],affinity=p.cpu_affinity(),solver_evaluations=0))