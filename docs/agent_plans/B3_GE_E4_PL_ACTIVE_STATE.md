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
branch codex/b3-ge-e4-pl-integration; latest product `7adee4f511fb173a5fbaef8e30938e7dbd0ba076`.
ANYfem: C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer,
tests-only commit `268001efc9102b46ffeb6ea776472a26205b4152`;
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
The shared finite owner now retains physical-fibre/mixed histories and native
strain/stress/plastic-increment recovery. V7 stores last predecessor and resulting
history separately; restore repeats the native update before atomic publication.
Verified positive histories: Q4 pure/mixed partial yield and elastic mixed S3.
Pure-fibre S3 and strong full-section yield still fail bounded cases. Do not
count their failure-contract tests as physical acceptance. J2/fibre combinations,
integrated energy/dissipation and line+fibre remain unfinished/excluded.

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

**Decision sought:** finish actual native fibre stored-energy/dissipation recovery
from accepted return-map quantities, without changing beam equations or confusing
material potential with physical energy. The history/predecessor seam is delivered;
do not rebuild it. Then wire coupled shell J2/fibre histories with independently
checked snapshot ownership and predecessor semantics. Required strong-yield and
pure-S3 convergence remain open; before another numerical batch, distinguish a
specific global-step/representation/roundoff explanation and its resulting action.
Do not automatically refine increments, change flow laws, relax residual criteria,
or rerun F03/F06. Reuse unchanged native local-operator/F08 evidence only within
its scoped identity; any changed native response must receive its affected checks.

No owned numerical job remains: source36248, installed76798 and consumer82461
completed. Installed62 guard280.442s/242937856B; consumer4 guard29.808s/216891392B.
Observed Python3.14.2, one numerical thread/JIT off;385solver+97consumer modules
match artifacts,269/270 imports onsite. Consumer worker finished; only its
tests changed and were independently inspected, verified and committed.
Keep100000rows/600s/8GiB/eight-thread ceilings, one heavy programme job and
at most three workers. No completed campaign needs repeating without changed inputs.

Prior longer note preserved byte-for-byte in
[pre-consolidation history](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_R8_20260930_F08_FIBRE.md),
SHA-256 fe37ee289e5ee35847e092befd76f474ee82f792ab9f009ee1f671b7ceff6506.
Earlier [B2/F09 history](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_R8_20260930_B2_F09.md)
and protected evidence retain their original dispositions.
