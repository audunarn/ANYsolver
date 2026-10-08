"""Bounded F03 axial comparison with a separately assembled classical model.

The shell supports, section constants, signed load density, four-sample rail
and P1 test functions are matched. The classical Q4 and beam interior fields
are not identified with E4 Q4 and native B3-GE; this is development evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

# The older independent preflight modules use script-local imports.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _b3_e4_f03_independent_beam as classical_beam
import _b3_e4_f03_independent_coupled as classical_coupled
import _b3_e4_f03_independent_line as classical_line
import _b3_e4_f03_independent_shell as classical_shell

from scripts._b3_e4_f03_native_fixture import (
    AREA, E, G, I, SHEAR_AREA)
from scripts.b3_e4_f03_weak_line_resolution_screen import one_case


def compare(topology: str, n_s: int, n_y: int) -> dict:
    """Solve independent and native systems from the same stated inputs."""
    if topology not in ("Q4", "S3-V2D") or n_s not in (2, 4, 8) or n_y not in (2, 4, 8):
        raise ValueError("bounded axial comparison grid required")
    if not (classical_beam.E == E and
            classical_beam.AREA == AREA and
            classical_beam.SHEAR_AREA == SHEAR_AREA and
            classical_beam.INERTIA == I and
            classical_beam.G == G and
            classical_shell.E == E and
            classical_shell.THICKNESS == .07):
        raise ValueError("independent and native section or shell data differ")
    n_beam = 2*n_s
    native = one_case(
        topology, n_s, "continuous_linear", shell_port="rail",
        load_kind="sinusoidal_axial_density", n_s=n_s,
        native_half_cells=2*n_beam, n_y=n_y,
        shell_support_policy="both_xy_edges")
    classical_topology = "Q4" if topology == "Q4" else "CST"
    shell = classical_shell.panel(n_s, n_y, classical_topology)
    classical = classical_coupled.solve(
        shell, n_beam, n_s, "P1", "axial_sine")
    classical_tip = float(classical.beam[2*n_beam])
    gap = classical_line.integrated_gap(
        shell, n_beam, n_s, classical.shell, classical.beam)
    shell_reaction = float(np.sum(classical.shell_reactions[0::2]))
    beam_reaction = float(classical.beam_reactions[0])
    out = dict(
        topology=topology, n_s=n_s, n_y=n_y,
        native=native,
        classical=dict(
            topology=classical_topology,
            beam_elements=n_beam, mortar_intervals=n_s,
            axial_tip_m=classical_tip,
            gap_l2_m=gap,
            shell_energy_j=classical.shell_energy,
            beam_energy_j=classical.beam_energy,
            shell_reaction_fx_n=shell_reaction,
            beam_root_reaction_fx_n=beam_reaction,
            global_axial_balance_n=shell_reaction+beam_reaction,
            algebraic_residual_ratio=classical.algebraic_residual_ratio,
            weak_compatibility_ratio=classical.weak_compatibility_ratio),
        tip_relative_difference=abs(native["beam_tip_ux_m"]-classical_tip)/
        abs(classical_tip))
    if not np.isfinite(out["tip_relative_difference"]):
        raise ArithmeticError("nonfinite axial comparison")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell-host-intervals", type=int,
                        choices=(2, 4, 8), default=4)
    parser.add_argument("--transverse-intervals", type=int, nargs="+",
                        choices=(2, 4, 8), default=(2, 4, 8))
    args = parser.parse_args()
    rows = [compare(topology, args.shell_host_intervals, n_y)
            for topology in ("Q4", "S3-V2D")
            for n_y in args.transverse_intervals]
    print(json.dumps(dict(
        status="UNREGISTERED_MATCHED_IDEALIZATION_DIAGNOSTIC",
        physical_load="q_x(s)=1e5 sin(2 pi s) N/m, s in [0,1] m",
        native_shell_support="both_xy_edges; left z/rx/ry fixed",
        classical_shell_support="both x edges ux/uy fixed",
        beam_root="all native or three classical planar root coordinates fixed",
        shell_port="four-sample rail",
        multiplier="continuous P1, one interval per shell host",
        distinct_laws=("classical Q4 versus E4 Q4",
                       "classical quadratic interior axial trace versus native half-cell trace",
                       "classical planar three-channel versus native six-channel coupling"),
        cases=rows), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
