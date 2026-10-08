"""Independent small-strain plate/beam reference for F03 transverse work.

This bounded Ritz model imports no native shell, beam, trace, or coupling
operator. It matches their declared flat geometry, elastic resultants,
supports, and line pose *definition* in the transverse z/rx/ry subsystem.
It is a development comparator, not a native six-channel or external oracle.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.polynomial.legendre import Legendre, leggauss
from scipy.interpolate import BSpline


E = 210e9
NU = .3
G = E / (2 * (1 + NU))
THICKNESS = .07
BENDING_D = E * THICKNESS**3 / (12 * (1 - NU**2))
SHEAR_K = (5 / 6) * G * THICKNESS
BEAM_I = 8.333333333333333e-6
BEAM_J = 2 * BEAM_I
BEAM_SHEAR_AREA = .008
HALF_WINDOW = .2
HALF_RAIL = .23
SAMPLES = ((-HALF_WINDOW, -HALF_RAIL),
           (HALF_WINDOW, -HALF_RAIL),
           (HALF_WINDOW, HALF_RAIL),
           (-HALF_WINDOW, HALF_RAIL))


@lru_cache(None)
def _polynomial(order: int) -> tuple[Legendre, Legendre]:
    if type(order) is not int or order < 0:
        raise ValueError("nonnegative integer Legendre order required")
    polynomial = Legendre.basis(order)
    return polynomial, polynomial.deriv()


@lru_cache(None)
def _spline(elements: int, left: float, right: float
            ) -> tuple[BSpline, BSpline, np.ndarray]:
    """Open cubic basis; its first function is removed at a rooted edge."""
    edges = np.linspace(left, right, elements + 1)
    knots = np.r_[np.full(4, left), edges[1:-1], np.full(4, right)]
    values = BSpline(knots, np.eye(elements + 3), 3, extrapolate=False)
    return values, values.derivative(), edges


def _quadrature(order: int, edges: np.ndarray):
    for left, right in zip(edges[:-1], edges[1:]):
        yield from zip(*_gauss(order, float(left), float(right)))


def _line_edges(cell: int, intervals: int, nx: int, nb: int,
                basis: str, *, origin: str = "rail",
                director: str = "rail",
                strip_half_length: float = HALF_WINDOW) -> np.ndarray:
    left, right = cell/intervals, (cell+1)/intervals
    if basis == "global":
        return np.array((left, right))
    xedges = _spline(nx, -.5, 1.5)[2]
    bedges = _spline(nb, 0., 1.)[2]
    stations = [left, right]
    for ox, _ in SAMPLES:
        if origin == "rail" or director == "rail":
            stations.extend(float(x-ox) for x in xedges if left < x-ox < right)
    if origin == "strip" or director == "strip":
        for offset in (-strip_half_length, strip_half_length):
            stations.extend(float(x-offset) for x in xedges
                            if left < x-offset < right)
    stations.extend(float(s) for s in bedges if left < s < right)
    stations.extend(float(s) for s in xedges if left < s < right)
    return np.unique(np.round(stations, 14))


def plate_basis(nx: int, ny: int, x: float, y: float, *,
                basis: str = "global"
                ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Supported tensor trial: global Legendre or rooted local cubic."""
    if not (-.5 <= x <= 1.5 and -.5 <= y <= .5):
        raise ValueError("plate station outside declared geometry")
    if basis == "spline":
        bx, dbx, _ = _spline(nx, -.5, 1.5)
        by, dby, _ = _spline(ny, -.5, .5)
        px, dpx = bx(x)[1:], dbx(x)[1:]
        py, dpy = by(y), dby(y)
        return (np.outer(px, py).ravel(),
                np.outer(dpx, py).ravel(),
                np.outer(px, dpy).ravel())
    if basis != "global":
        raise ValueError("global or spline trial basis required")
    X = (x + .5) / 2
    px = np.array([_polynomial(i)[0](2*X-1) for i in range(nx)])
    dpx = np.array([_polynomial(i)[1](2*X-1) for i in range(nx)])
    py = np.array([_polynomial(j)[0](2*y) for j in range(ny)])
    dpy = np.array([_polynomial(j)[1](2*y) for j in range(ny)])
    value = np.outer(X*px, py).ravel()
    dx = np.outer(.5*px + X*dpx, py).ravel()
    dy = np.outer(2*X*px, dpy).ravel()
    return value, dx, dy


