# S3 E4-PL V4C physical-first Q4-subcell preregistration

## Decision

V4A and V4B are closed local-operator NO-GOs.  Both preserve six rigid modes,
symmetry, D3 covariance, director reversal, and final rank 12, but both produce
physical rank 11 instead of 9.  Releasing all three midpoint drill coordinates
in V4B leaves that rank unchanged.  This proves that the defect is not the
midpoint drill constraint; it is the use of the total Q4 numerical-coordinate
equilibrium map when defining the transformed physical component.

V4C separates the physical and numerical constructions before condensation.
Its reserved research identity is
`CANDIDATE_E4_PL_S3_V4C_Q4_SUBCELL_PHYSICAL_FIRST_FLAT_LINEAR_V1`.

## Frozen physical construction

Retain the three V4 subcells and physical points.  From each unchanged qualified
Q4 use only its hash-bound `physical/core` block.  Work in the local numbered
surface frame and retain exactly five physical coordinates at every point:
three translations and two director rotations.  All Q4 drilling rows and
columns are excluded from the physical restriction.

The 42 Q4 coordinates are restricted to exactly 20 physical coordinates:

- 15 external corner physical coordinates;
- five independent barycentre physical coordinates.

Every midpoint physical coordinate is the arithmetic endpoint average.  The
barycentre coordinates are independent.  Restrict the assembled Q4 physical
core and condense the five barycentre coordinates through physical equilibrium.
Embed the resulting 15-by-15 operator into the 18 external S3 coordinates with
zero physical drilling rows and columns.  Physical load work is reduced through
the same physical equilibrium map.

## Frozen numerical completion

After physical condensation, add the previously accepted barycentric S3 PL
completion without importing any failed V1 physical operator.  With
`omega=(v_,x-u_,y)/2` and `(Cq)_i=theta_D,i-omega`, use

`M=A/12 [[2,1,1],[1,2,1],[1,1,2]]` and `K_D=k_D C^T M C`.

The drill scale remains
`k_D=1/2 lambda_min(P^T A P,diag(2,1/2))`, using the elastic membrane section.
The PL block must have rank 3, may not enter physical resultants or recovery,
and must raise the final rank from 9 to 12.  Q4 PL/hourglass blocks are not
carried into V4C.  No empirical coefficient, blending, tuning, quadrature,
topology, Q4 mechanic, scientific tolerance, or reference changes.

Any change to the physical coordinate selection, midpoint relation,
barycentre definition, physical condensation, PL basis, drill scale, or load
reduction creates a successor formulation ID.

## Bounded screen

The screen proceeds in strict order:

1. validate the exact subcell partition, 42-by-20 physical restriction, and
   external 15-to-18 embedding without importing Q4 mechanics;
2. verify the five-coordinate internal physical block is invertible, the
   condensed physical rank is 9 with six rigid modes, the PL rank is 3, and the
   final rank is 12; also verify symmetry, component sum, work conjugacy, all
   six D3 transports, and physical director reversal;
3. only after the local gate passes, compare slash, backslash, and alternating
   two-triangle macrocells plus 1x1, 2x2, and 4x4 Dirichlet-to-Neumann traces;
4. only after the macrocell gate passes, run the registered slash/dispersed 5
   and 10 percent N20/N40 development records.

Backslash, alternating, chain, 1 percent, 25 percent, and all-S3 development
remain holdouts.  Stage 4A remains separately authorized.  Each child has one
numerical-library thread, 24 GiB process-tree memory, and 600 seconds.  A wave
has at most three workers and 1800 seconds, with exclusive outputs, complete
tree termination, checkpoints, no automatic retry, and two byte-identical
fresh-directory scientific cycles.

Terminal precedence is:

1. `BLOCKED_E4_PL_S3_V4C_PROCESS_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V4C_CONSTRUCTION_IDENTITY`
3. `NO_GO_E4_PL_S3_V4C_LOCAL_OPERATOR`
4. `NO_GO_E4_PL_S3_V4C_MIXED_INTERFACE`
5. `PROVISIONAL_GO_E4_PL_S3_V4C_STAGE4A_RERUN`

Preregistration authorizes only the bounded V4C screen.  Production S3 remains
legacy, qualified Q4 remains unchanged, ANYmesh remains untouched, activation
and release remain unauthorized, and every outcome retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
