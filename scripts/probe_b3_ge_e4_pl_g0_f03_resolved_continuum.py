"""Exploratory independent membrane/Timoshenko coupled response, not F03 evidence.

The panel uses classical Q4 or CST plane stress. A conventional
two-node Timoshenko beam has physical (u,v,theta) nodes, unlike the native
retained B3 operator. Stiffness, equivalent line load and station traces
use its homogeneous exact-static interior field. This is still a finite
station collocation, not the sought continuous mortar line law.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

from probe_b3_ge_e4_pl_g0_f03_independent_membrane import continuum_stiffness


E = 210e9
NU = .3
G = E / (2 * (1 + NU))
AREA = .01
SHEAR_AREA = .008
INERTIA = 8.333333333333333e-6
OFFSETS = ((-.2, -.23), (.2, -.23), (.2, .23), (-.2, .23))
YAW_DENOMINATOR = 4 * (.2**2 + .23**2)


def panel(n: int, n_y: int, topology: str):
    """Assemble classical membrane blocks independently of E4-PL."""
    nx = 2 * n
    points = np.array([(x, y) for y in np.linspace(-.5, .5, n_y+1)
                       for x in np.linspace(-.5, 1.5, nx + 1)])
    rows, columns, data = [], [], []
    for j in range(n_y):
        for i in range(nx):
            a = j * (nx + 1) + i
            b, d = a + 1, a + nx + 1
            c = d + 1
            for nodes in (((a, b, c, d),) if topology == 'Q4'
                          else ((a, b, c), (a, c, d))):
                dofs = [2 * node + axis for node in nodes for axis in (0, 1)]
                local = continuum_stiffness(points[list(nodes)], topology)
                for lr, gr in enumerate(dofs):
                    for lc, gc in enumerate(dofs):
                        rows.append(gr)
                        columns.append(gc)
                        data.append(local[lr, lc])
    nd = 2 * len(points)
    k = sparse.coo_matrix((data, (rows, columns)), shape=(nd, nd)).tocsr()
    free = np.array([2 * (j * (nx + 1) + i) + axis
                     for j in range(n_y+1) for i in range(1, nx)
                     for axis in (0, 1)])
    return points, k, free


def beam(n: int):
    """Exact static Timoshenko two-node stiffness for constant section."""
    h = 1 / n
    phi = 12 * E * INERTIA / (G * SHEAR_AREA * h**2)
    flex = E * INERTIA / (h**3 * (1 + phi)) * np.array([
        [12, 6*h, -12, 6*h],
        [6*h, (4+phi)*h*h, -6*h, (2-phi)*h*h],
        [-12, -6*h, 12, -6*h],
        [6*h, (2-phi)*h*h, -6*h, (4+phi)*h*h],
    ])
    local = np.zeros((6, 6))
    local[np.ix_((0, 3), (0, 3))] = E * AREA / h * np.array([[1, -1], [-1, 1]])
    local[np.ix_((1, 2, 4, 5), (1, 2, 4, 5))] = flex
    rows, columns, data = [], [], []
    for i in range(n):
        dofs = tuple(range(3*i, 3*i+6))
        for lr, gr in enumerate(dofs):
            for lc, gc in enumerate(dofs):
                rows.append(gr)
                columns.append(gc)
                data.append(local[lr, lc])
    k = sparse.coo_matrix((data, (rows, columns)),
                          shape=(3*(n+1), 3*(n+1))).tocsr()
    return k, np.arange(3, 3*(n+1))


def beam_segment_pose(x: float, h: float, nodal: np.ndarray):
    """Homogeneous Timoshenko field and its derivatives from endpoint data.

    EI*theta''=-V, V=kGA*(v'-theta), with constant shear V. Distributed
    loads enter through virtual work against these homogeneous test fields;
    the missing particular solution converges under beam refinement.
    """
    u0, v0, theta0, u1, v1, theta1 = nodal
    delta_theta = theta1-theta0
    shear = ((v1-v0)-h*(theta0+theta1)/2) / (
        h**3/(12*E*INERTIA)+h/(G*SHEAR_AREA))
    u = (1-x/h)*u0 + (x/h)*u1
    theta = theta0 + delta_theta*x/h + shear*(h*x-x*x)/(2*E*INERTIA)
    v = (v0 + theta0*x + delta_theta*x*x/(2*h) + shear*(
        h*x*x/(4*E*INERTIA)-x**3/(6*E*INERTIA)+x/(G*SHEAR_AREA)))
    theta_prime = delta_theta/h + shear*(h-2*x)/(2*E*INERTIA)
    return np.array((u, v, theta)), theta_prime, shear


def beam_trace(s: float, n: int):
    """Exact-static field map at a material station, global 3-by-3(n+1)."""
    h = 1/n
    i = min(int(np.floor(s*n + 1e-11)), n-1)
    x = s-i*h
    out = np.zeros((3, 3*(n+1)))
    for local in range(6):
        basis = np.zeros(6)
        basis[local] = 1.
        out[:, 3*i+local] = beam_segment_pose(x, h, basis)[0]
    return out


def _host(x, y, n: int, n_y: int, topology: str):
    """Return independent physical interpolation on the structured panel."""
    nx = 2*n
    dx = 1/n
    i = int(np.clip(np.floor((x+.5)/dx - 1e-12), 0, nx-1))
    dy = 1/n_y
    j = int(np.clip(np.floor((y+.5)/dy - 1e-12), 0, n_y-1))
    a = j*(nx+1)+i
    b, d = a+1, a+nx+1
    c = d+1
    r = (x - (-.5+i*dx))/dx
    t = (y - (-.5+j*dy))/dy
    if not (-1e-10 <= r <= 1+1e-10 and -1e-10 <= t <= 1+1e-10):
        raise AssertionError('host outside panel')
    if topology == 'Q4':
        return ((a, b, c, d), ((1-r)*(1-t), r*(1-t), r*t, (1-r)*t))
    return (((a, b, c), (1-r, r-t, t)) if t <= r
            else ((a, c, d), (1-t, r, t-r)))


def shell_trace(s: float, n: int, n_y: int, topology: str, node_count: int):
    trace = np.zeros((3, 2*node_count))
    for ox, y in OFFSETS:
        ids, weights = _host(s+ox, y, n, n_y, topology)
        for node, weight in zip(ids, weights):
            trace[0, 2*node] += weight/4
            trace[1, 2*node+1] += weight/4
            trace[2, 2*node] -= y*weight/YAW_DENOMINATOR
            trace[2, 2*node+1] += ox*weight/YAW_DENOMINATOR
    return trace


def gap_knots(n_shell: int, n_y: int, n_beam: int, topology: str):
    """All shell/beam field breaks for a bounded gap search grid."""
    dx = 1/n_shell
    knots = [i/n_beam for i in range(n_beam+1)]
    for ox, y in OFFSETS:
        eta = ((y+.5)*n_y) % 1
        for i in range(2*n_shell+1):
            edge = -.5 + i*dx
            knots.append(edge-ox)
            if topology == 'S3-V2D' and i < 2*n_shell:
                knots.append(edge + eta*dx-ox)
    return np.unique(np.round([min(1., max(0., s)) for s in knots
                               if -1e-12 <= s <= 1+1e-12], 13))


def load_vector(n: int, kind: str):
    """Virtual-work-consistent load for the exact-static beam test field."""
    f = np.zeros(3*(n+1))
    stations, weights = np.polynomial.legendre.leggauss(8)
    for i in range(n):
        for xi, weight in zip(stations, weights):
            s = (i + (xi+1)/2)/n
            if kind == 'smooth':
                q = 1e6*(1+.25*np.cos(2*np.pi*s))
            elif kind == 'sine':
                q = 1e6*np.sin(2*np.pi*s)
            else:
                raise ValueError('unknown load')
            shape = beam_trace(s, n)[1]
            f += weight*q/(2*n)*shape
    return f


def self_check():
    """Analytic one-element beam flexibility and independent rigid pose patch."""
    kb, free = beam(1)
    force = np.zeros(6)
    force[4] = 1.
    tip = np.linalg.solve(kb[free, :][:, free].toarray(), force[free])
    expected = 1/(3*E*INERTIA) + 1/(G*SHEAR_AREA)
    if not np.isclose(tip[1], expected, rtol=2e-12):
        raise AssertionError('Timoshenko cantilever flexibility identity')
    h = .375
    sample = np.array((.1, -.2, .03, .11, -.19, -.05))
    left, _, _ = beam_segment_pose(0., h, sample)
    right, _, _ = beam_segment_pose(h, h, sample)
    if not np.allclose(np.r_[left, right], sample, rtol=0, atol=3e-16):
        raise AssertionError('beam exact-static field endpoint interpolation')
    # Independent integrated elastic-energy identity for an arbitrary pose.
    sample_energy = 0.
    stations, weights = np.polynomial.legendre.leggauss(5)
    for xi, weight in zip(stations, weights):
        _, theta_prime, shear = beam_segment_pose(h*(xi+1)/2, h, sample)
        sample_energy += weight*h/2*(E*INERTIA*theta_prime**2
                                     + shear**2/(G*SHEAR_AREA))
    # Compare with the independently formed one-element bending matrix.
    phi = 12*E*INERTIA/(G*SHEAR_AREA*h*h)
    flex = E*INERTIA/(h**3*(1+phi))*np.array((
        (12,6*h,-12,6*h),
        (6*h,(4+phi)*h*h,-6*h,(2-phi)*h*h),
        (-12,-6*h,12,-6*h),
        (6*h,(2-phi)*h*h,-6*h,(4+phi)*h*h)))
    expected_energy = sample[[1,2,4,5]]@flex@sample[[1,2,4,5]]
    if not np.isclose(sample_energy, expected_energy, rtol=1e-12):
        raise AssertionError('beam exact-static field energy identity')
    for topology in ('Q4', 'S3-V2D'):
        points, _, _ = panel(2, 4, topology)
        for s in (0., .125, .35, .875, 1.):
            trace = shell_trace(s, 2, 4, topology, len(points))
            ux, uy, angle = .3, -.4, .07
            displacement = np.column_stack((ux-angle*points[:, 1],
                                            uy+angle*points[:, 0])).ravel()
            if not np.allclose(trace@displacement,
                               (ux-angle*0., uy+angle*s, angle),
                               rtol=0, atol=2e-14):
                raise AssertionError('four-sample rigid pose patch')


def solve(topology: str, n_shell: int, n_beam: int, kind: str, n_y: int = 2):
    points, ks, sf = panel(n_shell, n_y, topology)
    kb, bf = beam(n_beam)
    fs = np.zeros(ks.shape[0])
    fb = load_vector(n_beam, kind)
    matrices = sparse.block_diag((ks[sf, :][:, sf], kb[bf, :][:, bf]),
                                 format='csr')
    loads = np.r_[fs[sf], fb[bf]]
    cs, cb = [], []
    for i in range(n_beam+1):
        s = i/n_beam
        t = shell_trace(s, n_shell, n_y, topology, len(points))
        b = beam_trace(s, n_beam)
        cs.append(t)
        cb.append(b)
    c_shell, c_beam = np.vstack(cs), np.vstack(cb)
    c = sparse.csr_matrix(np.hstack((-c_shell[:, sf], c_beam[:, bf])))
    # Bounded row-space diagnostic only. This is not a signed KKT inf-sup
    # result or a production dense operation; rows are normalized after the
    # physical one-metre moment/translation choice.
    gram = (c@c.T).toarray()
    row_norm = np.sqrt(np.diag(gram))
    gram /= row_norm[:, None]*row_norm[None, :]
    gram_spectrum = np.linalg.eigvalsh(gram)
    row_gram_ratio = float(max(0., gram_spectrum[0])/gram_spectrum[-1])
    # Physical coordinates use a common 1e-5 m/rad perturbation scale (the
    # characteristic length is one metre). Force and moment both use 1e6
    # N/Nm; consequently work is 10 J and physical multiplier=1e6*dual.
    # This is a dual-consistent congruence, not a stiffness alteration.
    coordinate_scale = 1e-5
    work_scale = 10.
    gap_scale = 1e-5
    full = sparse.bmat(((matrices*(coordinate_scale**2/work_scale),
                         c.T*(coordinate_scale/gap_scale)),
                        (c*(coordinate_scale/gap_scale), None)), format='csc')
    rhs = np.r_[loads*(coordinate_scale/work_scale), np.zeros(c.shape[0])]
    solution = spsolve(full, rhs)
    if not np.all(np.isfinite(solution)):
        raise AssertionError('singular or nonfinite coupled result')
    u = solution[:len(loads)]*coordinate_scale
    lam = solution[len(loads):]*(work_scale/gap_scale)
    us = np.zeros(ks.shape[0])
    ub = np.zeros(kb.shape[0])
    us[sf], ub[bf] = u[:len(sf)], u[len(sf):]
    eq = matrices@u + c.T@lam - loads
    gap = c@u
    reaction_shell = ks@us - c_shell.T@lam - fs
    reaction_beam = kb@ub + c_beam.T@lam - fb
    # Actual interface force applied to each domain is -C_domain.T*lambda;
    # C_shell=-trace, C_beam=+trace in the KKT residual convention.
    shell_interface_work = float(lam@(c_shell@us))
    beam_interface_work = float(-lam@(c_beam@ub))
    shell_fixed = np.setdiff1d(np.arange(ks.shape[0]), sf)
    beam_fixed = np.setdiff1d(np.arange(kb.shape[0]), bf)
    shell_force = np.array([reaction_shell[shell_fixed[axis::2]].sum()
                            for axis in (0, 1)])
    beam_force = reaction_beam[:2]
    support_force = shell_force + beam_force
    shell_moment = sum(points[i, 0]*reaction_shell[2*i+1] -
                       points[i, 1]*reaction_shell[2*i]
                       for i in range(len(points)) if 2*i in shell_fixed)
    support_moment = shell_moment + reaction_beam[2]
    external_moment = sum((i/n_beam)*fb[3*i+1]+fb[3*i+2]
                          for i in range(n_beam+1))
    work = float(loads@u)
    se = float(us@ks@us/2)
    be = float(ub@kb@ub/2)
    probes = []
    continuous_gap = np.zeros(3)
    # The exact-static beam trace is cubic/quadratic within a cell, while
    # the shell trace is piecewise affine. Search interval endpoints and
    # fitted polynomial stationary points, independently checking the fit.
    # These floating-point extrema are estimates, not certified enclosures.
    breaks = gap_knots(n_shell, n_y, n_beam, topology)
    search_stations = np.unique(np.concatenate((breaks,
        np.concatenate([np.linspace(a, b, 17) for a, b in zip(breaks[:-1], breaks[1:])]))))
    def gap_at(s):
        pose = shell_trace(float(s), n_shell, n_y, topology, len(points))@us
        return beam_trace(float(s), n_beam)@ub - pose

    nodes = np.array((0., 1/3, 2/3, 1.))
    vandermonde = np.vander(nodes, 4, increasing=True)
    extrema_stations = list(breaks)
    interpolation_error = 0.
    for a, b in zip(breaks[:-1], breaks[1:]):
        coefficients = np.linalg.solve(vandermonde,
                                       np.array([gap_at(a+(b-a)*t) for t in nodes]))
        interpolation_error = max(interpolation_error, float(np.max(np.abs(
            gap_at((a+b)/2) - np.array((1., .5, .25, .125))@coefficients))))
        for component in range(3):
            polynomial = coefficients[:, component]
            for root in np.roots((3*polynomial[3], 2*polynomial[2], polynomial[1])):
                if abs(root.imag) < 1e-10 and 0 < root.real < 1:
                    extrema_stations.append(float(a+(b-a)*root.real))
    for s in search_stations:
        continuous_gap = np.maximum(continuous_gap, np.abs(gap_at(s)))
    extrema_gap = np.max(np.abs([gap_at(s) for s in extrema_stations]), axis=0)
    for s in (0., .125, .25, .375, .5, .625, .75, .875, 1.):
        pose = shell_trace(s, n_shell, n_y, topology, len(points))@us
        beam_pose = beam_trace(s, n_beam)@ub
        probes.append(dict(s=s, shell=[float(v) for v in pose],
                           beam=[float(v) for v in beam_pose],
                           gap=[float(v) for v in beam_pose-pose]))
    return dict(topology=topology, n_shell=n_shell, n_y=n_y,
                n_beam=n_beam, load=kind,
                model='CLASSICAL_PLANE_STRESS_EXACT_STATIC_TIMOSHENKO_FINITE_COLLOCATION',
                beam_interior_idealization='HOMOGENEOUS_EXACT_STATIC_TEST_FIELD',
                coordinate_scale=coordinate_scale, gap_scale=gap_scale,
                work_scale_j=work_scale,
                shell_nodes=len(points), beam_nodes=n_beam+1,
                multiplier_rows=c.shape[0], matrix_nnz=full.nnz,
                row_normalized_constraint_gram_eigen_ratio=row_gram_ratio,
                load_y_total=float(fb[1::3].sum()),
                load_moment_z_nm=float(external_moment),
                support_force_n=[float(v) for v in support_force],
                support_moment_z_nm=float(support_moment),
                shell_energy_j=se, beam_energy_j=be, external_work_j=work,
                shell_interface_work_j=shell_interface_work,
                beam_interface_work_j=beam_interface_work,
                energy_balance_relative=float(abs(work-2*(se+be))/max(abs(work), 1)),
                equilibrium_relative=float(np.linalg.norm(eq)/max(np.linalg.norm(loads), 1)),
                constraint_absolute=float(np.max(np.abs(gap))),
                discrete_gap_knots=len(breaks), gap_search_stations=len(search_stations),
                sampled_max_gap_lower_bound_components=[float(v) for v in continuous_gap],
                polynomial_extrema_station_count=len(extrema_stations),
                polynomial_gap_extrema_estimate_components=[float(v) for v in extrema_gap],
                max_polynomial_fit_midpoint_error=float(interpolation_error),
                station_probes=probes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topology', choices=('Q4', 'S3-V2D'), required=True)
    parser.add_argument('--n-shell', type=int, required=True)
    parser.add_argument('--n-y', type=int, default=2)
    parser.add_argument('--n-beam', type=int, required=True)
    parser.add_argument('--load', choices=('smooth', 'sine'), required=True)
    args = parser.parse_args()
    if not 1 <= args.n_shell <= 64 or not 2 <= args.n_y <= 64 or not 2 <= args.n_beam <= 64:
        raise ValueError('bounded mesh inventory required')
    self_check()
    print(json.dumps(solve(args.topology, args.n_shell, args.n_beam, args.load, args.n_y),
                     allow_nan=False, sort_keys=True))


if __name__ == '__main__':
    main()
