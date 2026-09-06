"""Bounded sampled lateral-onset diagnostic, not a qualification runner.

No numerical import occurs at module import. A future separately frozen,
leased process runner must contain any multi-mesh execution of ``records``.
Numerical uncertainty is retained; a sampled sign bracket is not a proof of
the first continuum critical point or even of uniqueness between samples.
"""

import math


SCHEMA = 'GE_BEAM3_P5_SAMPLED_LATERAL_ONSET_DEVELOPMENT_V1'
MESHES = (4, 8, 16)
DROPS = tuple(i / 200 for i in range(13))
MAX_BISECTIONS = 16
WIDTH = 1e-7
LIMIT = 1e-11
RESTRICTION = 'NO_GO_PRODUCTION_RESTRICTION_UNCHANGED'


def sign(row):
    """Classify only outside the supplied numerical uncertainty band."""
    keys = {'drop', 'load', 'lowest', 'uncertainty', 'negative', 'unresolved'}
    if type(row) is not dict or set(row) != keys:
        raise ValueError('exact onset sample schema required')
    for key in keys - {'negative', 'unresolved'}:
        if type(row[key]) not in (int, float) or not math.isfinite(row[key]):
            raise ValueError('finite real onset values required')
    if not 0 <= row['drop'] <= DROPS[-1] or row['uncertainty'] < 0:
        raise ValueError('bounded drop and nonnegative uncertainty required')
    for key in ('negative', 'unresolved'):
        if type(row[key]) is not int or row[key] < 0:
            raise ValueError('nonnegative integer inertia counts required')
    result = 1 if row['lowest'] > row['uncertainty'] else (
        -1 if row['lowest'] < -row['uncertainty'] else 0)
    if ((result == 1 and (row['negative'] or row['unresolved'])) or
            (result == -1 and not row['negative']) or
            (result == 0 and (row['negative'] or not row['unresolved']))):
        raise ValueError('lowest value and inertia counts disagree')
    return result


def locate(evaluate):
    """Evaluate a fixed grid, then bisect its earliest observed + to - pair.

    ``evaluate(label, drop, origin_label)`` returns exactly the six-key sample.
    Origin labels name accepted states, not interpolated displacement fields.
    All grid samples run even after a crossing. A failure propagates, with no
    retry, cutback or interval extension. An uncertain midpoint stops refinement
    without destroying the last sign-separated bracket.
    """
    samples = []
    def sample(label, drop, origin):
        row = evaluate(label, drop, origin)
        polarity = sign(row)
        if row['drop'] != drop:
            raise ValueError('evaluated target differs from scheduled target')
        made = {'id': label, 'origin_id': origin, 'sign': polarity, **row}
        samples.append(made)
        return made
    grid = []
    for i, drop in enumerate(DROPS):
        grid.append(sample(f'grid-{i:02}', drop, grid[-1]['id'] if grid else None))
    common = {'schema': SCHEMA, 'samples': samples, 'production_qualified': False,
              'restriction': RESTRICTION, 'first_critical_point_proven': False,
              'interval_is_rigorous': False}
    if grid[0]['sign'] != 1:
        return dict(common, disposition='REFERENCE_LATERAL_POSITIVITY_UNRESOLVED', bracket=None)
    first = next((i for i, row in enumerate(grid) if row['sign'] != 1), None)
    if first is None:
        return dict(common, disposition='NO_LATERAL_CROSSING_OBSERVED_ON_FIXED_GRID', bracket=None)
    if grid[first]['sign'] == 0:
        return dict(common, disposition='GRID_LATERAL_SIGN_UNRESOLVED', bracket=None)
    left, right = grid[first-1], grid[first]
    disposition = 'BISECTION_BUDGET_EXHAUSTED'
    for i in range(MAX_BISECTIONS):
        if right['drop'] - left['drop'] <= WIDTH:
            disposition = 'SAMPLED_LATERAL_SIGN_BRACKET_LOCALIZED'
            break
        middle = sample(f'bisect-{i:02}', (left['drop']+right['drop'])/2, left['id'])
        if middle['sign'] == 0:
            disposition = 'MIDPOINT_LATERAL_SIGN_UNRESOLVED'
            break
        if middle['sign'] > 0:
            left = middle
        else:
            right = middle
    if right['drop'] - left['drop'] <= WIDTH:
        disposition = 'SAMPLED_LATERAL_SIGN_BRACKET_LOCALIZED'
    return dict(common, disposition=disposition,
                bracket={'left_id': left['id'], 'right_id': right['id'],
                         'width': right['drop']-left['drop']})


