# Restart checkpoint

User instruction: `stop` means usage is too high. Stop dispatch, safely end
task-owned runs, retain logs and source edits, and report a restartable state.
Never interrupt unrelated processes or discard partial evidence.

## Current state

- Solver branch: `codex/spectral-medium-fine-gate`.
- Worktree: `C:\Github\ANYsolver\.perf2-worktrees\spectral-medium-fine-gate`.
- Baseline: `5883ae1d7ad1b5abea3a660cc8feecc7e65c7154`.
- Clean adapter: `C:\Github\ANYsolver\.perf2-worktrees\anystructure-medium-fine-profile`.
- Adapter baseline: integrated ANYstructure `a377448dc235463b624226dd230f2fdb849acdd0`.
- Active ANYstructure checkout is an older release branch with an unrelated
  IDE edit; it is not a benchmark input and remains untouched.
- Interpreter: `C:\Github\ANYsolver\.venv\Scripts\python.exe` (3.13.9).
- Available numerical stack: NumPy 2.4.3, SciPy 1.16.3, Numba 0.65.0,
  psutil 7.2.2. Bind actual imported paths explicitly in benchmark children.
- Gate definition: `docs/SPECTRAL_MEDIUM_FINE_GATE.md`.
- Harness implemented in `scripts/benchmark_spectral_medium_fine.py`; five
  process-control/parser tests passed after parent corrections. Not yet accepted.
- Baseline diagnostic outputs: `C:\Github\ANYsolver\.tmp_spectral_medium_fine`.
- Coarse panel buckling smoke passed with five modes and residuals around 1e-14.
- Medium panel buckling: first screen cold 9.846 s, retained 5.442 s;
  retained validation 1.263 s and geometric assembly 0.539 s. Separate cProfile
  completed; repeated lifecycle/class inspection dominates. No speedup claim.
- Fine panel timing completed: cold 18.690 s, retained 11.249 s; separate
  cProfile still running at this checkpoint. Task terminal session 77088 owns
  the coordinator; inspect process/checkpoint before resuming or terminating.
- Only baseline solver source is used by active fine profiling (root checkout).
- `/root/validation_candidate` (requested Sol/high) owns only
  `current_state_tangent.py` and `tests/test_spectral_validation_preparation.py`.
  It is implementing conservative shared validation preparation; do not overlap.
- No candidate performance or acceptance claims yet.
- Delegated inspection: `/root/profile_fixture_map`, requested
  `gpt-5.6-luna` / `high`; runtime model/effort not independently exposed.

## Next actions

1. Finish active fine profile; preserve completed raw records.
2. Complete cylinder and modal medium/fine baselines serially.
3. Finish candidate shared-validation work and compare under the same harness.
4. Implement a narrow candidate, screen and verify; inspect complete diff and
   obtain a fresh independent read-only review before acceptance.

All raw outputs use fresh directories; no automatic retry. Parent remains
responsible for architecture, integration, profile interpretation and acceptance.
