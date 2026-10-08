# Revision 8 current-wheel integration screen

Development verification only; this is not M1/G1 acceptance or final platform
qualification.

| Item | Exact identity |
|---|---|
| ANYsolver source | `2f3161b3cab318045465934015a974f85ed321a8` |
| ANYfem consumer source | `8c8a482301ac39662aa673a74eaf38335a3f094c` |
| ANYsolver wheel SHA-256 | `2a458326c52ec19f5a50c86b598e00252d521c956df62e429181a94e24a9cc25` |
| ANYfem wheel SHA-256 | `edc1457950fc250e5a283c47b2cf98246e21dfb59198dfc6f697c88c0336c3a8` |

Both wheels were built with the worktree Python 3.14 environment, `python -m
build --wheel --no-isolation`, installed with `pip --no-deps --no-compile
--target site`, and exercised using `PYTHONPATH=site`. `environment.json`
records the actual imported locations, dependency versions and effective
numerical pools. `NUMBA_DISABLE_JIT=1`, `OPENBLAS_NUM_THREADS=1`,
`OMP_NUM_THREADS=1` and `MKL_NUM_THREADS=1` were set for tests. Build and
installation logs are retained.

The current ANYfem test file
`tests/test_experimental_stiffened_shell_consumer.py` passed 4/4 against
the installed wheels. Its cases cover headless construction, native consumer
save/reopen, linear and finite solves, material checkpoint/restore/continue,
and invalid project data. The current solver
`tests/test_stiffened_shell_b2_experimental.py` passed 5/5 against the same
installed solver, including 1/10/100 loads, selected recovery, cancellation
and factorization reuse.

The first B2 pytest invocation failed during collection because its peer test
fixture directory was absent from `PYTHONPATH`; `installed-b2.log` preserves
that setup failure. The v2 run added that directory after the installed site
and passed. `installed-b2-v2.log` is the completed result. Neither test file
proves the complete M1/M3 mechanical domains, E01 external agreement, Linux
coverage, F01–F13 acceptance or G0–G6 completion.
