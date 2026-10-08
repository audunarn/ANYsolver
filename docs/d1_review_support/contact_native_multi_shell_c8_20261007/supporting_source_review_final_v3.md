# Multiple native/S3 final supporting source review

## Disposition and binding

Complete bounded source review: **implemented but numerically unverified**. No confirmed remaining consequential source blocker in the reviewed slice after the repairs below. No imports, tests, builds, numerical jobs, product edits, Git, workers or other-repository access by reviewer. Same-family support only; no independent engineering acceptance or release.

Final author source_check_v3 and pending manifest_v3 bind the files below; all12 current listed hashes match. The pending manifest/runner is preparation, not execution authority or a PASS. Original supporting_source_review_v1 and its findings are preserved unchanged.

## Reviewed global equations and paths

One system has unique native node/frame coordinates, per-element physical cell frames/resultants, and one shell DOF vector per distinct FEModel. Each structural S3 triangle scatters actual formulation K/M ONCE, including unselected faces and shared nodes; body-global coordinates are reused by every pair. Native local42 maps are Boolean gathers/scatters, so repeated beam/target selections contribute force/tangent without duplicating structural mass. Native bodies must each be connected; cross-body native node aliases, model/body aliases and duplicate pair selections refuse. Actual authoritative coordinate-count preflight happens before native preparation/dense allocation and is checked against final layout.

Both-body contact residual and all native/shell crossblocks enter the same stage. Native own Hessian is spatial-work converted; the full midpoint chart and finite native inertia remain inherited. Shell rotations retain zero mass but genuine offset-skin work; no child stepping, local condensation, lagged force or rotary/trace inertia. Endpoint projection solves global algebraic equilibrium at fixed physical endpoint. Shell momentum gathers actual node slots, preserving insertion-order independence; native/shell elastic, translation kinetic and normal penalty storage are separate.

The dimensional physical-sample map A is constant under admitted native zero lift and affine shell W. Both row/column absolute sums are bounded by B=max(4,1+2|offset|/L), hence ||A||2<=sqrt(||A||1 ||A||infinity)<=B. A27-component max error eps gives ||A^T dg||2<=sqrt27*B*eps; a27x27 max entry error eps gives ||A^T dH A||2<=27*B²*eps. Zero lift eliminates native geometric curvature and rotational contact/spatial correction error terms. Per-pair reserves divide the global limits by contributor count and these factors; final mapped witnesses are aggregated and checked against unchanged global E/F/K limits. Row AND column/zero-curvature fixtures exist, but these remain quadrature estimators, not independent continuum-error qualification.

Selected whole native curves stay inside explicit offset top triangles. Physical exterior edge identities differ from internal artificial patch transitions; neither gets an edge force or feature-union switching. Initial/direct restore admits actual signed gap/side/rim and all structural skin orientations. Both actual previous->stage and stage->projected endpoint legs use inherited exact Bernstein/rounding-enclosure path proof for every selected pair; all unselected structural triangles additionally certify both-leg orientation/area. Shell massless rotations participate in both legs. All work/certification replay derives from saved unknown/predecessor and actual stage/endpoint; initial and endpoint physical shell translations bind the declared contract.

One operation ledger spans inherited initialization/trial/restore preparation callbacks. Geometry, recursive integration and swept visits debit before work, across all contributors/legs and repeated checks; failed work is retained. Per-path saved counts are deterministic deltas, enabling exact replay. Long prefixes that exhaust explicit admission caps refuse; no hidden per-pair cap renewal. Transactions retain inherited candidate/current/issued rollback and atomic publication.

## Findings resolved and discriminating source checks

1. Original all-rim-to-internal-transition reporting was false for exterior edges. It now emits honest UNADMITTED_SELECTED_PATCH_BOUNDARY with complete selected-face exterior/internal edge inventory; accepted records carry that inventory. Separate exterior/internal refusal assertions exist. No nearest-edge classification is invented.
2. Original owner orientation refusal could occur before geometry debit. Owner geometry now debits before W/exact normal work; work adapter likewise debits before fingerprint/skin and uses the private leaf predebited protocol to avoid double charging. Direct leaf calls still debit themselves. Invalid orientation requires used geometry1; default None retains historical branch/fingerprint equations.
3. Lead-owned repairs add authoritative allocation preflight and a distinct NativeTransientS3ContactPair, preserving the older static NativeS3ContactPair API. New public exports are additive.
4. A subset-of-existing-pairs regression now retains the unselected structural triangle and checks unchanged K/M/maps plus both unselected orientation legs and exact cap refusal. This resolves the previously missing source fixture; it is unexecuted.

