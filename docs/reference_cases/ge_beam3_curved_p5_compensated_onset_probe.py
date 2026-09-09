"""Compensated-coordinate successor of the sampled onset diagnostic.

No numerical import at module load. The historical grid, search and uncertainty
classification are reused unchanged. This is not a qualification certificate.
"""

import math

from docs.reference_cases import ge_beam3_curved_p5_arch_onset_probe as search


SCHEMA = 'GE_BEAM3_P5_COMPENSATED_SAMPLED_ONSET_V1'
RAW_SCHEMA = 'GE_BEAM3_P5_COMPENSATED_ONSET_RAW_V1'


def locate(evaluate):
    result = search.locate(evaluate)
    result['schema'] = SCHEMA
    return result


def records(*, count, progress, publish_raw):
    """Only two-element disposable tests or the separately leased 32 extent."""
    if type(count) is not int or count not in (2, 32):
        raise ValueError('registered compensated onset count required')
    from dataclasses import asdict
    from types import SimpleNamespace
    import numpy as np
    from docs.reference_cases.ge_beam3_curved_p5_arch_refinement_case import make_beam
    from docs.reference_cases.ge_beam3_curved_p5_compensated_assembly import CompensatedAssemblyHistoryProbe
    from docs.reference_cases.ge_beam3_curved_p5_compensated_control import CompensatedDisplacementControlledAssemblyProbe
    from docs.reference_cases.ge_beam3_curved_p5_arch_stability_inspection import classify_matrix
    from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest

    source, _ = make_beam(count, extent='ARCH_ONSET32')
    beam = CompensatedAssemblyHistoryProbe(source._references,
        [tuple(int(n) for n in row) for row in source._maps], source._sections,
        fixed_nodes=tuple(int(n) for n in source._fixed), order=source._order, extent=source._extent)
    states, bindings = {}, {}
    progress('INITIALIZATION', None)

    def evaluate(label, drop, origin):
        progress('STATE_START', label)
        control = CompensatedDisplacementControlledAssemblyProbe(beam if origin is None else states[origin], node=count)
        before = digest(control.committed_model.committed)

        def failed(snapshot):
            current = control.committed_model
            if digest(current.committed) != before or control._pending is not None:
                raise ValueError('failed onset modified committed state')
            if digest(current._reconstruct(SimpleNamespace(**snapshot))) != digest(snapshot['response']):
                raise ValueError('failed onset last evaluation replay mismatch')
            raw = dict(snapshot, replay_verified=True, id=label, origin_id=origin,
                       origin_checkpoint_sha256=before, production_qualified=False)
            raw['response'] = asdict(snapshot['response'])
            raw['origins'] = [[asdict(h) for h in group] for group in snapshot['origins']]
            publish_raw(label+'-failed-last', raw)

        trial = control.trial(.1-drop, observer=lambda event: progress('CONTROL', label, event),
                              failure_observer=failed)
        control.commit(trial)
        current = control.committed_model
        state, response = current.committed, trial.assembly.response
        if digest(current.replay()) != digest(response):
            raise ValueError('onset accepted-origin replay mismatch')
        if any(h.accumulated != 0 for group in state.histories for h in group):
            raise ValueError('elastic onset state acquired plastic history')
        reflection = np.diag([1., 1., -1.])
        expected = np.zeros_like(state.forces); expected[count, 1] = state.forces[count, 1]
        residual = response.residual-current._external(expected)
        errors = {
            'equilibrium': current._norm(residual, expected),
            'position_planarity': max(abs(math.fsum((float(h), float(l))))
                for h, l in zip(state.positions[:, 2], state.position_low[:, 2])),
            'rotation_planarity': float(np.max(np.abs(state.rotations-reflection@state.rotations@reflection))),
            'rotation_orthogonality': float(np.max(np.abs(state.rotations.transpose(0, 2, 1)@state.rotations-np.eye(3)))),
            'rotation_determinant': float(np.max(np.abs(np.linalg.det(state.rotations)-1))),
            'fixed_positions': max(abs(math.fsum((float(state.positions[i,j]), float(state.position_low[i,j]),
                -float(beam._coordinates[i,j])))) for i in (0, 2*count) for j in range(3)),
            'fixed_rotations': float(np.max(np.abs(state.rotations[[0, 2*count]]-np.eye(3)))),
            'load_pattern': float(np.max(np.abs(state.forces-expected))),
        }
        if (state.positions[count, 1] != .1-drop or state.position_low[count, 1] != 0. or
                any(not math.isfinite(v) or v > search.LIMIT for v in errors.values())):
            raise ValueError('onset full spatial equilibrium/planarity/constraint mismatch')
        # Full conservative tangent; no controlled Schur or lateral projection.
        spectra = classify_matrix(response.tangent, nodes=2*count+1, extent='ARCH_ONSET32')
        odd = spectra['out_of_plane']
        row = {'drop': drop, 'load': float(-state.forces[count, 1]),
               'lowest': float(odd['values'][0]), 'uncertainty': odd['uncertainty_band'],
               'negative': odd['negative'], 'unresolved': odd['unresolved']}
        search.sign(row)
        raw = {'schema': RAW_SCHEMA, 'id': label, 'origin_id': origin, 'elements': count,
               'origin_checkpoint_sha256': before, 'checkpoint_sha256': digest(state),
               'sample': row, 'state_errors': errors, 'trial': asdict(trial),
               'spectra': spectra, 'production_qualified': False}
        bindings[label] = publish_raw(label, raw)
        states[label] = current
        progress('STATE_COMPLETE', label)
        return row

    result = locate(evaluate)
    result.update(elements=count, raw_bindings=bindings)
    progress('PROBE_COMPLETE', None)
    return result
