"""Development-only loaded C1 line quadrature attribution control."""

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
from scripts.b3_e4_f03_local_footprint_work import graded_terminal_coupling
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def save(path: Path, record: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args()
    root = args.output_root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    source = subprocess.check_output(("git", "rev-parse", "HEAD"),
                                     text=True).strip()
    save(root / "manifest.json", {
        "status": "development attribution, not F03 acceptance",
        "source": source,
        "runner": __file__,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "thread_env": {key: os.environ.get(key) for key in
                       ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                        "OMP_NUM_THREADS")},
        "comparison": "same C1 Q4 x2/y4, B3 bond 2/16 halfcells, 3x3 versus 5x5 line quadrature",
        "load_cases": "tip Mx=100 Nm, tip Fz=-1000 N, separately",
        "context_lifetime_s": 120,
        "dense_square_row_cap": 1900,
    })
    with threadpool_limits(limits=1):
        try:
            for half_cells in (12, 26):
                for order in (3, 5):
                    began = time.monotonic()
                    beam = build(
                        half_cells, z_offset=.0675,
                        torsion_constant=square_torsion_constant(),
                        reference_profile="c1_tangent_2um")
                    result = graded_terminal_coupling(
                        2, beam, transverse_cells=4, plate_thickness=.035,
                        include_line_hybrid_spaces=True, sparse_line_only=True,
                        line_quadrature_order=order, force_sign=-1.)
                    save(root / f"b{half_cells}-q{order}-loaded.json", {
                        "elapsed_s": time.monotonic()-began,
                        "beam_dense_oracle_max_error":
                            beam.dense_oracle_max_error,
                        "result": result,
                    })
                    print(f"completed B3-{half_cells} Q{order}", flush=True)
        except BaseException as error:
            save(root / "failure.json", {
                "completed_files": sorted(p.name for p in root.iterdir()),
                "error_type": type(error).__name__,
                "error": str(error),
            })
            raise


if __name__ == "__main__":
    main()
