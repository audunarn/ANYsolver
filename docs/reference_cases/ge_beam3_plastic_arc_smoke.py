"""Three isolated smoke stages; no public qualification and no automatic retry."""
import argparse
from hashlib import sha256
import os
from pathlib import Path
from threading import Event
import sys
import time
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical, strict_bytes, read, bind, bound
from docs.reference_cases.ge_beam3_retained_prestress_wave import supervise, write, publish
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_plastic_arc_fixture import fixture

MODULE = 'docs.reference_cases.ge_beam3_plastic_arc_smoke'

def build():
    import numpy as np
    from anysolver.fe_core import FEModel
    from anysolver.boundary import BoundaryCondition
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry
    from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
    from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
    from anysolver import _ge_beam3_retained_arc as arc
    f = fixture(1); model = FEModel('active-plastic-arc-smoke-v1')
    for i, point in enumerate(f['points'], 1):
        model.add_node(i, *point)
    law = EllipsoidalGeneralizedSection(f['elastic'], f['metric'], f['yield_force'], f['hardening'])
    for i, ids in enumerate(f['connectivity'], 1):
        nodes = [j-1 for j in ids]
        reference = CenteredCurvedBeam3ReferenceGeometry(np.array([f['points'][j] for j in nodes]), np.array([f['frames'][j] for j in nodes]))
        element = NativeGeneralizedStaticElement(i, tuple(ids), reference, law, order=f['order'])
        model.add_element(i, element); model.materials[element.material_name] = law
    model.add_boundary_condition(BoundaryCondition('clamped', [f['fixed_node']], {k:0. for k in ('ux','uy','uz','rx','ry','rz')}))
    programme = arc.Program(tuple(f['steps']), f['length_scale'], arc.NodalDeadForces((tuple(f['force']),)),
        parameter_scale=f['parameter_scale'], initial_sign=f['initial_sign'], max_iterations=f['max_iterations'], max_backtracks=f['max_backtracks'])
    return model, programme

def worker(mode, revision, output, input_path=None, input_sha=None, checkpoint=None, checkpoint_sha=None):
    guard(revision)
    if sys.flags.optimize or any(os.environ.get(k) != v for k,v in THREAD_ENVIRONMENT.items()):
        raise ValueError('assertions and one numerical thread required')
    if mode not in ('full', 'capture', 'check'):
        raise ValueError('registered worker stage')
    raw = None
    if mode != 'full':
        raw = read(input_path)
        if sha256(raw).hexdigest() != input_sha:
            raise ValueError('bound predecessor input')
    elif any(v is not None for v in (input_path, input_sha, checkpoint, checkpoint_sha)):
        raise ValueError('virgin full smoke has no input state')
    out = Path(output).resolve()
    if out.exists() or out.is_relative_to(ROOT):
        raise ValueError('fresh exclusive external output')
    out.mkdir()
    print(dict(stage='plastic-arc-initialized', mode=mode), flush=True)
    if mode == 'check':
        # This fresh process never imports ANYsolver, NumPy or producer mechanics.
        from docs.reference_cases.ge_beam3_plastic_arc_audit import audit
        cp = read(checkpoint)
        if sha256(cp).hexdigest() != checkpoint_sha:
            raise ValueError('original full checkpoint binding')
        result = audit(strict_bytes(raw), cp, revision, 1)
        if any(name == 'anysolver' or name.startswith('anysolver.') or name in ('numpy','scipy') for name in sys.modules):
            raise ValueError('independent checker imported mechanics')
        if read(checkpoint) != cp:
            raise ValueError('checkpoint changed during audit')
        publish(out/'result.json', result)
    else:
        sys.path.insert(0, str(ROOT/'src'))
        from math import fsum
        from anysolver import _ge_beam3_retained_arc as arc
        from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
        model, programme = build()
        if mode == 'full':
            result = arc.solve(model, programme, progress=lambda row: print(row, flush=True))
            write(out/'checkpoint-diagnostic.json', result.checkpoint)
            write(out/'disposition.json', dict(status=result.status, completed=result.completed_steps, failure=result.failure))
            if result.status != 'completed' or result.completed_steps != 3:
                raise RuntimeError('native plastic arc smoke did not complete: '+str(result.failure))
            write(out/'checkpoint.json', result.checkpoint)
        else:
            context = arc.Context(model, programme)
            accepted, records = context.restore(raw, expected_sha256=input_sha)
            if accepted.completed_steps != 3:
                raise ValueError('complete owned arc history required')
            before = native_canonical(accepted); steps = []
            for index in range(1,4):
                # Only the native owner creates a prefix of its own complete programme.
                prefix = context.checkpoint(records[:index])
                state, _ = context.restore(prefix, expected_sha256=sha256(prefix).hexdigest())
                state_before = native_canonical(state)
                _, _, metrics, responses, _ = context.physical.assemble(state.mechanical, state.parameter, state.origins)
                if max(metrics) > 1e-11:
                    raise ValueError('actual accepted equilibrium changed')
                elements = []
                for i, ((eid, element), response) in enumerate(zip(context.physical.elements, responses, strict=True)):
                    material = strict_bytes(response.material); stations = []
                    if native_canonical(material['origin']) != native_canonical(state.origins[i]) or native_canonical(material['history']) != native_canonical(state.histories[i]):
                        raise ValueError('original increment material histories')
                    for j, (row, origin) in enumerate(zip(material['stations'], state.origins[i].stations, strict=True)):
                        force = [fsum((a,b)) for a,b in zip(*row['resultants'])]
                        sample = element.section.response(force, origin=origin, control='resultant')
                        stations.append(dict(material=row, tangent=[sample.tangent, sample.tangent_low],
                            tangent_strain=[sample.strain,sample.strain_low], tangent_resultants=[sample.resultants,sample.resultants_low],
                            tangent_origin=sample.origin))
                        print(dict(stage='station-captured', step=index, element=eid, station=j), flush=True)
                    elements.append(dict(element_id=eid, stations=stations))
                context.recover(state)
                if native_canonical(state) != state_before:
                    raise ValueError('capture/recovery advanced committed history')
                steps.append(dict(step=index, record_sha256=strict_bytes(records[index-1])['record_sha256'], elements=elements))
            if native_canonical(accepted) != before or context.checkpoint(records) != raw:
                raise ValueError('original complete arc state changed')
            capture = dict(schema='GE_BEAM3_PLASTIC_ARC_CAPTURE_V1', revision=revision, fixture=fixture(1),
                checkpoint_sha256=input_sha, steps=steps, production_qualified=False)
            write(out/'capture.json', native_canonical(capture))
    guard(revision)
    if raw is not None and read(input_path) != raw:
        raise ValueError('predecessor changed')
    print(dict(stage='plastic-arc-worker-complete', mode=mode), flush=True)

