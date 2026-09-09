"""Saved endpoint negative direction and independent exact work execution."""
import argparse
from decimal import Decimal as D,localcontext
from hashlib import sha256
import os
from pathlib import Path
from time import monotonic
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,read
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_scaled_energy_worker import load,PACKETS

PRIOR=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-scaled-energy-4608ace-20260909')
PRIOR_MANIFEST='3dcdc558b0b49de53858eb2c0185d348cc4448dc0c79060d783a428b7ebb1690'
ENERGY={'plus':'c24836015f457188e199653fd82fc91463081e981171f040e9fb52aa2bbd54c3',
        'minus':'5594e69b738402d037983ef1a070d9cdc7923948af36138cc67671d042751c61'}


def prior(sign):
    if sign not in ENERGY:raise ValueError('registered sign')
    manifest=read(PRIOR/'manifest.json')
    if sha256(manifest).hexdigest()!=PRIOR_MANIFEST:raise ValueError('prior energy archive hash')
    path='wave/'+sign+'-100-a/output/energy.json'
    rows=[r for r in strict_bytes(manifest)['entries'] if r['path']==path]
    raw=read(PRIOR/path)
    if len(rows)!=1 or rows[0]['bytes']!=len(raw) or rows[0]['sha256']!=ENERGY[sign] or sha256(raw).hexdigest()!=ENERGY[sign]:
        raise ValueError('prior precise energy binding')
    value=strict_bytes(raw)
    if value['packet_sha256']!=PACKETS[sign] or value['result']['digits']!=100:raise ValueError('prior input/precision')
    row=value['result']['rows'][0]
    if row['negative']!=1 or row['positive']!=425:raise ValueError('accepted endpoint scope')
    return row


def produce(revision,sign,root):
    packet=load(sign);accepted=prior(sign);start=monotonic()
    def check():
        if monotonic()-start>120:raise ValueError('witness construction deadline')
    from docs.reference_cases.ge_beam3_negative_scaled_witness import witness
    with localcontext() as context:
        context.prec=100
        def sparse(a):return [{i:D.from_float(x) for i,x in enumerate(row) if x} for row in a]
        ll,rr=sparse(packet['left']),sparse(packet['right']);ff=[];n=len(packet['geometric'])
        for row in ll:
            check();out={}
            for j,value in row.items():
                for k,v in rr[j].items():out[k]=out.get(k,D(0))+value*v
            ff.append(out)
        k=[[D(0)]*n for _ in range(n)]
        for row in ff:
            check();entries=sorted(row.items())
            for index,(i,x) in enumerate(entries):
                for j,y in entries[index:]:k[i][j]+=x*y
        g=[[D.from_float(x) for x in row] for row in packet['geometric']]
        for i in range(n):
            for j in range(i,n):
                value=k[i][j]+(g[i][j]+g[j][i])/2;k[i][j]=k[j][i]=value
        free=packet['free_dofs'];matrix=[[k[i][j] for j in free] for i in free]
        print(dict(stage='full-negative-direction-factorization',sign=sign),flush=True)
        result=witness(matrix,check)
        for key in ('negative','positive','pivot_indices','pivot_sizes','coordinate_scales'):
            if result[key]!=accepted[key]:raise ValueError('witness changed accepted factor path')
        direction=result.pop('negative_direction')
    guard(revision);load(sign);prior(sign)
    write(root/'witness.json',dict(schema='GE_BEAM3_N24_EXPLICIT_NEGATIVE_WORK_WITNESS_V1',
        revision=revision,sign=sign,packet_sha256=PACKETS[sign],prior_energy_sha256=ENERGY[sign],
        free_dofs=free,direction=direction,factorization=result,production_qualified=False,
        physical_interval_certified=False,raw_tangent_exact_symmetry_proved=False))
    print(dict(stage='negative-direction-complete',sign=sign),flush=True)


def check_saved(revision,path,digest,root):
    raw=read(path)
    if sha256(raw).hexdigest()!=digest:raise ValueError('external witness hash')
    v=strict_bytes(raw)
    if set(v)!={'schema','revision','sign','packet_sha256','prior_energy_sha256','free_dofs','direction','factorization',
                'production_qualified','physical_interval_certified','raw_tangent_exact_symmetry_proved'}:
        raise ValueError('exact witness schema')
    if v['schema']!='GE_BEAM3_N24_EXPLICIT_NEGATIVE_WORK_WITNESS_V1' or v['revision']!=revision:raise ValueError('witness authority')
    sign=v['sign'];packet=load(sign);prior(sign)
    if (v['packet_sha256']!=PACKETS[sign] or v['prior_energy_sha256']!=ENERGY[sign]
            or v['free_dofs']!=packet['free_dofs'] or 74 not in v['free_dofs']):raise ValueError('original factor/free-space binding')
    if any(v[k] is not False for k in ('production_qualified','physical_interval_certified','raw_tangent_exact_symmetry_proved')):
        raise ValueError('unproved witness claims')
    from docs.reference_cases.ge_beam3_exact_negative_work import verify
    print(dict(stage='exact-original-factor-work',sign=sign),flush=True)
    result=verify(packet['left'],packet['right'],packet['geometric'],tuple(v['free_dofs']),v['direction'])
    if read(path)!=raw:raise ValueError('witness changed during verification')
    guard(revision);load(sign);prior(sign)
    write(root/'exact.json',dict(schema='GE_BEAM3_N24_EXACT_NEGATIVE_WORK_CHECK_V1',revision=revision,
        sign=sign,witness_sha256=digest,packet_sha256=PACKETS[sign],result=result,
        independent_author_review='PENDING',production_qualified=False))
    print(dict(stage='exact-negative-work-verified',sign=sign),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--mode',choices=('produce','check'),required=True)
    p.add_argument('--sign',choices=('plus','minus'));p.add_argument('--witness');p.add_argument('--sha256');p.add_argument('--output',required=True)
    a=p.parse_args();guard(a.revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('single numerical thread')
    root=Path(a.output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('external fresh output required')
    root.mkdir(exist_ok=False)
    if a.mode=='produce':produce(a.revision,a.sign,root)
    else:check_saved(a.revision,a.witness,a.sha256,root)
