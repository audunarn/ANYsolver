# B3-GE / E4-PL / B2 active state — 1 October 2026

[Revision 8 goal](B3_GE_E4_PL_REVISION_8_GOAL.md), [plan](B3_GE_E4_PL_REVISION_8_PLAN.md)
and [acceptance matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md) govern under
risk-proportionate policy2026-09-24.2. Goal active; no aggregate gate accepted.
Formal F03 unconsumed. No main merge/publication authority. Full programme remains.

## Source, ownership and execution

Solver: C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling,
codex/b3-ge-e4-pl-integration, HEAD a9277078 (reviewed GE and B2 footprints).
ANYfem: C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer,
codex/experimental-ge-panel-consumer, HEAD cc9a490 (B2 footprint consumer).
Root owns integration/evidence/note. Previous solver8/consumer4 source bindings
are committed and recorded in their report; new B2 changes do not relabel those
artifacts. B2 core and consumer are committed. bl5_consumer owns the next bounded
GE reference-modal source/test slice; reviewer is readonly. Root owns evidence,
integration and checks. All owned numerical jobs are terminal.
At most3 workers/one heavy job/100k rows/600s/8GiB/8 numerical threads.
Python C:/Python/Python314/python.exe; child settings BLAS/Numba1/JIT off.

Foreign dirty scripts/b3_e4_f03_c1_fy_supported_reference.py SHA
c908b1f3e4d9467deb3a96876126d5488cd040503cc6c6ec485b8aeaecef9481:
do not edit/stage/run/interrupt. Main untouched. Verify changed identities on resume.

## Delivered behavior and scientific boundary

GE point owners provide sparse Q4/S3/native-retained solves, finite/adaptive
stepping, atomic state, physical recovery, restart and chart reset. Physical B2
provides batching/envelopes and eligible factor reuse. Scoped foundation acceptance
is recorded in the matrix; it does not confer an aggregate pass.
[Material histories](development/r8-staged-material-history-20261001/results.md)
cover bounded yielding fibres, S3 J2 and simultaneous Q4/generalized yielding.
[F06](development/r8-f06-staged-transport-20261001/results.md) accepts loaded
large-elastic point transport only. Correct retained6-force/12-moment normalization
still passes its original26 pairs; protected44 snapshots unchanged. Large plastic,
wider attachment/support and full history coverage remain open.

BL5 releases normal spin and is distinct from six-pose points/welds. Retain P0
c_lambda=2 for development only. [Combined evidence](development/r8-bl5-matched-comparison-20261001/common-action-v1-results.md)
finds fine matched work gaps<.061%, but Mz reference refinement>1.3% and unresolved
root/integrated transfer. Isolated common-action states are not coupled solutions.
Stop mesh/port tuning in that slice. F03/G0B/M2, physical torque/shear/drilling and
mandatory CalculiX comparisons remain open.

## Completed footprint slice and next action

[Combined solver/consumer delivery](development/r8-nodal-rigid-footprint-20261001/results.md):
elastic selected-node rigid footprints stack existing six-pose constraints at
one native beam node, locking normal spin. Complete selected-cell patches bind
all vertices/actual edges. Not distributing or continuous-area coupling.
Q4 requires full pullback; mixed/all-S3 solver scope admitted. Grouped physical
wrenches use transpose actions and compensated lever arms. New nonempty-footprint
policies bind stable S3 histories, F6/M12 scales and unrebased admission.

Final solver wheel5d4d8602:49 footprint+4 legacy-chart checks pass;26 preceding
legacy-impact checks reused by reviewed unchanged dependencies. Fixed prior/current
Q4 default observables/checkpoints are exact. Paired ANYfem wheela336e719:23new+89
existing checks pass;389+98 source/wheel/site modules exact. Q4 consumer example
completes input/Project save-reopen, solve, recovery, checkpoint/restore/continuation.
Mixed/all-S3 consumer evidence is persistence, not a full finite campaign.
Independent reviews have no blocking scoped finding; report binds raw292-file
archive, all artifacts/resources/failed versions and provenance discrepancies.

Strict rebased successor parity failed at unchanged1e-9 for Q4/mixed/S3.
Ordinary restore is exact; cross-chart roundoff is amplified in retained forces.
No narrow repair justified. Public footprint rebase/chart restore reject atomically.
Required M4/F06 chart transport stays OPEN, not waived or removed. Full F04,
distributing/area/plastic/off-node/line/seam/torque/external/scale obligations remain.

Both preceding footprint commits are verified. [B2 core delivery](development/r8-b2-nodal-rigid-footprint-20261001/results.md)
adds distinct reference-linear nodal groups, sparse affine factor reuse and selected
physical wrenches: g=(ub-us+[Xb-Xs]x theta_s,theta_b-theta_s), not the historical
least-squares finite-vertex point port. Installed wheel ee6f70a2 binds390 modules/
209 onsite imports/pools1/JIT off.35 original passes plus one corrected predicate,
38 legacy passes, public example and exact13-array/defaultJSON old/current control
have complete independent review. Initial collinear-fixture/build/preparation
failures remain in the63-file raw archive. New spectra reject; no finite/drill-free/
distributing/full foundation claim. Root commits this bounded source/evidence now.

Completed [B2 consumer](development/r8-anyfem-b2-nodal-footprint-20261001/results.md):
distinct strict input/Project schema, footprint-only input, legacy no-silent-drop
guard, selected batches and complete-case cancellation. Paired ee6f70a2/c07432fb
artifacts bind390+98 modules.37new+112legacy checks and installed1/10/100 examples
pass, one factor each. Previous/current payload SHA99b4bf40 and observations
406b29c9 are byte-identical. Independent review clear;119-file raw archive retains
the initial bytes-JSON recorder failure and corrected UTF8 representation.

Next M4/F07: supported virgin elastic flat-Q4/generalized-GE point-owner finite
modes using the actual sparse descriptor. Decision: six retained half-cell beam
rotations carry inertia;18 resultants, nodal rotational traces, shell normal spin
and multipliers remain algebraic. Existing native kinetic factors and physical
Q4 mass are reused. No positive-definite interpretation of native mixed K, no
global production condensation. Author prepares bounded source/tests; root checks
kinetic work, full descriptor-QZ parity, equations/gaps and unchanged owner state.
Reject S3/footprints/lines/material histories/free-free/prestress in this initial
slice. If actual physical mass or descriptor consistency fails, retain finding
and repair affected seam before expanding. Full F07/G4B remains open.
Do not reopen
parked BL5/chart sweeps by default. [Historical note](history/ACTIVE_STATE_20261001_NODAL_S3_TRANSITION.md)
is preserved byte-for-byte; immutable reports preserve failed runs and authority.
No overall speedup, production qualification or release claim.
