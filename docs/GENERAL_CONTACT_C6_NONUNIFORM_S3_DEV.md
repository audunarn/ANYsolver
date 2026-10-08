# Nonuniform S3 target impact — development

Run `examples/general_contact_nonuniform_s3_impact_dev.py --output <result.json>`.
Two source S3 V2D faces cover a unit square; one larger S3 target receives contact
force and develops a nonuniform normal displacement. Both finite bodies use the
same average-acceleration Newmark stage and the existing nonlinear structural
assembler. The general Jet2 contact contributor supplies complete both-body work;
the pressure sidecar supplies event coordinates and verifies candidate agreement.

## Explicit API and limits

Select `ContactTransientSolverControls(allow_fixed_projection_s3_target_dev=True,
q4_plane_event_subdivision_dev=True, batch_plane_event_fronts_dev=True)` and
`ContactSolverSettings(pair_motion='general', general_s3_difference_step=1e-5,
general_s3_differentiation='jet2_s3_dev')`. Use one `projected_penalty` interaction.
`TransientConfig` owns time integration, initial conditions and output controls.
The inherited Q4 event flag enables the shared pressure-event machinery here;
neither body becomes a rigid plane. Historical controls and schemas remain separate.

Only exact qualified isotropic-elastic S3 V2D selections are admitted: two
surfaces, one S3 target, strict reference projected coverage and positive supported
P1 modes. All elements must belong to the selections. Source normal translation
must be exactly uniform, with zero rotations and tangential motion. Target nodal
normal motion may be nonuniform. Exact represented generator, candidate and actual
mapped skin endpoint/rate checks reject unsupported motion or rounding. Fixed
source projection preserves support and makes normalized pressure gaps affine
on this restricted subspace. This does not certify general source deformation,
sliding, finite rotation or arbitrary cancelling approximate motion generators.

Reduced mass must be physically positive, with the existing 512-coordinate limit.
No inertia is added to shell algebraic rotations; this fixture fixes them.
Every source face receives a complete supplied-float Hermite geometry certificate
against the original target triangle. `maximum_gap_triangles` bounds proof panels;
`maximum_swept_subdivisions` bounds depth. Unresolved proof requests bounded step
cutback, never partial face acceptance. Cancellation and exceptions clear the
solve-owned context. V12 restart binds the profile, ordered pair/node features,
event controls, physical sweep budgets and existing structural/contact identities.

## Fixture and reporting

Thickness 0.02 m, initial physical gap 0.0002 m, source/target areas 1/24.5 m²,
densities 1000/100 kg/m³ and penalty stiffness 1e9 N/m³ are explicit. Source normal
velocity is −0.1 m/s; the target starts at rest. Source translation plus target
translation and one affine slope remain after manufactured guides. The target
slope retains actual S3 structural work. Its physical lumped nodal mass gives
modal inertia `diag(20,49,49*98/9)`, rather than a substituted consistent mass.
Default time step is 25 µs and endpoint 3 ms; gap budget is 20 µm.

The existing projected full-space work convention is
`projected_weak_gap_nonpotential_v1`. `penalty_energy` remains zero; use
`regularization_storage_j` for the separately labelled contact storage. Only the
admitted fixed-support reachable coordinates justify the reference storage
potential used in this fixture's accounting.

An independent 16-branch P1 pressure/Newmark oracle uses the already qualified
structural stiffness as input. It verifies the new coupling, not independently
the S3 spatial formulation. Separate physical cubic gap checks, momentum/wrench,
active restart, tamper rejection, cancellation, exception and unresolved-proof
checks are retained. Source/wheel result and imported-source parity are recorded.

**Status:** implemented, source-tested and installed-tested development.
Engineering acceptance, release and unrestricted shell-impact admission remain
false. General source deformation, two-direction target fixtures, materials,
friction, rotation and full C6 outcomes remain programme requirements.
[Evidence](d1_review_support/C6_NONUNIFORM_S3_DRIVER_SLICE_20261003.md).
