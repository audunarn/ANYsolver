# Coupled retained native/S3 material assembly

Development successor to d8edbfcd. Existing native_retained_s3_static assembly is
split into structural blocks and one spatial contact scatter. Its historical
line-contact solve still uses the same operations in the same order. The new
NativeS3MaterialContributor binds source reference/element and physical S3 work
map to this owner, evaluates from a supplied physical origin, then adds the point
material contribution instead of the old line normal law. It retains all42native
coordinates, both beam/shell cross blocks and algebraic structural equations.
No new solver, accepted-state codec or distributed surface discretization exists.

The path uses the native rotation primitive, matching context.advance exactly.
Every candidate's positions, low parts, cell rotations and shell displacement
must exactly match the authoritative structural candidate. Support increments
and absolute origin supports are checked. No material/friction state is committed.

## Evidence and preserved failure

Initial integrated run:17passed,2failed in7.69s. Failure was a test-indexing defect:
a tuple of supported DOFs was interpreted as multiple NumPy axes, before the two
directional checks ran. Corrected to an index list; both checks pass4.58s.
The17passes include15path checks after native rotation alignment, the existing
coupled line-contact solve and contributor definition/support rejection.

Independent OpenAI read confirmed native slot mapping, exactly one spatial
connection conversion, no duplicate old contact force and retained cross blocks.
It identified two integration requirements:

1. Total rotation increments from an origin have a different derivative from
   spatial endpoint corrections. Resolved with explicit spatial_tangent and
   origin_chart_tangent. The latter multiplies rotational columns by J_l(w),
   using the existing exponential Jacobian. A finite non-axis-aligned test
   distinguishes the tangents and meets1e-5 at two perturbation sizes.
2. Definition guards do not associate independently supplied friction history
   with an issued accepted origin. Absolute support checking is now added, but
   accepted-record binding remains required before commit/restart. This bridge
   does not claim otherwise.

Final contributor module:4passed4.85s (stick/slip coupled tangents, retained and
cross blocks, binding/support guards, finite-rotation origin chart). Unaffected
path/legacy-solve checks reused. All runs180s/953MiB/JIToff; raw logs/resource and
effective runtime records are retained in coupled_assembly_results.json.

Fixtures are preloaded local candidate states, not valid virgin analysis starts,
converged physical increments, initial interference-fit admission or engineering
acceptance. Next integrate the accepted-origin transaction and bounded equilibrium
driver/event control through the existing native owner. Distributed swept-surface
integration, physical initialization, restart and qualification remain required.
