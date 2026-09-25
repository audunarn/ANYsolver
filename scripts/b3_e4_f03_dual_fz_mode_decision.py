"""Fixed-mesh dual-Fz mode decision, using its actual piecewise dual norm.

This is a bounded development diagnostic, not an inf-sup certificate.
"""

from __future__ import annotations

import hashlib
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
from scripts._b3_e4_f03_dual_linear_norm import (
    dual_linear_cosine_moments, dual_linear_gram,
)
from scripts._b3_e4_f03_p0_dual_norm import cell_cosine_moments, p0_dual_gram
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_channel_basis_reference_kkt,
)


def norm_gram(kind: str, cells: int, power: float, last: int = 4095):
    if kind == "piecewise_constant" and power == -.5:
        return p0_dual_gram(cells, 1., last)
    if kind == "dual_linear" and power == -.5:
        return dual_linear_gram(cells, 1., last)
    h = 1. / cells
    if kind == "piecewise_constant":
        moments_fn = cell_cosine_moments
        mass = np.eye(cells) * h
    elif kind == "dual_linear":
        moments_fn = dual_linear_cosine_moments
        mass = np.diag(np.r_[h, np.full(cells - 1, 2 * h), h])
        adjacent = np.arange(cells)
        mass[adjacent, adjacent + 1] = -h / 2
        mass[adjacent + 1, adjacent] = -h / 2
    else:
        raise ValueError("unexpected line space")
    weighted = np.zeros_like(mass)
    projection = np.zeros_like(mass)
    for first in range(0, last + 1, 1024):
        stop = min(first + 1024, last + 1)
        moments = moments_fn(cells, first, stop)
        modes = np.arange(first, stop, dtype=float)
        weight = (1 + (np.pi * modes)**2)**power
        weighted += (moments * weight[None, :]) @ moments.T
        projection += moments @ moments.T
    residual = (mass - projection + mass.T - projection.T) / 2
    eigen, vectors = linalg.eigh(residual)
    if eigen[0] < -1e-10 / cells:
        raise ArithmeticError("dual cosine projection exceeds Parseval mass")
    residual = (vectors * np.maximum(eigen, 0.)) @ vectors.T
    lower = (weighted + weighted.T) / 2
    upper = lower + (1 + (np.pi * (last + 1))**2)**power * residual
    return lower, (upper + upper.T) / 2


