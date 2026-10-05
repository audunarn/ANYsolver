"""Preparatory exact planar KKT probe; NOT a frozen or executed G0 gate.

Uses the native retained B3 and physical E4-PL in-plane operators.  The
three-channel screen cannot qualify eccentric six-channel line coupling.
Run only after the F03-K0 manifest, implementation and independent review
have been frozen and an immutable output location has been registered.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import linalg, sparse
from scipy.sparse.linalg import splu
from scipy.spatial.transform import Rotation

from _b3_e4_f03_native_fixture import Fixture, build
from _b3_e4_f03_shell_trace import ShellPanel, make_shell


ELL = .46
GAUSS_4 = np.polynomial.legendre.leggauss(4)
GAUSS_2 = np.polynomial.legendre.leggauss(2)
SPACES = ('p0-union', 'p1-shell', 'p1-beam', 'p1-union', 'dual-union')


class CandidateSingular(Exception):
    """Typed singular multiplier candidate, distinct from execution failure."""


class PrimalNotAdmissible(Exception):
    """Typed failure of the retained primal elimination block."""


def knots(*arrays):
    values = np.concatenate([np.asarray(a, dtype=float) for a in arrays])
    result = np.unique(np.round(values, 14))
    if result[0] != 0 or result[-1] != 1 or np.any(np.diff(result) <= 1e-12):
        raise ValueError('invalid or near-duplicate interface knots')
    return result


@dataclass(frozen=True)
class Space:
    name: str
    basis_knots: np.ndarray

    @property
    def dimension(self):
        return len(self.basis_knots) - (1 if self.name == 'p0-union' else 0)

    def at(self, s: float, *, side: str = 'left'):
        k = self.basis_knots
        if side not in ('left', 'right'):
            raise ValueError('side must be left or right')
        i = int(np.clip(np.searchsorted(k, s, side=side) - 1, 0, len(k)-2))
        xi = (s-k[i])/(k[i+1]-k[i])
        out = np.zeros(self.dimension)
        if self.name == 'p0-union':
            out[i] = 1.
        elif self.name == 'dual-union':
            out[i:i+2] = (2.-3.*xi, 3.*xi-1.)
        else:
            out[i:i+2] = (1.-xi, xi)
        return out

    def derivative(self, s: float, *, side='left'):
        k = self.basis_knots
        i = int(np.clip(np.searchsorted(k, s, side=side) - 1, 0, len(k)-2))
        out = np.zeros(self.dimension)
        h = k[i+1]-k[i]
        if self.name == 'dual-union':
            out[i:i+2] = (-3./h, 3./h)
        elif self.name != 'p0-union':
            out[i:i+2] = (-1./h, 1./h)
        return out


def spaces(beam: Fixture, shell: ShellPanel):
    beam_knots = np.linspace(0., 1., beam.n_half_cells+1)
    shell_knots = shell.breakpoints()
    union = knots(beam_knots, shell_knots)
    return tuple(Space(name, {'p0-union': union, 'p1-shell': shell_knots,
                              'p1-beam': beam_knots, 'p1-union': union,
                              'dual-union': union}[name]) for name in SPACES)


@dataclass
class Coupling:
    matrix: sparse.csr_matrix
    mass: np.ndarray
    gap_gram: np.ndarray
    trace_factor: np.ndarray
    load_smooth: np.ndarray
    load_alternating: np.ndarray
    full_constraint: np.ndarray
    full_load_smooth: np.ndarray
    full_load_alternating: np.ndarray
    integration_knots: np.ndarray
    quadrature_error: dict
    max_row_incidence: int


def _integrate(beam: Fixture, shell: ShellPanel, space: Space, order: int):
    """Build exact-reference B and M and two independent native trace loads."""
    integration_knots = knots(np.linspace(0, 1, beam.n_half_cells+1),
                              shell.breakpoints(), space.basis_knots)
    gauss_x, gauss_w = GAUSS_4 if order == 4 else GAUSS_2
    ns = shell.free_count
    nb = len(beam.physical)
    nr = len(beam.internal)
    n = ns+nb+nr
    m = 3*space.dimension
    c = np.zeros((m, n))
    c_all = np.zeros((m, shell.dof_count+beam.context.count))
    mass = np.zeros((space.dimension, space.dimension))
    gap_gram = np.zeros((n,n))
    trace_factor = []
    loads = np.zeros((2, n))
    loads_all = np.zeros((2, shell.dof_count+beam.context.count))
    scale = np.diag((1., 1., ELL))
    for a, b in zip(integration_knots[:-1], integration_knots[1:]):
        for xi, wi in zip(gauss_x, gauss_w):
            s = .5*(a+b)+.5*(b-a)*xi
            weight = .5*(b-a)*wi
            basis = space.at(s)
            st_full = shell.trace(float(s))
            st = st_full[:, shell.free]
            bt = beam.planar_trace_jacobian(float(s))
            trace = scale @ np.hstack((-st, bt[:, beam.physical],
                                       bt[:, beam.internal]))
            c += weight*np.kron(basis[:, None], trace)
            c_all += weight*np.kron(basis[:,None],
                                    scale@np.hstack((-st_full,bt)))
            mass += weight*np.outer(basis, basis)
            gap_gram += weight*(trace.T@trace)
            trace_factor.append(np.sqrt(weight)*trace)
            # The test loads act on the beam's actual lifted y displacement.
            # The alternating density changes only at native half-cell knots.
            j = min(int(s*beam.n_half_cells), beam.n_half_cells-1)
            fy = 1e6*np.array((1+.25*np.cos(2*np.pi*s), (-1.)**j))
            loads[:, ns:ns+nb] += weight*fy[:, None]*bt[1, beam.physical]
            loads[:, ns+nb:] += weight*fy[:, None]*bt[1, beam.internal]
            loads_all[:,shell.dof_count:] += weight*fy[:,None]*bt[1]
    sq, _ = scales(beam,shell,m)
    work_scaled = np.abs(c*sq[None,:])
    thresholds = 1e-12*np.max(work_scaled,axis=1)
    nnz_by_row = np.count_nonzero(work_scaled > thresholds[:,None],axis=1)
    return (c, mass, gap_gram, np.vstack(trace_factor), loads, c_all, loads_all,
            integration_knots, int(nnz_by_row.max(initial=0)))


def assemble(beam: Fixture, shell: ShellPanel, space: Space) -> Coupling:
    c4, m4, g4, t4, f4, ca4, fa4, mesh, incidence = _integrate(beam, shell, space, 4)
    c2, m2, g2, _, _, _, _, _, _ = _integrate(beam, shell, space, 2)
    def relative(a, b):
        norm = np.linalg.norm(a)
        if norm <= 0 or not np.isfinite(norm):
            raise ValueError('quadrature reference norm zero or nonfinite')
        return float(np.linalg.norm(a-b)/norm)
    sq, _ = scales(beam, shell, 3*space.dimension)
    # One independent scalar mass per channel; channels have metre gaps.
    return Coupling(sparse.csr_matrix(c4), np.kron(m4, np.eye(3)), g4, t4,
                    f4[0], f4[1], ca4, fa4[0], fa4[1], mesh,
                    {'C': relative(c4*sq[None,:],c2*sq[None,:]),
                     'G_D':relative(sq[:,None]*g4*sq[None,:],
                                    sq[:,None]*g2*sq[None,:]),
                     'M': relative(m4,m2)}, incidence)


def supported_stiffness(beam: Fixture, shell: ShellPanel):
    """Physical shell first, native physical second, retained last."""
    local = np.r_[beam.physical, beam.internal]
    kb = beam.tangent[local, :][:, local]
    ks = shell.stiffness[shell.free, :][:, shell.free]
    return sparse.block_diag((ks, kb), format='csc')


def independent_shell_pose(shell: ShellPanel, s: float,
                           displacement: np.ndarray):
    """Separate finite 3D proper fit, not the linearized shell trace."""
    if displacement.shape != (shell.dof_count,):
        raise ValueError('full shell physical displacement required')
    from _b3_e4_f03_shell_trace import _SAMPLE_OFFSETS
    reference = np.asarray([(s+ox,y,0.) for ox,y in _SAMPLE_OFFSETS],
                           dtype=float)
    assert reference.shape == (4,3)
    # Constructing the samples from reference positions independently of the
    # shell trace catches a centroid, host, orientation or yaw-derivative error.
    current = reference.copy()
    nodal = displacement.reshape(-1,2)
    current[:,:2] += shell.sample_weights(s)@nodal
    center = current.mean(axis=0)
    h = (reference-reference.mean(axis=0)).T@(current-center)
    u, _, vt = linalg.svd(h)
    correction = np.diag((1.,1.,np.linalg.det(vt.T@u.T)))
    orientation = vt.T@correction@u.T
    return center, orientation


def independent_sample_hosts(shell: ShellPanel, s: float):
    """Audit four reference hosts with a separate geometric interpolator."""
    from _b3_e4_f03_shell_trace import _SAMPLE_OFFSETS
    n = shell.x_interval_count
    dx = 1./shell.n_s
    expected = np.zeros((4,shell.node_count))
    for sample,(offset,y) in enumerate(_SAMPLE_OFFSETS):
        x = s+offset
        i = min(n-1,max(0,int(np.floor((x+.5)/dx))))
        j = min(1,max(0,int(np.floor((y+.5)/.5))))
        vertices = np.array([(i,j),(i+1,j),(i+1,j+1),(i,j+1)])
        points = np.array([(-.5+v[0]*dx,-.5+v[1]*.5) for v in vertices])
        local = np.linalg.solve(np.column_stack((points[1]-points[0],
                                                  points[3]-points[0])),
                                np.array((x,y))-points[0])
        xi,eta = local
        if shell.topology == 'Q4':
            shape = np.array(((1-xi)*(1-eta),xi*(1-eta),xi*eta,
                              (1-xi)*eta))
            chosen = np.arange(4)
        else:
            chosen = np.array((0,1,2)) if xi > eta else np.array((0,2,3))
            tri = points[chosen]
            # Solve barycentric partition and both coordinate moments, not
            # the branch formulas used by ShellPanel._shape.
            shape = np.linalg.solve(np.vstack((np.ones(3),tri.T)),
                                    np.array((1.,x,y)))
        ids = vertices[chosen,1]*(n+1)+vertices[chosen,0]
        expected[sample,ids] = shape
    return float(np.max(np.abs(expected-shell.sample_weights(s))))


def actual_pose_gap(beam: Fixture, shell: ShellPanel, s: float,
                    shell_displacement: np.ndarray,
                    beam_increment: np.ndarray):
    """Objective finite point gap with frozen reference offset/frame."""
    rs, rot_s = independent_shell_pose(shell,s,shell_displacement)
    rb, rot_b = beam.pose(s,beam_increment)
    rs0, rot_s0 = independent_shell_pose(shell,s,np.zeros(shell.dof_count))
    rb0, rot_b0 = beam.pose(s)
    e0 = rot_s0.T@(rb0-rs0)
    a0 = rot_s0.T@rot_b0
    ct = rot_s.T@(rb-rs)-e0
    cr = Rotation.from_matrix(a0.T@rot_s.T@rot_b).as_rotvec()
    return np.r_[ct,cr]


def supported_pose_derivative(beam: Fixture, shell: ShellPanel,
                              s: float, shell_direction: np.ndarray,
                              beam_direction: np.ndarray, h: float = 1e-7):
    """Check actual Context.advance with only zero-root beam directions."""
    if any(abs(beam_direction[i]) > 0 for i in beam.context.fixed):
        raise ValueError('finite difference violates native fixed root')
    nonlinear = (actual_pose_gap(beam,shell,s,h*shell_direction,h*beam_direction)
                 -actual_pose_gap(beam,shell,s,-h*shell_direction,
                                   -h*beam_direction))/(2*h)
    analytic = beam.planar_trace_jacobian(s)@beam_direction-shell.trace(s)@shell_direction
    error = np.r_[nonlinear[:2]-analytic[:2],nonlinear[5]-analytic[2]]
    scale = np.diag((1.,1.,ELL))
    u = 1e6/(210e9*.07)
    gap_zero = actual_pose_gap(
                beam,shell,s,np.zeros(shell.dof_count),
                np.zeros(beam.context.count))
    return {'scaled_relative_error':float(np.linalg.norm(scale@error)/
                max(np.linalg.norm(scale@analytic),u)),
            'reference_translation_m':float(np.max(np.abs(gap_zero[:3]))),
            'reference_rotation_rad':float(np.max(np.abs(gap_zero[3:]))),
            'out_of_plane_variation':float(np.linalg.norm(nonlinear[[2,3,4]]))}


def supported_pose_work(beam: Fixture, shell: ShellPanel, s: float,
                        shell_direction: np.ndarray,
                        beam_direction: np.ndarray,
                        multiplier: np.ndarray, h: float = 1e-3):
    """Independent finite pose virtual-work variation at one station."""
    if multiplier.shape != (3,):
        raise ValueError('three planar physical-gap dual coefficients required')
    plus = actual_pose_gap(beam,shell,s,h*shell_direction,h*beam_direction)
    minus = actual_pose_gap(beam,shell,s,-h*shell_direction,-h*beam_direction)
    scale = np.diag((1.,1.,ELL))
    finite = float(multiplier@(scale@np.r_[(plus-minus)[:2]/(2*h),
                                          (plus-minus)[5]/(2*h)]))
    linear = float(multiplier@scale@(
        beam.planar_trace_jacobian(s)@beam_direction
        -shell.trace(s)@shell_direction))
    u = 1e6/(210e9*.07)
    return {'finite_work_density':finite, 'linear_work_density':linear,
            'normalized_gradient_error':float(abs(finite-linear)/(1e6*u))}


def unrestricted_common_patch(beam: Fixture, shell: ShellPanel, s: float,
                              affine: np.ndarray, translation: np.ndarray):
    """Full-column kinematic patch, outside fixed-root Context.advance.

    An in-plane affine field F=I+A has a well-defined proper polar frame.
    Apply it to native reference nodes and cell frames analytically; the
    actual straight native lift and station interpolation remain in use.
    This is not a supported beam constitutive or finite-difference check.
    """
    if affine.shape != (2,2) or translation.shape != (2,):
        raise ValueError('planar affine tensor and translation required')
    f = np.eye(2)+affine
    if np.linalg.det(f) <= 0:
        raise ValueError('affine patch must preserve orientation')
    nx = shell.x_interval_count
    coords_shell = np.array([(float(-.5+i/shell.n_s), y)
                             for y in (-.5,0.,.5) for i in range(nx+1)])
    shell_delta = (coords_shell@affine.T+translation).reshape(-1)
    shell_center, shell_rot = independent_shell_pose(shell,s,shell_delta)
    infinitesimal_yaw = (shell.trace(s)@shell_delta)[2]
    beam_delta = np.zeros(beam.context.count)
    for node in range(beam.n_half_cells+1):
        x = node/beam.n_half_cells
        beam_delta[6*node:6*node+2] = affine@np.array((x,0.))+translation
        beam_delta[6*node+5] = infinitesimal_yaw
    for cell in range(beam.n_half_cells):
        e,c = divmod(cell,2)
        beam_delta[beam.context.nodal_count+24*e+3*c+2] = infinitesimal_yaw
    native_reference, native_frame = beam.pose(s)
    native_current = native_reference.copy()
    native_current[:2] = f@native_reference[:2]+translation
    physical_rotation = np.eye(3)
    physical_rotation[:2,:2] = shell_rot[:2,:2]
    native_current_frame = physical_rotation@native_frame
    # The finite cell and nodal frames follow the shell sample fit, while the
    # unrestricted tangent field uses that fit's first variation. Rectangular
    # sampling makes its yaw differ from polar(F) for generic shear.
    gap = np.r_[shell_rot.T@(native_current-shell_center),
                Rotation.from_matrix(shell_rot.T@native_current_frame).as_rotvec()]
    infinitesimal = beam.planar_trace_jacobian(s)@beam_delta-shell.trace(s)@shell_delta
    return {'finite_gap':float(np.linalg.norm(gap)),
            'linear_gap':float(np.linalg.norm(infinitesimal))}


def scales(beam: Fixture, shell: ShellPanel, m: int):
    """Frozen congruence scales; register exact station/cell ordering."""
    from _b3_e4_f03_native_fixture import E, G, AREA, SHEAR_AREA, I, J
    f0 = 1e6
    u = f0/(E*.07)
    physical = [u]*shell.free_count
    for slot in beam.physical:
        physical.append(u if slot%6 < 3 else u/ELL)
    retained = []
    force_scale = np.array((E*AREA, G*SHEAR_AREA, G*SHEAR_AREA))*u
    moment_scale = np.array((G*J/ELL, E*I/ELL, E*I/ELL))*u
    # Native z+ell order: two cell force triplets, then four endpoint
    # moment triplets.  It is not three repeated six-resultant vectors.
    resultants = np.r_[np.tile(force_scale,2),np.tile(moment_scale,4)]
    for _ in range(beam.n_half_cells//2):
        retained.extend([u/ELL]*6)
        retained.extend(resultants)
    if len(retained) != len(beam.internal):
        raise AssertionError('native retained ordering changed')
    return np.asarray(physical+retained), np.full(m, f0)


def exact_partition(beam: Fixture, shell: ShellPanel, c: sparse.csr_matrix):
    """Exact retained elimination, including induced multiplier block."""
    np_ = shell.free_count+len(beam.physical)
    k = supported_stiffness(beam, shell).toarray()
    sq, _ = scales(beam, shell, c.shape[0])
    cp, cr = c[:, :np_].toarray(), c[:, np_:].toarray()
    kpp, kpr, krp, krr = k[:np_, :np_], k[:np_, np_:], k[np_:, :np_], k[np_:, np_:]
    sr_scale = sq[np_:]
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',linalg.LinAlgWarning)
            factor = linalg.lu_factor((sr_scale[:,None]*krr)*sr_scale[None,:],
                                      check_finite=True)
    except (linalg.LinAlgError,linalg.LinAlgWarning) as exc:
        raise PrimalNotAdmissible('scaled native Krr cannot be factored') from exc
    def solve_rr(rhs):
        return sr_scale[:,None]*linalg.lu_solve(
            factor, sr_scale[:,None]*np.atleast_2d(rhs).reshape(len(krr),-1))
    xr = solve_rr(krp)
    xc = solve_rr(cr.T)
    ke = kpp-kpr@xr
    cl = cp-cr@xr
    cu = cp.T-kpr@xc
    sr = cr@xc
    return k, (ke, cl, cu, sr, solve_rr), (krr, krp, cr)


def solve_exact(beam: Fixture, shell: ShellPanel, coupling: Coupling,
                load: np.ndarray):
    """Sparse full KKT, bounded dense exact elimination and signed checks."""
    c = coupling.matrix
    k, (ke, cl, cu, sr, solve_rr), (krr, krp, cr) = exact_partition(beam,shell,c)
    np_ = len(ke)
    full_kkt = sparse.bmat(((sparse.csc_matrix(k), c.T),
                            (c, None)), format='csc')
    rhs = np.r_[load, np.zeros(c.shape[0])]
    sq, sl = scales(beam,shell,c.shape[0])
    kkt_scale = np.r_[sq,sl]
    scaled_sparse_kkt = sparse.diags(kkt_scale) @ full_kkt @ sparse.diags(kkt_scale)
    try:
        full = kkt_scale*splu(scaled_sparse_kkt).solve(kkt_scale*rhs)
    except RuntimeError as exc:
        if 'exactly singular' not in str(exc).lower():
            raise
        raise CandidateSingular(str(exc)) from exc
    xr = solve_rr(load[np_:])[:,0]
    rhs_reduced = np.r_[load[:np_]-k[:np_,np_:]@xr, -cr@xr]
    reduced = np.block([[ke, cu], [cl, -sr]])
    reduced_scale = np.r_[sq[:np_],sl]
    reduced_scaled = (reduced_scale[:,None]*reduced)*reduced_scale[None,:]
    solution = reduced_scale*linalg.solve(reduced_scaled,
                                         reduced_scale*rhs_reduced,
                                         assume_a='gen')
    recovered = xr-solve_rr(krp@solution[:np_]+cr.T@solution[np_:])[:,0]
    condensed_full = np.r_[solution[:np_], recovered,solution[np_:]]
    parity = np.linalg.norm((full-condensed_full)/kkt_scale)/np.linalg.norm(full/kkt_scale)
    primal = full[:len(k)]
    multipliers = full[len(k):]
    primal_internal = k@primal
    primal_constraint = c.T@multipliers
    equilibrium = np.linalg.norm(sq*(primal_internal+primal_constraint-load))/max(
        np.linalg.norm(sq*primal_internal),
        np.linalg.norm(sq*primal_constraint),np.linalg.norm(sq*load))
    weak = c@primal
    mass_factor = linalg.cho_factor(coupling.mass, check_finite=True)
    weak_residual = np.sqrt(max(0.,weak@linalg.cho_solve(mass_factor,weak)))
    weak_residual /= np.sqrt(1.)*(1e6/(210e9*.07))
    k_scaled = (sq[:,None]*k)*sq[None,:]
    krr_scaled = k_scaled[np_:,np_:]
    ke_scaled = (sq[:np_,None]*ke)*sq[None,:np_]
    def skew(x):
        return float(np.linalg.norm(x-x.T)/max(np.linalg.norm(x),1e-30))
    # Small bounded candidate only: dense SVD is diagnostic, not a production
    # algorithm; a resource budget must be registered before running a suite.
    scaled_kkt = scaled_sparse_kkt.toarray()
    singular = linalg.svdvals(scaled_kkt)
    # Whiten row units with the exact (possibly non-diagonal) dual mass.
    lower_mass = linalg.cholesky(coupling.mass, lower=True)
    whitened_c = linalg.solve_triangular(
        lower_mass, c.toarray()*sq[None,:], lower=True)
    row_singular = linalg.svdvals(whitened_c)
    row_rank = int(np.count_nonzero(row_singular > 1e-10*row_singular[0]))
    # Rank the weighted trace operator itself.  A relative cutoff on its
    # squared Gram spectrum would silently loosen 1e-10 to 1e-5.
    trace_singular = linalg.svdvals(coupling.trace_factor*sq[None,:])
    gram_rank = int(np.count_nonzero(
        trace_singular > 1e-10*trace_singular[0]))
    result = {'scaled_solution_parity': float(parity),
              'scaled_free_equilibrium':float(equilibrium),
              'normalized_weak_residual':float(weak_residual),
              'skew_k':skew(k_scaled), 'skew_krr':skew(krr_scaled),
              'skew_ke':skew(ke_scaled),
              'cond_krr':float(np.linalg.cond(krr_scaled)),
              'scaled_kkt_singular_ratio':float(singular[-1]/singular[0]),
              'mass_whitened_constraint_singular':row_singular.tolist(),
              'constraint_row_rank':row_rank,
              'constraint_rows':int(c.shape[0]),
              'trace_gram_rank':gram_rank,
              'weighted_trace_singular':trace_singular.tolist(),
              'gram_minus_constraint_rank':gram_rank-row_rank,
              'quadrature_error':coupling.quadrature_error,
              'max_row_incidence':coupling.max_row_incidence}
    if result['skew_krr'] <= 1e-10:
        native_spectrum = linalg.eigvalsh(krr_scaled)
        floor = 1e-12*max(abs(native_spectrum[0]),abs(native_spectrum[-1]))
        result['krr_inertia'] = {
            'negative':int(np.count_nonzero(native_spectrum < -floor)),
            'zero':int(np.count_nonzero(np.abs(native_spectrum) <= floor)),
            'positive':int(np.count_nonzero(native_spectrum > floor))}
    if result['skew_k'] <= 1e-10:
        saddle = linalg.eigvalsh(scaled_kkt)
        floor = 1e-12*max(abs(saddle[0]),abs(saddle[-1]))
        result['scaled_kkt_inertia'] = {
            'negative':int(np.count_nonzero(saddle < -floor)),
            'zero':int(np.count_nonzero(np.abs(saddle) <= floor)),
            'positive':int(np.count_nonzero(saddle > floor))}
    if all(result[name] <= 1e-10 for name in ('skew_k','skew_krr','skew_ke')):
        spectrum = linalg.eigvalsh(ke_scaled)
        result['ke_min_eigen_ratio'] = float(spectrum[0]/max(abs(spectrum[-1]),1e-30))
        if spectrum[0] > 1e-12*max(abs(spectrum[-1]),1e-30):
            scaled_physical = linalg.solve(ke_scaled,
                                           sq[:np_,None]*cu,assume_a='gen')
            physical = cl@(sq[:np_,None]*scaled_physical)
            exact = physical+sr
            # No averaging: the eigen route is admitted only if the actual
            # assembled representation satisfies its symmetry obligation.
            def spectral_report(matrix):
                asymmetry = float(np.linalg.norm(matrix-matrix.T)/
                                  max(np.linalg.norm(matrix),1e-30))
                if asymmetry <= 1e-10:
                    values,vectors = linalg.eigh(matrix,coupling.mass,
                                                  check_finite=True)
                    normalized = values*(210e9*.07)
                    return {'skew':asymmetry,
                            'dimensionless_eigen':normalized.tolist(),
                            'floor':float(normalized[0]),
                            'minimum_mode_coefficients':vectors[:,0].tolist(),
                            'negative_count':int(np.count_nonzero(normalized < -1e-10)),
                            'near_zero_count':int(np.count_nonzero(
                                np.abs(normalized) <= 1e-10))}
                singular_values = linalg.svdvals(
                    linalg.solve_triangular(lower_mass,matrix,lower=True)
                    @linalg.solve_triangular(lower_mass,np.eye(len(matrix)),
                                              lower=True).T)
                return {'skew':asymmetry,
                        'dimensionless_whitened_singular':(
                            singular_values*(210e9*.07)).tolist()}
            result['physical_schur'] = spectral_report(physical)
            result['exact_signed_schur'] = spectral_report(exact)
    else:
        result['conservative_spectrum_status'] = 'INADMISSIBLE_ASYMMETRIC_TANGENT'
    return result, full


def gap_and_oscillation(beam: Fixture, shell: ShellPanel, space: Space,
                        coupling: Coupling, solution: np.ndarray):
    """Physical gap and multiplier smoothness, with one-sided knot values."""
    ns = shell.free_count
    nbeam = beam.context.count
    primal_count = ns+len(beam.physical)+len(beam.internal)
    q = solution[:primal_count]
    coeffs = solution[primal_count:].reshape(space.dimension,3)
    displacement = np.zeros(shell.dof_count)
    displacement[shell.free] = q[:ns]
    native = np.zeros(nbeam)
    native[np.r_[beam.physical,beam.internal]] = q[ns:]
    scale = np.diag((1.,1.,ELL))
    def physical_gap(s):
        return scale@(beam.planar_trace_jacobian(float(s))@native
                      -shell.trace(float(s))@displacement)
    gauss_x, gauss_w = GAUSS_4
    gap_squared = 0.
    direct_work = 0.
    derivative_squared = np.zeros(3)
    multiplier_squared = np.zeros(3)
    samples = []
    gap_field = []
    for a,b in zip(coupling.integration_knots[:-1],
                   coupling.integration_knots[1:]):
        for xi,wi in zip(gauss_x,gauss_w):
            s = .5*(a+b)+.5*(b-a)*xi
            weight = .5*(b-a)*wi
            g = physical_gap(s)
            samples.append(float(np.linalg.norm(g)))
            gap_field.append([float(s),*map(float,g)])
            gap_squared += weight*float(g@g)
            field = space.at(s)@coeffs
            direct_work += weight*float(field@g)
            slope = space.derivative(s)@coeffs
            multiplier_squared += weight*field**2
            derivative_squared += weight*slope**2
    jump_squared = np.zeros(3)
    for s in space.basis_knots[1:-1]:
        before = space.at(s,side='left')@coeffs
        after = space.at(s,side='right')@coeffs
        jump_squared += (after-before)**2
    for s in coupling.integration_knots:
        samples.append(float(np.linalg.norm(physical_gap(float(s)))))
        if 0 < s < 1:
            delta = min(1e-10, .01*np.min(np.diff(coupling.integration_knots)))
            samples.extend((float(np.linalg.norm(physical_gap(float(s-delta)))),
                            float(np.linalg.norm(physical_gap(float(s+delta))))))
    u = 1e6/(210e9*.07)
    assembled_work = float(solution[primal_count:]@(
        coupling.matrix@q))
    return {'max_pointwise_gap':max(samples)/u,
            'normalized_l2_gap':np.sqrt(gap_squared)/u,
            'four_point_gap_field_m':gap_field,
            'assembled_work_quadrature_error':float(abs(direct_work-assembled_work)
                /max(abs(direct_work),abs(assembled_work),1e6*u)),
            'oscillation_by_channel':(
                np.sqrt(derivative_squared+jump_squared)
                /np.maximum(np.sqrt(multiplier_squared),1e6)).tolist(),
            'derivative_part':derivative_squared.tolist(),
            'jump_part':jump_squared.tolist()}


def screen_mesh(n_beam: int, n_shell: int, topology: str):
    """Preparatory inventory calculation; call only from a frozen gate runner.

    No blanket exception handler: ownership/programming/memory/cancellation
    failures must propagate. Candidate singularity is a negative observation.
    """
    import warnings
    beam = build(n_beam)
    shell = make_shell(n_shell,topology)
    result = {'beam_half_cells':n_beam,'shell_x_intervals':2*n_shell,
              'shell':shell.diagnostics(),
              'native_assembly_parity':beam.dense_oracle_max_error,
              'cases':[]}
    u = 1e6/(210e9*.07)
    row_width = 2*n_shell+1
    stations = sorted(set((.337, .5-1e-7, .5+1e-7)))
    pose = []
    for s in stations:
        shell_direction = np.zeros(shell.dof_count)
        hosts = shell.sample_weights(s)
        lower = int(np.argmax(np.max(hosts[:2,:row_width],axis=0)))
        upper = 2*row_width+int(np.argmax(
            np.max(hosts[2:,2*row_width:],axis=0)))
        if hosts[:2,lower].max() < .01 or hosts[2:,upper].max() < .01:
            raise AssertionError('differential rail probe has inactive host')
        shell_direction[2*lower] = u
        shell_direction[2*upper] = -u
        yaw_amplitude = abs((shell.trace(s)@shell_direction)[2])
        if yaw_amplitude < .01*u/ELL:
            raise AssertionError('differential rail yaw probe is inactive')
        beam_direction = np.zeros(beam.context.count)
        e,cell,_,_ = beam._locate(s)
        # Separate retained-cell yaw probe in the cell containing this
        # station; no native fixed root is changed.
        beam_direction[beam.context.nodal_count+24*e+3*cell+2] = u/ELL
        if abs((beam.planar_trace_jacobian(s)@beam_direction)[2]) < .01*u/ELL:
            raise AssertionError('retained yaw probe is inactive')
        pose.append({'station':s,
                     'host_weight_error':independent_sample_hosts(shell,s),
                     'derivative':supported_pose_derivative(
                         beam,shell,s,shell_direction,beam_direction,h=1e-3),
                     'work':supported_pose_work(
                         beam,shell,s,shell_direction,beam_direction,
                         np.array((.8e6,-.35e6,.21e6)),h=1e-3),
                     'unrestricted_rigid':unrestricted_common_patch(
                         beam,shell,s,Rotation.from_euler('z',.002).as_matrix()[:2,:2]
                         -np.eye(2),
                         np.array((.003,-.001))),
                     'unrestricted_affine':unrestricted_common_patch(
                         beam,shell,s,np.array(((.004,.001),(.001,-.002))),
                         np.array((.003,-.001)))})
    if topology == 'S3-V2D':
        diagonal = next((float(s) for s in shell.breakpoints()
                         if .3 < s < .4),None)
        if diagonal is not None:
            pose.extend({'station':diagonal+d,
                         'host_weight_error':independent_sample_hosts(
                             shell,diagonal+d)} for d in (-1e-8,1e-8))
    result['pose_probes'] = pose
    for space in spaces(beam,shell):
        coupling = assemble(beam,shell,space)
        reference = reference_consistency(beam,shell,coupling)
        case = {'space':space.name, 'basis_dimension':space.dimension,
                'basis_knots':space.basis_knots.tolist(),
                'integration_knots':coupling.integration_knots.tolist(),
                'quadrature':coupling.quadrature_error,
                'reference_consistency':reference,
                'loads':{}}
        try:
            rank_context = candidate_rank_context(beam,shell,coupling)
        except linalg.LinAlgError as failure:
            case['rank_failure'] = {'type':type(failure).__name__,
                                    'message':str(failure)}
            case['loads'] = {kind:{'status':'CONSTRAINT_MASS_INVALID'}
                             for kind in ('smooth','alternating')}
            result['cases'].append(case)
            continue
        case['rank_context'] = rank_context
        if rank_context['row_rank'] < rank_context['rows']:
            case['loads'] = {kind:{'status':'CONSTRAINT_RANK_LOSS',
                                   'rank_context':rank_context}
                             for kind in ('smooth','alternating')}
            result['cases'].append(case)
            continue
        for kind,load in (('smooth',coupling.load_smooth),
                          ('alternating',coupling.load_alternating)):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error',linalg.LinAlgWarning)
                    measure,solution = solve_exact(beam,shell,coupling,load)
                physical = gap_and_oscillation(beam,shell,space,
                                               coupling,solution)
                balance = physical_support_balance(beam,shell,coupling,
                                                   solution,kind)
                measure.update(physical)
                measure['support_balance'] = balance
                measure['status'] = restricted_disposition(
                    measure,rank_context,reference,pose,balance)
            except (linalg.LinAlgError,linalg.LinAlgWarning,
                    CandidateSingular) as failure:
                measure = {'status':('KKT_SINGULAR_OR_ILL_CONDITIONED'
                                     if isinstance(failure,CandidateSingular)
                                     else 'NUMERICAL_CANDIDATE_FAILURE'),
                           'rank_context':rank_context,
                           'failure_type':type(failure).__name__,
                           'failure':str(failure)}
            except PrimalNotAdmissible as failure:
                measure = {'status':'PRIMAL_NOT_ADMISSIBLE',
                           'rank_context':rank_context,
                           'failure_type':type(failure).__name__,
                           'failure':str(failure)}
            case['loads'][kind] = measure
        result['cases'].append(case)
    return result


def physical_support_balance(beam: Fixture, shell: ShellPanel,
                             coupling: Coupling, solution: np.ndarray,
                             load_kind: str):
    """Recover fixed reactions from unrestricted residual/constraint rows."""
    n_shell = shell.dof_count
    n_beam = beam.context.count
    n_free = shell.free_count+len(beam.physical)+len(beam.internal)
    q_all = np.zeros(n_shell+n_beam)
    q_all[shell.free] = solution[:shell.free_count]
    q_all[n_shell+np.r_[beam.physical,beam.internal]] = (
        solution[shell.free_count:n_free])
    multiplier = solution[n_free:]
    load = {'smooth':coupling.full_load_smooth,
            'alternating':coupling.full_load_alternating}[load_kind]
    r_all = np.r_[shell.stiffness@q_all[:n_shell],
                   beam.tangent@q_all[n_shell:]]
    r_all += coupling.full_constraint.T@multiplier-load
    fixed_shell = np.setdiff1d(np.arange(n_shell),shell.free)
    fixed_beam = np.asarray(sorted(beam.context.fixed),dtype=int)+n_shell
    fixed = np.r_[fixed_shell,fixed_beam]
    reaction = np.zeros_like(r_all)
    reaction[fixed] = r_all[fixed]
    nx = shell.x_interval_count
    xy = np.asarray([(float(-.5+i/shell.n_s),y)
                     for y in (-.5,0.,.5) for i in range(nx+1)])
    def wrench(vector):
        shell_force = vector[:n_shell].reshape(-1,2)
        forces = shell_force.sum(axis=0)
        moment = np.sum(xy[:,0]*shell_force[:,1]
                        -xy[:,1]*shell_force[:,0])
        native = vector[n_shell:n_shell+beam.context.nodal_count].reshape(-1,6)
        forces += native[:,:2].sum(axis=0)
        positions = np.arange(beam.n_half_cells+1)/beam.n_half_cells
        moment += np.sum(positions*native[:,1]+native[:,5])
        return np.r_[forces,moment]
    applied = wrench(load)
    supports = wrench(reaction)
    residual = applied+supports
    shell_energy = .5*float(q_all[:n_shell]@(
        shell.stiffness@q_all[:n_shell]))
    return {'applied_wrench':applied.tolist(),
            'support_wrench':supports.tolist(),
            'active_physical_shell_energy_j':shell_energy,
            'normalized_force_balance':float(np.linalg.norm(residual[:2])/
                    max(np.linalg.norm(applied[:2]),
                        np.linalg.norm(supports[:2]),1e6)),
            'normalized_moment_balance':float(abs(residual[2])/
                    max(abs(applied[2]),abs(supports[2]),1e6)),
            'max_free_residual':float(np.max(np.abs(r_all[np.setdiff1d(
                np.arange(len(r_all)),fixed)])))}


def reference_consistency(beam: Fixture, shell: ShellPanel,
                          coupling: Coupling):
    """Independent six-component pose gap at every assembled station."""
    x,_ = GAUSS_4
    translations, rotations = [], []
    zero_s = np.zeros(shell.dof_count)
    zero_b = np.zeros(beam.context.count)
    for a,b in zip(coupling.integration_knots[:-1],
                   coupling.integration_knots[1:]):
        for gauss in x:
            s = float(.5*(a+b)+.5*(b-a)*gauss)
            gap = actual_pose_gap(beam,shell,s,zero_s,zero_b)
            translations.append(float(np.max(np.abs(gap[:3]))))
            rotations.append(float(np.max(np.abs(gap[3:]))))
    return {'stations':len(translations),
            'max_translation_m':max(translations),
            'max_rotation_rad':max(rotations)}


def candidate_rank_context(beam: Fixture, shell: ShellPanel,
                           coupling: Coupling):
    """Retain rank evidence even when the subsequent KKT factorization fails."""
    sq,_ = scales(beam,shell,coupling.matrix.shape[0])
    lower = linalg.cholesky(coupling.mass,lower=True,check_finite=True)
    whitened = linalg.solve_triangular(
        lower,coupling.matrix.toarray()*sq[None,:],lower=True)
    row_singular = linalg.svdvals(whitened)
    trace_singular = linalg.svdvals(coupling.trace_factor*sq[None,:])
    def rank(singular):
        return int(np.count_nonzero(singular > 1e-10*singular[0]))
    return {'rows':int(coupling.matrix.shape[0]),
            'row_rank':rank(row_singular),
            'trace_rank':rank(trace_singular),
            'trace_minus_row_rank':rank(trace_singular)-rank(row_singular),
            'minimum_mass_whitened_row_ratio':float(
                row_singular[-1]/row_singular[0])}


def complete_inventory(on_mesh=None):
    """All 18 physical meshes, five spaces and two registered loads.

    This calculates diagnostic rows only. The caller must bind source,
    dependencies, resources and immutable execution evidence beforehand.
    """
    rows = []
    for topology in ('Q4','S3-V2D'):
        for ratio in (.5,1.,2.):
            for n in (4,8,16):
                row = screen_mesh(n,int(n*ratio),topology)
                rows.append(row)
                if on_mesh is not None:
                    on_mesh(row)
    trends = []
    for topology in ('Q4','S3-V2D'):
        for ratio in (.5,1.,2.):
            triple = [next(row for row in rows
                           if row['shell']['topology'] == topology
                           and row['beam_half_cells'] == n
                           and row['shell']['n_s'] == int(n*ratio))
                      for n in (4,8,16)]
            for name in SPACES:
                candidates = [next(c for c in row['cases']
                                   if c['space'] == name) for row in triple]
                smooth = [c['loads']['smooth'] for c in candidates]
                alternating = [c['loads']['alternating'] for c in candidates]
                def values(solutions, key):
                    if any(key not in item for item in solutions):
                        return None
                    result = [float(item[key]) for item in solutions]
                    return result if all(np.isfinite(result)) else None
                pointwise = values(smooth,'max_pointwise_gap')
                oscillation = None
                if all('oscillation_by_channel' in item for item in alternating):
                    oscillation = [max(item['oscillation_by_channel'])
                                   for item in alternating]
                    if not all(np.isfinite(oscillation)):
                        oscillation = None
                beta = None
                if all('floor' in item.get('physical_schur',{}) for item in smooth):
                    beta = [float(item['physical_schur']['floor'])
                            for item in smooth]
                    if not all(np.isfinite(beta)):
                        beta = None
                local_statuses = {'smooth':[item['status'] for item in smooth],
                                  'alternating':[item['status'] for item in alternating]}
                complete_local = all(
                    status == 'RESTRICTED_LOCAL_SCREEN_PASS_PENDING_TRENDS'
                    for statuses in local_statuses.values() for status in statuses)
                decreasing = (beta is not None and beta[0] > 0
                              and beta[1] <= .5*beta[0]
                              and beta[2] <= .5*beta[1])
                stuck_gap = (pointwise is not None and pointwise[0] > 0
                             and pointwise[1] >= .99*pointwise[0]
                             and pointwise[2] >= .99*pointwise[1])
                growing_oscillation = (
                    oscillation is not None and oscillation[0] > 0
                    and oscillation[1] >= 2*oscillation[0]
                    and oscillation[2] >= 2*oscillation[1])
                disposition = ('INCOMPLETE_OR_LOCAL_FAILURE'
                               if not complete_local else
                               'ZERO_BASELINE_TREND_UNDEFINED'
                               if any(series is None or series[0] <= 0
                                      for series in (beta,pointwise,oscillation)) else
                               'MECHANICS_REVIEW_REQUIRED'
                               if stuck_gap or growing_oscillation else
                               'DECAYING_PHYSICAL_FLOOR'
                               if decreasing else 'INCONCLUSIVE_TREND')
                trends.append({'topology':topology,'ratio':ratio,
                               'space':name,'beam_half_cells':[4,8,16],
                               'local_statuses':local_statuses,
                               'physical_only_floor':beta,
                               'smooth_max_pointwise_gap':pointwise,
                               'alternating_max_channel_oscillation':oscillation,
                               'decaying_physical_floor':bool(decreasing),
                               'nondecreasing_pointwise_gap':bool(stuck_gap),
                               'growing_alternating_oscillation':bool(growing_oscillation),
                               'disposition':disposition})
    status_counts = {}
    for row in rows:
        for candidate in row['cases']:
            for measurement in candidate['loads'].values():
                status = measurement['status']
                status_counts[status] = status_counts.get(status,0)+1
    any_local = status_counts.get(
        'RESTRICTED_LOCAL_SCREEN_PASS_PENDING_TRENDS',0) > 0
    return {'status':('PLANAR_SCREEN_HAS_LOCAL_PASSES_NOT_F03_ACCEPTANCE'
                      if any_local else
                      'PLANAR_SCREEN_NO_LOCAL_PASS_NOT_F03_ACCEPTANCE'),
            'status_counts':status_counts,
            'mesh_count':len(rows),'candidate_count':sum(len(r['cases'])
                for r in rows),'load_rows':sum(len(c['loads'])
                for r in rows for c in r['cases']),
            'meshes':rows,'trends':trends}


def restricted_disposition(measure: dict, context: dict,
                           reference: dict, probes: list[dict],
                           balance: dict) -> str:
    """Local planar-screen predicates; no F03/G0 acceptance or space choice."""
    required = ('cond_krr','ke_min_eigen_ratio','skew_k','skew_krr',
                'skew_ke','scaled_kkt_singular_ratio','scaled_solution_parity',
                'scaled_free_equilibrium','normalized_weak_residual',
                'assembled_work_quadrature_error')
    diagnostic_values = ([measure.get(k,np.nan) for k in required]
        +list(measure['quadrature_error'].values())
        +[context['minimum_mass_whitened_row_ratio'],
          reference['max_translation_m'],reference['max_rotation_rad'],
          balance['normalized_force_balance'],
          balance['normalized_moment_balance'],
          balance['active_physical_shell_energy_j'],
          measure.get('max_pointwise_gap',np.nan),
          measure.get('normalized_l2_gap',np.nan),
          measure.get('assembled_work_quadrature_error',np.nan)]
        +list(measure.get('oscillation_by_channel',(np.nan,)))
        +list(measure.get('derivative_part',(np.nan,)))
        +list(measure.get('jump_part',(np.nan,)))
        +[v for row in measure.get('four_point_gap_field_m',((np.nan,),))
          for v in row])
    for probe in probes:
        diagnostic_values.append(probe['host_weight_error'])
        if 'derivative' in probe:
            diagnostic_values.extend((
                probe['derivative']['scaled_relative_error'],
                probe['work']['normalized_gradient_error'],
                probe['unrestricted_rigid']['finite_gap'],
                probe['unrestricted_affine']['finite_gap']))
    if not all(np.isfinite(value) for value in diagnostic_values):
        return 'INVALID_NONFINITE_DIAGNOSTIC'
    if context['row_rank'] != context['rows']:
        return 'CONSTRAINT_RANK_LOSS'
    if (measure.get('cond_krr',np.inf) >= 1e16
            or measure.get('ke_min_eigen_ratio',-np.inf) <= 1e-12
            or any(measure.get(n,np.inf) > 1e-10
                   for n in ('skew_k','skew_krr','skew_ke'))):
        return 'PRIMAL_NOT_ADMISSIBLE'
    if measure.get('scaled_kkt_singular_ratio',0.) <= 1e-12:
        return 'KKT_SINGULAR_OR_ILL_CONDITIONED'
    physical_spectrum = measure.get('physical_schur',{})
    exact_spectrum = measure.get('exact_signed_schur',{})
    if ('floor' not in physical_spectrum
            or not np.isfinite(physical_spectrum['floor'])
            or physical_spectrum['floor'] <= 1e-12
            or 'dimensionless_eigen' not in exact_spectrum
            or not all(np.isfinite(v) for v in
                physical_spectrum['dimensionless_eigen']
                + exact_spectrum['dimensionless_eigen'])):
        return 'MECHANICS_REVIEW_REQUIRED'
    thresholds = (
        (reference['max_translation_m'],1e-12),
        (reference['max_rotation_rad'],1e-12),
        (measure.get('scaled_solution_parity',np.inf),1e-10),
        (measure.get('scaled_free_equilibrium',np.inf),1e-9),
        (measure.get('normalized_weak_residual',np.inf),1e-10),
        (measure.get('assembled_work_quadrature_error',np.inf),1e-10),
        (balance['normalized_force_balance'],1e-8),
        (balance['normalized_moment_balance'],1e-8),
    )
    if any(not np.isfinite(value) or value > limit for value,limit in thresholds):
        return 'RESTRICTED_MECHANICS_FAIL'
    if (any(not np.isfinite(error) or error > 1e-10
            for error in measure['quadrature_error'].values())
            or any(probe.get('host_weight_error',np.inf) > 1e-12
                   for probe in probes)
            or any(probe['derivative']['scaled_relative_error'] > 1e-10
                   or probe['work']['normalized_gradient_error'] > 1e-10
                   or probe['unrestricted_rigid']['finite_gap'] > 1e-10
                   or probe['unrestricted_affine']['finite_gap'] > 1e-10
                   for probe in probes if 'derivative' in probe)):
        return 'RESTRICTED_MECHANICS_FAIL'
    return 'RESTRICTED_LOCAL_SCREEN_PASS_PENDING_TRENDS'


if __name__ == '__main__':
    raise SystemExit('F03-K0 execution is not registered; freeze the gate first')
