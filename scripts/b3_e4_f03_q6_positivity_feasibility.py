"""Supervised unregistered Q6 sparse-positivity resource experiment.

This uses an independent full-column certificate for the triangular factor,
then an outward-rounded residual against the original represented shell matrix.
It does not qualify a mechanical model or an installed package.
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
from scipy.sparse.linalg import splu, spsolve_triangular

from scripts._b3_e4_f03_conforming_qp_energy import E0, assemble
from scripts._b3_e4_f03_local_scientific_supervisor import (
    SupervisorLimits, frozen_thread_environment, supervise,
)
from scripts._b3_e4_f03_qp_h_contract import CASES, CASE_COUNTS, trace_for_case
from scripts._b3_e4_f03_q6_positivity_interval import (
    PositivityIntervalBudget, certify_positive,
)
from scripts._b3_e4_f03_q6_positivity_archive import write_inputs
from scripts._b3_e4_f03_sparse_certificate import SparseBudget
from scripts._b3_e4_f03_sparse_factor_candidate import _digest_owned


_SECONDS = {"X0": 900., "X1": 1200., "X2": 1800.}
_TREE_RSS_BYTES = 2*1024**3
_MAX_PATHS = 50_000_000
_MAX_PATTERN_NNZ = 50_000_000


def _write_new(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")


def child(output: Path, case_id: str, *, operators=None) -> None:
    if case_id not in CASES:
        raise ValueError("fixed Q6 grid required")
    _write_new(output / "start.json", {
        "status": "UNREGISTERED_Q6_POSITIVITY_FEASIBILITY_STARTED",
        "case_id": case_id,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_executable": sys.executable,
        "thread_environment": {name: os.environ.get(name) for name in
            ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")},
    })
    begun = perf_counter()
    expected_trace = trace_for_case(case_id)
    if operators is None:
        operators = assemble(expected_trace)
    elif (operators.trace.p != expected_trace.p or
          operators.trace.x != expected_trace.x or
          operators.trace.y != expected_trace.y or
          operators.trace.offsets != expected_trace.offsets or
          operators.trace.a != expected_trace.a or
          operators.trace.j != expected_trace.j):
        raise ValueError("shared Q6 positivity operators do not match grid")
    n = operators.dof_count
    if n != CASE_COUNTS[case_id][2]:
        raise ArithmeticError("Q6 positivity grid inventory changed")
    diagonal = (operators.shell_stiffness + operators.beam_stiffness).diagonal()
    if not np.isfinite(diagonal).all() or np.any(diagonal <= 0):
        raise ArithmeticError("Q6 positivity scaling diagonal invalid")
    d = np.sqrt(E0/diagonal)
    scaled_shell = (sparse.diags(d) @ operators.shell_stiffness @
                    sparse.diags(d) / E0).tocsr()
    scaled_shell.sum_duplicates()
    scaled_shell.eliminate_zeros()
    scaled_shell.sort_indices()
    shell_hash = _digest_owned(scaled_shell)
    working = ((scaled_shell + scaled_shell.T)*.5).tocsc()
    working.sum_duplicates()
    working.eliminate_zeros()
    working.sort_indices()
    assembly_seconds = perf_counter() - begun
    factor_start = perf_counter()
    factor = splu(working, permc_spec="MMD_AT_PLUS_A",
                  diag_pivot_thresh=0.,
                  options={"Equil": False, "SymmetricMode": True,
                           "IterRefine": "NOREFINE"})
    if not np.array_equal(factor.perm_r, factor.perm_c):
        raise ArithmeticError("Q6 positivity factor permutations differ")
    lower = sparse.csr_matrix(factor.L)
    lower.sort_indices()
    factor_diagonal = np.asarray(factor.U.diagonal(), dtype=np.float64)
    order = tuple(int(i) for i in np.argsort(factor.perm_c))
    factor_seconds = perf_counter() - factor_start
    archive = write_inputs(
        output / "positivity_inputs.npz", scaled_shell, working.tocsr(),
        lower, factor_diagonal, np.asarray(order, dtype=np.int64), d)
    inverse_path = output / "lower_inverse_float64.bin"
    with inverse_path.open("xb") as stream:
        stream.truncate(8*n*n)
    inverse = np.memmap(inverse_path, dtype="<f8", mode="r+", shape=(n, n))
    blocks_completed = 0

    def blocks():
        nonlocal blocks_completed
        for first in range(0, n, 32):
            width = min(32, n-first)
            basis = np.zeros((n, width))
            basis[first+np.arange(width), np.arange(width)] = 1.
            solved = np.asarray(spsolve_triangular(
                lower, basis, lower=True, unit_diagonal=True),
                dtype=np.float64)
            inverse[:, first:first+width] = solved
            for offset in range(0, width, 4):
                block = np.array(solved[:, offset:offset+4],
                                 dtype=np.float64, order="C", copy=True)
                blocks_completed += 1
                yield first+offset, block

    budget = PositivityIntervalBudget(
        SparseBudget(n, max(int(scaled_shell.nnz), int(lower.nnz)),
                     4, 512*1024**2),
        _MAX_PATHS, _MAX_PATTERN_NNZ)
    proof_start = perf_counter()
    proof = certify_positive(scaled_shell, lower, factor_diagonal, order,
                             blocks(), budget=budget)
    proof_seconds = perf_counter() - proof_start
    inverse.flush()
    with inverse_path.open("rb") as stream:
        inverse_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    if (inverse_path.stat().st_size != 8*n*n or
            blocks_completed != (n+3)//4 or
            proof["inverse"]["inverse_columns"] != n):
        raise ArithmeticError("incomplete Q6 positivity inverse evidence")
    _write_new(output / "measurement.json", {
        "status": "UNREGISTERED_Q6_POSITIVITY_FEASIBILITY",
        "case_id": case_id,
        "shell_order": n,
        "shell_nnz": int(scaled_shell.nnz),
        "original_scaled_shell_sha256": shell_hash,
        "rounded_symmetric_working_sha256": _digest_owned(working.tocsr()),
        "lower_sha256": _digest_owned(lower),
        "working_nnz": int(working.nnz),
        "lower_nnz": int(lower.nnz),
        "positivity_inputs_archive": archive,
        "proof_source_sha256": hashlib.sha256(
            Path(sys.modules[certify_positive.__module__].__file__).read_bytes()).hexdigest(),
        "archive_source_sha256": hashlib.sha256(
            Path(sys.modules[write_inputs.__module__].__file__).read_bytes()).hexdigest(),
        "diagonal_sha256": hashlib.sha256(
            np.asarray(factor_diagonal, dtype="<f8").tobytes()).hexdigest(),
        "permutation_sha256": hashlib.sha256(
            np.asarray(order, dtype="<i8").tobytes()).hexdigest(),
        "inverse_archive_bytes": inverse_path.stat().st_size,
        "inverse_archive_sha256": inverse_hash,
        "inverse_blocks": blocks_completed,
        "assembly_seconds": assembly_seconds,
        "factor_seconds": factor_seconds,
        "proof_seconds": proof_seconds,
        "proof": proof,
        "scientific_registration": False,
    })


def parent(output: Path, case_id: str) -> None:
    if case_id not in CASES:
        raise ValueError("fixed Q6 grid required")
    if output.exists():
        raise FileExistsError("diagnostic evidence must not be overwritten")
    output.mkdir(parents=True)
    command = [sys.executable, "-m", "scripts.b3_e4_f03_q6_positivity_feasibility",
               "--child", str(output.resolve()), "--grid", case_id]
    _write_new(output / "attempt.json", {
        "status": "UNREGISTERED_Q6_POSITIVITY_FEASIBILITY_ATTEMPT",
        "case_id": case_id,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "argv": command,
        "seconds_limit": _SECONDS[case_id],
        "tree_rss_bytes_limit": _TREE_RSS_BYTES,
        "stream_bytes_limit": 8*1024**2,
        "inverse_archive_bytes": 8*(CASE_COUNTS[case_id][2]**2),
    })
    with (output / "stdout.log").open("wb") as stdout, (
            output / "stderr.log").open("wb") as stderr:
        receipt = supervise(
            command, cwd=Path(__file__).resolve().parents[1],
            environment=frozen_thread_environment(), stdout=stdout,
            stderr=stderr,
            limits=SupervisorLimits(_SECONDS[case_id], _TREE_RSS_BYTES),
            log_byte_limit=8*1024**2)
    _write_new(output / "receipt.json", asdict(receipt))
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
