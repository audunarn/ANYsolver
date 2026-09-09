# Private retained arc controller development closeout

Implementation freeze ed6d4ed2aaa8e011be2c66a8df69cd95514745ff. Final
test freeze 331c5234e5f9f3eed248f41706d779526106426e, tree
c1d533d940f83eaa83de07f466e0261d872e7160. Only the test's fixed-DOF
tuple/list indexing and its incident note changed after implementation freeze.
The failed curved smoke is preserved, not reclassified.

The new private retained frame-chord controller uses current-spatial rotation
rows, compensated translations and complete retained predictor/corrector
borders. Its separately issued state owns actual lambda, incoming predictor,
step size, origins/history and full predecessor chain. Restore recomputes each
predictor and each accepted physical/chord relation. Full remaining corrections
are mandatory; residual-only acceptance is not used.

## Separate passing inventories

| Lane | Tests | Scientific files |
| --- | ---: | ---: |
| Geometry, scalar fold and program admission | 19 | 0 |
| Actual elastic axial paths, both signs | 2 | 4 |
| Actual coupled curved transverse path | 1 | 2 |
| Replay mutation, ownership and cancellation | 28 | 6 |
| Prior translation-controller regression | 41 | 15 |

The regression's 15 files equal the preserved 12202be translation archive
byte-for-byte. Each of the four new lanes passed a rehearsal, then two fresh
process repeats. Both repeat aggregates and all per-lane scientific files match
exactly. No combined test inventory is claimed.

Cycle A: 19.390671 seconds; cycle B: 19.090656 seconds. Both peaked at three
workers. Longest repeat child: 15.377980 seconds; regression child: 33.050155
seconds. All process-tree receipts show zero remaining children, no watchdog
breach and successful cleanup. Bounds remained 600 seconds/child,
1800 seconds/wave, 24 GiB/tree, one numerical thread and 120 seconds CPU idle.
There was no automatic retry. Curved current-spatial row directional error:
6.127320872906239e-13 against the unchanged 1e-7 gate.

## Bound archive

External directory:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-arc-331c523-20260908`.
All 187 manifest entries were copied and verified; originals remain intact.

- Shared aggregate: 1841 bytes, SHA-256
  `BC1DE899F01CC75A59021B369FF24ABACE2AE605EC2C7F340F2095227BF6AEF1`.
- Archive manifest: 23195 bytes, SHA-256
  `9AB68D850D8912F7A2B208E4609316CD1DBE6D8ACEAD291E011DFBB7BC1FF3EE`.
- Audit: 10668 bytes, SHA-256
  `4D8532EAF6C9A648EF478AD66EC2EF395B8A6438BB1DB9B208EBBED993DA6796`.

## Remaining boundary

This is controller development evidence, NOT actual beam postbuckling or
plastic arc qualification. The scalar fold is only a linear-algebra/continuation
test. Next: actual curved-arch post-limit continuation against independent BVP
reference branches, including same-branch and spatial covariance checks.
Plastic active-set continuation, complete load/state/solver parity, full
environment attestation, independent review, public installed opt-in integration
and objective eccentric/curved beam-shell joints remain incomplete.

Independent review: PENDING. Full goal: ACTIVE, incomplete. No public selectors,
versions, defaults, existing B2/B3/S3/Q4 mechanics or historical evidence changed.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
