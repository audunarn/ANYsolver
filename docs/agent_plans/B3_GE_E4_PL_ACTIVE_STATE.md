# B3-GE / E4-PL and B2 — current development state

**8 October 2026.** Worktree `C:/Github/ANYsolver/.perf2-worktrees/stiffened-rev8-20261008`,
branch `codex/stiffened-rev8-resume`, pushed head `0cda7dcc`. This is the
authoritative current-state note. The preceding 448-line note was copied
byte-for-byte to [history](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_20261008_V12.md)
(SHA-256 `f09b8d490d39b6b3ea528f7a8f91007962607ef82ca2777e2107934132e36f10`).
The [Revision 8 plan](B3_GE_E4_PL_REVISION_8_PLAN.md),
[goal](B3_GE_E4_PL_REVISION_8_GOAL.md) and
[acceptance matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md) retain the
full G0–G6, F01–F13, V01–V28 and B01–B18 scope and all historical failures.

## Decision and next discriminator

The native BL5 connection law and multiplier policy remain **unselected**.
V5's original P0/tip action produced `1.74538504e-6 J` native beam work
versus `2.40980606e-7 J` resolved C3D20 beam work, a ratio of `7.24284`.
V11 found the saved V7 cut-face zero-resultant action changes the bounded
two-sided *solid* response by only `0.155%` under V9 supports. V12 then showed
the original native retained-spin interface action is separately balanced;
removing it on the unchanged native body reduces work by `1.15586949e-7 J`
and leaves `1.62979809e-6 J`, still `6.76319` times the saved resolved work.
Both checks had independent read-only review without blocking findings.
Neither allocates body versus connection error or qualifies a line law.
[V11](../../.development/bl5-mz-common-beam-20261008/v11-cut-warping-adjudication.md)
and [V12](../../.development/bl5-mz-common-beam-20261008/v12-retained-load-adjudication.md)
retain source, exact input, runtime, raw output and limitations.

The frozen V5/V7 records **cannot** supply a full two-sided original-action
reference. The C3D20 bar has axial faces only at `x=0,.5,1 m`, while native
retained half-cell sides also meet at `.25` and `.75 m`. A four-axial-cell
solid with duplicated interior faces would expose those sides, but its extra
relative rigid modes require an independently physical seam traction/jump
law. A full displacement weld removes the sided freedom; an unspecified
hinge fitted to V5 would be circular. This is a missing reference contract,
not a native-formulation failure. Keep V5's `7.24284` ratio unallocated and
stop the V5 causal-decomposition sequence. Advance the plan's physically
matched BL5 torque/shear and work-transfer benchmark under an explicitly
declared continuous connection, with its real geometry, loads and supports.
Do not repeat classical axial refinement or tune channels to one case.
Formal F03 remains unconsumed; G0B and G1 acceptance remain open.

## Delivered experimental behavior and open acceptance

- The sparse multi-element Q4/mixed Q4-S3/all-S3 GE point workflow, physical
  recovery, checkpoint/restore, and continued stepping exist. Separate B2
  batch execution and an ANYfem consumer exist. These are experimental
  capabilities, not G0/G1/G6 acceptance.
- The pinned ANYfem `345db0c` and solver installed sites pass 54/54 affected
  plus 19/19 legacy development controls. Earlier exact packet V2/V3
  pre-pytest timeouts remain failed evidence. Effective numerical thread
  pools were not independently audited in the successful consumer smoke.
  [Evidence](<C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/.development/distributing-displacement-consumer-common-main-20261008-v1/installed-development-adjudication-v1.md>).
- The simultaneous Q4-J2/native-fibre chart-rebase source and installed
  checks passed for a small-angle, three-increment, two-stiffener history.
  Finite-angle sensitivity, S3, broader F06/V18/G3 and different-family
  acceptance remain open. [Evidence](../../.development/f06-j2-fibre-chart-20261008/evidence-index-v1.json).
- B2's coarse external compliance comparison remains failed/not converged;
  the continuum-versus-plate/beam idealization is unresolved. It is separate
  from the principal GE connection decision. Other G2–G6 mechanics, scale,
  external comparisons, platforms, consumer completion and release remain open.

## Execution and restart boundaries

No owned numerical job is in flight. V11 and V12 each completed one distinct,
bounded development attempt; their unused time does not authorize another
question. V5–V10 and older closed one-use evidence remain unchanged. The
historical body retry is pending, formal F03 unconsumed, and protected
`us3-modal-canary` material must not be inspected or copied. For current
bounded diagnostics, use one numerical job, CPU0, one thread, JIT disabled,
2 GiB and the case-specific process/cumulative limits. Preserve exact
receipts and failures. The user's prospective approval supports needed work
within these contracts; it does not relax scientific criteria or publish a
partial release.

Mistral/local workers were unavailable for this task; Astra directly owned
the tightly coupled physical diagnostics and their Git integration. Do not
communicate with the separate contact worker. On resumption, verify actual
Git and process state, read this note and the relevant evidence only, then
advance the matched P0/tip contract while independent capability work
continues where prerequisites permit. Do not rerun passed campaigns merely
to reconstruct their accounting.
