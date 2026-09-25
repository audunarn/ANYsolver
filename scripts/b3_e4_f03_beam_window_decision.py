"""Bounded native Fz trace-window decision at one fixed physical resolution.

Only the *linearized* beam translation row is changed. This is a diagnostic
of a proposed distributing connection, not a nonlinear six-channel law.
"""

from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import scipy
from scipy import linalg
from threadpoolctl import threadpool_info, threadpool_limits

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_p0_dual_norm import p0_dual_gram
from scripts._b3_e4_f03_shell_finite_pose_candidate import reference_nodes
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_channel_basis_reference_kkt, segments,
)
from scripts.b3_e4_f03_dual_fz_mode_decision import norm_gram


def point_shape(station: float, cells: int) -> np.ndarray:
    """Native straight-axis nodal translation trace on a half-cell."""
    cell = min(int(station * cells), cells - 1)
    fraction = station * cells - cell
    shape = np.zeros(cells + 1)
    shape[cell:cell + 2] = (1 - fraction, fraction)
    return shape


def window_shape(station: float, cells: int, half_length: float) -> np.ndarray:
    """Exact mean of the native P1 translation trace over symmetric support.

    Support tapers to a point at each beam end. This preserves the straight
    stress-free reference station and avoids an undeclared outboard beam.
    """
    radius = min(half_length, station, 1 - station)
    if radius <= 1e-14:
        return point_shape(station, cells)
    left, right = station - radius, station + radius
    shape = np.zeros(cells + 1)
    for cell in range(cells):
        a = max(left, cell / cells)
        b = min(right, (cell + 1) / cells)
        if b <= a:
            continue
        mean_fraction = cells * (a + b) / 2 - cell
        shape[cell] += (b - a) * (1 - mean_fraction)
        shape[cell + 1] += (b - a) * mean_fraction
    return shape / (right - left)


def window_constraint(kkt, shell, beam, fz_space, half_length):
    """Replace only the native beam Fz block in the exact reference rows."""
    shell_size = 6 * shell.panel.node_count
    changed = kkt.constraint_jacobian.copy()
    fz_first = 2 * fz_space.count
    edges = segments(shell, beam, fz_space,
                     shell_port="physical_strip_005_005")
    beam_edges = np.arange(beam.n_half_cells + 1) / beam.n_half_cells
    extra = [half_length, 1 - half_length]
    for boundary in beam_edges:
        extra.extend((boundary - half_length, boundary + half_length))
    edges = np.unique(np.round(np.r_[edges,
                                     [x for x in extra if 0 < x < 1]], 14))
    points, weights = np.polynomial.legendre.leggauss(4)
    for left, right in zip(edges[:-1], edges[1:]):
        for point, weight in zip(points, weights):
            station = (left + right) / 2 + (right - left) * point / 2
            delta = (window_shape(station, beam.n_half_cells, half_length) -
                     point_shape(station, beam.n_half_cells))
            measure = (right - left) * weight / 2
            for row, basis in enumerate(fz_space.values(station)):
                changed[fz_first + row, shell_size + 2:
                        shell_size + beam.context.nodal_count:6] += (
                            measure * basis * delta)
    return changed


def mode(kkt, shell, beam, spaces, constraint):
    free = kkt.free_primal
    n = len(free)
    if n + len(constraint) > 1200:
        raise ValueError("bounded dense diagnostic limit exceeded")
    physical = int(np.count_nonzero(
        free < 6 * shell.panel.node_count + beam.context.nodal_count))
    scale = kkt.coordinate_scale[:n]
    stiffness = kkt.primal_tangent[np.ix_(free, free)]
    scaled = (scale[:, None] * stiffness) * scale[None, :] / kkt.energy_scale
    kp, kpr = scaled[:physical, :physical], scaled[:physical, physical:]
    krp, kr = scaled[physical:, :physical], scaled[physical:, physical:]
    retained = linalg.solve(kr, krp, assume_a="sym")
    ep, up = linalg.eigh(kp - kpr @ retained)
    er, ur = linalg.eigh(kr)
    if ep[0] <= 1e-10 * ep[-1] or min(abs(er)) <= 1e-12 * max(abs(er)):
        raise ArithmeticError("physical/retained energy split failed")
    channels = [axis for axis, space in enumerate(spaces)
                for _ in range(space.count)]
    displacement_scale = 1e6 / (210e9 * .07)
    row_scale = np.array([1. if axis < 3 else .46 for axis in channels]) / displacement_scale
    cbar = (row_scale[:, None] * constraint[:, free]) * scale[None, :]
    cp, cr = cbar[:, :physical], cbar[:, physical:]
    bp = (cp - cr @ retained) @ (up / np.sqrt(ep)[None, :])
    br = cr @ (ur / np.sqrt(np.abs(er))[None, :])
    action = bp @ bp.T + br @ br.T
    selected = [i for i, axis in enumerate(channels) if axis in (2, 3, 4)]
    action = action[np.ix_(selected, selected)]
    action = (action + action.T) / 2
    result = {"row_rank": int(np.linalg.matrix_rank(constraint[:, free])),
              "row_count": len(constraint)}
    for name, power in (("HminusHalf", -.5), ("HminusOne", -1.)):
        gr = [norm_gram(space.kind, len(space.knots) - 1, power)
              for space in (spaces[2], spaces[3], spaces[4])]
        lower = linalg.block_diag(*(g[0] for g in gr))
        upper = linalg.block_diag(*(g[1] for g in gr))
        eigen, vectors = linalg.eigh(action, upper)
        weak = vectors[:, 0]
        fz = weak[:spaces[2].count]
        signs = np.sign(fz[np.abs(fz) > 1e-8 * max(abs(fz))])
        result[name] = {
            "beta_lower": float(np.sqrt(max(0., eigen[0]))),
            "beta_upper": float(np.sqrt(max(0., linalg.eigh(action, lower, eigvals_only=True)[0]))),
            "fz_sign_changes": int(np.count_nonzero(signs[1:] != signs[:-1])),
            "fz_coefficients": fz.tolist(),
        }
    return result


