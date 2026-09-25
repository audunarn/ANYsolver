# C3 local native B3-GE line to physical S3 interior

`NativeRetainedRoundLineS3Interior` is an internal frictionless contact
component. It evaluates both Q2 half-cells of one retained native B3-GE beam
against one deformable, ordered physical S3 skin triangle. The S3 vertex input
already includes its formulation-owned director, side, offset and thickness.
It is **not** an S3 nodal translation/rotation adapter or a coupled analysis
owner. C3 native beam–shell contact remains open.

The declared round centreline radius and normal line stiffness have units of
metres and N/m². The energy is the reference-arc integral of
`0.5 * stiffness * min(0, signed_plane_gap - radius)²`. The reference measure
comes from the native curved beam; current position uses its retained Q2
half-cell geometry. The output has a 51-coordinate residual and tangent: 42
native retained coordinates followed by nine physical S3 skin-vertex
coordinates. The second derivative includes the native internal-rotation
curvature term and full shell-normal variation. It uses the same spatial
rotation-increment convention as the retained Q2 cell adapter.

The kernel partitions the Q2 line at exact signed-gap roots, then applies
adaptive 8/16-point Gauss integration with separate dimensional energy, force
and tangent error budgets. Reported integration errors are quadrature
estimators. An exhausted interval budget raises an explicit resource error.
The complete Q2 Bézier hull must project beyond `radius + rim_clearance_m`
from every physical triangle edge. This sufficient interior certificate
rejects admissible-looking near-rim cases until rim ownership is available;
it never substitutes a point or endpoint contact. Degenerate geometry and
changed definition identity are rejected.

The ordered material S3 vertices define the physical normal. A single pose
cannot distinguish an inverted patch from a valid large rigid rotation by
comparison with the reference normal. The future analysis owner must track
orientation and swept side identity along the accepted path, map the physical
vertex work to authoritative S3 degrees of freedom, assemble shell and native
structural equations, and control initial interference, increments, state and
restart. No public native beam–shell capability is admitted by this component.

Focused development checks cover an analytic parallel plane, partial line
activation, paired force/moment balance, shell-vertex work and tangent,
retained rotation work and curvature, an independently integrated curved
scalar potential, common rigid motion through 170 degrees, opening, geometry
rejection and bounded integration. These are local tests, not independent
engineering qualification.
