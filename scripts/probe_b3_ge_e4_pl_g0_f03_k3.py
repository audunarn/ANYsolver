"""P0 native/shell line-space physical KKT comparison, not F03 acceptance."""

from __future__ import annotations

import numpy as np
from scipy import linalg

from _b3_e4_f03_native_fixture import build
from _b3_e4_f03_shell_trace import make_shell
from probe_b3_ge_e4_pl_g0_f03_k1_rank import MESHES, candidate_spaces
from probe_b3_ge_e4_pl_g0_f03_k2p import LOADS, STATIONS, solve_candidate
from probe_b3_ge_e4_pl_g0_f03_kkt import (
    assemble, candidate_rank_context, reference_consistency,
)


NAMES=('p0-beam','p0-shell-grid')


def coarse_side(spaces):
    beam,shell=(spaces[name] for name in NAMES)
    if shell.dimension < beam.dimension:
        return shell.name
    if shell.dimension == beam.dimension and not np.array_equal(
            shell.basis_knots,beam.basis_knots):
        return 'UNRESOLVED_EQUAL_DIMENSION_NONMATCHING'
    return beam.name


def screen_mesh(topology,n_beam,n_shell):
    beam=build(n_beam)
    shell=make_shell(n_shell,topology)
    spaces={space.name:space for space in candidate_spaces(beam,shell)}
    results=[]
    for name in NAMES:
        space=spaces[name]
        try:
            coupling=assemble(beam,shell,space)
        except ValueError as exc:
            if str(exc) != 'quadrature reference norm zero or nonfinite':
                raise
            results.append({'space':name,'basis_dimension':space.dimension,
                            'basis_knots':space.basis_knots.tolist(),
                            'status':'INVALID_QUADRATURE_REFERENCE',
                            'failure_type':type(exc).__name__,
                            'failure':str(exc),'loads':{}})
            continue
        if not np.all(np.isfinite(coupling.mass)):
            results.append({'space':name,'basis_dimension':space.dimension,
                            'basis_knots':space.basis_knots.tolist(),
                            'status':'MASS_INVALID',
                            'failure_type':'NonfiniteMass','loads':{}})
            continue
        reference=reference_consistency(beam,shell,coupling)
        try:
            rank=candidate_rank_context(beam,shell,coupling)
        except linalg.LinAlgError as exc:
            results.append({'space':name,'basis_dimension':space.dimension,
                            'basis_knots':space.basis_knots.tolist(),
                            'status':'MASS_OR_RANK_INVALID',
                            'failure_type':type(exc).__name__,
                            'failure':str(exc),'loads':{}})
            continue
        # K2P uses the actual signed full load for recovery, including sine:
        # its local alias to the smooth slot does not alter the load vector.
        response=solve_candidate(beam,shell,space,coupling,reference,rank)
        for load in response['loads'].values():
            if 'multiplier_coefficients_n_per_m' not in load:
                continue
            coefficients=np.asarray(load['multiplier_coefficients_n_per_m'])
            load['multiplier_one_sided_at_stations_n_per_m']=[
                {'s':s,'left':(space.at(s,side='left')@coefficients).tolist(),
                 'right':(space.at(s,side='right')@coefficients).tolist()}
                for s in STATIONS]
        results.append(response)
    return {'topology':topology,'n_beam':n_beam,'n_shell':n_shell,
            'shell':shell.diagnostics(),
            'native_physical_count':len(beam.physical),
            'native_retained_count':len(beam.internal),
            'native_assembly_parity':beam.dense_oracle_max_error,
            'coarse_side_hypothesis':coarse_side(spaces),
            'cases':results}
