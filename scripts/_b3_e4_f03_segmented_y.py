"""Continuous spectral-element transverse basis aligned to F03 sample lines.

The base physical intervals meet at y=+-0.23 m. Optional midpoint splitting
preserves those material lines. Displacement is continuous while transverse
derivatives may jump. This is a classical-shell basis, not E4-PL.
"""

from __future__ import annotations

import numpy as np
from numpy.polynomial import legendre


BREAKS = (-.5, -.23, .23, .5)


class SegmentedYBasis:
    """Conforming Lobatto elements, optionally with midpoint h refinement."""

    __slots__ = ("degree", "subdivisions", "_breaks", "_local_nodes",
                 "_coefficients", "_global_nodes")

    def __init__(self, degree: int, subdivisions: int = 1):
        if type(degree) is not int or not 1 <= degree <= 24:
            raise ValueError("bounded segmented transverse degree required")
        if type(subdivisions) is not int or subdivisions not in (1,2):
            raise ValueError("bounded transverse subdivision required")
        breaks = [BREAKS[0]]
        for a,b in zip(BREAKS[:-1],BREAKS[1:]):
            if subdivisions == 2:
                breaks.append((a+b)/2)
            breaks.append(b)
        interior = (legendre.Legendre.basis(degree).deriv().roots()
                    if degree > 1 else np.empty(0))
        local = np.r_[-1., interior, 1.]
        if len(local) != degree+1 or np.any(np.diff(local) <= 0):
            raise ValueError("invalid Lobatto transverse nodes")
        coefficient = np.linalg.inv(legendre.legvander(local, degree))
        nodes = []
        for segment, (a,b) in enumerate(zip(breaks[:-1],breaks[1:])):
            physical = a+(local+1)*(b-a)/2
            nodes.extend(physical if segment == 0 else physical[1:])
        self.degree = degree
        self.subdivisions = subdivisions
        self._breaks = tuple(float(v) for v in breaks)
        self._local_nodes = tuple(float(x) for x in local)
        self._coefficients = tuple(tuple(float(v) for v in row)
                                   for row in coefficient)
        self._global_nodes = tuple(float(y) for y in nodes)

    @property
    def size(self) -> int:
        return 3*self.subdivisions*self.degree+1

    @property
    def breaks(self) -> tuple[float,...]:
        return self._breaks

    @property
    def nodes(self) -> tuple[float,...]:
        return self._global_nodes

    def _evaluation(self, t: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
        coefficient = np.asarray(self._coefficients)
        values = legendre.legvander(t,self.degree)@coefficient
        derivative_coefficients = np.column_stack(
            [legendre.legder(coefficient[:,j]) for j in range(self.degree+1)])
        derivatives = legendre.legvander(t,self.degree-1)@derivative_coefficients
        return values,derivatives

    def values(self, y: float) -> np.ndarray:
        if not np.isfinite(y) or not self._breaks[0] <= y <= self._breaks[-1]:
            raise ValueError("transverse sample outside reference panel")
        segment = min(max(int(np.searchsorted(self._breaks,y,side="right")-1),0),
                      len(self._breaks)-2)
        a,b = self._breaks[segment:segment+2]
        t = np.array([2*(y-a)/(b-a)-1])
        local,_ = self._evaluation(t)
        result = np.zeros(self.size)
        result[segment*self.degree:segment*self.degree+self.degree+1] = local[0]
        return result

    def matrices(self) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
        """Physical ∫NN, ∫N'N', and ∫NN' over the admitted intervals."""
        n=self.size
        mass=np.zeros((n,n))
        derivative=np.zeros((n,n))
        mixed=np.zeros((n,n))
        roots,weights=legendre.leggauss(self.degree+2)
        values,dvalues=self._evaluation(roots)
        for segment,(a,b) in enumerate(zip(self._breaks[:-1],self._breaks[1:])):
            length=b-a
            ids=np.arange(segment*self.degree,segment*self.degree+self.degree+1)
            mass[np.ix_(ids,ids)] += length/2*(values.T*weights)@values
            derivative[np.ix_(ids,ids)] += 2/length*(dvalues.T*weights)@dvalues
            mixed[np.ix_(ids,ids)] += (values.T*weights)@dvalues
        return mass,derivative,mixed

    def moments(self) -> tuple[np.ndarray,np.ndarray]:
        """Exact-in-space integral weights for 1 and y in this P1-complete space."""
        mass,_,_=self.matrices()
        return mass@np.ones(self.size),mass@np.asarray(self._global_nodes)
