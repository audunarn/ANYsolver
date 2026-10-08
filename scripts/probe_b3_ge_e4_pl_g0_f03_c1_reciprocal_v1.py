"""Bounded development-only C1 bond-ratio discriminator; not G0 acceptance."""

import argparse
import json
import os
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import scipy
from threadpoolctl import threadpool_limits

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_distributed_surface_finite import (
    bounded_physical_compliance_screen,
)
from scripts.b3_e4_f03_local_footprint_work import graded_terminal_coupling
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


KINDS = ("piecewise_constant", "continuous_linear", "dual_linear")
HALF_CELLS = (12, 14, 18, 26)


def _save(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args()
    root = args.output_root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    source = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), text=True).strip()
    _save(root / "manifest.json", {
        "status": "development diagnostic; not formal F03 execution",
        "source": source,
        "runner": __file__,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "thread_env": {key: os.environ.get(key) for key in
                       ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                        "OMP_NUM_THREADS")},
        "geometry": "C1 35 mm Q4, shell bond x2/y4; exterior B3 cuts fixed",
        "loads": "native tip Mx=100 Nm and Fz=-1000 N, separate cases",
        "bond_half_cells": (2, 4, 8, 16),
        "native_total_half_cells": HALF_CELLS,
        "multiplier_cells": 2,
        "dense_square_row_cap": 1900,
        "native_context_lifetime_s": 120,
        "interpretation": "finite-grid signed action and loaded work; no multiplier-space selection",
    })
    with threadpool_limits(limits=1):
        try:
            for half_cells in HALF_CELLS:
                for kind in KINDS:
                    began = time.monotonic()
                    item = bounded_physical_compliance_screen(
                        hybrid=True, segmented=True, sparse_action=True,
                        line_space_kind=kind,
                        c1_beam_half_cells=half_cells,
                        reciprocal_shell_x_cells=2)[0]
                    _save(root / f"b{half_cells}-{kind}-norm.json", {
                        "elapsed_s": time.monotonic()-began,
                        "result": item,
                    })
                began = time.monotonic()
                beam = build(
                    half_cells, z_offset=.0675,
                    torsion_constant=square_torsion_constant(),
                    reference_profile="c1_tangent_2um")
                response = graded_terminal_coupling(
                    2, beam, transverse_cells=4, plate_thickness=.035,
                    include_line_hybrid_spaces=True, sparse_line_only=True,
                    force_sign=-1.)
                _save(root / f"b{half_cells}-loaded.json", {
                    "elapsed_s": time.monotonic()-began,
                    "beam_dense_oracle_max_error": beam.dense_oracle_max_error,
                    "beam_stations_m": beam.abscissae.tolist(),
                    "result": response,
                })
                print(f"completed B3-{half_cells}", flush=True)
        except BaseException as error:
            _save(root / "failure.json", {
                "completed_files": sorted(p.name for p in root.iterdir()),
                "error_type": type(error).__name__,
                "error": str(error),
            })
            raise


if __name__ == "__main__":
    main()
