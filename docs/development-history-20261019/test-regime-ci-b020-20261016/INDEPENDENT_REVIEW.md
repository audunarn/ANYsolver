Read the patch in full (432 lines, one call). Findings below; I could not cross-check against the source files (single-file scope per the brief), so source-dependent claims are marked.

## Verdict

No outright logic bug found in the enforcement, failure-preservation, or scheduling code. Two actionable findings, both in the new thread-capacity feature, plus two minor notes. No mechanics changed: only `scripts/development_test_runtime.py`, `scripts/run_portable_ci.py`, and three test files are touched; the s3 change is assertion-only.

## Findings

**1. OpenMP pool check enforces a condition the runner never establishes (actionable).**
`runtime_record` (development_test_runtime.py, openmp branch) rejects any `user_api == "openmp"` pool with `count > requested_threads`, but `run_portable_ci.py` `environment.update` sets only `NUMBA_NUM_THREADS` / `ANYSOLVER_DEVELOPMENT_NUMBA_THREADS` — nothing sets `OMP_NUM_THREADS`. Concrete counterexample: `--threads 3` on a host with OpenMP-linked numpy/scipy (standard manylinux wheels) and more than 3 cores reports `num_threads` = core count, producing "effective OpenMP capacity exceeds the requested profile" and exit 1 on an otherwise clean run. Either the runner should set `OMP_NUM_THREADS=str(threads)` (and pin BLAS env, e.g. `OPENBLAS_NUM_THREADS=1`, to match the BLAS=1 rule) or the openmp branch false-fails for exactly the admitted compiled scopes the flag exists for. BLAS=1 enforcement itself is preserved unchanged from the prior all-pools-==1 rule.

**2. Default `threads=1` narrows Numba capacity for existing focused runs (verify).**
Previously focused runs left `NUMBA_NUM_THREADS` unset (numba defaults to core count); now the default pins it to 1. Any existing test that calls `numba.set_num_threads(k>1)` inside a focused run without passing `--threads k` now raises ValueError at the call site, where it previously succeeded. If admitted compiled scopes exist in the suite, plain `--development` invocations of them regress. I could not confirm whether such tests exist without reading suite sources.

**3. Minor: duplicated bound.** `MAX_DEVELOPMENT_THREADS = 8` in run_portable_ci.py is re-hardcoded as `1 <= threads <= 8` in `_requested_profile`; raising one without the other makes every session fail with "profile is not recorded".

**4. Minor: diagnostic marker test is weaker but low-risk.** The s3 test moves from blanket `'profile' not in message and 'checkpoint_sha256' not in message` to two exact markers (`'profile checkpoint='`, `'checkpoint_sha256 body='`). Since `pytest.raises(match='schema checkpoint=.*; identity checkpoint=')` already pins the error variant, the change is defensible, but a leak like `checkpoint_sha256=<hash>` without ` body=` would now pass. I could not verify the claimed "identity component names may include profile" against the actual error-message source.

## Confirmed intact

- **Failure preservation:** errors (including new startup errors) still force `session.exitstatus = 1` when pytest exits 0; `exit_code` records the final status; threadpool observation failures are now recorded instead of crashing sessionfinish (an improvement over the old unguarded `threadpool_info()` and the old `os.environ["NUMBA_DISABLE_JIT"]` KeyError path).
- **Active-1 restoration:** `pytest_configure` snapshots pre-init state, sets `set_num_threads(1)` while retaining `NUMBA_NUM_THREADS` capacity, and sessionfinish requires active == 1; the real-subprocess leaked-scope test exercises this end to end.
- **Scheduling integrity:** the eight new entries are weight overrides only — no module list, timeout, or test content changes; the e4 test now derives the heaviest set from `_module_weight` dynamically, so it stays consistent as weights evolve.
- **Bounded profile:** `--threads` validated as int in [1, 8], bool rejected, matrix mode rejects the option; selection.json records it.

Finding 1 is the one I would act on before merging; finding 2 needs a one-time grep for `set_num_threads` in the suite to confirm or dismiss.
