# S3 E4-PL V4A Q4-subcell successor preregistration

## Decision

V3A is closed as `NO_GO_E4_PL_S3_V3A_LOCAL_OPERATOR`.  Its source-native
MiSP3 moment block is positive definite and its six rigid motions are exact,
but independent rational reconstruction gives coupling rank 5, physical rank
8, and final rank 11.  The required ranks are 6, 9, and 12.  The unexecuted
macrocell, development, and Stage 4A stages remain unexecuted.

V4A screens a coefficient-free construction derived from the already
qualified Q4 rather than selecting another unrelated triangular shear rule.
Its reserved identity is
`CANDIDATE_E4_PL_S3_V4A_Q4_SUBCELL_CONDENSED_FLAT_LINEAR_V1`.
It is research-only and does not identify implemented or qualified mechanics.

## Frozen construction

For triangle vertices `v0,v1,v2`, create physical edge midpoints `m01,m12,m20`
and the barycentre `c`.  Cover the triangle by exactly three positively
oriented sub-quadrilaterals:

1. `(v0,m01,c,m20)`;
2. `(v1,m12,c,m01)`;
3. `(v2,m20,c,m12)`.

Each subcell uses the frozen qualified E4-PL Q4 tangent and load operator with
unchanged coefficients, quadrature, recovery conventions, and physical
director.  Midpoint values for all six nodal coordinates are constrained to
the arithmetic mean of their two endpoints.  The six barycentre coordinates
are independent internal coordinates.  After subcell assembly and midpoint
restriction, statically condense the barycentre by two-sided equilibrium.

The same total-energy condensation transformation must decompose the final
tangent into transformed physical, PL, and hourglass contributions whose sum
is the exact total Schur complement.  Consistent external load work is reduced
by the same equilibrium equations.  Numerical PL/hourglass quantities remain
diagnostic and cannot enter physical resultants or recovery.  There are no
tunable coefficients, empirical blending weights, or qualification-derived
parameters.  Any change to subcell topology, midpoint constraint, barycentre
definition, Q4 formulation identity, condensation rule, or load reduction
creates a successor formulation ID.

## Bounded feasibility screen

The implementation screen must proceed in this order:

1. validate the exact subcell partition and constraint map before importing
   Q4 mechanics;
2. verify the barycentre block is invertible and the condensed triangle has
   exact symmetry, six rigid modes, physical rank 9, total rank 12, work
   conjugacy, constant membrane/bending/shear patches, all six D3 transports,
   and physical-director reversal;
3. compare a qualified Q4 macrocell and its two-V4A replacement for slash,
   backslash, and alternating diagonals, including 1x1, 2x2, and 4x4
   Dirichlet-to-Neumann maps and exact rigid/constant/affine trace actions;
4. only after the prior gates pass, run the registered slash/dispersed 5 and
   10 percent N20/N40 development records.

Full unrestricted Q4/V4A matrix equality is diagnostic.  Backslash,
alternating, chain, 1 percent, 25 percent, and all-S3 development sequences
remain holdouts.  Stage 4A remains separately authorized and cannot run in
this gate.

Each child has one numerical-library thread, a 24 GiB process-tree memory
limit, and a 600 second wall limit.  A complete wave has an 1800 second limit,
at most three workers, checkpoint monitoring, complete process-tree
termination, and no automatic retry.  Two fresh-directory cycles must produce
byte-identical canonical scientific output.

## Terminals

Terminal precedence is:

1. `BLOCKED_E4_PL_S3_V4A_PROCESS_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V4A_CONSTRUCTION_IDENTITY`
3. `NO_GO_E4_PL_S3_V4A_LOCAL_OPERATOR`
4. `NO_GO_E4_PL_S3_V4A_MIXED_INTERFACE`
5. `PROVISIONAL_GO_E4_PL_S3_V4A_STAGE4A_RERUN`

The successful preregistration terminal authorizes only the bounded V4A
implementation screen.  It does not authorize production code, Stage 4A,
default activation, release, ANYmesh changes, or improved S4 work.  Qualified
Q4 and `DEFAULT_S3_FORMULATION="legacy-s3"` remain unchanged, and every result
retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
