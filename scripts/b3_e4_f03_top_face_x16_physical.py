"""Bounded third-level top-face transfer check; not formal F03 execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
from time import monotonic

import numpy as np
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_local_footprint_work import graded_terminal_coupling
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--intervals", type=int, choices=(4, 8), default=8)
    parser.add_argument("--beam-half-cells", type=int, choices=(12, 24), default=12)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    start = monotonic()
    beam = build(args.beam_half_cells, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    result = graded_terminal_coupling(
        16, beam, plate_thickness=.035, transverse_cells=4,
        top_face_intervals=args.intervals, top_face_only=True, force_sign=-1.)
    if monotonic()-start > 120.:
        raise TimeoutError("bounded x16 top-face physical check exceeded 120 s")
    family_name = {4: "top_face_four_intervals",
                   8: "top_face_eight_intervals"}[args.intervals]
    family = result["results"][family_name]
    reference = result["top_face_reference"][family_name]
    expected_rank = 6*args.intervals
    if (family["constraint_rank"] != expected_rank or
            reference["max_reference_gap_m_rad"] > 1e-12):
        raise ArithmeticError("x16 top-face rank or reference closure failed")
    if (family["scaled_row_inventory"]["whole"]
            ["rank_at_relative_1e_minus_10"] != expected_rank):
        raise ArithmeticError("x16 norm-scaled row rank failed")
    if any(float(case["mechanics_error"]) > 1e-8 for case in family["cases"].values()):
        raise ArithmeticError("x16 top-face mechanics balance failed")
    if family["cases"]["tip_fz"]["tip_uz_m"] >= 0.:
        raise ArithmeticError("x16 top-face opening load sign changed")
    sources = [Path(__file__),
               Path("scripts/b3_e4_f03_local_footprint_work.py"),
               Path("scripts/b3_e4_f03_distributed_surface_finite.py"),
               Path("scripts/_b3_e4_f03_native_fixture.py")]
    evidence = {
        "classification": "bounded x16 top-face physical transfer diagnostic, not G0B/F03 acceptance",
        "question": ("At fixed x16 shell, does B3-12 to B3-24 trace refinement change the four-to-eight row effect?"
                     if args.beam_half_cells == 24 else
                     "At fixed x16 shell, does four-to-eight line-row growth or shell refinement explain the remaining torque/shear transfer change?"
                     if args.intervals == 4 else
                     "With two Q4 hosts per multiplier interval, does top-face torque/shear transfer settle across the existing x4/two and x8/four levels?"),
        "result": result,
        "elapsed_s_not_benchmark": monotonic()-start,
        "source_git": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sources},
        "python": platform.python_version(),
        "numpy": np.__version__,
        "threadpool_info": threadpool_info(),
        "thread_env": {key: os.environ.get(key) for key in
                       ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS",
                        "MKL_NUM_THREADS", "OMP_NUM_THREADS")},
        "limitations": ["coupled shell/row refinement does not isolate their effects",
                        "one B3-12 beam resolution; no ratio-uniform or physical-reference conclusion",
                        "an algebraic row inventory is not an interface inf-sup constant"],
    }
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"elapsed_s": evidence["elapsed_s_not_benchmark"],
                      "rank": family["constraint_rank"],
                      "max_reference_gap": reference["max_reference_gap_m_rad"],
                      "case_inventory": list(family["cases"])}))


if __name__ == "__main__":
    main()
