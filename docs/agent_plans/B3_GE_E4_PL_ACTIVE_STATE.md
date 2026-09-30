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
branch codex/b3-ge-e4-pl-integration; latest product `6b0b1131a9dcf055811901d55daabac049a4e2a0`.
ANYfem: C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer,
tests-only commit `69184db3bc7e6ccdde0c7e1642fc6bb78afd7cf8`;
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
Finite fibre histories/stresses and line+fibre are explicitly unsupported.

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

**Decision sought:** extend the existing finite owner to physical-fibre material
histories without independent component commits or loss of old checkpoint meaning.
The reference-linear seam is now verified. Read FinitePointDriver's history,
recovery and checkpoint contracts and the existing native fibre history/force
driver. Choose a family-aware immutable accepted-state layout using those
operators; preserve generalized-only schemas and use a distinct identity for
new mixed/fibre histories. Begin with one bounded point-panel load/unload,
rejection and fresh-restore slice; verify actual accepted material recovery and
predecessor ownership before broader histories. If the existing adapter cannot
supply a faithful candidate/history, resolve that seam rather than inventing
another beam law. Do not restart F03/F06 diagnostics by implication.

No owned numerical job remains: source94277, installed94839 and consumer adjunct
completed. Installed54 guard202.673s/239112192B; adjunct4.121s/206434304B.
Observed Python3.14.2, one numerical thread/JIT off;384solver+97consumer modules
match artifacts,268/267 imports onsite. Reviewer finished without jobs/edits.
Keep100000rows/600s/8GiB/eight-thread ceilings, one heavy programme job and
at most three workers. No completed campaign needs repeating without changed inputs.

Prior longer note preserved byte-for-byte in
[pre-consolidation history](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_R8_20260930_F08_FIBRE.md),
SHA-256 fe37ee289e5ee35847e092befd76f474ee82f792ab9f009ee1f671b7ceff6506.
Earlier [B2/F09 history](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_R8_20260930_B2_F09.md)
and protected evidence retain their original dispositions.
