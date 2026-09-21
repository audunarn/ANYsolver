"""External resource and inventory attestation for the K2L diagnostic."""

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

from probe_b3_ge_e4_pl_g0_f03_k2l import MESHES, NAMES, RELATIVE_CUTOFF
from run_b3_ge_e4_pl_g0_f03_k2l import ROOT, PROTOCOL, identity, sha256, verify


STATUSES={'INVALID_QUADRATURE_REFERENCE','NONFINITE_ASSEMBLY',
          'NONFINITE_REFERENCE_OR_QUADRATURE','NONFINITE_MASS_METRIC',
          'NONPOSITIVE_MULTIPLIER_MASS','NONFINITE_OR_ZERO_TRACE',
          'NONFINITE_RANK_DECOMPOSITION',
          'REFERENCE_OR_QUADRATURE_INVALID','MASS_ASYMMETRIC',
          'MASS_EIGEN_FAILURE','MASS_ILL_CONDITIONED',
          'INVALID_COORDINATE_SCALE','MASS_FACTOR_FAILURE',
          'NONFINITE_WHITENED_MAP','TRACE_SVD_FAILURE',
          'NATIVE_SVD_FAILURE','PROJECTED_SVD_FAILURE',
          'RANK_DECOMPOSITION_CONSISTENT_NOT_F03_ACCEPTANCE',
          'RANK_DECOMPOSITION_AMBIGUOUS_NOT_F03_ACCEPTANCE'}


def check_candidate(item):
    if (item['space'] not in NAMES or item['basis_dimension'] < 1
            or item['status'] not in STATUSES):
        raise ValueError('K2L candidate grammar invalid')
    knots=np.asarray(item['basis_knots'],dtype=float)
    expected_knots=item['basis_dimension']+(
        1 if item['space'].startswith('p0-') else 0)
    if (len(knots) != expected_knots or not np.all(np.isfinite(knots))
            or knots[0] != 0. or knots[-1] != 1.
            or not np.all(np.diff(knots)>0)):
        raise ValueError('K2L basis geometry invalid')
    for field in ('mass_relative_skew','mass_min_eigen',
                  'mass_max_eigen','mass_eigen_ratio'):
        if field in item and not np.isfinite(item[field]):
            raise ValueError('K2L mass metric nonfinite')
    for field in ('reference_consistency','quadrature_error'):
        if field in item and not np.all(np.isfinite(
                np.asarray(list(item[field].values()),dtype=float))):
            raise ValueError('K2L geometry/quadrature metric nonfinite')
    if not item['status'].startswith('RANK_DECOMPOSITION_'):
        if any(key in item for key in ('full_rank','native_rank',
                                       'shell_restrictions')):
            raise ValueError('invalid candidate contains completed rank data')
        return
    rows=item['constraint_rows']
    shell=item['shell_free_coordinates']
    native=item['beam_physical_coordinates']+item['beam_retained_coordinates']
    if (rows != 3*item['basis_dimension'] or shell < 1 or native < 1
            or item['relative_cutoff'] != RELATIVE_CUTOFF
            or len(item['projected_shell_map']) != rows-item['native_rank']
            or any(len(row) != shell for row in item['projected_shell_map'])
            or item['shell_restrictions'] != item['full_rank']-item['native_rank']
            or len(item['full_singular']) != min(rows,shell+native)
            or len(item['native_singular']) != min(rows,native)
            or len(item['beam_physical_singular']) != min(
                rows,item['beam_physical_coordinates'])
            or len(item['projected_shell_singular']) != min(
                rows-item['native_rank'],shell)):
        raise ValueError('K2L rank dimensions/inventory inconsistent')
    if not np.all(np.isfinite(np.asarray(item['projected_shell_map'],dtype=float))):
        raise ValueError('K2L projected map nonfinite')
    for key in ('full_singular','native_singular','beam_physical_singular',
                'projected_shell_singular'):
        values=np.asarray(item[key],dtype=float)
        if (not np.all(np.isfinite(values)) or np.any(values < 0)
                or np.any(np.diff(values) > 0)):
            raise ValueError('K2L singular spectrum invalid')
    cutoff=item['absolute_cutoff']
    full_top=item['full_singular'][0]
    if (not np.isfinite(cutoff) or cutoff <= 0 or full_top <= 0
            or not np.isclose(cutoff,RELATIVE_CUTOFF*full_top,
                              rtol=1e-12,atol=0.)
            or not (0<=item['native_rank']<=item['full_rank']<=rows)
            or not (0<=item['projected_shell_rank']<=rows-item['native_rank'])
            or item['full_rank'] != sum(x>cutoff for x in item['full_singular'])
            or item['native_rank'] != sum(x>cutoff for x in item['native_singular'])
            or item['beam_physical_rank'] != sum(
                x>cutoff for x in item['beam_physical_singular'])
            or item['projected_shell_rank'] != sum(
                x>cutoff for x in item['projected_shell_singular'])):
        raise ValueError('K2L rank cutoff mismatch')
    near=any(np.any((np.asarray(item[key])>=.1*cutoff)&
                    (np.asarray(item[key])<=10.*cutoff))
             for key in ('full_singular','native_singular',
                         'beam_physical_singular','projected_shell_singular'))
    if item['near_cutoff'] != bool(near):
        raise ValueError('K2L cutoff uncertainty mismatch')
    metrics=(item['left_null_native_residual'],
             item['discarded_native_to_cutoff'],
             item['shell_reconstruction_residual'],
             item['projector_orthogonality_residual'])
    if not np.all(np.isfinite(metrics)) or any(value < 0 for value in metrics):
        raise ValueError('K2L decomposition metrics nonfinite/negative')
    if (item['status']=='RANK_DECOMPOSITION_CONSISTENT_NOT_F03_ACCEPTANCE') != (
            item['projected_shell_rank']==item['shell_restrictions']
            and item['discarded_native_to_cutoff'] <= .1
            and item['left_null_native_residual'] <= 1e-10
            and item['shell_reconstruction_residual'] <= 1e-10
            and item['projector_orthogonality_residual'] <= 1e-10
            and not near):
        raise ValueError('K2L rank disposition mismatch')


