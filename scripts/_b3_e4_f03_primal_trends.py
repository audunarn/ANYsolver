"""Frozen internal Ritz settling checks on already saved physical states."""
from __future__ import annotations

import math
import numpy as np
from _b3_e4_f03_primal_functional import (Functional, norm_squared,
    NonfiniteGreenResponse, NegativeGreenResponse)

LEVELS = (4, 8, 12, 16, 24)
F0 = 1e6
M0 = F0
U0 = F0/(210e9*.07)
E0 = F0*U0
SCALAR_SCALES = {'root_reaction': F0, 'left_edge_wrench': F0,
    'right_edge_wrench': F0, 'tip_pose_scaled': U0,
    'shell_energy_j': E0, 'beam_energy_j': E0, 'total_energy_j': E0,
    'root_atom': F0, 'tip_atom': F0, 'total_band_wrenches': F0}


def embed(q, coarse, fine):
    """Exact component/i/j embedding of nested supported Legendre bases."""
    if type(coarse) is not int or type(fine) is not int or not 2 <= coarse < fine <= 24:
        raise ValueError('invalid nested Ritz degree pair')
    q = np.asarray(q)
    if q.shape != (2*(coarse*coarse-1),) or not np.isfinite(q).all():
        raise ValueError('invalid coarse Ritz coefficients')
    result = np.zeros((2, fine-1, fine+1))
    result[:, :coarse-1, :coarse+1] = q.reshape(2, coarse-1, coarse+1)
    return result.ravel()


def _functional(arrays):
    return Functional(arrays['density_coefficients'], arrays['cosine'], arrays['atoms'])


def scalar_trend(values, scale):
    if len(values) != len(LEVELS) or any(not math.isfinite(v) for v in values):
        raise ValueError('invalid five-level physical scalar inventory')
    signed = [b-a for a, b in zip(values, values[1:])]
    changes = [abs(v) for v in signed]
    relative = [c/max(abs(a), abs(b), 1e-3*scale)
                for a, b, c in zip(values, values[1:], changes)]
    settled = all(value <= .01 for value in relative[-2:])
    not_growing = changes[-1] <= changes[-2]+1e-5*scale
    return {'values': values, 'signed_changes': signed, 'relative_changes': relative,
            'both_final_pairs_within_one_percent': settled,
            'last_change_not_growing': not_growing, 'passed': settled and not_growing}


def assess_sequence(saved, metrics):
    if set(saved) != set(LEVELS) or set(metrics) != set(LEVELS):
        raise ValueError('complete fixed five-level reference sequence required')
    scalars = {}
    for name, scale in SCALAR_SCALES.items():
        all_values = [np.asarray(metrics[n]['observables'][name], dtype=float) for n in LEVELS]
        if any(value.shape != all_values[0].shape for value in all_values):
            raise ValueError('physical reference output shape changed')
        for index in np.ndindex(all_values[0].shape):
            label = name+('['+','.join(map(str, index))+']' if index else '')
            scalars[label] = scalar_trend([float(value[index]) for value in all_values], scale)
    transitions = []
    numerical_passed = True
    for coarse, fine in zip(LEVELS, LEVELS[1:]):
        left, right = saved[coarse], saved[fine]
        kfine = right['K_shell']+right['K_beam']
        qleft = embed(left['q'], coarse, fine)
        error = right['q']-qleft
        distance = float(.5*error@kfine@error)
        uc = float(metrics[coarse]['observables']['total_energy_j'])
        uf = float(metrics[fine]['observables']['total_energy_j'])
        defect = abs((uf-uc)-distance)/max(E0, abs(uc)+abs(uf)+abs(distance))
        ordered = uf >= uc-1e-10*E0
        fleft, fright = _functional(left), _functional(right)
        delta = fright.difference(fleft)
        try:
            q48, q64 = norm_squared(delta, order=48), norm_squared(delta, order=64)
            resolution = abs(q48-q64)/max(abs(q48), abs(q64), 1000.**2)
            difference = math.sqrt(q64)
            operand_norms = [float(metrics[n]['observables']['full_functional_norm_N']) for n in (coarse, fine)]
            relative = difference/max(*operand_norms, 1000.)
            norm_data = {'squared_48': q48, 'squared_64': q64, 'resolution': resolution,
                         'difference_N': difference, 'operand_norms_N': operand_norms,
                         'relative_difference': relative}
            passed = (math.isfinite(defect) and distance >= 0 and ordered
                      and defect <= 1e-10 and resolution <= 1e-10)
        except (NonfiniteGreenResponse, NegativeGreenResponse) as exc:
            # A negative/nonfinite Green quadratic form is a failed numerical
            # check. Preserve the reason; never substitute a clipped norm.
            norm_data = {'failure': str(exc)}
            passed = False
        numerical_passed &= passed
        transitions.append({'coarse': coarse, 'fine': fine, 'energy_distance_j': distance,
            'energy_change_j': uf-uc, 'nested_energy_defect': defect,
            'energy_nondecreasing': ordered, 'functional': norm_data, 'numerical_passed': passed})
    functional_passed = False
    if numerical_passed:
        penultimate, final = [row['functional'] for row in transitions[-2:]]
        functional_passed = (penultimate['relative_difference'] <= .01
            and final['relative_difference'] <= .01
            and final['difference_N'] <= penultimate['difference_N']+10.)
    scalar_passed = all(row['passed'] for row in scalars.values())
    status = ('FAILED_NUMERICAL_SCREEN' if not numerical_passed else
              'PASSED_BOUNDED_PRIMAL_REFERENCE' if scalar_passed and functional_passed else
              'UNRESOLVED_RITZ_REFERENCE')
    return {'status': status, 'levels': list(LEVELS), 'transitions': transitions,
            'scalars': scalars, 'scalar_screen_passed': scalar_passed,
            'full_functional_screen_passed': functional_passed,
            'scope': 'internal bounded reference settling only; FE comparisons and G0B remain separate'}
