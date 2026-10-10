"""Flat mixed Q4/S3 restriction of the declared F03 shell auxiliary H1 norm.

This independent development operator is a positive kinematic Riesz form, not
E4-PL stiffness. It does not change the BL5 law or select multiplier spaces.
The five fields at each node are (translation xyz, director variation xy).
Only flat reference directors and coordinate-selection supports are admitted.
"""
from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from scipy import sparse


def _triangle(coords: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    edges = np.stack((coords[1]-coords[0], coords[2]-coords[0]), axis=1)
    determinant = float(np.linalg.det(edges))
    floor = 32*np.finfo(float).eps*float(np.sum(edges**2))
    if not np.isfinite(determinant) or determinant <= floor:
        raise ValueError("positively oriented, nondegenerate S3 required")
    area = determinant/2.
    derivatives = np.array(((-1., -1.), (1., 0.), (0., 1.)))
    gradient = derivatives@np.linalg.inv(edges)
    mass = area*(np.ones((3, 3))+np.eye(3))/12.
    gram = area*gradient@gradient.T
    return mass, gram, area


def _quad(coords: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    mass = np.zeros((4, 4))
    gram = np.zeros((4, 4))
    area = 0.
    station = 1./np.sqrt(3.)
    for xi in (-station, station):
        for eta in (-station, station):
            shape = np.array(((1-xi)*(1-eta), (1+xi)*(1-eta),
                              (1+xi)*(1+eta), (1-xi)*(1+eta)))/4.
            reference_gradient = np.array((
                (-(1-eta), -(1-xi)), (1-eta, -(1+xi)),
                (1+eta, 1+xi), (-(1+eta), 1-xi)))/4.
            jacobian = coords.T@reference_gradient
            determinant = float(np.linalg.det(jacobian))
            floor = 32*np.finfo(float).eps*float(np.sum(jacobian**2))
            if not np.isfinite(determinant) or determinant <= floor:
                raise ValueError("positively oriented, nondegenerate Q4 required")
            gradient = reference_gradient@np.linalg.inv(jacobian)
            mass += determinant*np.outer(shape, shape)
            gram += determinant*gradient@gradient.T
            area += determinant
    return mass, gram, area


def scalar_mixed_h1(nodes: np.ndarray, elements: Iterable[tuple[int, ...]],
                    ell: float) -> tuple[sparse.csc_matrix, float]:
    """Return area-normalized M + ell**2 G on actual S3/Q4 topology."""
    xy = np.asarray(nodes, dtype=float)
    if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 3 or not np.all(np.isfinite(xy)):
        raise ValueError("finite flat reference nodes required")
    if not np.isfinite(ell) or ell <= 0.:
        raise ValueError("positive frozen characteristic length required")
    entries: list[float] = []
    rows: list[int] = []
    cols: list[int] = []
    area = 0.
    used = 0
    seen: set[frozenset[int]] = set()
    touched: set[int] = set()
    for element in elements:
        ids = tuple(element)
        if (len(ids) not in (3, 4) or len(set(ids)) != len(ids) or
                any(type(i) is not int or i < 0 or i >= len(xy) for i in ids)):
            raise ValueError("valid S3/Q4 node indices required")
        identity = frozenset(ids)
        if identity in seen:
            raise ValueError("duplicate S3/Q4 element support")
        seen.add(identity)
        touched.update(ids)
        mass, gram, element_area = (_triangle(xy[list(ids)]) if len(ids) == 3
                                    else _quad(xy[list(ids)]))
        local = mass+ell**2*gram
        for i, row in enumerate(ids):
            for j, column in enumerate(ids):
                rows.append(row)
                cols.append(column)
                entries.append(float(local[i, j]))
        area += element_area
        used += 1
    if not used or area <= 0. or touched != set(range(len(xy))):
        raise ValueError("positive-area shell mesh using every declared node required")
    matrix = sparse.coo_matrix((entries, (rows, cols)),
                               shape=(len(xy), len(xy))).tocsc()/area
    return matrix, float(area)


def flat_shell_embedding(node_count: int) -> sparse.csc_matrix:
    """Map (u, eta) to actual (u, omega) with delta d = omega cross e_z."""
    if type(node_count) is not int or node_count <= 0:
        raise ValueError("positive node count required")
    local = sparse.coo_matrix((np.array((1., 1., 1., -1., 1.)),
        (np.array((0, 1, 2, 3, 4)), np.array((0, 1, 2, 4, 3)))),
        shape=(6, 5)).tocsc()
    return sparse.kron(sparse.eye(node_count, format="csc"), local,
                       format="csc")


def supported_shell_h1(nodes: np.ndarray, elements: Iterable[tuple[int, ...]],
                       ell: float, fixed_shell_coordinates: Iterable[tuple[int, int]]
                       ) -> tuple[sparse.csc_matrix, np.ndarray, sparse.csc_matrix]:
    """Restrict the five-field norm to supported physical coordinates.

    fixed_shell_coordinates use zero-based node and 0..5 translation/rotation
    components. Drilling component 5 has no auxiliary field. Affine supports
    require a separate physical map and are intentionally not inferred here.
    """
    xy = np.asarray(nodes, dtype=float)
    scalar, _ = scalar_mixed_h1(xy, elements, ell)
    local_scale = sparse.diags((1., 1., 1., ell**2, ell**2), format="csc")
    full = sparse.kron(scalar, local_scale, format="csc")
    fixed: set[int] = set()
    for node, component in fixed_shell_coordinates:
        if (type(node) is not int or type(component) is not int or
                not 0 <= node < len(xy) or not 0 <= component < 6):
            raise ValueError("known fixed shell coordinate required")
        mapped = (0, 1, 2, 4, 3, None)[component]
        if mapped is not None:
            fixed.add(5*node+mapped)
    active = np.array([i for i in range(5*len(xy)) if i not in fixed], dtype=int)
    if not len(active):
        raise ValueError("at least one supported auxiliary coordinate required")
    return full[active][:, active].tocsc(), active, flat_shell_embedding(len(xy))[:, active]
