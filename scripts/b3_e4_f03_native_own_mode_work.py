"""Recover physical work for native Q4/S3 weakest transverse line modes.

The registered fixed mesh is unchanged. The absolute retained-coordinate
action used for the diagnostic quotient is reported separately from the
positive shell/beam strain work induced by its multiplier vector.
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
from scripts._b3_e4_f03_shell_spatial_linear_port import physical_shell_stiffness
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_channel_basis_reference_kkt,
)
from scripts.b3_e4_f03_beam_window_decision import mode as weakest_mode


def recovered_work(kkt, shell, beam, spaces, selected: list[int],
                   coefficients: list[float]) -> dict:
    """Apply the mode's physical interface wrench to uncoupled domains."""
    shell_size = 6 * shell.panel.node_count
    channels = [axis for axis, space in enumerate(spaces)
                for _ in range(space.count)]
    if (len(channels) != len(kkt.constraint_jacobian) or
            len(selected) != len(coefficients)):
        raise ValueError("mode/line-row inventory changed")
    displacement_scale = 1e6 / (210e9 * .07)
    row_scale = np.array([1. if axis < 3 else .46
                          for axis in channels]) / displacement_scale
    multipliers = np.zeros(len(channels))
    multipliers[selected] = coefficients
    multipliers *= row_scale
    shell_load = kkt.constraint_jacobian[:, :shell_size].T @ multipliers
    beam_load = kkt.constraint_jacobian[:, shell_size:].T @ multipliers
    shell_free = kkt.free_primal[kkt.free_primal < shell_size]
    beam_free = (kkt.free_primal[kkt.free_primal >= shell_size] -
                 shell_size)
    shell_k = kkt.primal_tangent[:shell_size, :shell_size]
    beam_k = beam.tangent.toarray()
    shell_q = np.zeros(shell_size)
    beam_q = np.zeros(beam.context.count)
    shell_q[shell_free] = linalg.solve(
        shell_k[np.ix_(shell_free, shell_free)], shell_load[shell_free],
        assume_a="pos")
    beam_q[beam_free] = linalg.solve(
        beam_k[np.ix_(beam_free, beam_free)], beam_load[beam_free],
        assume_a="sym")
    max_nodal = max(float(np.max(np.abs(shell_q))),
                    float(np.max(np.abs(beam_q[:beam.context.nodal_count]))))
    if not np.isfinite(max_nodal) or max_nodal < 1e-20:
        raise ArithmeticError("weak mode has no physical response")
    amplitude = 1e-6 / max_nodal
    shell_q *= amplitude
    beam_q *= amplitude
    shell_load *= amplitude
    beam_load *= amplitude
    shell_residual = shell_k @ shell_q - shell_load
    beam_residual = beam_k @ beam_q - beam_load
    shell_ratio = float(np.linalg.norm(shell_residual[shell_free]) /
                        max(np.linalg.norm(shell_load[shell_free]), 1.))
    beam_ratio = float(np.linalg.norm(beam_residual[beam_free]) /
                       max(np.linalg.norm(beam_load[beam_free]), 1.))
    if max(shell_ratio, beam_ratio) > 1e-9:
        raise ArithmeticError("uncoupled physical mode solve failed")
    shell_action = float(shell_q @ shell_k @ shell_q)
    physical_shell = float(shell_q @ (
        physical_shell_stiffness(shell.panel) @ shell_q))
    numerical_shell = shell_action - physical_shell
    beam_action = float(beam_q @ beam_k @ beam_q)
    mechanical = beam.context.advance(
        beam.context.initial.mechanical, beam_q)
    components = np.zeros(6)
    stations = 0
    measure = 0.
    for index, (_, element) in enumerate(beam.context.elements):
        for point in element.operator.recover(
                mechanical.cell_rotations[index],
                mechanical.resultants[index],
                origin=beam.context.initial.origins[index]):
            components += point["measure"] * (
                point["resultants"] + point["resultants_low"]) * (
                point["strain"] + point["strain_low"])
            measure += point["measure"]
            stations += 1
    if (shell_action <= 0 or beam_action <= 0 or
            abs(float(components.sum()) - beam_action) >
            2e-9 * beam_action or abs(measure - 1.) > 1e-12 or
            numerical_shell < -1e-8 * shell_action):
        raise ArithmeticError("physical shell/beam action closure failed")
    total = shell_action + beam_action
    return {
        "shell_beam_physical_action_shares": [shell_action / total,
                                               beam_action / total],
        "beam_axial_shear_y_shear_z_torsion_bend_y_bend_z_actions_j": components.tolist(),
        "beam_bending_shear_z_shares": [float(components[4] / beam_action),
                                         float(components[2] / beam_action)],
        "shell_action_j": shell_action,
        "shell_physical_action_j": physical_shell,
        "shell_numerical_action_j": numerical_shell,
        "beam_action_j": beam_action,
        "beam_strain_work_closure_relative": float(
            (components.sum() - beam_action) / beam_action),
        "shell_equilibrium_residual_ratio": shell_ratio,
        "beam_equilibrium_residual_ratio": beam_ratio,
        "amplitude_to_one_micron": amplitude,
        "max_native_retained_increment": float(np.max(np.abs(
            beam_q[beam.context.nodal_count:]))),
        "beam_recovery_stations": stations,
    }


