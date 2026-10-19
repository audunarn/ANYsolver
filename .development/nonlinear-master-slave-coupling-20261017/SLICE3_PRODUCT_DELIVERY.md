# Same Mistral owner: unblock and deliver the product/EP slice

Repo C:/Github/ANYsolver; Edit; MaxTurns60, final12 reserved for checks/handoff.
This is a focused continuation from your useful source/diagnostic artifacts,
not a new investigation. Two prior runs ended at their turn bounds without final
handoffs; Astra has inspected actual source, tests, receipts and checkpoint.

Read supervisor_findings.md latest sections and checkpoint.md. Established
decisions stand; do not reread broad history/catalogs, rerun attribution or probe
serialized checkpoints. Policy/source ownership remains unchanged. R2 stays
refused; do not add initial-field capability. No Git mutations/sibling edits or
workers. No physics/tolerance changes. The original sources/tests are preserved.

## Owned outcome

Finish current product repairs R1,R3,R4,R5 and maintained source/EP regressions:
- Owned product files remain the original five, with actual current edits only
  corotational.py/nonlinear_static.py. Keep all existing work. Own
  tests/test_nonlinear_beam_shell_slice3.py and a new
  tests/test_nonlinear_beam_shell_slice3_continuation.py; current EP diagnostic
  ep_edge_coupling.py and harness.py repairs as needed. Do not edit/run the new
  mesh_study.py, arc_reference.py, analytical_derivation.md: Astra now owns those
  independent acceptance oracles concurrently. Do not run full25 final regression;
  Astra integrates it after this handoff. This preserves you as the central
  product/EP implementation owner, not just a helper.
- First run focused source repair tests through harness and fix remaining fixture
  failures. Parent run supervisor-source-repairs-1 retained12passed/4failed at
  pre-repair identities (inputs changed during that run, not current acceptance).
  Current R3 source/fixture fixes and external-only tangent test already exist.
  R1 positive test builds an invalid shell [1,2,3,3]; replace with a valid 4-node
  rectangle (and valid linear chain), not weakened validation. R5 finite-state
  presolve gives ry0.003144rad, not >.1; the regression concerns nonzero finite
  Jacobian, not a particular large angle. Assert actual J-row and load projection
  nonzero while linear row is zero. Use a well-conditioned finite initial state
  and a controlled increment near that state (or a clear minimal elastic spring
  fixture through the public driver), rather than requiring a huge jump from a
  tiny Jacobian to uz-.01. Do not weaken mechanics error tolerances. Fix genuine
  production defects if uncovered. Stop broad fixture parameter sweeps.
- Deliver the original EP geometry direct2/interp3 beam elements, S355 canonical
  curve, -.20m full12steps/max40/tol1e-8, half6 to-.10/resume6 to-.20 with ordinary
  copied initial displacement/material state and equilibrate_initial_state=False,
  emit_restart_checkpoint=False. Independent residual at actual lambda<=1e-7,
  controlerror<=1e-8m, positive plasticity, same restart tolerances, physical
  histories and force/wrench balance, existing constraint limits. Preserve inputs
  on success/rejection/cancellation; cancel via accepted progress events, reuse
  same inputs. Retain failed evidence; no serialized-checkpoint workaround.
- Prefer fixture/session solve caching so several assertions inspect the same
  expensive immutable result; final regression starts a fresh process naturally.
  Tests must assert outcomes, not merely print JSON. Nonlinear full route must be
  exercised. Existing preyield4 controls already passed; add maintained assertions.

## Execution and handoff

Budget NOT reset: budget.json used661.0452738000022s of3600 at assignment,
remaining2938.954726199998s, final900 reserved for integrated checks. You have
exclusive task numerical execution during this focused assignment; Astra only
writes the independent oracles. Use shared harness for all solves/pytest,
unique evidence dirs, per-case120s, one child, exact source/test hashes/JUnit and
effective one thread/JIT off. Do not use --allow-reserve here. Do not rerun passed
unchanged checks; new source/test changes justify relevant reruns. Total allowance
is unchanged; stop if a gate cannot fit the remaining nonreserve time.

Within first6 turns make a concrete edit/run using existing artifacts; don't
spend this assignment re-investigating already decided facts. Read latest
supervisor_findings at that point for actionable review. By turn45 save a concise
handoff even if partial; use final12 turns for verification/repair/documentation.
Report changed files, exact checks/actual counts, all failures/unmet gates and
evidence paths, current hashes and used/remaining budget. Update HANDOVER §8 with
this product slice's actual state. Do not declare whole Slice3 complete: analytical,
mesh and final integration acceptance are Astra's remaining work.
