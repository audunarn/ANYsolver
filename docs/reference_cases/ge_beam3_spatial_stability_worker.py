"""Actual N24 endpoint factor capture and separate full-spatial inertia audit."""
import argparse
from hashlib import sha256
import os
from pathlib import Path
import sys
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT

ARCHIVE = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-spatial-refinement24-aea4c0c-20260909')
MANIFEST = 'ab327928e6a5b4ad8c0e3b72b564e9321e56e29693764ec8f418d2e2a3f061c9'


def serialize_packet(packet):
    from anysolver._ge_beam3_p5_seeded.core import canonical
    return strict_bytes(canonical(packet))


def inputs(sign):
    if sign not in ('plus', 'minus'): raise ValueError('registered sign')
    raw = (ARCHIVE/'manifest.json').read_bytes()
    if sha256(raw).hexdigest() != MANIFEST: raise ValueError('refinement archive authority')
    manifest = strict_bytes(raw)
    records = {r['path']: r for r in manifest['entries']}
    if len(records) != len(manifest['entries']): raise ValueError('duplicate archive member')
    result = {}
    for name in ('seed.json', 'checkpoint.json'):
        path = 'wave/'+sign+'-endpoint-a/output/'+name
        data = (ARCHIVE/path).read_bytes(); record = records[path]
        if len(data) != record['bytes'] or sha256(data).hexdigest() != record['sha256']:
            raise ValueError('actual endpoint source hash')
        strict_bytes(data); result[name] = data
    return result


def capture(revision, sign, root):
    source = inputs(sign)
    sys.path.insert(0, str(ROOT/'src'))
    from anysolver import _ge_beam3_elastic_seed_modal as modal
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from docs.reference_cases.ge_beam3_refined_controlled_case import model, masses
    direction = 1. if sign == 'plus' else -1.
    program = owner.Program((direction*.0045, direction*.006), 13, (0., 0., 1.),
                            NodalDeadForces(((25, 0., -1., 0.),)))
    made = model(24)
    print(dict(stage='authenticated-endpoint-replay', sign=sign), flush=True)
    packet, check = modal.prepare(made, program, source['seed.json'], source['checkpoint.json'], masses(made),
        expected_seed_sha256=sha256(source['seed.json']).hexdigest(),
        expected_sha256=sha256(source['checkpoint.json']).hexdigest())
    if len(packet.free_dofs) != 426 or packet.completed_targets != 2:
        raise ValueError('complete N24 spatial endpoint extent')
    if 74 not in packet.free_dofs or packet.control_constraint_in_physical_stiffness:
        raise ValueError('numerical lateral control must stay physically free')
    print(dict(stage='full-spatial-factors-captured', coordinates=438), flush=True)
    check(); guard(revision)
    if inputs(sign) != source: raise ValueError('endpoint changed during capture')
    write(root/'packet.json', dict(schema='GE_BEAM3_N24_SPATIAL_FACTORS_V1', revision=revision,
        sign=sign, archive_sha256=MANIFEST, packet=serialize_packet(packet), production_qualified=False))


def verify(revision, path, expected, digits, root):
    raw = Path(path).read_bytes()
    if sha256(raw).hexdigest() != expected: raise ValueError('external factor packet hash')
    value = strict_bytes(raw)
    if set(value) != {'schema', 'revision', 'sign', 'archive_sha256', 'packet', 'production_qualified'}:
        raise ValueError('exact factor wrapper schema')
    if (value['schema'] != 'GE_BEAM3_N24_SPATIAL_FACTORS_V1' or value['revision'] != revision
            or value['archive_sha256'] != MANIFEST or value['production_qualified'] is not False):
        raise ValueError('factor wrapper authority')
    source = inputs(value['sign']); p = value['packet']
    if p['checkpoint_sha256'] != sha256(source['checkpoint.json']).hexdigest():
        raise ValueError('factor checkpoint provenance')
    if (p['seed_sha256'] != sha256(source['seed.json']).hexdigest()
            or p['control_constraint_in_physical_stiffness'] is not False
            or p['physical_loading_path_from_rest'] is not False or p['production_qualified'] is not False
            or p['completed_targets'] != 2 or len(p['geometric']) != 438 or len(p['free_dofs']) != 426):
        raise ValueError('complete physical endpoint policy')
    from docs.reference_cases.ge_beam3_sparse_inertia_audit import audit
    print(dict(stage='full-spatial-decimal-start', digits=digits), flush=True)
    result = audit(p['left'], p['right'], p['geometric'], p['kinetic'],
                   tuple(p['free_dofs']), tuple(p['algebraic_dofs']), (0.,), digits=digits)
    if Path(path).read_bytes() != raw: raise ValueError('packet changed during audit')
    guard(revision)
    write(root/'audit.json', dict(schema='GE_BEAM3_N24_FULL_SPATIAL_INERTIA_V1', revision=revision,
        sign=value['sign'], packet_sha256=expected, result=result, production_qualified=False,
        interval_certified=False, independent_author_review='PENDING'))
    print(dict(stage='full-spatial-decimal-complete', negative=result['rows'][0]['negative']), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--revision', required=True)
    p.add_argument('--mode', choices=('capture', 'audit'), required=True)
    p.add_argument('--sign', choices=('plus', 'minus')); p.add_argument('--packet'); p.add_argument('--sha256')
    p.add_argument('--digits', type=int, choices=(80, 100)); p.add_argument('--output', required=True)
    a = p.parse_args(); guard(a.revision)
    if any(os.environ.get(k) != v for k, v in THREAD_ENVIRONMENT.items()):
        raise ValueError('single numerical thread')
    root = Path(a.output).resolve()
    if root.is_relative_to(ROOT): raise ValueError('external exclusive output required')
    root.mkdir(exist_ok=False)
    if a.mode == 'capture': capture(a.revision, a.sign, root)
    else: verify(a.revision, a.packet, a.sha256, a.digits, root)