def loaded(kkt, shell, beam, constraint, load_axis):
    shell_size = 6 * shell.panel.node_count
    free = kkt.free_primal
    n = len(free)
    rows = constraint[:, free]
    system = np.block(((kkt.primal_tangent[np.ix_(free, free)], rows.T),
                       (rows, np.zeros((len(rows), len(rows))))))
    scale = kkt.coordinate_scale
    scaled = (scale[:, None] * system) * scale[None, :] / kkt.energy_scale
    load = np.zeros(shell_size + beam.context.count)
    load[shell_size + 6 * beam.n_half_cells + load_axis] = (
        100. if load_axis == 3 else 1000.)
    rhs = np.r_[load[free] * scale[:n] / kkt.energy_scale,
                np.zeros(len(rows))]
    solution = linalg.solve(scaled, rhs, assume_a="gen")
    full = np.zeros_like(load)
    full[free] = (scale * solution)[:n]
    multipliers = (scale * solution)[n:]
    residual = kkt.primal_tangent @ full + constraint.T @ multipliers - load
    shell_fixed = np.ones(shell_size, dtype=bool)
    shell_fixed[free[free < shell_size]] = False
    shell_reaction = residual[:shell_size].copy()
    shell_reaction[~shell_fixed] = 0.
    shell_reaction = shell_reaction.reshape(-1, 6)
    shell_nodes = reference_nodes(shell.panel)
    shell_mx = float(np.sum(shell_reaction[:, 3] +
                            shell_nodes[:, 1] * shell_reaction[:, 2] -
                            shell_nodes[:, 2] * shell_reaction[:, 1]))
    work_error = float(full @ (kkt.primal_tangent @ full) - load @ full)
    return {
        "tip_rx_rad": float(full[shell_size + 6 * beam.n_half_cells + 3]),
        "tip_uz_m": float(full[shell_size + 6 * beam.n_half_cells + 2]),
        "shell_support_mx_nm": shell_mx,
        "shell_support_fz_n": float(np.sum(shell_reaction[:, 2])),
        "beam_root_fz_n": float(residual[shell_size + 2]),
        "scaled_equilibrium_residual": float(np.linalg.norm(residual[free]) /
                                             max(np.linalg.norm(load[free]), 1.)),
        "weak_gap_norm": float(np.linalg.norm(constraint @ full)),
        "work_error_j": work_error,
    }


def run(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=False)
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RuntimeError("run requires clean source")
    p0 = LineMultiplierSpace("piecewise_constant", (0., .25, .5, .75, 1.))
    mx = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 9)))
    spaces = (p0, p0, p0, mx, p0, p0)
    manifest = {
        "question": "Does symmetric finite beam Fz support reduce the alternating weak mode without distorting fixed-mesh torque/shear transfer?",
        "alternatives": ["beam point trace", "beam symmetric 0.05 m half-window, tapered at both ends"],
        "decision": "Advance only if mode and physical transfer both improve; otherwise stop this connection-law candidate.",
        "source_sha": source, "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__, "threads": 1,
        "mesh": "Q4/S3 x8/y4, native beam-half16, shell square strip .05/.05 m",
        "loads": "separate +100 N m tip Mx and +1000 N tip Fz",
        "scope": "linearized Fz trace only; not a nonlinear six-channel connection or qualification",
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        with (output_dir / "results.jsonl").open("w") as stream:
            for topology in ("Q4", "S3-V2D"):
                shell = FlatE4TrialPanel(make_shell(4, topology, n_y=4))
                beam = build(16)
                kkt = assemble_channel_basis_reference_kkt(
                    shell, beam, spaces, shell_port="physical_strip_005_005",
                    shell_support_policy="full_left_edge")
                candidate = window_constraint(kkt, shell, beam, p0, .05)
                cases = {}
                for name, constraint in (("point", kkt.constraint_jacobian),
                                         ("window", candidate)):
                    cases[name] = {
                        "mode": mode(kkt, shell, beam, spaces, constraint),
                        "torque": loaded(kkt, shell, beam, constraint, 3),
                        "shear": loaded(kkt, shell, beam, constraint, 2),
                    }
                row = {"topology": topology, "cases": cases,
                       "shape_checks": {
                           "partition_max_error": float(max(abs(window_shape(s, 16, .05).sum() - 1)
                                                            for s in np.linspace(0, 1, 65))),
                           "first_moment_max_error_m": float(max(abs(window_shape(s, 16, .05) @
                                                                    np.linspace(0, 1, 17) - s)
                                                                 for s in np.linspace(0, 1, 65))),
                       }}
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(topology, cases["point"]["mode"]["HminusHalf"]["beta_lower"],
                      cases["window"]["mode"]["HminusHalf"]["beta_lower"], flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    run(parser.parse_args().output_dir)
