# Finite triangulated rigid contact (development)

`TriangulatedRigidContactBody(name, vertices, faces)` is an immutable explicit
mesh declaration. Vertices are xyz metres; faces are `(positive_stable_id,
(zero_based_vertex_indices))`. Oriented arbitrary mesh data can be declared.
The first executable profile admits a fixed planar, consistently oriented,
nonoverlapping finite mesh against **one elastic e4-pl-s3-v2d shell element**.
Exact stored-coordinate coplanarity and positive-area overlap checks refuse
unresolved geometry. Shared edges use common geometric vertex labels.

Import the descriptor from `anysolver.general_contact`. Use it in the ordinary
`ContactDefinition.rigid_bodies`; the interaction's source is the physical shell
surface, target is the rigid descriptor name. Select `pair_motion="general"`,
`normal_discretization="primal_mortar"`, and an explicit positive
`general_s3_difference_step`. Execution requires `kinematics="von_karman"`
and `corotational_tangent="auto"`; static paths use their existing affine skin
profile. Target vertices are never FE nodes, constraints, masses or materials.
The example `examples/general_contact_triangulated_rigid.py` is a force-driven
deforming-shell press; focused tests also exercise press/open/recontact and
split restart through `solve_static_nonlinear`.

For each shared source pressure node, all triangle support `s`, weighted gap
`w`, gradients and Hessians are summed before the penalty is evaluated:
`E = k/2 sum(w*w/s)` for `s>0,w<0`. Existing S3 clipping Jet2 derivatives include
moving polygon/support work. The full Hessian retains cross-face outer products.
Exact zero support is open; unresolved differentiable clipping branches refuse.
No per-triangle pressure potentials or infinite-plane forces are substituted.

The physical skin map includes side, thickness/reference offset and the
formulation's director and rotational work. Forces are negative potential
gradients. Reported integration/target moments are physical contact moments
about global origin, in N m; forces are N, gaps m, pressures Pa, energy J.
Structural support reactions remain work-conjugate structural coordinates.
Only rigid translation/rotation variations are physical target variations.

For fixed tools, a conservative swept certificate uses affine source vertex
height and quadratic Bernstein source normals. It includes chart evaluation
uncertainty before cancellation and propagated cross-product uncertainty.
It bounds a plane superset for **gap certification only**; force integration and
initial penetration checks retain the finite footprint. Inconclusive polarity,
geometry, crossing or gap checks refuse/cut back. Complete descriptor, physical
skin map, settings and captured operator bind restart and mutation guards.

This is development integration, not C4 qualification or release acceptance.
Nonplanar geometry, Q4 mechanics, multiple source elements, finite rotations,
free/moving rigid bodies, friction, self-contact and physical edge-only contact
remain unsupported. No derivative is claimed at unresolved clipping incidence;
such a trial must refuse, rather than activate a fallback engine. Normal-law,
resource limits and old profile identities remain unchanged.
