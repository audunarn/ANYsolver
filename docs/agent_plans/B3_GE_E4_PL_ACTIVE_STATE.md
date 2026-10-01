# B3-GE / E4-PL / B2 active state — 1 October 2026

[Revision 8 goal](B3_GE_E4_PL_REVISION_8_GOAL.md), [plan](B3_GE_E4_PL_REVISION_8_PLAN.md)
and [acceptance matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md) govern under
risk-proportionate policy2026-09-24.2. Goal active; no aggregate gate accepted.
Formal F03 unconsumed. No main merge/publication authority. Full programme remains.

## Source, ownership and execution

Solver: C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling,
codex/b3-ge-e4-pl-integration, HEAD f2528206 before footprint commit.
ANYfem: C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer,
codex/experimental-ge-panel-consumer, HEAD0f0981de before consumer commit.
Root owns integration/evidence/note. Author and reviewer finished and hold readonly.
Solver8/consumer4 files are frozen, bound in the report. All numerical jobs terminal.
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

Next: narrow commit of both reviewed slices, verify foreign bytes/main preserved,
then select the next bounded M4 deliverable from reusable contracts. Do not reopen
parked BL5/chart sweeps by default. [Historical note](history/ACTIVE_STATE_20261001_NODAL_S3_TRANSITION.md)
is preserved byte-for-byte; immutable reports preserve failed runs and authority.
No overall speedup, production qualification or release claim.
