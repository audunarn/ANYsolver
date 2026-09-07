"""One bounded new field diagnostic using preserved six/twelve native states."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, _ProcessJob, THREAD_ENVIRONMENT
from docs.reference_cases import ge_beam3_preserved_arch_load_comparison as audit


ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease')
INPUTS = {
    6: (141754, '20a1a48cf6e2dfdc669c4f2d823deb89a9da8c6560ab716eb32e95b1b917a940'),
    12: (278640, 'ca95e88b6d354c3aeeb4bcebc1f49791cb3b1cef0781644f3be0e696e3a33683'),
}


def inputs():
    packets = {}
    reference = (ROOT/audit.REFERENCE_PATH).read_bytes().replace(b'\r\n', b'\n')
    if sha256(reference).hexdigest() != audit.REFERENCE_LF_SHA: raise ValueError('reference input changed')
    parsed = audit.parse(reference)
    for count, (size, digest) in INPUTS.items():
        path = EXTERNAL/f'ge-beam3-fibre-arch{count}-20260907-v1/checkpoint-diagnostic.json'
        if path.stat().st_size != size: raise ValueError('preserved checkpoint size')
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != digest: raise ValueError('preserved checkpoint identity')
        packets[count] = audit.parse(raw)
        audit.inspect_records(packets[count], parsed, macros=count)
    return packets, parsed


def parse_diagnostics(raw):
    if not 0 < len(raw) <= 8*(1 << 20): raise ValueError('bounded complete field diagnostics')
    value = json.loads(raw, object_pairs_hook=audit._pairs, parse_constant=audit._constant)
    if audit.canonical(value) != raw: raise ValueError('strict canonical field diagnostics')
    return value


def validate(raw, diagnostic_raw, revision, packets):
    value = audit.parse(raw); diagnostic = parse_diagnostics(diagnostic_raw)
    if (value['revision'] != revision or value['schema'] != 'GE_BEAM3_ARCH_GEOMETRY_RECOVERY_DEVELOPMENT_V1'
            or value['status'] != 'DEVELOPMENT_COMPARISON_NOT_QUALIFICATION'
            or value['diagnostics_sha256'] != sha256(diagnostic_raw).hexdigest()
            or value['checkpoint_sha256'] != {str(m): s for m, (_, s) in INPUTS.items()}
            or value['native_nonlinear_solves'] != 0 or value['new_reference_solves'] != 8
            or value['production_qualified'] is not False or value['same_equilibrium_branch_proved'] is not False
            or value['independent_review'] != 'PENDING'
            or value['nominal_section_comparison_not_exact_dyadic_certificate'] is not True):
        raise ValueError('development-only field result identity')
    order = [(t, m) for t in audit.TARGETS for m in (6, 12)]
    if ([(r['displacement'], r['macros']) for r in value['rows']] != order
            or [(r['target'], r['macros']) for r in diagnostic['recoveries']] != order
            or [(r['displacement'], r['profile']) for r in diagnostic['references']]
            != [(t, p) for t in audit.TARGETS for p in ('BVP7', 'BVP9')]):
        raise ValueError('complete ordered field/reference coverage')
    for index, (row, rec) in enumerate(zip(value['rows'], diagnostic['recoveries'])):
        m = row['macros']; origin = packets[m]['records'][index//2]
        if (sha256(audit.canonical(rec['fields'])).hexdigest() != origin['recovery_sha256']
                or rec['recovery_sha256'] != origin['recovery_sha256']
                or len(rec['fields']) != m or len(rec['locations']) != 8*m
                or any(len(e['stations']) != 8 for e in rec['fields'])
                or row['station_recovery']['stations'] != 8*m
                or row['nodal_geometry']['production_qualified'] is not False):
            raise ValueError('saved recovery hash or station coverage')
    from docs.reference_cases.ge_beam3_arch_field_comparison import recompute_rows
    if audit.canonical(recompute_rows(diagnostic, packets)) != audit.canonical(value['rows']):
        raise ValueError('field summary metrics differ from saved fields')
    return value


def worker(revision, output):
    guard(revision); packets, reference = inputs()
    if any(os.environ.get(k) != v for k, v in THREAD_ENVIRONMENT.items()):
        raise ValueError('one numerical thread required')
    sys.path.insert(0, str(ROOT/'src'))
    from docs.reference_cases import ge_beam3_arch_field_comparison as comparison
    from anysolver._ge_beam3_p5_seeded.core import canonical
    def progress(event): print(json.dumps(event, sort_keys=True), flush=True)
    progress(dict(stage='INITIALIZATION'))
    value, diagnostic = comparison.build(packets, reference, progress)
    diagnostic_raw = canonical(diagnostic)
    value.update(revision=revision, diagnostics_sha256=sha256(diagnostic_raw).hexdigest(),
                 checkpoint_sha256={str(m): h for m, (_, h) in INPUTS.items()})
    raw = canonical(value)
    validate(raw, diagnostic_raw, revision, packets)
    guard(revision); inputs()
    for name, data in (('fields-diagnostic.json', diagnostic_raw), ('comparison.pending.json', raw)):
        with (output/name).open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
    progress(dict(stage='COMPLETION', native_nonlinear_solves=0))


def run(revision, output):
    if os.name != 'nt': raise ValueError('Windows complete Job containment required')
    guard(revision); packets, _ = inputs()
    if not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github').resolve()):
        raise ValueError('fresh external absolute output required')
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ); env.update(THREAD_ENVIRONMENT)
    env.pop('PYTHONPATH', None); env['PYTHONDONTWRITEBYTECODE'] = '1'; env['PYTHONHASHSEED'] = '0'
    command = [sys.executable, '-B', '-m', 'docs.reference_cases.ge_beam3_arch_field_probe',
               '--worker', '--revision', revision, '--output', str(output)]
    job = _ProcessJob(24*(1 << 30)); start = time.monotonic(); activity = start; last = (0, 0)
    try:
        with (output/'stdout.log').open('xb') as stdout, (output/'stderr.log').open('xb') as stderr:
            process = job.launch(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
            while True:
                cpu, active, memory = job.accounting(); code = process.poll(); now = time.monotonic()
                current = (cpu, (output/'stdout.log').stat().st_size)
                if current != last: activity = now; last = current
                if now-start >= 600 or now-activity >= 120 or memory >= 24*(1 << 30):
                    raise RuntimeError('field diagnostic wall/inactivity/memory bound')
                if code is not None and active == 0: break
                time.sleep(.2)
            if code != 0: raise RuntimeError(f'field diagnostic failed: exit {code}; no retry')
        pending = output/'comparison.pending.json'; details = output/'fields-diagnostic.json'
        if pending.stat().st_size > 65536 or details.stat().st_size > 8*(1 << 20):
            raise ValueError('bounded staged field evidence')
        raw, diagnostic_raw = pending.read_bytes(), details.read_bytes()
        validate(raw, diagnostic_raw, revision, packets)
        guard(revision); inputs()
    finally:
        try:
            if not job.terminate(): raise RuntimeError('complete tree termination not proven')
        finally: job.close()
    guard(revision); inputs()
    if pending.read_bytes() != raw or details.read_bytes() != diagnostic_raw:
        raise ValueError('staged field evidence changed after cleanup')
    os.link(pending, output/'comparison.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    (worker if args.worker else run)(args.revision, args.output)


if __name__ == '__main__': main()
