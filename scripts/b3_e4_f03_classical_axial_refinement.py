"""Sparse classical axial weak-line refinement, separate from native F03.

Q4/CST membrane, quadratic/Hermite Timoshenko beam, and continuous-P1
three-channel variational line. The matched support and axial density make
this a useful independent continuum diagnostic, not a native operator oracle.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_coupled as coupled
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell


def one_case(topology: str, n: int, *, equilibrate: bool = False) -> dict:
    if topology not in ("Q4", "CST") or n not in (8, 16, 32, 64, 128, 256):
        raise ValueError("bounded classical axial refinement required")
    began = time.perf_counter()
    model = shell.panel(n, n, topology)
    n_beam = 2*n
    result = coupled.solve(model, n_beam, n, "P1", "axial_sine",
                           equilibrate=equilibrate)
    gap = line.integrated_gap(model, n_beam, n, result.shell, result.beam)
    shell_reaction = float(np.sum(result.shell_reactions[0::2]))
    beam_reaction = float(result.beam_reactions[0])
    tip = float(result.beam[2*n_beam])
    fields = []
    for station in (0., .25, .5, .75, 1.):
        shell_pose = np.asarray(shell.pose(model, station)@result.shell).ravel()
        beam_pose = np.asarray(beam.trace(n_beam, station)@result.beam).ravel()
        fields.append(dict(station=station,
                           shell_axial_m=float(shell_pose[0]),
                           beam_axial_m=float(beam_pose[0]),
                           axial_gap_m=float(beam_pose[0]-shell_pose[0])))
    return dict(
        status="UNREGISTERED_CLASSICAL_AXIAL_REFERENCE_DIAGNOSTIC",
        numerical_solver=("symmetric_row_equilibration_6_passes" if equilibrate
                          else "raw_sparse_direct"),
        topology=topology, shell_hosts=n, shell_transverse_intervals=n,
        shell_elements=len(model.elements), shell_nodes=len(model.nodes),
        beam_elements=n_beam, multiplier_intervals=n,
        physical_load="q_x(s)=1e5 sin(2 pi s) N/m, s in [0,1] m",
        shell_support="both x edges ux/uy fixed",
        beam_root="u,v,theta fixed",
        distinct_from_native=("classical Q4/CST membrane",
                              "quadratic/Hermite Timoshenko beam",
                              "three-channel P1 weak line"),
        beam_tip_axial_m=tip,
        shell_reaction_fx_n=shell_reaction,
        beam_root_reaction_fx_n=beam_reaction,
        global_axial_balance_n=shell_reaction+beam_reaction,
        shell_energy_j=result.shell_energy,
        beam_energy_j=result.beam_energy,
        external_work_j=result.external_work,
        energy_work_relative_error=float(abs(
            result.shell_energy+result.beam_energy-.5*result.external_work)
            /max(abs(.5*result.external_work), 1e-16)),
        gap_l2_m=gap,
        algebraic_residual_ratio=result.algebraic_residual_ratio,
        weak_compatibility_ratio=result.weak_compatibility_ratio,
        weak_gap_l2=float(np.linalg.norm(result.weak_gap)),
        station_fields=fields,
        elapsed_seconds=time.perf_counter()-began)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", required=True, choices=("Q4", "CST"))
    parser.add_argument("--n", required=True, type=int, choices=(8, 16, 32, 64))
    parser.add_argument("--equilibrated", action="store_true")
    args = parser.parse_args()
    print(json.dumps(one_case(args.topology, args.n,
                              equilibrate=args.equilibrated),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
