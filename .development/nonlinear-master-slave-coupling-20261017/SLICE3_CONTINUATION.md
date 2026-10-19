# Same-owner Slice 3 continuation — delivery, not another audit

Repo C:/Github/ANYsolver; Edit; MaxTurns120. Same Mistral implementation ownership
as SLICE3_ASSIGNMENT.md. The initial 80-turn run reached its bound without a final
handoff; Astra reconstructed actual progress in supervisor_findings.md. Read that
file FIRST, then supervisor_code_review.md and supervisor_reference_review.md.
These contain resolved scientific decisions and concrete corrections, not guesses.
Original assignment/user acceptance remains applicable except the explicitly
adopted bounded refinements and scoped analytical constraints in supervisor notes.

Evidence allowance is NOT reset: budget.json used621.3494068000291s of3600 at
handoff, remaining2978.650593199971s, final900 reserved. Keep every attempt/failure.
Initial five product source files and two new tests still match original hashes.
The original 61 baseline tests passed; seven-case attribution proved partial-load
plateau and reproduced VK on HEAD. No need to rerun them before source changes.

## Deliver connected remaining outcome

1. Fix harness findings (exception-proof timing/cleanup, correct source identity,
   actual named counts/new input hashes). No blanket reruns to recreate evidence.
   Correct ep_attribution prose: lambda<1 + small achieved residual is valid partial
   equilibrium, not solver bug. Existing diagnosis is decided; no more sweeps or
   checkpoint probes. Native Q4 serialized checkpoint limitation is documented,
   not part of this repair. DO NOT weaken native state binding/checkpoint guards.
2. Finish EP direct/interp continuation/tests using ordinary initial u/state API:
   emit_restart_checkpoint=False; half6steps to-.10, resume6steps to-.20 with deep
   copied initial_displacements/initial_element_states, equilibrate_initial_state=False;
   uninterrupted12steps. The starting lambda0 is an augmented Newton guess, not
   lost material history; external loads are on shell masters in these cases.
   Correct independent residual to actual result.load_factor and assert accepted
   residual<=1e-7, control target<=1e-8m, positive plastic strain, constraints,
   full force/wrench reactions, input immutability, split history tolerances.
   DC cancellation uses progress_callback, not status_callback. Rejected-step
   snapshots must exclude rejected history. Convert these into maintained pytest
   cases under tests/test_nonlinear_beam_shell_slice3*.py; output alone is not a test.
3. Repair confirmed non-author findings R1,R3,R4,R5 (review has exact lines/tests):
   fail closed for downstream dependencies on rotating slave translations;
   map fully constrained returns; coupled auto selects work_conjugate with follower
   loads and explicit legacy modes are refused on this new route; nonlinear DC
   row AND load admission use full_u(q) and its actual initial Jacobian. R2 is
   already refused by initial-field admission: retain that guard, no new capability.
   All owned five files and designated tests are authorized. Other product files
   need a scope report before edit. Source reviewer can recheck artifacts later.
4. Implement and execute bounded mesh study (R1–R4 at12k, M1–M4/P1–P4 at140k,
   corresponding linear, exact gates in original assignment) with machine results,
   per-case flush, explicit completion/target/residual, input/source identity.
5. Implement independent constrained-plane-section circular arc reference using
   reviewed formulas/terminal constituent loads, exact row constraints, given
   geometry/material and nx8/16/32 initially, both coupling ratios/e0/e.002/30/60deg.
   Do not use free-width shell as exact arc. Refinements64/128/256 conditionally
   authorized prospectively in supervisor_findings; same1%/.25% gates and budget.
   Save adopted analytical_derivation.md; reference is independently reviewed but
   FE results are not accepted until measured. No empirical fitting/relaxation.
6. Final exact25 historical + two Slice1/2 + newSlice3 modules through portable
   runner, one verified thread/JIT off/retired0. No retired imports/runs. Preserve
   all selected identities/full logs/actual counts. Final regression must follow
   integrated source/test edits; do not consume final reserve on exploratory work.
7. Address actionable parent/reviewer findings, update HANDOVER active §8 with
   exact candidate/evidence/tables/budget/unmet gates; concise actual final handoff.

By turn12 update checkpoint.md with concrete implementation progress, not another
inspection-only plan. Read supervisor_findings.md again at that checkpoint and
before final verification for feedback; use artifacts instead of expecting chat
messages into this noninteractive wrapper. Reserve last20 turns for checks/repair/
handoff. If blocked, report the specific scope/contract question and continue
independent permitted gates. Stop optional investigations that do not change the
next implementation decision. Do not leave handoff to an unexecuted final turn.
Do not launch workers, mutate Git, commit/push, touch unrelated dirty work or siblings.
