"""One resource-approved development probe; never a qualification campaign.

The external resource administrator must approve/acquire this exact command.
This module supplies process containment, not resource approval. It imports
only the pre-existing generic Windows Job implementation from the S3 runner;
no S3 mechanics or scientific protocol is used or changed.
"""
import argparse
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
import subprocess
import sys
import time

from docs.reference_cases.e4_pl_s3_v2_bounded_process import _ProcessJob, THREAD_ENVIRONMENT


ROOT = Path(__file__).resolve().parents[2]
PYTHON_SHA256 = 'fda7026477256845afab371e354c4d512896665f1761939cb5887d0a9dec257a'
RUNTIME = {'numpy': '2.4.6', 'scipy': '1.17.1', 'ANYfileio': '0.3.1',
           'ANYmesher': '0.4.0', 'ANYgeometry': '0.4.2', 'ANYmaterial': '0.2.0'}


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii')


def guard(revision):
    from importlib import metadata
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('exact frozen commit required')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=10).decode().strip()
    if git('rev-parse', 'HEAD') != revision or git('status', '--porcelain', '--untracked-files=all'):
        raise ValueError('frozen clean source required')
    if sha256(Path(sys.executable).read_bytes()).hexdigest() != PYTHON_SHA256:
        raise ValueError('frozen Python executable required')
    if {name: metadata.version(name) for name in RUNTIME} != RUNTIME:
        raise ValueError('development runtime version mismatch')


def validate_ready(value, revision):
    if (not isinstance(value, dict) or set(value) != {'schema', 'revision', 'macros', 'checkpoint_sha256',
            'rows', 'production_qualified', 'independent_review', 'runtime_version_check_only'}
            or value['schema'] != 'GE_BEAM3_FOUR_MACRO_ARCH_DEVELOPMENT_V1'
            or value['revision'] != revision or type(value['macros']) is not int or value['macros'] != 4
            or value['production_qualified'] is not False or value['independent_review'] != 'PENDING'
            or value['runtime_version_check_only'] is not True):
        raise ValueError('development ready schema')
    if (not isinstance(value['rows'], list) or len(value['rows']) != 4
            or type(value['checkpoint_sha256']) is not str or len(value['checkpoint_sha256']) != 64
            or any(c not in '0123456789abcdef' for c in value['checkpoint_sha256'])):
        raise ValueError('complete target/checkpoint coverage')
    numeric = {'displacement', 'native_load', 'reference_load', 'load_relative_error',
               'nodal_position_error', 'nodal_frame_error', 'stiffness_scale',
               'reference_energy', 'reference_load_slope'}
    flags = {'same_equilibrium_branch_proved', 'mechanics_replayed', 'production_qualified'}
    geometry_keys = {'position_reflection_error', 'out_of_plane_position', 'nodal_frame_reflection_error',
                     'cell_rotation_reflection_error', 'physical_second_director_error'}
    for target, row in zip((.01, .025, .04, .055), value['rows']):
        if (not isinstance(row, dict) or set(row) != numeric | flags | {'geometry',
                'reference_profile', 'reference_errors_normalized'}
                or any(type(row[k]) is not float or not isfinite(row[k]) for k in numeric)
                or row['displacement'] != target or row['stiffness_scale'] != 1.e6
                or row['reference_profile'] != 'BVP9' or row['mechanics_replayed'] is not True
                or any(row[k] is not False for k in flags-{'mechanics_replayed'})):
            raise ValueError('complete comparison row')
        for key, keys in (('geometry', geometry_keys), ('reference_errors_normalized',
                          {'boundary', 'differential', 'sensitivity', 'work'})):
            data = row[key]
            if (not isinstance(data, dict) or set(data) != keys
                    or any(type(v) is not float or not isfinite(v) or v < 0 for v in data.values())):
                raise ValueError('finite diagnostic fields')
        if any(row[k] < 0 for k in ('load_relative_error', 'nodal_position_error',
                                    'nodal_frame_error', 'reference_energy')):
            raise ValueError('nonnegative error/energy')
    canonical(value)


