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
- Frozen prototype/harness: `7321baff6185ebff8750d07755ed042f8aab7e34`.
  Not accepted for integration. Harness failure-safety corrections verified:
  eight tests passed in the parent; focused source/guard suite 116 passed.
- Baseline diagnostic outputs: `C:\Github\ANYsolver\.tmp_spectral_medium_fine`.
- Coarse panel buckling smoke passed with five modes and residuals around 1e-14.
- Medium panel buckling: first screen cold 9.846 s, retained 5.442 s;
  retained validation 1.263 s and geometric assembly 0.539 s. Separate cProfile
  completed; repeated lifecycle/class inspection dominates. No speedup claim.
- Fine panel timing and separate profile completed: cold 18.690 s,
  retained 11.249 s. Profile covers four analyses, unlike the successor
  harness that profiles only the final retained analysis.
- Cylinder fixture initially imported the GUI through absent optional load
  fields. The harness now supplies their existing absent-value defaults;
  production adapter/mechanics are unchanged. Coarse corrected smoke passed.
- Corrected medium-cylinder attempt `baseline-cylinder-medium-buckling-corrected-03`
  logged a native access violation during asynchronous stack dumping, then
  failed to exit. Four solve records exist but are NOT accepted evidence.
  Known worker tree 16552/36120 was terminated; coordinator session 7837
  ended failed. No `result.json` was promoted. All raw files are preserved.
  Confirm fresh process status before resuming; do not reuse this directory.
- `/root/validation_candidate` completed its conservative captured-name
  preparation and 11 regressions. No live-class authority checks were removed.
- `/root/harness_failure_safety` (requested Terra/high) completed benchmark
  script/process-control tests: no-error-dialog handling, fatal-log rejection,
  process-tree cleanup and failure tests. No solver source edits.
- No candidate performance or acceptance claims yet.
- Delegated inspection: `/root/profile_fixture_map`, requested
  `gpt-5.6-luna` / `high`; runtime model/effort not independently exposed.

## Next actions

1. Failure-safety correction is frozen at `48ecf5f`; successor effective-load
   correction passes ten harness tests. Cylinder modal diagnostic `04` was
   explicitly stopped before its first mode after several minutes; no success
   result, no retry and no fine-modal escalation. Its process tree is gone.
2. Complete cylinder and modal medium/fine baselines serially where healthy.
3. Screen candidate shared validation against baseline with identical harness.
4. Implement a narrow candidate, screen and verify; inspect complete diff and
   obtain a fresh independent read-only review before acceptance.

All raw outputs use fresh directories; no automatic retry. Parent remains
responsible for architecture, integration, profile interpretation and acceptance.