def supervise(registration_path: Path,evidence: Path):
    registration_path=registration_path.resolve(strict=True)
    evidence=evidence.resolve()
    registration=json.loads(registration_path.read_text(encoding='utf-8'))
    observed=identity()
    verify(registration,observed,evidence)
    paths={name:evidence.with_name(evidence.name+'.'+name)
           for name in ('stdout.log','stderr.log','attestation.json')}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError('K2L registration already consumed')
    started=time.monotonic()
    peak=0
    violation=None
    supervisor_error=None
    child=None
    with paths['stdout.log'].open('x',encoding='utf-8') as stdout, \
            paths['stderr.log'].open('x',encoding='utf-8') as stderr:
        try:
            child=subprocess.Popen((sys.executable,str(ROOT/
                                   'scripts/run_b3_ge_e4_pl_g0_f03_k2l.py'),
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
    status_counts={}
    read_error=None
    try:
        if not raw.exists():
            raise ValueError('K2L raw evidence missing')
        with raw.open(encoding='utf-8') as source:
            rows=[json.loads(line) for line in source]
        if len(rows) != len(MESHES)+2:
            raise ValueError('K2L exact record count mismatch')
        first=rows[0]
        if (first.get('type') != 'start'
                or first.get('registration_sha256') != sha256(registration_path)
                or first.get('registration') != registration
                or first.get('identity') != observed):
            raise ValueError('K2L start identity mismatch')
        for index,case in enumerate(MESHES,1):
            row=rows[index]
            data=row['data']
            if (row.get('type') != 'mesh' or row.get('index') != index
                    or (data['topology'],data['n_beam'],data['n_shell']) != case
                    or [c['space'] for c in data['cases']] != list(NAMES)):
                raise ValueError('K2L mesh/candidate inventory mismatch')
            for candidate in data['cases']:
                check_candidate(candidate)
                status=candidate['status']
                status_counts[status]=status_counts.get(status,0)+1
        terminal=rows[-1]
        if (terminal.get('type') != 'terminal'
                or terminal.get('status') != PROTOCOL['status']
                or terminal.get('completed_meshes') != len(MESHES)
                or terminal.get('status_counts') != status_counts
                or sum(status_counts.values()) != len(MESHES)*len(NAMES)):
            raise ValueError('K2L terminal inventory/status inconsistent')
    except (ValueError,TypeError,KeyError,UnicodeError) as exc:
        read_error=str(exc)
    success=(exit_code == 0 and violation is None and supervisor_error is None
             and read_error is None)
    attestation={
        'status':('COMPLETE_NATIVE_IMAGE_DIAGNOSTIC_NOT_F03_ACCEPTANCE'
                  if success else 'ABORTED_OR_INCOMPLETE_NOT_QUALIFIED'),
        'exit_code':exit_code,'violation':violation,
        'supervisor_error':supervisor_error,'read_error':read_error,
        'observed_meshes':max(0,len(rows)-2),
        'status_counts':status_counts,
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
