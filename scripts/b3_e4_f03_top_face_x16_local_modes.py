"""Selected local gap/work recovery for the x16 four/eight top-face pair."""

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


BASE = Path("docs/agent_plans")
PREVIOUS = {
    12: (("B3_GE_E4_PL_F03_TOP_FACE_X16_FOUR_CONTROL_20260927.json",
          "B3_GE_E4_PL_F03_TOP_FACE_X16_PHYSICAL_DEV_20260927_v2.json")),
    24: (("B3_GE_E4_PL_F03_TOP_FACE_X16_B24_FOUR_20260927.json",
          "B3_GE_E4_PL_F03_TOP_FACE_X16_B24_EIGHT_20260927.json")),
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--beam-half-cells", type=int, choices=(12, 24), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    started = monotonic()
    beam = build(args.beam_half_cells, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    result = graded_terminal_coupling(
        16, beam, plate_thickness=.035, transverse_cells=4,
        top_face_intervals=(4, 8), top_face_only=True,
        recover_top_face_local=True, force_sign=-1.)
    elapsed = monotonic()-started
    if elapsed > 120.:
        raise TimeoutError("selected local recovery exceeded 120 s")
    prior_inputs = {}
    for intervals, prior_name in zip((4, 8), PREVIOUS[args.beam_half_cells]):
        path = BASE/prior_name
        prior_inputs[str(path)] = _sha(path)
        old = json.loads(path.read_text())["result"]
        family = {4: "top_face_four_intervals",
                  8: "top_face_eight_intervals"}[intervals]
        current = result["results"][family]
        old_family = old["results"][family]
        if current["constraint_rank"] != old_family["constraint_rank"]:
            raise ArithmeticError("paired top-face rank changed")
        for loading in ("tip_mx", "tip_fz"):
            present = current["cases"][loading]
            previous = old_family["cases"][loading]
            for key in ("tip_rx_rad", "tip_uz_m", "total_external_work_j",
                        "physical_shell_work_j", "interface_shell_work_j"):
                if not np.isclose(present[key], previous[key], rtol=1e-8,
                                  atol=1e-12):
                    raise ArithmeticError(f"paired local recovery changed {family} {loading} {key}")
    sources = [Path(__file__),
               Path("scripts/b3_e4_f03_local_footprint_work.py"),
               Path("scripts/b3_e4_f03_plate_patch_work.py"),
               Path("scripts/b3_e4_f03_distributed_surface_finite.py"),
               Path("scripts/_b3_e4_f03_native_fixture.py")]
    evidence = {
        "classification": "selected x16 local top-face work/gap recovery, not G0B/F03 acceptance",
        "question": "Which extra eight-interval weak modes and physical shell work are present in the nested four-interval solution?",
        "result": result,
        "prior_input_sha256": prior_inputs,
        "source_sha256": {str(path): _sha(path) for path in sources},
        "source_git": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "elapsed_s_not_benchmark": elapsed,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "threadpool_info": threadpool_info(),
        "thread_env": {key: os.environ.get(key) for key in
                       ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS",
                        "MKL_NUM_THREADS", "OMP_NUM_THREADS")},
        "limitations": ["linearized reference-chart recovery only",
                        "selected local energy is shell physical stiffness, not a weld stress",
                        "F5 lacks verified sided B3 retained-port work"],
    }
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n")
    summary = {family: {loading: {
        "gap_m8_of_solution_max":case["selected_top_face_local_recovery"]
            ["gap_on_both_spaces"]["top_face_eight_intervals"]
            ["max_abs_weak_six_gap_m_rad"],
        "gap_m4_of_solution_max":case["selected_top_face_local_recovery"]
            ["gap_on_both_spaces"]["top_face_four_intervals"]
            ["max_abs_weak_six_gap_m_rad"],
    } for loading,case in item["cases"].items()}
        for family,item in result["results"].items()}
    print(json.dumps({"elapsed_s":elapsed,"beam_half_cells":args.beam_half_cells,
                      "gap_summary":summary},sort_keys=True))


if __name__ == "__main__":
    main()
