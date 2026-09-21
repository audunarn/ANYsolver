"""Reduced-space rank inventory for F03-K1; no KKT or F03 acceptance."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import linalg

from _b3_e4_f03_native_fixture import build
from _b3_e4_f03_shell_trace import make_shell
from probe_b3_ge_e4_pl_g0_f03_kkt import (
    assemble, reference_consistency, scales,
)


NAMES = ('p0-beam','p0-shell-grid','p1-shell-grid',
         'p1-beam-coarse','p1-beam')
CORE_RATIOS = (.5,1.,2.)
REACH_RATIOS = (.125,.25,4.,8.)
MESHES = tuple((topology,n,int(n*ratio))
               for topology in ('Q4','S3-V2D')
               for ratio in CORE_RATIOS for n in (4,8,16)) + tuple(
                   (topology,8,int(8*ratio))
                   for topology in ('Q4','S3-V2D')
                   for ratio in REACH_RATIOS)


@dataclass(frozen=True)
class RankSpace:
    name: str
    basis_knots: np.ndarray

    @property
    def dimension(self) -> int:
        return len(self.basis_knots)-(1 if self.name.startswith('p0-') else 0)

    def at(self, s: float, *, side: str = 'left') -> np.ndarray:
        knots=self.basis_knots
        if side not in ('left','right'):
            raise ValueError('invalid side')
        i=int(np.clip(np.searchsorted(knots,s,side=side)-1,0,len(knots)-2))
        result=np.zeros(self.dimension)
        if self.name.startswith('p0-'):
            result[i]=1.
        else:
            t=(s-knots[i])/(knots[i+1]-knots[i])
            result[i:i+2]=(1.-t,t)
        return result


def candidate_spaces(beam,shell) -> tuple[RankSpace,...]:
    nb=beam.n_half_cells
    ns=shell.n_s
    # Clip actual panel x-grid edges to [0,1]; at Ns=1 an x=.5 edge
    # produces two physical shell intervals rather than one.
    x=-.5+np.arange(shell.x_interval_count+1,dtype=float)/ns
    shell_grid=np.r_[0.,x[(x > 0.) & (x < 1.)],1.]
    definitions=(
        (NAMES[0],np.linspace(0.,1.,nb+1)),
        (NAMES[1],shell_grid),
        (NAMES[2],shell_grid),
        (NAMES[3],np.linspace(0.,1.,nb//2+1)),
        (NAMES[4],np.linspace(0.,1.,nb+1)),
    )
    result=tuple(RankSpace(name,knots) for name,knots in definitions)
    for space in result:
        if (len(space.basis_knots) < 2
                or not np.all(np.diff(space.basis_knots) > 0)
                or space.basis_knots[0] != 0.
                or space.basis_knots[-1] != 1.
                or abs(np.sum(space.at(.371))-1.) > 1e-14):
            raise AssertionError('invalid K1 multiplier basis')
    return result


def rank_measure(beam,shell,space):
    result={'space':space.name,'basis_knots':space.basis_knots.tolist(),
            'basis_dimension':space.dimension,
            'constraint_rows':3*space.dimension}
    try:
        coupling=assemble(beam,shell,space)
    except ValueError as exc:
        if str(exc) != 'quadrature reference norm zero or nonfinite':
            raise
        result.update(status='INVALID_QUADRATURE_REFERENCE',
                      failure_type=type(exc).__name__,failure=str(exc))
        return result
    mass=coupling.mass
    reference=reference_consistency(beam,shell,coupling)
    result.update(
            integration_knots=coupling.integration_knots.tolist(),
            reference_consistency=reference,
            quadrature_error=coupling.quadrature_error,
            max_row_incidence=coupling.max_row_incidence)
    if not np.all(np.isfinite(mass)):
        result.update(status='MASS_INVALID',failure_type='NonfiniteMass',
                      failure='nonfinite multiplier mass')
        return result
    result['mass_symmetry_error']=float(np.linalg.norm(mass-mass.T)/
        max(np.linalg.norm(mass),np.finfo(float).tiny))
    try:
        chol=linalg.cholesky(mass,lower=True,check_finite=True)
    except linalg.LinAlgError as exc:
        result.update(status='MASS_INVALID',failure_type=type(exc).__name__,
                      failure=str(exc))
        return result
    sq,_=scales(beam,shell,coupling.matrix.shape[0])
    whitened=linalg.solve_triangular(
        chol,coupling.matrix.toarray()*sq[None,:],lower=True)
    row_singular=linalg.svdvals(whitened)
    trace_singular=linalg.svdvals(coupling.trace_factor*sq[None,:])
    if (len(row_singular) == 0 or len(trace_singular) == 0
            or row_singular[0] <= 0 or trace_singular[0] <= 0
            or not np.all(np.isfinite(row_singular))
            or not np.all(np.isfinite(trace_singular))):
        result['status']='INVALID_SINGULAR_REFERENCE'
        return result
    row_rank=int(np.count_nonzero(row_singular > 1e-10*row_singular[0]))
    trace_rank=int(np.count_nonzero(trace_singular > 1e-10*trace_singular[0]))
    result.update(row_singular=row_singular.tolist(),
                  trace_singular=trace_singular.tolist(),
                  row_rank=row_rank,trace_rank=trace_rank,
                  unsupported_trace_modes=trace_rank-row_rank,
                  minimum_row_singular_ratio=float(
                      row_singular[-1]/row_singular[0]))
    good=(reference['max_translation_m'] <= 1e-12
          and reference['max_rotation_rad'] <= 1e-12
          and all(np.isfinite(value) and value <= 1e-10
                  for value in coupling.quadrature_error.values())
          and result['mass_symmetry_error'] <= 1e-10)
    result['status']=('TRACE_RANK_INCONSISTENT' if trace_rank < row_rank else
                      'INVALID_REFERENCE_OR_QUADRATURE' if not good else
                      'ROW_RANK_LOSS' if row_rank < coupling.matrix.shape[0] else
                      'FULL_ROW_RANK_WITH_TRACE_MODES'
                      if trace_rank > row_rank else
                      'FULL_ROW_RANK_NO_TRACE_MODES')
    return result


def screen_mesh(topology: str, n_beam: int, n_shell: int):
    beam=build(n_beam)
    shell=make_shell(n_shell,topology)
    return {'topology':topology,'n_beam':n_beam,'n_shell':n_shell,
            'shell':shell.diagnostics(),
            'native_physical_count':len(beam.physical),
            'native_retained_count':len(beam.internal),
            'native_assembly_parity':beam.dense_oracle_max_error,
            'cases':[rank_measure(beam,shell,space)
                     for space in candidate_spaces(beam,shell)]}