def plate_strain_rows(nx: int, ny: int, x: float, y: float, *,
                      basis: str = "global"
                      ) -> tuple[np.ndarray, np.ndarray]:
    """Curvatures [kx,ky,kxy] and engineering shears [gxz,gyz]."""
    v, dx, dy = plate_basis(nx, ny, x, y, basis=basis)
    n = len(v)
    bending = np.zeros((3, 3*n))
    shear = np.zeros((2, 3*n))
    # Physical rotations are spatial rx,ry, so the director is
    # (ry,-rx,1) at the flat reference.
    bending[0, 2*n:] = -dx
    bending[1, n:2*n] = dy
    bending[2, n:2*n] = .5*dx
    bending[2, 2*n:] = -.5*dy
    shear[0, :n] = dx
    shear[0, 2*n:] = v
    shear[1, :n] = dy
    shear[1, n:2*n] = -v
    return bending, shear


def beam_basis(nb: int, s: float, *, basis: str = "global"
               ) -> tuple[np.ndarray, np.ndarray]:
    """Rooted independent w/rx/ry fields, global or local cubic."""
    if not 0 <= s <= 1:
        raise ValueError("beam station outside [0,1]")
    if basis == "spline":
        b, db, _ = _spline(nb, 0., 1.)
        return b(s)[1:], db(s)[1:]
    if basis != "global":
        raise ValueError("global or spline trial basis required")
    p = np.array([_polynomial(i)[0](2*s-1) for i in range(nb)])
    dp = np.array([_polynomial(i)[1](2*s-1) for i in range(nb)])
    return s*p, p+2*s*dp


def beam_strain_rows(nb: int, s: float, *, basis: str = "global"
                     ) -> np.ndarray:
    """[twist rate, bending rate, transverse shear]."""
    v, dv = beam_basis(nb, s, basis=basis)
    n = len(v)
    result = np.zeros((3, 3*n))
    result[0, n:2*n] = dv
    result[1, 2*n:] = dv
    result[2, :n] = dv
    result[2, 2*n:] = v
    return result


def _orders(nx: int, ny: int, nb: int, intervals: int) -> None:
    if (any(type(x) is not int or not 2 <= x <= 16
            for x in (nx, ny, nb)) or
            type(intervals) is not int or not 2 <= intervals <= 24):
        raise ValueError("bounded element orders 2-16 and line intervals 2-24 required")


