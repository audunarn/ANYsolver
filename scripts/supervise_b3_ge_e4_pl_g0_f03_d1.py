"""Single-use external process and evidence attestation for F03-D1."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

from run_b3_ge_e4_pl_g0_f03_d1 import (
    DERIVATIVE_MESHES, PARITY_CASES, ROOT, STATIONS, STEPS, identity, sha256,
    verify,
)


DERIVATIVE_FIELDS = (
    'physical_perturbation_m','finite_planar_derivative',
    'absolute_scaled_derivative_error','normalized_derivative_error',
    'finite_work_density','analytic_work_density','normalized_work_error',
    'out_of_plane_translation_derivative_m',
    'out_of_plane_rotation_derivative_rad',
)


def derivative_inventory_ok(data):
    if [station['station'] for station in data['stations']] != list(STATIONS):
        return False
    for station in data['stations']:
        directions=station['directions']
        if [item['direction'] for item in directions] != ['combined','beam_only']:
            return False
        for item in directions:
            rows=item['results']
            if [row['h'] for row in rows] != list(STEPS):
                return False
            if any(not all(field in row for field in DERIVATIVE_FIELDS)
                   for row in rows):
                return False
    return True


def supervise(registration_path: Path, evidence: Path):
    registration_path=registration_path.resolve(strict=True)
    evidence=evidence.resolve()
    registration=json.loads(registration_path.read_text(encoding='utf-8'))
    observed=identity()
    verify(registration,observed,evidence)
    log_paths={name:evidence.with_name(evidence.name+f'.{name}')
               for name in ('stdout.log','stderr.log','attestation.json')}
    if any(path.exists() for path in log_paths.values()):
        raise FileExistsError('D1 registration already consumed')
    started=time.monotonic()
    peak=0
    violation=None
    supervisor_error=None
    child=None
    with log_paths['stdout.log'].open('x',encoding='utf-8') as stdout, \
            log_paths['stderr.log'].open('x',encoding='utf-8') as stderr:
        try:
            child=subprocess.Popen((sys.executable,str(ROOT/
                                   'scripts/run_b3_ge_e4_pl_g0_f03_d1.py'),
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
    records=[]
    read_error=None
    if raw.exists():
        try:
            with raw.open(encoding='utf-8') as source:
                records=[json.loads(line) for line in source]
            if len(records) != 12:
                raise ValueError('D1 must have 12 exact records')
            if (records[0].get('type') != 'start'
                    or records[0].get('registration') != registration
                    or records[0].get('identity') != observed
                    or records[0].get('registration_sha256') != sha256(registration_path)):
                raise ValueError('start identity mismatch')
            for index,case in enumerate(DERIVATIVE_MESHES,1):
                item=records[index]
                data=item['data']
                if (item.get('type') != 'derivative' or item.get('index') != index
                        or (data['topology'],data['n_beam'],data['n_shell']) != case
                        or not derivative_inventory_ok(data)):
                    raise ValueError('derivative inventory incomplete')
            for index,case in enumerate(PARITY_CASES,5):
                item=records[index]
                data=item['data']
                if (item.get('type') != 'parity' or item.get('index') != index
                        or (data['topology'],data['n_beam'],data['n_shell'],
                            data['load']) != case
                        or data.get('space') != 'p1-shell'
                        or not all(key in data for key in (
                            'v2_sparse_condensed_parity','sparse_dense_parity',
                            'sparse_condensed_parity','dense_condensed_parity',
                            'scaled_kkt_singular_ratio','scaled_krr_condition',
                            'physical_count','retained_count','multiplier_count'))
                        or set(data['work_scaled_backward']) != {
                            'sparse','dense','condensed'}):
                    raise ValueError('parity inventory incomplete')
            if (records[-1].get('type') != 'terminal'
                    or records[-1].get('status') !=
                       'DIAGNOSTIC_COMPLETE_NOT_F03_ACCEPTANCE'
                    or records[-1].get('records') != 10):
                raise ValueError('terminal inventory mismatch')
        except (ValueError,TypeError,KeyError,UnicodeError) as exc:
            read_error=str(exc)
    else:
        read_error='raw evidence missing'
    success=(exit_code == 0 and violation is None and supervisor_error is None
             and read_error is None)
    attestation={
        'status':('DIAGNOSTIC_COMPLETE_NOT_F03_ACCEPTANCE' if success else
                  'ABORTED_OR_INCOMPLETE_NOT_QUALIFIED'),
        'exit_code':exit_code,'violation':violation,'supervisor_error':supervisor_error,
        'read_error':read_error,'observed_records':len(records),
        'elapsed_seconds':time.monotonic()-started,
        'sampled_peak_rss_bytes':peak,
        'registration_sha256':sha256(registration_path),
        'raw_sha256':sha256(raw) if raw.exists() else None,
        'stdout_sha256':sha256(log_paths['stdout.log']),
        'stderr_sha256':sha256(log_paths['stderr.log']),
        'identity':observed}
    with log_paths['attestation.json'].open('x',encoding='utf-8') as output:
        json.dump(attestation,output,indent=2,sort_keys=True,allow_nan=False)
        output.flush();os.fsync(output.fileno())
    return 0 if success else 2


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(supervise(args.registration,args.evidence))
