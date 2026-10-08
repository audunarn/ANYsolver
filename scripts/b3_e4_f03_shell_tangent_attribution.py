"""Bounded F03 shell-block sensitivity; the mixed operator is not a model.

Replace only the native E4 in-plane tangent block with the separately
assembled physical membrane block. Supports, load, beam, weak line, and every
other E4 block remain fixed. This attributes sensitivity, not qualification.
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_reference_kkt)
from scripts.b3_e4_f03_weak_line_resolution_screen import (
    one_case, sinusoidal_axial_density_load)


def sensitivity(topology: str, n_s: int, n_y: int) -> dict:
    """Compare the unmodified native KKT with one in-plane-block substitution."""
    if topology not in ("Q4", "S3-V2D") or n_s not in (4, 8) or n_y not in (2, 4, 8):
        raise ValueError("bounded shell-block sensitivity grid required")
    shell = FlatE4TrialPanel(make_shell(n_s, topology, n_y=n_y))
    beam = build(4*n_s)
    space = LineMultiplierSpace("continuous_linear", tuple(np.linspace(0., 1., n_s+1)))
    kkt = assemble_reference_kkt(
        shell, beam, space, shell_support_policy="both_xy_edges")
    shell_size = 6*shell.panel.node_count
    load = np.r_[np.zeros(shell_size), sinusoidal_axial_density_load(beam)]
    planar = (6*np.arange(shell.panel.node_count)[:, None]
              + np.array((0, 1))[None, :]).ravel()
    full_block = kkt.primal_tangent[np.ix_(planar, planar)]
    physical_block = shell.panel.stiffness.toarray()
    delta = physical_block-full_block
    free = kkt.free_primal
    scale = kkt.coordinate_scale
    right = np.r_[load[free]*scale[:len(free)]/kkt.energy_scale,
                  np.zeros(kkt.constraint_jacobian.shape[0])]

    def solve(replace: bool) -> dict:
        primal = kkt.primal_tangent.copy()
        if replace:
            primal[np.ix_(planar, planar)] = physical_block
        if replace:
            c = kkt.constraint_jacobian[:, free]
            reduced = primal[np.ix_(free, free)]
            system = np.block([[reduced, c.T],
                               [c, np.zeros((c.shape[0], c.shape[0]))]])
            scaled = scale[:, None]*system*scale[None, :]/kkt.energy_scale
        else:
            scaled = kkt.scaled_system
        state = np.linalg.solve(scaled, right)
        result = scale*state
        q = np.zeros(len(load))
        q[free] = result[:len(free)]
        lam = result[len(free):]
        residual = primal@q+kkt.constraint_jacobian.T@lam-load
        fixed_shell = np.ones(shell_size, dtype=bool)
        fixed_shell[free[free < shell_size]] = False
        return dict(
            beam_tip_ux_m=float(q[shell_size+6*beam.n_half_cells]),
            shell_reaction_fx_n=float(np.sum(
                residual[:shell_size:6][fixed_shell[0::6]])),
            shell_energy_j=float(.5*q[:shell_size]@primal[:shell_size, :shell_size]@q[:shell_size]),
            scaled_residual=float(np.linalg.norm(scaled@state-right)))

    native = solve(False)
    substituted = solve(True)
    return dict(
        topology=topology, n_s=n_s, n_y=n_y,
        full_block_relative_difference=float(np.linalg.norm(delta)/np.linalg.norm(physical_block)),
        native=native, substituted=substituted,
        tip_change_fraction=float((substituted["beam_tip_ux_m"]-native["beam_tip_ux_m"])
                                  /native["beam_tip_ux_m"]),
        reaction_change_fraction=float((substituted["shell_reaction_fx_n"]-
                                        native["shell_reaction_fx_n"])
                                       /native["shell_reaction_fx_n"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell-host-intervals", type=int, choices=(4, 8), default=4)
    parser.add_argument("--transverse-intervals", type=int, nargs="+", choices=(2, 4, 8),
                        default=(2, 4, 8))
    args = parser.parse_args()
    rows = [sensitivity(topology, args.shell_host_intervals, n_y)
            for topology in ("Q4", "S3-V2D") for n_y in args.transverse_intervals]
    print(json.dumps(dict(
        status="UNREGISTERED_NONPHYSICAL_OPERATOR_SENSITIVITY",
        fixed="native B3, six-channel weak line, rail port, physical load, both-edge supports",
        replacement="only native E4 in-plane tangent block; all cross/other blocks retained",
        cases=rows), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
