# Slice 3 implementation checkpoint

Written by the Mistral implementation owner. Living checkpoint. Policy
ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1 rev 2026-09-24.2.
Assignment: SLICE3_FINAL_REPAIR.md (same owner, MaxTurns80, early checkpoint
by turn12, final15 reserved). Prior assignment record preserved at
`checkpoint-prior-unblock-delivery.md`.

## FINAL HANDOFF — implemented, focused verification passed; full-target
## integrated checks unmet (root runs them)

State label: **implemented and verified against the assigned focused
criteria** (typed domain refusal, trial backtracking, classified
no-improvement failure, preserved committed state, EP half acceptance
compatibility). The full-target direct/interp -0.20 integrated checks were
NOT run within this assignment's remaining budget and remain unmet gates
for Astra's final integrated verification.

### Budget ledger (exact)

- Ledger at assignment start: 2030.6258823000244 s of the 3600 s original
  allowance; active owner allocation 220 additional process-wall seconds;
  absolute process-wall ceiling 2250.6258823000244 s
  (product_execution_ceiling.json). 900 s final reserve untouched.
- Charged this assignment (all through harness.py, one child at a time):
  1. `dc-final-repair-probe-direct-1` TIMEOUT 120.335 s (diagnostic, cap 120)
  2. `slice3-final-repair-focused-1` EXIT_1 12.314 s (1 failed, 8 passed)
  3. `slice3-final-repair-focused-2` EXIT 10.118 s (9 passed)
  4. `slice3-final-repair-ep-half-1` EXIT 27.286 s (2 passed)
- Total charged this assignment: 170.053 s. Final ledger 2200.6850848000613 s
  (budget.json, 51 attempts); 49.94 s of the 220 s allocation unspent, not
  renewed or transferred. No --allow-reserve, no Git mutations, no workers,
  no sibling edits, no configuration changes.

### Diagnosis (current measurements, evidence retained)

1. Direct full -0.20 stop (dc-final-repair-probe-direct-1, partial stdout
   preserved after the 120 s timeout): the CURRENT source falls into an
   exact period-3 Newton limit cycle at a control-satisfied state —
   reduced residual 1058.09 -> 102.49 -> 76.53 -> 1058.09 repeating to 13
   significant digits, lam oscillating, constraint exactly 0. At the
   76.53 state the residual line search runs all 8 halvings with no
   improving alpha and the existing fallback commits the full Newton step
   anyway, re-entering the cycle. This is the globalization defect; it is
   not evidence of physical collapse (no fold/collapse claim is made).
   The run also shows why the fallback must survive elsewhere: from an
   unloaded state (residual 0, constraint = span) no alpha can ever pass
   the merit test because the constraint term dominates, and committing
   the full step there is what lets the first control increment converge.
2. Interp full -0.20 abort (supervisor-domain-dc-full-1 traceback, current):
   `full_u(q_trial)` inside the residual line search raises the principal
   chart ValueError when an overshooting trial pushes master rotations
   beyond the supported chart; the bare ValueError aborts the whole solve
   from an otherwise valid committed state.

### Repair (equations/reason)

- `corotational.py`: new `SO3MeanDomainError(ValueError)`; the seven
  domain guards of `_so3_weighted_mean` (input principal chart, ambiguous
  two-master geodesic, pi/4 anchor-ball admission/non-convergence/escape,
  mean chart boundary, singular B) raise it. Input-contract violations
  (finite, nonnegative, partition weights) remain plain ValueError. No
  physics, chart, tolerance or admission change; ValueError compatibility
  retained (existing `pytest.raises(ValueError)` tests still pass).
