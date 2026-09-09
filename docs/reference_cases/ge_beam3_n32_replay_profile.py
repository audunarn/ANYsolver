"""Bounded read-only native replay diagnostic; no branch solve or qualification."""
import argparse
from contextlib import ExitStack
from hashlib import sha256
import os
from pathlib import Path
import sys
import time
import traceback
from unittest.mock import patch

from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, ROOT
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_n32_snapshot_capture import sources, PREFIX
from docs.reference_cases.ge_beam3_next_spatial_native import member
from docs.reference_cases.ge_beam3_n32_owned_capture import POLICY
from docs.reference_cases.ge_beam3_call_observer import Observer

ARCHIVE = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-n32-branch-b2d15e2-20260909')
MANIFEST = '586fa4cf92e5e12a1fb12c8334aafd41f79b9f245b62534b2bc1df9478808be5'
CHECKPOINT = '6d6d4790cff22761f2c04f0fcc9172630eebbf49f386f4b540047984e223b226'


def run(revision, mode, output):
    guard(revision)
    if mode not in ('control', 'observed'):
        raise ValueError('registered diagnostic mode')
    if any(os.environ.get(k) != v for k, v in THREAD_ENVIRONMENT.items()):
        raise ValueError('one numerical thread')
    inputs, _ = sources('plus')
    checkpoint = member(ARCHIVE, MANIFEST, 'wave/plus-a-advance-1/output/checkpoint.json', CHECKPOINT)
    root = Path(output).resolve()
    if root.is_relative_to(ROOT):
        raise ValueError('external diagnostic output only')
    root.mkdir(exist_ok=False)
    print(dict(stage='profile-authority-complete', mode=mode), flush=True)
    sys.path.insert(0, str(ROOT/'src'))
    from anysolver import _ge_beam3_retained_generalized_state as physical
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_refinement_capacity import n32_refinement_capacity
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from anysolver._ge_beam3_p5_seeded.core import canonical as native
    from docs.reference_cases.ge_beam3_n32_controlled_case import model

    observer = Observer(); timings = {}; error = None
    # Selected wrappers call each original exactly once, preserve return values
    # and exceptions, and are removed by ExitStack even on native deadline.
    targets = [(physical.Context, name, 'physical.'+name) for name in
        ('guard', 'assemble', 'record', '_recover_validated')]
    targets += [(physical, name, name) for name in ('retained_model_identity', 'require_valid_constraints')]
    targets += [(owner.Context, name, 'owner.'+name) for name in ('__init__', '_record', 'restore')]
    try:
        with n32_refinement_capacity(), ExitStack() as stack:
            if mode == 'observed':
                for obj, name, label in targets:
                    stack.enter_context(patch.object(obj, name, observer.wrap(label, getattr(obj, name))))
            observer.phase = 'model'; start = time.perf_counter(); cpu = time.process_time()
            made = model(32, arithmetic_policy=POLICY)
            timings['model'] = dict(wall=time.perf_counter()-start, cpu=time.process_time()-cpu)
            program = owner.Program((.0075, .010, .015), 17, (0., 0., 1.), NodalDeadForces(((33, 0., -1., 0.),)))
            observer.phase = 'enrollment'; start = time.perf_counter(); cpu = time.process_time()
            context = owner.Context(made, program, inputs['seed-input.json'], expected_seed_sha256=PREFIX['plus']['seed-input.json'])
            timings['enrollment'] = dict(wall=time.perf_counter()-start, cpu=time.process_time()-cpu)
            print(dict(stage='profile-enrollment-complete', mode=mode), flush=True)
            observer.phase = 'restore'; start = time.perf_counter(); cpu = time.process_time()
            state, records = context.restore(checkpoint, expected_sha256=CHECKPOINT)
            restored = context.checkpoint(records)
            if restored != checkpoint:
                raise ValueError('native replay changed accepted bytes')
            timings['restore'] = dict(wall=time.perf_counter()-start, cpu=time.process_time()-cpu)
            print(dict(stage='profile-restore-complete', mode=mode), flush=True)
            write(root/'checkpoint.json', restored)
            write(root/'state.json', native(state))
        guard(revision)
        if sources('plus')[0] != inputs or member(ARCHIVE, MANIFEST,
                'wave/plus-a-advance-1/output/checkpoint.json', CHECKPOINT) != checkpoint:
            raise ValueError('diagnostic inputs changed')
    except BaseException:
        error = traceback.format_exc()
        raise
    finally:
        write(root/'profile.json', dict(schema='GE_BEAM3_N32_REPLAY_PROFILE_V1',
            revision=revision, mode=mode, source_manifest=MANIFEST, checkpoint_sha256=CHECKPOINT,
            selected_calls=observer.summary(), timings=timings, error=error,
            advances_run=False, qualification_evidence=False, production_qualified=False))
    write(root/'complete.json', dict(schema='GE_BEAM3_N32_REPLAY_DIAGNOSTIC_V1',
        revision=revision, checkpoint_sha256=CHECKPOINT,
        state_sha256=sha256((root/'state.json').read_bytes()).hexdigest(),
        advances_run=False, qualification_evidence=False, production_qualified=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--revision', required=True)
    p.add_argument('--mode', choices=('control', 'observed'), required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    run(args.revision, args.mode, args.output)
