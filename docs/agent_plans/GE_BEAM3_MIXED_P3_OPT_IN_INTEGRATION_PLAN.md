# GE Beam3 mixed P3 opt-in integration

## Authority and outcome boundary

P3 starts from the accepted P2 closeout at
`e31c9e292a2fc9f6b57472bb8c5b90919a535492`.  P2 qualified the private
straight, stateless, mixed discrete-curvature mechanics for solver state,
dead loads, reference mass, native recovery, reference modal analysis, and
reference Euler buckling.  P3 does not repeat or enlarge those scientific
claims.  It promotes that exact mechanics to formulation ID
`GE_BEAM3_DC_MIXED_K1_MACRO_V2` and exposes only the exact selector
`ge-beam3` through `create_element`.

The public class remains `GeometricallyExactBeam3D3NElement`.  New qualified
wrapper modules `ge_beam3_element.py` and `ge_beam3_state.py` provide the
promotion and v2 boundary while the accepted P2 candidate modules and evidence
remain intact.  A minimal protected hook may be added to the mixed element,
but its equations and P2 identity do not change.  The qualified class must stay
formulation-native, must not inherit from `QuadraticBeamElement`, and must not
enter legacy B3 or beam batching kernels.  P3 is additive.  Existing B2, B3,
Q4, S3, defaults, aliases, package metadata, dependencies, workflows, and
versions are frozen.

## Public interface

`create_element("ge-beam3", ...)` accepts exactly three distinct node IDs and
the existing mandatory physical reference-orientation authority.  No spelling
normalization beyond the factory's existing lowercase conversion creates an
alias: in particular `ge_beam3`, `beam3`, `b3`, `quadratic_beam`, and `beam`
retain their prior dispositions.  The qualified class and formulation ID are
exported from the package root.  No existing selector changes meaning.

The standard linear stiffness route returns the already qualified
reference-linear condensed 18 by 18 operator.  The standard linear internal
force route is exactly that operator multiplied by the finite 18-coordinate
linear displacement vector.  These routes do not reinterpret rotation-vector
coordinates as accumulated finite-rotation state and do not change the P2
nonlinear transaction path.

Only the P2-qualified native capabilities may become reachable: native
four-station recovery, reference-configuration consistent mass, reference
modal analysis, and signed-axial-force reference Euler buckling.  Fibre stress,
history-bearing sections, follower loads, current-state modal or buckling,
linear or finite-rotation transient dynamics, gyroscopic terms, curved or
kinked references, joints, and ecosystem exposure remain fail-closed.

## Serialization and restart

P3 introduces element and committed-state schema v2.  The element record binds
the qualified formulation, exact geometry/orientation/triad policy IDs,
section descriptor, and qualification origin.  The committed-state identity
uses the qualified formulation ID, v2 layout, and v2 integrity preimage.

P2 candidate-state records are research evidence, not migratable production
state.  A v1 state, candidate formulation ID, candidate identity preimage, or
missing formulation authority is rejected before mechanics.  There is no hot
restart conversion.  Canonical JSON rejects duplicate keys, unknown keys,
nonfinite values, invalid array encodings, and digest mismatches.

## Package and nonintrusion gates

Build one wheel without build isolation from the clean frozen candidate.  In a
fresh external environment, install that exact wheel and its declared runtime
dependencies, remove repository and source paths, enable no user site, and
prove that `anysolver`, the class, selector, formulation ID, and schemas all
originate from the installed target.  Run selector, linear assembly, native
recovery, reference mass/modal/buckling, serialization, restart rejection, and
unsupported-route checks from the installed artifact.  Two fresh package runs
must produce byte-identical canonical correctness records; raw timing and path
diagnostics stay external.

Compare the base and candidate wheels with paired, alternating-order B2 and B3
fixtures.  Use one warm-up and at least eleven measured pairs for construction,
stiffness, internal force, assembly, solve, recovery, and restart.  Report
median, MAD, p95, CPU time, and peak RSS.  No existing B2 or B3 median may
regress by more than five percent.  P3 imposes no speed ratio on GE-B3 and does
not add a batch implementation.

## Execution and terminals

Smoke tests precede package or performance work.  A child uses one numerical
library thread, no more than 24 GiB, and no more than 600 seconds.  At most
three children run concurrently and a complete wave is capped at 1,800
seconds.  Outputs are exclusive, partial results are noncanonical, process
trees are terminated on resource or inactivity failure, no automatic retry is
allowed, and an authority request is never reused.

Terminal precedence is:

1. `BLOCKED_GE_BEAM3_P3_BASELINE_OR_AUTHORITY`
2. `BLOCKED_GE_BEAM3_P3_PROCESS_OR_EVIDENCE`
3. `NO_GO_GE_BEAM3_P3_SELECTOR_OR_SERIALIZATION`
4. `NO_GO_GE_BEAM3_P3_LINEAR_INTEGRATION`
5. `NO_GO_GE_BEAM3_P3_PACKAGE_ISOLATION`
6. `UNCLASSIFIED_GE_BEAM3_P3_PERFORMANCE`
7. `PROVISIONAL_GO_GE_BEAM3_STRAIGHT_STANDALONE_OPT_IN`

The successful terminal authorizes only explicit straight-reference use in
ANYsolver.  It does not authorize defaults, additional aliases, ANYfem or
ANYstructure exposure, version changes, tags, publication, curved geometry,
beam-shell joints, or new mechanics.
