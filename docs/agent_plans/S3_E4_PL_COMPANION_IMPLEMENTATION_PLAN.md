# S3 E4-PL Companion Implementation Plan

## Authority and scope

This plan replaces the design draft
`S3_E4_PL_COMPANION_ELEMENT_PLAN.md` (12,394 bytes, SHA-256
`3F11A2EBDDDB0CDE55F9B0C52F43FABF33C6F01217DADCEEA26C6AAC3D26D5D7`).
The draft is background input, not executable formulation authority.

The ANYsolver base is commit
`534985fa7699dd4bb484e99ff295e523557555e6`, tree
`06a2251edcd271f4f8a55246f43d46528b4f505b`, subject
`Merge pull request #26 from audunarn/codex/s4-e4-pl-q1l-default-activation`.
The qualified-Q4 feature parent is
`d627ee28bf506d66445e79a624dba8f18a0c7a35`.

The first release is additive and opt-in.  It must not change the Q4 default,
the legacy S3 aliases, or persisted old-project behavior.  Default S3
activation is a separate coordinated release after every gate below closes.

## Frozen linear identity

The candidate is `E4_PL_QUALIFIED_S3_COMPANION_V1`, with three nodes, six
external DOFs per node, two internal hierarchical bubble rotations, and three
barycentric PL multipliers.  The public 2014 MITC3+ paper is the physical-core
authority.  Its exact URL, bytes, digest, pages, and equation map are bound in
`e4_pl_s3_formulation_contract.json`.

The following are formulation identity:

- `L1=1-r-s`, `L2=r`, `L3=s`, and `b=27*L1*L2*L3`;
- the six A--F tying positions and `d=1/10000`;
- the covariant assumed-shear construction in equations 12--17;
- standard degree-five seven-point triangle integration for stiffness;
- analytic barycentric integration through degree six for consistent mass;
- node-major external ordering `(u,v,w,theta_1,theta_2,theta_D)`;
- barycentric PL basis and its analytic Gram matrix;
- the basis-invariant elastic membrane drill scale;
- exact local bubble/PL condensation and the selected Guyan mass reduction.

The condensed 18-coordinate element must have rank 12 and exactly six rigid
modes.  The staged rank and saddle-inertia obligations are part of the
contract.  Exact D3 numbering transport and physical-director reversal are
different operations; reversal is a covariance case only when section offset,
`B` coupling, layer order, moments, and top/bottom recovery are transformed as
well.

## Implementation stages

1. **Linear opt-in candidate.** Implement the flat physical core, PL
   completion, local condensation, physical/numerical diagnostic split,
   strict geometry admission, stable serialization identity, and explicit
   `e4-pl-s3`/`qualified-s3` factory selectors.  All unsupported nonlinear,
   dynamic, buckling, restart-history, or recovery paths must fail closed.
2. **Independent local qualification.** Compare independent reference and
   oracle constructions at uncondensed blocks, bubble and PL Schur blocks,
   condensed stiffness, rigid modes, D3/director transport, recovered fields,
   and virtual work.  Cover the full admitted triangle-quality domain with a
   bounded interval/coercivity certificate in addition to named regression
   triangles.
3. **Native parity.** Implement a formulation-native internal bubble solve and
   consistent state-dependent Schur tangent for nonlinear geometry, material
   state, and initial fields.  Back-substitute the bubble for physical
   recovery and condense internal load work.  Condense geometric stiffness
   consistently for prestressed modal and buckling analysis.
4. **Dynamics.** Form the full consistent nodal-plus-bubble mass using analytic
   bubble moments and reduce it through the static bubble map.  Numerical
   drilling coordinates receive zero inertia and are eliminated/projected as
   algebraic coordinates by modal and transient solvers.
5. **Ecosystem qualification.** Route ANYfem through the central solver factory,
   persist the topology-specific formulation policy, and add ANYmesh
   authoritative-normal admission, directed-edge auditing, and triangle
   contributions to mixed nodal normals.  Qualify active ANYstructure and
   ANYintelligent adapters against candidate wheels.
6. **Activation.** Only after local, mixed-mesh, locking, parity, performance,
   serialization, restart, and cross-wheel gates pass in two deterministic
   cycles may S3 topology aliases select the qualified element by default.

## Admission, evidence, and release gates

Qualified triangles require a positive owner-normal signed area ratio, angles
in `[30,150]` degrees, edge ratio at most 4, signed scaled Jacobian at least
0.20, and normalized area at least 0.60.  A rejected triangle is repaired by a
bounded deterministic mesher operation or produces a typed error; it never
falls back silently.

The mixed campaign uses exact S3 area fractions `0,1,5,10,25%` on nested
`20,40,80,160` macrocell sequences and preregistered masks/diagonals.  It gates
patch and equilibrium residuals, convergence slopes, locking through
`t/L=1e-6`, interface-resultant errors, modal/buckling correlation, numerical
PL participation, and deterministic performance.  Formal work is sharded at
one numerical thread, 600 seconds, and 24 GiB per process with no retry.

Candidate releases remain opt-in (`ANYsolver 0.3.1`, `ANYfem 0.3.3`,
`ANYmesher 0.2.6`).  Default activation requires coordinated breaking releases
and keeps `legacy-s3` for at least two releases and 180 days.  History-bearing
models cannot hot-switch formulation; they continue under their original
identity or replay their load history from a pristine state.

Any later improved-S4 mechanics change must rerun the complete mixed Q4/S3
campaign.  S3 completion by itself does not authorize an S4 formulation change.
