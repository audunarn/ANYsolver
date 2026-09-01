# S3 E4-PL V5D response-metric diagnosis

## Purpose

Diagnose, without reclassifying V5C, why four 25% Stage 4A sequences fail the
centre-displacement slope gate while every energy-norm and finest-error-ratio
gate passes.  The V5C NO-GO and all V5B mechanics remain immutable.

## Frozen diagnostic

For slash, backslash, and alternating diagonals, reconstruct N20, N40, and N80
for the all-Q4 baseline and dispersed/chain masks at 10% and 25% S3.  Produce
exactly 45 records and 12 mixed sequences.  Recompute:

- the historical centre-displacement relative error;
- the spatial nodal transverse-displacement relative L2 and L-infinity errors;
- the two shell-rotation spatial relative L2 error;
- the discrete stiffness energy-norm error;
- solve residual, physical response, connectivity, and reference hashes.

The spatial displacement norm uses every nodal `uz` value, including the
exact-zero supported boundary, and is normalized by the corresponding frozen
Mindlin reference vector.  It is not fitted to V5C output.

An independently authored checker reconstructs the V5B relaxed operator and
all spatial fields without importing the diagnostic producer.  Producer and
checker records must agree within `3e-12`; residuals remain bounded by `1e-8`.

## Adjudication

Retain the same `1.80` response-slope and `0.15` all-Q4 slope-deficit limits,
the same one-sided 95% energy-slope lower bound `0.90`, and the same finest
error-ratio limits.  Do not weaken V5C or substitute a passing metric after the
fact.

Terminal precedence:

1. `BLOCKED_E4_PL_S3_V5D_PROCESS_OR_EVIDENCE`;
2. `NO_GO_E4_PL_S3_V5D_HIGH_FRACTION_SPATIAL_CONVERGENCE`;
3. `UNCLASSIFIED_E4_PL_S3_V5D_RESPONSE_METRIC_PROTOCOL_REPLACEMENT_REQUIRED`;
4. `UNCLASSIFIED_E4_PL_S3_V5D_DIAGNOSIS_INCONCLUSIVE`.

The protocol-replacement terminal requires all four V5C failing sequences to
pass both spatial-displacement and energy convergence while reproducing their
centre-slope failures, and all 10% controls to pass.  It authorizes only a
separately preregistered V5E Stage 4A protocol correction using the spatial
displacement norm required by the governing companion-element plan.  It does
not authorize Stage 4B or activation.

## Execution and boundary

Run two fresh-directory cycles, three diagonal producer shards concurrently,
and two independent checker replicas per shard with at most three concurrent
checkers.  Each process tree receives one numerical-library thread, 24 GiB,
and at most 600 seconds; the complete wave receives at most 1,800 seconds.
Never retry automatically.

ANYmesh, qualified Q4 mechanics, public APIs, and defaults are unchanged.
`DEFAULT_S3_FORMULATION` remains `legacy-s3`; every outcome retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