def worker(revision, output):
    guard(revision)
    if any(os.environ.get(k) != v for k, v in THREAD_ENVIRONMENT.items()):
        raise ValueError('single numerical thread required')
    sys.path.insert(0, str(ROOT/'src'))
    from docs.reference_cases import ge_beam3_fibre_arch_refinement as family
    from docs.reference_cases import ge_beam3_fibre_arch_comparison as comparison
    from anysolver import _ge_beam3_seeded_fibre_control as control
    def progress(event):
        print(json.dumps(event, sort_keys=True, default=str), flush=True)
    progress({'stage': 'INITIALIZATION', 'macros': 4})
    made = family.model(4); program = family.program(4)
    result = control.solve_translation_program(made, program, progress=progress)
    with (output/'checkpoint-diagnostic.json').open('xb') as stream: stream.write(result.checkpoint)
    if result.status != 'completed': raise RuntimeError(f'{result.status}: {result.failure}')
    context = control.Context(made, program)
    context.restore(result.checkpoint, expected_sha256=sha256(result.checkpoint).hexdigest())
    data = json.loads(result.checkpoint); rows = []; previous = None
    for row in data['records']:
        if any(x != 0. for cell in row['histories'] for station in cell['stations']
               for fibre in station['rows'] for x in fibre):
            raise ValueError('plastic history cannot be compared with the elastic continuum reference')
        scale, ref = comparison.normalized_reference(row['displacement_target'], axial=1.e6,
            shear=4.e5, bending=100., previous=previous)
        previous = ref
        comparison_row = comparison.compare(row, [-1.+i/4 for i in range(9)], scale, ref)
        comparison_row['mechanics_replayed'] = True
        rows.append(comparison_row)
        progress({'stage': 'REFERENCE_COMPARISON', 'target': row['displacement_target']})
    value = dict(schema='GE_BEAM3_FOUR_MACRO_ARCH_DEVELOPMENT_V1', revision=revision, macros=4,
        checkpoint_sha256=sha256(result.checkpoint).hexdigest(), rows=rows,
        production_qualified=False, independent_review='PENDING', runtime_version_check_only=True)
    guard(revision); validate_ready(value, revision)
    with (output/'comparison.pending.json').open('xb') as stream: stream.write(canonical(value))
    progress({'stage': 'COMPLETION'})


def run(revision, output):
    if os.name != 'nt': raise ValueError('Windows Job process-tree containment required')
    guard(revision)
    if not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github').resolve()):
        raise ValueError('fresh absolute external output required')
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ); env.update(THREAD_ENVIRONMENT)
    env.pop('PYTHONPATH', None); env['PYTHONHASHSEED'] = '0'; env['PYTHONDONTWRITEBYTECODE'] = '1'
    command = [sys.executable, '-B', '-m', 'docs.reference_cases.ge_beam3_fibre_arch_probe',
               '--worker', '--revision', revision, '--output', str(output)]
    job = _ProcessJob(24*(1 << 30)); started = time.monotonic(); activity = started; last = (0, 0)
    try:
        with (output/'stdout.log').open('xb') as out, (output/'stderr.log').open('xb') as err:
            process = job.launch(command, cwd=ROOT, env=env, stdout=out, stderr=err)
            while True:
                cpu, active, memory = job.accounting(); code = process.poll(); now = time.monotonic()
                current = (cpu, (output/'stdout.log').stat().st_size)
                if current != last: activity = now; last = current
                if now-started >= 600 or now-activity >= 120 or memory >= 24*(1 << 30):
                    raise RuntimeError('bounded probe wall/inactivity/memory limit')
                if code is not None and active == 0: break
                time.sleep(.2)
            if code != 0: raise RuntimeError(f'probe failed with exit {code}; diagnostics preserved')
        guard(revision)
        pending = output/'comparison.pending.json'; raw = pending.read_bytes()
        value = json.loads(raw); validate_ready(value, revision)
        if canonical(value) != raw: raise ValueError('noncanonical worker comparison')
        if sha256((output/'checkpoint-diagnostic.json').read_bytes()).hexdigest() != value['checkpoint_sha256']:
            raise ValueError('checkpoint changed before publication')
        # Same-volume exclusive hard-link promotion only after full tree exit.
        os.link(pending, output/'comparison.json')
    finally:
        try:
            if not job.terminate(): raise RuntimeError('complete tree termination not proven')
        finally:
            job.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    (worker if args.worker else run)(args.revision, args.output)


if __name__ == '__main__': main()
