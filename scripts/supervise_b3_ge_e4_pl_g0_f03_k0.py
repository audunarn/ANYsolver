"""One-shot process/exit attestation for the registered F03-K0 screen."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

from run_b3_ge_e4_pl_g0_f03_k0 import (
    ROOT, actual_identity, sha256, verify_registration)


SUCCESS_TERMINALS = {
    'PLANAR_SCREEN_HAS_LOCAL_PASSES_NOT_F03_ACCEPTANCE',
    'PLANAR_SCREEN_NO_LOCAL_PASS_NOT_F03_ACCEPTANCE',
}
EXPECTED_MESHES = [(topology,n,int(n*ratio))
                   for topology in ('Q4','S3-V2D')
                   for ratio in (.5,1.,2.) for n in (4,8,16)]
EXPECTED_SPACES = ('p0-union','p1-shell','p1-beam','p1-union','dual-union')


def supervise(registration_path: Path, evidence: Path) -> int:
    registration_path = registration_path.resolve(strict=True)
    evidence = evidence.resolve()
    registration = json.loads(registration_path.read_text(encoding='utf-8'))
    identity = actual_identity()
    verify_registration(registration,identity,evidence)
    paths = {suffix:evidence.with_name(evidence.name+f'.{suffix}')
             for suffix in ('stdout.log','stderr.log','attestation.json')}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError('registered one-shot supervisor evidence already exists')
    start = time.monotonic()
    violation = None
    supervisor_error = None
    maximum_rss = 0
    # Exclusive log creation consumes this registration even if process setup,
    # execution or supervisor attestation later fails. Never overwrite logs.
    with paths['stdout.log'].open('x',encoding='utf-8') as stdout, \
            paths['stderr.log'].open('x',encoding='utf-8') as stderr:
        child = None
        try:
            child = subprocess.Popen(
                (sys.executable,str(ROOT/'scripts/run_b3_ge_e4_pl_g0_f03_k0.py'),
                 '--registration',str(registration_path),'--evidence',str(evidence)),
                cwd=ROOT,stdout=stdout,stderr=stderr)
            process = psutil.Process(child.pid)
            while child.poll() is None:
                elapsed = time.monotonic()-start
                try:
                    maximum_rss = max(maximum_rss,process.memory_info().rss)
                except psutil.NoSuchProcess:
                    pass
                if elapsed > registration['limits']['wall_seconds']:
                    violation = 'EXTERNAL_WALL_TIMEOUT'
                elif maximum_rss > registration['limits']['sampled_rss_limit_bytes']:
                    violation = 'SAMPLED_RSS_LIMIT'
                if violation:
                    child.kill()
                    break
                time.sleep(.1)
        except BaseException as exc:
            supervisor_error = f'{type(exc).__name__}: {exc}'
            if child is not None and child.poll() is None:
                child.kill()
        finally:
            exit_code = child.wait() if child is not None else None
            stdout.flush();os.fsync(stdout.fileno())
            stderr.flush();os.fsync(stderr.fileno())
    raw = evidence/'raw.jsonl'
    terminal = None
    observed_meshes = 0
    observed_statuses = {}
    observed_trends = None
    read_error = None
    if raw.exists():
        try:
            with raw.open(encoding='utf-8') as source:
                for index,line in enumerate(source):
                    entry = json.loads(line)
                    expected = ('start' if index == 0 else 'mesh'
                                if 1 <= index <= 18 else 'trends'
                                if index == 19 else 'terminal'
                                if index == 20 else None)
                    if entry.get('type') != expected:
                        raise ValueError('raw record order/type/length mismatch')
                    if expected == 'start':
                        if (entry.get('registration_sha256') != sha256(registration_path)
                                or entry.get('registration') != registration
                                or entry.get('identity') != identity):
                            raise ValueError('raw start identity/registration mismatch')
                    elif expected == 'mesh':
                        mesh = entry['data']
                        if (entry.get('index') != index
                                or len(mesh['cases']) != 5
                                or (mesh['shell']['topology'],
                                    mesh['beam_half_cells'],
                                    mesh['shell']['n_s']) != EXPECTED_MESHES[index-1]
                                or tuple(case['space'] for case in mesh['cases'])
                                   != EXPECTED_SPACES):
                            raise ValueError('mesh index or candidate count mismatch')
                        for case in mesh['cases']:
                            if set(case['loads']) != {'smooth','alternating'}:
                                raise ValueError('mesh load count mismatch')
                            for load in case['loads'].values():
                                status = load['status']
                                observed_statuses[status] = (
                                    observed_statuses.get(status,0)+1)
                        observed_meshes += 1
                    elif expected == 'trends':
                        observed_trends = entry['data']
                        if (len(observed_trends) != 30
                                or len({(item['topology'],item['ratio'],
                                         item['space']) for item in observed_trends}) != 30):
                            raise ValueError('trend inventory incomplete')
                    elif expected == 'terminal':
                        if terminal is not None:
                            raise ValueError('duplicate terminal records')
                        terminal = entry
            if (terminal is None or observed_meshes != 18
                    or sum(observed_statuses.values()) != 180
                    or terminal.get('status_counts') != observed_statuses
                    or terminal.get('status') != (
                        'PLANAR_SCREEN_HAS_LOCAL_PASSES_NOT_F03_ACCEPTANCE'
                        if observed_statuses.get(
                            'RESTRICTED_LOCAL_SCREEN_PASS_PENDING_TRENDS',0) > 0
                        else 'PLANAR_SCREEN_NO_LOCAL_PASS_NOT_F03_ACCEPTANCE')
                    or terminal.get('trend_dispositions') != {
                        name:sum(t['disposition'] == name for t in observed_trends)
                        for name in sorted({t['disposition'] for t in observed_trends})}):
                raise ValueError('terminal and raw inventory disagree')
        except (ValueError,UnicodeError,KeyError,TypeError) as exc:
            read_error = str(exc)
    success = (exit_code == 0 and violation is None and supervisor_error is None
               and read_error is None
               and observed_meshes == 18 and terminal is not None
               and terminal.get('status') in SUCCESS_TERMINALS
               and terminal.get('completed_meshes') == 18)
    attestation = {
        'status':('COMPLETE_PLANAR_SCREEN_NOT_F03_ACCEPTANCE' if success
                  else 'ABORTED_OR_INCOMPLETE_NOT_QUALIFIED'),
        'observed_process_exit_code':exit_code,
        'observed_meshes':observed_meshes,
        'terminal':terminal,
        'violation':violation,'read_error':read_error,
        'supervisor_error':supervisor_error,
        'elapsed_seconds':time.monotonic()-start,
        'sampled_peak_rss_bytes':maximum_rss,
        'registration_sha256':sha256(registration_path),
        'raw_sha256':sha256(raw) if raw.exists() else None,
        'stdout_sha256':sha256(paths['stdout.log']),
        'stderr_sha256':sha256(paths['stderr.log']),
        'identity':identity,
    }
    with paths['attestation.json'].open('x',encoding='utf-8') as output:
        json.dump(attestation,output,indent=2,sort_keys=True,allow_nan=False)
        output.flush();os.fsync(output.fileno())
    return 0 if success else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args = parser.parse_args()
    return supervise(args.registration,args.evidence)


if __name__ == '__main__':
    raise SystemExit(main())
