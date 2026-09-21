"""Single-use native-image rank diagnostic; no F03/G0 acceptance."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import traceback

from probe_b3_ge_e4_pl_g0_f03_k2l import MESHES, NAMES, RELATIVE_CUTOFF, screen_mesh
from run_b3_ge_e4_pl_g0_f03_k0 import EVIDENCE_ROOT, MemoryMonitor, ROOT, sha256
from run_b3_ge_e4_pl_g0_f03_k2p import identity as k2p_identity


GATE='G0_F03_K2L_V1'
SOURCES=(
    'docs/agent_plans/B3_GE_E4_PL_G0_F03_K2L_DESIGN.md',
    'docs/agent_plans/B3_GE_E4_PL_G0_F03_K2L_PREEXEC_REVIEW_V1.md',
    'scripts/probe_b3_ge_e4_pl_g0_f03_k2l.py',
    'scripts/run_b3_ge_e4_pl_g0_f03_k2l.py',
    'scripts/supervise_b3_ge_e4_pl_g0_f03_k2l.py',
)
LIMITS={'wall_seconds':1200,'sampled_rss_limit_bytes':8*1024**3}
PROTOCOL={'meshes':[list(item) for item in MESHES],
          'spaces':list(NAMES),'relative_cutoff':RELATIVE_CUTOFF,
          'status':'NATIVE_IMAGE_INVENTORY_NOT_F03_ACCEPTANCE'}


def identity():
    evidence=EVIDENCE_ROOT
    predecessor='f03-k2p-v1'
    return {
        'predecessor_source':k2p_identity(),
        'predecessor_evidence_sha256':{
            'registration':sha256(evidence/(predecessor+'-registration.json')),
            'raw':sha256(evidence/predecessor/'raw.jsonl'),
            'attestation':sha256(evidence/(predecessor+'.attestation.json'))},
        'k2l_source_sha256':{name:sha256(ROOT/name) for name in SOURCES}}


def verify(registration,observed,evidence):
    if (registration.get('gate') != GATE
            or registration.get('status') != 'FROZEN'
            or registration.get('identity') != observed
            or registration.get('protocol') != PROTOCOL
            or registration.get('limits') != LIMITS
            or registration.get('evidence_directory') != str(evidence)
            or evidence.parent != EVIDENCE_ROOT or evidence.exists()):
        raise ValueError('frozen K2L registration or cold evidence mismatch')
    base=observed['predecessor_source']['predecessor_source'][
        'predecessor_source']['base']
    if base['total_memory_bytes'] < LIMITS['sampled_rss_limit_bytes']:
        raise ValueError('RSS limit exceeds physical memory')


def run(registration_path: Path,evidence: Path):
    registration_path=registration_path.resolve(strict=True)
    evidence=evidence.resolve()
    registration=json.loads(registration_path.read_text(encoding='utf-8'))
    observed=identity()
    verify(registration,observed,evidence)
    reg_hash=sha256(registration_path)
    evidence.mkdir(exist_ok=False)
    started=time.monotonic()
    status_counts={}
    count=0
    with (evidence/'raw.jsonl').open('x',encoding='utf-8') as raw, MemoryMonitor() as monitor:
        def emit(item):
            raw.write(json.dumps(item,sort_keys=True,allow_nan=False)+'\n')
            raw.flush();os.fsync(raw.fileno())
        emit({'type':'start','registration':registration,
              'registration_sha256':reg_hash,'identity':observed})
        try:
            for case in MESHES:
                row=screen_mesh(*case)
                count+=1
                if [item['space'] for item in row['cases']] != list(NAMES):
                    raise AssertionError('candidate inventory mismatch')
                for item in row['cases']:
                    status_counts[item['status']]=status_counts.get(item['status'],0)+1
                emit({'type':'mesh','index':count,'data':row,
                      'elapsed_seconds':time.monotonic()-started,
                      'rss_bytes':monitor.process.memory_info().rss})
                if time.monotonic()-started > LIMITS['wall_seconds']:
                    raise TimeoutError('registered cooperative wall limit')
                if monitor.maximum > LIMITS['sampled_rss_limit_bytes']:
                    raise MemoryError('registered sampled RSS limit')
            if (count != len(MESHES)
                    or sum(status_counts.values()) != len(MESHES)*len(NAMES)
                    or identity() != observed or sha256(registration_path) != reg_hash):
                raise RuntimeError('source/registration changed during K2L')
            emit({'type':'terminal','status':PROTOCOL['status'],
                  'completed_meshes':count,'status_counts':status_counts,
                  'elapsed_seconds':time.monotonic()-started,
                  'sampled_peak_rss_bytes':monitor.maximum})
            return 0
        except BaseException as exc:
            emit({'type':'terminal','status':'ABORTED_NOT_QUALIFIED',
                  'completed_meshes':count,'status_counts':status_counts,
                  'failure_type':type(exc).__name__,'failure':str(exc),
                  'traceback':traceback.format_exc(),
                  'elapsed_seconds':time.monotonic()-started,
                  'sampled_peak_rss_bytes':monitor.maximum})
            raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(run(args.registration,args.evidence))
