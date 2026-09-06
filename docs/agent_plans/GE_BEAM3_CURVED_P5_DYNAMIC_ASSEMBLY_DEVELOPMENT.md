# P5 shared-node dynamic assembly development

Parent `406837df73de976079803b6b4f9987749bc2f37a`, tree
`c22e626aff0fc34b6bf1555851e9ca32cd92e4d6`.
Add a research assembly, tests and this plan; preserve previous implementations,
qualification evidence, production mechanics, APIs, aliases and defaults.

## Assembly contract

Support connected graphs of one to four three-node macros with explicit,
distinct integer connectivity and exact shared reference positions. Each
element retains its own material reference triads. A shared node owns one
spatial deformation rotation V; its frame in element e is Qe=V R0e. Do not
force differing material triads to be equal or duplicate the shared rotation.
This is a beam-only welded-node research convention, not a beam-shell joint.

State owns global nodal positions, V matrices, nodal translational velocities,
and two cell rotations/angular velocities per element. All cell spins retain
inertia. Nodal rotation traces have exactly zero inertia. Clamp whole nodes
only; permit free-body tests. Accept spatial dead nodal forces only, assembled
once globally rather than once per incident element. No follower work,
material histories, production restart codec or automatic step retry.

Use the preserved single-element midpoint stage kernel, never its local
endpoint trace solve or local trial/commit. Scatter stage forces, inertia and
full analytic Jacobians into the common global increment vector. Solve free
stage equations globally. At the endpoint, hold all nodal positions and cell
rotations fixed and solve the assembled free nodal trace equilibrium. Shared
endpoint moments may be nonzero elementwise; their global sum must balance.
Keep stage and endpoint element forces in the replayable receipt so a hidden
independent-element solve or omitted shared contribution is detectable.

## Transactions and safety

Use a distinct state schema/model hash binding connectivity, each frozen
reference/section/inertia/order identity, global coordinates and clamps. Trial
does not commit child models. Commit freshly recomputes every stage and
endpoint, checks the full receipt and previous state, then replaces the whole
model checkpoint in one assignment. Discard, foreign/modified receipts,
nonconvergence, dirty model identities and failures in later elements leave the
committed graph unchanged. No element-local partial commit is permitted.

Bounds: 16 global Newton updates, 128 evaluations, ten line-search attempts;
endpoint traces eight updates, 64 evaluations, ten line-search attempts.
Step is positive and <=0.1; existing 0.9-pi and relative-frame guards stay
active. Stage and global endpoint trace norms use 1e-11 with declared length
scaling. A 600-second operation watchdog checks at each element evaluation.
No automatic retry/cutback. Future heavy waves still require separate resource
requests and ledger approval. Current tests are small correctness tests only.

## Checks

- One-macro agreement with the preserved midpoint implementation.
- Two/four-macro reference effective matrix against the existing full-inertia
  chain stiffness/mass construction at matching quadrature.
- Nonzero-increment assembled analytic Jacobian and scatter/work identities.
- Shared stage/endpoint moment balance with individually nonzero incident
  moments, including different material reference triads at a common node.
- Curved coupled multi-step replay, observer covariance, free translation.
- All-or-nothing commit including injected failure in the last element.
- Receipt/hash/input mutations, invalid graphs, bounded failures and watchdog.
- No changes to previous research/production paths.

Success is a development checkpoint, not multi-element dynamic qualification.
Independent mechanics checking, broader temporal/engineering comparisons,
material-state parity, native solver/restart integration and beam-shell
connections remain required for the full production beam goal.

## Development incident retained

The initial six-test smoke selection had four passes and two assertion
failures (ordinary and rolled shared material triads). The new test compared
raw endpoint moment norms directly with 1e-11, instead of the already declared
moment/reference-length normalization. Raw norms were
1.7146445692246643e-11 and 1.6942892486344635e-11; the reference length is 2.
The implementation's normalized values therefore satisfied the declared
criterion. Correct only the new test to divide by reference length and compare
its reconstructed norm with the receipt. No solver convergence threshold,
mechanics, reference field, input case or historical test is changed. This
test-authoring failure is not silently omitted or called a scientific NO-GO.

## Observed development result

After the normalization assertion correction, all 17 focused tests passed in
21.02 seconds. Additional checks cover an actually loaded four-macro step,
reordered element enumeration, altered scatter slots and norm scale, and
invalid steps/clamps. The final assembly, single-macro midpoint, finite-inertia
and full-inertia modal-chain suites passed **80 tests in 60.58 seconds**.
The new assembly suite contains 22 tests; the other 58 tests are preserved
regressions. These are small correctness tests, not a performance campaign.

Reference effective matrices match the existing full-inertia chain pencils
for two and four macros at matching 24-point quadrature. The nonlinear
development steps use explicitly selected order 8, matching the preserved
single-macro midpoint tests. No claim that those orders are interchangeable
for arbitrary geometry/sections is made. The assembled nonzero-increment
analytic Jacobian passes the unchanged 1e-7 directional check. The independent
scatter/work calculation confirms that nodal loads are applied once globally.

At a shared node, each incident stage and endpoint moment is individually
nonzero, while their assembled sum meets equilibrium. This also holds with
different material reference triads on the two elements. Cell elastic moments
are balanced by retained cell inertia, and nodal traces have exactly zero
inertia. Observer covariance, free uniform translation, curved three-step
loading/reversal/unloading and fresh receipt replay pass. A loaded four-macro
step retains all eight cell rotations and angular velocities.

No child model commits a dynamic step. Injecting a last-element failure during
commit leaves the complete graph checkpoint unchanged. Rehashed force,
endpoint-part, state and metadata mutations, changed element identity, altered
scatter layout or normalization scale, foreign trials and failed bounded
steps are rejected. Discard permits an explicit new trial with the same
deterministic receipt; this is a unit test, not automatic retry of a consumed
resource request. The watchdog rejection also preserves the checkpoint.

Exactly this plan, the new assembly module and its test are added. All
previous tracked files remain unchanged relative to the parent; no mechanics,
qualification evidence, production routing, package, dependency or defaults
are edited. No resource request, canonical qualification aggregate, push,
merge, tag or release is produced. Same-author checks are not independent
scientific review, and the production beam goal remains incomplete.

Next: strict restart/continuation of the assembled dynamic state, including
shared deformation rotations, retained cell velocities, the complete accepted
origin/receipt, exact model/layout identity and fail-closed cross-method/schema
handling. Native solver/material-state integration and broader assembled
dynamic qualification remain separate required work; none is implied by the
small tests reported here.
