# Retained guard optimization and actual-preload Euler progress

Latest implementation: `c50361b4b38a9fcfe1e516d18cae1d8c26757492`.
Optimization rehearsal: `16bef8b32375426c361b65bc8782539ba6afce7c`.
Pre-optimization Euler freeze: `65e4be3f5288670161345d8a5b0db8090ee545ce`.
Worktree: `C:/Github/ANYsolver/.perf2-worktrees/ge-beam3-curved-moment-reference-v1`.
Branch: `codex/ge-beam3-curved-moment-reference-v1`.

## Completed implementation and verification

Only the private retained Context guard changed. It constructs the full sparse
supported transformation once per Context, then retains full model, support
audit, program/load and deadline checks at every callback. It does not cache
acceptance on object identity. The captured DOF count's type and value are
checked explicitly. Element-provided constraint equations are included in the
live audit. Existing state ownership and replay checks remain intact.

No element/section equations, loads, interpolation, quadrature, numerical
coefficients, tolerances, recovery, serialized identities, B2/B3/Q4/S3,
public selectors, defaults, dependencies or package metadata changed.

Separate rehearsal inventories at 16bef8b:

- Guard tests: 14; scientific files: 0.
- Diagnostic profile: 1; two numerical output files plus timing/profile data.
- Nodal-load suite: 22; scientific files: 19.
- Distributed ports: 6; scientific files: 18.
- State ownership: 10; scientific files: 0.
- Modal suite: 20; scientific files: 29.
- Historical state guards: 22; scientific files: 5.
- N1 Euler search: 1; scientific files: 45.
- N2 Euler search: 1; scientific files: 45.
- N4 Euler search: 1; scientific files: 45.

All passed. The nodal/port/modal/state-guard outputs match their bound archive
exactly. All N1/N2 scientific bytes match the pre-optimization version, including
each actual Newton checkpoint, factor packet, spectrum and final bracket.

The same diagnostic N2 point used 2 sparse support constructions instead of
3546. Profiled time decreased from 10.505678 to 8.402129 seconds. Its numerical
checkpoint and packet/modes are byte-identical. This is a single instrumented
sample, not a statistically established general performance claim.

All 22-point actual-preload searches through N4 passed unchanged criteria:

| Macrocells | Child seconds at 16bef8b | Relative Euler-load error |
| --- | ---: | ---: |
| 1 | 42.495 | 0.051120758056640625 |
| 2 | 93.801 | 0.011745452880859375 |
| 4 | 243.316 | 0.002063751220703347 |

Errors decrease with refinement. Each point uses actual retained nodal Newton
loading from virgin genesis, not a manufactured accepted state. Both bending
families are checked; the exact-support axial/torsional checks remain active.
The 2% finest gate is registered at N8, which has NOT run.

The final type-guard correction at c50361b has separate passing inventories:

- Guard tests: 15; scientific files: 0.
- Nodal-load suite: 22; scientific files: 19.
- Modal suite: 20; scientific files: 29.
- N2 Euler search: 1; scientific files: 45.

All 93 scientific files match the 16bef8b archive exactly. The final N2 child
took 86.211 seconds. N1/N4 were not rerun after this type-only correction;
their preserved evidence remains explicitly bound to 16bef8b.

Every invocation completed with clean pre/post source guards, under 600 seconds,
24 GiB and one numerical-library thread. Peak overlap was three workers. The
16bef8b wave spanned 558.950476 seconds. All process trees are empty; no run was
retried, no canonical partial qualification aggregate was produced.

## Preserved archives

All below are under
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/`. Originals are intact.

- `ge-beam3-retained-euler-partial-65e4be3-20260908`: manifest 16025 bytes,
  SHA-256 `CE3CB44587311AC1CF88725CDF9AC95D3EA413C82D767D3BE14B91D2AAD87779`.
- `ge-beam3-retained-guard-16bef8b-20260908`: manifest 32910 bytes,
  SHA-256 `ECCAEF6F8E79A3FFC41E866362C16832ACF8677557A768767779AFFA2129CAE1`;
  audit 27827 bytes,
  SHA-256 `EF4E76E6FFD8A34E72760C82C2B175348B8C4B3EDCB638BD3489359AA26206E0`.
- `ge-beam3-retained-guard-c50361b-20260908`: manifest 14405 bytes,
  SHA-256 `2760DD3F39F5CBD7707A5EE0A79DD4D4F64B6970E947FC78F28917C22D5AFFD4`;
  audit 12144 bytes,
  SHA-256 `16B5E18D365BCBBDC0C0F7D7EE54813AB77F8B6464EEEF44FA6C9137C7623EF0`.

Exact source/test/plan snapshots, supervisors, receipts, logs and numerical
outputs are included and per-file copy-verified. External staging scripts remain
at `C:/Github/ANYsolver/.perf2-worktrees/.ge-beam3-retained-euler-transfer-20260908`.
Do not rerun archive creators against their exclusive destination directories.

## Next implementation gate

Avoid a monolithic N8 launch: measured N2-to-N4 scaling leaves inadequate margin
under 600 seconds. Freeze a research-only bounded point/segment scheduler for
the SAME 22-point protocol, not a different scientific search. Extract a shared
point evaluator and preserve exact operation ordering and canonical outputs.

Bind each assignment to source, geometry count, exact preload/index, prior
search transcript and the initial axial/torsional-family proof. Every launched
point still performs its actual Newton solve. Validate the previous hashes and
derive the next bracket deterministically; no skipped/retried points or synthetic
accepted states. Persist exclusive raw point/state records; aggregate only a
complete validated search. Prove scheduler byte parity against saved N1/N2/N4
outputs before N8. Keep 600 seconds/child, 1800 seconds/wave, 24 GiB/process tree,
one thread and at most three workers, with progress and CPU-inactivity checks.
Then perform N8 and the two complete deterministic refinement cycles.

## Full goal remains active

This is private development, not production beam qualification. Still required:
complete prestress refinement/repeats, broader curved/postbuckling engineering,
nonlinear/fibre material parity, practical model scale, public FEModel/state
integration, independent review, full environment graph, installed opt-in class,
and objective finite-rotation eccentric/curved beam-shell connection qualification.
The separate connection worktree and concurrent ANYmesh work remain untouched.
No publication, merge, default activation or overall completion is claimed.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
