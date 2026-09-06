# P5 bounded force-accuracy32 comparison freeze

Parent `6ef2a405365ae786c7d0022f660188996a51a8ea`, tree
`2bce225d8b9506158903f0b28532e306972af6c5`.
Exact five-path extent: new force-accuracy32 diagnostic runner and test,
failure-snapshot test, this plan, and an optional failure-only observer in
the research displacement controller. No mechanics, section, production,
environment, physical tolerance or previous evidence changes.

## One bounded causal comparison

Run only the two existing arch targets 0.1 and 0.095 on 32 elements (65
nodes, 512 stations, explicit ARCH_ONSET32 extent), using the separately
developed ForceAccurateAssemblyHistoryProbe. Geometry, section, quadrature,
clamps, all free spatial DOFs, predictor/corrector and line-search acceptance
remain as in the preserved observation. There is no additional onset grid,
bisection, continuum execution or branch switching.

Freeze the existing force-accuracy policy without tuning: total estimated
error 1e-12, local allocation 1e-12/32, physical length 2, force scale one.
Global physical acceptance remains 1e-11. Retain sixteen global corrections,
ten backtracks and 8192 mixed evaluations per trial. The estimate is not a
rigorous arithmetic-error bound, and failure remains possible.

## Prior evidence and authority

Bind all eight files of the first failed onset32 attempt and all nine files
of the completed observation. The runner contains their exact names, byte
counts and SHA-256 values. Their historical FAILED outcomes are not changed.
The observation diagnostic hash is
`046373A0827D2CCBCD4EBE9EF86D0700D44F7B7FFB1F9B853607E39123C2C10E`.
Its original authority commit is
`9d3b67a730a1db5d67985c4be7c60586114917f8`.

Require the new clean direct child of this plan's parent with the exact
five-path extent. Bind the unchanged Python/NumPy/SciPy executable and full
non-bytecode inventory through environment hash
`2CD226A5CF78C9CC833DCBAF7E4CD0C8EAB92DD8566AF69412E13D346DC298F4`.
Require clean ANYfileIO commit `b48ba51c7b79e6d64b3f99c1fb131b9b602e7e1d`,
tree `29cb248a8d320607e21424c68625c4af6a949da1`.
Complete authority/lease checks before numerical imports and repeat both
at worker and coordinator finalization.

After the clean freeze, a fresh immutable resource request must bind the
new coordinator's exact command and a fresh external output directory.
Obtain administrator APPROVED status, acquire that exact ID, execute once,
and release in finally after the complete tree terminates. No automatic
retry, authority alteration while active, or reuse of a consumed ID.
The two known consumed IDs are explicitly rejected even while terminal
accounting for the last observation remains pending. Claims from another
runner also reject reuse. A permanent exclusive claim belongs to this run.

The previous notification was blocked by the communication permission
reviewer. Do not bypass it with another transport or direct ledger edit.
This implementation does not itself authorize resource execution.

## Runtime and failure preservation

Use one Windows Job-contained child with one numerical-library thread,
24-GiB complete-tree memory limit, 600-second child ceiling and 300-second
CPU/checkpoint inactivity threshold. The coordinator has an 890-second
watchdog. Existing whole-tree termination/drainage is reused unchanged.
No global resource lane runs concurrently. Flush scalar progress events.

The optional failure observer retains the **last successful evaluation**,
which may be a rejected line-search candidate. It is not necessarily the
last accepted Newton iterate, an accepted target, or a committed state.
Record its positions, frames, loads/reaction, origins, response, residual,
evaluation count and explicit UNCOMMITTED_DIAGNOSTIC_ONLY disposition.
The sink receives a detached deep copy and cannot alter solver state.
No successful evaluation means no fabricated snapshot. On success no
failure observer runs; default and successful trial bytes remain unchanged.
Sink failure blocks publication instead of hiding absent diagnostics.

For the new runner, reconstruct a captured failure response from its actual
last evaluated internal coordinates and fixed origins before serializing.
Require exact response replay, without requiring the failed state to pass
global equilibrium and without committing it. Bind the snapshot separately
as failed_last.json, never target.json. A later diagnostic can inspect this
state without rerunning merely to recover missing numerical arrays.

Strict canonical JSON rejects duplicate/nonfinite data. Validate exact
packet keys, case/origin identities, accuracy schema and allocations,
station ordering, raw hashes, clamp/reaction values, residual reconstruction,
event/checkpoint agreement and initial-state digest. Require a snapshot when
progress proves a successful evaluated target state existed. These are
author integrity/replay checks, not an independently authored mechanics
oracle or a proof of global qualification.

## Outcome and next boundary

A complete diagnostic has schema GE_BEAM3_P5_FORCE_ACCURACY32_DIAGNOSTIC_V1
and disposition RESEARCH_FORCE_ACCURACY_COMPARISON_CAPTURED. Its explicit
solver_outcome is TARGET_CONVERGED or FAILED. Both may be valid captured
observations; neither means the beam is qualified. Process, authority,
malformed evidence or snapshot/replay failure yields only blocked diagnostics
and preserved partial logs, never a completed diagnostic or aggregate.

Convergence supports further bounded refinement evaluation. Failure directs
analysis to the preserved state, including residual evaluation precision,
without relaxing acceptance or automatically trying again. A later onset
grid or broader qualification requires separate scope and fresh authority.

Only two-element disposable fixtures run during harness validation. No new
32-element execution, resource approval, integration or publication occurs
as part of this preparation. B2/B3/Q4/S3 and all defaults remain unchanged.

Pre-freeze validation: **193 small unit/regression tests passed in 39.90
seconds**. This includes snapshot isolation, successful/failed captures,
rehashed mutations, authority/lease guards, simulated resource failures,
current historical file hashes and prior byte/source-identity fixtures.
The initial hand-transcribed observation hash was corrected against the
actual preserved file before validation. `git diff --check` passed, with
the exact five-path extent and no production-source changes in this step.
No independently authored scientific review is claimed.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
