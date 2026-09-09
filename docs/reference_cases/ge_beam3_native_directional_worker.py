"""Bounded authentic-state native directional variation; no history advance."""
import argparse
from fractions import Fraction
from hashlib import sha256
import os
from pathlib import Path
import sys
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,read
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_scaled_energy_worker import load,PACKETS
from docs.reference_cases.ge_beam3_spatial_stability_worker import inputs

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-negative-work-0c0b043-20260909')
MANIFEST='55e6e7cfe7f588e637c60bea415a47ac5a59dac97bdbee1c69ce83fe4ae1177d'
WITNESS={'plus':'a465c0c8fc5b36b691443c4047e354d0c2f176aa27a8f234ab954d8962d4795d',
         'minus':'392e6eb53edaeed761ec8d4d3c852b4164a73ff11fd1c1e1e152e58f400b87a8'}
CHECK={'plus':'8db94812c02a900aa087125f232e00651e46a376a0bd4c3b2ba469042cb9f105',
       'minus':'ad892f0a38df49dfc7c49d7d6088ab9d90aacdaca5979096847d4f2ca7d9b785'}


def witness_input(sign):
    if sign not in WITNESS:raise ValueError('registered signed endpoint')
    raw=read(ARCHIVE/'manifest.json')
    if sha256(raw).hexdigest()!=MANIFEST:raise ValueError('witness archive identity')
    manifest=strict_bytes(raw);values=[]
    for label,name,digest in (('produce','witness',WITNESS[sign]),('check','exact',CHECK[sign])):
        path='wave/'+sign+'-'+label+'-a/output/'+name+'.json';data=read(ARCHIVE/path)
        rows=[r for r in manifest['entries'] if r['path']==path]
        if len(rows)!=1 or rows[0]['bytes']!=len(data) or rows[0]['sha256']!=digest or sha256(data).hexdigest()!=digest:
            raise ValueError('bound witness/checker bytes')
        values.append(strict_bytes(data))
    witness,checked=values
    if (witness['packet_sha256']!=PACKETS[sign] or checked['packet_sha256']!=PACKETS[sign]
            or checked['witness_sha256']!=WITNESS[sign] or not checked['result']['exact_negative']):
        raise ValueError('original exact work authority')
    q=checked['result']['total'];expected=Fraction(int(q['numerator']),int(q['denominator']))
    if expected>=0:raise ValueError('negative direction required')
    return witness,checked,float(expected)


def run(revision,sign,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('single numerical thread')
    packet=load(sign);source=inputs(sign);witness,checked,expected=witness_input(sign)
    if witness['free_dofs']!=packet['free_dofs']:raise ValueError('original free-space identity')
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('fresh external native trial output')
    root.mkdir(exist_ok=False);sys.path.insert(0,str(ROOT/'src'))
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from docs.reference_cases.ge_beam3_refined_controlled_case import model
    from docs.reference_cases.ge_beam3_native_directional_work import evaluate,adjudicate
    direction=1. if sign=='plus' else -1.
    program=owner.Program((direction*.0045,direction*.006),13,(0.,0.,1.),NodalDeadForces(((25,0.,-1.,0.),)))
    print(dict(stage='authentic-native-state-replay',sign=sign),flush=True)
    context=owner.Context(model(24),program,source['seed.json'],expected_seed_sha256=sha256(source['seed.json']).hexdigest())
    state,records=context.restore(source['checkpoint.json'],expected_sha256=sha256(source['checkpoint.json']).hexdigest())
    if context.checkpoint(records)!=source['checkpoint.json']:raise ValueError('original checkpoint replay')
    state_bytes=canonical(state);recovery=canonical(context.recover(state))
    result=evaluate(context,state,packet,witness['direction'],progress=lambda row:print(row,flush=True))
    adjudicate(result,expected)
    if (canonical(state)!=state_bytes or canonical(context.recover(state))!=recovery
            or context.checkpoint(records)!=source['checkpoint.json']):raise ValueError('native trial changed accepted state/history/recovery')
    guard(revision)
    if inputs(sign)!=source or witness_input(sign)!=(witness,checked,expected):raise ValueError('external input changed')
    load(sign)
    write(root/'native.json',dict(schema='GE_BEAM3_N24_NATIVE_NEGATIVE_SECOND_VARIATION_V1',revision=revision,
        sign=sign,packet_sha256=PACKETS[sign],witness_sha256=WITNESS[sign],exact_work_sha256=CHECK[sign],
        expected_factor_work=expected,result=result,state_sha256=sha256(state_bytes).hexdigest(),
        checkpoint_sha256=sha256(source['checkpoint.json']).hexdigest(),recovery_sha256=sha256(recovery).hexdigest(),
        original_checkpoint_unchanged=True,original_recovery_unchanged=True,production_qualified=False,
        independent_author_review='PENDING',physical_loading_path_from_rest=False))
    print(dict(stage='native-negative-second-variation-complete',sign=sign),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True)
    p.add_argument('--output',required=True);a=p.parse_args();run(a.revision,a.sign,a.output)
