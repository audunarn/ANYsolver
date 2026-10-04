# Private distributing reference-linear compiler — 4 October 2026

Implementation/test status: IMPLEMENTED_NOT_QUALIFIED. This slice adds one
model-bound local operator, with no public facade, owner wiring or qualification.
Scientific F04/G0/G2 acceptance remains open. No legacy law/default changed.

The separate identity is
`GE_FLAT_Q4_DISTRIBUTING_DIRECTOR_POLAR_REFERENCE_LINEAR_V1_EXPERIMENTAL`.
It extracts the existing area-mean/director/polar-yaw prototype; it is distinct
from the historical position-only Procrustes candidate and BL5's released spin.
Exactly two adjacent Cartesian XY Q4 hosts, six explicitly identified shell
nodes and one existing physical beam nodal port are admitted. Reference-spatial
axes are declared identity; unsupported geometry/frames fail explicitly.

Frozen clipped integrals give area-mean translation and independent area-mean
director roll/pitch. Yaw is half the averaged planar displacement curl; shell
drilling coordinates supply no port action. The local constraint is6x42, never
a global dense matrix. Exact rational integration on stored reference coordinates
is converted once to binary64. Owned immutable buffers retain model IDs,
physical gather slots, centroid/offset, weights and source-bound identity.

For e0=b0-centroid, the declared reference-linear work law is
dc_t=du_b-dmean+[e0]cross domega_s, dc_R=domega_b-domega_s.
The transpose gives beam(f,m), shell force-f and shell moment about the area
centroid -(m+e0cross f). It preserves resultant virtual work while allowing
local nonrigid deformation; it does not enforce a pointwise welded surface.

ONE focused source suite passed34 checks in.32s (whole supervised2.191s,
sampled process-tree peak174104576B, actual numerical pools1/JIT off). Checks
cover both host orientations/asymmetric cuts, independently integrated bilinear
weights, all six infinitesimal rigid fields, director-only and distinct shear
fields, physical yaw force-couple work, eccentric force/moment/work balance,
an admissible transverse slope rejected by the existing rigid reference map,
renumbering/reordering, immutable arrays, geometry/mapping negatives and finite
input overflow. Six-row local rank is not a combined-model stability result.

Independent source review caught finite-input overflow returning nonfinite gaps
or work. The fix rejects unrepresentable computed results; new controls pass.
No numerical case was run before this correction. Different-family scientific
acceptance remains open. Actual root-source imports and command/runtime logs:
[development evidence](../../../../.qualification/b3-ge-e4-pl/r8-distributing-reference-linear-dev-20261004-v1/).

Helper SHA9768b46ab0d3fb89d083e9547f7aebe38046d800e23286ba8abe359ab1d77816;
tests SHA20d073ef846c9b20bdaddf7f53171c310a4d77a1b6af25b32ce15b56b56220ef.
No installed-wheel check is claimed for this private source-only slice. Earlier
installed results retain their original artifact scope. Next integration must
verify actual nodal-coordinate pullback and sparse/dense equilibrium/reactions
before any experimental owner admission. Finite objective pose, Hessian/chart
transport, shell energy/thinning/refinement, other hosts, overlap audits,
external comparisons and the complete footprint programme remain mandatory.

## Actual GE reference assembly bridge

The private adapter `_stiffened_shell_ge_distributing_reference.py` now binds
the derivative to actual GE model IDs, geometry, nodal gather and sparse global
numbering. Candidate rows are independent of the owner's original point/rigid
rows; it leaves the original operator, state and public definitions untouched.
Model/state guards exclude advanced or finite-chart use. This is reference-only
implementation/test evidence, not public owner admission or F04 acceptance.

A three-Q4 clamped panel places the two-host attachment outside the fixed edge.
One native B3 retains all24 internal coordinates. The same material K, supports
and physical load vector are used for the six-row distributing candidate and
36-row full-vertex rigid control. Both are solved through general sparse KKT;
a separately congruence-balanced dense LU oracle is checked against the original
unscaled equations. No SPD assumption, tangent averaging or static condensation.

| Measure | Distributing | Rigid |
|---|---:|---:|
| Full coordinates / retained |90 /24|90 /24|
| KKT dimension / nnz |84 /2888|114 /3636|
| Scaled sparse/dense q difference |2.0023e-12|9.0609e-13|
| Scaled sparse/dense multiplier difference |1.7992e-16|6.8442e-13|
| Scaled equilibrium |7.8581e-13|1.4382e-13|
| Scaled constraint residual |5.8884e-21|2.4187e-21|
| External work F.q, J |0.011270906243963727|0.006182536679271101|

Eleven focused source checks PASS in.98s; whole supervised2.7651s, sampled
process-tree peak179613696B, numerical pools1/JIT off, empty stderr. Checks include
native retained equations, original dense KKT residuals, physical support and
side force/moment balance, transpose work, an admissible nonrigid slope, actual
point-coordinate pullback, reordered inputs, immutable arrays and stale/wrong/
closed-owner negatives. The distinct compliance is an outcome of these different
connection laws, not a physical superiority criterion or a general stability proof.

One pre-test startup attempt selected a runtime without psutil; it launched no
test child or numerical work. Its failure is retained. The successful run uses
the preceding Python3.14 environment, NumPy2.4.6/SciPy1.17.1/pytest9.0.3.
No installed-artifact result is claimed. Supporting independent OpenAI source
review found no blocking defect; different-family scientific acceptance remains
open. Guards cover model/state/mapping, not arbitrary mutation of private element
objects or K buffers. Saved JSON response arrays rely on the separate source and
input bindings, rather than proving their own physical admissibility.

Adapter SHAaaabc0f02721cca7a71531a1b4ce0afbc99028e8a34ccf67e5f9224ff6d376cc;
tests SHA02c11ffeb4cd5c25097f85bceb32558fdc8009abb35543633c787e80610dd608.
[Commands, runtime, responses and review](../../../../.qualification/b3-ge-e4-pl/r8-distributing-ge-reference-dev-20261004-v1/).
Next product boundary is explicit experimental reference-linear owner admission
and lifecycle/recovery integration; finite pose/Hessian/chart transport, other
geometry/materials, physical references and complete footprint acceptance stay open.
