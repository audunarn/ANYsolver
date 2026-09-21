"""Work-scaled native-image/shell-compatibility rank diagnostic only."""

from __future__ import annotations

import numpy as np
from scipy import linalg

from _b3_e4_f03_native_fixture import build
from _b3_e4_f03_shell_trace import make_shell
from probe_b3_ge_e4_pl_g0_f03_k1_rank import MESHES, candidate_spaces
from probe_b3_ge_e4_pl_g0_f03_kkt import assemble, reference_consistency, scales


NAMES=('p1-beam','p1-shell-grid','p0-shell-grid')
RELATIVE_CUTOFF=1e-10
U=1e6/(210e9*.07)
L0=1.


def finite(values):
    return bool(np.all(np.isfinite(values)))


def spectrum_and_rank(matrix,cutoff):
    values=linalg.svdvals(matrix,check_finite=True)
    return values,int(np.count_nonzero(values > cutoff))


def candidate(beam,shell,space):
    result={'space':space.name,'basis_dimension':space.dimension,
            'basis_knots':space.basis_knots.tolist(),
            'status':'UNCLASSIFIED'}
    try:
        coupling=assemble(beam,shell,space)
    except ValueError as exc:
        if str(exc) != 'quadrature reference norm zero or nonfinite':
            raise
        result.update(status='INVALID_QUADRATURE_REFERENCE',
                      failure_type=type(exc).__name__,failure=str(exc))
        return result
    c=coupling.matrix.toarray()
    m=coupling.mass
    if not finite(c) or not finite(m):
        result['status']='NONFINITE_ASSEMBLY'
        return result
    reference=reference_consistency(beam,shell,coupling)
    if (not finite(np.asarray(list(reference.values()),dtype=float))
            or not finite(np.asarray(list(coupling.quadrature_error.values()),
                                     dtype=float))):
        result['status']='NONFINITE_REFERENCE_OR_QUADRATURE'
        return result
    result['reference_consistency']=reference
    result['quadrature_error']=coupling.quadrature_error
    if (any(value > 1e-10 for value in coupling.quadrature_error.values())
            or reference['max_translation_m'] > 1e-12
            or reference['max_rotation_rad'] > 1e-12):
        result['status']='REFERENCE_OR_QUADRATURE_INVALID'
        return result
    mass_skew=float(np.linalg.norm(m-m.T)/max(np.linalg.norm(m),1e-30))
    if not np.isfinite(mass_skew):
        result['status']='NONFINITE_MASS_METRIC'
        return result
    result['mass_relative_skew']=mass_skew
    if mass_skew > 1e-12:
        result['status']='MASS_ASYMMETRIC'
        return result
    try:
        mass_eigen=linalg.eigvalsh(m,check_finite=True)
    except linalg.LinAlgError as exc:
        result.update(status='MASS_EIGEN_FAILURE',
                      failure_type=type(exc).__name__,failure=str(exc))
        return result
    if not finite(mass_eigen):
        result['status']='NONFINITE_MASS_METRIC'
        return result
    result['mass_min_eigen']=float(mass_eigen[0])
    result['mass_max_eigen']=float(mass_eigen[-1])
    if mass_eigen[0] <= 0:
        result['status']='NONPOSITIVE_MULTIPLIER_MASS'
        return result
    result['mass_eigen_ratio']=float(mass_eigen[0]/mass_eigen[-1])
    if result['mass_eigen_ratio'] <= 1e-12:
        result['status']='MASS_ILL_CONDITIONED'
        return result
    sq,_=scales(beam,shell,c.shape[0])
    if not finite(sq) or np.any(sq<=0):
        result['status']='INVALID_COORDINATE_SCALE'
        return result
    try:
        lower=linalg.cholesky(m,lower=True,check_finite=True)
        a=linalg.solve_triangular(lower,c*sq[None,:],lower=True,
                                  check_finite=True)/(U*np.sqrt(L0))
    except linalg.LinAlgError as exc:
        result.update(status='MASS_FACTOR_FAILURE',
                      failure_type=type(exc).__name__,failure=str(exc))
        return result
    if not finite(a):
        result['status']='NONFINITE_WHITENED_MAP'
        return result
    n_shell=shell.free_count
    n_physical=len(beam.physical)
    native=a[:,n_shell:]
    physical=a[:,n_shell:n_shell+n_physical]
    try:
        full_singular,_=spectrum_and_rank(a,0.)
    except linalg.LinAlgError as exc:
        result.update(status='TRACE_SVD_FAILURE',
                      failure_type=type(exc).__name__,failure=str(exc))
        return result
    if not finite(full_singular) or full_singular[0] <= 0:
        result['status']='NONFINITE_OR_ZERO_TRACE'
        return result
    cutoff=RELATIVE_CUTOFF*full_singular[0]
    full_rank=int(np.count_nonzero(full_singular > cutoff))
    try:
        native_u,native_singular,_=linalg.svd(
            native,full_matrices=True,check_finite=True)
        physical_singular,physical_rank=spectrum_and_rank(physical,cutoff)
    except linalg.LinAlgError as exc:
        result.update(status='NATIVE_SVD_FAILURE',
                      failure_type=type(exc).__name__,failure=str(exc))
        return result
    native_rank=int(np.count_nonzero(native_singular > cutoff))
    left_null=native_u[:,native_rank:]
    projected=left_null.T@a[:,:n_shell]
    try:
        projected_singular,projected_rank=spectrum_and_rank(projected,cutoff)
    except linalg.LinAlgError as exc:
        result.update(status='PROJECTED_SVD_FAILURE',
                      failure_type=type(exc).__name__,failure=str(exc))
        return result
    if not all(finite(s) for s in (native_singular,physical_singular,
                                   projected_singular,projected)):
        result['status']='NONFINITE_RANK_DECOMPOSITION'
        return result
    shell_restrictions=full_rank-native_rank
    left_null_residual=float(np.linalg.norm(left_null.T@native)/
                             max(np.linalg.norm(native),np.finfo(float).tiny))
    discarded_native_max=float(native_singular[native_rank]
                               if native_rank < len(native_singular) else 0.)
    range_basis=native_u[:,:native_rank]
    shell_part=a[:,:n_shell]
    reconstruction=(range_basis@(range_basis.T@shell_part)
                    +left_null@projected)
    reconstruction_residual=float(np.linalg.norm(shell_part-reconstruction)/
                                  max(np.linalg.norm(shell_part),
                                      np.finfo(float).tiny))
    projector_orthogonality=float(np.linalg.norm(native_u.T@native_u-
                                                np.eye(len(native_u))))
    near_cutoff=any(np.any((values>=.1*cutoff)&(values<=10.*cutoff))
                    for values in (full_singular,native_singular,
                                   physical_singular,projected_singular))
    if not finite(np.asarray((left_null_residual,discarded_native_max,
                              reconstruction_residual,
                              projector_orthogonality))):
        result['status']='NONFINITE_RANK_DECOMPOSITION'
        return result
    result.update(
        constraint_rows=int(c.shape[0]),
        shell_free_coordinates=n_shell,
        beam_physical_coordinates=n_physical,
        beam_retained_coordinates=len(beam.internal),
        relative_cutoff=RELATIVE_CUTOFF,
        absolute_cutoff=float(cutoff),
        full_singular=full_singular.tolist(),
        native_singular=native_singular.tolist(),
        beam_physical_singular=physical_singular.tolist(),
        projected_shell_singular=projected_singular.tolist(),
        full_rank=full_rank,native_rank=native_rank,
        beam_physical_rank=physical_rank,
        projected_shell_rank=projected_rank,
        shell_restrictions=shell_restrictions,
        left_null_native_residual=left_null_residual,
        discarded_native_to_cutoff=discarded_native_max/cutoff,
        shell_reconstruction_residual=reconstruction_residual,
        projector_orthogonality_residual=projector_orthogonality,
        near_cutoff=bool(near_cutoff),
        projected_shell_map=projected.tolist(),
        min_full_singular_to_cutoff=float(full_singular[-1]/cutoff),
        min_native_singular_to_cutoff=float(native_singular[-1]/cutoff),
        status=('RANK_DECOMPOSITION_CONSISTENT_NOT_F03_ACCEPTANCE'
                if projected_rank == shell_restrictions
                and discarded_native_max <= .1*cutoff
                and left_null_residual <= 1e-10
                and reconstruction_residual <= 1e-10
                and projector_orthogonality <= 1e-10
                and not near_cutoff else
                'RANK_DECOMPOSITION_AMBIGUOUS_NOT_F03_ACCEPTANCE'))
    return result


def screen_mesh(topology,n_beam,n_shell):
    beam=build(n_beam)
    shell=make_shell(n_shell,topology)
    spaces={space.name:space for space in candidate_spaces(beam,shell)}
    return {'topology':topology,'n_beam':n_beam,'n_shell':n_shell,
            'shell':shell.diagnostics(),
            'cases':[candidate(beam,shell,spaces[name]) for name in NAMES]}
