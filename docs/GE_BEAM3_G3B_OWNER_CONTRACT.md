# G3b reference mixed owner development contract

Parent: 40a1cbdc971116b0b371fa7dd8e82161d249c66e.
Status: private implementation contract, not qualification or public admission.

## Closed admission

MixedReferenceOwner accepts exactly one of the five existing B2, B3, Q4,
S3 V2D or quarter-weighted Q4 reference problem types, with fresh exclusive
problem ownership. Existing helper admissions, operator assembly, family
mechanics and recovery remain unchanged. No subclass, finite program,
rotational target, shared-pose adapter, general graph or material history is
admitted. A private registry prevents two owners claiming the same problem.

## State and transaction

The owner owns a single immutable publication bundle: ordered reference loads,
their complete family results, generation and canonical checkpoint bytes.
Native 24-coordinate back-substitution and native/nonnative recovery are prepared
before publication. These are reference-linear solution snapshots, not finite
committed rotations or constitutive state. No element state store is advanced.

One call accepts one or two RHS vectors and publishes the whole batch or none.
The total journal has at most 128 entries and a checkpoint at most 8 MiB.
Preparation hooks receive only phase names and immutable preview bytes at
native_prepared, other_prepared and final_prepare. Cancellation is checked before
work and after every hook. Every callback is followed by frozen graph, operator,
dispatch, ownership, cache and accepted-bundle validation. All potentially
failing work and return-value allocation precede one publication assignment.
Reentry fails before work. A failed call leaves the previous bundle and cache
unchanged; mutation of external graph inputs is rejected, not silently repaired.

The captured Cholesky factor is private/read-only, hash-bound to the exact
reduced reference operator, graph identity, family policies, mesh epoch and
runtime/source identity. RHS reuse is only under that unchanged reference
operator epoch. Journal generation is not a finite-pose/operator update.
Each cached solve is checked against the unchanged helper solve and independent
existing stationary-system regressions; no performance claim is made.

## Restart

Use a distinct GE_BEAM3_G3B_REFERENCE_OWNER_RESTART_V1 schema, never the accepted
G3a schema. Bind graph definition, operator identity, family policy, runtime,
source identity, load policy, empty rotational-adapter allowlist, journal,
generation and all result/internal/recovery snapshots.

restore(fresh_problem, bytes, expected_sha256) authenticates the exact bytes
using an external digest, rejects duplicates, nonfinite values, noncanonical
JSON, wrong/extra/missing fields and byte/count bounds before solving. A caller
must provide a fresh exact matching reference graph; no automatic formulation
migration or reconstruction from an untrusted factory. Replay every RHS through
a new owner, compare every complete result byte-for-byte, and require the final
checkpoint to equal the input bytes. Failed replay returns no owner and releases
its provisional ownership claim. Foreign G1/G2/G3a and resealed altered results
fail closed. The digest is integrity authority supplied by the caller, not a
digital signature.

## Verification and limits

Start with M_Q4 publication/replay smoke. Then cover all five helper types:
two-RHS atomicity, load/unload/reversal snapshots, isolated owners, failed
last-family/final preparation, cancellation, stale/foreign previews, mutations
of graph/cache/dispatch/accepted data, reentry, malformed/foreign restart,
fresh replay and deterministic packets. Keep historical test bodies and
packets unchanged; extend successor path allowlists only.

Use the existing bounded runner: one numerical thread, 24 GiB/process tree,
600 seconds, 120-second CPU/output inactivity, no automatic retry. Keep lanes
separate and raw diagnostics external. No formal confirmation, merge, version,
publication, defaults or Q4/S3 mechanics changes. Independent implementation
review and a separately frozen two-cycle formal G3b confirmation remain later.
