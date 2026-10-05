"""External wall/RSS supervisor and one-shot K1 evidence attestation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

from probe_b3_ge_e4_pl_g0_f03_k1_rank import MESHES, NAMES
from run_b3_ge_e4_pl_g0_f03_k1 import ROOT, identity, sha256, verify


def supervise(registration_path: Path,evidence: Path):
    registration_path=registration_path.resolve(strict=True)
    evidence=evidence.resolve()
    registration=json.loads(registration_path.read_text(encoding='utf-8'))
    observed=identity()
    verify(registration,observed,evidence)
    paths={name:evidence.with_name(evidence.name+f'.{name}')
           for name in ('stdout.log','stderr.log','attestation.json')}
    if any(p.exists() for p in paths.values()):
        raise FileExistsError('K1 evidence registration already consumed')
    started=time.monotonic()
    peak=0
    violation=None
    supervisor_error=None
    child=None
    with paths['stdout.log'].open('x',encoding='utf-8') as stdout, \
            paths['stderr.log'].open('x',encoding='utf-8') as stderr:
        try:
            child=subprocess.Popen((sys.executable,str(ROOT/
                                   'scripts/run_b3_ge_e4_pl_g0_f03_k1.py'),
                                   '--registration',str(registration_path),
                                   '--evidence',str(evidence)),cwd=ROOT,
                                   stdout=stdout,stderr=stderr)
            process=psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    peak=max(peak,process.memory_info().rss)
                except psutil.NoSuchProcess:
                    pass
                if time.monotonic()-started > registration['limits']['wall_seconds']:
                    violation='EXTERNAL_WALL_TIMEOUT'
                elif peak > registration['limits']['sampled_rss_limit_bytes']:
                    violation='SAMPLED_RSS_LIMIT'
                if violation:
                    child.kill()
                    break
                time.sleep(.1)
        except BaseException as exc:
            supervisor_error=f'{type(exc).__name__}: {exc}'
            if child is not None and child.poll() is None:
                child.kill()
        finally:
            exit_code=child.wait() if child is not None else None
            stdout.flush();os.fsync(stdout.fileno())
            stderr.flush();os.fsync(stderr.fileno())
    raw=evidence/'raw.jsonl'
    read_error=None
    rows=[]
    statuses={}
    eligible=set(NAMES)
    try:
        if not raw.exists():
            raise ValueError('raw K1 evidence missing')
        with raw.open(encoding='utf-8') as source:
            rows=[json.loads(line) for line in source]
        if len(rows) != len(MESHES)+2:
            raise ValueError('exact K1 evidence length mismatch')
        start=rows[0]
        if (start.get('type') != 'start'
                or start.get('registration_sha256') != sha256(registration_path)
                or start.get('registration') != registration
                or start.get('identity') != observed):
            raise ValueError('K1 start identity mismatch')
        for index,case in enumerate(MESHES,1):
            item=rows[index]
            data=item['data']
            if (item.get('type') != 'mesh' or item.get('index') != index
                    or (data['topology'],data['n_beam'],data['n_shell']) != case
                    or [c['space'] for c in data['cases']] != list(NAMES)):
                raise ValueError('K1 ordered mesh/space inventory mismatch')
            for candidate in data['cases']:
                status=candidate['status']
                statuses[status]=statuses.get(status,0)+1
                if (candidate['constraint_rows'] != 3*candidate['basis_dimension']
                        or not candidate['basis_knots']):
                    raise ValueError('K1 candidate schema incomplete')
                if status == 'INVALID_QUADRATURE_REFERENCE':
                    if (candidate.get('failure_type') != 'ValueError'
                            or candidate.get('failure') !=
                               'quadrature reference norm zero or nonfinite'):
                        raise ValueError('K1 quadrature failure malformed')
                    eligible.discard(candidate['space'])
                    continue
                if (candidate['reference_consistency']['stations'] < 1
                        or candidate['max_row_incidence'] < 1
                        or not candidate['integration_knots']):
                    raise ValueError('K1 assembled candidate schema incomplete')
                if status in ('FULL_ROW_RANK_WITH_TRACE_MODES',
                              'FULL_ROW_RANK_NO_TRACE_MODES'):
                    if (len(candidate['row_singular']) != candidate['constraint_rows']
                            or candidate['row_rank'] != candidate['constraint_rows']
                            or candidate['unsupported_trace_modes'] !=
                               candidate['trace_rank']-candidate['row_rank']):
                        raise ValueError('K1 rank outcome malformed')
                else:
                    eligible.discard(candidate['space'])
        terminal=rows[-1]
        if (terminal.get('type') != 'terminal'
                or terminal.get('status') !=
                   'RANK_INVENTORY_ONLY_NOT_F03_ACCEPTANCE'
                or terminal.get('completed_meshes') != len(MESHES)
                or terminal.get('status_counts') != statuses
                or terminal.get('full_rank_all_meshes') != sorted(eligible)
                or sum(statuses.values()) != len(MESHES)*len(NAMES)):
            raise ValueError('K1 terminal inventory inconsistent')
    except (ValueError,TypeError,KeyError,UnicodeError) as exc:
        read_error=str(exc)
    success=(exit_code == 0 and violation is None and supervisor_error is None
             and read_error is None)
    attestation={
        'status':('COMPLETE_RANK_INVENTORY_NOT_F03_ACCEPTANCE' if success else
                  'ABORTED_OR_INCOMPLETE_NOT_QUALIFIED'),
        'exit_code':exit_code,'violation':violation,
        'supervisor_error':supervisor_error,'read_error':read_error,
        'observed_meshes':max(0,len(rows)-2),
        'status_counts':statuses,'full_rank_all_meshes':sorted(eligible),
        'elapsed_seconds':time.monotonic()-started,
        'sampled_peak_rss_bytes':peak,
        'registration_sha256':sha256(registration_path),
        'raw_sha256':sha256(raw) if raw.exists() else None,
        'stdout_sha256':sha256(paths['stdout.log']),
        'stderr_sha256':sha256(paths['stderr.log']),
        'identity':observed}
    with paths['attestation.json'].open('x',encoding='utf-8') as out:
        json.dump(attestation,out,indent=2,sort_keys=True,allow_nan=False)
        out.flush();os.fsync(out.fileno())
    return 0 if success else 2


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(supervise(args.registration,args.evidence))
