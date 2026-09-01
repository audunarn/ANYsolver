# S3 V5B MIN3 Relaxation Equation Authority Gate

## Purpose

V5A established that the source-defined unrelaxed MIN3 operator satisfies the
local patch, interface action-reaction, covariance, and bounded N20/N40
development gates.  It deliberately stopped before thin-regime use because
UHM/CE/02-02 gives the relaxation law but does not publish the numerical value
of its constant `C_s` in the bound report bytes.

V5B closes only that equation-authority gap.  No coefficient may be inferred
from Q4, Stage 4A, or qualification results.  The next mechanics run is allowed
only if an independently checkable public implementation and manual bind the
constant, the formula, and the original MIN3 publication identity.

## Bound source chain

The primary field/operator equations remain UHM/CE/02-02, equations
2.23-2.28.  A frozen checkout of the official MYSTRAN project supplies the
missing implementation authority:

- `dev_docs/BD_PARAM.md` states that `CBMIN3` defaults to `2.0` and that this
  is the value suggested by the author for the reference-three TRIA3 plate;
- `Source/Modules/PARAMS.f90` initializes `CBMIN3` to `TWO`;
- `Source/EMG/EMG4/TPLT2.f90` identifies the element as the Tessler-Hughes
  1985 MIN3 and forms `K = K_b + phi^2 K_s*`;
- `Source/EMG/EMG4/CALC_PHI_SQ.f90` defines
  `psi_hat = BENSUM/SHRSUM` and
  `phi^2 = CBMIN3*psi_hat/(1 + CBMIN3*psi_hat)`; and
- `Source/EMG/EMG2/ELMOUT.f90` independently emits that same runtime formula.

The official MYSTRAN user manual repeats the `2.0` default, says it was
suggested by the author, and identifies reference three as Tessler and Hughes,
“A three-node Mindlin plate element with improved transverse shear,” CMAME 50
(1985), 71-101.

The Git commits, trees, blobs, byte counts, and SHA-256 digests are frozen in
the source-selection record.  These sources are implementation/equation
authority only; MYSTRAN is not imported or used as a scientific oracle.

## Exact parameter map

Let the UHM quantities be

`alpha = SHRSUM/BENSUM`

and

`phi^2 = 1/(1 + C_s*alpha)`.

MYSTRAN uses the reciprocal variable

`psi_hat = BENSUM/SHRSUM = 1/alpha`

and

`phi^2 = CBMIN3*psi_hat/(1 + CBMIN3*psi_hat)`.

For positive bending and shear diagonal sums this is identically

`phi^2 = 1/(1 + alpha/CBMIN3)`.

Therefore the source-published `CBMIN3 = 2` maps exactly to UHM
`C_s = 1/2`.  The V5B candidate must use that exact rational constant.  Using
`C_s = 2`, tuning the value, or changing the diagonal-sum definitions is a
source-authority failure.

## Authorized successor screen

Candidate:
`CANDIDATE_E4_PL_S3_V5B_MIN3_RELAXED_FLAT_LINEAR_SCREEN_V1`.

After this gate is accepted, V5B may apply the source-defined `phi^2` to the
already reviewed V5A `K_s*`.  It must preserve the V5A interpolation,
quadrature, bending operator, shell rotation map, PL completion, load work,
and all production boundaries.

The bounded repair funnel must rerun the V5A local and macrocell identities,
then add a preregistered thickness ladder and the held-out N20/N40/N80 mixed
sequences.  It may use no fitted coefficients or relaxed scientific
thresholds.  Two fresh cycles must be byte-identical.  Each child remains
bounded to 600 seconds, 24 GiB, and one numerical-library thread; at most three
children may overlap, a wave is bounded to 1,800 seconds, and automatic retry
is forbidden.

## Decisions and boundaries

Terminal precedence for the eventual V5B screen is:

1. `BLOCKED_E4_PL_S3_V5B_PROCESS_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V5B_RELAXATION_SOURCE_OR_LOCAL_OPERATOR`
3. `NO_GO_E4_PL_S3_V5B_MIXED_INTERFACE`
4. `NO_GO_E4_PL_S3_V5B_THIN_REGIME`
5. `PROVISIONAL_GO_E4_PL_S3_V5B_STAGE4A_RERUN`

This authority gate can authorize only the bounded V5B repair funnel.  It
cannot authorize Stage 4A, production, or default activation.  ANYmesh remains
untouched, qualified Q4 mechanics remain unchanged, and
`DEFAULT_S3_FORMULATION` remains `legacy-s3`.
