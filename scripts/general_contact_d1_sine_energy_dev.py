"""Compare two finite Q1 pressure modes with an idealized source plate.

This independent sine calculation is a development scale discriminator. The
Kirchhoff source-only plate is not the complete two-body shell continuum.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _hat_sine_integrals(elements: int, modes: int) -> np.ndarray:
    """Integrals of interior uniform Q1 hats against sin(m*pi*x)."""
    h = 1.0/elements
    indices = np.arange(1, elements, dtype=float)[:, None]
    frequency = np.arange(1, modes+1, dtype=float)[None, :]
    angle = np.pi*frequency*h
    return (2.0*(1.0-np.cos(angle))*np.sin(indices*angle)
            / (h*(np.pi*frequency)**2))


def _continuum_dual_squared(pressure: np.ndarray, bending: float,
                            cutoff: int) -> float:
    rows, columns = pressure.shape
    x = _hat_sine_integrals(columns-1, cutoff)
    y = _hat_sine_integrals(rows-1, cutoff)
    coefficients = 2.0*y.T @ pressure[1:-1, 1:-1] @ x
    indices = np.arange(1, cutoff+1, dtype=float)
    wave_squared = np.pi**2*(indices[:, None]**2+indices[None, :]**2)
    return float(np.sum(coefficients**2/(bending*wave_squared**2)))


def analyze(path: Path, *, young_pa: float, poisson: float,
            thickness_m: float):
    if (not np.isfinite(young_pa) or young_pa <= 0.0
            or not np.isfinite(poisson) or not -1.0 < poisson < 0.5
            or not np.isfinite(thickness_m) or thickness_m <= 0.0):
        raise ValueError("source plate properties must be physically finite")
    bending = young_pa*thickness_m**3/(12.0*(1.0-poisson**2))
    saved = json.loads(path.read_text(encoding="utf-8"))
    cases = []
    for case in saved["cases"]:
        faces = case["source_q4_faces"]
        rows = 4
        if faces % rows:
            raise ValueError("only the declared four-row source family is admitted")
        columns = faces//rows
        pressure = np.zeros((rows+1, columns+1))
        ids = case["signed_interior_mode_ids"]
        mode = case["smallest_signed_mode_mass_normalized"]
        if len(ids) != len(mode) or len(ids) != (rows-1)*(columns-1):
            raise ValueError("signed interior mode does not cover the full interior")
        for node, coefficient in zip(ids, mode, strict=True):
            row, column = divmod(int(node)-1, columns+1)
            if not (0 < row < rows and 0 < column < columns):
                raise ValueError("pressure mode reaches a physical source rim")
            pressure[row, column] = coefficient
        reference = {str(cutoff): _continuum_dual_squared(
            pressure, bending, cutoff) for cutoff in (16, 32, 64, 128)}
        discrete = case["production_work_singular_values_squared"][0]
        oracle = case["independent_vertical_work_singular_values_squared"][0]
        cases.append({
            "source_q4_faces": faces,
            "source_grid": [columns, rows],
            "discrete_two_body_dual_squared": discrete,
            "frozen_vertical_two_body_dual_squared": oracle,
            "idealized_source_kirchhoff_dual_squared": reference,
            "discrete_to_idealized_source_ratio_squared_128": (
                discrete/reference["128"]),
            "reference_tail_fraction_64_to_128": (
                (reference["128"]-reference["64"])/reference["128"]),
        })
    return {"input": str(path), "young_pa": young_pa, "poisson": poisson,
            "thickness_m": thickness_m, "bending_n_m": bending,
            "interpretation": (
                "Idealized simply supported Kirchhoff source plate only; "
                "no full shell inf-sup or D1 acceptance claim"),
            "cases": cases}


def main(input_path: Path, output_path: Path):
    if output_path.exists():
        raise FileExistsError(output_path)
    payload = analyze(input_path, young_pa=1.0e5, poisson=0.3,
                      thickness_m=0.05)
    output_path.write_text(json.dumps(payload, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"cases": [{
        "source_q4_faces": item["source_q4_faces"],
        "idealized_source_dual_squared": (
            item["idealized_source_kirchhoff_dual_squared"]["128"]),
        "discrete_to_source_ratio_squared": (
            item["discrete_to_idealized_source_ratio_squared_128"]),
    } for item in payload["cases"]]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    main(args.input, args.output)
