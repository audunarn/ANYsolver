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
branch codex/b3-ge-e4-pl-integration; latest product `d6397cad2701566350620ccc6e274c4f51f5c808`.
ANYfem: C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer,
tests-only commit `527a48daaebcbefb1f5494efbfe7375f23be870d`;
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

**Established:** optional adaptive cutbacks complete unchanged partial-fibre S3
load/unload(.5,1,.75,.5). Physical checkpoint and fibre energies match fixed
identical accepted increments byte-for-byte. V10 atomically binds pending plan,
controls and accepted work to the snapshot. Defaults and physical checks unchanged.
Strong full-section Q4 still fails after an elastic(.0625,) prefix; no active
yield was accepted. Preserve this named M4 obstruction without automatic budget
growth or fixture/tolerance tuning. Simultaneous yielding/full G3 stay open.

[Current results and raw failures](../../.qualification/b3-ge-e4-pl/r8-adaptive-native-increments-dev-20260930-v1/results.md):
installed88/88; installed S3 complete history and focused ANYfem1/1
save/reopen/cancel/restore/complete. Wheel654ff57c...; consumerff143e5f...
unchanged.386solver+97consumer modules match source/wheel/site;280/270 onsite
imports. Old V7 retains exact bytes and prior failed unloading. No gate closes.

**Decision sought next:** resolve E01 shell/point rotational transfer and M2
physical law/interface policy. Existing two-direction E01 and direct torque
evidence locate a coupled-action discrepancy; no further refinement by default.
Obtain focused independent mechanics interpretation and choose one discriminator
that separates a work-map defect from distinct shell/connection idealizations.
Before numerical execution, record competing explanations, bounded check and
retain/revise/reference action. Do not drop a point row, tune drilling or select
multipliers from one quotient. Existing BL5 semantics remain distinct.

[Saved-work decision](../../.qualification/b3-ge-e4-pl/r8-e01-cross-work-dev-20260930-v1/results.md):
no new solve; reciprocal closure4.1554e-13. Membrane/normal-spin contributes
102.2491% signed, plate-2.2491%. Independent review confirms geometry/map/signs;
48-port beam parity is already established. Normal-spin/membrane impedance,
not beam interpolation or sparse roundoff, principally explains this coupled
gap; neither shell is thereby physically qualified. Retain six-row points.
Next define a matched material-spin/director/footprint work reference explicitly;
a recovered-frame variant cannot silently replace nodal-pose E01 semantics.
Advance BL5 independently from existing tests/evidence, preserving its distinct
top-surface/director bond, free spin and retained half-cell work. Do not repeat
completed common-field/retained-work/saved-mode checks or launch formal F03.

No owned numerical job remains: installed73264, S3 screen9387 and consumer85487
are terminal passed. Guards387.533s/250912768B,69.693s/161853440B and
56.224s/215064576B. Actual Python3.14.2,one numerical thread/JIT off.
Independent adaptive and E01 mechanics reviews completed read-only, no jobs or
source edits; findings/dispositions are archived. Foreign F03 untouched.

Prospective finite-BL5 slice: elastic shell/generalized beams only, unchanged
director/top-surface law and existing P0/P1 spaces, no multiplier selection.
Spatial left-port work plus gauge correction and additive shell column map
must pass actual-update nonzero-multiplier derivatives, fixed-reference parity,
physical station wrench balance, cancellation/rebase/V11 restore/continuation.
Then run a small nonmatching elastic finite load/unload route through installed
artifacts. Failure identifies implementation/chart/response obstruction; retain
it rather than tune spaces/tolerances. F03/G2 remain open. Existing typed global
cutbacks apply; only typed BL5 candidate chart failures may backtrack locally.
Keep100000rows/600s/8GiB/eight-thread ceilings, one heavy programme job and
at most three workers. No completed campaign needs repeating without changed inputs.

Prior longer note preserved byte-for-byte in
[pre-consolidation history](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_R8_20260930_F08_FIBRE.md),
SHA-256 fe37ee289e5ee35847e092befd76f474ee82f792ab9f009ee1f671b7ceff6506.
Earlier [B2/F09 history](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_R8_20260930_B2_F09.md)
and protected evidence retain their original dispositions.
