# P5 sampled lateral-onset probe — development checkpoint

Parent: `d1ac769dac6a6b87e48593450ceed6675ae9aeeb`, tree
`ff3f9aae795d216729ba1fd44fa1daaead3f59c9`.
This increment contains only the research onset probe, its tests and this
record. It does not change the displacement controller, finite-element
operators, section law, source equations, prior evidence, production code,
selectors or defaults. The GE-B3 programme remains unqualified.

## Fixed search and interpretation

The planned refinement meshes are 4, 8 and 16 elements, within the existing
explicit assembly envelope. Each mesh has a fixed crown-drop grid
`0, 0.005, ..., 0.060`. Every grid state is evaluated even if an earlier
sample has a negative odd eigenvalue. A solve failure propagates without
cutback, retry, interval extension or a replacement state.

Only the earliest adjacent positive/negative pair preceded by exclusively
positive sampled lowest lateral values is refined. There are at most sixteen
bisection evaluations, stopping at bracket width `1e-7` or an unresolved
midpoint sign. Each midpoint starts from the saved accepted positive-endpoint
state, using the already tested single-translation controller. All other free
spatial coordinates remain in equilibrium. An unresolved midpoint leaves the
last sign-separated endpoints intact; it is not silently assigned a sign.

Each value is interpreted with the unchanged sampled-inertia inspector's
backward-error uncertainty band, including reflection cross-block coupling.
This is numerical uncertainty, not a rigorous interval. The entire
conservative force-controlled Hessian is classified; neither the controller's
reduced matrix nor its reaction derivative replaces that Hessian. Full,
in-plane and lateral spectra and lowest nodal mode vectors remain in raw
diagnostics. Rotational scaling remains the reference span, not physical mass.

The outcomes distinguish an unresolved reference state, no observed grid
crossing, an uncertain grid sign, a localized sampled sign bracket, an
uncertain midpoint and exhausted bisection budget. None establishes the first
critical point, uniqueness between samples, continuum accuracy, natural
frequencies or production qualification. The search deliberately makes no
claim about a hidden crossing between positive sampled endpoints.

## State and diagnostic preservation

Each state must satisfy the controlled target exactly, the full physical
residual at `1e-11`, fixed end constraints, planar reflection, proper rotation
matrices and the pure crown dead-load pattern. Elastic histories must remain
elastic. Existing accepted-origin commit and replay are both checked.

Raw records retain the complete trial, physical state checks, full tangent,
spectra, sample ID and accepted origin ID. A callback publishes each raw
record and returns its binding. Deterministic result records retain those
bindings and the complete sampled/refined search history. Publication integrity
is the future runner's responsibility, not a claim made by this callback API.

The module has no numerical import at import time, CLI, lease acquisition,
resource-request creation, automatic aggregate publication or execution
authority. A separately frozen runner is required before a larger campaign.
The existing consumed arclength and continuum requests remain consumed.

## Disposable tests performed

- New probe suite: **28 passed in 2.78 seconds**. Synthetic tests cover
  bounded sampling/bisection, accepted-state origins, uncertainty boundaries,
  no extension/retry, budget exhaustion, multiple observed crossings without
  uniqueness claims, malformed/mutated data, deterministic serialization and
  deferred numerical imports.
- The suite includes only a two-element, three-state mechanical smoke at
  drops `0, 0.005, 0.010`. It checks raw full matrices and mode dimensions,
  accepted replay and state checks. It is not a root-location study, mesh
  convergence result or external scientific certificate.
- Unchanged controller and sampled-stability regressions: **36 passed in
  7.32 seconds**. Pytest then reported a permission error in its shared
  temporary-directory atexit cleanup (`pytest-current`). The tests exited
  successfully; no historical temporary directory was removed or repaired.

## Next gate — not executed by this checkpoint

Prepare and test the external coordinator/worker and strict raw validator.
Before numerical imports, bind the clean candidate commit/tree, source and
environment identities, fixed search contract, and both preserved
knot-resolved continuum endpoint packets:

- Stride 1: 29,126 bytes, SHA-256
  `64C47952DACD030D81EC3A631744179C300C33052551E1EBE5C16A9E191019FC`.
- Stride 2: 29,139 bytes, SHA-256
  `A7917C813953D181DF20748C5E54179E0F84597585650B641FBD46B90E8F073C`.

Validate bindings again at finalization. Preserve previous continuum and
discrete evidence unchanged. Report discrete drop/load brackets against the
continuum endpoint data with observed numerical uncertainty; do not invent
engineering accuracy acceptance or infer accuracy from mode correlation.

For the resource run, obtain a fresh administrator-approved request, acquire
only its exact ID, execute its stored command once and release in `finally`.
Use fresh external directories, exclusive records, one numerical-library
thread per child, at most 24 GiB per complete child tree, 600 seconds per
child and 1,800 seconds per wave. Global resource serialization applies;
there is no authorization here to overlap other resource-heavy tasks. The
runner must contain/terminate whole child trees, preserve partial logs and
never create a partial canonical aggregate on failure. It must independently
validate raw identities, search order, origins, counts, signs and hashes.

No multi-mesh onset run, new resource request, continuum re-solve, independent
review, production qualification, push, merge or activation occurred here.
Broader nonlinear material parity, physical mass/dynamics, restart,
packaging and objective beam-shell connections remain open.

NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
