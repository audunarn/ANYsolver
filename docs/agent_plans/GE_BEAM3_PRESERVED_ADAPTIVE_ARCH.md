# Preserved adaptive arch: staged validation successor

Base: 394030cf30c9980609ef9319a19d0d8c4b18ec97.
Freeze exactly this plan and tests/test_ge_beam3_preserved_adaptive_arch.py.
No production source, mechanics, source programme, bounds or tolerance changes.

Bind the blocked adaptive continuation status SHA-256
8BAAA4DE3FD5DE70C6F98BE658B297DB7254C00AC5F28BF25D8A2EA7E26F42A9.
Its archive binds two completed solver checkpoints whose enclosing processes
were interrupted during subsequent validation. The original gate remains
BLOCKED_GE_BEAM3_PROCESS_OR_EVIDENCE. This successor is not a worker retry,
new continuation, or reclassification of that gate.

## Two separate inventories

1. Five archive-reader mutation tests: hash, byte count, duplicate, missing
   file and path traversal. No mechanics.
2. Two preserved checkpoint assessments: cycle-a-arch and cycle-b-arch.
   Authenticate their input/result/checkpoint files and the complete earlier
   rehearsal reference output set against exact manifest byte counts/hashes.
   Reconstruct the original programme, but never call solve_adaptive_arc.

Every assessment performs full existing decode_checkpoint accepted-history
and predictor/equilibrium replay, seven-snapshot/source-prefix verification,
canonical wrap roundtrip, actual adaptive schedule .12/.12/.24, all three
states' native physical recovery at 128 stations, zero plastic history,
constitutive checks, BVP9 reference field comparison and native/continuum
slope checks. All original bounds/tolerances apply unchanged.

The field/comparison calculation is a same-author copy of the frozen
continuation test, not an independent oracle. The entire seven scientific
files must match the completed rehearsal byte-for-byte. Origin/binding and
non-reclassification statements are stored separately in a receipt.
Independent review remains PENDING.

## Execution

One clean frozen rehearsal per inventory; only after both pass, two fresh
invocations per inventory. Require byte-identical scientific files and receipts
within each inventory between rehearsal and repeats. At most three workers,
one numerical-library thread, 24 GiB process tree, 600 seconds child wall,
120 seconds CPU inactivity, 1800 seconds per wave. No automatic retries.

The supervisor distinguishes WALL_DEADLINE and CPU_INACTIVITY, records elapsed
and accounting before and after termination when available, waits for tree
cleanup, and preserves stdout/stderr even on failure. Child and supervisor
return codes are both required for acceptance. Runtime values are external.
All outputs use exclusive creation in new external directories. Preserve
partial evidence on failure; create no passing assessment from partial files.

## Outcome boundary

Success: PASS_DEVELOPMENT_PRESERVED_ADAPTIVE_ARCH_VALIDATION_ONLY.
Failure: BLOCKED_GE_BEAM3_PROCESS_OR_EVIDENCE or a recorded concrete failed
scientific check; never fabricate missing assessment or retry automatically.

Success establishes full replay/recovery checks for these already-produced
checkpoints, not two new complete continuation cycles, production
qualification, or universal postbuckling stability. Both original interrupted
processes remain failed. Do not widen the old checkpoint size/time limits,
skip accepted-history replay, or substitute a trusted summary for mechanics.

This avoids repeating approximately nine minutes of continuation merely to
perform its remaining checks. After this bounded validation, prioritize
native physical mass/modal/prestress/buckling and the other full-goal gaps.
Keep B2/B3, Q4/S3, defaults and historical qualification evidence unchanged.
