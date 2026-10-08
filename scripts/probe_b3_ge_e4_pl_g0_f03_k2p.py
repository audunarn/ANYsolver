"""Fixed-continuum-load planar physical KKT diagnostic, not F03 acceptance."""

from __future__ import annotations

from dataclasses import replace
import warnings

import numpy as np
from scipy import linalg

from _b3_e4_f03_native_fixture import build
from _b3_e4_f03_shell_trace import make_shell
from probe_b3_ge_e4_pl_g0_f03_k1_rank import MESHES, candidate_spaces
from probe_b3_ge_e4_pl_g0_f03_kkt import (
    ELL, CandidateSingular, PrimalNotAdmissible, assemble,
    candidate_rank_context, gap_and_oscillation, physical_support_balance,
    reference_consistency, scales, solve_exact,
)


NAMES=('p1-beam','p1-shell-grid')
LOADS=('smooth','sine')
STATIONS=(.0,.125,.25,.375,.5,.625,.75,.875,1.0)
GAUSS8=np.polynomial.legendre.leggauss(8)
GAUSS4=np.polynomial.legendre.leggauss(4)
GAUSS12=np.polynomial.legendre.leggauss(12)
F0=1e6
U=F0/(210e9*.07)


def finite_tree(value):
    if isinstance(value,dict):
        return all(finite_tree(item) for item in value.values())
    if isinstance(value,(tuple,list,np.ndarray)):
        return all(finite_tree(item) for item in value)
    if isinstance(value,(int,float,np.integer,np.floating)):
        return bool(np.isfinite(value))
    return isinstance(value,(str,type(None),bool))


def fixed_load(beam,shell,coupling,kind,order):
    """Fixed continuum density on the actual native lifted y trace."""
    if kind not in LOADS or order not in (4,8,12):
        raise ValueError('unregistered K2P load or quadrature order')
    roots,weights={4:GAUSS4,8:GAUSS8,12:GAUSS12}[order]
    n_shell=shell.free_count
    n_beam=len(beam.physical)
    load=np.zeros(n_shell+n_beam+len(beam.internal))
    full=np.zeros(shell.dof_count+beam.context.count)
    for a,b in zip(coupling.integration_knots[:-1],
                   coupling.integration_knots[1:]):
        for xi,wi in zip(roots,weights):
            s=float(.5*(a+b)+.5*(b-a)*xi)
            weight=.5*(b-a)*wi
            force=(F0*(1+.25*np.cos(2*np.pi*s)) if kind == 'smooth'
                   else F0*np.sin(2*np.pi*s))
            native=beam.planar_trace_jacobian(s)[1]
            load[n_shell:n_shell+n_beam] += (
                weight*force*native[beam.physical])
            load[n_shell+n_beam:] += (
                weight*force*native[beam.internal])
            full[shell.dof_count:] += weight*force*native
    return load,full


def physical_stations(beam,shell,solution):
    ns=shell.free_count
    nb=len(beam.physical)+len(beam.internal)
    q_shell=np.zeros(shell.dof_count)
    q_shell[shell.free]=solution[:ns]
    q_beam=np.zeros(beam.context.count)
    q_beam[np.r_[beam.physical,beam.internal]]=solution[ns:ns+nb]
    scale=np.array((1.,1.,ELL))
    return [{'s':s,
             'beam_scaled_trace_m':(scale*(
                 beam.planar_trace_jacobian(s)@q_beam)).tolist(),
             'shell_scaled_trace_m':(scale*(shell.trace(s)@q_shell)).tolist(),
             'gap_m':(scale*(beam.planar_trace_jacobian(s)@q_beam
                             -shell.trace(s)@q_shell)).tolist()}
            for s in STATIONS]


