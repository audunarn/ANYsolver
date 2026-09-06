# P5 assembled dynamic restart development

Parent `16eeafd4eb44a5f8966efb44b99df38b4f26e77f`, tree
`e5d96c6b535939c173f3ec2364ea1a575ceb565e`.
Add a research codec, tests and this plan only. Preserve all prior mechanics,
evidence, dynamic state/step implementations, public APIs and defaults.

## Wire and authority contract

Use an explicit dynamic-assembly restart schema, not the old static-history,
backward-Euler, single-macro midpoint, legacy B3 or production record schemas.
Canonical ASCII JSON has sorted keys, compact separators and one trailing
newline. The five top-level keys are schema, identity, state, accepted and
payload_sha256. Reject duplicate keys, nonfinite numbers, coercion, unknown or
missing fields, invalid shapes/rotations, oversized input and excessive nesting.
Limits: four MiB and depth 32; all array entries are JSON floats, never bools,
strings or silently coerced integers. Epochs are bounded integers.

Identity binds the expected model/layout hash, connectivity, references and
material triads, elastic and inertia matrices, quadrature order, clamps, shared
deformation-rotation convention, retained cell inertia, method/state schemas,
the explicit implementation-source hashes, Python/NumPy versions, platform,
machine and numerical-thread environment. No module, class, path or constructor
is selected by payload data.
Caller supplies a known expected model; loading constructs a separate clean
model from its reference/section/inertia inputs, never overwrites that caller.

Store the entire ChainState and last accepted ChainTrial, including its full
origin, increment, step, nodal forces, stage/endpoint fields, element forces,
velocities and solver metadata. An epoch-zero record must be the exact freshly
constructed reference/rest initial state with no accepted step. Explicit
nonzero initial-velocity/predeformation authority is a future extension, not
inferred from arbitrary private state. For later epochs, check epoch/time
linkage, origin model/clamps and algebraic endpoint equilibrium. Origin epoch
zero must match the fresh initial state. Reconstruct the saved step using the
existing bounded replay, require exact canonical receipt/state agreement, and
only then return the restored model.

Checksums provide integrity and identity, not authenticity or proof of all
earlier load steps. A record cannot claim qualification or replace scientific
evidence. These research snapshots require the same bound implementation and
runtime profile; they are not a cross-version production migration scheme or
an exact external dependency-graph attestation.

## Atomicity and publication

Reject exports with pending trials, corrupt checkpoints or failed replay.
Validate export through fresh-model loading. Loading failures expose no staged
model and do not alter the expected caller, even if the final element fails.
Preserve the existing 600-second replay/endpoint operation bounds; no global
time-stepping or load-history replay is launched, and nothing retries itself.

For file export, validate the bytes first, write a unique same-directory
temporary file, flush/fsync it, and create the destination exclusively using a
hard link. Existing destinations must not be overwritten. Remove only the
codec's own temporary file. This is exclusive publication on the supported
filesystem, not a claim of power-loss durability. Tests use fresh disposable
directories, not historical or canonical qualification evidence paths.

## Verification

- Initial and accepted-state exact canonical round trips.
- Uninterrupted versus restored curved multi-element loading/unloading and
  reversal, with byte-identical accepted receipts and continuation snapshots.
- Fresh-process load/re-export using the same frozen code/runtime.
- Rehashed velocity, rotation, time, origin, stage, endpoint, element force,
  layout, source/runtime and solver metadata mutations must fail.
- Duplicate/nonfinite/depth/size and strict schema/type rejection.
- Identity/hash mismatch rejected before mechanics replay; foreign methods,
  changed sections/inertia/geometry/clamps and pending models fail closed.
- Late replay failure is atomic; exclusive output preserves existing files
  and leaves no partial destination after an injected publication failure.

Only small correctness tests run here; no resource request or formal
qualification cycle. Native material-state/dynamic solver integration,
broader engineering validation, independent review and beam-shell coupling
remain necessary for the full production goal.

## Observed development result

Initial canonical round-trip, continuation and fresh-process smoke selection:
**3 passed in 19.05 seconds**. The restart, dynamic assembly and preserved
single-macro midpoint regression then passed **91 tests in 91.72 seconds**.
A subsequent code review added an explicit structural chronology check: epoch
zero requires time zero, and positive epochs require positive time, for every
decoded state including nested origins and stage guesses. The final restart
suite, including both added chronology tests, passed **49 tests in 37.04
seconds**. Do not report these different runs as one combined test count.

Uninterrupted and restored three-step continuation after the first accepted
step produced byte-identical accepted receipts and snapshots through reversal,
unloading and reloading. The resulting graph reaches epoch four/time 0.08
with nonzero retained cell angular velocities. A fresh Python process loaded
and re-exported exactly the same checkpoint bytes. Rolled material triads,
a four-macro graph and a free graph also round-trip without losing nodal or
cell velocities or reference authority.

Strict byte/depth/schema/type checks, nested duplicate-key rejection, rehashed
state/velocity/stage/endpoint/origin changes and source/runtime/model mismatch
tests pass. An inconsistent later origin is rejected before accepted-step
replay, rather than silently equilibrated. Positive-epoch/zero-time records
are rejected before mechanics. Pending exports, changed expected models and
unregistered private initial velocities fail closed. Injected late replay
failure leaves the caller unchanged. Exclusive file publication preserves an
existing destination and removes only its own staging file after failure.

No mechanics or qualification evidence was rerun as a formal campaign. Only
small correctness tests and one explicitly bounded fresh-process codec check
were used; no resource request was created or reused. `git diff --check`
passed. Exactly this plan, the new codec and its test are added; all prior
tracked files, production paths and defaults remain unchanged. The runtime
binding is an explicit research profile, not a full binary/dependency graph
attestation. No production restart capability or qualification is claimed.

## Next required work

Provide an explicit, validated initial-condition protocol for nonzero nodal
and cell velocities and admissible predeformation, including consistent shared
algebraic traces and a bound initialization record. Do not weaken this codec
to infer such authority from privately modified epoch-zero state. Follow with
native solver/material-state integration and broader engineering/independent
qualification. This checkpoint is progress toward, not completion of, the
full straight/curved production beam and beam-shell connection goal.
