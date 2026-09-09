# Actual-preload Euler point-wave closeout

Frozen implementation: `6536b4c10e330a3702825fe5847cd3e3aac4bebf`.
Tree: `1c10e3773879e339f7a8246152db25fd6939ec94`.
Branch: `codex/ge-beam3-curved-moment-reference-v1`.

The registered straight clamped-free Euler reference subset passed two complete
external cycles. This closes this reference case only, not spatial postbuckling
or overall beam qualification. No B2/B3/Q4/S3 mechanics, defaults, dependencies,
package metadata or public routing changed. The six-path scheduler freeze has
no `src/` delta from `60e42facb4013866dafec8239755dcf87180adea`.

## Scientific scope and separate inventories

Each of N1, N2, N4 and N8 uses 22 actual retained nodal Newton preload solves:
four initial loads and eighteen bisections. Each mesh produces 45 scientific
files: 22 accepted-state checkpoints, 22 point packets and one bracket record.
Every point starts from virgin genesis and uses targets (0.5, 1). Accepted
preloads are not manufactured axial states. The original two bending-family,
exact-support axial/torsional, F/EA, reaction and N1 paired-spectrum checks are
unchanged. The finest gate is a relative Euler-load error below 2%.

| Macrocells | Relative Euler-load error |
| --- | ---: |
| 1 | 0.051120758056640625 |
| 2 | 0.011745452880859375 |
| 4 | 0.002063751220703347 |
| 8 | 0.000339508056640736 |

The N8 error is approximately 0.034%. Errors decrease over the tested meshes;
this does not prove asymptotic exactness or general buckling qualification.

Separate passing test inventories:

- Scheduler/protocol/process containment: 29 tests.
- Existing partition checks: 6 tests.
- Disposable output/failure mutation checks: 7 tests, preserved externally.

The N1/N2/N4 rehearsal matches the prior monolithic scientific bytes exactly.
The N8 development run also completed and was audited before the repeats.
Neither development run counts as a complete repeat cycle.

## Complete cycles

| Cycle | Wave seconds (diagnostic) | Longest child seconds | Peak workers |
| --- | ---: | ---: | ---: |
| A | 893.6209144 | 40.2974251 | 3 |
| B | 887.1024825 | 39.5066445 | 3 |

Both waves completed sequentially, with all child process trees empty. Each
child retained a 600-second limit, 24-GiB tree memory limit, one numerical
thread and 120-second CPU-inactivity protection. Each wave remained below
1800 seconds. No worker was retried.

The two canonical aggregates are byte-identical: 24,321 bytes, SHA-256
`3543E8193EB6D394BA1D4D6A9B3D7F9C8AB2202B9DEA2E7C0434F7A748B27686`.
All 45 scientific files for each mesh match between cycles and the development
baseline. Full assignment, transcript, checkpoint and point-output hash DAGs
were revalidated after restart; no mechanics was rerun for this closeout.

## Preservation

Archive root: `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/`.

- `ge-beam3-euler-points-6536b4c-complete-20260908/archive-manifest.json`:
  139,942 bytes, SHA-256
  `6331A22BE4E8EE751B29A5765DB2E728589E0CA77987EB5175F971A4495CC273`.
- Its `agreement.json`: 35,991 bytes, SHA-256
  `7F92B3BD85AC566C49E501F02CC3B4AA63150594328C887AF09D9B93CF1B816B`.
- All 1,275 manifest entries verified against archived file bytes and hashes.
- Development archive `ge-beam3-euler-points-6536b4c-evidence-20260908`:
  manifest 77,834 bytes, SHA-256
  `054E0C89E288C990C5FCF562FAAF0E9A18C830FD1C350CAFA849439D3C747805`;
  audit 18,668 bytes, SHA-256
  `6ED96A8CAD0C049ABAFA79B747F1078FB37060F48F21E143FECD7A9D0CAE1E75`.

The original cycle directories, historical failures, raw logs, point proofs,
source snapshots and earlier archives remain intact. The archive creator was
not rerun after restart. No publication, merge or activation is authorized by
this record.

## Next gate and remaining work

Implement a distinct retained generalized displacement/arc-control protocol.
Preserve accepted load factor separately from physical control targets; do not
reinterpret or weaken the existing force-controlled history schema. Use the
full bordered Newton system with residual, compatibility and remaining-correction
checks, fixed accepted material origins across rejected trials, and complete
state ownership/replay. Establish bounded straight analytical and curved/coupled
port checks before broader arch/post-limit testing.

Full curved/spatial postbuckling, nonlinear/fibre parity, practical scale,
public FEModel/state and installed opt-in integration, complete environment
attestation, independent review and objective eccentric/curved beam-shell
connection qualification remain open. Independent review is PENDING.
`production_qualified=false`; full goal remains active and incomplete.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
