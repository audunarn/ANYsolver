"""Development-only flat Q4 finite-support shell pose.

This line-indexed area patch is a distinct candidate from a local bonded
trace. It establishes bounded kinematics only; it is not a selected F03
connection, production attachment, or qualified E4 energy estimate.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from anysolver.corotational import rotation_matrix_from_vector
from scripts.b3_e4_f03_l1_physical_rail import (
    _owned, _unit, transverse_shape_integrals,
)


def _centred_longitudinal_weights(
        cuts: np.ndarray, bounds: tuple[float, float]) -> np.ndarray:
    """Integrate (x-centroid) times Q4 line shapes over a uniform patch."""
    left, right = bounds
    centroid = .5*(left+right)
    width = right-left
    result = np.zeros(len(cuts))
    gauss = (.5-.5/np.sqrt(3.), .5+.5/np.sqrt(3.))
    for cell, (a, b) in enumerate(zip(cuts[:-1], cuts[1:])):
        lo, hi = max(a, left), min(b, right)
        if hi <= lo:
            continue
        for t in gauss:
            x = lo+(hi-lo)*t
            shape_right = (x-a)/(b-a)
            weight = .5*(hi-lo)*(x-centroid)/width
            result[cell] += weight*(1.-shape_right)
            result[cell+1] += weight*shape_right
    if not np.isclose(result.sum(), 0., rtol=0., atol=2e-14):
        raise ArithmeticError("centred patch moment lost translation invariance")
    return _owned(result, (len(cuts),))


@dataclass(frozen=True)
class FlatQ4FiniteSupportPose:
    """One objective pose from a fixed physical area patch at material s.

    The uniform bounded window is a small diagnostic kernel. A production
    line law must separately decide its smooth kernel, endpoint ownership,
    footprint distinction, quadrature, and physical work bounds.
    """

    reference: np.ndarray
    station: float
    line_y: float
    thickness: float
    x_window: tuple[float, float]
    y_window: tuple[float, float]
    weights: np.ndarray
    moments: np.ndarray
    reference_centroid: np.ndarray
    reference_frame: np.ndarray
    reference_offset: np.ndarray
    covariance: float

    @classmethod
    def at_reference(
            cls, reference: np.ndarray, x_cuts: np.ndarray,
            y_cuts: np.ndarray, *, station: float, line_y: float,
            longitudinal_width: float, transverse_bounds: tuple[float, float],
            thickness: float) -> FlatQ4FiniteSupportPose:
        x = np.asarray(x_cuts, dtype=float)
        y = np.asarray(y_cuts, dtype=float)
        if (x.ndim != 1 or y.ndim != 1 or len(x) < 2 or len(y) < 2 or
                not np.isfinite(x).all() or not np.isfinite(y).all() or
                not np.all(np.diff(x) > 0.) or
                not np.all(np.diff(y) > 0.)):
            raise ValueError("ordered finite Q4 material cuts required")
        ref = _owned(reference, (len(x), len(y), 3))
        if (not np.allclose(ref[:, :, 0], x[:, None], rtol=0., atol=1e-14) or
                not np.allclose(ref[:, :, 1], y[None, :], rtol=0., atol=1e-14)
                or not np.allclose(ref[:, :, 2], 0., rtol=0., atol=1e-14)):
            raise ValueError("flat Cartesian Q4 reference required")
        if (not np.isfinite((station, line_y, longitudinal_width,
                             thickness)).all() or
                not x[0] <= station <= x[-1] or
                not y[0] <= line_y <= y[-1] or
                longitudinal_width <= 0. or thickness <= 0.):
            raise ValueError("positive finite material patch required")
        half = .5*longitudinal_width
        x_window = (max(float(x[0]), station-half),
                    min(float(x[-1]), station+half))
        if x_window[1]-x_window[0] <= 1e-10:
            raise ValueError("nondegenerate longitudinal support required")
        wx = transverse_shape_integrals(x, x_window)
        wy = transverse_shape_integrals(y, transverse_bounds)
        hx = _centred_longitudinal_weights(x, x_window)
        weights = _owned(wx[:, None]*wy[None, :], (len(x), len(y)))
        moments = _owned(hx[:, None]*wy[None, :], (len(x), len(y)))
        reference_top = ref.copy()
        reference_top[:, :, 2] += .5*thickness
        centroid = np.einsum("ij,ijk->k", weights, reference_top)
        longitudinal = np.einsum("ij,ijk->k", moments, reference_top)
        covariance = float(np.linalg.norm(longitudinal))
        if covariance <= 1e-12:
            raise ValueError("nondegenerate longitudinal covariance required")
        tangent = _unit(longitudinal, "reference patch tangent")
        normal = np.array((0., 0., 1.))
        frame = np.column_stack((tangent, np.cross(normal, tangent), normal))
        point = np.array((station, line_y, .5*thickness))
        return cls(ref, float(station), float(line_y), float(thickness),
                   tuple(float(v) for v in x_window),
                   tuple(float(v) for v in transverse_bounds),
                   weights, moments, _owned(centroid, (3,)),
                   _owned(frame, (3, 3)), _owned(point-centroid, (3,)),
                   covariance)

    def pose(self, total: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        q = _owned(total, (*self.reference.shape[:2], 6))
        directors = np.array([
            [rotation_matrix_from_vector(q[i, j, 3:])[:, 2]
             for j in range(q.shape[1])] for i in range(q.shape[0])])
        top = self.reference+q[:, :, :3]+.5*self.thickness*directors
        centroid = np.einsum("ij,ijk->k", self.weights, top)
        normal = _unit(
            np.einsum("ij,ijk->k", self.weights, directors),
            "averaged patch director")
        raw = np.einsum("ij,ijk->k", self.moments, top)
        tangent = _unit(raw-normal*(normal@raw),
                        "projected patch covariance")
        frame = np.column_stack((tangent, np.cross(normal, tangent), normal))
        position = centroid+frame@self.reference_frame.T@self.reference_offset
        return position, frame
