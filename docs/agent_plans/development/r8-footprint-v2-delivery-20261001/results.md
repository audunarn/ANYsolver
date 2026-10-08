# V2 footprint chart and consumer delivery — 1 October 2026

The experimental selected-node footprint workflow now has an explicit ANYfem V2
input route: construct, preflight, save/reopen, finite solve, physical recovery,
chart reset, checkpoint, fresh-owner restore and continue. The old V1 schema,
default numerical route and chart guards are preserved. This closes the pending
development slice; broader F06/M4 and programme acceptance remain open.

## Solver assessment and evidence reuse

Product is unchanged from reconciled source `d31e09dc`, wheel SHA256
`a80d4a862b2155292baf385549d430baa22865056b5343ee8454cd8fa8a11435`.
The [main reconciliation record](../r8-main-reconciliation-20261001/results.md)
binds 391 source/wheel/site modules, GE141 and the other installed impact checks.
Its independent review covers all 20 V2 predicates, role-scaled actual-update
derivatives, detached ownership, fixed accepted predecessors, atomic rejection/
cancellation and fresh-owner semantic checkpoint negatives.

The independent review identified two missing explicit predicates. A bounded
supplement closes them:

- Old `6eede4913a22987bf1a5e41b428ab496dffb3298` versus current default V1:
  Q4/mixed/all-S3 preflight, linear and finite result-array hashes and accepted
  checkpoint hashes match exactly. The old artifact is
  `be63b72482e3965900c4ecb5c9eba2af984cbcaaf79b00af55e87ec587466f54`.
- Three existing four-branch tests and the public solver example now explicitly
  compare successor shell translations, normalized by 2 m at unchanged `1e-9`.
  All four installed checks pass. Only assertions changed; the solver artifact
  remains unchanged and earlier passing predicates retain their original binding.

Q4/mixed/all-S3 derivative errors are at most `2.447718e-10`, below the existing
`1e-6` criterion. No normalization floor or physical tolerance was relaxed.
Independent [solver review](solver-review.md) accepts this scoped development
assessment, including the two supplements. Historical source schema and
malformed-restore fixture failures remain in their original evidence. Two new
probe setup mistakes (context-manager use and virgin checkpoint access) are
retained alongside the corrected public-lifetime probe. They led to no product
repair.

## ANYfem delivery

Delivered consumer source is commit `bd3c9a6baa3ffff2a34b72829491e87c058c4443`
on `codex/experimental-ge-panel-consumer`, based on `f4bb5ed2`. Its exact product
content matches the final artifact; no unrelated files changed.

`ExperimentalGENodalRigidFootprintPanel` has a keyword-only explicit chart
policy. V2 uses `anyfem.experimental-ge-nodal-rigid-footprint-chart-panel-v2`;
V1 emits its original fields. Strict parsing owns nested inputs, rejects policy/
schema mismatches and unsupported material/load/support combinations, and
delegates physical admission to the public solver owner. Standalone and ordinary
explicit mesh-native Project persistence use the existing GE selector. Preflight
failures retain exception identity and close the owner.

Installed candidate wheel
`a1e5157d1a47804f5a09fafb9846dee76beffea18971a1b5845bd618602b356f`
passes 87/87 checks: 27 new predicates, existing footprint/Project coverage and
the public example. All 98 consumer modules and 391 solver modules match their
source/wheel/site bindings; 278 observed imports are onsite. Supervised elapsed
time is 39.857 s, sampled process-tree peak RSS 209,567,744 bytes.

A review-requested docstring correction clarifies V1/V2 selection. ASTs after
removing docstrings are identical. Final consumer wheel
`4aca099800620016ca8967b1283bf7c4f6e3f0ad5034dafae4b929dbfc749a2a`
has fresh 98-module bindings and 13/13 installed framing/persistence/example
checks; 277 observed imports are onsite. Earlier 87-pass behavior evidence is
reused by the verified docstring-only difference, retaining its own artifact
identity. Old/current saved V1 consumer records also match exactly across all
three layouts. The public documentation states the experimental scope.

The consumer Q4 test explicitly compares four successor branches. Mixed/all-S3
consumer tests establish reset/restore/continue, equilibrium and recovery; their
four-branch physical comparison is solver evidence. [Consumer review](consumer-review.md)
records these distinct applicability limits and no blocking finding.

## Limits, resources and tiered execution

Scope remains unstaged elastic generalized beams and elastic Q4/mixed/all-S3
selected-node footprints, no weak lines, each shell rotational triple fully
fixed or fully free. Normal spin is locked. This is neither distributing nor
continuous-area/weld/drilling-independent qualification. Plastic footprint
transport, broad large-rotation history, stability/capacity, mandatory external
references, practical scale and aggregate gates remain open. The shared ABC
metadata guard issue remains with its existing maintainer.

Numerical checks were serial, supervised at 600 s/8 GiB, with actual BLAS/Numba
one thread and JIT disabled. Reported costs are observations, not speedup claims.
The user requested tiered execution prospectively. The local configured worker
performed seven successful read/lookup tools but timed out at 120 s before its
conclusion; its task is incomplete. Mistral failed at launcher startup before
inference. Failed/partial outputs are retained. Independent OpenAI reviews
supply the completed reviews; no alternative-model-family claim follows.

Raw evidence working directory:
`C:/Users/AUDUNA~1/AppData/Local/Temp/r8-footprint-v2-delivery-20261001-v1`.
[Archive](raw-v1.zip) SHA256
`29cd18fdd95733e8a0bb61868a84d6cd070268a50652c21f5a13be10f8ee50dc`
and [inventory](raw-v1-identity.json) bind 2,608 files, each reread from the zip
and checked against its digest. Artifacts, source snapshots, exact runners,
fixtures, outputs, failures and local-worker tool/permission logs are preserved.
Installed directories/caches and the full global-provider config are excluded;
effective local model routing was inspected as `ollama/qwen3.8:27b`, with the same
helper model, sharing disabled and agent steps5. Its unfinished audit is not a pass.
No release/version/default or main merge was performed.
