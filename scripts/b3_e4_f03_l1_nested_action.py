"""Whole-space L1 multiplier injection on a fixed material line.

This bounded algebra check covers the two surviving six-channel development
spaces on nested two-, four-, eight-, and sixteen-edge grids over [0.5, 1] m. It proves
identity of sampled multiplier density and quadrature work for every coarse
coefficient and every fine station gap. It does not construct a reference
stiffness, establish convergence, or assess F03 stability.
"""

from __future__ import annotations

from dataclasses import dataclass
import json

import numpy as np
from scipy.linalg import block_diag


A = "P1_translation_twist_P0_pitch_normal"
B = "P0_translation_twist_pair_P0_pitch_normal"
SPACES = (A, B)


@dataclass(frozen=True)
class Grid:
    cuts: np.ndarray
    stations: np.ndarray
    weights: np.ndarray

    @property
    def segments(self) -> int:
        return len(self.cuts) - 1


def grid(segments: int, *, start: float = .5, end: float = 1.) -> Grid:
    """Two-point Gauss cuts for a bounded, consistently oriented straight line."""
    if (type(segments) is not int or segments not in (2, 4, 8, 16) or
            not np.isfinite((start, end)).all() or end <= start):
        raise ValueError("bounded ordered 2/4/8/16-edge reference grid required")
    cuts = np.linspace(start, end, segments + 1)
    alpha = (.5 - .5 / np.sqrt(3.), .5 + .5 / np.sqrt(3.))
    stations = np.array([cuts[edge] + fraction * (cuts[edge+1]-cuts[edge])
                         for edge in range(segments) for fraction in alpha])
    weights = np.repeat(np.diff(cuts) / 2., 2)
    for array in (cuts, stations, weights):
        array.setflags(write=False)
    return Grid(cuts, stations, weights)


def samples(cuts: np.ndarray, stations: np.ndarray, space: str) -> np.ndarray:
    """Evaluate one complete six-channel multiplier basis at material stations."""
    cuts = np.asarray(cuts, dtype=float)
    stations = np.asarray(stations, dtype=float)
    n = len(cuts) - 1
    if (space not in SPACES or n not in (2, 4, 8, 16) or n % 2 or
            cuts.ndim != 1 or stations.ndim != 1 or
            not np.isfinite(cuts).all() or not np.isfinite(stations).all() or
            not np.all(np.diff(cuts) > 0.)):
        raise ValueError("ordered even-edge six-channel basis required")
    edge = np.searchsorted(cuts, stations, side="right") - 1
    if (np.any(edge < 0) or np.any(edge >= n) or
            np.any(stations <= cuts[edge]) or
            np.any(stations >= cuts[edge+1])):
        raise ValueError("all samples must lie strictly inside material edges")
    fraction = (stations-cuts[edge])/(cuts[edge+1]-cuts[edge])
    hat = np.zeros((len(stations), n+1))
    cell = np.zeros((len(stations), n))
    patch = np.zeros((len(stations), n//2))
    row = np.arange(len(stations))
    hat[row, edge], hat[row, edge+1] = 1.-fraction, fraction
    cell[row, edge] = 1.
    patch[row, edge//2] = 1.
    bases = ([hat]*4+[cell]*2 if space == A else [cell]*4+[patch]*2)
    columns = sum(base.shape[1] for base in bases)
    out = np.zeros((6*len(stations), columns))
    begin = 0
    for channel, basis in enumerate(bases):
        width = basis.shape[1]
        out[channel::6, begin:begin+width] = basis
        begin += width
    return out


def injection(coarse: Grid, fine: Grid, space: str) -> np.ndarray:
    """Represent every coarse multiplier function exactly in the fine basis."""
    nc, nf = coarse.segments, fine.segments
    if (space not in SPACES or nf != 2*nc or
            not np.array_equal(fine.cuts[::2], coarse.cuts)):
        raise ValueError("nested same-line doubling and admitted space required")
    parent_node = np.minimum(
        np.searchsorted(coarse.cuts, fine.cuts, side="right")-1, nc-1)
    fraction = ((fine.cuts-coarse.cuts[parent_node]) /
                (coarse.cuts[parent_node+1]-coarse.cuts[parent_node]))
    node = np.zeros((nf+1, nc+1))
    rows = np.arange(nf+1)
    node[rows, parent_node], node[rows, parent_node+1] = 1.-fraction, fraction

    parent_edge = np.searchsorted(
        coarse.cuts, (fine.cuts[:-1]+fine.cuts[1:])/2.,
        side="right")-1
    edge = np.zeros((nf, nc))
    edge[np.arange(nf), parent_edge] = 1.

    coarse_patch_cuts = coarse.cuts[::2]
    fine_patch_midpoint = (fine.cuts[::2][:-1]+fine.cuts[::2][1:])/2.
    parent_patch = np.searchsorted(
        coarse_patch_cuts, fine_patch_midpoint, side="right")-1
    patch = np.zeros((nf//2, nc//2))
    patch[np.arange(nf//2), parent_patch] = 1.
    blocks = ([node]*4+[edge]*2 if space == A else [edge]*4+[patch]*2)
    return block_diag(*blocks)


def work_map(coarse: Grid, fine: Grid, space: str) -> tuple[np.ndarray, np.ndarray]:
    """Return the two maps acting on arbitrary fine six-channel gap samples."""
    j = injection(coarse, fine, space)
    weighted = np.repeat(fine.weights, 6)
    fine_basis = samples(fine.cuts, fine.stations, space)
    coarse_on_fine = samples(coarse.cuts, fine.stations, space)
    return (j.T @ (fine_basis.T * weighted),
            coarse_on_fine.T * weighted)


def report() -> list[dict]:
    """Small algebraic results, not a compliance or stability score."""
    results = []
    for nc in (2, 4, 8):
        coarse, fine = grid(nc), grid(2*nc)
        for space in SPACES:
            j = injection(coarse, fine, space)
            coarse_on_fine = samples(coarse.cuts, fine.stations, space)
            fine_samples = samples(fine.cuts, fine.stations, space)
            left, right = work_map(coarse, fine, space)
            results.append({
                "coarse_edges": nc, "fine_edges": 2*nc, "space": space,
                "line_interval_m": [float(coarse.cuts[0]),
                                    float(coarse.cuts[-1])],
                "coarse_coefficients": int(j.shape[1]),
                "fine_coefficients": int(j.shape[0]),
                "whole_basis_sample_error": float(np.max(np.abs(
                    fine_samples @ j - coarse_on_fine))),
                "whole_space_work_map_error": float(np.max(np.abs(left-right))),
            })
    return results


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
