# N32 extended branch: preserved deadline failure

Frozen implementation b2d15e295874711be9cd89f606f5f48a13e00949, tree
f40e1d75f1914bb3bd0bdd3f06840b0ea155b7fe, remains historical authority.
Disposition: incomplete process gate, not a demonstrated mechanical contradiction.
No source, target, tolerance, context deadline or completed evidence was changed
during execution. No consumed worker was retried.

## Actual execution and preservation

Twelve of the 23 registered workers launched. Four enrollment workers and all four
first-target workers passed. All four second-target workers returned native
`failed`, cursor 1, with `RuntimeError: retained generalized context deadline`.
The existing 120-second context guard operated within the 600-second child cap.
The full launched wave took 572.094543 seconds, with at most three concurrent
workers and peak process-tree memory 213676032 bytes. Every launched process has
a terminal receipt and empty child tree. Coordinator session 55414 exited 1.

Same-sign enrollment and first-target replicas are byte-identical across every
output file. Each failed second-target output retains its actual first-target
checkpoint byte-for-byte, with matching recomputed native state hash:

| Sign | Checkpoint bytes | SHA-256 |
| --- | ---: | --- |
| plus | 346490 | 6d6d4790cff22761f2c04f0fcc9172630eebbf49f386f4b540047984e223b226 |
| minus | 346435 | 0346eac1dc8ca714df7a56c06761531a3f147800a9492b3cc769d114b5da3eff |

No third-target, cancellation/resume or final fresh-owner replay worker launched.
No complete branch aggregate exists. The saved partial successes cannot substitute
for those unexecuted gates. The last accepted targets are +/-0.0075, starting
from the original +/-0.0065 equilibria, not a loading path from rest.

External archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-n32-branch-b2d15e2-20260909`.
Its 101 entries plus canonical manifest include raw outputs/logs, exact launch
commands, terminal receipts, source helpers, 11 earlier saved-prefix mutation
checks, the full saved audit and the additional failed-prefix/replica audit.
Manifest: 13837 bytes, SHA-256
586fa4cf92e5e12a1fb12c8334aafd41f79b9f245b62534b2bc1df9478808be5.
Both staged and external copies were verified by exact extent, byte count and
SHA-256. The archive and original temporary output are preserved; neither may be
used as a fresh execution root.

## Next gate: measure before optimizing

Source inspection identifies plausible redundant work, not yet a measured
profile: physical Context constructs and certifies a virgin initial record;
seed Context then certifies its nonzero genesis; restore mechanically replays
each prior record. Inner operator callbacks repeatedly recompute the full model,
section/DOF, constraint and programme identities. The existing compliance snapshot
optimization applies only to modal preparation, not nonlinear assembly/recovery.

Prepare a separately frozen, bounded profiling diagnostic for enrollment and
accepted-prefix restoration. Measure call counts and cumulative time for full
guards, construction, assembly and recovery, without replaying a consumed failed
branch command. Preserve the original context and process limits. This diagnostic
must not classify a scientific result or alter accepted checkpoint bytes.

Only after measurements should a successor optimize redundant authority work.
Retain full input validation before and after immutable computations, deadline and
cancellation safe points, exact state ownership, mechanical replay semantics and
all mutation rejection. Do not weaken checks by caching mutable object identities,
resetting timers, tuning target values or relaxing tolerances. A successor needs
tests for mutation/cancellation/error paths and byte-identical scientific outputs
before a new frozen branch gate in fresh directories.

## Scope retained

The earlier N32 six-mode comparison and full native inertia remain valid within
their recorded scopes. Their +/-0.0065 equilibria each have one negative direction;
they do not establish stable postbuckling. New target accuracy/stability, the
remaining branch lifecycle gates, broad nonlinear/fibre and solver parity,
independent-author review, opt-in integration and objective beam-shell connections
remain unfinished. The overall beam goal stays active.

No B2/B3/S3/Q4 mechanics, defaults, public selector, version, tag, merge or release
changed. No new independent-author review is claimed.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
