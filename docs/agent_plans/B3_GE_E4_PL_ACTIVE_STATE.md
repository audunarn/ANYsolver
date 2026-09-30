# B3-GE / E4-PL / B2 active state — 30 September 2026

[Revision 8 goal](B3_GE_E4_PL_REVISION_8_GOAL.md), [plan](B3_GE_E4_PL_REVISION_8_PLAN.md),
[acceptance matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md) and
[complete programme](B3_GE_E4_PL_B2_COMPLETE_PROGRAMME.md) govern.
Policy: ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1,2026-09-24.2.
**Scoped F05/F08/F09 PASSED. G0B and formal G1 acceptance remain open.**
Experimental integration is permitted; full G0–G6/F01–F13/V01–V28/B01–B18,
external/scale/platform/consumer/release obligations remain. Goal active.
No main merge/publication authority; this task has not changed main.

## Source, ownership and delivered behavior

Solver: C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling,
branch codex/b3-ge-e4-pl-integration; latest product `86d3759a2441ab22735c3e195e5bb44ed62beee8`.
ANYfem: C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer,
tests-only commit `2a5352c0adc5fcbce25bbb1484553108c906157f`;
runtime remains `a615c4b`.

**Separately owned dirty scripts/b3_e4_f03_c1_fy_supported_reference.py:
do not edit/stage/run/interrupt.** Formal F03 authority is unconsumed;
historical consumed authorities remain consumed. No outside job was interrupted.

GE Q4/S3 point panels support experimental finite generalized-beam/shell J2,
owned shell anchors, atomic state and restart. Selected fixed-predecessor F05
is accepted; full material/rotation-history scope remains open.

New native integration: the same owner now handles reference-linear physical
axial/biaxial-fibre beams and mixed generalized/fibre members with Q4/S3.
Native42-coordinate operators/equations remain unchanged. Public headless
example options physical_fibre/mixed solve/recover/checkpoint/restore/continue.
ANYfem's existing experimental input v1 preserves their raw definitions.
The shared finite owner retains physical-fibre/mixed histories, actual station
strain/stress/plastic increments and paired beam stored energy/last-increment
dissipation. Distinct V8 stores coupled shell-J2/beam predecessors and accepted
histories with S3 chart bindings; restore repeats/validates before publication.
V7/legacy contracts remain. Positive cases: Q4 partial-fibre yield with elastic
shell-J2-defined response, and mixed all-S3 shell yield with elastic fibres.
Pure-fibre elastic S3 and partial-fibre S3 now complete unchanged monotonic
loading with stable translation arithmetic and checkpoint-bound V9 policy.
V7 restores retain legacy arithmetic. Simultaneous active yielding, yielded
S3 unloading, strong full-section yield, line+fibre and total-system energy
remain open. Failure-contract tests are not physical acceptance.

## Accepted evidence and remaining uncertainty

- [F08 foundation](../../.qualification/b3-ge-e4-pl/r8-f08-foundation-20260930-v1/results.md):
  current local extraction17/17 installed, independent acceptance; accepted
  predecessors,18+24/shared/disjoint blocks, actual-update derivatives and
  exact history/checkpoint checks. V1 collection failure remains preserved.
  This is not independent material-law, yield-switch semismooth, line or scale acceptance.
- [Fibre-linear integration](../../.qualification/b3-ge-e4-pl/r8-ge-fibre-linear-dev-20260930-v1/results.md):
  source52/52 plus focused extras; fresh installed54/54, three headless families,
  distinct ANYfem2/2, independent code/mechanics/artifact review clear.
  Source fixture failures retained. Wheel56deb65e...; unchanged consumerff143e5f....
  This is verified experimental behavior, not an aggregate gate or speedup.
- [Finite-history integration](../../.qualification/b3-ge-e4-pl/r8-ge-fibre-finite-dev-20260930-v1/results.md):
  source41/41; new wheel909f26ce..., installed62/62 plus two public Q4 history
  examples; unchanged consumerff143e5f..., installed4/4 save/reopen/history checks.
  Independent review clear within the experimental scope. All convergence and
  cache-build failures retained; no aggregate acceptance or measured speedup.
