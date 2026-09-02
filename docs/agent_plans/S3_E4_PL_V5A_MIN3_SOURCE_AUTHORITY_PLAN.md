# S3 V5A MIN3 Source and Equation Authority Gate

## Purpose

V4D is not eligible for threshold relaxation or re-adjudication.  A direct
constant-shear patch check (`w=x, theta=0` and `w=y, theta=0`) gives a nonzero
Q4/two-S3 action residual and an S3/Q4 energy ratio of approximately 0.35545.
V4E additionally establishes that this mismatch is order `t`, not PL work or
the corrected Hermite bending term.  V4E therefore remains closed as
`UNCLASSIFIED_E4_PL_S3_V4E_SHEAR_FORMULATION_REPLACEMENT_REQUIRED`.

The next candidate family is the published three-node anisoparametric Mindlin
plate element, MIN3.  This gate binds the public equations before any mechanics
is written.  It authorizes only a bounded, unrelaxed local/interface screen.
It does not authorize production, Stage 4A, thin-regime qualification, or use
of an empirically selected coefficient.

## Source authority

The implementation equation authority is the public University of Hawaii
report UHM/CE/02-02 by Liu and Riggs.  Chapter 2 reproduces MIN3:

- equations 2.20-2.22: the virgin quadratic deflection, linear rotations, and
  continuous constant-shear edge constraints;
- equations 2.23a-e: the constrained three-node anisoparametric fields;
- equations 2.24a-e: bending/shear operators and constitutive matrices;
- equation 2.25: the consistent distributed and boundary load vector;
- equations 2.26-2.27: moment and shear resultants; and
- equation 2.28a: the explicit unrelaxed/relaxed stiffness split.

NASA/TP-2018-220079 independently reproduces the anisoparametric field in
equations 22a-e and the shape functions in Appendix A, equations A.1-A.4.
The original Tessler-Hughes paper is identity authority through DOI
`10.1016/0045-7825(85)90114-8`.

The public equations define the relaxation law in equations 2.28b-c but state
only that `C_s` was determined numerically.  They do not publish its value in
the bound source bytes.  Consequently V5A freezes `phi^2=1` and uses the
unrelaxed `K_s*` only for a feasibility screen.  A relaxed or thin-regime
candidate requires a successor equation-authority gate with a hash-bound,
source-published value or rule for `C_s`.  Fitting `C_s` to Q4 or qualification
results is forbidden.

## Candidate and bounded screen

Candidate:
`CANDIDATE_E4_PL_S3_V5A_MIN3_UNRELAXED_FLAT_LINEAR_SCREEN_V1`.

The screen reuses the already reviewed S3 membrane and PL completion as fixed
components and replaces only the transverse bending/shear operator with the
source-defined MIN3 operator.  The producer and independent checker must map
the source equations separately.  Hard local gates are:

- source shape-function identities and continuous edge shear;
- exact rigid transverse modes, constant shear, and constant curvature;
- symmetry, expected physical rank/nullity, D3 covariance, director reversal,
  load work, and resultant conjugacy;
- exact continuum action and energy for the common polynomial patch space; and
- interface action-reaction for 1x1, 2x2, and 4x4 slash, backslash, and
  alternating macrocells.

Arbitrary nonpatch Dirichlet-to-Neumann differences against Q4 are diagnostics,
not exact-equality gates.  This corrects the overly broad V4 trace comparison
without weakening the genuine constant-shear contradiction.

Only after the local gates pass may the screen run the preregistered N20/N40
5% and 10% development samples.  Backslash/alternating, 25%, chain, and all-S3
cases remain holdouts.  No Stage 4A record may be launched.

Each child uses one numerical-library thread, no more than 24 GiB, and no more
than 600 seconds.  At most three children run concurrently, a complete wave is
bounded to 1,800 seconds, no automatic retry is allowed, and two fresh cycles
must have byte-identical canonical scientific outputs.

## Decisions and boundaries

Terminal precedence for the eventual V5A screen is:

1. `BLOCKED_E4_PL_S3_V5A_PROCESS_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V5A_SOURCE_OR_LOCAL_OPERATOR`
3. `NO_GO_E4_PL_S3_V5A_MIXED_INTERFACE`
4. `UNCLASSIFIED_E4_PL_S3_V5A_RELAXATION_AUTHORITY_REQUIRED`
5. `PROVISIONAL_GO_E4_PL_S3_V5A_RELAXED_SUCCESSOR_SCREEN`

The source gate itself may authorize the unrelaxed screen because equations
2.23-2.28a are complete for that scope.  Even a successful unrelaxed screen
cannot authorize activation or Stage 4A.  ANYmesh remains untouched, qualified
Q4 mechanics remain unchanged, and `DEFAULT_S3_FORMULATION` remains
`legacy-s3`.