def run(revision, output):
    guard(revision)
    root = Path(output).resolve()
    if root.exists() or root.is_relative_to(ROOT):
        raise ValueError('fresh external smoke wave')
    root.mkdir(parents=True, exist_ok=False)
    start = time.monotonic(); deadline = start+1800.; stop = Event(); receipts = {}; failure = None
    try:
        unit = root/'unit'; unit.mkdir()
        code = "import sys;sys.path[:0]=['src','.'];import pytest;raise SystemExit(pytest.main(sys.argv[1:]))"
        receipts['unit'] = supervise([sys.executable,'-B','-c',code,'-q','-p','no:cacheprovider',
            'tests/test_ge_beam3_plastic_arc_audit.py','--basetemp',str(unit/'pytest')], unit, deadline, stop)
        if not receipts['unit']['success']:
            raise RuntimeError('smoke authority unit failed')
        cp = cap = None
        for mode in ('full','capture','check'):
            guard(revision); job = root/mode; job.mkdir()
            command = [sys.executable,'-B','-m',MODULE,'--worker',mode,'--revision',revision,'--output',str(job/'output')]
            if mode != 'full':
                binding = cp if mode == 'capture' else cap
                bound(binding)
                command += ['--input',binding['path'],'--input-sha256',binding['sha256']]
            if mode == 'check':
                bound(cp); command += ['--checkpoint',cp['path'],'--checkpoint-sha256',cp['sha256']]
            receipts[mode] = supervise(command, job, deadline, stop)
            print(dict(mode=mode, **receipts[mode]), flush=True)
            if not receipts[mode]['success']:
                raise RuntimeError('bounded smoke failed: '+mode+'; no retry')
            if mode == 'full': cp = bind(job/'output/checkpoint.json')
            elif mode == 'capture': cap = bind(job/'output/capture.json')
        guard(revision); bound(cp); bound(cap)
    except Exception as error:
        failure = type(error).__name__+': '+str(error)
    elapsed = time.monotonic()-start
    if elapsed >= 1800.:
        failure = 'wave deadline'
    write(root/'wave.json', dict(revision=revision, receipts=receipts, elapsed=elapsed,
        success=failure is None, failure=failure, all_children_terminal=True, production_qualified=False))
    if failure is not None:
        raise RuntimeError(failure)
    result = bound(bind(root/'check/output/result.json'))
    publish(root/'aggregate.json', result)
    print(dict(stage='plastic-arc-smoke-complete', terminal=result['terminal'], steps=result['steps']), flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', choices=('full','capture','check'))
    parser.add_argument('--revision', required=True); parser.add_argument('--output', required=True)
    parser.add_argument('--input'); parser.add_argument('--input-sha256')
    parser.add_argument('--checkpoint'); parser.add_argument('--checkpoint-sha256')
    a = parser.parse_args()
    if a.worker:
        worker(a.worker,a.revision,a.output,a.input,a.input_sha256,a.checkpoint,a.checkpoint_sha256)
    else:
        if any(v is not None for v in (a.input,a.input_sha256,a.checkpoint,a.checkpoint_sha256)):
            raise ValueError('smoke coordinator takes no historical state')
        run(a.revision,a.output)

if __name__ == '__main__':
    main()
