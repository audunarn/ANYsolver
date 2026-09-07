"""Bounded two-macro native-plastic integration probe, not restart authority.

Reuse the elastic context's standalone model capture, DOF layout, supports,
and purely geometric increment operation only. Do NOT use its elastic
assembly, recovery, checkpoint, or restore for plastic state.
"""
from time import monotonic
import numpy as np
from anysolver._ge_beam3_retained_state import Context
from anysolver._ge_beam3_retained_plastic import RetainedPlasticOperator
from anysolver._native_reference_modal import _owned
from anysolver._ge_beam3_p5_seeded.core import canonical


def solve(model, program, *, progress=None):
    start = monotonic(); layout = Context(model, program)
    if len(layout.elements) != 2 or layout.count > 80: raise ValueError('two-macro correctness probe only')
    probes = tuple(RetainedPlasticOperator(e) for _, e in layout.elements)
    if any(len(p.stations) != 16 for p in probes): raise ValueError('16 stations per macro required')
    accepted = layout.initial; histories = _owned(np.zeros((2, 16, 4)))
    replay_origins = histories; records = []; trace = []
    def safe(stage, target, iteration):
        layout.guard()
        if monotonic()-start > 120: raise RuntimeError('plastic probe cooperative deadline')
        event = dict(stage=stage, target=target, iteration=iteration)
        trace.append(event)
        if progress is not None: progress(dict(event))
        layout.guard()
    def assemble(state, parameter, origins):
        layout.guard(); residual = np.zeros(layout.count); hessian = np.zeros((layout.count, layout.count))
        evaluations = []
        for i, probe in enumerate(probes):
            nodes = layout.nodes[i]
            response = probe.evaluate(state.positions[nodes], state.position_low[nodes], state.nodal_frames[nodes],
                state.cell_rotations[i], state.resultants[i], origins=origins[i].tolist())
            residual[layout.slots[i]] += response.residual
            hessian[np.ix_(layout.slots[i], layout.slots[i])] += response.hessian+response.hessian_low
            evaluations.append(response)
        residual[:layout.nodal_count] -= parameter*layout.force
        scaled = residual/layout.scales
        metrics = [float(np.linalg.norm(scaled[layout.equilibrium])), float(np.linalg.norm(scaled[layout.compatibility]))]
        return residual, hessian, metrics, evaluations
    failure = None
    try:
        for target_index, target in enumerate(program.targets, 1):
            trial = accepted; origins = histories
            for iteration in range(program.max_iterations+1):
                safe('before_assembly', target_index, iteration)
                residual, hessian, metrics, evaluations = assemble(trial, target, origins)
                trace.append(dict(stage='metrics', target=target_index, iteration=iteration, metrics=metrics))
                if max(metrics) <= 1e-11:
                    proposed = _owned([r.history for r in evaluations])
                    before = canonical([r.material.decode() for r in evaluations])
                    # Final-state replay uses the same accepted increment origin,
                    # not the newly proposed history of this increment.
                    _, _, replay_metrics, replay = assemble(trial, target, origins)
                    if before != canonical([r.material.decode() for r in replay]) or replay_metrics != metrics:
                        raise ValueError('plastic final-state replay disagreement')
                    safe('before_commit', target_index, iteration)
                    accepted, histories, replay_origins = trial, proposed, origins
                    records.append(dict(target=target_index, parameter=target, iterations=iteration,
                        metrics=metrics, state=accepted.descriptor(), origins=origins, histories=histories,
                        material=[r.material.decode() for r in evaluations]))
                    safe('committed', target_index, iteration)
                    break
                if iteration == program.max_iterations: raise RuntimeError('plastic probe Newton limit')
                step = np.zeros(layout.count)
                step[layout.free] = np.linalg.solve(hessian[np.ix_(layout.free, layout.free)], -residual[layout.free])
                if not np.isfinite(step).all(): raise ValueError('nonfinite plastic probe step')
                for cut in range(program.max_backtracks+1):
                    safe('before_trial', target_index, iteration)
                    candidate = layout.advance(trial, step*(.5**cut))
                    _, _, changed, _ = assemble(candidate, target, origins)
                    if max(changed) < max(metrics): trial = candidate; break
                else: raise RuntimeError('plastic probe line search limit')
    except Exception as error:
        failure = type(error).__name__+': '+str(error)
    return dict(status='completed' if failure is None else 'failed', failure=failure,
        completed_targets=len(records), records=records, trace=trace,
        state=accepted.descriptor(), histories=histories, replay_origins=replay_origins,
        production_qualified=False)
