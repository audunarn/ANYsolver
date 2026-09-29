# Development execution

Worktree: `C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling`.

Source: `PYTHONPATH=src;tests NUMBA_DISABLE_JIT=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest tests/test_stiffened_shell_ge_owned_rebase.py tests/test_stiffened_shell_ge_experimental.py -q` -> 33 passed.

Earlier impact suite: finite owner + S3 algorithmic pullback -> 28 passed, before final chart-only corrections. Individual failed and repaired direct screens are retained, not substituted for acceptance.

Exact build commands/fixture closure: `r8-owned-rebase-build.py`, wheel/install logs. Build uses an isolated source copy with unchanged version, no dependency resolution or build isolation.

Installed execution: `python -u run_bounded.py` in the isolated artifact directory. Runner pins its actual site, validates all loaded ANYsolver modules, BLAS threads and JIT setting. Execution enforces 600 s / 8 GiB process-tree. See `execution.json`; no performance gain is claimed.

Resolved elastic central differences use two physical Newton-direction levels (h=0.5,0.2) at unchanged 1e-6 tolerance. Smaller-parameter baseline/anchor floors are retained in the plateau logs. This is focused development evidence, not a formal F06/F03 authority invocation.
