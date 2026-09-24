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


def plate_basis(nx: int, ny: int, x: float, y: float
                ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Supported tensor trial X*Pi(2X-1)*Pj(2y), X=(x+.5)/2."""
    if not (-.5 <= x <= 1.5 and -.5 <= y <= .5):
        raise ValueError("plate station outside declared geometry")
    X = (x + .5) / 2
    px = np.array([_polynomial(i)[0](2*X-1) for i in range(nx)])
    dpx = np.array([_polynomial(i)[1](2*X-1) for i in range(nx)])
    py = np.array([_polynomial(j)[0](2*y) for j in range(ny)])
    dpy = np.array([_polynomial(j)[1](2*y) for j in range(ny)])
    value = np.outer(X*px, py).ravel()
    dx = np.outer(.5*px + X*dpx, py).ravel()
    dy = np.outer(2*X*px, dpy).ravel()
    return value, dx, dy


def plate_strain_rows(nx: int, ny: int, x: float, y: float
                      ) -> tuple[np.ndarray, np.ndarray]:
    """Curvatures [kx,ky,kxy] and engineering shears [gxz,gyz]."""
    v, dx, dy = plate_basis(nx, ny, x, y)
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


def beam_basis(nb: int, s: float) -> tuple[np.ndarray, np.ndarray]:
    """Rooted independent w/rx/ry fields s*Pi(2s-1)."""
    if not 0 <= s <= 1:
        raise ValueError("beam station outside [0,1]")
    p = np.array([_polynomial(i)[0](2*s-1) for i in range(nb)])
    dp = np.array([_polynomial(i)[1](2*s-1) for i in range(nb)])
    return s*p, p+2*s*dp


def beam_strain_rows(nb: int, s: float) -> np.ndarray:
    """[twist rate, bending rate, transverse shear]."""
    v, dv = beam_basis(nb, s)
    result = np.zeros((3, 3*nb))
    result[0, nb:2*nb] = dv
    result[1, 2*nb:] = dv
    result[2, :nb] = dv
    result[2, 2*nb:] = v
    return result


def _orders(nx: int, ny: int, nb: int, intervals: int) -> None:
    if any(type(x) is not int or not 2 <= x <= 12
           for x in (nx, ny, nb, intervals)):
        raise ValueError("bounded integer orders/intervals 2 through 12 required")


def shell_trace(nx: int, ny: int, s: float, origin: str) -> np.ndarray:
    """Linearized [z,rx,ry] trace of the declared material rail or center."""
    if origin not in ("rail", "local"):
        raise ValueError("rail or local shell origin required")
    n = nx*ny
    result = np.zeros((3, 3*n))
    values = [plate_basis(nx, ny, s+ox, y)[0] for ox, y in SAMPLES]
    mean = np.mean(values, axis=0)
    result[0, :n] = (mean if origin == "rail" else
                     plate_basis(nx, ny, s, 0.)[0])
    result[1, n:2*n] = mean
    result[2, 2*n:] = mean
    return result


def _gauss(order: int, left: float, right: float):
    points, weights = leggauss(order)
    return (.5*(left+right)+.5*(right-left)*points,
            .5*(right-left)*weights)


def assemble(nx: int, ny: int, nb: int, intervals: int, *,
             origin: str = "rail", multiplier: str = "p1"
             ) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                        np.ndarray, np.ndarray, np.ndarray]:
    """Independent plate/beam energies and exact weak-line KKT blocks."""
    _orders(nx, ny, nb, intervals)
    if multiplier not in ("p0", "p1"):
        raise ValueError("P0 or continuous P1 multiplier required")
    # Each scalar line trace is a single polynomial of degree at most
    # max(nx,nb). More test rows than its polynomial dimension are exactly
    # dependent, whatever the shell's transverse polynomial order.
    trace_dimension = max(nx, nb)+1
    multiplier_dimension = intervals if multiplier == "p0" else intervals+1
    if multiplier_dimension > trace_dimension:
        raise ValueError("line multiplier rows exceed the polynomial trace image")
    ns, nbeam = 3*nx*ny, 3*nb
    ks = np.zeros((ns, ns))
    kb = np.zeros((nbeam, nbeam))
    cb = BENDING_D * np.array(((1., NU, 0.),
                               (NU, 1., 0.),
                               (0., 0., 2*(1-NU))))
    cs = SHEAR_K*np.eye(2)
    xq, xw = _gauss(max(2*nx+4, 12), -.5, 1.5)
    yq, yw = _gauss(max(2*ny+4, 12), -.5, .5)
    for x, wx in zip(xq, xw):
        for y, wy in zip(yq, yw):
            b, g = plate_strain_rows(nx, ny, float(x), float(y))
            ks += wx*wy*(b.T@cb@b + g.T@cs@g)
    sq, sw = _gauss(max(2*nb+4, 12), 0., 1.)
    beam_constitutive = np.diag((G*BEAM_J, E*BEAM_I,
                                 G*BEAM_SHEAR_AREA))
    for s, weight in zip(sq, sw):
        b = beam_strain_rows(nb, float(s))
        kb += weight*(b.T@beam_constitutive@b)
    nm = intervals if multiplier == "p0" else intervals+1
    c = np.zeros((3*nm, ns+nbeam))
    moments = np.zeros(nm)
    first_moments = np.zeros(nm)
    for cell in range(intervals):
        left, right = cell/intervals, (cell+1)/intervals
        points, weights = _gauss(max(2*max(nx, ny, nb)+4, 12), left, right)
        for s, weight in zip(points, weights):
            s = float(s)
            value, _ = beam_basis(nb, s)
            beam_trace = np.zeros((3, nbeam))
            for channel in range(3):
                beam_trace[channel, channel*nb:(channel+1)*nb] = value
            trace = np.column_stack((-shell_trace(nx, ny, s, origin),
                                     beam_trace))
            local = ((1.,) if multiplier == "p0" else
                     ((right-s)/(right-left), (s-left)/(right-left)))
            for offset, phi in enumerate(local):
                row = cell+offset
                c[3*row:3*row+3] += weight*phi*trace
                moments[row] += weight*phi
                first_moments[row] += weight*phi*s
    return ks, kb, c, moments, first_moments, beam_constitutive


def solve(nx: int, ny: int, nb: int, intervals: int, *,
          origin: str = "rail", multiplier: str = "p1",
          tip_force_z: float = 1000., tip_torque_x: float = 0.) -> dict:
    """Solve a bounded flat reference and recover work-conjugate reactions."""
    ks, kb, c, moments, first, _ = assemble(
        nx, ny, nb, intervals, origin=origin, multiplier=multiplier)
    ns, nbeam = len(ks), len(kb)
    n = nb
    f = np.zeros(ns+nbeam)
    tip, _ = beam_basis(nb, 1.)
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
        points, weights = _gauss(max(2*max(nx,ny,nb)+6, 16), left, right)
        for s, weight in zip(points, weights):
            s = float(s)
            b, _ = beam_basis(nb, s)
            beam_pose = np.array([b@q[ns+i*nb:ns+(i+1)*nb]
                                  for i in range(3)])
            gap = beam_pose-shell_trace(nx, ny, s, origin)@q[:ns]
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
    tip_pose = np.array([tip@q[ns+i*nb:ns+(i+1)*nb]
                         for i in range(3)])
    return {
        "model":"independent_flat_RM_plate_Timoshenko_beam",
        "nx":nx, "ny":ny, "nb":nb, "line_intervals":intervals,
        "origin":origin, "multiplier":multiplier,
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
