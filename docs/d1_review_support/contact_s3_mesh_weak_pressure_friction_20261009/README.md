# Weak-pressure S3 material friction development

Delivered an explicit `S3MeshWeakPressureFrictionSettings` route for the existing
fully covered connected S3 mesh and its shared P1 monolithic normal owner.
The original hard full-contact guard and legacy settings remain unchanged.

The six-phase press/stick/slip/reversal/open/recontact workflow passed using
authenticated restart segments. Source execution supplies phases1-2; private
installed execution supplies phases3-6. An alternate suffix from the same
phase3 checkpoint verifies phases4-6 and complete friction-history parity.
This is segmented evidence, not an uninterrupted six-phase solve.

The required `finite_material_gap_error_m=5e-5` bounds perpendicular physical
gap at **accepted endpoints** on pressure-supported faces, including corners
and actual stored dense points against every target facet. It does not bound
the absolute material gap throughout a trial chord or detect hidden opening
events. Existing whole-chord coverage and source-ray nonpenetration remain.
Numerical positive pressure at local opening is explicitly reported; this
candidate does not establish pointwise complementarity or Cauchy traction.

Example: `examples/general_contact_s3_mesh_weak_pressure_friction.py`.
Use `--through-step` and `--restart` to consume the declared public path.
The final installed CLI test consumes the authentic terminal checkpoint with
zero new increments; actual increments are established by installed tests.

See [OUTCOME.md](OUTCOME.md) and [IMPACT.md](IMPACT.md). Full commands, identities,
logs, metrics and failed attempts are retained under
`C:/ANYworkspaceWork/contact_s3_mesh_weak_pressure_friction_20261009`.
Engineering acceptance and release remain false.
