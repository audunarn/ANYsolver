"""Compare pure P0 physical actions and a saved mixed Fz action.

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
    CHANNELS, SCALE, _native_matrices, _solid_matrices,
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
            ("axial_Fx", 0, 1000., "N"),
            ("transverse_Fz", 2, 1000., "N"),
            ("torsion_Mx", 3, 100., "Nm"),
            ("bending_My", 4, 100., "Nm")):
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
    saved_fz_density = np.asarray(solid["cases"]["tip_fz"][
        "dual_physical_line_density"])
    coefficient = saved_fz_density/SCALE
    if coefficient.shape != (24,):
        raise ValueError("saved mixed Fz action inventory changed")
    grouped = {name: np.where(np.arange(24)%6 == i, coefficient, 0.)
               for i, name in enumerate(CHANNELS)}
    mixed_fz = {}
    for domain, matrix in matrices.items():
        self_work = {name: float(vector@matrix@vector)
                     for name, vector in grouped.items()}
        cross_work = {f"{left}×{right}": float(
            grouped[left]@matrix@grouped[right]+grouped[right]@matrix@grouped[left])
            for i, left in enumerate(CHANNELS)
            for right in CHANNELS[i+1:]}
        total = float(coefficient@matrix@coefficient)
        if abs(total-sum(self_work.values())-sum(cross_work.values())) > (
                1e-10*max(1., abs(total))):
            raise ArithmeticError("saved mixed-channel work did not decompose")
        mixed_fz[domain] = {"total_work_J": total,
                            "same_channel_work_J": self_work,
                            "cross_channel_work_J": cross_work}
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "pure P0 axial/shear/bending/torsion and mixed Fz work",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "native_component_diagnostics": native_diagnostics,
        "cases": cases,
        "saved_mixed_tip_fz_action": mixed_fz,
        "limitations": [
            "linear open-interface influence with separate plate/bar and E4/B3 domains",
            "not a standalone contact state or re-equilibrated bonded comparison",
            "interval and uniform responses include different longitudinal action shapes",
            "pure positive work does not by itself establish physical torque/shear fidelity",
            "mixed channel and cross terms are signed and may cancel; not independent energies",
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
