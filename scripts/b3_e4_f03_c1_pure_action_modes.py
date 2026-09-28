"""Compare pure P0 transverse-force and torque component work.

Reuses the reviewed 24 saved solid unit responses and the native x4
E4/B3 component operators. This is an open-interface linear influence,
not a re-equilibrated bonded solve or a contact-state claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.b3_e4_f03_c1_component_compliance import (
    _native_matrices, _solid_matrices,
)
from scripts.b3_e4_f03_c1_material_line_loaded import (
    _validated_solid_reconstruction,
)
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest


def evaluate(reconstruction_path: Path) -> dict:
    solid = _validated_solid_reconstruction(reconstruction_path)
    solid_shell, solid_bar = _solid_matrices(solid)
    native_shell, native_bar, native_diagnostics = _native_matrices()
    matrices = {"solid_plate": solid_shell, "solid_bar": solid_bar,
                "native_E4": native_shell, "native_B3": native_bar}
    for name, matrix in matrices.items():
        if matrix.shape != (24, 24) or not np.isfinite(matrix).all():
            raise ArithmeticError(f"incomplete {name} P0 component work matrix")

    cases = {}
    for label, channel, resultant, unit in (
            ("transverse_Fz", 2, 1000., "N"),
            ("torsion_Mx", 3, 100., "Nm")):
        interval = []
        for i in range(4):
            coefficient = np.zeros(24)
            coefficient[6*i+channel] = 1.
            work = {name: float(coefficient@matrix@coefficient)
                    for name, matrix in matrices.items()}
            if any(value <= 0. for value in work.values()):
                raise ArithmeticError("pure physical interval work is nonpositive")
            interval.append({
                "interval_index": i,
                "x_interval_m": [float(.9+.025*i), float(.925+.025*i)],
                "integrated_interface_resultant": resultant,
                "component_work_J": work,
                "native_E4_vs_solid_plate_relative": (
                    work["native_E4"]/work["solid_plate"]-1.),
                "native_B3_vs_solid_bar_relative": (
                    work["native_B3"]/work["solid_bar"]-1.),
            })
        # Each interval receives one quarter of the same total
        # resultant, so the uniform physical line density is constant.
        coefficient = np.zeros(24)
        coefficient[channel::6] = .25
        uniform = {name: float(coefficient@matrix@coefficient)
                   for name, matrix in matrices.items()}
        if any(value <= 0. for value in uniform.values()):
            raise ArithmeticError("uniform pure physical work is nonpositive")
        uncoupled = {name: sum(item["component_work_J"][name]
                                for item in interval)/16.
                     for name in matrices}
        cases[label] = {
            "resultant": resultant,
            "resultant_unit": unit,
            "intervals": interval,
            "uniform_component_work_J": uniform,
            "uniform_native_E4_vs_solid_plate_relative": (
                uniform["native_E4"]/uniform["solid_plate"]-1.),
            "uniform_native_B3_vs_solid_bar_relative": (
                uniform["native_B3"]/uniform["solid_bar"]-1.),
            "uniform_minus_uncoupled_interval_work_J": {
                name: uniform[name]-uncoupled[name] for name in matrices},
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "pure P0 material-line transverse-force and torque action work",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "native_component_diagnostics": native_diagnostics,
        "cases": cases,
        "limitations": [
            "linear open-interface influence with separate plate/bar and E4/B3 domains",
            "not a standalone contact state or re-equilibrated bonded comparison",
            "interval and uniform responses include different longitudinal action shapes",
            "pure positive work does not by itself establish physical torque/shear fidelity",
            "not multiplier-space, F03 or G0B acceptance",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous pure-action result")
    result = evaluate(args.reconstruction.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({key: {
        "shell_relative": value["uniform_native_E4_vs_solid_plate_relative"],
        "beam_relative": value["uniform_native_B3_vs_solid_bar_relative"]}
        for key, value in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
