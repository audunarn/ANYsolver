"""Bounded nodal pad projection and support-work recovery for F03 Qp.

This compares the physical pad area push with a separately assembled beam
line work vector. It is a classical preparatory reference, not a native
beam/shell attachment or a physical-convergence qualification.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scripts._b3_e4_f03_conforming_qp_energy import _shell
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_qp_area_adjoint import FinitePadAreaAdjoint
from scripts._b3_e4_f03_qp_beam_recovery import recover_interface
from scripts._b3_e4_f03_qp_shell_recovery import PiecewiseQpShellRecovery


@dataclass(frozen=True)
class NodalQpRecovery:
    area_nodal_load: np.ndarray
    line_nodal_load: np.ndarray
    shell_nodal_force: np.ndarray
    support_residual: np.ndarray
    free_residual: np.ndarray
    support_wrenches: np.ndarray
    area_wrench: np.ndarray
    line_wrench: np.ndarray
    beam_root_reaction: np.ndarray


def _area_rule(trace: FinitePadQpTrace, x_order: int, y_order: int):
    x_edges = {*trace.x}
    y_edges = {*trace.y}
    for ox, oy in trace.offsets:
        y_edges.update((oy-trace.a, oy+trace.a))
        for station in (*trace.station_breakpoints(), 0., 1.):
            x_edges.update((station+ox-trace.a, station+ox+trace.a))
    x_edges = sorted(value for value in x_edges
                     if trace.x[0] <= value <= trace.x[-1])
    y_edges = sorted(value for value in y_edges
                     if trace.y[0] <= value <= trace.y[-1])
    rx, wx = np.polynomial.legendre.leggauss(x_order)
    ry, wy = np.polynomial.legendre.leggauss(y_order)
    for xl, xr in zip(x_edges, x_edges[1:]):
        if xr <= xl:
            continue
        x_values = (xl+xr)/2+(xr-xl)*rx/2
        for yb, yt in zip(y_edges, y_edges[1:]):
            if yt <= yb or not any(
                    yb >= oy-trace.a and yt <= oy+trace.a
                    for _, oy in trace.offsets):
                continue
            y_values = (yb+yt)/2+(yt-yb)*ry/2
            for x, x_weight in zip(x_values, wx):
                i = int(np.searchsorted(trace.x, x, side="right")-1)
                if i < 0 or i >= len(trace.x)-1:
                    raise ValueError("area x quadrature left shell cell")
                tx = (x-trace.x[i])/(trace.x[i+1]-trace.x[i])
                bx = np.array([basis(tx) for basis, _ in trace._basis])
                for y, y_weight in zip(y_values, wy):
                    k = int(np.searchsorted(trace.y, y, side="right")-1)
                    if k < 0 or k >= len(trace.y)-1:
                        raise ValueError("area y quadrature left shell cell")
                    ty = (y-trace.y[k])/(trace.y[k+1]-trace.y[k])
                    by = np.array([basis(ty) for basis, _ in trace._basis])
                    nodes = np.array([(i*trace.p+a)*trace.ny+k*trace.p+b
                                      for a in range(trace.p+1)
                                      for b in range(trace.p+1)])
                    weight = x_weight*y_weight*(xr-xl)*(yt-yb)/4
                    yield (float(x), float(y), float(weight), nodes,
                           np.outer(bx, by).ravel())


def assemble_area_nodal_load(adjoint: FinitePadAreaAdjoint, *,
                             x_order: int | None = None,
                             y_order: int | None = None):
    """Integrate physical f_mu against all shared Qp nodal shape functions."""
    trace = adjoint.trace
    x_order = trace.p+3 if x_order is None else x_order
    y_order = trace.p+1 if y_order is None else y_order
    if (x_order < trace.p+2 or x_order > 14 or
            y_order < trace.p+1 or y_order > 10):
        raise ValueError("unsupported bounded area quadrature order")
    load = np.zeros(2*trace.n)
    wrench = np.zeros(3)
    def accumulate(chunk):
        points = np.array([(x, y) for x, y, _, _, _ in chunk])
        forces = adjoint.area_forces(points)
        for (x, y, weight, nodes, basis), force in zip(chunk, forces):
            load[nodes] += weight*force[0]*basis
            load[trace.n+nodes] += weight*force[1]*basis
            wrench[:] += weight*np.array((force[0], force[1],
                                          x*force[1]-y*force[0]))
    chunk = []
    count = 0
    for item in _area_rule(trace, x_order, y_order):
        count += 1
        if count > 65536:
            raise ValueError("outside bounded area projection point budget")
        chunk.append(item)
        if len(chunk) == 8192:
            accumulate(chunk)
            chunk.clear()
    if chunk:
        accumulate(chunk)
    return load, wrench


def assemble_line_nodal_load(adjoint: FinitePadAreaAdjoint, *,
                             order: int = 48) -> np.ndarray:
    """Separately integrate recovered line density through the Qp pose map."""
    trace = adjoint.trace
    if order not in (48, 64):
        raise ValueError("fixed 48/64 station comparison order required")
    roots, weights = np.polynomial.legendre.leggauss(order)
    result = np.zeros(2*trace.n)
    for left, right in trace.station_intervals():
        stations = (left+right)/2+(right-left)*roots/2
        density = recover_interface(trace, adjoint.q, adjoint.eta,
                                    stations)["density"]
        for station, weight, force in zip(stations, weights, density):
            pose = trace.matrices(float(station))[0]
            result += (right-left)*weight/2*(force@pose)
    root, tip = adjoint.atoms
    result += root@trace.matrices(0., side="right")[0]
    result += tip@trace.matrices(1., side="left")[0]
    return result


def support_liftings(trace: FinitePadQpTrace) -> np.ndarray:
    """Six physical unit edge translations/rotations about the origin."""
    lifts = np.zeros((6, 2*trace.n))
    for edge_index, column in enumerate((0, trace.nx-1)):
        nodes = np.arange(column*trace.ny, (column+1)*trace.ny)
        y = np.asarray(trace.nodes_y)
        x = trace.nodes_x[column]
        lifts[3*edge_index, nodes] = 1.
        lifts[3*edge_index+1, trace.n+nodes] = 1.
        lifts[3*edge_index+2, nodes] = -y
        lifts[3*edge_index+2, trace.n+nodes] = x
    return lifts


def distributed_support_liftings(trace: FinitePadQpTrace) -> np.ndarray:
    """Six blended edge liftings with the same physical support traces."""
    xx, yy = np.meshgrid(trace.nodes_x, trace.nodes_y, indexing="ij")
    left = (trace.x[-1]-xx)/(trace.x[-1]-trace.x[0])
    right = (xx-trace.x[0])/(trace.x[-1]-trace.x[0])
    lifts = np.zeros((6, 2*trace.n))
    for edge, chi in enumerate((left, right)):
        lifts[3*edge, :trace.n] = chi.ravel()
        lifts[3*edge+1, trace.n:] = chi.ravel()
        lifts[3*edge+2, :trace.n] = (-chi*yy).ravel()
        lifts[3*edge+2, trace.n:] = (chi*xx).ravel()
    return lifts


def recover_nodal(adjoint: FinitePadAreaAdjoint) -> NodalQpRecovery:
    """Recover nodal balance and six physical supported-edge works."""
    trace = adjoint.trace
    area_load, area_wrench = assemble_area_nodal_load(adjoint)
    line_load = assemble_line_nodal_load(adjoint)
    full_shell = _shell(trace, np.arange(2*trace.n))
    shell_force = full_shell@adjoint.q
    residual = shell_force-area_load
    support = np.setdiff1d(np.arange(2*trace.n), trace.free_columns)
    lifts = support_liftings(trace)
    root_reaction = recover_interface(trace, adjoint.q, adjoint.eta,
                                      np.empty(0))["root_reaction"]
    return NodalQpRecovery(
        area_load, line_load, shell_force,
        residual[support], residual[trace.free_columns],
        lifts@residual, area_wrench, adjoint.line_wrench(), root_reaction)
