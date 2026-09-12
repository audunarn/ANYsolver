# G3b safety audit: formal confirmation blocked

Frozen subject: `0eb2fca2d47a18070b625c0a4689c408a0ea88d6`,
tree `04bfd0a186839107ae7b387240e548a8b7042215`.

This is the implementation author's local adversarial audit, **not** the required
independent implementation review. Permission to delegate a separate reviewer
was requested; no independent review is claimed here.

## Reproduced findings

1. **G3B-LR-01 (P1): uncaptured native recovery dispatch.** A preparation callback
   replaced native cell recovery between the two M_Q4 RHS solves. The second
   result's native strains/resultants were doubled. The owner accepted and
   published that result, but a fresh graph rejected the new checkpoint during
   replay. Capture all invoked recovery/validation boundaries and object
   identities, with callback-boundary rejection before publication.
2. **G3B-LR-02 (P2): late result-schema rejection.** Removing a required stored
   displacement field reached one replay solve before rejection. No restored
   owner was returned. Exact family-specific nested result schemas must be
   validated for the complete journal before owner creation or replay.

Neither finding permits changing beam/Q4/S3 mechanics or recovery equations.
The normalized resultant difference in the first probe was
0.0015994860594858507; this is a deliberate callback-corruption reproduction,
not a spontaneous scientific element failure.

## Evidence and preservation

The two probes ran in one isolated process with one numerical thread,
24 GiB memory, 60-second wall and 30-second inactivity safeguards.
Completion: 2.727 seconds, peak 191,037,440 bytes, exit 0, no active children.
Process success means the probes completed, not that the candidate passed.

Probe source, stdout, stderr and process record are preserved externally with
byte counts and SHA-256 in the canonical five-key local audit record:
`reference_cases/ge_beam3_g3b_local_safety_review_v1.json`.

All four original source bindings and 39 archived development files were
reverified. Prior passing development records remain immutable. No formal
cycle, authority, qualification certificate, implementation correction or
mechanics rerun was performed. Main, defaults, production elements and other
repositories are untouched.

## Next gate

Create a scoped correction successor: close both findings, add regressions
covering all five reference families and accepted-prefix failure/replay, then
obtain independent implementation review. Only after acceptance freeze the
formal G3b runner, exact inventories and evidence schema, and perform the
bounded two-cycle confirmation. This audit does not qualify G3b.
