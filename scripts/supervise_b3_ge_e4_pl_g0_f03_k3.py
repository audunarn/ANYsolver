"""External resource and immutable inventory attestation for F03-K3."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import psutil

from probe_b3_ge_e4_pl_g0_f03_k3 import LOADS, MESHES, NAMES, STATIONS
from run_b3_ge_e4_pl_g0_f03_k3 import PROTOCOL, ROOT, identity, sha256, verify


PREEMPTED={'ROW_RANK_LOSS_NOT_F03_ACCEPTANCE',
           'INVALID_QUADRATURE_REFERENCE','MASS_INVALID',
           'MASS_OR_RANK_INVALID','INVALID_LOAD_QUADRATURE'}
COMPLETED={'TWO_LOAD_INVENTORY_WITH_FAILURES_NOT_F03_ACCEPTANCE',
           'TWO_LOAD_INVENTORY_WITH_PARITY_OPEN',
           'TWO_LOAD_LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE'}
LOAD_STATUSES={'NONFINITE_CANDIDATE_RESPONSE',
               'NUMERICAL_CANDIDATE_FAILURE',
               'NUMERICAL_OR_PHYSICAL_LOCAL_FAILURE',
               'LOCAL_DIAGNOSTIC_WITH_PARITY_OPEN',
               'LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE'}


def expected_knots(n_beam,n_shell):
    beam=np.linspace(0.,1.,n_beam+1)
    panel=-.5+np.arange(2*n_shell+1,dtype=float)/n_shell
    shell=np.r_[0.,panel[(panel>0.)&(panel<1.)],1.]
    return {'p0-beam':beam,'p0-shell-grid':shell}


def check_candidate(item,knots_expected):
    if item['space'] not in NAMES or item['basis_dimension'] < 1:
        raise ValueError('K3 basis invalid')
    knots=np.asarray(item['basis_knots'],dtype=float)
    if (len(knots) != item['basis_dimension']+1
            or not np.all(np.isfinite(knots))
            or knots[0] != 0. or knots[-1] != 1.
            or not np.all(np.diff(knots)>0)
            or not np.array_equal(knots,knots_expected[item['space']])):
        raise ValueError('K3 P0 knot grammar invalid')
    status=item['status']
    if status in PREEMPTED:
        if item['loads']:
            raise ValueError('K3 preempted candidate has loads')
        if (status=='ROW_RANK_LOSS_NOT_F03_ACCEPTANCE'
                and item['rank_context']['row_rank'] >=
                    item['rank_context']['rows']):
            raise ValueError('K3 row-rank status contradicted')
        if (status in ('INVALID_QUADRATURE_REFERENCE','MASS_OR_RANK_INVALID')
                and (not item.get('failure_type') or not item.get('failure'))):
            raise ValueError('K3 typed preemption missing failure')
        return
    if status not in COMPLETED or set(item['loads']) != set(LOADS):
        raise ValueError('K3 candidate/load grammar invalid')
    for load in item['loads'].values():
        if load.get('status') not in LOAD_STATUSES:
            raise ValueError('K3 load disposition unknown')
        if load['status']=='NUMERICAL_CANDIDATE_FAILURE' and (
                not load.get('failure_type') or not load.get('failure')):
            raise ValueError('K3 numerical failure missing provenance')
        if load['status']=='NONFINITE_CANDIDATE_RESPONSE' and (
                load.get('failure_type') not in ('NonfiniteKKTResult',
                                                 'NonfiniteRecoveryResult')):
            raise ValueError('K3 nonfinite failure missing provenance')
        if 'multiplier_coefficients_n_per_m' in load:
            values=load['multiplier_one_sided_at_stations_n_per_m']
            coeffs=np.asarray(load['multiplier_coefficients_n_per_m'])
            if (coeffs.shape != (item['basis_dimension'],3)
                    or len(values) != len(STATIONS)):
                raise ValueError('K3 P0 traction record incomplete')
            for entry,s in zip(values,STATIONS):
                if (entry['s'] != s or len(entry['left']) != 3
                        or len(entry['right']) != 3
                        or not np.all(np.isfinite(entry['left']))
                        or not np.all(np.isfinite(entry['right']))):
                    raise ValueError('K3 one-sided traction invalid')
                cell_l=int(np.clip(np.searchsorted(knots,s,side='left')-1,
                                   0,item['basis_dimension']-1))
                cell_r=int(np.clip(np.searchsorted(knots,s,side='right')-1,
                                   0,item['basis_dimension']-1))
                if (not np.allclose(entry['left'],coeffs[cell_l],rtol=1e-12,atol=0.)
                        or not np.allclose(entry['right'],coeffs[cell_r],
                                            rtol=1e-12,atol=0.)):
                    raise ValueError('K3 one-sided traction/basis mismatch')
        if load['status'].startswith('LOCAL_DIAGNOSTIC'):
            if (len(load['stations']) != len(STATIONS)
                    or [x['s'] for x in load['stations']] != list(STATIONS)
                    or 'support_balance' not in load
                    or 'four_point_gap_field_m' not in load
                    or 'scaled_solution_parity' not in load):
                raise ValueError('K3 physical response incomplete')
            parity=load['scaled_solution_parity']
            if ((load['status']=='LOCAL_DIAGNOSTIC_WITH_PARITY_OPEN')
                    != (parity>1e-10)):
                raise ValueError('K3 forward parity disposition mismatch')
    statuses=[load['status'] for load in item['loads'].values()]
    expected=(
        'TWO_LOAD_INVENTORY_WITH_FAILURES_NOT_F03_ACCEPTANCE'
        if any(s not in ('LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE',
                         'LOCAL_DIAGNOSTIC_WITH_PARITY_OPEN') for s in statuses)
        else 'TWO_LOAD_INVENTORY_WITH_PARITY_OPEN'
        if 'LOCAL_DIAGNOSTIC_WITH_PARITY_OPEN' in statuses
        else 'TWO_LOAD_LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE')
    if status != expected:
        raise ValueError('K3 parent status contradicts loads')


def check_coarse_side(data):
    beam,shell=data['cases']
    if shell['basis_dimension'] < beam['basis_dimension']:
        expected=shell['space']
    elif (shell['basis_dimension'] == beam['basis_dimension']
          and shell['basis_knots'] != beam['basis_knots']):
        expected='UNRESOLVED_EQUAL_DIMENSION_NONMATCHING'
    else:
        expected=beam['space']
    if data['coarse_side_hypothesis'] != expected:
        raise ValueError('K3 coarse-side mapping mismatch')


def supervise(registration_path: Path,evidence: Path):
    registration_path=registration_path.resolve(strict=True)
    evidence=evidence.resolve()
    registration=json.loads(registration_path.read_text(encoding='utf-8'))
    observed=identity()
    verify(registration,observed,evidence)
    paths={name:evidence.with_name(evidence.name+'.'+name)
           for name in ('stdout.log','stderr.log','attestation.json')}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError('K3 registration already consumed')
    started=time.monotonic()
    peak=0
    violation=None
    supervisor_error=None
    child=None
    with paths['stdout.log'].open('x',encoding='utf-8') as stdout, \
            paths['stderr.log'].open('x',encoding='utf-8') as stderr:
        try:
            child=subprocess.Popen((sys.executable,str(ROOT/
                                   'scripts/run_b3_ge_e4_pl_g0_f03_k3.py'),
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
            raise ValueError('K3 raw evidence missing')
        with raw.open(encoding='utf-8') as source:
            rows=[json.loads(line) for line in source]
        if len(rows) != len(MESHES)+2:
            raise ValueError('K3 exact record count mismatch')
        first=rows[0]
        if (first.get('type') != 'start'
                or first.get('registration_sha256') != sha256(registration_path)
                or first.get('registration') != registration
                or first.get('identity') != observed):
            raise ValueError('K3 start identity mismatch')
        for index,case in enumerate(MESHES,1):
            row=rows[index]
            data=row['data']
            if (row.get('type') != 'mesh' or row.get('index') != index
                    or (data['topology'],data['n_beam'],data['n_shell']) != case
                    or [c['space'] for c in data['cases']] != list(NAMES)):
                raise ValueError('K3 ordered inventory mismatch')
            check_coarse_side(data)
            knots_expected=expected_knots(data['n_beam'],data['n_shell'])
            for item in data['cases']:
                check_candidate(item,knots_expected)
                status=item['status']
                candidate_counts[status]=candidate_counts.get(status,0)+1
                for load in item['loads'].values():
                    status=load['status']
                    load_counts[status]=load_counts.get(status,0)+1
        terminal=rows[-1]
        if (terminal.get('type') != 'terminal'
                or terminal.get('status') != PROTOCOL['status']
                or terminal.get('completed_meshes') != len(MESHES)
                or terminal.get('candidate_status_counts') != candidate_counts
                or terminal.get('load_status_counts') != load_counts
                or terminal.get('observed_load_cases') != sum(load_counts.values())
                or sum(candidate_counts.values()) != len(MESHES)*len(NAMES)):
            raise ValueError('K3 terminal counts/status mismatch')
    except (ValueError,TypeError,KeyError,UnicodeError) as exc:
        read_error=str(exc)
    success=(exit_code == 0 and violation is None and supervisor_error is None
             and read_error is None)
    attestation={
        'status':('COMPLETE_P0_FIXED_LOAD_DIAGNOSTIC_NOT_F03_ACCEPTANCE'
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
    with paths['attestation.json'].open('x',encoding='utf-8') as output:
        json.dump(attestation,output,indent=2,sort_keys=True,allow_nan=False)
        output.flush();os.fsync(output.fileno())
    return 0 if success else 2


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(supervise(args.registration,args.evidence))
