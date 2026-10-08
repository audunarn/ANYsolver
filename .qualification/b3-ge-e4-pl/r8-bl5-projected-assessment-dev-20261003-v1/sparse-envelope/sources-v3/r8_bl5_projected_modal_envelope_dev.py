"""Bounded projected shell line-dual reference, for development only.

The projection maps density coordinates to complete P0 cell values. Projecting
the exact sine integrals before their Gram preserves the old reference equation
and its Loewner tail; this module supplies no mechanical or acceptance policy.
"""
from __future__ import annotations

from numbers import Integral, Real

import numpy as np
from scipy import linalg


MAX_CELLS = 1024
MAX_MODES = 16384
MAX_COLUMNS = 160
MODAL_CHUNK_ROWS = 256
SOURCE_EQUATION = {
    'file': 'scripts/b3_e4_bl5_modal_reference_dev.py',
    'symbol': 'p0_shell_bracket',
    'sha256': 'e1553e83596d5d371a7b2e196c000a1d9b551e361abf0942e352d54018b5712b',
    'integral': 'a_n=(2/(L*k_n))*(cos(k_n*x_left)-cos(k_n*x_right))',
    'weight': 'L^2*W/(2*ell^2*alpha_n*tanh(alpha_n*W))',
    'tail': 'original P0 count times jump Gram; alpha>=k, decreasing coth, integral-series majorant',
}


def _owned_real_array(value, name):
    try:
        raw = np.asarray(value)
        if np.iscomplexobj(raw):
            raise ValueError(f'{name} must be real')
        result = np.array(raw, dtype=np.float64, copy=True)
    except (TypeError, OverflowError) as error:
        raise ValueError(f'{name} must be finite real values') from error
    if not np.isfinite(result).all():
        raise ValueError(f'{name} must be finite real values')
    return result


def projected_modal_bracket(knots, projection, length, width, ell, modes):
    """Return ``P.T lower P``, ``P.T upper P`` and explicit diagnostics.

    Inputs are copied. Only a <=256 by cell-count coefficient block and its
    <=256 by projected-column image are formed; no cell-count squared Gram is
    allocated. Signed, zero and rank-deficient force actions remain admitted.
    A relative tail is reported only when a numerically positive lower Gram
    and a numerically full-column-rank projection permit that diagnostic.
    """
    for name, value in (('length', length), ('width', width), ('ell', ell)):
        if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
                or not np.isfinite(value) or value <= 0):
            raise ValueError(f'{name} must be a positive finite real scalar')
    length, width, ell = float(length), float(width), float(ell)
    knots = _owned_real_array(knots, 'knots')
    projection = _owned_real_array(projection, 'projection')
    if (knots.ndim != 1 or not 2 <= knots.size <= MAX_CELLS+1
            or np.any(np.diff(knots) <= 0) or knots[0] != 0.
            or knots[-1] != length):
        raise ValueError('bounded strictly increasing complete P0 knots required')
    count = knots.size-1
    if (projection.ndim != 2 or projection.shape[0] != count
            or not 1 <= projection.shape[1] <= MAX_COLUMNS):
        raise ValueError('projection must have one row per cell and 1..160 columns')
    if (isinstance(modes, (bool, np.bool_)) or not isinstance(modes, Integral)
            or not count <= modes <= MAX_MODES):
        raise ValueError('integer modal count must lie between cell count and 16384')
    modes = int(modes)
    columns = projection.shape[1]
    lower = np.zeros((columns, columns), dtype=np.float64)
    try:
        with np.errstate(over='raise', divide='raise', invalid='raise'):
            for start in range(0, modes, MODAL_CHUNK_ROWS):
                stop = min(start+MODAL_CHUNK_ROWS, modes)
                k = (np.arange(start, stop)+.5)*np.pi/length
                alpha = np.sqrt(1+ell**2*k**2)/ell
                coefficient = 2/(length*k[:, None])*(
                    np.cos(k[:, None]*knots[:-1])-np.cos(k[:, None]*knots[1:]))
                weight = length**2*width/(2*ell**2*alpha*np.tanh(alpha*width))
                projected = coefficient@projection
                lower += projected.T@(weight[:, None]*projected)
            # D has initial row p_0 and successive jumps p_j-p_(j-1).
            # cos(k_n L)=0: there is no terminal jump in the original bound.
            jumps = projection.copy()
            jumps[1:] -= projection[:-1]
            first = modes+.5
            series_bound = first**-3+1/(2*first**2)
            k_first = first*np.pi/length
            tail_coefficient = (2*width/ell**2/np.tanh(k_first*width)*
                                (length/np.pi)**3*series_bound*count)
            tail = tail_coefficient*(jumps.T@jumps)
            upper = lower+tail
    except (FloatingPointError, OverflowError) as error:
        raise ValueError('modal reference arithmetic is not finitely representable') from error
    if not all(np.isfinite(matrix).all() for matrix in (lower, tail, upper)):
        raise ValueError('modal reference produced nonfinite arrays')

    # Rank is needed solely for the relative diagnostic, never for admission.
    singular = linalg.svdvals(projection)
    rank_threshold = float(np.finfo(float).eps*max(projection.shape)*singular[0])
    rank = int(np.count_nonzero(singular > rank_threshold))
    minimum = float(linalg.eigvalsh(lower)[0])
    relative_tail = None
    if rank < columns:
        diagnostic_status = 'rank_deficient_projection'
    elif minimum <= 0:
        diagnostic_status = 'lower_not_numerically_positive'
    else:
        try:
            relative_tail = float(linalg.eigvalsh(tail, lower)[-1])
        except linalg.LinAlgError:
            diagnostic_status = 'lower_not_numerically_positive'
        else:
            if not np.isfinite(relative_tail):
                raise ValueError('relative modal tail diagnostic is nonfinite')
            diagnostic_status = 'available'
    if not np.isfinite(minimum):
        raise ValueError('lower modal eigenvalue diagnostic is nonfinite')
    info = dict(
        status='DEVELOPMENT_REFERENCE_ONLY',
        source_equation=dict(SOURCE_EQUATION),
        modes=modes, input_cells=count, projected_columns=columns,
        input_projection_shape=[count, columns], output_gram_shape=[columns, columns],
        supports=count,  # Historical helper key: this is its P0 cell count.
        chunks=(modes+MODAL_CHUNK_ROWS-1)//MODAL_CHUNK_ROWS,
        max_chunk_rows=min(modes, MODAL_CHUNK_ROWS),
        limits=dict(cells=MAX_CELLS, modes=MAX_MODES, columns=MAX_COLUMNS,
                    chunk_rows=MODAL_CHUNK_ROWS),
        tail_cell_count=count, tail_coefficient=float(tail_coefficient),
        projection_numerical_rank=rank, rank_threshold=rank_threshold,
        relative_diagnostic_status=diagnostic_status,
        relative_loewner_tail_bound=relative_tail,
        lower_min_eigenvalue=minimum,
    )
    return lower, upper, info