def records(*, count, progress, publish_raw, extent='REFINEMENT16'):
    """Numerical callback for a future contained runner; no standalone CLI.

    The two-element extent is solely for small disposable unit smoke tests.
    Every bisection starts from its saved positive endpoint; no accepted state
    is overwritten or extrapolated. Full trial matrices and mode vectors are
    raw diagnostics. This function neither claims a lease nor publishes an
    aggregate or grants execution authority.
    """
    if extent not in ('REFINEMENT16','ARCH_ONSET32'):
        raise ValueError('registered onset extent required')
    counts = (2, *MESHES, 32) if extent == 'ARCH_ONSET32' else (2, *MESHES)
    if type(count) is not int or count not in counts:
        raise ValueError('registered onset mesh count required')
    from dataclasses import asdict
    import numpy as np
    from docs.reference_cases.ge_beam3_curved_p5_arch_refinement_case import make_beam
    from docs.reference_cases.ge_beam3_curved_p5_displacement_control_probe import DisplacementControlledAssemblyProbe
    from docs.reference_cases.ge_beam3_curved_p5_arch_stability_inspection import classify_matrix
    from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest

    beam, _ = make_beam(count, extent=extent)
    states, bindings = {}, {}
    progress('INITIALIZATION', None)
    def evaluate(label, drop, origin):
        progress('STATE_START', label)
        control = DisplacementControlledAssemblyProbe(beam if origin is None else states[origin], node=count)
        trial = control.trial(.1-drop)
        control.commit(trial)
        current = control.committed_model
        state, response = current.committed, trial.assembly.response
        if digest(current.replay()) != digest(response):
            raise ValueError('onset accepted-origin replay mismatch')
        if any(h.accumulated != 0 for group in state.histories for h in group):
            raise ValueError('elastic onset state acquired plastic history')
        reflection = np.diag([1., 1., -1.])
        expected = np.zeros_like(state.forces);expected[count, 1] = state.forces[count, 1]
        residual = response.residual - current._external(expected)
        errors = {
            'equilibrium': current._norm(residual, expected),
            'position_planarity': float(np.max(np.abs(state.positions[:, 2]))),
            'rotation_planarity': float(np.max(np.abs(state.rotations-reflection@state.rotations@reflection))),
            'rotation_orthogonality': float(np.max(np.abs(state.rotations.transpose(0, 2, 1)@state.rotations-np.eye(3)))),
            'rotation_determinant': float(np.max(np.abs(np.linalg.det(state.rotations)-1))),
            'fixed_positions': float(np.max(np.abs(state.positions[[0, 2*count]]-beam._coordinates[[0, 2*count]]))),
            'fixed_rotations': float(np.max(np.abs(state.rotations[[0, 2*count]]-np.eye(3)))),
            'load_pattern': float(np.max(np.abs(state.forces-expected))),
        }
        if (state.positions[count, 1] != .1-drop or
                any(not math.isfinite(v) or v > LIMIT for v in errors.values())):
            raise ValueError('onset full spatial equilibrium/planarity/constraint mismatch')
        # Use the full conservative Hessian, never the control Schur matrix.
        spectra = classify_matrix(response.tangent, nodes=2*count+1, extent=extent)
        odd = spectra['out_of_plane']
        row = {'drop': drop, 'load': float(-state.forces[count, 1]),
               'lowest': float(odd['values'][0]), 'uncertainty': odd['uncertainty_band'],
               'negative': odd['negative'], 'unresolved': odd['unresolved']}
        sign(row)
        raw = {'id': label, 'origin_id': origin, 'elements': count,
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