def solve_candidate(beam,shell,space,coupling,reference,rank):
    n_shell=shell.free_count
    n_beam=len(beam.physical)
    result={'space':space.name,'basis_dimension':space.dimension,
            'basis_knots':space.basis_knots.tolist(),
            'constraint_rows':coupling.matrix.shape[0],
            'reference_consistency':reference,
            'quadrature_error':coupling.quadrature_error,
            'rank_context':rank,
            'loads':{}}
    if rank['row_rank'] < rank['rows']:
        result['status']='ROW_RANK_LOSS_NOT_F03_ACCEPTANCE'
        return result
    load_sine,full_sine=fixed_load(beam,shell,coupling,'sine',8)
    load_sine_12,full_sine_12=fixed_load(beam,shell,coupling,'sine',12)
    load_smooth_4,full_smooth_4=fixed_load(beam,shell,coupling,'smooth',4)
    load_smooth,full_smooth=fixed_load(beam,shell,coupling,'smooth',8)
    load_smooth_12,full_smooth_12=fixed_load(beam,shell,coupling,'smooth',12)
    sq,sl=scales(beam,shell,coupling.matrix.shape[0])
    full_scale=np.full(shell.dof_count+beam.context.count,U)
    for slot in range(beam.context.nodal_count):
        if slot%6 >= 3:
            full_scale[shell.dof_count+slot]=U/ELL
    full_scale[shell.dof_count+beam.internal]=sq[n_shell+n_beam:]
    result['primal_coordinate_scales']=sq.tolist()
    result['multiplier_coordinate_scales']=sl.tolist()
    result['full_native_coordinate_scales']=full_scale.tolist()
    sine_error=float(np.linalg.norm(sq*(load_sine-load_sine_12)) /
                     max(np.linalg.norm(sq*load_sine_12),np.finfo(float).tiny))
    full_error=float(np.linalg.norm(full_scale*(full_sine-full_sine_12)) /
                     max(np.linalg.norm(full_scale*full_sine_12),
                         np.finfo(float).tiny))
    smooth_error=float(np.linalg.norm(sq*(load_smooth-load_smooth_12)) /
                       max(np.linalg.norm(sq*load_smooth_12),
                           np.finfo(float).tiny))
    smooth_full_error=float(np.linalg.norm(full_scale*(
        full_smooth-full_smooth_12))/
        max(np.linalg.norm(full_scale*full_smooth_12),
            np.finfo(float).tiny))
    smooth_same_rule=float(np.linalg.norm(sq*(
        coupling.load_smooth-load_smooth_4))/
        max(np.linalg.norm(sq*coupling.load_smooth),np.finfo(float).tiny))
    smooth_full_same_rule=float(np.linalg.norm(full_scale*(
        coupling.full_load_smooth-full_smooth_4))/
        max(np.linalg.norm(full_scale*coupling.full_load_smooth),
            np.finfo(float).tiny))
    result['sine_load_quadrature_error']=sine_error
    result['sine_full_load_quadrature_error']=full_error
    result['smooth_load_quadrature_error']=smooth_error
    result['smooth_full_load_quadrature_error']=smooth_full_error
    result['smooth_same_rule_parity']=smooth_same_rule
    result['smooth_full_same_rule_parity']=smooth_full_same_rule
    result['legacy_smooth_eight_point_difference']=float(
        np.linalg.norm(sq*(coupling.load_smooth-load_smooth)) /
        max(np.linalg.norm(sq*load_smooth),np.finfo(float).tiny))
    if not all(np.isfinite(v) for v in (sine_error,full_error,
                                        smooth_error,smooth_full_error,
                                        smooth_same_rule,smooth_full_same_rule)):
        result['status']='INVALID_LOAD_QUADRATURE'
        return result
    for name,load,full in (
            ('smooth',load_smooth,full_smooth),
            ('sine',load_sine,full_sine)):
        # Recovery's legacy smooth slot is replaced locally with the actual
        # signed full load; the original coupling is never mutated.
        for_balance=replace(coupling,full_load_smooth=full)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error',linalg.LinAlgWarning)
                measure,solution=solve_exact(beam,shell,coupling,load)
            if not np.all(np.isfinite(solution)) or not finite_tree(measure):
                result['loads'][name]={
                    'status':'NONFINITE_CANDIDATE_RESPONSE',
                    'failure_type':'NonfiniteKKTResult'}
                continue
            physical=gap_and_oscillation(beam,shell,space,coupling,solution)
            balance=physical_support_balance(
                beam,shell,for_balance,solution,'smooth')
            measure.update(physical)
            measure['support_balance']=balance
            measure['stations']=physical_stations(beam,shell,solution)
            primal_count=n_shell+len(beam.physical)+len(beam.internal)
            coefficients=solution[primal_count:].reshape(space.dimension,3)
            measure['multiplier_coefficients_n_per_m']=coefficients.tolist()
            measure['multiplier_at_stations_n_per_m']=[
                (space.at(s)@coefficients).tolist() for s in STATIONS]
            measure['retained_coordinates']=solution[
                n_shell+len(beam.physical):primal_count].tolist()
            measure['assembled_interface_work_j']=float(
                solution[primal_count:]@(
                    coupling.matrix@solution[:primal_count]))
            if not finite_tree(measure):
                result['loads'][name]={
                    'status':'NONFINITE_CANDIDATE_RESPONSE',
                    'failure_type':'NonfiniteRecoveryResult'}
                continue
            local_valid=(
                measure['skew_k'] <= 1e-10
                and measure['skew_krr'] <= 1e-10
                and measure['skew_ke'] <= 1e-10
                and measure.get('ke_min_eigen_ratio',0.) > 1e-12
                and measure['scaled_kkt_singular_ratio'] > 1e-12
                and measure['scaled_free_equilibrium'] <= 1e-9
                and measure['normalized_weak_residual'] <= 1e-10
                and measure['assembled_work_quadrature_error'] <= 1e-10
                and balance['normalized_force_balance'] <= 1e-8
                and balance['normalized_moment_balance'] <= 1e-8
                and reference['max_translation_m'] <= 1e-12
                and reference['max_rotation_rad'] <= 1e-12
                and all(v <= 1e-10 for v in coupling.quadrature_error.values())
                and sine_error <= 1e-10 and full_error <= 1e-10
                and smooth_error <= 1e-10 and smooth_full_error <= 1e-10
                and smooth_same_rule <= 1e-12
                and smooth_full_same_rule <= 1e-12)
            measure['status']=(
                'NUMERICAL_OR_PHYSICAL_LOCAL_FAILURE' if not local_valid else
                'LOCAL_DIAGNOSTIC_WITH_PARITY_OPEN'
                if measure['scaled_solution_parity'] > 1e-10 else
                'LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE')
        except (linalg.LinAlgError,linalg.LinAlgWarning,
                CandidateSingular,PrimalNotAdmissible) as exc:
            measure={'status':'NUMERICAL_CANDIDATE_FAILURE',
                     'failure_type':type(exc).__name__,'failure':str(exc)}
        result['loads'][name]=measure
    statuses=[item['status'] for item in result['loads'].values()]
    result['status']=(
        'TWO_LOAD_INVENTORY_WITH_FAILURES_NOT_F03_ACCEPTANCE'
        if any(status not in ('LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE',
                              'LOCAL_DIAGNOSTIC_WITH_PARITY_OPEN')
               for status in statuses) else
        'TWO_LOAD_INVENTORY_WITH_PARITY_OPEN'
        if 'LOCAL_DIAGNOSTIC_WITH_PARITY_OPEN' in statuses else
        'TWO_LOAD_LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE')
    return result


