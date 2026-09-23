"""Unregistered full X0 inverse-column certificate feasibility experiment.

This is a supervised diagnostic, not an F03 scientific registration or pass.
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
from scripts._b3_e4_f03_qp_h_contract import minimum_inverse_bytes, trace_for_case
from scripts._b3_e4_f03_sparse_certificate import SparseBudget, certificate_a


def child(output: Path) -> None:
    (output / "start.json").write_text(json.dumps({
        "status": "UNREGISTERED_X0_CERTIFICATE_FEASIBILITY_STARTED",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_executable": sys.executable,
        "thread_environment": {name: os.environ.get(name) for name in
            ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")},
    }, indent=2) + "\n", encoding="utf-8")
    start = perf_counter()
    operators = assemble(trace_for_case("X0"))
    assembly_s = perf_counter() - start
    stiffness = operators.shell_stiffness + operators.beam_stiffness
    diagonal = stiffness.diagonal()
    if not np.isfinite(diagonal).all() or np.any(diagonal <= 0):
        raise ArithmeticError("nonpositive X0 KKT diagonal")
    d = np.sqrt(E0/diagonal)
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
    matrix.sort_indices()
    order = matrix.shape[0]
    if order != 3289 or matrix.nnz != 1200496:
        raise ArithmeticError("X0 KKT inventory changed since cost screen")
    matrix_s = perf_counter() - start - assembly_s
    factor_start = perf_counter()
    factor = splu(matrix, permc_spec="COLAMD", diag_pivot_thresh=1.,
                  options={"Equil": False, "IterRefine": "NOREFINE"})
    rhs = np.r_[d*operators.load/E0, np.zeros(3)]
    state = factor.solve(rhs)
    factor_s = perf_counter() - factor_start
    inverse_path = output / "inverse_float64.bin"
    inverse = np.memmap(inverse_path, dtype="<f8", mode="w+",
                        shape=(order, order))
    blocks_completed = 0

    def blocks():
        nonlocal blocks_completed
        for first in range(0, order, 4):
            width = min(4, order-first)
            basis = np.zeros((order, width))
            basis[first+np.arange(width), np.arange(width)] = 1.
            block = np.asarray(factor.solve(basis), dtype=np.float64)
            inverse[:, first:first+width] = block
            blocks_completed += 1
            yield first, block

    budget = SparseBudget(order, int(matrix.nnz), 4, 256*1024**2)
    cert_start = perf_counter()
    certificate = certificate_a(matrix, blocks(), budget, b=rhs, z=state,
                                interval_kernel="compiled_experimental")
    certificate_s = perf_counter() - cert_start
    inverse.flush()
    if inverse_path.stat().st_size != minimum_inverse_bytes("X0"):
        raise ArithmeticError("incomplete X0 raw inverse archive")
    with inverse_path.open("rb") as stream:
        inverse_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    if blocks_completed != (order+3)//4 or certificate["inverse_columns"] != order:
        raise ArithmeticError("incomplete X0 inverse stream")
    result = {
        "status": "UNREGISTERED_X0_FULL_CERTIFICATE_FEASIBILITY",
        "kkt_order": order,
        "kkt_nnz": int(matrix.nnz),
        "factor_l_nnz": int(factor.L.nnz),
        "factor_u_nnz": int(factor.U.nnz),
        "assembly_seconds": assembly_s,
        "matrix_preparation_seconds": matrix_s,
        "factor_and_rhs_seconds": factor_s,
        "certificate_seconds": certificate_s,
        "inverse_archive_bytes": inverse_path.stat().st_size,
        "inverse_archive_sha256": inverse_hash,
        "certificate": certificate,
        "scientific_registration": False,
    }
    (output / "measurement.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")


def parent(output: Path) -> None:
    if output.exists():
        raise FileExistsError("diagnostic evidence must not be overwritten")
    output.mkdir(parents=True)
    workdir = Path(__file__).resolve().parents[1]
    with (output / "stdout.log").open("wb") as stdout, (
            output / "stderr.log").open("wb") as stderr:
        receipt = supervise(
            [sys.executable, "-m", "scripts.b3_e4_f03_q6_x0_full_certificate_feasibility",
             "--child", str(output.resolve())],
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
    args = parser.parse_args()
    if (args.child is None) == (args.output is None):
        parser.error("select exactly one child or supervised output")
    if args.child is not None:
        child(args.child)
    else:
        parent(args.output)


if __name__ == "__main__":
    main()
