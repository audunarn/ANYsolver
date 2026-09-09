# Continued signed endpoints: separate continuum comparison passed

Frozen source 5469c43cb13a86a2e1f381643d7df2369883a080,
tree e72c6a1ecaf2f8bdb25efe23860ead40b3551b1a. Four research-only paths;
no production mechanics, section state, recovery, defaults, APIs or version changes.
Sixteen targeted tests passed in 0.62 seconds before freeze; diff check passed.

The actual N24 continued endpoints at +/-0.0065 were compared against the
separate spatial continuum boundary-value solution, using unchanged source
equations SHA-256
2f3c960cf0dfda2b62d2e3e0073533ee390e1c5e3af993758aa808f64401f1b9.
Original N20 +/-0.006 fields initialized the reference Newton iteration only.
No native beam solve, completed continuation, or historical qualification run
was repeated. All 49 nodes and 192 stations per endpoint were compared.

All four workers passed: positive smoke 1.314s, negative 1.515s, positive
replica 1.515s, negative replica 1.515s. Total wave approximately three seconds;
maximum recorded process-tree peak 1718988800 bytes. Each exited zero with an
empty Windows Job tree. One numerical thread per child, maximum three concurrent,
600-second/24-GiB child bounds and 1800-second wave bound retained. No retry.

Each signed replica pair produced byte-identical comparison records.
Maximum errors across the two signs:

| Quantity | Relative error | Frozen limit |
| --- | ---: | ---: |
| Load | 0.640541% | <2% |
| Nodal displacement | 1.164336% | <2% |
| Resultant energy norm | 0.614537% | <2% |
| Strain energy | 0.916803% | <2% |

Reference loads are 0.027135560267634123 (positive) and
0.027135560267634126 (negative); native load is 0.027309374581706167.
Each reference used 385 knots, four iterations and 906 callbacks.
Boundary residuals are below 9.12e-27; normalized differential residuals below
1.609e-10; quaternion norm error below 3.442e-14. Differential/norm validation
used two interior Gauss sites in every actual collocation interval (768 sites).
The separately registered 64/128-point reference energy comparison passed.

The complete 52-field cubic polynomial is preserved with all coefficients,
knots and field ordering, not only plotting/station samples. Value and derivative
serialization roundtrips passed. A standard-library-only saved-data auditor
independently evaluated this polynomial by Horner evaluation, reconstructed the
rod ODE and station fields, recomputed all four engineering error definitions,
and checked canonical bytes, receipt bounds, hashes and replica equality.
This audit did not independently reintegrate the 64/128-point reference energy
or reconstruct the boundary equations; those checks remain worker checks.
Separate code does not constitute independent author review or an interval proof.

## Immutable external preservation

Root: C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/
ge-beam3-next-reference-5469c43-20260909.
There are 34 manifest-bound files plus the manifest. Both the exclusive staging
copy and external copy were verified by exact path extent, byte count and SHA-256.
Original temporary outputs are retained.

Manifest: 4472 bytes, SHA-256
6e4ee30363656257d27db2fc5ace7ff24b76472b17050e6481af6d72ffe82ff6.
Saved audit: 750 bytes, SHA-256
1aa7b95917ff06b2c5cf0c6a90da140763f85b3e45b8c90198d2735c2f75584e.
Positive comparison: 1580596 bytes, SHA-256
deaded9e95bcafe8654b9b51143d38c12fd194422458ed420c1ab139aa070a5f.
Negative comparison: 1585040 bytes, SHA-256
6a2d9cdc2e0a66d8894965783bf2f2311122ac8bc57b11092f1c09ec66ac774f.

## Remaining gate and interpretation

Endpoint agreement is established only for these two elastic states. Full spatial
stability remains unresolved. The earlier exact discrete negative-work witness
at +/-0.006 remains valid and must not be reclassified as a stable equilibrium.
Continuation convergence and reference agreement do not establish stability,
uniqueness, a loading path from rest, or an entire postbuckling branch.

Next derive and test the full spatial continuum second variation against the
saved complete fields before conducting a separately frozen bounded stability
comparison. Distinguish chart-conjugate moment variations from raw spatial moment
variations. Require a consistent six-component admissible variation with correct
clamps, segment continuity and dead-load jumps; a planar-only operator or a
determinant sign alone cannot certify full spatial inertia. Do not add continuation
targets to the existing hash-bound programme. No completed run is to be reused.

Still outstanding are independent mechanical review, broader geometry and
slenderness coverage, complete nonlinear/material/state/solver parity, installed
public opt-in selection and objective eccentric/curved beam-shell connections.
No public qualification, stable-postbuckling claim, activation, push, release,
version change or default change is authorized by this result.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
