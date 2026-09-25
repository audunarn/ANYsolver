"""Bounded independent membrane/beam yaw reference for the F03 line study.

This small-strain Ritz model uses no native shell, beam, or attachment
operator. It matches the flat panel geometry, full left-edge support,
generalized B3 section, center material-line pose and exact weak-line law.
It is an exploratory physical comparator, not external-solver qualification.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_p0_dual_norm import p0_dual_gram
from scripts._b3_e4_f03_p1_dual_norm import p1_dual_gram
from scripts._b3_e4_f03_dual_linear_norm import dual_linear_gram
from scripts.b3_e4_f03_independent_transverse_reference import (
    E, G, NU, THICKNESS, _quadrature, _spline, beam_basis, plate_basis,
)

AREA = .01
SHEAR_AREA = .008
I = 8.333333333333333e-6


def local_yaw_trace_boundary_layer(half_width: float, *,
                                   amplitude: float = 1e-4,
                                   thickness: float = THICKNESS) -> dict:
    """C1 membrane witness with fixed centerline yaw and vanishing energy.

    On the physical panel, ux=A(x+.5)d*phi(y/d), uy=0, with
    phi(t)=t(1-t²)² for |t|<=1 and zero outside. It obeys full left-edge
    translation support. At s=.5 the local polar yaw is -A/2 for every d,
    while physical membrane energy tends to zero as O(d). This tests the
    continuity of a *zero-width normal-gradient* yaw trace, not a finite
    strip/footprint law or a discrete mesh's numerical completion.
    """
    d = float(half_width)
    a = float(amplitude)
    if (not np.isfinite(d) or not 0. < d <= .5 or not np.isfinite(a)
            or a == 0. or not np.isfinite(thickness) or thickness <= 0.):
        raise ValueError("finite positive width/thickness and nonzero amplitude required")
    points, weights = np.polynomial.legendre.leggauss(12)
    phi = points*(1-points**2)**2
    dphi = 1-6*points**2+5*points**4
    # C11=Et/(1-nu²), C66=Gt, integral_x 1=2, integral_x (x+.5)²=8/3.
    extensional = .5*E*thickness/(1-NU**2)*a*a*d**3*2*float(
        weights@(phi*phi))
    shear = .5*G*thickness*a*a*d*(8/3)*float(
        weights@(dphi*dphi))
    return {"half_width_m": d, "centerline_yaw_rad": -.5*a,
            "physical_membrane_energy_j": extensional+shear,
            "extensional_energy_j": extensional,
            "shear_energy_j": shear}


def _validate(nx: int, ny: int, nb: int, intervals: int, kind: str) -> None:
    if (any(type(v) is not int or not 2 <= v <= 16 for v in (nx, ny, nb))
            or type(intervals) is not int or not 1 <= intervals <= 12
            or kind not in ("p0", "p1", "dual")):
        raise ValueError("bounded spline counts 2-16, intervals 1-12, P0/P1/dual")


def plate_membrane_rows(nx: int, ny: int, x: float, y: float) -> np.ndarray:
    """Return [ux,x, uy,y, ux,y+uy,x] from rooted x/full y splines."""
    value, dx, dy = plate_basis(nx, ny, x, y, basis="spline")
    n = len(value)
    rows = np.zeros((3, 2*n))
    rows[0, :n] = dx
    rows[1, n:] = dy
    rows[2, :n] = dy
    rows[2, n:] = dx
    return rows


def beam_inplane_rows(nb: int, s: float) -> np.ndarray:
    """Return [ux', uy'-rz, rz'] in the generalized-section work order."""
    value, derivative = beam_basis(nb, s, basis="spline")
    n = len(value)
    rows = np.zeros((3, 3*n))
    rows[0, :n] = derivative
    rows[1, n:2*n] = derivative
    rows[1, 2*n:] = -value
    rows[2, 2*n:] = derivative
    return rows


def shell_local_trace(nx: int, ny: int, s: float) -> np.ndarray:
    """Return [ux,uy,half(uy,x-ux,y)] at the material centerline."""
    value, dx, dy = plate_basis(nx, ny, s, 0., basis="spline")
    n = len(value)
    rows = np.zeros((3, 2*n))
    rows[0, :n] = value
    rows[1, n:] = value
    rows[2, :n] = -.5*dy
    rows[2, n:] = .5*dx
    return rows


def shell_strip_trace(nx: int, ny: int, s: float, *,
                      half_length: float = .2,
                      half_width: float = .23) -> np.ndarray:
    """Independent physical area mean of [ux,uy,polar yaw] on one strip."""
    if (not 0. <= s <= 1. or not .05 <= half_length <= .25 or
            not .05 <= half_width <= .25):
        raise ValueError("bounded finite material strip required")
    x0, x1 = s-half_length, s+half_length
    y0, y1 = -half_width, half_width
    xknots = _spline(nx, -.5, 1.5)[2]
    yknots = _spline(ny, -.5, .5)[2]
    xedges = np.r_[x0, xknots[(x0 < xknots) & (xknots < x1)], x1]
    yedges = np.r_[y0, yknots[(y0 < yknots) & (yknots < y1)], y1]
    n = len(plate_basis(nx, ny, s, 0., basis="spline")[0])
    mean = np.zeros(n)
    gx = np.zeros(n)
    gy = np.zeros(n)
    for x, wx in _quadrature(4, xedges):
        for y, wy in _quadrature(4, yedges):
            value, dx, dy = plate_basis(
                nx, ny, float(x), float(y), basis="spline")
            mean += wx*wy*value
            gx += wx*wy*dx
            gy += wx*wy*dy
    area = 4*half_length*half_width
    rows = np.zeros((3, 2*n))
    rows[0, :n] = mean/area
    rows[1, n:] = mean/area
    rows[2, :n] = -.5*gy/area
    rows[2, n:] = .5*gx/area
    return rows


def shell_chord_trace(nx: int, ny: int, s: float, *,
                      half_chord: float = .2) -> np.ndarray:
    """Independent centerline displacement and fixed-chord heading."""
    if not 0. <= s <= 1. or not .05 <= half_chord <= .25:
        raise ValueError("bounded fixed shell-line chord required")
    center = plate_basis(nx, ny, s, 0., basis="spline")[0]
    plus = plate_basis(nx, ny, s+half_chord, 0., basis="spline")[0]
    minus = plate_basis(nx, ny, s-half_chord, 0., basis="spline")[0]
    n = len(center)
    rows = np.zeros((3, 2*n))
    rows[0, :n] = center
    rows[1, n:] = center
    rows[2, n:] = (plus-minus)/(2*half_chord)
    return rows


def _line_edges(nx: int, nb: int, intervals: int, *,
                trace_kind: str = "local") -> np.ndarray:
    """Split weak integrals at every spline or multiplier breakpoint."""
    xknots = _spline(nx, -.5, 1.5)[2]
    moving = (np.r_[xknots-.2, xknots+.2]
              if trace_kind in ("strip_020_023", "chord_020")
              else np.array(()))
    return np.unique(np.r_[np.linspace(0., 1., intervals+1), xknots, moving,
                           _spline(nb, 0., 1.)[2]].clip(0., 1.))


def assemble(nx: int, ny: int, nb: int, intervals: int, *,
             kind: str = "p0", thickness: float = THICKNESS,
             trace_kind: str = "local"
             ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Independently assemble physical plate, beam and line constraint."""
    _validate(nx, ny, nb, intervals, kind)
    if trace_kind not in ("local", "strip_020_023", "chord_020"):
        raise ValueError("local, strip or declared line-chord trace required")
    if (isinstance(thickness, bool) or not np.isfinite(thickness)
            or thickness <= 0.):
        raise ValueError("finite positive thickness required")
    ns = 2*len(plate_basis(nx, ny, 0., 0., basis="spline")[0])
    beam_n = len(beam_basis(nb, 0., basis="spline")[0])
    nbeam = 3*beam_n
    shell = np.zeros((ns, ns))
    beam = np.zeros((nbeam, nbeam))
    membrane = E*thickness/(1-NU**2)*np.array(
        ((1., NU, 0.), (NU, 1., 0.), (0., 0., .5*(1-NU))))
    for x, wx in _quadrature(5, _spline(nx, -.5, 1.5)[2]):
        for y, wy in _quadrature(5, _spline(ny, -.5, .5)[2]):
            strain = plate_membrane_rows(nx, ny, float(x), float(y))
            shell += wx*wy*(strain.T@membrane@strain)
    section = np.diag((E*AREA, G*SHEAR_AREA, E*I))
    for s, weight in _quadrature(5, _spline(nb, 0., 1.)[2]):
        strain = beam_inplane_rows(nb, float(s))
        beam += weight*(strain.T@section@strain)
    nrows = intervals if kind == "p0" else intervals+1
    constraints = np.zeros((3*nrows, ns+nbeam))
    moments = np.zeros((nrows, 2))
    edges = _line_edges(nx, nb, intervals, trace_kind=trace_kind)
    for left, right in zip(edges[:-1], edges[1:]):
        if right-left < 1e-13:
            continue
        cell = min(int(np.floor((left+right)*.5*intervals)), intervals-1)
        c_left, c_right = cell/intervals, (cell+1)/intervals
        for s, weight in _quadrature(5, np.array((left, right))):
            shell_trace = {
                "local": shell_local_trace,
                "strip_020_023": shell_strip_trace,
                "chord_020": shell_chord_trace,
            }[trace_kind](nx, ny, float(s))
            value, _ = beam_basis(nb, float(s), basis="spline")
            beam_trace = np.zeros((3, nbeam))
            for axis in range(3):
                beam_trace[axis, axis*beam_n:(axis+1)*beam_n] = value
            trace = np.column_stack((-shell_trace, beam_trace))
            fraction = (s-c_left)/(c_right-c_left)
            shape = ((1.,) if kind == "p0" else
                     (2.-3*fraction, 3*fraction-1.) if kind == "dual" else
                     (1.-fraction, fraction))
            for offset, phi in enumerate(shape):
                row = cell+offset
                constraints[3*row:3*row+3] += weight*phi*trace
                moments[row] += weight*phi*np.array((1., s))
    return shell, beam, constraints, moments


def interface_stability(nx: int, ny: int, nb: int, intervals: int, *,
                        kind: str = "p0", thickness: float = THICKNESS,
                        characteristic_length: float = 1.,
                        trace_kind: str = "local") -> dict:
    """Energy/L2-scaled physical three-channel inf-sup diagnostic.

    The shell and beam matrices here are positive physical energies. The
    multiplier L2 Gram uses the exact P0/P1/dual line mass. Rotational gaps are
    converted to lengths with the fixed characteristic length. This does
    not include native retained variables, Q4/S3 numerical completion, or
    the other three six-channel constraints and cannot select a space.
    """
    shell, beam, c, _ = assemble(nx, ny, nb, intervals,
                                 kind=kind, thickness=thickness,
                                 trace_kind=trace_kind)
    if (not np.isfinite(characteristic_length) or
            characteristic_length <= 0.):
        raise ValueError("positive characteristic length required")
    k = linalg.block_diag(shell, beam)
    linalg.cholesky(k, lower=True)
    nrows = intervals if kind == "p0" else intervals+1
    mass = np.zeros((nrows, nrows))
    for cell in range(intervals):
        h = 1./intervals
        if kind == "p0":
            mass[cell, cell] += h
        elif kind == "p1":
            mass[cell:cell+2, cell:cell+2] += h/6*np.array(((2., 1.), (1., 2.)))
        else:
            mass[cell:cell+2, cell:cell+2] += h*np.array(((1., -.5), (-.5, 1.)))
    gap_scale = np.tile((1., 1., characteristic_length), nrows)
    scaled_c = gap_scale[:, None]*c
    schur = scaled_c@linalg.solve(k, scaled_c.T, assume_a="pos")
    gram = np.kron(mass, np.eye(3))
    eig, modes = linalg.eigh(schur, gram)
    scaled = eig*(E*thickness/characteristic_length)
    lowest = modes[:, 0].reshape(-1, 3)
    channel_beta = []
    for axis in range(3):
        rows = np.arange(axis, len(c), 3)
        channel_eigen = linalg.eigh(
            schur[np.ix_(rows, rows)], mass, eigvals_only=True)
        channel_beta.append(float(np.sqrt(max(
            channel_eigen[0]*E*thickness/characteristic_length, 0.))))
    # Separately report the finite-dimensional H^-1/2 diagnostic used by
    # historical F03 work. Unlike the L2 quotient, this dual norm accounts
    # for multiplier wavelength. Its bounded spectral tail is retained.
    dual_lower, dual_upper = {"p0": p0_dual_gram,
                              "p1": p1_dual_gram,
                              "dual": dual_linear_gram}[kind](
                                  intervals, 1., 4095)
    h_gram_lower = np.kron(dual_lower, np.eye(3))
    h_gram_upper = np.kron(dual_upper, np.eye(3))
    h_min_lower = float(linalg.eigh(
        E*thickness*schur, h_gram_upper,
        eigvals_only=True)[0])
    h_min_upper = float(linalg.eigh(
        E*thickness*schur, h_gram_lower,
        eigvals_only=True)[0])
    h_channel_lower = []
    for axis in range(3):
        rows = np.arange(axis, len(c), 3)
        h_channel_lower.append(float(linalg.eigh(
            E*thickness*schur[np.ix_(rows, rows)], dual_upper,
            eigvals_only=True)[0]))
    return {
        "physical_subsystem": "membrane_ux_uy_and_beam_ux_uy_rz",
        "kind": kind, "trace_kind": trace_kind,
        "intervals": intervals, "rows": len(c),
        "rank": int(np.linalg.matrix_rank(c)),
        "characteristic_length_m": characteristic_length,
        "normalized_eigen_min": float(scaled[0]),
        "normalized_eigen_max": float(scaled[-1]),
        "normalized_beta_min": float(np.sqrt(max(scaled[0], 0.))),
        "lowest_mode_channel_l2": [
            float(np.sqrt(lowest[:, axis]@mass@lowest[:, axis]))
            for axis in range(3)],
        "single_channel_beta_min_ux_uy_yaw": channel_beta,
        "h_minus_half_eigen_min_bracket": [h_min_lower, h_min_upper],
        "h_minus_half_channel_eigen_min_lower_ux_uy_yaw": h_channel_lower,
        "h_minus_half_tail_relative": float(np.linalg.norm(
            dual_upper-dual_lower)/np.linalg.norm(dual_lower)),
        "interpretation": "physical three-channel diagnostics, not native six-channel qualification",
    }


def solve(nx: int, ny: int, nb: int, intervals: int, *,
          kind: str = "p0", tip_mz: float = 100.,
          thickness: float = THICKNESS,
          trace_kind: str = "local") -> dict:
    """Solve and recover independent physical yaw work and support moment."""
    shell, beam, c, moments = assemble(
        nx, ny, nb, intervals, kind=kind, thickness=thickness,
        trace_kind=trace_kind)
    ns, nbeam = len(shell), len(beam)
    n = nbeam//3
    if np.linalg.matrix_rank(c) != len(c):
        raise ValueError("line multiplier rows exceed trace image")
    k = np.zeros((ns+nbeam, ns+nbeam))
    k[:ns, :ns] = shell
    k[ns:, ns:] = beam
    load = np.zeros(ns+nbeam)
    tip, _ = beam_basis(nb, 1., basis="spline")
    load[ns+2*n:] = tip_mz*tip
    displacement_scale, force_scale = 1e-5, 1000.
    matrix = np.block([[k*(displacement_scale/force_scale), c.T],
                       [c, np.zeros((len(c), len(c)))]])
    rhs = np.r_[load/force_scale, np.zeros(len(c))]
    solution = np.linalg.solve(matrix, rhs)
    q = displacement_scale*solution[:ns+nbeam]
    multipliers = force_scale*solution[ns+nbeam:].reshape(-1, 3)
    tip_yaw = float(tip@q[ns+2*n:])
    shell_energy = float(.5*q[:ns]@shell@q[:ns])
    beam_energy = float(.5*q[ns:]@beam@q[ns:])
    transferred_mz = float(moments[:, 0]@multipliers[:, 2]
                           + moments[:, 1]@multipliers[:, 1])
    shell_support_mz = -transferred_mz
    beam_root_mz = transferred_mz-tip_mz
    return {
        "model": {
            "local": "independent_membrane_Timoshenko_centerline_yaw",
            "strip_020_023": "independent_membrane_Timoshenko_finite_strip_yaw",
            "chord_020": "independent_membrane_Timoshenko_line_chord_yaw",
        }[trace_kind],
        "nx": nx, "ny": ny, "nb": nb, "intervals": intervals,
        "kind": kind, "trace_kind": trace_kind,
        "support": "full_left_edge_shell_and_beam_root",
        "load": "beam_tip_yaw_couple", "tip_mz_n_m": tip_mz,
        "tip_rz_rad": tip_yaw,
        "shell_energy_j": shell_energy, "beam_energy_j": beam_energy,
        "external_work_j": float(load@q),
        "work_error_j": float(2*(shell_energy+beam_energy)-load@q),
        "shell_support_mz_n_m": shell_support_mz,
        "beam_root_mz_n_m": beam_root_mz,
        "global_moment_balance_n_m": shell_support_mz+beam_root_mz+tip_mz,
        "scaled_equilibrium_residual": float(np.linalg.norm(matrix@solution-rhs)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nx", type=int, default=8)
    parser.add_argument("--ny", type=int, default=4)
    parser.add_argument("--nb", type=int, default=8)
    parser.add_argument("--intervals", type=int, default=2)
    parser.add_argument("--kind", choices=("p0", "p1", "dual"), default="p0")
    parser.add_argument("--trace-kind", choices=("local", "strip_020_023",
                                                 "chord_020"),
                        default="local")
    args = parser.parse_args()
    print(json.dumps(solve(args.nx, args.ny, args.nb, args.intervals,
                           kind=args.kind, trace_kind=args.trace_kind),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
