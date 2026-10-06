# Elastic beam / deformable S3 impact development route

Use the ordinary `solve_transient_contact` with `TransientConfig` and explicit
`ContactTransientSolverControls(allow_deformable_beam_s3_dev=True)`.
The example `general_contact_beam_s3_transient.py` supplies a fully declared
model. This is development verification, not C6 qualification or admission of
general beam/shell impact.

## Mechanical scope

One classical B2 or B3 round beam and one E4-PL S3 V2D elastic skin comprise
all elements. The existing moving-normal line Jet2 potential, physical skin
side/offset, complete both-body residual and tangent are reused. S3 rotational
coordinates and rates must be exactly zero; the actual model constraints must
annihilate these rows of the reduction. Actual reduced physical mass must be
positive definite. There is no added inertia, damping, spring or restitution.
The first profile supports initial impact and constant external dead loading;
time histories, friction, genuine caps/rims, finite rotations, native retained
beams and multiple faces remain unsupported.

## Complete represented path

For each accepted proposal the two endpoints and rates define the actual cubic
Hermite motion. All four Bernstein controls of both bodies are mapped through
the physical skin chart. B3 spatial Q2 controls and cubic time controls form a
complete tensor hull. Subdivision uses de Casteljau, bounded by existing finite
controls; unresolved intervals reject the proposal and use the ordinary finite
cutback path.

At an exact anchor let C=e1 cross e2. Vertex displacement enclosures give
edge uncertainties delta1/delta2. The cross uncertainty is
|e1| delta2 + |e2| delta1 + delta1 delta2. A positive normal magnitude floor and
reference orientation floor are required. Exact stored-coordinate Fraction
arithmetic and directed norm conversion enclose the mathematical hull;
128 epsilon times the uncancelled reference/chart magnitude supplies the
separate binary64 chart/Hermite allowance for this bounded profile. Unit-vector
conversion errors are explicitly included.

The gap enclosure uses n(t) dot delta-r + (n(t)-n0) dot r0, with true unit n(t).
The anchor extent bounds r0 and the first term is bounded by |delta-r|, so no
omitted displacement-normal product remains. The same decomposition bounds
each inward unit rim direction. Hidden target motion, normal collapse and rim
crossing are covered by the full controls, rather than checking hull edges.

## State and consumer contract

The existing shared Newmark residual, general tangent solve, material candidate
commit/rollback and cancellation services are used. New opt-in profile and V17
checkpoint bind the contributor contract and path budgets. Old profiles retain
their schema and analysis-contract keys. Resume does not restore an executable
object from data. The existing transient archive adds one exact known inert
`DeformableBeamS3Results` record; old result fields and numeric wire tags remain.

## References and reporting

The matched uniform-normal fixture is strain free by explicit constraints.
Its independent masses are rho*A*L and rho*t*area, and effective stiffness is
line_stiffness*L. The independent discrete Newmark and flight/sine/separation
references quantify response and temporal sensitivity. Its energy is kinetic
plus the unchanged line potential; the fixed gate is 1%. This formula does not
assert that general von Karman stored energy equals one-half u Kref u.

Unequal target nodal motion is a separate genuinely deforming case. Its checks
recover actual structural internal work, mass inertia and generalized constraint
reactions at accepted states, then form each body's physical force and moment
about global origin, including position cross force. Forces and moments use
separate 0.5 N / 0.25 Nm scales, gate 1e-6. Local virtual work and directional
tangent use 1e-5. The fixture physical gap gate is 10 micrometres. Generalized
reaction components are not automatically physical moments without the node and
skin work maps. No general deforming-body energy acceptance is claimed here.
