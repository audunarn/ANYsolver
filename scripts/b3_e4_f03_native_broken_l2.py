"""Bounded B3 broken-pose L2 versus stationary physical-energy diagnostic.

This tests a necessary continuity condition for a prospective six-channel
L2 line-density norm. It does not prove a mesh-uniform bound, select an F03
multiplier space, or condense native retained rotations in production.
"""

from __future__ import annotations

import json
import os

import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_native_fixture import SECTION_DIAGONAL, build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort


BOND = (.5, 1.)
CHARACTERISTIC_LENGTH = .1


def _physical_beam(fixture):
    """Eliminate only stationary generalized resultants; retain cell spins."""
    context = fixture.context
    h = fixture.tangent.toarray()
    p = np.concatenate([
        context.nodal_count+24*element+np.arange(6, 24)
        for element in range(len(context.elements))])
    x = np.setdiff1d(np.asarray(context.free, dtype=int), p)
    if len(x)+len(p) != len(context.free):
        raise AssertionError("supported native physical/resultant layout changed")
    xx, xp, pp = h[np.ix_(x, x)], h[np.ix_(x, p)], h[np.ix_(p, p)]
    stationary = linalg.cho_solve(
        linalg.cho_factor(-pp, lower=True, check_finite=True), -xp.T)
    k = xx-xp@stationary
    if np.linalg.norm(k-k.T, ord=np.inf) > 1e-10*max(
            1., np.linalg.norm(k, ord=np.inf)):
        raise AssertionError("stationary native physical operator is asymmetric")
    linalg.cho_factor(k, lower=True, check_finite=True)
    return x, p, k


def _pose_grams(fixture, x, order: int):
    """Integrate actual one-sided native port derivatives on each bond cell."""
    nodes, weights = np.polynomial.legendre.leggauss(order)
    grams = np.zeros((6, len(x), len(x)))
    state = fixture.context.initial.mechanical
    cuts = fixture.abscissae
    bond_length = BOND[1]-BOND[0]
    start = int(np.searchsorted(cuts, BOND[0]))
    if not np.array_equal(cuts[[start, -1]], np.asarray(BOND)):
        raise AssertionError("bond endpoints must be native material cuts")
    for half in range(start, fixture.n_half_cells):
        a, b = cuts[half:half+2]
        element, cell = divmod(half, 2)
        for node, weight in zip(nodes, weights):
            station = .5*((a+b)+(b-a)*node)
            port = NativeHalfCellSpatialPort(
                fixture.context, element, cell, .5*(node+1.))
            pose = port.tangent(state)[:, x].copy()
            pose[:3] /= CHARACTERISTIC_LENGTH
            factor = .5*(b-a)*weight/bond_length
            for channel in range(6):
                grams[channel] += factor*np.outer(pose[channel], pose[channel])
    return grams


def _upper(gram: np.ndarray, energy: np.ndarray) -> float:
    scale = 1./np.sqrt(np.diag(energy))
    return float(linalg.eigvalsh(
        scale[:, None]*gram*scale[None, :],
        scale[:, None]*energy*scale[None, :],
        check_finite=True)[-1])


def report(n_half_cells: int) -> dict:
    if n_half_cells not in (4, 8, 16):
        raise ValueError("bounded 4/8/16-half-cell native screen required")
    fixture = build(n_half_cells, z_offset=.0675, assemble=True)
    if fixture.dense_oracle_max_error is None or (
            fixture.dense_oracle_max_error > 1e-9):
        raise AssertionError("native sparse/dense operator parity lost")
    x, p, energy = _physical_beam(fixture)
    grams = _pose_grams(fixture, x, 3)
    check = _pose_grams(fixture, x, 4)
    error = float(np.max(np.abs(grams-check)))
    if error > 1e-11*max(1., float(np.max(np.abs(check)))):
        raise AssertionError("native trace quadrature disagrees")
    # For a straight member, each retained half-cell spin has a unit spatial
    # rotation trace throughout its own material cell and zero elsewhere.
    half = n_half_cells-1
    element, cell = divmod(half, 2)
    spin = fixture.context.nodal_count+24*element+3*cell
    local = np.flatnonzero(x == spin)
    expected = (fixture.abscissae[half+1]-
                fixture.abscissae[half])/(BOND[1]-BOND[0])
    if (len(local) != 1 or
            not np.isclose(grams[3, local[0], local[0]], expected,
                           atol=2e-14, rtol=0.)):
        raise AssertionError("broken native rotation trace measure changed")
    first = int(np.searchsorted(fixture.abscissae, BOND[0]))
    nodal_y = np.flatnonzero(x == 6*first+1)
    nodal_expected = ((fixture.abscissae[first+1]-
                       fixture.abscissae[first]) /
                      (3*(BOND[1]-BOND[0])*CHARACTERISTIC_LENGTH**2))
    if (len(nodal_y) != 1 or
            not np.isclose(grams[1, nodal_y[0], nodal_y[0]],
                           nodal_expected, atol=2e-13, rtol=0.)):
        raise AssertionError("native interpolated translation measure changed")
    upper = [_upper(gram, energy) for gram in grams]
    combined = _upper(np.sum(grams, axis=0), energy)
    scale = float(SECTION_DIAGONAL[0]*(BOND[1]-BOND[0]))
    return {
        "scope": "finite-grid native broken-L2 continuity screen; no F03 acceptance",
        "n_half_cells": n_half_cells,
        "physical_dofs": len(x),
        "stationary_resultant_dofs": len(p),
        "bond_m": list(BOND),
        "characteristic_length_m": CHARACTERISTIC_LENGTH,
        "quadrature_3_vs_4_max_abs": error,
        "sparse_dense_operator_max_abs": fixture.dense_oracle_max_error,
        "upper_trace_per_joule": combined,
        "upper_by_channel_per_joule": upper,
        "fixed_EA_times_bond_scale_J": scale,
        "scaled_upper_trace": combined*scale,
        "scaled_upper_by_channel": [value*scale for value in upper],
    }


if __name__ == "__main__":
    print(json.dumps({
        "requested_threads": {name: os.environ.get(name) for name in (
            "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
        "effective_blas_threads": [
            {"api": info["internal_api"], "threads": info["num_threads"]}
            for info in threadpool_info()],
        "cases": [report(n) for n in (4, 8, 16)],
    }, indent=2))
