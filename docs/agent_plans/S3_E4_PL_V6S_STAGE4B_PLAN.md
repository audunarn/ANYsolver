# S3 E4-PL V6S Stage 4B plan

## Purpose

V6S re-runs only the accepted Stage 4B modal, buckling, and paired-performance
scope against the current V2D candidate.  The historical V2C Stage 4B result
is retained as method authority, but it is not transferred as V2D scientific
evidence.  The accepted V6R result is the sole Stage 4A predecessor.

## Frozen scope

- Modal: 10 and 25 percent mixed S3, six rigid modes, first ten elastic
  frequencies, two-percent frequency and 0.95 clustered-MAC gates.
- Buckling: 10 and 25 percent mixed S3, first five factors from an eight-mode
  window, three-percent factor and 0.95 clustered-subspace-MAC gates.
- Performance: all-Q4, 10 percent, and 25 percent mixed models, one warm-up and
  eleven measurements for assembly and production solve, with independent RSS
  measurement and the existing ten-percent relative gate.
- Candidate: `CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1`, selected only through
  `e4-pl-s3-v2d`.

Each of the seven workers runs in a fresh directory with one numerical-library
thread, a 600-second wall limit, and a 24-GiB process-tree memory limit.  At
most three producer workers and four checker workers overlap.  A complete
two-cycle wave is bounded to 1,800 seconds.  No failed or consumed execution is
retried automatically.

Two independently launched standard-library checkers must reproduce every
scientific decision byte-for-byte.  Timings remain external diagnostics;
canonical evidence contains only identities, coverage, decisions, and hashes.

## Terminals

1. `BLOCKED_E4_PL_S3_V6S_STAGE4B_PROCESS_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V6S_MIXED_EIGEN`
3. `NO_GO_E4_PL_S3_V6S_MIXED_PERFORMANCE`
4. `PROVISIONAL_GO_E4_PL_S3_V6S_STAGE4B_CLOSED_ONLY`

A pass authorizes only the separately frozen V6T packaging, restart, batching,
and activation-gap audit.  It does not activate S3.  Q4 mechanics and both
defaults remain unchanged, ANYmesh is untouched, and every terminal retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
