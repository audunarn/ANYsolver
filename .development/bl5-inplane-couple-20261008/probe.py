"""One source-development BL5 in-plane-couple discriminator; not qualification."""

import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

import psutil

process = psutil.Process()
process.cpu_affinity([0])
if process.cpu_affinity() != [0]:
    raise RuntimeError("effective CPU affinity differs")

import numba
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as api
from test_stiffened_shell_l1_assembly_experimental import _bl5_nonmatching_definition

if numba.config.DISABLE_JIT != 1 or numba.config.NUMBA_NUM_THREADS != 1 or numba.get_num_threads() != 1:
    raise RuntimeError("effective Numba/JIT settings differ")
pools = threadpool_info()
if not pools or any(pool["num_threads"] != 1 for pool in pools):
    raise RuntimeError("effective numerical pool setting differs")

definition = _bl5_nonmatching_definition(3, 1)
owner = api.create_analysis(definition=definition)
try:
    action = (api.NodalAction("beam", 105, (0., 0., 0., 0., 0., 1.)),)
    result = owner.solve_linear(action)
    shell_count = owner._shell_count
    q = np.r_[result.shell_displacement, result.beam_coordinates]
    interface = np.asarray(owner._C.T @ result.multipliers).reshape(-1)
    shell_interface = interface[:shell_count].reshape(-1, 6)
    shell_reactions = np.asarray(result.reactions[:shell_count]).reshape(-1, 6)
    shell_positions = np.asarray(definition.shell.coordinates_m, dtype=float)
    root_force = shell_reactions[:, :3].sum(axis=0)
    root_moment = (shell_reactions[:, 3:].sum(axis=0) +
                   np.cross(shell_positions, shell_reactions[:, :3]).sum(axis=0))
    interface_force = shell_interface[:, :3].sum(axis=0)
    interface_moment = (shell_interface[:, 3:].sum(axis=0) +
                        np.cross(shell_positions, shell_interface[:, :3]).sum(axis=0))
    output = {
        "scope": "BL5 pure in-plane tip moment, source development only",
        "qualified": False,
        "status": result.status,
        "equilibrium": float(result.free_equilibrium_ratio),
        "constraint": float(result.constraint_max),
        "root_force": root_force.tolist(),
        "root_moment_about_origin": root_moment.tolist(),
        "shell_interface_force": interface_force.tolist(),
        "shell_interface_moment_about_origin": interface_moment.tolist(),
        "max_shell_interface_covector": float(np.max(np.abs(shell_interface))),
        "external_work_at_final_load": float(owner._accepted[1] @ q),
        "matrix_dimension": int(owner._A.shape[0]),
        "matrix_nnz": int(owner._A.nnz),
        "line_samples": len(owner._line_samples),
        "multiplier_rows": int(owner._C.shape[0]),
        "cpu_affinity": process.cpu_affinity(),
        "numba_disable_jit": int(numba.config.DISABLE_JIT),
        "numba_threads": int(numba.get_num_threads()),
        "threadpools": pools,
        "children_after": [child.pid for child in process.children(recursive=True)],
        "fixture_sha256": hashlib.sha256((ROOT / "tests/test_stiffened_shell_l1_assembly_experimental.py").read_bytes()).hexdigest(),
    }
    if output["children_after"]:
        raise RuntimeError("unexpected numerical child process")
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: output[key] for key in (
        "status", "equilibrium", "constraint", "root_force",
        "root_moment_about_origin", "shell_interface_moment_about_origin",
        "max_shell_interface_covector", "external_work_at_final_load",
        "matrix_dimension", "matrix_nnz")}))
finally:
    owner.close()
