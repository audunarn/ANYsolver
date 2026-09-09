"""Front-aware saved-factor energy-form successor; imports no production mechanics."""
import argparse
from hashlib import sha256
import os
from pathlib import Path
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes, canonical
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_spatial_stability_worker import inputs

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-spatial-stability-d0ef7f5-20260909')
MANIFEST='3700cf12a6b82b0148f843366c5c5c4b5316d8371925da34aa38d5bd12f9abdd'
CAPTURE_REVISION='d0ef7f5b72c57ebfc49cf13189fe53e73e4086f2'
PACKETS={'plus':'3c5a16d4616947e0872983350a028c4079008af4902df1efe427b76580855d00',
         'minus':'1ba92a5a4c93e51036a617a99e22ec89f812caf2599cb69d00c5553ade9a08ad'}


def load(sign):
    if sign not in PACKETS:raise ValueError('registered endpoint sign')
    manifest=(ARCHIVE/'manifest.json').read_bytes()
    if sha256(manifest).hexdigest()!=MANIFEST:raise ValueError('saved factor archive identity')
    rows=strict_bytes(manifest)['entries']
    name='wave/'+sign+'-capture/output/packet.json'
    row=[r for r in rows if r['path']==name]
    if len(row)!=1:raise ValueError('unique archived factor member')
    raw=(ARCHIVE/name).read_bytes()
    if (sha256(raw).hexdigest()!=PACKETS[sign] or len(raw)!=row[0]['bytes']
            or row[0]['sha256']!=PACKETS[sign]):raise ValueError('bound factor bytes')
    v=strict_bytes(raw);p=v['packet'];source=inputs(sign)
    if (v['revision']!=CAPTURE_REVISION or v['schema']!='GE_BEAM3_N24_SPATIAL_FACTORS_V1'
            or v['sign']!=sign or v['production_qualified'] is not False):raise ValueError('capture policy')
    if (p['checkpoint_sha256']!=sha256(source['checkpoint.json']).hexdigest()
            or p['seed_sha256']!=sha256(source['seed.json']).hexdigest()):raise ValueError('actual seed/checkpoint binding')
    if (p['control_constraint_in_physical_stiffness'] is not False or p['physical_loading_path_from_rest'] is not False
            or p['production_qualified'] is not False or p['completed_targets']!=2):raise ValueError('physical state policy')
    body={k:p[k] for k in ('left','right','geometric','kinetic','stiffness','mass','net_residual',
        'free_dofs','algebraic_dofs','internal_layout','compliance_errors','checkpoint_sha256','model_sha256',
        'parameter','completed_targets','displacement_target')}
    if sha256(canonical(dict(policy=p['policy'],**body))).hexdigest()!=p['identity']:raise ValueError('factor object identity')
    if len(p['geometric'])!=438 or len(set(p['free_dofs']))!=426 or 74 not in p['free_dofs']:
        raise ValueError('full physical perturbation space')
    return p


def run(revision,sign,digits,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('single numerical thread')
    p=load(sign)
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('external fresh output')
    root.mkdir(exist_ok=False)
    from docs.reference_cases.ge_beam3_scaled_energy_inertia import audit
    print(dict(stage='full-energy-form-audit',sign=sign,digits=digits),flush=True)
    result=audit(p['left'],p['right'],p['geometric'],p['kinetic'],tuple(p['free_dofs']),
                 tuple(p['algebraic_dofs']),(0.,),digits=digits)
    if result['physical_dimension']!=285 or result['algebraic_dimension']!=141:raise ValueError('full mass split')
    guard(revision);load(sign)
    write(root/'energy.json',dict(schema='GE_BEAM3_N24_SCALED_FRONT_ENERGY_INERTIA_V1',revision=revision,
        capture_revision=CAPTURE_REVISION,sign=sign,packet_sha256=PACKETS[sign],result=result,
        production_qualified=False,raw_tangent_exact_symmetry_proved=False,
        physical_interval_certified=False,independent_author_review='PENDING'))
    print(dict(stage='energy-inertia-complete',negative=result['rows'][0]['negative']),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True)
    p.add_argument('--digits',type=int,choices=(80,100),required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.revision,a.sign,a.digits,a.output)
