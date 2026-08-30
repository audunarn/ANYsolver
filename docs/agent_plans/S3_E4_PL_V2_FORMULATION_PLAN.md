# S3 E4-PL V2 formulation plan

## Decision and scope

QV9 rejects `E4_PL_QUALIFIED_S3_COMPANION_V1` for default activation. Its two independently reviewed contradictions are the interface-resultant gate (240 of 240 comparisons failed) and mixed-convergence gate (47 of 63 sequences failed). The all-Q4 audit closes the analytical and Q4 reference controls and attributes the QV8 ultrathin discrepancy to binary64 global-solve conditioning, not to the reference or qualified Q4.

V1 remains available only for immutable historical replay. It must not be selected by new models, used as a fallback, or reclassified by this successor. Qualified Q4 remains unchanged. The successor formulation ID is `E4_PL_QUALIFIED_S3_COMPANION_V2`.

## Formulation

V2 will use a formulation-native triangular shell operator:

- constant-strain membrane terms;
- published discrete-Kirchhoff/Mindlin triangular bending and transverse-shear interpolation, with every equation, sign, frame, and quadrature convention hash-bound before implementation;
- the accepted barycentric E4-PL drilling constraint and basis-invariant positive drill scale;
- equilibrated physical patch recovery constructed from the V2 variational operator rather than a post-processed V1 field;
- exact condensation of internal coordinates, internal load work, mass, material tangent, and geometric tangent.

No V1 coefficient, tying equation, recovery operator, or scientific evidence may silently migrate into V2. A change to the frozen interpolation, quadrature, PL basis, drill scale, dynamic reduction, or recovery definition creates another formulation ID.

## Proof and checking

Before production coding, freeze independent producer and checker contracts for local algebra, D3 transport, director reversal, work conjugacy, recovery equilibrium, and mixed Q4/S3 interfaces. The checker must be independently authored and must not import producer mechanics. Exact or outward-certified arithmetic is required for algebraic identities and ordered signs; numerical acceptance uses preregistered norms and references.

The local proof must cover rigid modes, rank and inertia, symmetry, positive semidefiniteness on the rigid complement, condensation identities, virtual work, consistent mass, and all six D3 transports. Physical director reversal is separate from connectivity reordering and must consistently reverse thickness, offsets, layer order, coupling, moments, and recovery faces.

## Production integration

Implement V2 as opt-in first. Preserve `DEFAULT_Q4_FORMULATION = "e4-pl"`, `DEFAULT_S3_FORMULATION = "legacy-s3"`, direct `ShellElement(...)` legacy behavior, and explicit `legacy-s3` rollback during development. Add formulation-aware construction, serialization, restart fingerprints, caches, batching, diagnostics, and result provenance without altering historical records. Qualified/legacy/V1/V2 hot restart is forbidden unless a full load-history replay is performed.

## Qualification

Qualification must use exact frozen wheels and two deterministic cycles. It must cover the complete 252-record mixed-topology campaign, all special interfaces and numberings, component reversal, locking, modal, buckling, recovery, batching, restart, serialization, migration, and cross-wheel behavior. The reference fields and hard-Navier support definition remain independent and frozen. Performance measurements are diagnostic and comparative; activity and memory watchdogs protect against unhealthy processes without becoming scientific duration gates.

V2 default activation requires every scientific and ecosystem gate to pass twice, byte-identical canonical aggregates, empty independent P0/P1 findings, and no unresolved rollback incident. Failure or incomplete evidence blocks activation. Success authorizes a separate reviewed default-activation commit; it does not change qualified Q4 mechanics or authorize an improved S4.

## Delivery stages

1. Preregister V2 sources, equations, conventions, proof contracts, and test inventory.
2. Implement research producer and independent checker; close local algebra and recovery equilibrium.
3. Add an opt-in production candidate with package, restart, and migration tests.
4. Integrate exact candidate wheels across ANYmesh, ANYfem, ANYstructure, ANYintelligent, geometry, and file-format adapters.
5. Run two complete mixed-mesh qualification cycles and independent review.
6. Only after acceptance, activate current-policy S3 aliases through protected pull requests, with ANYsolver last.

Every stage retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` until the separate activation authority is accepted.
