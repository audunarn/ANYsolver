# S3 E4-PL V5E Stage 4A spatial-response correction

## Purpose

Run the complete 81-record mixed-flexural Stage 4A campaign with the spatial
nodal transverse-displacement relative L2 norm required by the governing
companion-element plan.  V5D established, without changing mechanics, that
the historical centre-point sample loses asymptotic meaning through local
error cancellation at four 25% topologies while spatial displacement and
energy continue to converge.

V5C remains an immutable NO-GO under its frozen protocol.  V5E is a successor
protocol, not a reclassification and not a tolerance or formulation change.

## Frozen campaign

For slash, backslash, and alternating diagonals, reconstruct N20, N40, and N80
for the all-Q4 baseline and dispersed/chain masks at 1%, 5%, 10%, and 25% S3.
Produce exactly 81 records and 24 mixed sequences per cycle.  Each record
contains the spatial `uz` L2 and L-infinity errors, shell-rotation L2 error,
energy-norm error, historical centre-point diagnostic, residual, and frozen
connectivity/reference hashes.

The response gate uses spatial nodal `uz` relative L2 error at every node,
including exact-zero supported boundary nodes.  Retain without change:

- response slope at least `1.80`;
- response-slope deficit from all-Q4 at most `0.15`;
- successive response error factor at most `1.02`;
- finest response-error ratio at most `1.25` through 10% and `1.50` at 25%;
- one-sided 95% energy-slope lower bound at least `0.90`;
- producer/checker identity `3e-12` and solve residual `1e-8`.

The centre-point metric is reported but cannot classify V5E.  No coefficient,
reference field, topology, support, load, tolerance, or scientific record is
changed.

## Execution and adjudication

Use two fresh-directory deterministic cycles, three diagonal producer shards
concurrently, and two independent checker replicas per shard with no more
than three checker processes.  Each process tree receives one numerical
thread, 24 GiB, and at most 600 seconds; the complete wave receives at most
1,800 seconds.  Do not retry automatically.

Terminal precedence:

1. `BLOCKED_E4_PL_S3_V5E_STAGE4A_PROCESS_OR_EVIDENCE`;
2. `NO_GO_E4_PL_S3_V5E_STAGE4A_SPATIAL_CONVERGENCE`;
3. `PROVISIONAL_GO_E4_PL_S3_V5E_STAGE4B_PREPARATION`.

The provisional terminal authorizes preparation of a separately frozen Stage
4B gate only.  It does not authorize S3 activation.

ANYmesh, qualified Q4 mechanics, public APIs, and defaults are unchanged.
`DEFAULT_S3_FORMULATION` remains `legacy-s3`; every outcome retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
