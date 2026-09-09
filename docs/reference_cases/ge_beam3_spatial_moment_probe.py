"""Bounded frozen development test lane for native force/couple loading."""
import argparse
from hashlib import sha256
import os
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET

from docs.reference_cases.ge_beam3_fibre_arch_probe import guard as source_guard, _ProcessJob, THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical


ROOT = Path(__file__).resolve().parents[2]
TESTS = ('tests/test_ge_beam3_spatial_nodal_moments.py', 'tests/test_ge_beam3_fibre_dense_admission.py')
ARTIFACTS = (
    'coupled-plastic-moments0/status.json', 'coupled-plastic-moments0/whole.json',
    'test_all_six_load_components_p0/paused.json',
    'test_biaxial_bending_moment_an0/bending-rotated.json', 'test_biaxial_bending_moment_an0/bending.json',
    'test_pure_torsion_large_rotati0/torsion.json',
)


def guard(revision):
    from importlib.metadata import version
    source_guard(revision)
    if version('pytest') != '9.0.3': raise ValueError('frozen pytest version required')


def summarize(output, revision):
    report = output/'unit.xml'
    if not 0 < report.stat().st_size <= 1 << 20: raise ValueError('bounded complete test report')
    suites = ET.fromstring(report.read_bytes()).iter('testsuite')
    counts = {k:0 for k in ('tests','failures','errors','skipped')}
    for suite in suites:
        for k in counts: counts[k] += int(suite.attrib.get(k, '0'))
    if counts != dict(tests=34,failures=0,errors=0,skipped=0): raise ValueError('complete passing frozen moment lane required')
    artifacts = []
    for path in sorted((output/'pytest').rglob('*.json')):
        if not 0 < path.stat().st_size <= 2*(1 << 20): raise ValueError('bounded complete state artifact')
        raw = path.read_bytes()
        artifacts.append(dict(path=path.relative_to(output/'pytest').as_posix(), bytes=len(raw), sha256=sha256(raw).hexdigest()))
    if tuple(a['path'] for a in artifacts) != ARTIFACTS:
        raise ValueError('exact complete moment state/restart artifact inventory required')
    return dict(schema='GE_BEAM3_SPATIAL_NODAL_MOMENT_DEVELOPMENT_CYCLE_V1', revision=revision,
        status='DEVELOPMENT_STATIC_LOAD_PARITY_NOT_QUALIFICATION', tests=counts, artifacts=artifacts,
        conservative_spectral_authority=False, independent_review='PENDING', production_qualified=False,
        runtime_version_check_only=True)


def run(revision, output):
    guard(revision)
    if os.name != 'nt' or not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github').resolve()):
        raise ValueError('Windows containment and fresh external output required')
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ); env.update(THREAD_ENVIRONMENT)
    env.pop('PYTHONPATH', None); env['PYTHONHASHSEED']='0'; env['PYTHONDONTWRITEBYTECODE']='1'
    command = [sys.executable,'-B','-m','pytest',*TESTS,'-q','-p','no:cacheprovider',
               '--basetemp',str(output/'pytest'),'--junitxml',str(output/'unit.xml')]
    job = _ProcessJob(24*(1 << 30)); start=time.monotonic(); activity=start; last=(0,0)
    try:
        with (output/'stdout.log').open('xb') as stdout, (output/'stderr.log').open('xb') as stderr:
            process=job.launch(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            while True:
                cpu,active,memory=job.accounting(); code=process.poll(); now=time.monotonic()
                current=(cpu,(output/'stdout.log').stat().st_size)
                if current!=last: activity=now; last=current
                if now-start>=600 or now-activity>=120 or memory>=24*(1 << 30):
                    raise RuntimeError('moment lane wall/inactivity/memory bound')
                if code is not None and active==0: break
                time.sleep(.2)
            if code!=0: raise RuntimeError(f'moment lane failed: exit {code}; no automatic retry')
        guard(revision)
        raw=canonical(summarize(output,revision))
    finally:
        try:
            if not job.terminate(): raise RuntimeError('complete moment lane tree termination not proven')
        finally: job.close()
    guard(revision)
    if canonical(summarize(output,revision))!=raw: raise ValueError('moment evidence changed after cleanup')
    pending=output/'cycle.pending.json'
    with pending.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    if pending.read_bytes()!=raw: raise ValueError('staged moment cycle differs')
    os.link(pending,output/'cycle.json')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',required=True); parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(); run(args.revision,args.output)


if __name__=='__main__': main()
