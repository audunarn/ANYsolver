"""Pure-norm checks with independent Decimal Green and analytic-cell solvers."""

from __future__ import annotations

from dataclasses import asdict

import numpy as np
from scipy import linalg

import _b3_e4_f03_trace_dual as finite_element
import _b3_e4_f03_trace_dual_exact as exact
import _b3_e4_f03_trace_green_oracle as oracle


LIMITS={'relative_skew':1e-12,'relative_frobenius_error':1e-12,
        'relative_operator_error':1e-9,'oracle_operator_change':1e-12,
        'analytical_identity_error':1e-12}


def relative_operator_error(candidate: np.ndarray,reference: np.ndarray) -> float:
    """Full-error spectral norm after reference Cholesky congruence; no repair."""
    lower=linalg.cholesky(reference,lower=True)
    left=linalg.solve_triangular(lower,candidate-reference,lower=True)
    whitened=linalg.solve_triangular(lower,left.T,lower=True).T
    return float(linalg.norm(whitened,2))


def compare(n_mortar: int) -> tuple[dict,dict[str,np.ndarray]]:
    if type(n_mortar) is not int or n_mortar not in (4,8,16):
        raise ValueError('registered norm inventory is Nm=4,8,16')
    n=n_mortar
    green12=oracle.green_gram(n,12,70)
    green16=oracle.green_gram(n,16,70)
    canonical=exact.dual_gram(n,'enriched')
    measure=np.full(n+1,1/n); measure[[0,-1]]*=.5
    endpoint=np.array(((1/np.tanh(1.),1/np.sinh(1.)),
                       (1/np.sinh(1.),1/np.tanh(1.))))
    identity=max(float(np.max(np.abs(canonical[-2:,-2:]-endpoint))),
                 abs(float(measure@canonical[:n+1,:n+1]@measure)-1),
                 float(np.max(np.abs(measure@canonical[:n+1,-2:]-1))))
    arrays={'green12_enriched':green12,'green16_enriched':green16}
    rows={}
    for family in ('P1','hybrid','enriched'):
        # Independently stated selection, not imported from the candidate metadata.
        selected=(list(range(n+1)) if family=='P1' else
                  list(range(1,n))+[n+1,n+2] if family=='hybrid' else
                  list(range(n+3)))
        candidate=exact.dual_gram(n,family)
        reference=green16[np.ix_(selected,selected)]
        earlier=green12[np.ix_(selected,selected)]
        if not np.all(np.isfinite(candidate)) or not np.all(np.isfinite(reference)):
            raise ValueError('nonfinite norm matrix')
        linalg.cholesky(candidate,lower=True)
        linalg.cholesky(reference,lower=True)
        metrics={
            'relative_skew':float(np.linalg.norm(candidate-candidate.T)/np.linalg.norm(candidate)),
            'relative_frobenius_error':float(np.linalg.norm(candidate-reference)/np.linalg.norm(reference)),
            'relative_operator_error':relative_operator_error(candidate,reference),
            'oracle_operator_change':relative_operator_error(earlier,reference),
            'analytical_identity_error':identity}
        if not all(np.isfinite(v) and v>=0 for v in metrics.values()):
            raise ValueError('invalid norm-comparison metric')
        approximation={}
        for level in (32,64):
            fe=finite_element.dual_gram(n,family,level)
            arrays[f'{family}_fe{level}']=fe
            approximation[str(level)]=relative_operator_error(fe,reference)
        arrays[family+'_analytic']=candidate
        rows[family]={
            'status':('PASSED_AUXILIARY_NORM_VALIDATION' if
                      all(metrics[k]<=v for k,v in LIMITS.items()) else 'FAILED_AUXILIARY_NORM_VALIDATION'),
            'measurements':metrics,'condition_2':float(np.linalg.cond(candidate)),
            'metadata':asdict(exact.metadata(n,family)),
            'descriptive_fe_relative_operator_error':approximation}
    return {'n_mortar':n,'families':rows},arrays
