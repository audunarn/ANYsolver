"""Registered physical residual policy; no stability or physics certificate.

Reference scales are supplied by the caller, never inferred from a residual.
Legacy componentwise measures are reported without participating in acceptance.
"""
from dataclasses import dataclass
from numbers import Real
from collections.abc import Sequence
import numpy as np
from scipy import sparse


TOLERANCE = 1e-9


def _reference(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f'{name} must be a positive finite numeric reference')
    result = float(value)
    if not np.isfinite(result) or result <= 0:
        raise ValueError(f'{name} must be a positive finite numeric reference')
    return result


@dataclass(frozen=True)
class ResidualScales:
    """SI reference magnitudes registered independently for one right-hand side.

    An empty interface tuple explicitly uses ``displacement`` for all rows;
    a nonempty tuple must have exactly one entry per labelled interface.
    """
    length: float
    force: float
    displacement: float
    interface_displacements: tuple[float, ...] = ()

    def __post_init__(self):
        for name in ('length', 'force', 'displacement'):
            object.__setattr__(self, name, _reference(getattr(self, name), name))
        try:
            values = tuple(_reference(v, 'interface displacement') for v in self.interface_displacements)
        except TypeError as exc:
            raise ValueError('interface_displacements must be a sequence of references') from exc
        object.__setattr__(self, 'interface_displacements', values)


def _array(value, name, ndim):
    raw = np.asarray(value)
    if raw.dtype.kind not in 'biuf' or raw.ndim != ndim:
        raise ValueError(f'{name} must be a real {ndim}-dimensional array')
    result = np.array(raw, dtype=float, copy=True)
    if not np.isfinite(result).all():
        raise ValueError(f'{name} must be finite')
    return result


def _matrix(value, name):
    if sparse.issparse(value):
        if value.dtype.kind not in 'biuf' or value.ndim != 2:
            raise ValueError(f'{name} must be a real matrix')
        result = sparse.csr_matrix(value, dtype=float, copy=True)
        if not np.isfinite(result.data).all():
            raise ValueError(f'{name} must be finite')
        result.sum_duplicates()
        if not np.isfinite(result.data).all():
            raise ValueError(f'{name} has nonfinite summed entries')
        return result
    return sparse.csr_matrix(_array(value, name, 2))


def _indices(value, size, name):
    raw = np.asarray(value)
    if raw.shape == (0,):
        return np.empty(0, dtype=np.int64)
    if raw.ndim != 1 or raw.dtype.kind not in 'iu' or np.any(raw < 0) or np.any(raw >= size):
        raise ValueError(f'{name} must contain integer indices in [0,{size})')
    return np.array(raw, dtype=np.int64, copy=True)


def _max(value):
    return float(np.max(value, initial=0.0))


def _norm(value):
    return _max(np.abs(value))


def _matrix_norm(matrix):
    return _max(np.asarray(abs(matrix).sum(axis=1)).ravel())


def _computed_finite(*values):
    for value in values:
        data = value.data if sparse.issparse(value) else np.asarray(value)
        if not np.isfinite(data).all():
            raise ValueError('registered residual arithmetic produced nonfinite values/scales')


def _ratios(numerator, denominator):
    numerator, denominator = np.broadcast_arrays(np.abs(numerator), denominator)
    result = np.full(numerator.shape, np.inf)
    np.divide(numerator, denominator, out=result, where=denominator != 0)
    result[(numerator == 0) & (denominator == 0)] = 0.
    # Arithmetic overflow cannot turn finite-input acceptance into a pass.
    return np.where(np.isfinite(result), result, np.inf)


