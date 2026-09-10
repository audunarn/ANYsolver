# G1a / G1 implementation handoff

Status: **IMPLEMENTED_DEVELOPMENT_VERIFIED_PENDING_INDEPENDENT_REVIEW**.
This is not formal qualification or full general-static parity.

Design freeze: `00866ca`.
Final candidate: `635888afa6d5f0ed9523f10ed4339670276d61c3`.
Tree: `bf948f65e9133f2a7b7b481ef6c089ee2eccdc7a`.
Branch: `codex/ge-beam3-g1a-exact-elastic-v1` (local only).

## Delivered

- Exact SPD linear-elastic section with empty history, isotropic mapping and
  immutable external-section capture. No surrogate yield law.
- Independent station-force constrained quadratic reduction and additive
  centered 42-variable elastic operator; 24 internal variables retained.
- Native Element/material-context adapter using the actual reference assembler
  and NonlinearStateStore; one shared nodal SO(3) state, all-or-nothing commit.
- Private two-element static owner with force/couple loading, rollback,
  accepted-state recovery and authenticated checkpoint replay/publication.
- Bounded development runner, with hard Windows process-tree memory enforcement,
  CPU/output inactivity checks and no automatic retry.

No old runtime file was edited. Qualified Q4/S3, old GE workflows, B2/B3,
selectors, defaults, package metadata and qualification records are unchanged.
Main remains `74703a3202251edc0beafb21cd31f52c9304ceb8` (0.4.3).
The unrelated ANYmesher compatibility plan in the main checkout is preserved.

## Verification

The final candidate passed **27 development tests in each of two fresh-directory
runs**, with one numerical thread per child. Elapsed process times were
30.86s and 30.55s; peak process-tree memory was below 193 MiB. Both complete
process trees drained to zero. These measurements are diagnostics, not speed
claims or performance qualification.

The scientific development packets are byte-identical: 14,968 bytes,
SHA-256 `c173c210ea0eed11501c9a13a6f391f727c1d67ed995bd4e631b509e9d2d5574`.
They cover the registered two-beam development fixture, not a complete future
general-static or legacy-domain campaign. The 39 inherited static planning and
admission tests also pass; these are a separate inventory.

S01-S04 cover shared rotations/rolls, rejected trials, second-element prepare
failure, stale/foreign tokens and busy-owner rejection. S05-S06 cover exact
section work, independent station KKT reconstruction and nonzero-residual Schur
elimination. S07-S08 cover actual assembly, directional tangent, physical
recovery, replay continuation and failed/no-overwrite checkpoint publication.
Additional checks cover reversal covariance/work, distributed load balance,
empty-history and definition/accepted-journal/checkpoint mutation rejection.

An initial development attempt failed because the new Element lacked two
abstract interface methods. That failure is preserved; the methods were added
before integration passed. A subsequent primary-agent inspection identified
warning-only handling of unhealthy linear solves. The final candidate promotes
that warning to a typed failure requiring cutback, without changing tolerances.
All earlier runs remain diagnostics, not substitute formal evidence.

Durable logs and final packets are under
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-g1a-20260910-635888a`.
The companion result binds per-file byte counts and SHA-256. Original temporary
diagnostics remain untouched; temporary workspace transfer copies were removed
after byte-verified archival.

## Remaining gate

The design review was by the primary implementer, not an independent reviewer.
No independent implementation review or formal qualification cycles have run.
Do not reinterpret development reproducibility as those missing approvals.

Next: independently review the frozen candidate, test coverage, state ownership,
load/tangent work and restart trust boundary. Address findings in a successor
candidate if necessary, then run the separately bound formal G1 confirmation.
Only after acceptance recommend G2 (constraints/MPCs); do not execute G2 now.
No merge, publication or new public selector is included in this handoff.