- `nonlinear_static.py` `_solve_static_displacement_control`:
  - Line-search trials: `SO3MeanDomainError` from `full_u(q_trial)` is
    caught as trial inadmissibility — the trial is skipped (`continue`),
    never assembled, never committed, so no constitutive mutation occurs
    on refused trials; the search backtracks to smaller alpha.
  - Classified no-improvement failure: when no trial passed the sufficient
    decrease test and the residual term dominates the augmented merit
    (`residual_norm * target_scale >= constraint_error * reference`,
    i.e. res/(tol*ref) >= constraint/(tol*scale) — equilibrium
    correction rather than control move), the full step is NOT committed;
    `failure_reason = "line_search_no_improvement"` breaks the attempt,
    the existing rollback restores the committed state and bounded
    subdivision (max 8 cutbacks, min span) retries. This cuts the
    measured period-3 cycle at its entry. When the constraint term
    dominates (control move from an equilibrated/unloaded state), the
    full-step fallback is kept unchanged.
  - Commit guard: if the step endpoint was never verified admissible
    (line search skipped or its alpha=1 trial refused),
    `full_u(q + delta)` is evaluated before committing; a refusal sets
    `failure_reason = "trial_state_domain_refused"`, rolls back and
    classifies instead of aborting at the next iteration top.
  - Both new reasons are subdivision-eligible like
    `maximum_iterations_reached`; when subdivision is exhausted the
    specific classified reason is kept (no rename), status stays
    `stopped_at_limit`/`diverged` and public `converged` semantics are
    unchanged.
- `tests/test_nonlinear_beam_shell_slice3.py`: three focused regressions
  (typed refusal; interp trial-domain refusal via an inflated augmented
  step reproducing the abort mechanism on a small fixture — must
  backtrack/classify, preserve zero displacements, bounded cutbacks;
  fixed irreducible reduced residual — must classify
  `line_search_no_improvement` with rollback, not cycle). A first test
  design using a growing force perturbation was wrong (the Newton step
  linearly tracks it through the load-factor channel) and was replaced by
  the fixed-residual design before verification.

### Changed files (SHA-256 prefixes, candidate-identities/after-final-repair)

- `src/anysolver/corotational.py` e83976dd855f8e56 (was 74cae9c362ec73a0)
- `src/anysolver/nonlinear_static.py` 789fd3e991d11e83 (was d9968dbcd7cb2812)
- `tests/test_nonlinear_beam_shell_slice3.py` 76faacea7f6a9168
- Task artifacts: `diagnostics/dc_final_repair_probe.py` (new),
  `apply_final_repair.py` (one-shot patcher, anchors exhausted),
  `checkpoint-prior-unblock-delivery.md` (preserved prior record).
- Candidate identity (756 source/selected inputs):
  `4432d4dd09fd1667354ef51aef68e27fb35e045868946feb648bc33bc2c5360b`.
- `tests/test_corotational_work_conjugate.py` unchanged (b5ca8d2ccb65e230).
  `tests/test_nonlinear_beam_shell_coupling.py` remains at its
  sixth-run objectivity state (acd63dff89934d01, unchanged this run);
  final identity must not claim it unchanged vs the original backup.
- All other dirty work, backups, failed evidence and root assessment
  tools untouched. Astra's zero-span list/tuple assertion fix preserved.

### Exact commands and actual results

- `.venv/Scripts/python.exe .development/nonlinear-master-slave-coupling-20261017/harness.py
  --name dc-final-repair-probe-direct-1 --timeout 120 --cwd C:/Github/ANYsolver --
  .venv/Scripts/python.exe .development/.../diagnostics/dc_final_repair_probe.py direct`
  -> TIMEOUT 120.335 s; partial per-iteration JSON stdout retained
  (evidence/dc-final-repair-probe-direct-1/stdout.txt); diagnosis above.
- `... harness.py --name slice3-final-repair-focused-1 --timeout 60 --
  python -m pytest tests/test_nonlinear_beam_shell_slice3.py -q -k
  "so3_mean_domain_refusal or trial_domain_refusal or no_improvement or
  zero_span or intrinsic_mean" --tb=short` -> EXIT_1 12.314 s,
  8 passed / 1 failed (the no-improvement test, then redesigned).
- Same selection, `--name slice3-final-repair-focused-2` -> EXIT 10.118 s,
  **9 passed, 17 deselected** (typed refusal, trial-domain backtracking,
  no-improvement classification, zero-span, both intrinsic-mean tests).
- `... harness.py --name slice3-final-repair-ep-half-1 --timeout 60 --
  python -m pytest tests/test_nonlinear_beam_shell_slice3_continuation.py
  -q -k "half" --tb=short` -> EXIT 27.286 s, **2 passed, 9 deselected**:
  the EP half direct+interp acceptance at -0.10 (wrench balance, restart
  contract) still passes on the repaired globalization.

