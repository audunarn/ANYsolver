# S3 E4-PL V3 formulation preregistration plan

## Decision

V1 and V2A are closed scientific predecessors, not implementation templates. V1
failed every registered interface-resultant comparison and 47 of 63 mixed
convergence sequences. V2A agrees with an independent reconstruction of the
published DKMT/T3-gamma-s equations, yet its two-triangle macrocell operator is
not compatible with the qualified Q4 operator and its N20-to-N40 development
sequences fail. Neither result may be reclassified, repaired by coefficient
tuning, or rerun.

V3A will screen the three-node MiSP3 Hellinger-Reissner formulation. The primary
authority is the open, versioned paper by Yu, Xie, and Guo, *Analysis of hybrid
methods of mixed-shear-projected triangular and quadrilateral elements for
Reissner-Mindlin plates*, arXiv:1410.3683v1. It defines the mixed variational
system, triangular finite-dimensional spaces, shear reduction operator, and
thickness-uniform stability and convergence results. Its independent bending
moment and shear-stress parameters are element-local and must be eliminated by
the source-defined variational equations.

The CS-DSG3 paper by Nguyen-Thoi et al. is retained only as a diagnostic
comparator. It is not implementation authority: its stabilized shear matrix has
an unspecified positive constant, it uses a numerical drilling penalty that is
incompatible with the accepted E4-PL completion, and it remains in the DSG
operator lineage already implicated by V2. No equation, coefficient, smoothing
rule, or result may be copied from this comparator into V3A.

The reserved candidate identity is
`CANDIDATE_E4_PL_S3_V3A_MISP3_HR_FLAT_LINEAR_V1`. This identity does not denote
implemented or qualified mechanics.

## Equation authority gate

Before mechanics code is written, create two independently authored equation
maps from the hash-bound MiSP3 paper. Both maps must cover:

- equations 2.3-2.10: moment, shear, displacement, rotation, and the
  Hellinger-Reissner bilinear forms;
- equations 3.1-3.14: the discrete scheme, shear reduction, triangular
  displacement/rotation spaces, independent moment space, projected shear
  space, and midpoint-continuous scalar space;
- the local algebra that eliminates independent moment/shear parameters;
- the hypotheses and conclusions of the MiSP3 stability and convergence
  results, including all thickness and mesh-shape restrictions;
- the exact plate-to-shell rotation, engineering/tensor shear, frame, sign,
  quadrature, loading, and constitutive conventions required by ANYsolver.

Any missing coefficient, conflicting convention, nonlocal internal variable, or
source ambiguity terminates V3A as `NO_GO_E4_PL_S3_V3_SOURCE_IDENTITY`. It may
not be filled by V1, V2, CS-DSG3, numerical fitting, or generic simplification.

The accepted barycentric E4-PL drill completion may be composed only after the
source-native physical operator passes the screen. It must remain a separate
block and may not alter physical resultants, recovery, or work.

## Bounded implementation screen

The screen is research-only and proceeds in strict order:

1. Reconstruct the source equations in a producer and independent checker that
   share no mechanics implementation.
2. Verify exact symmetry, six rigid modes, rank, work conjugacy, constant
   bending and shear patches, all six D3 reorderings, and director reversal.
3. Condense the source-local stress parameters and compare 1x1, 2x2, and 4x4
   Dirichlet-to-Neumann maps for a qualified Q4 macrocell and its two-S3
   replacement. Exact agreement is required for rigid, constant-curvature,
   constant-shear, and affine boundary-trace subspaces. The unrestricted
   operator difference is diagnostic because different conforming spaces need
   not have identical high-order stiffness.
4. Run only slash/dispersed 5 and 10 percent N20/N40 development samples.
   Backslash, alternating, chain, 1 percent, 25 percent, and all-S3 cases remain
   holdouts.

Every child has one numerical-library thread, a 24 GiB process-tree memory
limit, and a 600 second wall limit. At most three children run concurrently. A
complete wave has an 1800 second limit with checkpoint monitoring and complete
process-tree termination. There is no automatic retry. Two fresh-directory
cycles must produce byte-identical canonical scientific records.

The screen may not import production V1/V2 mechanics, change qualified Q4,
change tolerances or references, touch ANYmesh, or execute Stage 4A.

## Terminals

Terminal precedence is:

1. `BLOCKED_E4_PL_S3_V3_SOURCE_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V3_SOURCE_IDENTITY`
3. `NO_GO_E4_PL_S3_V3A_LOCAL_OPERATOR`
4. `NO_GO_E4_PL_S3_V3A_MIXED_INTERFACE`
5. `UNCLASSIFIED_E4_PL_S3_V3_FORMULATION_REPLACEMENT_REQUIRED`
6. `PROVISIONAL_GO_E4_PL_S3_V3A_STAGE4A_RERUN`

This preregistration closes only source selection and authorizes the bounded
equation/implementation screen. It does not authorize production integration,
Stage 4A, default activation, release, or an S4 change. Qualified Q4 and
`DEFAULT_S3_FORMULATION="legacy-s3"` remain unchanged, and every outcome retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
