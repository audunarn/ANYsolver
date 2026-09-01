# S3 E4-PL V4D Hermite-edge Q4-subcell preregistration

## Decision

V4C is closed as `NO_GO_E4_PL_S3_V4C_MIXED_INTERFACE`.  It passes the complete
local gate with physical rank 9, PL rank 3, total rank 12, six rigid motions,
symmetry, work conjugacy, D3 covariance, and director reversal.  Independent
reconstruction of all nine 1x1, 2x2, and 4x4 boundary maps nevertheless finds
a constant-curvature trace contradiction.  N20/N40 and Stage 4A were not run.

The defect is the arithmetic midpoint transverse displacement inherited from
V4C.  It cannot reproduce a quadratic bending field even when the endpoint
rotations represent its exact linear gradient.  V4D replaces only this edge
relation by the unique cubic-Hermite midpoint evaluation.  Its reserved
research identity is
`CANDIDATE_E4_PL_S3_V4D_Q4_SUBCELL_HERMITE_EDGE_FLAT_LINEAR_V1`.

## Frozen edge identity

Retain V4C's three Q4 subcells, five-coordinate physical core, independent
five-coordinate barycentre, 15-to-18 external embedding, and native
barycentric S3 PL completion.

For an oriented physical edge from node `i` to node `j`, let
`e=(x_j-x_i,y_j-y_i)`.  In the frozen shell convention the Kirchhoff gradient
represented by physical rotations is `grad(w)=(-theta_y,theta_x)`.  Define the
normalized endpoint slopes

`m_i=e_x(-theta_y,i)+e_y theta_x,i` and
`m_j=e_x(-theta_y,j)+e_y theta_x,j`.

The midpoint relations are exactly:

- `u_m=(u_i+u_j)/2`, `v_m=(v_i+v_j)/2`;
- `w_m=(w_i+w_j)/2+(m_i-m_j)/8`;
- `theta_x,m=(theta_x,i+theta_x,j)/2`;
- `theta_y,m=(theta_y,i+theta_y,j)/2`.

All Q4 drilling rows and columns remain excluded from the physical core.  The
five barycentre physical coordinates remain internal and are condensed through
physical equilibrium.  The separately accepted PL block is added only after
physical condensation.  Physical load work uses the same Hermite restriction
and equilibrium map.

This identity must reproduce `1,x,y,x^2,y^2,xy` transverse fields at all three
edge midpoints when supplied their exact gradients.  The coefficient `1/8` is
the cubic-Hermite basis value, not a tunable parameter.  Subsets, scaling,
blending, empirical stabilization, or qualification-derived adjustment are
forbidden.  Any change creates a successor formulation ID.

## Bounded screen

The screen proceeds in strict order:

1. validate the geometry-dependent 42-by-20 restriction, exact quadratic
   midpoint reproduction, and 18-by-15 embedding without importing mechanics;
2. verify the internal physical block rank 5, physical rank 9, PL rank 3,
   total rank 12, six rigid modes, symmetry, work conjugacy, all D3 transports,
   and director reversal;
3. only after the local gate passes, reconstruct all slash, backslash, and
   alternating 1x1, 2x2, and 4x4 Dirichlet-to-Neumann maps and registered
   rigid, constant-strain, constant-curvature, linear-rotation, and quadratic
   transverse traces;
4. only after the complete macrocell gate passes, run slash/dispersed 5 and
   10 percent N20/N40 development records.

The established one-thread, 24-GiB, 600-second child, three-worker, and
1800-second wave bounds remain.  Use exclusive outputs, checkpoints, complete
process-tree termination, no automatic retry, and two byte-identical fresh
cycles.  Holdouts and Stage 4A remain unexecuted until separately authorized.

Terminal precedence is:

1. `BLOCKED_E4_PL_S3_V4D_PROCESS_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V4D_CONSTRUCTION_IDENTITY`
3. `NO_GO_E4_PL_S3_V4D_LOCAL_OPERATOR`
4. `NO_GO_E4_PL_S3_V4D_MIXED_INTERFACE`
5. `PROVISIONAL_GO_E4_PL_S3_V4D_STAGE4A_RERUN`

Qualified Q4, ANYmesh, production code, tolerances, references, aliases, and
`DEFAULT_S3_FORMULATION="legacy-s3"` remain unchanged.  Every outcome retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
