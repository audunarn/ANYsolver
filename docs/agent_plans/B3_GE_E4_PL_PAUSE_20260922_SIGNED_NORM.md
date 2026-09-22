# User-requested pause: signed norm batch

22 September 2026. User paused the plan for intermittent actions and intends
to resume later. No new implementation, tests, scientific runs or review
dispatches are authorized during this pause. Resume only on user instruction.

Worktree: `C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling`.
Branch: `codex/b3-ge-e4-pl-integration`.
Last verified committed HEAD: `4af18aba6ed6e1bb882950305f264d4980b302f3`.
Last completed source batch: `5acfd119b576237db4b104d4e56c1e4af93ebb81`,
27 distinct tests and independent review, documented in
`B3_GE_E4_PL_G0_F03_SAVED_RECOVERY_COMPONENT_PROOFS_V1_RESULTS.md`.
G0B remains open; G1 is barred. The complete B3-GE/E4-PL programme including
B2 remains the goal. Main was last observed clean at `be41a77a`; not refreshed
or audited as part of pausing. No release or scientific execution occurred.

## Uncommitted current work

Parent owns these new files:

- `scripts/_b3_e4_f03_saved_norm_checks.py`
- `tests/test_b3_e4_f03_saved_norm_checks.py`
- `docs/agent_plans/B3_GE_E4_PL_G0_F03_SAVED_NORM_CHECKS.md`

Worker `/root/f03_port_mechanics` owns the in-progress extraction in
`scripts/_b3_e4_f03_local_functional.py`, plus planned/new
`tests/test_b3_e4_f03_norm_observation.py` and
`docs/agent_plans/B3_GE_E4_PL_G0_F03_NORM_OBSERVATION.md`.
The worker was sent the pause instruction and interrupted. Its last actual
file/process state has not been re-audited; verify it narrowly on resume.
Do not overwrite its edits or restart any possibly consumed run.
Independent reviewer `/root/finite_pad_axis_review` finished its current
read-only response; no final GO was granted for this batch.

## Executed tests and open correctness work

Parent raw logs under `C:/Users/AUDUNA~1/AppData/Local/Temp/`:

- `f03-saved-norm-isolated-18cbe3d2aa8342b997e11c8c99b4d40c.log`:
  14 passed, 1 deselected, exit0; injected observations only.
- `f03-saved-norm-metadata-8aee6a63073141588934c878356aeb63.log`:
  2 passed, 15 deselected, exit0; finite-component/raw-schema guards.
- `f03-saved-norm-zero-red-bc16d97894994cc48d7c6028e6e34357.log`:
  **2 failed, 17 deselected, exit1**. Exact-zero channels and totals can still
  accept fabricated positive observations. These red regressions are the
  immediate resume point; the fix was not applied before pause.

All parent test processes above completed. No parent tool/test process is
pending. Worker process handles, if any, must be obtained from its preserved
context and verified; absence of a reported handle is not proof of termination.

Already applied: immutable saved snapshots, finite contribution requirement,
strict boolean raw flags and interval identity validation. Remaining:

1. Require measured zero exactly for each exact-zero physical channel and
   nonzero for nonzero channels; exact-zero functional must have zero total.
2. Require the raw total to agree with the declared legacy `math.fsum` of
   finite channels; handle only known sum overflow as unavailable/rejected,
   preserving finite peers. Do not broadly catch programming errors.
3. Finish/review the worker's raw observer and strict historical wrapper
   parity under `B3_GE_E4_PL_G0_F03_NORM_OBSERVATION_NEXT_CONTRACT.md`.
4. Run the real observer/saved-verifier connection (currently unexecuted),
   affected tests and independent final review, then freeze new evidence.

Agreed raw observer API: legacy contribution keys directly, plus
channel_finite/channel_nonnegative/channel_nonzero_valid, total_finite,
total_nonnegative, admissible and failures. Missing numeric positions use
None. Failure records have stage/reason/channel. Geometry/input errors remain
distinct; successful strict-wrapper dictionaries must retain bitwise parity.

Do not mark the current batch accepted, commit it as qualified, amend older
sealed roots, or claim that injected-observation tests qualify physical norms.
The full recovery composition and scientific protocol remain later work.
