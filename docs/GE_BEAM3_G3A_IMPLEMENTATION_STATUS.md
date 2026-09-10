# G3a native graph implementation

Status: **IMPLEMENTED_DEVELOPMENT_ONLY_AWAITING_INDEPENDENT_REVIEW**.

Branch: `codex/ge-beam3-g3a-native-graph-v1`.
Parent fixture freeze: `e78c1b667694b43141912c1d85f894de2b41a848`,
tree `ec23282230399da6a5c882f025f1bf53b16bc52b`.

This is the G3a / S15 and native S18 implementation, not a formal G3
confirmation or public integration. The historical G3 fixture freeze remains
unchanged, including its historical planning-only status. Current development
results are separately recorded in
`reference_cases/ge_beam3_g3a_development_v1.json`.

## Implemented boundary

- A private `NativeGraphAnalysis`, not a G1/G2 subclass or a collection of
  nested owners. One native rotation store owns every node's Q; each incident
  exact-elastic element keeps its own triads, stationary variables and recovery.
- Exact native `ElasticElement` and `GraphConstraintSet` classes only.
  No legacy beam, shell, unknown subclass or cross-family rotational adapter.
  Straight exact-midpoint references only in this slice.
- Up to eight elements, 32 actual nodes, 192 external DOFs and 384 combined
  external/internal coordinates. Admission validates incidence, duplicate and
  orphan nodes, midpoint ownership and all component rigid spaces before
  model/state construction.
- Deterministic sorted node/element traversal through the unchanged native
  assembler. The actual COO cache is hash-bound, and CSR ordering is checked
  against reversed insertion and independent local-operator scatter.
- A separate bounded graph constraint capture retaining G2's exact affine
  expansion and analytic physical-orientation/relative-pose equations.
  Accepted G2 node bounds and schema are not widened. Native remote pose
  ties use the same shared owner, not a cross-family adapter.
- Constrained Newton, noncommuting targets, external line forces/couples,
  physical reactions and native station recovery use unchanged element laws.
  The G3 tests compare actual full stationary and condensed systems, including
  nonzero internal residual and load work, and actual KKT directional derivatives.
- Guarded cancellation, immutable DOF authority, exclusive owner use, final
  callback and last-element preparation checks retain the accepted graph prefix.
  Explicit G1/G2 solve dispatch is rejected before evaluation.
  Store identity is bound and fallible progress output precedes publication.
- Native-only `GE_BEAM3_G3_GRAPH_ELASTIC_RESTART_V1`, bounded to 8 MiB and
  128 accepted entries. It binds graph policy/empty adapter allowlist, sections,
  triads, ordered constraints, native internals, poses, load/target journal and
  runtime. External digest, strict JSON and exact replay are required.
  Existing G1/G2 or mixed envelopes are not migrated.
- `reference_rhs` uses an ephemeral multi-RHS factorization only at a virgin,
  homogeneous reference state. There is **no persistent numerical factor cache**,
  no cross-epoch reuse and no speed claim. The topology cache remains guarded.

## Development coverage and corrections

The first N_BRANCH3 smoke reached admission and rejected FEModel's built-in
unused default material. This was a new guard inventory bug, not an element
defect. The guard was corrected to admit the exact expected material-key set;
the failed log is preserved. The corrected smoke then passed.

The initial 50-test graph rehearsal passed. Before the final rehearsal,
store-identity binding and prepublication progress logging were hardened and
eight tests were added. The resulting mechanics inventory contains 58 tests;
these development tests are not an independent implementation review.

Native coverage includes N_BRANCH3, N_RING4, N_BRACED5 and N_DISJOINT2,
their component/cycle identities, rigid nullspaces/positive quotient, sorted
assembly, five-step loading/unloading, restart continuation, native recovery,
prescribed-root work, global rotation/translation, renumbering/reversal,
multiple RHS, malformed graph/constraint/restart rejection and atomic failure.
Additional native remote-pose branch construction is compared with shared-node
construction. G1, G2 and five standard-library boundary checks are separate
inventories; do not combine their counts into a qualification total.

The development runner creates exclusive external directories, uses one
numerical-library thread, a 24-GiB process-tree job, 600-second child deadline
and 120-second CPU/output inactivity check. It has no automatic retry.
Development waves run at most three concurrent children; the recorded final
wave is below the frozen 1,800-second wave bound. A future formal coordinator
and evidence schema still require independent review before formal execution.

## Preserved boundaries and next gate

All parent-tracked files remain byte-bound and unchanged, including accepted
G1/G2 owners, element/operator laws, sections, public APIs, recovery, existing
beam/shell mechanics, Q4/S3 defaults, packaging and historical evidence.
No other repository or main branch is modified. The unrelated ANYmesher plan
in the root checkout is preserved.

**Next gate:** independently review the exact G3a implementation commit and
test coverage, correct any findings with regressions, then freeze/review the
G3a confirmation runner and run two bounded fresh-directory formal cycles.
Only accepted scoped G3a evidence may close its native graph obligations.
G3b mixed translation graphs, G3c positive cross-family pose adapters, G4
history-bearing sections and G5 public routing remain separate gates.
