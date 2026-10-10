"""Derived principal stresses from physically resolved symmetric stress tensors."""
from __future__ import annotations
from typing import Any, Mapping
import numpy as np

PRINCIPAL_COMPONENTS = ('principal_stresses_top', 'principal_stresses_bottom')
SHELL_LINEAR_COMPONENTS = ('membrane_xx', 'membrane_yy', 'membrane_xy',
                           'bending_xx', 'bending_yy', 'bending_xy', 'shear_xz', 'shear_yz')

def principal_stresses(tensor: Any) -> np.ndarray:
    """Return descending eigenvalues along the final axis, one tensor per station."""
    values = np.asarray(tensor, dtype=float)
    if values.shape[-2:] != (3, 3) or not np.all(np.isfinite(values)):
        raise ValueError('principal stresses require finite 3 by 3 tensors')
    if not np.allclose(values, np.swapaxes(values, -1, -2), rtol=1e-12, atol=1e-12):
        raise ValueError('principal stresses require symmetric tensors')
    symmetric = .5 * (values + np.swapaxes(values, -1, -2))
    return np.linalg.eigvalsh(symmetric)[..., ::-1].copy()

def shell_surface_tensor(record: Mapping[str, Any], surface: str) -> np.ndarray:
    """Physical local top/bottom tensors matching canonical shell surface recovery."""
    if surface not in ('top', 'bottom') or not all(name in record for name in SHELL_LINEAR_COMPONENTS):
        raise ValueError('physical shell surface stresses are unavailable; generalized resultants and beam envelopes cannot define a coherent tensor')
    mx, my, mxy, bx, by, bxy, sxz, syz = np.broadcast_arrays(*(np.asarray(record[name], dtype=float) for name in SHELL_LINEAR_COMPONENTS))
    sign = 1. if surface == 'top' else -1.
    tensor = np.zeros(mx.shape + (3, 3), dtype=float)
    tensor[..., 0, 0] = mx + sign*bx
    tensor[..., 1, 1] = my + sign*by
    tensor[..., 0, 1] = tensor[..., 1, 0] = mxy + sign*bxy
    tensor[..., 0, 2] = tensor[..., 2, 0] = sxz
    tensor[..., 1, 2] = tensor[..., 2, 1] = syz
    return tensor

def shell_principal_stresses(record: Mapping[str, Any], surface: str) -> np.ndarray:
    return principal_stresses(shell_surface_tensor(record, surface))
