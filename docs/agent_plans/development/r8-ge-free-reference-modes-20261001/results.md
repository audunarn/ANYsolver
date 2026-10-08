# Explicit free-free GE reference modes — 1 October 2026

Development delivery, not full F07/G4B or physical-frequency qualification.
The existing public GE owner admits empty supports only with the explicit
`LinearDefinition.modal_boundary_policy=GE_FREE_FREE_MODAL_ONLY_V1`. Default
supported construction and identities retain their meanings. The modal-only
owner rejects static/finite solves, restoration and chart state writes.

`modes(GEReferenceModesRequest(...))` returns a distinct
`GEFreeReferenceModesResult`: six analytic physical rigid fields, their
mass-normalized basis and kinetic Gram, plus the requested flexible pairs.
The admitted model is connected, virgin elastic flat-Q4/generalized-GE with
six-pose points. S3, lines, footprints, loaded histories, prestress/buckling and
finite dynamics remain unsupported. New ANYfem modal persistence is separate
forward work; old consumers cannot silently represent an empty-support policy.

The full sparse singular descriptor retains physical native half-cell inertia
and massless resultant/trace/spin/multiplier coordinates. The only projection
removes the known six rigid fields through their 6×6 physical kinetic Gram;
there is no production dense nullspace, static condensation or invented mass.
Flexible selection uses a negative spectral shift and general shifted solves.
The unchanged near-zero roundoff screen is a cancellation-resolution check,
not a certified Arnoldi/LU eigenvalue error bound. A finite Krylov request
cannot prove absence of every unexcited mechanism or exactly-six nullity.

Independent checks derive common rigid motion from model coordinates and
native incidence, and its inertia from shell-volume integration and explicit
beam particles. They verify KR/CR, positive six-dimensional kinetic work,
and rotated-frame equivalence. A bounded complete descriptor quotient removes
only the analytic rigid fields; native algebraic variables and multipliers
remain in its test-only dense QZ calculation. Independent inverse refinement
and physical-work subspace checks corroborate the requested flexible pairs at
the unchanged 1e-10 eigenvalue tolerance, including a second declared shift.
This is not all-root completeness or an external physical reference.

Review identified an inadequate negative test: zeroing all K failed before
testing the near-zero discriminator. The additional independent control retains
nonzero K and introduces one positive-kinetic compatible null field through a
documented rank-one test-only stiffness change. K'q, Cq, rigid mass orthogonality
and preserved common rigid fields are checked first. The actual near-zero path
then rejects it without partial publication or accepted-state change. This is
a synthetic numerical obstruction, not a physical material/connection oracle.

Final wheel SHA256
`4ddde5790ce72697d20425186473d1d5066f84156287d9d9083ea1f059643ccd`
binds391 source/wheel/site modules. Windows/Python3.14.2, actual pools/Numba1,
JIT disabled. Installed modal46/46 checks pass in7.288s supervised wall time,
186851328-byte process-tree peak;211 imported solver modules are onsite.
Original source12 and initial oracle4/5 checks belong to their saved source
versions; the final installed46 campaign includes all their predicates and
the strengthened preserved-rigid-field checks.

Affected legacy116/116 checks pass with no errors/skips in495.605s supervised
wall time and200130560-byte peak;214 imports are onsite. All numerical jobs
use the existing600s/8GiB limit and run serially. No timing gain is claimed.

The unchanged baseline control is reused at its exact identity:15 candidate
static CSR/result/JSON/checkpoint bindings agree byte-for-byte. Checkpoint SHA256
`6e390ce5d5eac5b356a0bc06fe2a4bc3c9f32ab02eafec6aaf3c77fc39be1651`;
observable JSON`2f34547fa46c3fcf18099bcfd75304d768244dd56c6e40cacc4bf3c01947ed56`.
The installed public free-free example completes with six rigid fields and
three flexible pairs, frequencies54.829686589138234/143.8233601277254/
548.7888919246996Hz, one factorization and211 onsite imports. Its supervised
wall/peak is2.101s/144613376 bytes. These are example outputs, not externally
qualified physical frequencies.

Failed preparation is retained: the first fixture list included nonexistent
files, so no tests executed; a follow-on bare package path failed to build.
The final artifact's first legacy collection lacked a required existing helper,
so no numerical checks executed; the missing exact fixture was added for a new
run label. Neither setup failure is counted as a pass. Product arithmetic or
scientific thresholds were not changed to repair these fixture errors.

Source snapshots, fixtures, matrices, wheels, effective settings, commands,
run inventories and review are retained together for this delivery.
[Independent review](independent-review.md) leaves no blocking finding in this
explicit scope. [Raw archive](raw-v1.zip) and [identity](raw-v1-identity.json)
preserve424 files; each archived file was reread against its SHA256 inventory.
Archive SHA256`4f69bd5b5376484bbf815b810381451367af053a02f1117f89b22fa8d29cb97f`;
review SHA256`f99e2a351bfab8f28679189004f7023265282649e0c5029b31569708d660e3d2`.
The full F07/G4B, repeated-space/completeness claims, mass/physical reference
convergence, consumer stability, external/scale and aggregate gates remain
OPEN. Main, release version, legacy equations and formal F03 authority are
unchanged; this delivery authorizes no publication.
