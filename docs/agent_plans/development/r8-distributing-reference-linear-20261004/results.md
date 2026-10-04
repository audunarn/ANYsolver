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