- [Energy/coupled integration](../../.qualification/b3-ge-e4-pl/r8-ge-native-energy-coupled-dev-20260930-v1/results.md):
  source10/10; fresh wheelb0f15d3e...,installed124/124 plus two public examples;
  unchanged consumerff143e5f...,installed7/7 save/reopen/material-history cases.
  Independent code/artifact review clear; Q4 active-shell coverage failure retained.
  Default native mechanics unchanged and affected checks pass; no blanket reuse
  of earlier artifact identity, aggregate qualification or measured speedup.
- [F09 foundation](../../.qualification/b3-ge-e4-pl/r8-f09-foundation-20260930-v1/results.md):
  physical B2 section/local operator/station trace accepted; guard200, exact
  threshold6 and candidate legacy14 retained with unchanged-input reuse.
  Arbitrary graph accuracy, attachments/mass/prestress and M3 acceptance remain open.
- [F05 foundation](../../.qualification/b3-ge-e4-pl/r8-f05-foundation-20260930-v1/results.md):
  selected Q4/existing S3 fixed-predecessor pullback accepted; not full G3.
- [F06 failed discriminator](../../.qualification/b3-ge-e4-pl/r8-f06-noncommuting-dev-20260930-v1/results.md):
  Q4 coverage bounds missed; S3 first-step Newton limit. Do not automatically
  retune/repeat; not formulation failure. Native total energy remains unmeasured.

BL5 physical transfer, norms, indefinite mixed-system interpretation and multiplier
resolution remain open; no selection from a quotient or automatic axial refinement.
Ordinary native persistence, complete spectra/capacity and practical scale remain open.

## Next action and restart

**Established:** the bounded native diagnosis isolated a shell-coordinate
roundoff floor for monotonic S3 partial-fibre yielding. The existing stable
map repairs that case at unchanged tolerances. Sparse equilibration/refinement
does not repair Q4 full-section yield or yielded S3 unloading. Their rejected
trials switch fibre branches and retain large residuals; small same-branch
actual-update derivatives are consistent in the inspected unload direction.
Do not treat this as a complete Jacobian qualification or formulation failure.

[Current results and raw failures](../../.qualification/b3-ge-e4-pl/r8-stable-native-s3-dev-20260930-v1/results.md):
source11/11 plus3 codec checks; installed113/113 and ANYfem1/1 focused S3
save/reopen/restore/continue. Wheel953f20d9...; unchanged consumerff143e5f....
385solver+97consumer modules match source/wheel/site;288/269 imports onsite.
Old-wheel V7 restores byte-identically, including its original failure status.
Independent review is clear within this slice. No aggregate gate closes.

**Decision sought next:** determine an admissible global stepping route through
the retained branch-switching failures. Prepare the already-required adaptive
increment controller against this persistent owner, with atomic cutback and
unchanged physical acceptance; preserve the fixed-increment failures as controls.
Before its numerical batch, specify the branch/step hypothesis and physical
history comparison. Do not tune constitutive laws, fixtures or tolerances, reuse
the closed Armijo experiment, or rebuild delivered energy/checkpoint seams.
Simultaneous yielding, actual-history coverage and full G3 remain mandatory.

No owned numerical job remains: source73148/13098 and installed28642 completed;
consumer bounded run completed directly. Installed guard413.402s/246206464B;
consumer6.199s/214282240B. Actual Python3.14.2, one numerical thread/JIT off.
Consumer worker finished read-only review. Foreign F03 work remains untouched.
Keep100000rows/600s/8GiB/eight-thread ceilings, one heavy programme job and
at most three workers. No completed campaign needs repeating without changed inputs.

Prior longer note preserved byte-for-byte in
[pre-consolidation history](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_R8_20260930_F08_FIBRE.md),
SHA-256 fe37ee289e5ee35847e092befd76f474ee82f792ab9f009ee1f671b7ceff6506.
Earlier [B2/F09 history](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_R8_20260930_B2_F09.md)
and protected evidence retain their original dispositions.