def shell_trace(nx: int, ny: int, s: float, origin: str, *,
                basis: str = "global", director: str = "rail",
                strip_half_length: float = HALF_WINDOW,
                strip_half_width: float = HALF_RAIL) -> np.ndarray:
    """Linearized [z,rx,ry] trace of the declared material point/director."""
    if origin not in ("rail", "local", "strip"):
        raise ValueError("rail, local or strip shell origin required")
    if director not in ("rail", "local", "strip"):
        raise ValueError("rail, local or strip shell director required")
    if (not np.isfinite(strip_half_length) or
            not np.isfinite(strip_half_width) or
            not .05 <= strip_half_length <= .25 or
            not .05 <= strip_half_width <= .25):
        raise ValueError("bounded positive strip half dimensions required")
    n = len(plate_basis(nx, ny, s, 0., basis=basis)[0])
    result = np.zeros((3, 3*n))
    values = [plate_basis(nx, ny, s+ox, y, basis=basis)[0]
              for ox, y in SAMPLES]
    mean = np.mean(values, axis=0)
    if origin == "strip" or director == "strip":
        xknots = (_spline(nx, -.5, 1.5)[2] if basis == "spline" else
                  np.array((-.5, 1.5)))
        yknots = (_spline(ny, -.5, .5)[2] if basis == "spline" else
                  np.array((-.5, .5)))
        x0, x1 = s-strip_half_length, s+strip_half_length
        y0, y1 = -strip_half_width, strip_half_width
        xedges = np.r_[x0, xknots[(x0 < xknots) & (xknots < x1)], x1]
        yedges = np.r_[y0, yknots[(y0 < yknots) & (yknots < y1)], y1]
        strip = np.zeros(n)
        for x, wx in _quadrature(4 if basis == "spline" else 16, xedges):
            for y, wy in _quadrature(4 if basis == "spline" else 16, yedges):
                strip += wx*wy*plate_basis(
                    nx, ny, float(x), float(y), basis=basis)[0]
        strip /= 4*strip_half_length*strip_half_width
    else:
        strip = None
    local = plate_basis(nx, ny, s, 0., basis=basis)[0]
    result[0, :n] = (mean if origin == "rail" else
                     local if origin == "local" else strip)
    director_values = (mean if director == "rail" else
                       local if director == "local" else strip)
    result[1, n:2*n] = director_values
    result[2, 2*n:] = director_values
    return result


def _gauss(order: int, left: float, right: float):
    points, weights = leggauss(order)
    return (.5*(left+right)+.5*(right-left)*points,
            .5*(right-left)*weights)


def assemble(nx: int, ny: int, nb: int, intervals: int, *,
             origin: str = "rail", multiplier: str = "p1",
             basis: str = "global", thickness: float = THICKNESS,
             director: str = "rail",
             strip_half_length: float = HALF_WINDOW,
             strip_half_width: float = HALF_RAIL
             ) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                        np.ndarray, np.ndarray, np.ndarray]:
    """Independent plate/beam energies and exact weak-line KKT blocks."""
    _orders(nx, ny, nb, intervals)
    if (isinstance(thickness, bool) or not np.isfinite(thickness) or
            thickness <= 0.):
        raise ValueError("finite positive shell thickness required")
    if (not np.isfinite(strip_half_length) or
            not np.isfinite(strip_half_width) or
            not .05 <= strip_half_length <= .25 or
            not .05 <= strip_half_width <= .25):
        raise ValueError("bounded positive strip half dimensions required")
    if multiplier not in ("p0", "p1"):
        raise ValueError("P0 or continuous P1 multiplier required")
    # Each scalar line trace is a single polynomial of degree at most
    # max(nx,nb). More test rows than its polynomial dimension are exactly
    # dependent, whatever the shell's transverse polynomial order.
    trace_dimension = max(nx, nb)+1
    multiplier_dimension = intervals if multiplier == "p0" else intervals+1
    if basis == "global" and multiplier_dimension > trace_dimension:
        raise ValueError("line multiplier rows exceed the polynomial trace image")
    ns = 3*len(plate_basis(nx, ny, 0., 0., basis=basis)[0])
    beam_n = len(beam_basis(nb, 0., basis=basis)[0])
    nbeam = 3*beam_n
    ks = np.zeros((ns, ns))
    kb = np.zeros((nbeam, nbeam))
    bending_d = E*thickness**3/(12*(1-NU**2))
    shear_k = (5/6)*G*thickness
    cb = bending_d * np.array(((1., NU, 0.),
                               (NU, 1., 0.),
                               (0., 0., 2*(1-NU))))
    cs = shear_k*np.eye(2)
    xedges = (_spline(nx, -.5, 1.5)[2] if basis == "spline" else
              np.array((-.5, 1.5)))
    yedges = (_spline(ny, -.5, .5)[2] if basis == "spline" else
              np.array((-.5, .5)))
    xorder = 5 if basis == "spline" else max(2*nx+4, 12)
    yorder = 5 if basis == "spline" else max(2*ny+4, 12)
    for x, wx in _quadrature(xorder, xedges):
        for y, wy in _quadrature(yorder, yedges):
            b, g = plate_strain_rows(nx, ny, float(x), float(y), basis=basis)
            ks += wx*wy*(b.T@cb@b + g.T@cs@g)
    sedges = (_spline(nb, 0., 1.)[2] if basis == "spline" else
              np.array((0., 1.)))
    beam_constitutive = np.diag((G*BEAM_J, E*BEAM_I,
                                 G*BEAM_SHEAR_AREA))
    for s, weight in _quadrature(
            5 if basis == "spline" else max(2*nb+4, 12), sedges):
        b = beam_strain_rows(nb, float(s), basis=basis)
        kb += weight*(b.T@beam_constitutive@b)
    nm = intervals if multiplier == "p0" else intervals+1
    c = np.zeros((3*nm, ns+nbeam))
    moments = np.zeros(nm)
    first_moments = np.zeros(nm)
    for cell in range(intervals):
        left, right = cell/intervals, (cell+1)/intervals
        edges = _line_edges(cell, intervals, nx, nb, basis,
                            origin=origin, director=director,
                            strip_half_length=strip_half_length)
        for s, weight in _quadrature(
                6 if basis == "spline" else max(2*max(nx, ny, nb)+4, 12),
                edges):
            s = float(s)
            value, _ = beam_basis(nb, s, basis=basis)
            beam_trace = np.zeros((3, nbeam))
            for channel in range(3):
                beam_trace[channel, channel*beam_n:(channel+1)*beam_n] = value
            trace = np.column_stack((-shell_trace(
                nx, ny, s, origin, basis=basis, director=director,
                strip_half_length=strip_half_length,
                strip_half_width=strip_half_width),
                                     beam_trace))
            local = ((1.,) if multiplier == "p0" else
                     ((right-s)/(right-left), (s-left)/(right-left)))
            for offset, phi in enumerate(local):
                row = cell+offset
                c[3*row:3*row+3] += weight*phi*trace
                moments[row] += weight*phi
                first_moments[row] += weight*phi*s
    if basis == "spline" and np.linalg.matrix_rank(c) < len(c):
        raise ValueError("line multiplier rows exceed the spline trace image")
    return ks, kb, c, moments, first_moments, beam_constitutive


