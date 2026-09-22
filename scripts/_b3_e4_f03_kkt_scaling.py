"""Work-conjugate diagonal scaling of the classical F03 saddle equations.

The transformation is a congruence of the *same* physical KKT system,
not a penalty, changed constitutive law, or physical convergence result.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_shell as shell


L0=1.
F0=1e6
M0=F0*L0
U0=F0/(shell.E*shell.THICKNESS)  # W0=L0=1 m.
E0=F0*U0


@dataclass(frozen=True)
class ScaledSystem:
    matrix: sparse.csc_matrix
    rhs: np.ndarray
    physical_coordinate_scale: np.ndarray
    angular_free_mask: np.ndarray
    physical_multiplier_scale: np.ndarray
    energy_scale: float
    free_count: int

    def recover(self, solution: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
        if solution.shape!=(self.matrix.shape[0],) or not np.all(np.isfinite(solution)):
            raise ValueError('invalid scaled KKT solution')
        return (self.physical_coordinate_scale*solution[:self.free_count],
                self.physical_multiplier_scale*solution[self.free_count:])


def build(k: sparse.spmatrix, c: sparse.spmatrix, f: np.ndarray,
          free: np.ndarray, shell_dofs: int, n_beam: int,
          n_mortar: int, law: str) -> ScaledSystem:
    """Return Tᵀ A T/E0 and Tᵀ b/E0, with T=diag(D,E0 S)."""
    count=beam.dof_count(n_beam)
    if (k.shape!=(shell_dofs+count,)*2 or
            c.shape[1]!=k.shape[0] or f.shape!=(k.shape[0],) or
            free.ndim!=1 or len(free)==0 or
            np.any(free<0) or np.any(free>=k.shape[0]) or
            np.any(np.diff(free)<=0) or law not in ('P0','P1') or
            not 1<=n_mortar<=128 or
            c.shape[0]!=3*(n_mortar+(law=='P1'))):
        raise ValueError('invalid classical KKT scaling layout')
    local=free-shell_dofs
    u=2*n_beam+1
    v=2*(n_beam+1)
    angular=(local>=u+v) | ((local>=u)&(local<u+v)&((local-u)%2==1))
    d=np.where(angular,U0/L0,U0)
    measure=np.full(n_mortar+(law=='P1'),L0/n_mortar)
    if law=='P1':
        measure[[0,-1]]*=.5
    s=1/(U0*np.repeat(measure,3))
    kff=k[free,:][:,free]
    cf=c[:,free]
    kd=sparse.diags(d,format='csr')
    cs=sparse.diags(s,format='csr')
    primal=(kd@kff@kd)*(1/E0)
    constraint=cs@cf@kd
    matrix=sparse.bmat(((primal,constraint.T),
                        (constraint,None)),format='csc')
    rhs=np.r_[d*f[free]/E0,np.zeros(len(s))]
    if not np.all(np.isfinite(rhs)) or not np.all(np.isfinite(matrix.data)):
        raise ValueError('nonfinite scaled classical KKT')
    return ScaledSystem(matrix,rhs,d,angular,E0*s,E0,len(free))
