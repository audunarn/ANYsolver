# Explicit bounded native history profile

Base 62eb65901c15aac05a2230f2952b1b74b0ce7b40. The eight-macro checkpoint is
1181530 bytes; a sixteen-macro three-target chain is estimated above the old
2-MiB cap. Add an explicit private GE_BEAM3_NATIVE_GENERALIZED_HISTORY_8M_V2
profile, not a global limit change or an omission of history.

Default programmes omit the new field from descriptors and keep their original
schemas and canonical bytes. Explicit profile programmes bind the ID in their
descriptors, outer checkpoint and nested combined-state envelope, each with a
distinct HISTORY8M_V2 schema. The caller selects the profile; decoders never
infer it from untrusted data. Reject cross-profile restart even for small files.

Keep the shared historical P5 parser and 2-MiB constant unchanged. The new
argument-local parser allows at most 8 MiB only for the exact selected ID,
canonical ASCII, depth 32, duplicate/nonfinite rejection and exact re-encoding.
External SHA-256 verification remains before native state evaluation. Individual
state parsing and the full combined-chain validator remain unchanged, including
65 snapshots, model extent, complete genesis/predecessor/origin/seed/rotation/
load/equilibrium checks and the 60-second validation deadline.

Change only the two private programme descriptors/validation, three checkpoint
envelopes, the new capacity helper, its tests and this plan. Do not alter beam,
shell, section, residual/tangent, recovery, shared solver mechanics or defaults.
The existing native numerical and process controls remain unchanged.

Rehearse strict parser/size and two-thread profile isolation; test an explicitly
synthetic 3-MiB parser payload without claiming a larger mechanical checkpoint.
Exercise real native translation and arc solves under the selected profile,
exact prefix restart, resealed profile/schema/programme/genesis/hash mutations,
accepted-prefix preservation on live profile mutation, and unchanged validation
deadline. Decode/re-encode the original archived default bar checkpoints and
require exact bytes. Then freeze and run two deterministic replicas. Keep the
original local/safety suites as separate regression inventories and compare
their default scientific outputs to the archived runs, not just test counts.

Every child uses one numerical thread, 24 GiB Windows Job tree, 600-second wall
and 120-second CPU-inactivity limits; at most three workers and 1800 seconds
per wave. No automatic retry. Preserve failures before correction. A real
sixteen-macro smoke is a subsequent capacity/accuracy check, not presumed
passed by parser tests. No independent review, production qualification,
default activation, package/version change, push or release is claimed here.
