"""Single-use F03-K1 rank-only inventory; no physical KKT acceptance."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import traceback

from probe_b3_ge_e4_pl_g0_f03_k1_rank import MESHES, NAMES, screen_mesh
from run_b3_ge_e4_pl_g0_f03_d1 import identity as d1_identity
from run_b3_ge_e4_pl_g0_f03_k0 import (
    EVIDENCE_ROOT, MemoryMonitor, ROOT, sha256,
)


GATE='G0_F03_K1_RANK_V1'
SOURCES=(
    'docs/agent_plans/B3_GE_E4_PL_G0_F03_K1_DESIGN.md',
    'scripts/probe_b3_ge_e4_pl_g0_f03_k1_rank.py',
    'scripts/run_b3_ge_e4_pl_g0_f03_k1.py',
    'scripts/supervise_b3_ge_e4_pl_g0_f03_k1.py',
)
LIMITS={'wall_seconds':7200,'sampled_rss_limit_bytes':8*1024**3}
PROTOCOL={'meshes':[list(x) for x in MESHES],
          'spaces':list(NAMES),'relative_rank_threshold':1e-10,
          'status':'RANK_INVENTORY_ONLY_NOT_F03_ACCEPTANCE'}


def identity():
    return {'predecessor_source':d1_identity(),
            'k1_source_sha256':{name:sha256(ROOT/name) for name in SOURCES}}


def verify(registration,observed,evidence):
    if (registration.get('gate') != GATE
            or registration.get('status') != 'FROZEN'
            or registration.get('identity') != observed
            or registration.get('protocol') != PROTOCOL
            or registration.get('limits') != LIMITS
            or registration.get('evidence_directory') != str(evidence)
            or evidence.parent != EVIDENCE_ROOT
            or evidence.exists()):
        raise ValueError('exact frozen K1 registration or new evidence path required')
    if observed['predecessor_source']['base']['total_memory_bytes'] < LIMITS[
            'sampled_rss_limit_bytes']:
        raise ValueError('RSS limit exceeds physical memory')


def run(registration_path: Path,evidence: Path):
    registration_path=registration_path.resolve(strict=True)
    evidence=evidence.resolve()
    registration=json.loads(registration_path.read_text(encoding='utf-8'))
    observed=identity()
    verify(registration,observed,evidence)
    registration_hash=sha256(registration_path)
    evidence.mkdir(exist_ok=False)
    started=time.monotonic()
    with (evidence/'raw.jsonl').open('x',encoding='utf-8') as raw, MemoryMonitor() as monitor:
        def emit(record):
            raw.write(json.dumps(record,sort_keys=True,allow_nan=False)+'\n')
            raw.flush();os.fsync(raw.fileno())
        emit({'type':'start','registration':registration,
              'registration_sha256':registration_hash,'identity':observed})
        count=0
        statuses={}
        eligible=set(NAMES)
        try:
            for case in MESHES:
                row=screen_mesh(*case)
                count+=1
                for candidate in row['cases']:
                    status=candidate['status']
                    statuses[status]=statuses.get(status,0)+1
                    if status not in ('FULL_ROW_RANK_WITH_TRACE_MODES',
                                      'FULL_ROW_RANK_NO_TRACE_MODES'):
                        eligible.discard(candidate['space'])
                emit({'type':'mesh','index':count,'data':row,
                      'elapsed_seconds':time.monotonic()-started,
                      'rss_bytes':monitor.process.memory_info().rss})
                if time.monotonic()-started > LIMITS['wall_seconds']:
                    raise TimeoutError('registered cooperative wall limit')
                if monitor.maximum > LIMITS['sampled_rss_limit_bytes']:
                    raise MemoryError('registered sampled RSS limit')
            if (count != len(MESHES) or sum(statuses.values()) != len(MESHES)*len(NAMES)
                    or identity() != observed
                    or sha256(registration_path) != registration_hash):
                raise RuntimeError('incomplete inventory or changed identity')
            emit({'type':'terminal','status':PROTOCOL['status'],
                  'completed_meshes':count,'status_counts':statuses,
                  'full_rank_all_meshes':sorted(eligible),
                  'elapsed_seconds':time.monotonic()-started,
                  'sampled_peak_rss_bytes':monitor.maximum})
            return 0
        except BaseException as exc:
            emit({'type':'terminal','status':'ABORTED_NOT_QUALIFIED',
                  'completed_meshes':count,'status_counts':statuses,
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
