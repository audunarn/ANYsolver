"""Versioned exact-uniform projected modal tail, reference development only.

The original helper owns lower-sum equations, validation and limits. Only its
tail is replaced for exactly uniform stored knots. Every nonuniform input
retains that helper's complete bracket, including its diagnostic behavior.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
from pathlib import Path

import numpy as np
from scipy import linalg

from scripts import r8_bl5_projected_modal_envelope_dev as legacy

VERSION = 'EXACT_UNIFORM_COMPLETE_2N_PROJECTED_TAIL_V1'
LEGACY_SHA256 = '6d534e8319c3b86b4660edc9a9857f35bd1a67f9a87975e1722212d31045387b'


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def projected_uniform_modal_bracket(knots, projection, length, width, ell, modes):
    """Return lower, upper, info with exact-uniform or original fallback tail.

    For N uniform cells, J=D P and a=M+1/2, every complete 2N-mode
    cosine-vector Gram equals N*(I+e0*e0.T). The decreasing block weights
    give tail A*N*(a^-3+1/(4*N*a^2))*(J.T@J+J0.T@J0), with the original
    Riesz prefactor A. This needs no positivity or rank assumption on P.
    It is an exact-arithmetic bound, not an interval arithmetic certificate.
    """
    actual_legacy_sha = _sha(legacy.__file__)
    if actual_legacy_sha != LEGACY_SHA256:
        raise ValueError('original projected lower/validation source identity changed')
    # Own both arrays before either validation or the exact stored-value gate.
    knots = legacy._owned_real_array(knots, 'knots')
    projection = legacy._owned_real_array(projection, 'projection')
    lower, old_upper, old_info = legacy.projected_modal_bracket(
        knots, projection, length, width, ell, modes)
    length, width, ell = float(length), float(width), float(ell)
    count, columns = projection.shape
    modes = int(modes)
    exact_length = Fraction.from_float(length)
    uniform = all(Fraction.from_float(float(value))*count == exact_length*j
                  for j, value in enumerate(knots))
    info = dict(old_info)
    info.update(tail_version=VERSION, exact_uniform_stored_knots=uniform,
        lower_validation_source=dict(file=Path(legacy.__file__).name, sha256=actual_legacy_sha),
        source_sha256=_sha(__file__))
    if not uniform:
        info.update(tail_method='ORIGINAL_PROJECTED_CAUCHY_FALLBACK',
                    fallback_reason='exact rational stored knot identity is nonuniform')
        return lower, old_upper, info

    first = modes+.5
    try:
        with np.errstate(over='raise', divide='raise', invalid='raise'):
            jumps = projection.copy()
            jumps[1:] -= projection[:-1]
            k_first = first*np.pi/length
            prefactor = 2*width/ell**2/np.tanh(k_first*width)*(length/np.pi)**3
            block_series_bound = first**-3+1/(4*count*first**2)
            coefficient = prefactor*count*block_series_bound
            jump_gram = jumps.T@jumps
            initial_jump_gram = np.outer(jumps[0], jumps[0])
            tail = coefficient*(jump_gram+initial_jump_gram)
            upper = lower+tail
    except (FloatingPointError, OverflowError) as error:
        raise ValueError('uniform modal tail arithmetic is not finitely representable') from error
    if not np.isfinite(tail).all() or not np.isfinite(upper).all():
        raise ValueError('uniform modal tail produced nonfinite arrays')

    # Legacy rank/minimum diagnostics describe the unchanged lower sum. Rank
    # is used only to decide whether a relative diagnostic is meaningful.
    relative = None
    if info['projection_numerical_rank'] < columns:
        diagnostic_status = 'rank_deficient_projection'
    elif info['lower_min_eigenvalue'] <= 0:
        diagnostic_status = 'lower_not_numerically_positive'
    else:
        try:
            relative = float(linalg.eigvalsh(tail, lower)[-1])
        except linalg.LinAlgError:
            diagnostic_status = 'lower_not_numerically_positive'
        else:
            if not np.isfinite(relative):
                raise ValueError('uniform relative tail diagnostic is nonfinite')
            diagnostic_status = 'available'
    multiplier = (4+first/count)/(2+first)
    equation = dict(info['source_equation'])
    equation['tail'] = 'complete 2N cosine-period jump Gram and decreasing stride-2N series majorant'
    info.update(source_equation=equation, tail_method='EXACT_UNIFORM_COMPLETE_2N',
        cosine_period_modes=2*count, block_series_bound=float(block_series_bound),
        tail_coefficient=float(coefficient), tail_initial_jump_outer_product=True,
        original_cauchy_tail_coefficient=old_info['tail_coefficient'],
        original_cauchy_relative_tail=old_info['relative_loewner_tail_bound'],
        analytical_old_tail_domination_multiplier=float(multiplier),
        analytical_old_tail_domination_certified=bool(multiplier <= 1),
        relative_diagnostic_status=diagnostic_status, relative_loewner_tail_bound=relative)
    return lower, upper, info


# Same call convention, only for an explicit import of this versioned module.
projected_modal_bracket = projected_uniform_modal_bracket
uniform_projected_modal_bracket = projected_uniform_modal_bracket
