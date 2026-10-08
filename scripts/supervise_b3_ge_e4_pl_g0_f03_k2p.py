"""External process and immutable inventory attestation for F03-K2P."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

from probe_b3_ge_e4_pl_g0_f03_k2p import LOADS, MESHES, NAMES, STATIONS
from run_b3_ge_e4_pl_g0_f03_k2p import ROOT, identity, sha256, verify


PREEMPTED={'ROW_RANK_LOSS_NOT_F03_ACCEPTANCE',
           'INVALID_QUADRATURE_REFERENCE','MASS_INVALID',
           'MASS_OR_RANK_INVALID','INVALID_LOAD_QUADRATURE'}
COMPLETED_CANDIDATE={'TWO_LOAD_INVENTORY_WITH_FAILURES_NOT_F03_ACCEPTANCE',
                     'TWO_LOAD_INVENTORY_WITH_PARITY_OPEN',
                     'TWO_LOAD_LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE'}
LOAD_STATUSES={'NONFINITE_CANDIDATE_RESPONSE',
               'NUMERICAL_CANDIDATE_FAILURE',
               'NUMERICAL_OR_PHYSICAL_LOCAL_FAILURE',
               'LOCAL_DIAGNOSTIC_WITH_PARITY_OPEN',
               'LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE'}


def check_candidate(item):
    if not item['basis_dimension'] > 0 or not item['space'] in NAMES:
        raise ValueError('invalid K2P basis')
    status=item['status']
    if status in PREEMPTED:
        if item['loads']:
            raise ValueError('preempted candidate contains load results')
        return
    if status not in COMPLETED_CANDIDATE or set(item['loads']) != set(LOADS):
        raise ValueError('K2P candidate/load status grammar mismatch')
    for name,result in item['loads'].items():
        if result.get('status') not in LOAD_STATUSES:
            raise ValueError('unknown K2P load disposition')
        if result['status'].startswith('LOCAL_DIAGNOSTIC'):
            if (len(result['stations']) != len(STATIONS)
                    or [station['s'] for station in result['stations']]
                       != list(STATIONS)
                    or len(result['multiplier_coefficients_n_per_m']) !=
                       item['basis_dimension']
                    or len(result['multiplier_at_stations_n_per_m']) !=
                       len(STATIONS)
                    or 'support_balance' not in result
                    or 'four_point_gap_field_m' not in result
                    or 'scaled_solution_parity' not in result):
                raise ValueError('K2P physical result incomplete')
        if name not in LOADS:
            raise ValueError('unknown K2P load')
    statuses=[result['status'] for result in item['loads'].values()]
    expected=(
        'TWO_LOAD_INVENTORY_WITH_FAILURES_NOT_F03_ACCEPTANCE'
        if any(s not in ('LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE',
                         'LOCAL_DIAGNOSTIC_WITH_PARITY_OPEN') for s in statuses)
        else 'TWO_LOAD_INVENTORY_WITH_PARITY_OPEN'
        if 'LOCAL_DIAGNOSTIC_WITH_PARITY_OPEN' in statuses
        else 'TWO_LOAD_LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE')
    if status != expected:
        raise ValueError('K2P parent status contradicts loads')


def supervise(registration_path: Path,evidence: Path):
    registration_path=registration_path.resolve(strict=True)
    evidence=evidence.resolve()
    registration=json.loads(registration_path.read_text(encoding='utf-8'))
    observed=identity()
    verify(registration,observed,evidence)
    paths={name:evidence.with_name(evidence.name+f'.{name}')
           for name in ('stdout.log','stderr.log','attestation.json')}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError('K2P registration already consumed')
    started=time.monotonic()
    peak=0
    violation=None
    supervisor_error=None
    child=None
    with paths['stdout.log'].open('x',encoding='utf-8') as stdout, \
            paths['stderr.log'].open('x',encoding='utf-8') as stderr:
        try:
            child=subprocess.Popen((sys.executable,str(ROOT/
                                   'scripts/run_b3_ge_e4_pl_g0_f03_k2p.py'),
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
    rows=[]
    candidate_counts={}
    load_counts={}
    read_error=None
    try:
        if not raw.exists():
            raise ValueError('K2P raw evidence missing')
        with raw.open(encoding='utf-8') as source:
            rows=[json.loads(line) for line in source]
        if len(rows) != len(MESHES)+2:
            raise ValueError('K2P exact record count mismatch')
        first=rows[0]
        if (first.get('type') != 'start'
                or first.get('registration_sha256') != sha256(registration_path)
                or first.get('registration') != registration
                or first.get('identity') != observed):
            raise ValueError('K2P start identity mismatch')
        for index,case in enumerate(MESHES,1):
            item=rows[index]
            data=item['data']
            if (item.get('type') != 'mesh' or item.get('index') != index
                    or (data['topology'],data['n_beam'],data['n_shell']) != case
                    or [c['space'] for c in data['cases']] != list(NAMES)):
                raise ValueError('K2P ordered mesh/candidate inventory mismatch')
            for candidate in data['cases']:
                check_candidate(candidate)
                status=candidate['status']
                candidate_counts[status]=candidate_counts.get(status,0)+1
                for result in candidate['loads'].values():
                    status=result['status']
                    load_counts[status]=load_counts.get(status,0)+1
        terminal=rows[-1]
        if (terminal.get('type') != 'terminal'
                or terminal.get('status') !=
                   'FIXED_LOAD_DIAGNOSTIC_COMPLETE_NOT_F03_ACCEPTANCE'
                or terminal.get('completed_meshes') != len(MESHES)
                or terminal.get('candidate_status_counts') != candidate_counts
                or terminal.get('load_status_counts') != load_counts
                or terminal.get('observed_load_cases') != sum(load_counts.values())
                or sum(candidate_counts.values()) != len(MESHES)*len(NAMES)):
            raise ValueError('K2P terminal counts/statuses inconsistent')
    except (ValueError,TypeError,KeyError,UnicodeError) as exc:
        read_error=str(exc)
    success=(exit_code == 0 and violation is None and supervisor_error is None
             and read_error is None)
    attestation={
        'status':('COMPLETE_FIXED_LOAD_DIAGNOSTIC_NOT_F03_ACCEPTANCE'
                  if success else 'ABORTED_OR_INCOMPLETE_NOT_QUALIFIED'),
        'exit_code':exit_code,'violation':violation,
        'supervisor_error':supervisor_error,'read_error':read_error,
        'observed_meshes':max(0,len(rows)-2),
        'candidate_status_counts':candidate_counts,
        'load_status_counts':load_counts,
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