def run(output_dir: Path) -> None:
    source = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"],
                               text=True).strip():
        raise RuntimeError("run requires clean source")
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "question": "Does the native Q4/S3 model's own weakest transverse mode carry physical beam shear, or an unsupported shell/retained branch, as Fz rows increase at fixed resolution?",
        "decision": "Use physical and algorithmic action together to decide whether the line-space problem remains; neither a finite quotient nor a shear shift alone is qualification.",
        "source_sha": source, "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__, "threads": 1,
        "mesh": "Q4/S3 shell x8/y4, native B3 half16, fixed .05/.05 m physical strip",
        "spaces": ["P0-4 Fz and other channels / P0-8 Mx",
                   "P0-8 all six channels"],
        "norms": ["Neumann H^-1/2", "Neumann H^-1"],
        "scope": "same fixed discrete model, actual native section recovery; no continuum inf-sup or production selection",
        "dense_limit": 1200,
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        with (output_dir / "results.jsonl").open("w") as stream:
            coarse = LineMultiplierSpace(
                "piecewise_constant", (0., .25, .5, .75, 1.))
            fine = LineMultiplierSpace(
                "piecewise_constant", tuple(np.linspace(0., 1., 9)))
            for topology in ("Q4", "S3-V2D"):
                shell = FlatE4TrialPanel(make_shell(4, topology, n_y=4))
                beam = build(16)
                for label, spaces in (
                        ("coarse_Fz_fine_Mx",
                         (coarse, coarse, coarse, fine, coarse, coarse)),
                        ("fine_all", (fine,) * 6)):
                    kkt = assemble_channel_basis_reference_kkt(
                        shell, beam, spaces,
                        shell_port="physical_strip_005_005",
                        shell_support_policy="full_left_edge")
                    diagnostic = weakest_mode(
                        kkt, shell, beam, spaces, kkt.constraint_jacobian)
                    selected = diagnostic["transverse_row_indices"]
                    row = {"topology": topology, "space": label,
                           "row_count": diagnostic["row_count"],
                           "row_rank": diagnostic["row_rank"]}
                    for norm in ("HminusHalf", "HminusOne"):
                        values = diagnostic[norm]
                        physical = recovered_work(
                            kkt, shell, beam, spaces, selected,
                            values["transverse_mode_coefficients"])
                        algorithmic = np.array((
                            values["algorithmic_physical_action"],
                            values["algorithmic_retained_absolute_action"]))
                        row[norm] = {
                            "beta_lower": values["beta_lower"],
                            "beta_upper": values["beta_upper"],
                            "fz_sign_changes": values["fz_sign_changes"],
                            "algorithmic_physical_retained_absolute_shares": (
                                algorithmic / algorithmic.sum()).tolist(),
                            "physical": physical,
                        }
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                    stream.flush()
                    print(topology, label,
                          row["HminusOne"]["physical"]["beam_bending_shear_z_shares"],
                          flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    run(parser.parse_args().output_dir)
