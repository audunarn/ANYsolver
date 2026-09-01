# S3 E4-PL V4B Q4-subcell drill-release preregistration

## Decision

V4A is closed as `NO_GO_E4_PL_S3_V4A_LOCAL_OPERATOR`.  Its three qualified-Q4
subcells passed the construction, centre-block, symmetry, rigid-motion, D3,
director-reversal, component-sum, and final-rank checks.  The independent
checker nevertheless found physical rank 11 rather than the required rank 9.
Macrocell, N20/N40, and Stage 4A work was therefore not executed.

The contradiction is confined to the physical treatment of the three edge
midpoint drilling coordinates.  V4A constrained each midpoint drill to the
arithmetic mean of its endpoint drills even though drilling is a numerical
coordinate rather than a physical surface interpolation variable.  V4B tests
the directly implicated, coefficient-free correction: retain V4A's affine
constraints for the five physical coordinates at every midpoint, but make the
three midpoint drilling coordinates internal and eliminate them together with
the six barycentre coordinates.

The reserved identity is
`CANDIDATE_E4_PL_S3_V4B_Q4_SUBCELL_DRILL_RELEASE_FLAT_LINEAR_V1`.  It denotes a
research-only candidate, not implemented or qualified production mechanics.

## Frozen construction

For triangle vertices `v0,v1,v2`, retain the V4A points `m01,m12,m20,c` and the
same three positively oriented qualified-Q4 subcells:

1. `(v0,m01,c,m20)`;
2. `(v1,m12,c,m01)`;
3. `(v2,m20,c,m12)`.

The reduced pre-condensation coordinate vector has exactly 27 entries:

- 18 external corner coordinates;
- three independent internal midpoint drilling coordinates, ordered
  `m01,m12,m20`;
- six independent barycentre coordinates.

At every midpoint, translations and the two physical director rotations are
the arithmetic endpoint average.  Its drilling coordinate is the corresponding
independent internal coordinate.  All six barycentre coordinates remain
independent.  Assemble the unchanged qualified-Q4 physical, PL, hourglass, and
total blocks, apply this 42-by-27 restriction, and statically condense the nine
internal coordinates through the total equilibrium block.  Apply that same
two-sided equilibrium transformation to every component and to external load
work.  The transformed physical, PL, and hourglass blocks must sum to the total
Schur complement.

No coefficient, stabilization weight, quadrature rule, topology, Q4 operator,
or scientific tolerance changes.  The choice to release all three midpoint
drills is fixed before evaluating V4B mechanics; subsets and blended constraints
are forbidden.  Any change creates a successor formulation ID.

## Bounded feasibility screen

The implementation screen proceeds in strict order:

1. validate the point partition and the exact 42-by-27 restriction structure
   without importing Q4 mechanics;
2. verify the nine-coordinate internal total block is invertible and the
   condensed triangle has symmetry, six rigid modes, physical rank 9, total
   rank 12, work conjugacy, component sum, all six D3 transports, and physical
   director reversal;
3. only if the local gate passes, compare qualified-Q4 and two-V4B macrocells
   for slash, backslash, and alternating diagonals, including 1x1, 2x2, and 4x4
   Dirichlet-to-Neumann maps and the registered rigid/constant/affine traces;
4. only if the macrocell gate passes, run the registered slash/dispersed 5 and
   10 percent N20/N40 development records.

Backslash, alternating, chain, 1 percent, 25 percent, and all-S3 development
sequences remain holdouts.  Full unrestricted Q4/V4B operator equality is
diagnostic only.  Stage 4A remains separately authorized.

Each child receives one numerical-library thread, a 24 GiB process-tree memory
limit, and a 600-second wall limit.  At most three children run concurrently.
The complete wave has an 1800-second limit, checkpoint monitoring, process-tree
termination, exclusive outputs, and no automatic retry.  Two fresh-directory
cycles must produce byte-identical canonical scientific outputs.

## Terminals and boundary

Terminal precedence is:

1. `BLOCKED_E4_PL_S3_V4B_PROCESS_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V4B_CONSTRUCTION_IDENTITY`
3. `NO_GO_E4_PL_S3_V4B_LOCAL_OPERATOR`
4. `NO_GO_E4_PL_S3_V4B_MIXED_INTERFACE`
5. `PROVISIONAL_GO_E4_PL_S3_V4B_STAGE4A_RERUN`

A successful preregistration authorizes only the bounded V4B screen.  It does
not authorize production code, Stage 4A, activation, release, ANYmesh changes,
or improved-S4 work.  Qualified Q4 and
`DEFAULT_S3_FORMULATION="legacy-s3"` remain unchanged.  Every outcome retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
