# GE Beam3 G6 remaining-domain parity contract

## Scope

G6 closes the frozen P01--P32 and U01--U10 legacy-parity inventory after the
accepted G1--G5 gates. Existing evidence is hash-bound and reused; no accepted
mechanics campaign is rerun. The local GE-B3 potential, interpolation,
condensation, SO(3) update, quadrature, section work, and qualified Q4/S3
mechanics are immutable inputs.

The only newly admitted behavior is integration around the explicit
`ge-beam3` selector: initial-field state ownership, reference-linear dynamics,
beam-segment contact, accepted-boundary activity/deletion, the reviewed
objective pose joint, bounded sparse/session use, actual limit-point behavior,
and explicit ANYfem/ANYstructure consumers. Existing aliases and defaults do
not change.

## Row disposition

Every P row receives either accepted GE evidence or a demonstrated
legacy-B3-unsupported disposition. Every U row receives a source/test-backed
non-obligation. B2-only tests do not establish a B3 obligation until a direct
B3 substitution passes. Shell-only follower, thermal, release, contact, or
dynamic routes never establish beam parity.

Finite-velocity finite-rotation dynamics, gyroscopic terms, curved-reference
geometry, capacity-based beam damage, and a general stable-postbuckling claim
remain unsupported. Reference-linear Newmark/contact behavior and actual
limit-point continuation are distinct and may be qualified.

## New integration lanes

1. Reconcile all 42 frozen rows against accepted evidence and direct B3
   baseline probes.
2. Verify initial fields, point/edge mass, damping, prescribed linear history,
   contact/fracture, activity and hard deletion with authenticated rollback.
3. Expose only the identity-bearing objective beam-shell pose joint; exercise
   sparse assembly, multiple RHS, sessions, cache invalidation and actual
   limit-point continuation.
4. Add persisted opt-in GE-B3 policy and exact provenance to ANYfem and
   ANYstructure. Missing policy remains legacy. ANYmesh and ANYintelligent are
   outside this gate.

## Execution

Development uses targeted tests. Formal work consists of one complete G6
rehearsal and two formal cycles; G1--G5 and the 375-history G3c campaign are
not rerun. Each child has one numerical-library thread, 24 GiB, 600 seconds,
and a 120-second inactivity watchdog. At most three children run together and
each wave is capped at 1,800 seconds. There is no automatic retry.

Scale fixtures contain 64, 256 and 1,024 straight elements. Large dense
eigensolves are forbidden. Performance uses one warm-up and eleven short
alternating-order samples; it may report only median, MAD and p95. Existing
B2/B3 hot paths may regress by at most five percent. A GE batch kernel is not
required.

## Decision

Terminal precedence:

1. `BLOCKED_GE_BEAM3_G6_BASELINE_OR_AUTHORITY`
2. `BLOCKED_GE_BEAM3_G6_PROCESS_OR_EVIDENCE`
3. `NO_GO_GE_BEAM3_G6_LEGACY_ROUTE_DISPOSITION`
4. `NO_GO_GE_BEAM3_G6_STATE_LOAD_OR_DYNAMICS`
5. `NO_GO_GE_BEAM3_G6_CONTACT_OR_ACTIVITY`
6. `NO_GO_GE_BEAM3_G6_JOINT_OR_CONTINUATION`
7. `NO_GO_GE_BEAM3_G6_SCALE_OR_PERFORMANCE`
8. `NO_GO_GE_BEAM3_G6_ECOSYSTEM`
9. `PROVISIONAL_GO_GE_BEAM3_FULL_LEGACY_DOMAIN_PARITY_OPT_IN`

Success qualifies the explicit straight GE-B3 selector against actual legacy
domain capability. It does not authorize a default, version, tag, publication,
or broader finite-rotation dynamics claim.
