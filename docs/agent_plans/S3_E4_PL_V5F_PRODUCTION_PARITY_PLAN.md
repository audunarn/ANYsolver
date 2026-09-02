# S3 E4-PL V5F production-candidate parity

## Purpose

Port the source-authorized V5B MIN3 relaxation into an isolated production
candidate before any modal, buckling, restart, or performance qualification.
The historical V2A production candidate and all V5B/V5E evidence remain
immutable.

## Candidate

Add `StrictFlatLinearE4PLS3V2BShellElement` with:

- selector `e4-pl-s3-v2b` (and exact alias `qualified-s3-v2b`);
- formulation ID `CANDIDATE_E4_PL_S3_V2B_FLAT_LINEAR_V1`;
- a successor implementation/schema identity;
- exact `CBMIN3=2`, equivalent to UHM `C_S=1/2`;
- element-level relaxation
  `phi_squared = 2*psi_hat/(1+2*psi_hat)`, where `psi_hat` is the ratio of
  the bending and unrelaxed-shear rotational diagonal sums over local shell
  indices `(3,4,9,10,15,16)`.

Scale only the integrated physical shear stiffness by `phi_squared`.  Keep
membrane, bending, PL, pressure work, frame, D3 transport, support admission,
quadrature, and tolerances unchanged.  Scale recovered shear resultants by the
same factor so their virtual work equals the relaxed shear stiffness; retain
the kinematic shear strain as an unscaled physical field and report the
relaxation factor explicitly.

V2B is additive and opt-in.  Do not change Q4, `DEFAULT_S3_FORMULATION`, the
existing V1/V2A selectors, serialization defaults, or ecosystem routing.

## Gate

Compare the production candidate with the accepted V5B reference and its
independent checker for local component matrices, total stiffness, relaxation
factor, D3 transports, director reversal, pressure work, internal force, and
variational-resultant work.  Exercise the complete N20/N40/N80 Stage 4A
catalog through the production selector and require byte-identical scientific
summaries in two bounded cycles.

Each child is limited to one numerical thread, 24 GiB, and 600 seconds; the
complete wave is limited to 1,800 seconds with at most three workers and no
automatic retry.

Terminal precedence:

1. `BLOCKED_E4_PL_S3_V5F_PRODUCTION_PARITY_PROCESS_OR_EVIDENCE`;
2. `NO_GO_E4_PL_S3_V5F_PRODUCTION_PARITY`;
3. `PROVISIONAL_GO_E4_PL_S3_V5F_STAGE4B_EXECUTION_PREPARATION`.

A pass authorizes only separately frozen Stage 4B execution.  It does not
authorize S3 activation or any default change.  Every result retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