def run(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RuntimeError("run requires clean source")
    p0 = LineMultiplierSpace("piecewise_constant", (0., .25, .5, .75, 1.))
    dual = LineMultiplierSpace("dual_linear", p0.knots)
    mx = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 9)))
    spaces = (p0, p0, dual, mx, p0, p0)
    control = output_dir.parent / "f03-p1fz-p0mx-modes-dev-20260925-v1" / "results.jsonl"
    controls = [json.loads(line) for line in control.read_text().splitlines()]
    manifest = {
        "question": "Does the local coarse dual Fz basis suppress the alternating transverse mode that survived P0/P1?",
        "decision": "If not, stop dual-Fz row-space development; revise physical trace/connection before another ratio sweep.",
        "source_sha": source, "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__, "threads": 1,
        "mesh": "Q4/S3 x8/y4, native beam-half16, physical square strip .05/.05 m",
        "control_path": str(control),
        "control_sha256": hashlib.sha256(control.read_bytes()).hexdigest(),
        "norms": ["Neumann H^-1/2", "Neumann H^-1"],
        "scope": "finite-mesh physical-action diagnostic only",
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        with (output_dir / "results.jsonl").open("w") as stream:
            for topology, control_row in zip(("Q4", "S3-V2D"), controls):
                if control_row["topology"] != topology:
                    raise ValueError("control topology order changed")
                shell = FlatE4TrialPanel(make_shell(4, topology, n_y=4))
                beam = build(16)
                kkt = assemble_channel_basis_reference_kkt(
                    shell, beam, spaces, shell_port="physical_strip_005_005",
                    shell_support_policy="full_left_edge")
                free = kkt.free_primal
                n = len(free)
                rows = kkt.constraint_jacobian.shape[0]
                if n + rows > 1200:
                    raise ValueError("bounded dense limit exceeded")
                physical = int(np.count_nonzero(
                    free < 6 * shell.panel.node_count + beam.context.nodal_count))
                shell_physical = int(np.count_nonzero(
                    free < 6 * shell.panel.node_count))
                scale = kkt.coordinate_scale[:n]
                stiffness = kkt.primal_tangent[np.ix_(free, free)]
                scaled = (scale[:, None] * stiffness) * scale[None, :] / kkt.energy_scale
                kp, kpr = scaled[:physical, :physical], scaled[:physical, physical:]
                krp, kr = scaled[physical:, :physical], scaled[physical:, physical:]
                retained = linalg.solve(kr, krp, assume_a="sym")
                physical_schur = kp - kpr @ retained
                ep, up = linalg.eigh(physical_schur)
                er, ur = linalg.eigh(kr)
                if ep[0] <= 1e-10 * ep[-1] or min(abs(er)) <= 1e-12 * max(abs(er)):
                    raise ArithmeticError("physical/retained energy split failed")
                channels = [axis for axis, space in enumerate(spaces)
                            for _ in range(space.count)]
                displacement_scale = 1e6 / (210e9 * .07)
                row_scale = np.array([1. if axis < 3 else .46 for axis in channels]) / displacement_scale
                cbar = (row_scale[:, None] * kkt.constraint_jacobian[:, free]) * scale[None, :]
                cp, cr = cbar[:, :physical], cbar[:, physical:]
                effective = cp - cr @ retained
                bp = effective @ (up / np.sqrt(ep)[None, :])
                br = cr @ (ur / np.sqrt(np.abs(er))[None, :])
                action = bp @ bp.T + br @ br.T
                selected = [i for i, axis in enumerate(channels) if axis in (2, 3, 4)]
                action = action[np.ix_(selected, selected)]
                action = (action + action.T) / 2
                result = {"topology": topology, "row_count": rows,
                          "row_rank": int(np.linalg.matrix_rank(kkt.constraint_jacobian[:, free])),
                          "p1_control": control_row}
                for name, power in (("HminusHalf", -.5), ("HminusOne", -1.)):
                    gr = [norm_gram(space.kind, len(space.knots) - 1, power)
                          for space in (dual, mx, p0)]
                    lower = linalg.block_diag(*(g[0] for g in gr))
                    upper = linalg.block_diag(*(g[1] for g in gr))
                    eigen, vectors = linalg.eigh(action, upper)
                    mode = vectors[:, 0]
                    fz = mode[:dual.count]
                    signs = np.sign(fz[np.abs(fz) > 1e-8 * max(abs(fz))])
                    shares = []
                    start = 0
                    for space, g in zip((dual, mx, p0), gr):
                        part = mode[start:start + space.count]
                        shares.append(float(part @ g[1] @ part))
                        start += space.count
                    force = effective[selected, :].T @ mode
                    shell_force = force[:shell_physical]
                    beam_force = force[shell_physical:]
                    shell_action = float(shell_force @ linalg.solve(
                        physical_schur[:shell_physical, :shell_physical],
                        shell_force, assume_a="pos"))
                    beam_action = float(beam_force @ linalg.solve(
                        physical_schur[shell_physical:, shell_physical:],
                        beam_force, assume_a="pos"))
                    retained_action = float(np.linalg.norm(br[selected, :].T @ mode)**2)
                    parts = np.array((shell_action, beam_action, retained_action))
                    total_action = float(mode @ action @ mode)
                    if abs(float(parts.sum()) - total_action) > 1e-8 * max(1., total_action):
                        raise ArithmeticError("physical/retained action closure failed")
                    result[name] = {
                        "beta_lower": float(np.sqrt(max(0., eigen[0]))),
                        "beta_upper": float(np.sqrt(max(0., linalg.eigh(action, lower, eigvals_only=True)[0]))),
                        "gram_relative_enclosure": float(linalg.eigvalsh(upper, lower)[-1] - 1.),
                        "fz_mx_my_shares": (np.array(shares) / sum(shares)).tolist(),
                        "fz_sign_changes": int(np.count_nonzero(signs[1:] != signs[:-1])),
                        "fz_coefficients": fz.tolist(),
                        "shell_beam_physical_beam_retained_action_shares": (parts / parts.sum()).tolist(),
                        "action_closure_error": float(parts.sum() - total_action),
                    }
                stream.write(json.dumps(result, allow_nan=False) + "\n")
                stream.flush()
                print(topology, result["HminusHalf"]["beta_lower"],
                      result["HminusOne"]["beta_lower"], flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    run(parser.parse_args().output_dir)
