# Multiple Q4 fixed-plane impact — development profile

Use `solve_transient_contact` with existing `TransientConfig` and
`ContactTransientSolverControls(allow_multiple_shell_planes_dev=True,
q4_plane_event_subdivision_dev=True)`. Public solve signatures stay unchanged.
The profile is `MULTIPLE_Q4_FIXED_PLANES_NEWMARK_EVENT_DEV_V1`; it is implemented
and source/installed-tested, not independently engineering-accepted or released.

Each explicitly named interaction retains its own fixed plane, surface skin,
dimensioned surface penalty, nodal support and gap tolerance. The contributor sums
the existing full residual/tangent work on authoritative structural coordinates;
it does not advance bodies separately or merge pressure rows. Pair/node identities
and resource limits are deterministic. Duplicate element/side/body interactions,
unreferenced selections, unsupported geometry/laws and exhausted aggregate limits
fail explicitly. Every positive support is retained.

Initial transient scope is exact qualified Q4, isotropic elasticity, guided motion,
fixed analytic planes and positive-definite reduced physical mass. S3 descriptor,
finite-rotation/warped geometry, plastic multiple-pair impact, friction, moving tools,
free bodies and native contact are outside this new profile. Those programme rows
remain required. Nodal dead loads and explicit scalar `ContactNodalLoadHistory`
are supported; the historical single-Q4 plane-event history restriction stays.

All pressure modes share the existing bounded endpoint/stage/event budgets from
one committed origin. Complete physical corner Hermite bounds check every pair
against that pair's own dimensional tolerance. `pair_swept_minimum_gaps` reports
named bounds aligned with saved states, including accepted unsaved steps between
outputs. Bounds concern the supplied-float represented cubic; upstream arithmetic
and general nonlinear integrated paths need their separate qualification.

V10 restart binds stable pair/node pressure features, phase/gap/rate evidence,
analysis settings and load history/work. Rehashed incompatible features are rejected.
Old V1–V9 identities remain selected for their historical profiles. Rejected
candidates do not commit partial child results.

Run `examples/general_contact_multiple_q4_planes_dev.py --output <result.json>`.
Three physical patches use manufactured constant MPCs: the third translates by
half the sum of the first two motions, so actual inertia couples both modes.
This fixture does not establish a permanent joint/attachment capability. Two
supports activate together; one face on the first support remains open. An
independently derived two-mode mass/potential and eight-branch Newmark reference
verify q/v/a, per-pair forces/storage and reaction work. Independent physical path
checks agree with reported bounds within7e-18m. Active restart and ramp-load work/
restart pass. The fixture's declared gap budgets1.5/0.9mm are developmental,
not the full programme's thickness-scaled qualification or application defaults.

The installed example matches all205 imported solver hashes and numerical fields.
Its maximum discrete energy defect8.86e-9 and exact-grid oracle agreement do not
establish temporal/spatial convergence or general deforming-shell impact.
[Evidence](d1_review_support/C6_MULTIPLE_SHELL_PLANES_SLICE_20261003.md).
