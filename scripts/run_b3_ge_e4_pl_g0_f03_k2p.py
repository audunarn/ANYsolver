"""One-shot fixed-load physical KKT diagnostic; no F03/G0 acceptance."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import traceback

from probe_b3_ge_e4_pl_g0_f03_k2p import LOADS, MESHES, NAMES, STATIONS, screen_mesh
from run_b3_ge_e4_pl_g0_f03_k1 import identity as k1_identity
from run_b3_ge_e4_pl_g0_f03_k0 import (
    EVIDENCE_ROOT, MemoryMonitor, ROOT, sha256,
)


GATE='G0_F03_K2P_V1'
SOURCES=(
    'docs/agent_plans/B3_GE_E4_PL_G0_F03_K2_DESIGN.md',
    'docs/agent_plans/B3_GE_E4_PL_G0_F03_K2_DESIGN_REVIEW_V1.md',
    'docs/agent_plans/B3_GE_E4_PL_G0_F03_K2P_MANIFEST.md',
    'docs/agent_plans/B3_GE_E4_PL_G0_F03_K2P_PREEXEC_REVIEW_V1.md',
    'scripts/probe_b3_ge_e4_pl_g0_f03_k2p.py',
    'scripts/run_b3_ge_e4_pl_g0_f03_k2p.py',
    'scripts/supervise_b3_ge_e4_pl_g0_f03_k2p.py',
)
LIMITS={'wall_seconds':7200,'sampled_rss_limit_bytes':8*1024**3}
PROTOCOL={'meshes':[list(x) for x in MESHES],
          'spaces':list(NAMES),'loads':list(LOADS),
          'stations':list(STATIONS),'force_density_n_per_m':1e6,
          'load_gauss_points':8,'load_reference_gauss_points':12,
          'legacy_smooth_parity_gauss_points':4,
          'length_m':1.,'yaw_to_length_m':.46,
          'status':'FIXED_LOAD_DIAGNOSTIC_COMPLETE_NOT_F03_ACCEPTANCE'}
PREDECESSOR_EVIDENCE=('f03-k0-v2','f03-d1-v1','f03-k1-rank-v1')


def predecessor_evidence_identity():
    return {name:{
        'registration_sha256':sha256(EVIDENCE_ROOT/(name+'-registration.json')),
        'attestation_sha256':sha256(EVIDENCE_ROOT/(name+'.attestation.json')),
        'raw_sha256':sha256(EVIDENCE_ROOT/name/'raw.jsonl')}
        for name in PREDECESSOR_EVIDENCE}


def identity():
    return {'predecessor_source':k1_identity(),
            'predecessor_evidence_sha256':predecessor_evidence_identity(),
            'k2p_source_sha256':{name:sha256(ROOT/name) for name in SOURCES}}


def verify(registration,observed,evidence):
    if (registration.get('gate') != GATE
            or registration.get('status') != 'FROZEN'
            or registration.get('identity') != observed
            or registration.get('protocol') != PROTOCOL
            or registration.get('limits') != LIMITS
            or registration.get('evidence_directory') != str(evidence)
            or evidence.parent != EVIDENCE_ROOT or evidence.exists()):
        raise ValueError('frozen K2P registration or cold output mismatch')
    memory=observed['predecessor_source'][
        'predecessor_source']['base']['total_memory_bytes']
    if memory < LIMITS['sampled_rss_limit_bytes']:
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
    candidate_counts={}
    load_counts={}
    mesh_count=0
    with (evidence/'raw.jsonl').open('x',encoding='utf-8') as raw, MemoryMonitor() as monitor:
        def emit(record):
            raw.write(json.dumps(record,sort_keys=True,allow_nan=False)+'\n')
            raw.flush();os.fsync(raw.fileno())
        emit({'type':'start','registration':registration,
              'registration_sha256':reg_hash,'identity':observed})
        try:
            for case in MESHES:
                row=screen_mesh(*case)
                mesh_count+=1
                if (len(row['cases']) != len(NAMES)
                        or [item['space'] for item in row['cases']] != list(NAMES)):
                    raise AssertionError('registered K2P candidate inventory missing')
                for item in row['cases']:
                    status=item['status']
                    candidate_counts[status]=candidate_counts.get(status,0)+1
                    if set(item['loads']) not in (set(),set(LOADS)):
                        raise AssertionError('partial K2P load inventory')
                    for result in item['loads'].values():
                        status=result['status']
                        load_counts[status]=load_counts.get(status,0)+1
                emit({'type':'mesh','index':mesh_count,'data':row,
                      'elapsed_seconds':time.monotonic()-started,
                      'rss_bytes':monitor.process.memory_info().rss})
                if time.monotonic()-started > LIMITS['wall_seconds']:
                    raise TimeoutError('registered cooperative wall limit')
                if monitor.maximum > LIMITS['sampled_rss_limit_bytes']:
                    raise MemoryError('registered sampled RSS limit')
            if (mesh_count != len(MESHES)
                    or sum(candidate_counts.values()) != len(MESHES)*len(NAMES)
                    or identity() != observed
                    or sha256(registration_path) != reg_hash):
                raise RuntimeError('source or registration changed during K2P')
            emit({'type':'terminal','status':PROTOCOL['status'],
                  'completed_meshes':mesh_count,
                  'candidate_status_counts':candidate_counts,
                  'load_status_counts':load_counts,
                  'observed_load_cases':sum(load_counts.values()),
                  'elapsed_seconds':time.monotonic()-started,
                  'sampled_peak_rss_bytes':monitor.maximum})
            return 0
        except BaseException as exc:
            emit({'type':'terminal','status':'ABORTED_NOT_QUALIFIED',
                  'completed_meshes':mesh_count,
                  'candidate_status_counts':candidate_counts,
                  'load_status_counts':load_counts,
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
