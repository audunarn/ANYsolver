# S3 V6R Cross-Implementation Gate-Decision Agreement

V6R is an evidence-only successor to the immutable V6Q process block.  It
binds the 18 completed V6Q correction-cycle-2 production proofs and runs only
the independently authored equation checker.  Production mechanics are not
executed.

For each of the six 25% sequences, V6R computes the accepted spatial gates
twice: once from the frozen production proof and once from the independent
reconstruction.  Exact record IDs, topology hashes, reference hashes, case
ordering, formulation identity, and threshold definitions must agree.  Both
solve residuals must remain below `1e-8`.  Producer and checker decisions must
agree for every unchanged threshold, and both must have zero formal failures.

The inherited `3e-12` raw derived-metric reproduction result remains recorded
as failed and nonclassifying.  V6R does not loosen it or use a replacement
numeric tolerance; it instead compares the registered scientific decisions
on both independently calculated values.  Center response remains diagnostic.

Run two fresh evidence cycles.  Each diagonal receives two concurrent checker
replicas.  Every child has one numerical-library thread, 24 GiB, and 600
seconds; each cycle has 1,800 seconds.  No retry is permitted.

Terminal precedence:

1. `BLOCKED_E4_PL_S3_V6R_EVIDENCE_OR_REVIEW`
2. `NO_GO_E4_PL_S3_V6R_SPATIAL_GATE_DISAGREEMENT`
3. `PROVISIONAL_GO_E4_PL_S3_V6R_STAGE4B_PREPARATION`

A pass authorizes only preparation of a separately frozen Stage 4B gate.  It
does not activate S3.  Q4 remains unchanged and S3 remains legacy by default.
