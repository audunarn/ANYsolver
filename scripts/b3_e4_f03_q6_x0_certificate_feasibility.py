"""Unregistered bounded Q6 certificate-cost diagnostic; never qualifies F03.

One supervised child assembles one fixed Q6 grid, factors its scaled KKT
matrix, and compares three sampled four-column interval products. It does not
compute or claim the required full inverse-column certificate.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from scripts._b3_e4_f03_conforming_qp_energy import assemble, E0, U0, YAW_LENGTH
from scripts._b3_e4_f03_local_scientific_supervisor import (
    SupervisorLimits, frozen_thread_environment, supervise,
)
from scripts._b3_e4_f03_qp_h_contract import CASES, CASE_COUNTS, minimum_inverse_bytes, trace_for_case
from scripts._b3_e4_f03_q6_interval_kernel import compiled_product_bounds
from scripts._b3_e4_f03_sparse_certificate import _product_bounds


def child(output: Path, case_id: str) -> None:
    if case_id not in CASES:
        raise ValueError("fixed Q6 grid required")
    start = perf_counter()
    trace = trace_for_case(case_id)
    operators = assemble(trace)
    assembly_s = perf_counter() - start
    stiffness = operators.shell_stiffness + operators.beam_stiffness
    diagonal = stiffness.diagonal()
    if not np.isfinite(diagonal).all() or np.any(diagonal <= 0):
        raise ArithmeticError("nonpositive Q6 KKT diagonal")
    d = np.sqrt(E0 / diagonal)
    scaled_stiffness = sparse.diags(d) @ stiffness @ sparse.diags(d) / E0
    root_scale = np.diag((1/U0, 1/U0, YAW_LENGTH/U0))
    scaled_root = root_scale @ operators.root_constraint @ np.diag(d)
    matrix = sparse.bmat(
        ((scaled_stiffness, sparse.csr_matrix(scaled_root.T)),
         (sparse.csr_matrix(scaled_root), sparse.csr_matrix((3, 3)))),
        format="csc",
    )
    matrix.sum_duplicates()
    matrix.eliminate_zeros()
    order = matrix.shape[0]
    if order != CASE_COUNTS[case_id][2]+3 or matrix.nnz <= 0:
        raise ArithmeticError("unexpected Q6 KKT inventory")
    preparation_s = perf_counter() - start - assembly_s
    start_factor = perf_counter()
    factor = splu(matrix, permc_spec="COLAMD", diag_pivot_thresh=1.,
                  options={"Equil": False, "IterRefine": "NOREFINE"})
    factor_s = perf_counter() - start_factor
    csr = matrix.tocsr()
    samples = []
    for first in sorted({0, (order//2//4)*4, ((order-1)//4)*4}):
        width = min(4, order-first)
        basis = np.zeros((order, width))
        basis[first+np.arange(width), np.arange(width)] = 1.
        started = perf_counter()
        block = factor.solve(basis)
        inverse_block_s = perf_counter() - started
        started = perf_counter()
        low, high = _product_bounds(csr, block)
        interval_product_s = perf_counter() - started
        started = perf_counter()
        compiled_low, compiled_high = compiled_product_bounds(csr, block)
        compiled_product_s = perf_counter() - started
        matching_bits = (
            np.array_equal(low.view(np.uint64), compiled_low.view(np.uint64)) and
            np.array_equal(high.view(np.uint64), compiled_high.view(np.uint64)))
        if not matching_bits or not all(np.isfinite(part).all() for part in
                                        (block, low, high)):
            raise ArithmeticError("nonfinite or mismatched interval sample")
        samples.append({
            "first_column": first,
            "width": width,
            "inverse_block_seconds": inverse_block_s,
            "scalar_interval_seconds": interval_product_s,
            "compiled_interval_including_jit_seconds": compiled_product_s,
            "interval_bounds_bitwise_equal": matching_bits,
            "block_max_residual": float(np.max(np.abs(matrix @ block - basis))),
        })
    result = {
        "status": "UNREGISTERED_Q6_CERTIFICATE_COST_DIAGNOSTIC",
        "case_id": case_id,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_executable": sys.executable,
        "thread_environment": {name: os.environ.get(name) for name in
            ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")},
        "kkt_order": order,
        "kkt_nnz": int(matrix.nnz),
        "inverse_float64_minimum_bytes": minimum_inverse_bytes(case_id),
        "four_column_blocks": (order + 3)//4,
        "required_interval_entry_visits": int(matrix.nnz*((order + 3)//4)),
        "factor_l_nnz": int(factor.L.nnz),
        "factor_u_nnz": int(factor.U.nnz),
        "assembly_seconds": assembly_s,
        "kkt_preparation_seconds": preparation_s,
        "factorization_seconds": factor_s,
        "sampled_blocks": samples,
        "complete_inverse_certificate": False,
    }
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")


def parent(output: Path, case_id: str) -> None:
    if case_id not in CASES:
        raise ValueError("fixed Q6 grid required")
    if output.exists():
        raise FileExistsError("diagnostic evidence must not be overwritten")
    output.mkdir(parents=True)
    workdir = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "scripts.b3_e4_f03_q6_x0_certificate_feasibility",
               "--child", str((output / "measurement.json").resolve()), "--grid", case_id]
    with (output / "attempt.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "status": "UNREGISTERED_Q6_COST_ATTEMPT",
            "case_id": case_id,
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "argv": command,
            "seconds_limit": 900.,
            "tree_rss_bytes_limit": 2*1024**3,
            "stream_bytes_limit": 8*1024**2,
        }, indent=2) + "\n")
    stdout_path, stderr_path = output / "stdout.log", output / "stderr.log"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        receipt = supervise(
            command,
            cwd=workdir, environment=frozen_thread_environment(),
            stdout=stdout, stderr=stderr,
            limits=SupervisorLimits(900., 2*1024**3),
            log_byte_limit=8*1024**2,
        )
    (output / "receipt.json").write_text(
        json.dumps(asdict(receipt), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt_reason": receipt.reason,
                      "exit_code": receipt.exit_code,
                      "peak_tree_rss_bytes": receipt.sampled_peak_tree_rss_bytes,
                      "measurement_exists": (output / "measurement.json").exists()}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--grid", choices=CASES, required=True)
    args = parser.parse_args()
    if (args.child is None) == (args.output is None):
        parser.error("select exactly one child or supervised output")
    if args.child is not None:
        child(args.child, args.grid)
    else:
        parent(args.output, args.grid)


if __name__ == "__main__":
    main()
