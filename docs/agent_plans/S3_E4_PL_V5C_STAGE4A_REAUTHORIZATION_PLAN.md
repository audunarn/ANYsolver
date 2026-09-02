# S3 E4-PL V5C Stage 4A reauthorization

## Scope

Reauthorize the immutable 81-record flat mixed-flexural Stage 4A protocol for
the accepted source-relaxed V5B MIN3 candidate.  Historical V2A evidence,
including aggregate `47CD9DEF9AC306635C16B662ECBF3628324350CCC80803D1AC586BC0A22D60F1`
and its 38 failures, remains final and is not reclassified or rerun.

The candidate is
`CANDIDATE_E4_PL_S3_V5B_MIN3_RELAXED_FLAT_LINEAR_SCREEN_V1`.  Its local
operator and relaxation are frozen by the accepted V5B result.  V5C adds no
mechanics; it reconstructs the Stage 4A energy-norm evidence omitted from the
smaller repair funnel.

## Coverage and decisions

For each slash, backslash, and alternating diagonal, execute N20, N40, and N80
for the all-Q4 baseline and both dispersed and chain masks at 1%, 5%, 10%, and
25% S3.  This is exactly 27 records per diagonal, 81 records total, and 24
mixed sequences.

Retain the frozen Stage 4A gates:

- response slope at least `1.80` and no more than `0.15` below all-Q4;
- energy-norm one-sided 95% slope lower bound at least `0.90`;
- successive response error factor no greater than `1.02`;
- finest response-error ratio no greater than `1.25` through 10% S3 and
  `1.50` at 25% S3;
- solve residual no greater than `1e-8` and producer/checker record identity
  no greater than `3e-12`.

Terminal precedence is:

1. `BLOCKED_E4_PL_S3_V5C_STAGE4A_PROCESS_OR_EVIDENCE`;
2. `NO_GO_E4_PL_S3_V5C_STAGE4A_MIXED_FLEXURAL_CONVERGENCE`;
3. `PROVISIONAL_GO_E4_PL_S3_V5C_STAGE4B_PREPARATION`.

A pass authorizes only preparation of a separately frozen Stage 4B gate.  It
does not authorize S3 activation, production registration, default changes,
or package publication.

## Bounded execution

Run one producer shard per diagonal, at most three concurrently.  Run two
independent checker replicas for every shard, with at most three checker
processes concurrently.  Execute two fresh-directory cycles and require
byte-identical shard proofs, checker replicas, and canonical aggregates.

Every child receives one numerical-library thread, a 24-GiB process-tree
limit, and a 600-second wall limit.  The complete wave is limited to 1,800
seconds.  Terminate complete process trees on failure, never retry
automatically, use exclusive outputs, and preserve failed diagnostics outside
canonical evidence.

Use diagonal equilibration, one reused sparse LU, and two residual-correction
solves.  This process-only stabilization preserves the assembled matrix,
loads, supports, reference field, and scientific thresholds.

## Production boundary

ANYmesh is untouched.  Qualified Q4 mechanics and
`DEFAULT_Q4_FORMULATION="e4-pl"` are unchanged.
`DEFAULT_S3_FORMULATION="legacy-s3"` remains unchanged.  Every outcome retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
