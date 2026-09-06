"""Read-only diagnostics around one unchanged bounded local Newton solve.

Scope: supplied local state only. No global seed retry, input mutation, history
commit or automatic second attempt. Nonstationary block spectra are diagnostics.
"""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from types import MethodType

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearMixedBeamProbe


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False,
        default=lambda v:v.tolist())+'\n').encode('ascii')


def trace(reference, section, positions, frames, *, order=8):
    records = []
    class Traced(NonlinearMixedBeamProbe):
        def evaluate(self,*args,**kwargs):
            result = super().evaluate(*args,**kwargs)
            r,h = result.residual[18:],result.hessian[18:,18:]
            spectrum = np.linalg.svd(h,compute_uv=False)
            record = {'evaluation':len(records)+1,'rotation_residual':float(np.max(np.abs(r[:6]))),
                'moment_residual':float(np.max(np.abs(r[6:]))),
                'norm':float(np.max(np.abs(r))),'minimum_singular':float(spectrum[-1]),
                'maximum_singular':float(spectrum[0]),'potential':result.potential,
                'rotations':np.asarray(args[2]).copy(),'moments':np.asarray(args[3]).copy()}
            records.append(record)
            return result
    probe = Traced(reference,deepcopy(section),order=order)
    inputs = {'coordinates':reference.coordinates,'reference_frames':reference.nodal_triads,
        'positions':positions,'frames':frames,'order':order,'origins':[asdict(h) for h in probe.origins],
        'section':{'elastic':section._elastic,'direction':section._direction,
                   'yield_force':section._yield,'hardening':section._hardening}}
    before = canonical(inputs)
    try:
        result = probe.solve(positions,frames,max_iterations=25,max_evaluations=64)
        status = {'state':'COMPLETE','iterations':result.iterations,'evaluations':result.evaluations,
                  'residual':result.local_residual_norm}
    except (ValueError,RuntimeError,np.linalg.LinAlgError) as exc:
        status = {'state':'FAILED','error_type':type(exc).__name__,'error':str(exc)}
    if before!=canonical(inputs):
        raise AssertionError('diagnostic mutated supplied inputs')
    return {'input_sha256':hashlib.sha256(before).hexdigest(),'inputs':inputs,
            'status':status,'records':records,'production_qualified':False}


def trace_seed(model, positions, rotations, forces):
    """One successor diagnostic around the unchanged bounded global seed solver.

    Instrumentation is attached only to a deep copy, never the model class or
    source implementation. Mechanics evaluation order and budgets are unchanged.
    """
    from docs.reference_cases.ge_beam3_curved_p5_seeded_equilibrium_probe import solve
    attempts = []
    def instrumented(self,x,u,origins,budget):
        attempt = {'positions':x.copy(),'rotations':u.copy(),'elements':[]}
        attempts.append(attempt)
        results = []
        for ref,row,section,history in zip(self._references,self._maps,self._sections,origins):
            element = {'evaluations':[]}
            attempt['elements'].append(element)
            class Traced(NonlinearMixedBeamProbe):
                def evaluate(inner,*args,**kwargs):
                    budget.consume()
                    result = super().evaluate(*args,**kwargs)
                    element['evaluations'].append({'norm':float(np.max(np.abs(result.residual[18:]))),
                        'rotation_norm':float(np.max(np.abs(result.residual[18:24]))),
                        'moment_norm':float(np.max(np.abs(result.residual[24:]))),
                        'rotations':np.asarray(args[2]).copy(),'moments':np.asarray(args[3]).copy()})
                    return result
            local = Traced(ref,section,order=self._order,origins=history)
            try:
                result = local.solve(x[row],u[row] @ ref.nodal_triads)
                results.append(result)
                element['status'] = 'COMPLETE'
            except (ValueError,RuntimeError,np.linalg.LinAlgError) as exc:
                element['status'] = 'FAILED'
                element['error'] = str(exc)
                raise
        response = self._scatter(results)
        attempt['global_norm'] = self._norm(response.residual-self._external(forces),forces)
        return response
    staged = deepcopy(model)
    staged._solve_all = MethodType(instrumented,staged)
    try:
        result = solve(staged,positions,rotations,forces)
        status = {'state':'COMPLETE','epoch':result.committed.epoch}
    except (ValueError,RuntimeError,np.linalg.LinAlgError) as exc:
        status = {'state':'FAILED','error_type':type(exc).__name__,'error':str(exc)}
    return {'status':status,'attempts':attempts,'production_qualified':False}
