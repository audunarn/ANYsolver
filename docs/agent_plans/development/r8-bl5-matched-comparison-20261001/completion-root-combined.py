"""Combine protected completed sensitivity and root-work evidence; no solves."""
from pathlib import Path
import hashlib,json,math,zipfile
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
end=ROOT/'endport-support-work.json'
assert sha(end)=='48f2132a483b19b803f6ad6623de8fab6cec83c56e9eb15432b39fd0e6ffc777'
a=ROOT.parent/'r8-bl5-completion-sensitivity-20261001/repair-v3-v4.zip'
assert sha(a)=='c781023a9df4500f4fa9ea16ec442651a72065427f87cbd3d4028ff8702680a0'
with zipfile.ZipFile(a) as z:
    raw=z.read('assessment/raw/result.json')
    assert hashlib.sha256(raw).hexdigest()=='ee9350ea262226261083ab49e50922dd21dbc3b7a1d8cc4deec43e3f1aba03ab'
    r=json.loads(raw)
s=json.loads(end.read_text())
assert r['status']=='COMPLETED_DEVELOPMENT_ONLY'
assert s['difference_sign']=='native minus external' and s['norm_scale']=='Lref1m: forces and M/Lref in N'
checked={}; common={}
for name,h in s['bound_inputs'].items():
    p=Path(name);assert sha(p)==h;checked[name]=h
    for key,expected in r['saved_input_sha256'].items():
        if p.as_posix().replace('//','/').endswith('/n64/'+key):
            assert h==expected;common[key]=h
assert {'operators.npz','inputs.json','layout.json','mz/raw-state.npz'} <= set(common)
roots={Path(name).parent for name in checked if Path(name).name=='operators.npz' and Path(name).parent.name=='n64'}
assert len(roots)==1
saved_root=roots.pop()
for key,expected in r['saved_input_sha256'].items():assert sha(saved_root/key)==expected
c=next(v for v in s['cases'] if v['nx']==64 and v['case']=='mz')
dot=lambda a,b:math.fsum(x*y for x,y in zip(a,b))
records={}
for domain,block in c['domains'].items():
    delta=block['delta_common_origin']['R']
    derivative=r['domain_wrench_derivatives'][domain]['ground']
    dn=math.hypot(*delta);sn=math.hypot(*derivative)
    assert dn>0 and sn>0 and all(map(math.isfinite,delta+derivative))
    records[domain]=dict(discrepancy=delta,derivative_per_unit_alpha=derivative,
        norm_ratio=sn/dn,projection_on_discrepancy=dot(delta,derivative)/dot(delta,delta),
        direction_cosine=dot(delta,derivative)/(dn*sn),
        fy_derivative_to_discrepancy=derivative[1]/delta[1],
        fy_derivative_to_native_reaction=derivative[1]/block['common_origin_native']['R'][1])
record=dict(classification='combined leading-order development interpretation; no causal allocation or acceptance',
    source_sha256=sha(Path(__file__)),input_sha256={'endport':sha(end),'repair_archive':sha(a)},
    verified_bound_inputs=len(checked),common_saved_inputs=len(common),verified_repair_inputs=len(r['saved_input_sha256']),parameter='common PL+hourglass coefficient alpha at1; C/supports/load fixed',
    moment_origin_m=[0.,0.,.0675],scale='1m force-equivalent; no scientific threshold',
    applied_work_relative_derivative=r['applied_work_relative_derivative'],domains=records,
    warning='Projection is a signed alignment, not a causal fraction. A local derivative cannot predict finite removal.',
    decision='Completion sensitivity is material for root transfer on this fixture despite small total-work slope. '
      'Do not dismiss it or tune coefficients; no new factorization/refinement/reference is justified by this contraction alone.')
(ROOT/'completion-root-combined.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(verified_inputs=len(checked),work_slope=record['applied_work_relative_derivative'],beam=records['beam'])))
