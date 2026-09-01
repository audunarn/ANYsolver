# S3 E4-PL V4E thickness-scaled shear diagnosis preregistration

## Decision

V4D is closed as `NO_GO_E4_PL_S3_V4D_MIXED_INTERFACE`.  The Hermite edge
identity corrected the V4C constant-curvature contradiction while preserving
physical rank 9, PL rank 3, total rank 12, the six rigid motions, symmetry,
D3 covariance, and director reversal.  Independent reconstruction nevertheless
finds a relative interface-action residual of approximately 0.737 for the
registered linear-rotation trace.  N20/N40 and Stage 4A were not run.

V4E is a diagnostic gate, not a new formulation.  It determines whether the
remaining contradiction has a nonzero thin-limit shear contribution in the
V4D Q4-subcell construction.  It may authorize source selection for a new
formulation, but it may not alter V4D or authorize activation.

## Frozen diagnostic

Use the unchanged V4D operator and the unchanged qualified Q4 comparator on a
single square macrocell divided by slash and backslash diagonals.  Apply the
registered trace `w=0, theta_x=x, theta_y=y, theta_d=0`.  Its PL work is zero.
Evaluate thickness ratios `1`, `1/10`, `1/100`, and `1/1000`, setting the same
thickness in every Q4 subcell and native PL construction.

For each thickness and diagonal record only deterministic hexadecimal values
for the Q4 energy, V4D energy, energy ratio, and relative boundary action.  The
independent checker reconstructs every matrix without importing the V4E
producer.  It also verifies the constant-curvature and quadratic-transverse
traces remain within the registered identity diagnostic.

A nonzero stable residual as thickness decreases from `1/100` to `1/1000`
isolates the order-`t` shear projection/condensation, because bending is
order-`t^3` and the chosen trace has zero PL work.  The classification requires
both thin residuals above `0.1`, their absolute difference at most `0.01`, and
both thin energy ratios strictly between zero and one with absolute difference
at most `0.01`.  These are disposition thresholds, not qualification
tolerances and not tunable mechanics coefficients.

## Execution and terminals

Run two fresh deterministic cycles.  Each child has one numerical-library
thread, 24 GiB, and 600 seconds; the complete wave has 1800 seconds, at most
three concurrent workers, exclusive outputs, process-tree termination, and no
automatic retry.

Terminal precedence is:

1. `BLOCKED_E4_PL_S3_V4E_PROCESS_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V4E_DIAGNOSTIC_IDENTITY`
3. `UNCLASSIFIED_E4_PL_S3_V4E_SHEAR_SOURCE_UNRESOLVED`
4. `UNCLASSIFIED_E4_PL_S3_V4E_SHEAR_FORMULATION_REPLACEMENT_REQUIRED`

The expected replacement terminal authorizes only a separately preregistered
V5 published-formulation source selection.  It does not authorize another
Q4-subcell coefficient adjustment, N20/N40, Stage 4A, production code, or S3
activation.  Qualified Q4, ANYmesh, all references and tolerances, and
`DEFAULT_S3_FORMULATION="legacy-s3"` remain unchanged.  Every outcome retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
