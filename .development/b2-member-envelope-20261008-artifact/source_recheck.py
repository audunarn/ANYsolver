"""Exact-source focused recheck after line-ending cleanup."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil


here = Path(__file__).resolve().parent
root = here.parents[1]
env = os.environ.copy()
env.update({name: "1" for name in (
    "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS")})
env["NUMBA_DISABLE_JIT"] = "1"
env["TEMP"] = env["TMP"] = str(here / "tmp")
psutil.Process().cpu_affinity([0])
targets = (
    "tests/test_stiffened_shell_b2_q4_panel_experimental.py::test_point_panel_batch_reuses_factorization_and_selects_recovery",
    "tests/test_stiffened_shell_b2_q4_panel_experimental.py::test_point_panel_selected_envelopes_report_signed_extrema_and_first_case_ties",
    "tests/test_stiffened_shell_b2_q4_panel_experimental.py::test_point_panel_selected_envelopes_use_only_complete_prefix",
    "tests/test_stiffened_shell_b2_q4_panel_experimental.py::test_point_panel_selected_envelopes_are_empty_for_zero_complete_cases",
    "tests/test_stiffened_shell_b2_physical_footprint_batch.py::test_public_batch_counts_selected_outputs_and_envelopes",
    "tests/test_stiffened_shell_b2_physical_footprint_batch.py::test_no_unselected_recovery_and_first_case_tie",
    "tests/test_stiffened_shell_b2_physical_footprint_batch.py::test_public_batch_example",
    "tests/test_b2_loaded_point_owner.py::test_loaded_batch_selection_and_factor_reuse",
    "tests/test_b2_loaded_point_owner.py::test_loaded_batch_cancellation_returns_complete_case",
    "tests/test_stiffened_shell_b2_body_acceleration.py::test_body_load_batches_keep_factor_and_complete_cancelled_prefix",
)
command = [sys.executable, "-m", "pytest", "-q", *targets]
started = time.perf_counter()
peak_rss = 0
with (here / "source-recheck.stdout.log").open("wb") as stdout, (here / "source-recheck.stderr.log").open("wb") as stderr:
    process = subprocess.Popen(command, cwd=root, env=env, stdout=stdout, stderr=stderr)
    family = psutil.Process(process.pid)
    status = "COMPLETED"
    while process.poll() is None:
        try:
            peak_rss = max(peak_rss, sum(item.memory_info().rss for item in
                           [family, *family.children(recursive=True)]))
        except psutil.NoSuchProcess:
            pass
        if peak_rss > 2 * 1024 ** 3 or time.perf_counter() - started > 45:
            status = "MEMORY_LIMIT" if peak_rss > 2 * 1024 ** 3 else "TIMEOUT"
            try:
                for item in family.children(recursive=True):
                    item.kill()
                family.kill()
            except psutil.NoSuchProcess:
                pass
            break
        time.sleep(0.05)
    code = process.wait()
wall = time.perf_counter() - started
receipt = {
    "command": command, "status": status, "exit_code": code,
    "wall_seconds": wall, "cumulative_used_seconds": 29.9718892 + wall,
    "cumulative_remaining_seconds": 180 - 29.9718892 - wall,
    "process_cap_seconds": 45, "peak_sampled_tree_rss_bytes": peak_rss,
    "memory_cap_bytes": 2 * 1024 ** 3, "cpu_affinity_observed": psutil.Process().cpu_affinity(),
    "threads_requested": 1, "jit_disabled_requested": True,
    "product_sha256": hashlib.sha256((root / "src/anysolver/_stiffened_shell_b2_q4_panel_experimental.py").read_bytes()).hexdigest(),
}
(here / "source-recheck-receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
if status != "COMPLETED" or code:
    raise RuntimeError(f"source recheck: {status}, exit {code}")
print(json.dumps({"status": "PASSED", "receipt": str(here / "source-recheck-receipt.json")}))
