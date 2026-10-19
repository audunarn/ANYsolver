"""Observe one registered case with an explicit existing trace policy.

Default and director-integrated evidence are separate families; no solver,
constitutive, physical fixture or reference-load policy is changed here.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import copy
import hashlib
import inspect
import json
from pathlib import Path
import pickle
import sys
import time

import numpy as np

PHASE = Path(__file__).resolve().parents[1]
TASK = PHASE.parent
REPO = TASK.parents[1]
sys.path.insert(0, str(TASK / 'diagnostics'))
import arc_reference as ar
import anysolver.nonlinear_static as ns


def owned(value):
    if isinstance(value, Mapping):
        return {k: owned(v) for k,v in value.items()}
    if isinstance(value, np.ndarray):
        return value.copy()
    if isinstance(value, (tuple,list)):
        return type(value)(owned(v) for v in value)
    return copy.deepcopy(value)


def scalar(value):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f'Unsupported JSON object: {type(value).__name__}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nx', type=int, choices=ar.BASE_LEVELS+ar.EXTRA_LEVELS, required=True)
    parser.add_argument('--coupling', choices=('matching','nonmatching'), required=True)
    parser.add_argument('--eccentricity', type=float, choices=(0.,.002), required=True)
    parser.add_argument('--angle', type=float, choices=(30.,60.), required=True)
    parser.add_argument('--trace', choices=('linear','director_integrated'), default='linear')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    counts = dict(accepted=0,iterations=0,assembly_calls=0,factorize_calls=0)
    state = dict(status='started',solver_returned=False)

    def event(kind, **fields):
        row = dict(fields)
        row.update(kind=kind,elapsed_seconds=time.perf_counter()-start)
        with (args.output/'events.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(row,default=scalar,allow_nan=False)+'\n')
        print(json.dumps(row,default=scalar,allow_nan=False),flush=True)

    def raw(name, payload):
        path = args.output/name
        temporary = path.with_suffix(path.suffix+'.tmp')
        with temporary.open('wb') as stream:
            pickle.dump(payload,stream,protocol=5)
            stream.flush()
        temporary.replace(path)

    def metadata(name,payload):
        (args.output/name).write_text(json.dumps(payload,indent=2,default=scalar,allow_nan=False)+'\n',encoding='utf-8')

    def status(message):
        counts['iterations'] += 1
        frame = inspect.currentframe().f_back
        try:
            while frame is not None and frame.f_code.co_name != '_newton_increment':
                frame = frame.f_back
            if frame is None:
                raise RuntimeError('Observer requires actual force Newton frame')
            c = frame.f_locals
            # Copy only already computed values; never assemble or solve here.
            data = {k: owned(c[k]) for k in ('u','q_trial','committed_states','trial_states',
                    'F_int','F_ext_red','residual','residual_norm','reference','path_factor',
                    'iteration','step_index','K_T') if k in c}
            needed = ('u','committed_states','residual','residual_norm','reference','path_factor')
            if any(k not in data for k in needed):
                raise RuntimeError('Observer force Newton layout changed')
            data.update(accepted=False,meaning='latest unaccepted/candidate Newton state; not a restart checkpoint')
            raw('latest-pending.pkl',data)
            event('iteration',message=message,iteration=int(c['iteration']),
                  load_factor=float(c['path_factor']),residual_norm=float(c['residual_norm']),
                  reference=float(c['reference']),relative_residual=float(c['residual_norm']/c['reference']))
        finally:
            del frame

    real_snapshot, real_solve = ns._increment_snapshot, ar.solve_static_nonlinear
    real_assembly, real_factorize = ns._assemble_nonlinear_system, ns.factorize
    real_interpolated = ar.InterpolatedBeamShellMPCElement

    def interpolated(*a, **kw):
        if 'connection_trace' in kw:
            raise RuntimeError('Fixture unexpectedly supplies a second trace policy')
        return real_interpolated(*a, **kw, connection_trace=args.trace)

    def snapshot(*a,**kw):
        value = real_snapshot(*a,**kw)
        counts['accepted'] += 1
        raw(f'accepted-{counts["accepted"]:04d}.pkl',dict(
            accepted=True,u=np.asarray(value.displacements).copy(),
            element_states=owned(value.element_states),load_factor=float(value.load_factor),
            step_index=int(value.step_index),control_value=value.control_value))
        event('accepted',index=counts['accepted'],load_factor=float(value.load_factor))
        return value

    def assembly(*a,**kw):
        counts['assembly_calls'] += 1
        return real_assembly(*a,**kw)

    def factorize(*a,**kw):
        counts['factorize_calls'] += 1
        return real_factorize(*a,**kw)

    def solve(model,load,**kw):
        expected=dict(kinematics='corotational',corotational_tangent='work_conjugate',
                      num_steps=12,max_iterations=40,tolerance=1e-8)
        if kw != expected:
            raise RuntimeError('Original force solver controls changed')
        mode_count = 0
        for el in model.mesh.elements.values():
            if isinstance(el, real_interpolated):
                mode_count += 1
                if el.connection_trace != args.trace:
                    raise RuntimeError('Requested public trace policy was not installed')
                desc = el.get_nonlinear_mpc_descriptor(model.mesh)
                admitted_director = desc is not None and desc['director_trace_geometry'] is not None
                if admitted_director != (args.trace == 'director_integrated'):
                    raise RuntimeError('Actual nonlinear descriptor does not execute requested trace')
        if args.trace == 'director_integrated' and mode_count == 0:
            raise RuntimeError('Director candidate requires actual nonmatching attachments')
        raw('fixture.pkl',dict(nx=args.nx,coupling=args.coupling,eccentricity=args.eccentricity,
            angle=args.angle,oracle=ar.oracle(args.eccentricity,args.angle),solver_controls=kw,
            nodes={n:dict(coords=x.coords(),dofs=x.dofs) for n,x in model.mesh.nodes.items()}))
        result = real_solve(model,load,**kw,status_callback=status,
                            record_increment_snapshots=True)
        raw('solver-returned.pkl',dict(u=np.asarray(result.displacements).copy(),
            element_states=owned(result.element_states),status=result.status,
            stop_reason=result.stop_reason,load_factor=float(result.load_factor),info=owned(result.info)))
        state.update(solver_returned=True,solver_status=result.status,stop_reason=result.stop_reason)
        event('solver_returned',status=result.status,stop_reason=result.stop_reason,
              load_factor=float(result.load_factor),steps=len(result.steps))
        return result

    paths = [REPO/'src/anysolver'/name for name in ('elements.py','mesh_gen.py',
        'nonlinear_static.py','corotational.py','nonlinear_performance.py','_corotational_batch.py',
        '_director_trace.py','_nonlinear_events.py','_nonlinear_seed.py')]
    paths += [Path(__file__).resolve(), TASK/'diagnostics/arc_reference.py',
              TASK/'diagnostics/assessment_support.py',PHASE/'analytical-refinement-extension-authority.json']
    if args.trace == 'director_integrated':
        paths.append(PHASE/'director-option-scientific-candidate-authority.json')
    identity = {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    metadata('observer-inputs.json',dict(arguments=vars(args)|{'output':str(args.output)},
             identity=identity,controls=dict(num_steps=12,max_iterations=40,tolerance=1e-8),
             trace=args.trace,kind='observed original analytical force solve'))
    ns._increment_snapshot, ar.solve_static_nonlinear = snapshot, solve
    ns._assemble_nonlinear_system, ns.factorize = assembly, factorize
    ar.InterpolatedBeamShellMPCElement = interpolated
    try:
        record = ar.run_case(args.nx,args.coupling,args.eccentricity,args.angle)
        record['observer_identity'] = identity
        record['observer_counts'] = counts.copy()
        record['connection_trace'] = ('linear default' if args.trace == 'linear' else args.trace)
        metadata('result.json',record)
        state['status'] = 'assessment_completed'
        event('assessment_completed',complete=record['complete_and_equilibrated'],
              accuracy=record['accuracy_passed'],errors=record['errors'],
              equilibrium=record['equilibrium'],moment_balance=record['physical_root_My_balance_relative'])
    except BaseException as exc:
        state.update(status='exception',exception_type=type(exc).__name__,detail=str(exc))
        raise
    finally:
        ns._increment_snapshot, ar.solve_static_nonlinear = real_snapshot, real_solve
        ns._assemble_nonlinear_system, ns.factorize = real_assembly, real_factorize
        ar.InterpolatedBeamShellMPCElement = real_interpolated
        state.update(counts=counts,elapsed_seconds=time.perf_counter()-start)
        metadata('terminal.json',state)
        event('observer_terminal',**state)


if __name__ == '__main__':
    main()