def solve(nx: int, ny: int, nb: int, intervals: int, *,
          origin: str = "rail", multiplier: str = "p1",
          tip_force_z: float = 1000., tip_torque_x: float = 0.,
          basis: str = "global", thickness: float = THICKNESS,
          director: str = "rail",
          strip_half_length: float = HALF_WINDOW,
          strip_half_width: float = HALF_RAIL) -> dict:
    """Solve a bounded flat reference and recover work-conjugate reactions."""
    ks, kb, c, moments, first, _ = assemble(
        nx, ny, nb, intervals, origin=origin, multiplier=multiplier,
        basis=basis, thickness=thickness, director=director,
        strip_half_length=strip_half_length,
        strip_half_width=strip_half_width)
    ns, nbeam = len(ks), len(kb)
    n = nbeam//3
    f = np.zeros(ns+nbeam)
    tip, _ = beam_basis(nb, 1., basis=basis)
    f[ns:ns+n] = tip_force_z*tip
    f[ns+n:ns+2*n] = tip_torque_x*tip
    k = np.zeros((ns+nbeam, ns+nbeam))
    k[:ns, :ns] = ks
    k[ns:, ns:] = kb
    displacement_scale, force_scale = 1e-5, 1000.
    a = k*(displacement_scale/force_scale)
    matrix = np.block([[a, c.T], [c, np.zeros((len(c), len(c)))]])
    rhs = np.r_[f/force_scale, np.zeros(len(c))]
    solution = np.linalg.solve(matrix, rhs)
    residual = matrix@solution-rhs
    q = displacement_scale*solution[:ns+nbeam]
    lam = force_scale*solution[ns+nbeam:].reshape(-1, 3)
    shell_energy = float(.5*q[:ns]@ks@q[:ns])
    beam_energy = float(.5*q[ns:]@kb@q[ns:])
    work = float(f@q)
    gap_points = []
    gap_squared = 0.
    gap_z_squared = 0.
    gap_rotation_squared = 0.
    for cell in range(intervals):
        left, right = cell/intervals, (cell+1)/intervals
        edges = _line_edges(cell, intervals, nx, nb, basis,
                            origin=origin, director=director,
                            strip_half_length=strip_half_length)
        for s, weight in _quadrature(
                8 if basis == "spline" else max(2*max(nx,ny,nb)+6, 16),
                edges):
            s = float(s)
            b, _ = beam_basis(nb, s, basis=basis)
            beam_pose = np.array([b@q[ns+i*n:ns+(i+1)*n]
                                  for i in range(3)])
            gap = beam_pose-shell_trace(
                nx, ny, s, origin, basis=basis,
                director=director,
                strip_half_length=strip_half_length,
                strip_half_width=strip_half_width)@q[:ns]
            gap_squared += weight*float(gap@gap)
            gap_z_squared += weight*float(gap[0]**2)
            gap_rotation_squared += weight*float(gap[1:]@gap[1:])
            gap_points.append(float(np.linalg.norm(gap)))
    shell_fz = float(-moments@lam[:, 0])
    beam_fz = float(moments@lam[:, 0]-tip_force_z)
    shell_mx = float(-moments@lam[:, 1])
    beam_mx = float(moments@lam[:, 1]-tip_torque_x)
    shell_my = float(first@lam[:, 0]-moments@lam[:, 2])
    beam_my = float(-first@lam[:, 0]+moments@lam[:, 2]+tip_force_z)
    tip_pose = np.array([tip@q[ns+i*n:ns+(i+1)*n]
                         for i in range(3)])
    return {
        "model":"independent_flat_RM_plate_Timoshenko_beam",
        "nx":nx, "ny":ny, "nb":nb, "line_intervals":intervals,
        "origin":origin, "director":director,
        "strip_half_length_m":strip_half_length,
        "strip_half_width_m":strip_half_width,
        "multiplier":multiplier, "basis":basis,
        "shell_thickness_m":thickness,
        "tip_force_z_n":tip_force_z, "tip_torque_x_n_m":tip_torque_x,
        "tip_z_m":float(tip_pose[0]), "tip_rx_rad":float(tip_pose[1]),
        "tip_ry_rad":float(tip_pose[2]),
        "shell_energy_j":shell_energy, "beam_energy_j":beam_energy,
        "external_work_j":work,
        "work_error_j":float(2*(shell_energy+beam_energy)-work),
        "scaled_equation_residual":float(np.linalg.norm(residual)),
        "weak_gap_l2":float(np.linalg.norm(c@q)),
        "gap_characteristic_length_m":1.,
        "gap_z_l2_m":float(np.sqrt(gap_z_squared)),
        "gap_rotation_l2_rad":float(np.sqrt(gap_rotation_squared)),
        "gap_combined_l2_m":float(np.sqrt(gap_squared)),
        "quadrature_combined_gap_max_m":float(max(gap_points)),
        "shell_reaction_fz_n":shell_fz, "beam_reaction_fz_n":beam_fz,
        "shell_reaction_mx_n_m":shell_mx, "beam_reaction_mx_n_m":beam_mx,
        "shell_reaction_my_n_m":shell_my, "beam_reaction_my_n_m":beam_my,
        "balance_fz_n":shell_fz+beam_fz+tip_force_z,
        "balance_mx_n_m":shell_mx+beam_mx+tip_torque_x,
        "balance_my_n_m":shell_my+beam_my-tip_force_z,
        "matrix_size":len(matrix),
        "matrix_condition":float(np.linalg.cond(matrix)),
    }
