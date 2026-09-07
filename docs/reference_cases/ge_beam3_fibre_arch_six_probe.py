"""Explicit six/twelve-macro diagnostic; never retries a preserved request.

Use the active workspace scheduling policy; preserve prior resource history.
The saved nominal reference loads are read and hash-checked; no BVP/reference
generation is performed. Process and scientific bounds are independent of
whether the workspace currently requires a global resource grant.
"""
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


def checked_macros(macros):
    if type(macros) is not int or macros not in (6, 12):
        raise ValueError('only the explicitly registered six/twelve-macro scope is admitted')
    return macros


def reference_bytes():
    path = ROOT/audit.REFERENCE_PATH
    if path.stat().st_size > 2*1024*1024: raise ValueError('reference size bound')
    raw = path.read_bytes().replace(b'\r\n', b'\n')
    if sha256(raw).hexdigest() != audit.REFERENCE_LF_SHA: raise ValueError('preserved reference identity')
    audit.parse(raw)
    return raw


def ready(checkpoint_raw, reference_raw, revision, *, macros=6):
    checked_macros(macros)
    if (type(revision) is not str or len(revision) != 40
            or any(c not in '0123456789abcdef' for c in revision)
            or sha256(reference_raw).hexdigest() != audit.REFERENCE_LF_SHA):
        raise ValueError('exact source/reference identity required')
    rows = audit.inspect_records(audit.parse(checkpoint_raw), audit.parse(reference_raw), macros=macros)
    name = {6: 'SIX', 12: 'TWELVE'}[macros]
    return dict(schema=f'GE_BEAM3_{name}_MACRO_PRESERVED_REFERENCE_LOAD_DIAGNOSTIC_V1',
        status='DEVELOPMENT_LOAD_COMPARISON_ONLY', revision=revision, macros=macros,
        checkpoint_sha256=sha256(checkpoint_raw).hexdigest(), checkpoint_bytes=len(checkpoint_raw),
        reference_commit=audit.REFERENCE_COMMIT, reference_lf_sha256=audit.REFERENCE_LF_SHA,
        reference_recomputed=False, native_replay_performed=True, rows=rows,
        independent_review='PENDING', production_qualified=False, same_equilibrium_branch_proved=False,
        prior_four_macro_request_successful=False, runtime_version_check_only=True)


def worker(revision, output, *, macros=6):
    checked_macros(macros)
    guard(revision); reference = reference_bytes()
    if any(os.environ.get(k) != v for k, v in THREAD_ENVIRONMENT.items()):
        raise ValueError('single numerical thread required')
    sys.path.insert(0, str(ROOT/'src'))
    from docs.reference_cases import ge_beam3_fibre_arch_refinement as family
    from anysolver import _ge_beam3_seeded_fibre_control as control
    def progress(event): print(json.dumps(event, sort_keys=True, default=str), flush=True)
    progress(dict(stage='INITIALIZATION', macros=macros))
    model = family.model(macros); program = family.program(macros)
    budget = 256 if macros == 6 else 512
    result = control.solve_translation_program(model, program, progress=progress, max_coordinates=budget)
    with (output/'checkpoint-diagnostic.json').open('xb') as stream: stream.write(result.checkpoint)
    if result.status != 'completed': raise RuntimeError(f'{result.status}: {result.failure}')
    progress(dict(stage='NATIVE_REPLAY'))
    control.Context(model, program, max_coordinates=budget).restore(result.checkpoint,
        expected_sha256=sha256(result.checkpoint).hexdigest())
    value = ready(result.checkpoint, reference, revision, macros=macros)
    guard(revision)
    if reference_bytes() != reference: raise ValueError('reference changed during worker')
    with (output/'comparison.pending.json').open('xb') as stream: stream.write(audit.canonical(value))
    progress(dict(stage='COMPLETION', reference_recomputed=False))


def run(revision, output, *, macros=6):
    checked_macros(macros)
    if os.name != 'nt': raise ValueError('Windows Job containment required')
    guard(revision); reference = reference_bytes()
    if not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github').resolve()):
        raise ValueError('fresh absolute external output required')
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ); env.update(THREAD_ENVIRONMENT)
    env.pop('PYTHONPATH', None); env['PYTHONHASHSEED'] = '0'; env['PYTHONDONTWRITEBYTECODE'] = '1'
    command = [sys.executable, '-B', '-m', 'docs.reference_cases.ge_beam3_fibre_arch_six_probe',
               '--worker', '--revision', revision, '--output', str(output), '--macros', str(macros)]
    job = _ProcessJob(24*(1 << 30)); started = time.monotonic(); activity = started; last = (0, 0)
    try:
        with (output/'stdout.log').open('xb') as out, (output/'stderr.log').open('xb') as err:
            process = job.launch(command, cwd=ROOT, env=env, stdout=out, stderr=err)
            while True:
                cpu, active, memory = job.accounting(); code = process.poll(); now = time.monotonic()
                current = (cpu, (output/'stdout.log').stat().st_size)
                if current != last: activity = now; last = current
                if now-started >= 600 or now-activity >= 120 or memory >= 24*(1 << 30):
                    raise RuntimeError('refinement wall/inactivity/memory bound')
                if code is not None and active == 0: break
                time.sleep(.2)
            if code != 0: raise RuntimeError(f'refinement diagnostic failed: exit {code}')
        guard(revision)
        if reference_bytes() != reference: raise ValueError('reference changed before publication')
        checkpoint = output/'checkpoint-diagnostic.json'
        pending = output/'comparison.pending.json'
        if checkpoint.stat().st_size > 2*1024*1024 or pending.stat().st_size > 65536:
            raise ValueError('bounded diagnostic sizes required')
        expected = audit.canonical(ready(checkpoint.read_bytes(), reference, revision, macros=macros))
        if pending.read_bytes() != expected: raise ValueError('complete exact comparison required')
    finally:
        try:
            if not job.terminate(): raise RuntimeError('complete tree termination not proven')
        finally:
            job.close()
    # Publication also requires successful cleanup proof, not just root exit.
    guard(revision)
    if reference_bytes() != reference or pending.read_bytes() != expected:
        raise ValueError('source or staged diagnostic changed after cleanup')
    os.link(pending, output/'comparison.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--macros', type=int, choices=(6, 12), default=6)
    args = parser.parse_args(); (worker if args.worker else run)(args.revision, args.output, macros=args.macros)


if __name__ == '__main__': main()
