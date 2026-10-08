"""Read-only bounded mode attribution of the native F03 signed KKT floor.

Development evidence only. This reuses the assembled signed-graph operator;
it does not change the native coupling, norm, or frozen V1 results.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

if not os.environ.get("NUMBA_CACHE_DIR"):
    raise RuntimeError("set a dedicated writable NUMBA_CACHE_DIR")

sys.path.insert(0,str(Path(__file__).resolve().parent))

import numpy as np
import scipy

from probe_b3_ge_e4_pl_g0_f03_signed_graph_v1 import measure


SOURCES = ("b3_e4_f03_signed_floor_mode_screen.py",
           "probe_b3_ge_e4_pl_g0_f03_signed_graph_v1.py",
           "probe_b3_ge_e4_pl_g0_f03_signed_norm_v1.py",
           "probe_b3_ge_e4_pl_g0_f03_shell_port_lift_v1.py")


def main() -> None:
    source_dir=Path(__file__).resolve().parent
    cases=[]
    for topology in ("Q4","S3-V2D"):
        for n in (4,8,16):
            result=measure(topology,n,n,observe_modes=True)
            cases.append({
                "topology":topology,"n_beam":n,"n_shell":n,
                "native_negative_modes":result["native_negative_modes"],
                "spaces":{
                    name:{
                        "positive_constraint_beta":space["positive_constraint_beta"],
                        "signed_kkt_min_singular":space["signed_kkt_min_singular"],
                        "signed_schur_min_eigen":space["signed_schur_min_eigen"],
                        "signed_kkt_equation_residual":
                            space["signed_kkt_equation_residual"],
                        "mode":space["lowest_mode_observation"],
                    }
                    for name,space in result["spaces"].items()},
            })
    output={
        "status":"UNREGISTERED_NATIVE_F03_SIGNED_FLOOR_MODE_DIAGNOSTIC",
        "source_revision":subprocess.check_output(
            ("git","rev-parse","HEAD"),text=True).strip(),
        "source_sha256":{
            name:hashlib.sha256((source_dir/name).read_bytes()).hexdigest()
            for name in SOURCES},
        "python":platform.python_version(),
        "numpy":np.__version__,"scipy":scipy.__version__,
        "threads":{
            name:os.environ.get(name)
            for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS",
                         "MKL_NUM_THREADS")},
        "cases":cases,
        "limitations":[
            "finite signed KKT mode observation, not an inf-sup proof",
            "single eigenvectors can rotate inside a nearby cluster",
            "raw multiplier row coefficients are not physical channel norms",
            "not a loaded physical response or formal F03 assessment",
        ],
    }
    print(json.dumps(output,indent=2,sort_keys=True,allow_nan=False))


if __name__=="__main__":
    main()
