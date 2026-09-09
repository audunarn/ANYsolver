# Model-owned native beam solver dispatch

Parent `1c1df3d35fd74e77ec30283bb1002cf02f3b1f07`, tree
`5cce8e8e4795a755e55acf7be765acdfc98cf7b9`.

Add a private `NativeBeamAnalysis` entry built from reconstructible definitions
and exact boundary conditions. It registers actual18-external-DOF elements in
an ordinary FEModel, binding shared reference coordinates, section ownership,
inertia, node/DOF maps and support data. Construction never migrates legacy
records or creates committed material history. Re-entry and model mutation fail
before state evaluation; the underlying solver retains its own live guards.
Support admission rejects dangling/duplicate node references, inconsistent
declared/cached constraints, unknown components, nonzero prescribed values and
partial rotational constraints. A force solve requires supports before virgin
state construction; a free-body reference-modal request remains admissible.

The analysis entry explicitly dispatches generalized distributed forces/couples
and physical-fibre nodal dead forces through their existing real native Newton
drivers. It does not choose a solver based on whether another one fails.
Checkpoints retain complete original backend chains inside a canonical external-
hash-bound envelope. The envelope also binds definition/inertia graph identity
and backend owner, preventing a physically different definition from accepting
an old checkpoint merely because geometry or a subset of hashes match.

Resume decodes/revalidates the existing backend chain first. Validated prefix
extraction invokes the original encoder; it never reseals guessed geometry,
material history or rotations. Recovery dispatches to the matching native
physical/resultant field owner and verifies no history advance. Failed solves
may return only the actually accepted prefix, never a completed status.

Reference/current-rest modes use the separate generalized descriptor pencil:
retain physical cell rotations/inertia; eliminate only the original inertia-free
resultants and assembled massless nodal traces. Static mass substitution is
forbidden. Current modes retain conservative, elastic-interior admission. The
physical-fibre modal route, cross-family models, MPC/joints, general partial
rotation constraints and full production selection are not authorized here.
They remain required integration/qualification work, not removed goal scope.

## Frozen development checks

First run constructor/guard tests, then separate actual generalized force,
physical-fibre force, intentional failed-step and reference-modal inventories.
Force checks compare native final states/displacements with direct original
driver calls, then authenticated prefix resume, recovery and correct failure
classification. Modal checks compare actual24-coordinate pencils/eigenvalues
with original calls, six rigid modes and physical mass rank15, not a static
18-coordinate approximation. No test substitutes a scalar toy system.

Use fresh external logs/artifacts and the existing Job supervisor:600seconds,
24GiB and one numerical thread per child,1800seconds/wave, at most3workers,
120seconds inactivity, no automatic retry. Rehearse, freeze and repeat actual
scientific outputs twice with byte-identical comparison. Preserve incidents.
No earlier onset/lifecycle/definition qualification wave is rerun.

No beam or shell mechanical expression, threshold, section law, public selector,
package version or default changes. This is actual solver integration under a
private entry, not independent qualification or production activation. Full goal
remains ACTIVE, including spatial postbuckled branches, remaining parity,
installed dependency environment, independent review and objective shell joints.
