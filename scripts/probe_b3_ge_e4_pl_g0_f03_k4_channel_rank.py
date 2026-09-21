"""Unregistered planar channel-span falsification, not F03 evidence.

This bounded probe reuses independently assembled P1-beam translation and
P0-beam yaw rows. A Riesz dual changes basis but not this row space.
"""

from __future__ import annotations

from dataclasses import replace
import json

import numpy as np
from scipy import linalg, sparse

from _b3_e4_f03_native_fixture import build
from _b3_e4_f03_shell_trace import make_shell
from probe_b3_ge_e4_pl_g0_f03_k1_rank import candidate_spaces
from probe_b3_ge_e4_pl_g0_f03_kkt import (
    CandidateSingular, PrimalNotAdmissible, assemble,
    physical_support_balance, scales, solve_exact,
)
from probe_b3_ge_e4_pl_g0_f03_k2p import fixed_load, physical_stations, U


def screen(topology: str, n_beam: int, n_shell: int) -> dict:
    beam, shell = build(n_beam), make_shell(n_shell, topology)
    nb = beam.n_half_cells
    spaces = {space.name: space for space in candidate_spaces(beam, shell)}
    p1 = assemble(beam, shell, spaces['p1-beam'])
    p0 = assemble(beam, shell, spaces['p0-beam'])
    if spaces['p1-beam'].dimension != nb+1 or spaces['p0-beam'].dimension != nb:
        raise AssertionError('unexpected native trace inventory')

    # Rows are basis-major: x, y, scaled yaw. Root translation is fixed in
    # this fixture; its two test hats are omitted only in this supported
    # diagnostic. Native yaw retains every independent half-cell row.
    translation_x = [3*j for j in range(1, nb+1)]
    translation_y = [3*j+1 for j in range(1, nb+1)]
    yaw = [3*k+2 for k in range(nb)]
    c = np.vstack((p1.matrix[translation_x].toarray(),
                   p1.matrix[translation_y].toarray(),
                   p0.matrix[yaw].toarray()))
    m = linalg.block_diag(p1.mass[np.ix_(translation_x,translation_x)],
                          p1.mass[np.ix_(translation_y,translation_y)],
                          p0.mass[np.ix_(yaw,yaw)])
    if c.shape[0] != 3*nb or m.shape != (3*nb,3*nb):
        raise AssertionError(f'channel-adapted row count: {nb=} {c.shape=} {m.shape=} '
                             f'{p1.mass.shape=} {p0.mass.shape=}')
    eig=linalg.eigvalsh(m)
    if eig[0] <= 0 or not np.isfinite(c).all():
        raise AssertionError('invalid multiplier mass/rows')
    sq,_=scales(beam,shell,c.shape[0])
    a=linalg.solve_triangular(linalg.cholesky(m,lower=True),
                              c*sq[None,:],lower=True)
    all_values=linalg.svdvals(a)
    native_values=linalg.svdvals(a[:,shell.free_count:])
    cutoff=1e-10*all_values[0]
    full_rank=int(np.count_nonzero(all_values>cutoff))
    native_rank=int(np.count_nonzero(native_values>cutoff))
    full=np.vstack((p1.full_constraint[translation_x],
                    p1.full_constraint[translation_y],
                    p0.full_constraint[yaw]))
    # Trace factor and gap Gram depend on the unchanged physical trace and
    # overlay, so are reusable here. P1 quadrature-error and incidence
    # fields are NOT recomputed for the combined rows: do not quote them
    # or promote this quick screen to numerical evidence.
    coupling=replace(p1,matrix=sparse.csr_matrix(c),mass=m,
                     full_constraint=full)
    loads={}
    for name in ('smooth','sine'):
        load,full_load=fixed_load(beam,shell,coupling,name,8)
        try:
            measures,solution=solve_exact(beam,shell,coupling,load)
            stations=physical_stations(beam,shell,solution)
            balance=physical_support_balance(beam,shell,
                replace(coupling,full_load_smooth=full_load),solution,'smooth')
            loads[name]={
                'status':'UNREGISTERED_PHYSICAL_SCREEN_NOT_F03_ACCEPTANCE',
                'max_station_gap_over_u':float(max(np.linalg.norm(row['gap_m'])
                    for row in stations)/U),
                'shell_energy_j':balance['active_physical_shell_energy_j'],
                'scaled_solution_parity':measures['scaled_solution_parity'],
                'normalized_force_balance':balance['normalized_force_balance'],
                'normalized_moment_balance':balance['normalized_moment_balance'],
            }
        except (linalg.LinAlgError,CandidateSingular,PrimalNotAdmissible) as exc:
            loads[name]={'status':'UNREGISTERED_NUMERICAL_FAILURE',
                         'failure_type':type(exc).__name__,'failure':str(exc)}
    return {'topology':topology,'n_beam':n_beam,'native_half_cells':nb,'n_shell':n_shell,
            'constraint_rows':int(c.shape[0]),
            'mass_eigen_ratio':float(eig[0]/eig[-1]),
            'full_rank':full_rank,'native_rank':native_rank,
            'shell_only_restrictions':full_rank-native_rank,
            'minimum_native_to_cutoff':float(native_values[-1]/cutoff),
            'loads':loads,
            'status':'UNREGISTERED_ALGEBRAIC_RANK_NOT_F03_ACCEPTANCE'}


if __name__ == '__main__':
    for topology in ('Q4','S3-V2D'):
        for n_shell in (1,8,64):
            print(json.dumps(screen(topology,8,n_shell),sort_keys=True))