def screen_mesh(topology,n_beam,n_shell):
    beam=build(n_beam)
    shell=make_shell(n_shell,topology)
    spaces={space.name:space for space in candidate_spaces(beam,shell)}
    rows=[]
    for name in NAMES:
        space=spaces[name]
        try:
            coupling=assemble(beam,shell,space)
        except ValueError as exc:
            if str(exc) != 'quadrature reference norm zero or nonfinite':
                raise
            rows.append({'space':name,'basis_dimension':space.dimension,
                         'basis_knots':space.basis_knots.tolist(),
                         'status':'INVALID_QUADRATURE_REFERENCE',
                         'failure_type':type(exc).__name__,
                         'failure':str(exc),'loads':{}})
            continue
        if not np.all(np.isfinite(coupling.mass)):
            rows.append({'space':name,'basis_dimension':space.dimension,
                         'status':'MASS_INVALID',
                         'failure_type':'NonfiniteMass','loads':{}})
            continue
        reference=reference_consistency(beam,shell,coupling)
        try:
            rank=candidate_rank_context(beam,shell,coupling)
        except linalg.LinAlgError as exc:
            rows.append({'space':name,'basis_dimension':space.dimension,
                         'status':'MASS_OR_RANK_INVALID',
                         'failure_type':type(exc).__name__,
                         'failure':str(exc),'loads':{}})
            continue
        rows.append(solve_candidate(beam,shell,space,coupling,reference,rank))
    return {'topology':topology,'n_beam':n_beam,'n_shell':n_shell,
            'shell':shell.diagnostics(),
            'native_physical_count':len(beam.physical),
            'native_retained_count':len(beam.internal),
            'native_assembly_parity':beam.dense_oracle_max_error,
            'cases':rows}