def evaluate_residuals(K, P, C, primary, multipliers, F, g, *,
                       native_rotation_dofs=(), scales: Sequence[ResidualScales],
                       constraint_interfaces=()):
    """Evaluate the immutable registered-v2 physical residual contract.

    All primary and force arrays have shape ``(n,nrhs)``, multiplier arrays
    ``(m,nrhs)``; affine constraints ``g`` have shape ``(m,)``. Row labels are
    contiguous interface indices starting at zero. Neither inputs nor scale
    objects are changed. Positive/zero normalized residuals are represented
    by Python ``float('inf')``; zero/zero is exactly zero.
    """
    K, P, C = (_matrix(v, name) for v, name in ((K, 'K'), (P, 'P'), (C, 'C')))
    u, lam, forces = (_array(v, name, 2) for v, name in
                      ((primary, 'primary'), (multipliers, 'multipliers'), (F, 'F')))
    affine = _array(g, 'g', 1)
    n, nrhs = u.shape
    if nrhs == 0:
        raise ValueError('at least one RHS')
    m = C.shape[0]
    if K.shape != (n, n) or P.shape[0] != n or C.shape[1] != n:
        raise ValueError('K/P/C shapes must be (n,n)/(n,r)/(m,n)')
    P.eliminate_zeros()
    if np.any(np.diff(P.indptr) > 1):
        raise ValueError('registered physical residual policy requires disjoint-support/orthogonal reduction; general multi-master MPC scaling is unqualified')
    if forces.shape != (n, nrhs) or lam.shape != (m, nrhs) or affine.shape != (m,):
        raise ValueError('F/multipliers/g shapes must be (n,nrhs)/(m,nrhs)/(m,)')
    rotations = _indices(native_rotation_dofs, n, 'native_rotation_dofs')
    if len(np.unique(rotations)) != len(rotations):
        raise ValueError('native_rotation_dofs must not repeat indices')
    labels = _indices(constraint_interfaces, m + 1, 'constraint_interfaces')
    if labels.shape != (m,):
        raise ValueError('constraint_interfaces must supply one integer label per constraint row')
    interfaces = int(labels.max()) + 1 if m else 0
    if not np.array_equal(np.unique(labels), np.arange(interfaces)):
        raise ValueError('constraint_interfaces labels must be contiguous from zero')
    try:
        references = tuple(scales)
    except TypeError as exc:
        raise ValueError('scales must supply one ResidualScales per RHS') from exc
    if len(references) != nrhs or any(not isinstance(s, ResidualScales) for s in references):
        raise ValueError('scales must supply one ResidualScales per RHS')
    for scale in references:
        if scale.interface_displacements and len(scale.interface_displacements) != interfaces:
            raise ValueError('interface_displacements must have exactly one reference per interface')

    cases = []
    with np.errstate(divide='ignore', over='ignore', invalid='ignore', under='ignore'):
        interface_forces = np.asarray(C.T @ lam)
        residual = np.asarray(P.T @ (K @ u + interface_forces - forces))
        constraint_residual = np.asarray(C @ u) - affine[:, None]
        legacy_e_scale = np.asarray(abs(P.T) @ (abs(K) @ abs(u) + abs(interface_forces) + abs(forces)))
        legacy_c_scale = np.asarray(abs(C) @ abs(u)) + abs(affine[:, None])
        legacy_e = abs(residual) / np.maximum(legacy_e_scale, np.finfo(float).tiny)
        legacy_c = abs(constraint_residual) / np.maximum(legacy_c_scale, 1e-14)
        _computed_finite(interface_forces, residual, constraint_residual, legacy_e_scale,
                         legacy_c_scale, legacy_e, legacy_c)

        for case, scale in enumerate(references):
            dimension = np.ones(n)
            dimension[rotations] = scale.length
            DP = sparse.diags(dimension) @ P
            column_scales = np.asarray(abs(DP).max(axis=0).toarray()).ravel() if P.shape[1] else np.empty(0)
            if np.any(column_scales == 0) or not np.isfinite(column_scales).all():
                raise ValueError('each reduced P column must have a finite nonzero physical scale')
            invs = sparse.diags(1 / column_scales)
            invD = sparse.diags(1 / dimension)
            A = invs @ P.T @ K @ invD
            B = invs @ P.T @ C.T
            CD = C @ invD
            scaled_u = dimension * u[:, case]
            scaled_force = np.asarray(invs @ P.T @ forces[:, case])
            scaled_residual = residual[:, case] / column_scales
            local_e = _ratios(abs(residual[:, case]), column_scales * scale.force)
            interface_refs = scale.interface_displacements or (scale.displacement,) * interfaces
            row_refs = np.asarray(interface_refs)[labels] if m else np.empty(0)
            local_c_denominator = np.asarray(abs(CD).sum(axis=1)).ravel() * row_refs
            _computed_finite(A, B, CD, scaled_u, scaled_force, scaled_residual,
                             local_c_denominator, column_scales * scale.force)
            local_c = _ratios(abs(constraint_residual[:, case]), local_c_denominator)
            global_e_denominator = (_matrix_norm(A) * _norm(scaled_u)
                                    + _matrix_norm(B) * _norm(lam[:, case]) + _norm(scaled_force))
            global_c_denominator = _matrix_norm(CD) * _norm(scaled_u) + _norm(affine)
            _computed_finite(global_e_denominator, global_c_denominator)
            global_e = float(_ratios(_norm(scaled_residual), global_e_denominator))
            global_c = float(_ratios(_norm(constraint_residual[:, case]), global_c_denominator))
            equilibrium = max(_max(local_e), global_e)
            constraint = max(_max(local_c), global_c)
            cases.append({
                'case': int(case), 'passed': bool(equilibrium <= TOLERANCE and constraint <= TOLERANCE),
                'normalized_equilibrium': float(equilibrium), 'normalized_constraint_error': float(constraint),
                'local_equilibrium': local_e.tolist(), 'local_constraint_error': local_c.tolist(),
                'normwise_equilibrium': global_e, 'normwise_constraint_error': global_c,
                'legacy_componentwise_equilibrium': _max(legacy_e[:, case]),
                'legacy_componentwise_constraint_error': _max(legacy_c[:, case]),
                'absolute_free_residual_max': _norm(residual[:, case]),
                'absolute_constraint_residual_max': _norm(constraint_residual[:, case]),
                'equilibrium_residual': residual[:, case].tolist(),
                'constraint_residual': constraint_residual[:, case].tolist(),
                'offending_equilibrium_indices': np.flatnonzero(local_e > TOLERANCE).tolist(),
                'offending_constraint_indices': np.flatnonzero(local_c > TOLERANCE).tolist(),
                'references': {'length': scale.length, 'force': scale.force,
                               'displacement': scale.displacement,
                               'interface_displacements': list(interface_refs),
                               'constraint_interfaces': labels.tolist(),
                               'native_rotation_dofs': rotations.tolist()},
                'reduced_column_scales': column_scales.tolist(),
                'local_constraint_denominators': local_c_denominator.tolist(),
                'normwise_equilibrium_denominator': float(global_e_denominator),
                'normwise_constraint_denominator': float(global_c_denominator),
            })
    return {
        'policy': 'registered_physical_v2', 'tolerance': TOLERANCE,
        'passed': bool(all(case['passed'] for case in cases)),
        'normalized_equilibrium': max((c['normalized_equilibrium'] for c in cases), default=0.),
        'normalized_constraint_error': max((c['normalized_constraint_error'] for c in cases), default=0.),
        'legacy_componentwise_equilibrium': _max(legacy_e),
        'legacy_componentwise_constraint_error': _max(legacy_c),
        'absolute_free_residual_max': _norm(residual),
        'absolute_constraint_residual_max': _norm(constraint_residual),
        'offending_equilibrium_indices': [{'case': c['case'], 'index': i} for c in cases for i in c['offending_equilibrium_indices']],
        'offending_constraint_indices': [{'case': c['case'], 'index': i} for c in cases for i in c['offending_constraint_indices']],
        'per_case': cases,
    }
