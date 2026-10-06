# Finite triangulated rigid contact (development)

`TriangulatedRigidContactBody(name, vertices, faces)` is an immutable explicit
mesh declaration. Vertices are xyz metres; faces are `(positive_stable_id,
(zero_based_vertex_indices))`. Oriented arbitrary mesh data can be declared.
The first executable profile admits a fixed planar, consistently oriented,
nonoverlapping finite mesh against an elastic e4-pl-s3-v2d shell source (one element or an explicitly connected patch).
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
Nonplanar geometry, Q4 mechanics, disconnected source elements, finite rotations,
free/moving rigid bodies, friction, self-contact and physical edge-only contact
remain unsupported. No derivative is claimed at unresolved clipping incidence;
such a trial must refuse, rather than activate a fallback engine. Normal-law,
resource limits and old profile identities remain unchanged.

## Connected source patch profile

`S3_PATCH_PLANAR_TRIANGULATED_RIGID_SHARED_PENALTY_STATIC_DEV_V1` admits a connected S3 physical patch. Shared edges must have opposite directed topology, shared physical positions and complete work maps must agree, and exact projected positive source-face overlap refuses reference and candidate geometry. Pressure unknowns are global material source nodes; shared support/weighted-gap Jets are summed across every source and target face before the same penalty law. Both source-face and target-face crossblocks survive the global skin pullback. The single-S3 profile and its restart contract are unchanged.

Before dense derivative allocation, the patch profile binds an explicit128MiB local derivative-work cap. For n source nodes, m geometry coordinates, p face pairs the conservative storage allowance is `8*(2*n*m*m+2*n*m+13*m*m+16*m+n*n+512*p)+4MiB`: two gradient/two Hessian arrays, returned Hessian plus twelve dense expression temporaries, vectors/pressure Gram/pair-state scratch, and sequential fixed18-coordinate Jet scratch. The4MiB allowance exceeds the fixed S3 polygon (at most6vertices/four fan triangles) primitive's retained Jets; no AD graph is retained. This is local work storage, not a total-process memory guarantee. Candidate, pressure-node, energy and process budgets retain their existing meanings.

`examples/general_contact_triangulated_rigid_patch.py` provides a connected two-S3/nonmatching finite-tool force press. New focused patch tests also cover press/open/recontact and exact restart, shared-junction skin-rotation work, and an independent P1 M/S active-set reference using a separately assembled no-contact structural K. The nonlinear correction expression is a leading-order estimate, not a rigorous uniform error bound; actual coupled response is measured against the independent reference at the unchanged1e-6 gate. Multi-element admission is development evidence, not spatial convergence or C4 qualification.
# Connected-patch reference invariance development control

The focused `test_general_contact_triangulated_rigid_invariance.py` rebuilds the
established connected two-S3/fixed nonmatching planar-tool fixture in four cases:
baseline, reference-frame change only, arbitrary stable material-node numbering
only, and their composition. The proper cyclic axis permutation sends z to x;
the translation is the exact dyadic vector (1/8,-1/4,1/2)m. Physical source skins,
reference directors, loads, supports and all six work coordinates per node are
transformed consistently. The actual constraint subspaces agree under that map.

Actual ordinary force equilibria compare mapped displacement at a fixed10um
clearance scale, each source/tool wrench separately, and support/load/contact
equilibrium. Aggregate moments use M'=R*M+t cross(R*F), about global origin0;
nodal couples rotate by R without a translation lever arm. Force/moment scales
are separately0.15N and0.15N*m, with unchanged1e-6 gates and50um physical-gap
gate. The local contact-work/H control is at a distinct active partial footprint,
with the real manager boundary guard intact. It tests the complete FE skin-map
pullback and all force/moment versus translation/rotation H blocks. Length/angle
chart scales are1m/1rad; directional force/moment-rate scales are0.15N and0.15N*m
per unit declared path parameter, and scalar work-rate scale is0.3J per parameter.
Two perturbations1e-7 and1e-8 retain1e-5 work/tangent gates. These absolute row
checks also imply the prior relative checks with denominators max(1,norm).

This reference-coordinate/node-inventory control does not extend admission to
finite-motion rotation, warped/moving tools or unrepresented physical rims.
Its local derivative pose is not a solved lifecycle state or a new rim law.
Source mechanics were unchanged; installed evidence uses the matching private
payload. It is development evidence, not formal qualification or acceptance.
