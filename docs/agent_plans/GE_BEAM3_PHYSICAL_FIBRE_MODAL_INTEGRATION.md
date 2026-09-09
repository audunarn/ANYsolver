# Physical-fibre modal integration

Successor of bdb5daf828449f4e9b454156f4effdbf32bfa354. Extend the existing
physical-fibre model-owned route; do not change its material law, kinematic map,
quadrature, tolerances, accepted-state chain, or the existing beam/shell defaults.

The current-rest modal capture mechanically replays the original retained fibre
translation checkpoint. Every station-owned fibre history must remain exactly
unchanged. Every fibre must be on a smooth elastic branch with a strictly positive
yield-interior margin. This admits unloaded plastic histories, not an elastic
substitution for an actively yielding state. Numerical modes at a nonsmooth
yield boundary are rejected rather than presented as a classical modal result.

Eliminate the eighteen inertia-free stress resultants through their actual
compliance factor; retain six physical cell rotations and the nodal variables.
The full consistent current-rest inertia is checked against its kinetic factor.
Nodal rotation traces remain exactly massless. Only real model supports constrain
the modal space; the displacement controller is not a support or a stiffness term.
The original paired-vector signed solver consumes the factors, preserves negative
eigenvalues and audits the original physical actions. No alternative solver or
static-mass fallback is introduced. Existing coordinate and process bounds remain.

NativeBeamAnalysis.translation_modes now dispatches physical-fibre checkpoints
to this material/state owner. Reference modes use a separate stress-free virgin
operator assembled directly from immutable fibre definitions, without inventing
an accepted checkpoint. Reference spectra admit supported and free-body models;
physical-fibre reference_modes calls require explicit spectral bounds. Existing
generalized reference-mode behaviour is unchanged. Both routes remain private
integration candidates pending full qualification and public current-core routing.

Development checks passed28 tests in33.89 seconds before reference integration,
then59 tests in71.39 seconds including reference integration. Separate inventories,
not119 total unique tests. Added coverage includes full stationary Schur equality,
unloaded plastic state/recovery preservation, yield rejection, independent dense
physical-pencil comparison on a moderate small fixture, deterministic modal bytes,
reference/current consistency, six free-body zero modes and positive elastic modes,
covariance, exact zero trace inertia, and identity/cancellation mutations. These
are regression checks, not independent authorship or complete engineering authority.

The final regression additionally checks section-content mutation against its
registered identity and preserves the actual unloaded and model-owned checkpoints.
Do not rebuild the prior wheel merely for another intermediate package milestone;
batch remaining current-core integration before final package qualification.

Remaining full-goal work includes larger-model modal consumption, mixed-family
assembly, full current-state/buckling interface parity, remaining engineering
acceptance and independent review, final explicit straight/curved public selection,
and qualified objective eccentric/curved finite-rotation beam-shell coupling.
Do not substitute this modal increment for the full goal or restart passed N32
campaigns. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