Inherited connected and single-shell source hashes are unchanged from their prior frozen candidate. Optional None leaf paths keep old calling arithmetic and fingerprint fields. The prepared default-None/ledger comparison checks output equality and identity, but comparison of two calls in the new source is not historical installed-artifact/capsule byte parity. Historical legacy compatibility remains a prospective requirement.

## Missing execution and claim limits

Ten selectors are prepared, none run: structural/shared mass; full210 two-epsilon tangent and isolated contact/work; dimensional map/error bounds; genuine coupled response; fresh full/split restart and authenticated tamper; aggregate-cap refusal; internal/exterior/inverted-skin paths; topology/aliases/mutation; cancellation/rollback/common native map; default-None/old owner compatibility. Precancellation and injected path refusal are source regressions, not measured in-flight active-contact cancellation.

The restart selector defaults to genuine fresh producers. Its optional saved-producer branch is only comparison/tamper work: guarded source/candidate and digest binding must come from authentic successful public producer jobs. Matching saved records alone does not establish accepted producer completion; terminal provenance and frozen install/runtime must be reviewed when execution is authorized.

Build/install/binder, installed public example/CLI, effective runtime/resources, all mechanics/descriptor convergence, genuine saved continuation/tamper and historical default byte parity remain pending. No numerical execution authority is inferred from this source review or prior single-pair evidence. Different-family assessment and broader temporal/spatial/section/native friction/finite-shell/curved-reference/feature-union/mixed beam-beam plus beam-shell qualification remain open. No exact energy or angular momentum invariant is claimed.

## Exact reviewed final file hashes

- `src/anysolver/_ge_beam3_native_multi_shell_contact.py` — `725691d2cc757d1e8cef6a5c28c666d5eb58c043254a20421c462cba82eeda25`

- `src/anysolver/general_contact/native_transient_multi_shell.py` — `1c0e459e6fde7b5f0b80cf62e0086cec90c23cd0f22e63e826abf5848bb658b1`

- `src/anysolver/general_contact/native_retained_line_s3.py` — `1be5799466e08e97eae80237732512756339fc23074f6de63f93f833fe1b16cb`

- `src/anysolver/general_contact/native_retained_line_s3_work.py` — `cc02f7dafe47cceb025a93c477380832004b2291db11b281f18e922d47aba18c`

- `tests/test_general_contact_native_transient_multi_shell.py` — `ad93fa71038d9833f45363ea76103afa526cf82742f1f6cbc15dff58b819e106`

- `examples/general_contact_native_multi_shell_impact_dev.py` — `f55b35fa78d15c6d17c7f58d93ba5b22214393f086e2fde101e7bf8e3735e52a`

- `docs/GENERAL_CONTACT_NATIVE_MULTI_SHELL_TRANSIENT_DEV.md` — `b5f71ca1451ea5a95b964bf580a617e5c24bb21faaecda4ebccf0e28a60e8997`

- `src/anysolver/general_contact/__init__.py` — `d766137752d5436387bbf6e45e4e28be41dbffb371bfbc505b5e97a94befc117`

- `src/anysolver/_ge_beam3_connected_dynamic.py` — `fc479d74504544e02a3f86145f7c7a7c63aa1baee620b37a4227f83140c792d6`

- `src/anysolver/_ge_beam3_connected_trajectory.py` — `f6869a6c67908767b70612b3b893cdc4d4aeaf1c1100893b0c2fc4b054db9e19`

- `src/anysolver/_ge_beam3_native_shell_contact.py` — `791447c155f4b45db21fcb6ff4f7cd7bafcfdfd25ebd246d743eace5b7284bf6`

- `src/anysolver/general_contact/native_transient_shell.py` — `0cbbb335e71cb0a82a0e94cc58e4e51b0f0d7483a9947afe7975da52279d8d27`

Source check SHA256: `4e00b706930c10d211204138771d6ceb27a405ef1797464d15c9d06d40de616b`.

Pending manifest SHA256: `e63546a4c498daa539943eff9a8be867433e6c92e94a3ee517899136f7ddce54`.

Author final handoff SHA256: `faae223f566ec39b267a7d5d4c6558f7fed3a1eaac374ceb95f3673efec02ef8`.

Preserved original review SHA256: `bb0052003b8ce404cfa33875f860e7510af75a5a03420cc049f2428420457095`.