### Remaining uncertainty and unmet gates

- Full-target -0.20 direct: the cycle is now cut and classified, but
  whether the run completes -0.20, stops earlier, or stops at a different
  control value is NOT measured (the instrumented run predates the repair
  and timed out at the diagnostic cap). No physical-collapse claim.
- Full-target -0.20 interp: the chart abort is repaired by design and the
  mechanism is regression-covered on a small fixture, but the full-target
  run itself was not repeated (~113 s pre-repair; did not fit the
  remaining allocation). Root's final integrated checks must run both.
- The residual-dominated guard changes committed-step behavior for any
  real iteration with no improving alpha and a residual-dominated merit;
  the EP half acceptance passed unchanged, but the full 17-test slice3
  module, the coupling module, zero-span Armijo module and the standard
  25-module regression were not rerun this assignment.
- The 240 s force-interpolated finite-rotation coupling-module case and
  all mesh/arc/final25 gates remain open exactly as in the prior handoff.

## EARLY CHECKPOINT (turn 12, superseded by the final handoff above)

Budget at checkpoint: 2030.6258823000244 s used, 220 s allocation, 0 spent.

### Current measurements (confirmed from evidence, not re-run)

- `supervisor-domain-dc-full-1` (154.328 s, EXIT_1, current source hashes in
  its receipt): 5 intrinsic-mean/zero-span-selected tests PASS; 3 FAIL:
  - zero-span list/tuple fixture assertion — ALREADY FIXED by Astra in the
    test source after that run; do not undo, do not re-diagnose.
  - direct full -0.20: `stopped_at_limit` (not completed).
  - interp full -0.20: `ValueError: interp_beam_shell_201: interpolated
    SO(3) mean is outside the principal rotation-vector chart` raised from
    `full_u(q_trial)` inside the DC residual line search
    (nonlinear_static.py:4220 -> corotational.py:1248), aborting the whole
    solve from an otherwise valid committed state.

### Concrete diagnosis at checkpoint

1. Interp abort mechanism fully identified (traceback): the line search
   evaluates trial states `full_u(q_line_start + alpha*delta[:-1])`; for
   wild trials the master rotations leave the supported principal chart,
   `_so3_weighted_mean` raises a bare ValueError and the exception
   propagates out of `solve_static_nonlinear`. The committed `q` itself is
   admissible, so by continuity small alpha is admissible; the defect is
   that domain refusal is not treated as trial inadmissibility.
2. Direct stop: the only per-accepted/per-iteration evidence
   (ep-dc-limit-probe-2, ep-dc-step11-probe-1, ep-dc-block-probe-direct-1)
   predates the current residual line search, so it is NOT current evidence.
   It shows the pre-line-search pattern: steps 1-10 accept in 6-7
   iterations, then accepted increments need 47/93/139/146 iterations with
   cutbacks while lam passes a peak near 2.82; the per-iteration trace at
   step 11 shows the reduced residual cycling 4e3..3e5 with lam oscillating
   2.7..3.2 — a Newton limit cycle consistent with plastic branch
   flip-flop plus full-step fallback. One current-source instrumented run
   was the planned discriminating measurement; it was executed first
   (dc-final-repair-probe-direct-1) and confirmed an exact period-3 cycle
   (see final handoff diagnosis).

### Intended edits at checkpoint (all implemented as described in the final
### handoff)

1. Typed `SO3MeanDomainError(ValueError)` for the `_so3_weighted_mean`
   domain guards; input-contract guards stay plain ValueError.
2. DC loop: line-search trial-domain rejection (backtrack, never commit or
   assemble a refused trial); commit guard with classified
   `trial_state_domain_refused`; classified `line_search_no_improvement`
   when no admissible improving step exists at a residual-dominated state;
   both subdivision-eligible; rollback preserves the committed state.
3. Focused regressions for trial refusal, typed refusal and preserved
   state (small fixtures, no full-target solves).

### Planned checks (executed as listed in the final handoff)

- One instrumented direct full-target run on CURRENT source (timeout 120).
- Focused pytest of the new regressions.
- EP half acceptance compatibility check.
- Full-target reruns left to root's final integrated checks (unmet gate).
