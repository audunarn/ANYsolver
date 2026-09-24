"""Supported spectral-element x basis for the exploratory F03 shell.

The breaks are the longitudinal ends swept by the four material samples.
This is a classical plane-stress reference basis, not an E4-PL operator.
"""

from __future__ import annotations

import numpy as np
from numpy.polynomial import legendre


BREAKS = (-.5, -.2, .2, .8, 1.2, 1.5)


class SegmentedXBasis:
    """C0 Lobatto elements with zero fields at both supported x edges."""

    __slots__ = ("degree", "_coefficients", "_nodes")

    def __init__(self, degree: int):
        if type(degree) is not int or not 1 <= degree <= 24:
            raise ValueError("bounded segmented longitudinal degree required")
        interior = (legendre.Legendre.basis(degree).deriv().roots()
                    if degree > 1 else np.empty(0))
        local = np.r_[-1., interior, 1.]
        if len(local) != degree+1 or np.any(np.diff(local) <= 0):
            raise ValueError("invalid Lobatto longitudinal nodes")
        coefficient = np.linalg.inv(legendre.legvander(local, degree))
        nodes = []
        for segment, (a,b) in enumerate(zip(BREAKS[:-1],BREAKS[1:])):
            physical = a+(local+1)*(b-a)/2
            nodes.extend(physical if segment == 0 else physical[1:])
        self.degree = degree
        self._coefficients = tuple(tuple(float(v) for v in row)
                                   for row in coefficient)
        self._nodes = tuple(float(x) for x in nodes)

    @property
    def size(self) -> int:
        return 5*self.degree-1

    @property
    def nodes(self) -> tuple[float,...]:
        return self._nodes[1:-1]

    def _local(self, t: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
        coefficient = np.asarray(self._coefficients)
        values = legendre.legvander(t,self.degree)@coefficient
        derivative_coefficients = np.column_stack(
            [legendre.legder(coefficient[:,j]) for j in range(self.degree+1)])
        derivatives = legendre.legvander(t,self.degree-1)@derivative_coefficients
        return values,derivatives

    def _full(self, x: float) -> tuple[np.ndarray,np.ndarray]:
        if not np.isfinite(x) or not BREAKS[0] <= x <= BREAKS[-1]:
            raise ValueError("longitudinal sample outside reference panel")
        segment = min(max(int(np.searchsorted(BREAKS,x,side="right")-1),0),4)
        a,b = BREAKS[segment:segment+2]
        t = np.array([2*(x-a)/(b-a)-1])
        values, derivatives = self._local(t)
        full_values = np.zeros(self.size+2)
        full_derivatives = np.zeros(self.size+2)
        sl = slice(segment*self.degree,segment*self.degree+self.degree+1)
        full_values[sl] = values[0]
        full_derivatives[sl] = 2/(b-a)*derivatives[0]
        return full_values,full_derivatives

    def values(self, x: float) -> np.ndarray:
        return self._full(x)[0][1:-1]

    def derivatives(self, x: float) -> np.ndarray:
        """Physical derivative, right-sided at internal breaks."""
        return self._full(x)[1][1:-1]

    def edge_derivatives(self, side: int) -> np.ndarray:
        if side not in (0,1):
            raise ValueError("edge side must be 0 or 1")
        return self.derivatives(BREAKS[-1] if side else BREAKS[0])

    def matrices(self) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
        """Physical ∫XX, ∫X'X', and ∫X'X for free coefficients."""
        full=self.size+2
        mass=np.zeros((full,full))
        derivative=np.zeros((full,full))
        mixed=np.zeros((full,full))
        roots,weights=legendre.leggauss(self.degree+2)
        values,dvalues=self._local(roots)
        for segment,(a,b) in enumerate(zip(BREAKS[:-1],BREAKS[1:])):
            length=b-a
            ids=np.arange(segment*self.degree,segment*self.degree+self.degree+1)
            mass[np.ix_(ids,ids)] += length/2*(values.T*weights)@values
            derivative[np.ix_(ids,ids)] += 2/length*(dvalues.T*weights)@dvalues
            mixed[np.ix_(ids,ids)] += (dvalues.T*weights)@values
        return mass[1:-1,1:-1],derivative[1:-1,1:-1],mixed[1:-1,1:-1]

    def crossing_stations(self, offsets: tuple[tuple[float,float],...]
                          ) -> np.ndarray:
        """Material stations where a sample crosses an x-element boundary."""
        return np.unique([station for dx,_ in offsets for edge in BREAKS
                          if 0 < (station := edge-dx) < 1])
