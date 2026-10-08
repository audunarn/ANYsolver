"""Bounded endpoint/interior-moment operators for the classical finite pad.

This is a diagnostic discretization of the *same* continuous line gap, not a
production connection or a qualification. It replaces the two boundary P1
moment rows with exact gap evaluations at s=0 and s=1. The resulting finite
constraint space is different from the original full P1 mortar space.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy import sparse

import _b3_e4_f03_area_line as line
import _b3_e4_f03_area_port as port
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as original
import _b3_e4_f03_independent_shell as shell


@dataclass(frozen=True)
class HybridOperators:
    """Positive shell/beam traces; signed gap matrix is ``[-cs, cb]``.

    Row order is the three physical channels (x,y,scaled yaw) at each
    interior P1 index 1..Nm-1, then three at root s=0, then three at tip
    s=1. The yaw row uses ell=.46 m on both traces. There are 3(Nm+1)
    rows. Interior rows integrate gap against P1 hats (units m² on the
    one-metre physical line); endpoint rows evaluate gap (units m).
    ``row_measures`` is h metres for each interior channel and numerical 1
    for endpoint evaluation. Physical interior multiplier coefficients have
    units N/m; endpoint atoms have units N. A diagonal KKT normalization
    must therefore use U0*h for interior rows and U0 for endpoint rows.
    """

    cs: sparse.csr_matrix
    cb: sparse.csr_matrix
    overlay: np.ndarray
    row_measures: np.ndarray
    n_mortar: int
    lifted: bool

    @property
    def interior_count(self) -> int:
        return self.n_mortar-1

    @property
    def root_rows(self) -> slice:
        offset=3*self.interior_count
        return slice(offset,offset+3)

    @property
    def tip_rows(self) -> slice:
        offset=3*self.n_mortar
        return slice(offset,offset+3)


def _admitted(n_mortar: int) -> int:
    if isinstance(n_mortar,bool) or not isinstance(n_mortar,int) or not 2<=n_mortar<=16:
        raise ValueError('hybrid requires 2..16 mortar cells')
    return n_mortar


def _endpoints(model: shell.Panel, n_beam: int, halfwidth: float
               ) -> tuple[sparse.csr_matrix,sparse.csr_matrix]:
    scale=sparse.diags((1.,1.,original.YAW_LENGTH),format='csr')
    cs=sparse.vstack((scale@port.pose(model,0.,halfwidth),
                      scale@port.pose(model,1.,halfwidth)),format='csr')
    cb=sparse.vstack((scale@beam.trace(n_beam,0.),
                      scale@beam.trace(n_beam,1.)),format='csr')
    return cs,cb


def assemble(model: shell.Panel, n_beam: int, n_mortar: int,
             halfwidth: float, *, lifted: bool = False,
             order: int = 6) -> HybridOperators:
    """Build unlifted or locally lifted exact-endpoint/line-gap rows.

    The local lift subtracts ``phi_0(s)*g(0)+phi_Nm(s)*g(1)`` from the
    interior moment integrands. On uniform cells the only overlap is h/6
    with the adjacent interior hat (both corrections hit i=1 for Nm=2).
    It is an invertible triangular row change within this hybrid, and does
    not transform the original full-P1 constraint into this hybrid.
    """
    _admitted(n_mortar)
    if (not isinstance(model,shell.Panel) or
            isinstance(n_beam,bool) or not isinstance(n_beam,int) or
            not isinstance(lifted,bool) or
            not np.all(np.isfinite(model.nodes)) or
            not isinstance(order,int) or isinstance(order,bool) or
            not 4<=order<=10 or not math.isfinite(halfwidth)):
        raise ValueError('invalid hybrid panel, beam, pad or quadrature')
    beam.dof_count(n_beam)
    cs_full,cb_full,knots=line.coupling(
        model,n_beam,n_mortar,'P1',halfwidth,order)
    interior=np.arange(3,3*n_mortar,dtype=int)
    cs_end,cb_end=_endpoints(model,n_beam,halfwidth)
    cs_inner=cs_full[interior,:]
    cb_inner=cb_full[interior,:]
    if lifted:
        h=1/n_mortar
        correction=sparse.lil_matrix((3*(n_mortar-1),6))
        for channel in range(3):
            correction[channel,channel]=h/6
            correction[3*(n_mortar-2)+channel,3+channel]=h/6
        correction=correction.tocsr()
        cs_inner=cs_inner-correction@cs_end
        cb_inner=cb_inner-correction@cb_end
    cs=sparse.vstack((cs_inner,cs_end),format='csr')
    cb=sparse.vstack((cb_inner,cb_end),format='csr')
    measures=np.r_[np.full(3*(n_mortar-1),1/n_mortar),np.ones(6)]
    if (cs.shape!=(3*(n_mortar+1),model.dof_count) or
            cb.shape!=(3*(n_mortar+1),beam.dof_count(n_beam)) or
            not np.all(np.isfinite(cs.data)) or
            not np.all(np.isfinite(cb.data)) or
            not np.all(np.isfinite(measures))):
        raise ValueError('invalid finite hybrid operator')
    return HybridOperators(cs,cb,knots,measures,n_mortar,lifted)


def to_physical_multipliers(lifted_multipliers: np.ndarray,
                            n_mortar: int) -> np.ndarray:
    """Map lifted coefficients to interior line density and endpoint atoms.

    Both arrays use row order [interior hats, root atom, tip atom]. The
    returned root/tip coefficients include the h/6 adjacent-hat correction;
    the line coefficients are unchanged. Work and full physical adjoints
    are invariant under this map paired with the lifted operator.
    """
    n=_admitted(n_mortar)
    value=np.asarray(lifted_multipliers,dtype=float)
    if value.shape!=(3*(n+1),) or not np.all(np.isfinite(value)):
        raise ValueError('invalid lifted multiplier vector')
    physical=value.copy()
    physical[3*(n-1):3*n]-=value[:3]/(6*n)
    physical[3*n:3*(n+1)]-=value[3*(n-2):3*(n-1)]/(6*n)
    return physical


def from_physical_multipliers(physical_multipliers: np.ndarray,
                              n_mortar: int) -> np.ndarray:
    """Inverse map from line-density coefficients and endpoint atoms."""
    n=_admitted(n_mortar)
    value=np.asarray(physical_multipliers,dtype=float)
    if value.shape!=(3*(n+1),) or not np.all(np.isfinite(value)):
        raise ValueError('invalid physical multiplier vector')
    lifted=value.copy()
    lifted[3*(n-1):3*n]+=value[:3]/(6*n)
    lifted[3*n:3*(n+1)]+=value[3*(n-2):3*(n-1)]/(6*n)
    return lifted
