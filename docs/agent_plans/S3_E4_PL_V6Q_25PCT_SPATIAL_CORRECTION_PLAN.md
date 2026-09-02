# S3 V6Q 25% Spatial-Response Correction Gate

## Purpose

V6P is preserved as a genuine execution record, but its nine formal failures
were produced by the center-point response metric.  Accepted V5D/V5E evidence
had already shown that this metric is cancellation-prone and nonclassifying.
V6Q therefore rechecks only the affected 25% holdout on the exact frozen V2D
candidate with the accepted `NODAL_UZ_RELATIVE_L2` response metric.

## Frozen scope

- Three diagonals: slash, backslash, and alternating.
- Two masks: dispersed and chain.
- Three levels: N20, N40, and N80.
- Exactly 18 current-candidate scientific records per cycle.
- Independent all-Q4 reference reconstructions at the same three levels.
- Center-point response is retained as a diagnostic and cannot classify V6Q.
- Existing V6P energy and non-response gates are not rerun or reclassified.

The exact V2D candidate archive and ANYfileIO support archive are extracted in
fresh worker directories.  The producer imports the frozen candidate only
after validating all authority inputs.  The independently authored checker
reconstructs the published source equations and does not import production
S3 mechanics.

## Execution bounds

Run two fresh-directory cycles.  Each cycle launches one producer per diagonal,
with at most two producers concurrently.  Each producer and checker process is
limited to one numerical-library thread, 24 GiB, and 600 seconds.  Each complete
cycle is limited to 1,800 seconds.  Checker replicas run together and must be
byte-identical.  There is no automatic retry.

## Decision

Terminal precedence is:

1. `BLOCKED_E4_PL_S3_V6Q_PROCESS_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V6Q_25PCT_SPATIAL_CONVERGENCE`
3. `PROVISIONAL_GO_E4_PL_S3_V6Q_STAGE4A_PROTOCOL_CLOSED`

A pass closes only the corrected Stage 4A response protocol and authorizes a
separately frozen Stage 4B gate.  It does not activate S3.  Qualified Q4 remains
unchanged and `DEFAULT_S3_FORMULATION` remains `legacy-s3`.
