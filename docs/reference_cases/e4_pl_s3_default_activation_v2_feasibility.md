# S3 default-activation protocol-v2 feasibility checkpoint

Status: preregistered implementation and runtime investigation only. No
formal cycle was launched, no canonical scientific aggregate was created, and
default S3 activation is not authorized by this checkpoint.

## Frozen candidate graph

The qualification candidate includes the relevant pre-existing local changes
on dedicated branches:

- ANYsolver `ab1139dfef497d19549f9153b95439764daa5a90`.
- ANYmesh `c1af6d5fab9a0ae301d14d9d5877b75362e7c6d1`.
- ANYfem `a3302d9c33be0d9f94d315cfadbab6e0a0022e64`.
- ANYstructure `830d1f2426f7fd9cf86485be6cea28a06f266ab5`.
- ANYintelligent `ba34973e0f4c093bbba7d60647f767e68ceb0087`.
- ANYfileIO `38102df2744fd0da72977a7cf10e7c93bb422cfa`.

The four package candidates were built from clean `git archive` snapshots and
installed into `s3-default-activation-ab1139d/isolated-target`. All package
origins resolved inside that target.

## Corrected protocol defects

- Hard-Navier rotations are `rx=0` on x-edges and `ry=0` on y-edges. The
  previous v2 draft had these constraints swapped and behaved as an
  over-stiff support.
- The classifying energy quantity is the discrete stiffness-energy norm of
  `u_h - I_h u_ref`, where the reference is the independently authored
  Reissner-Mindlin modal field. The historical total-energy-defect proxy is
  retained only as a nonclassifying diagnostic.
- Physical shell rotation mapping is `ry=theta_x`, `rx=-theta_y`.
- Twelve 4096-element batch measurements are partitioned without overlap over
  three fresh processes and recombined before adjudication.
- Execution is three bounded waves, at most three processes concurrently,
  540 seconds per child, and 1200 seconds for the complete command.

## Runtime investigation

The corrected all-Q4 N=20 smoke produced:

- center-displacement relative error `0.0004503787985691765`;
- discrete energy-norm error `0.0920927678173153`;
- historical energy-defect proxy `0.07502608130959489`.

An N=80 `cProfile` diagnostic completed in 159.034 seconds under profiling and
reported approximately 646 million function calls. Repeated qualified runtime
boundary checks dominated the run: `boundary_guard` accumulated 126.742
seconds, while cold assembly and load construction accumulated 95.165 seconds.
An unprofiled N=160 smoke took approximately four minutes.

Therefore, 63 independent sequences with an N=160 record each cannot complete
inside the user-mandated 20-minute ceiling. Parallel scheduling alone does not
repair this. A formal cycle was deliberately not started.

## Qualified-lease hardening result

The first successor action was implemented and frozen as ANYsolver commit
`e7060294a10b2ee8c18b4001e9194f608986d53e`, tree
`049c663c52e05231e186771b8a51f24f8492aafe`. It adds exact cold assembly,
dead-pressure load, narrow interface-recovery, and flexural-solve paths under
non-renewable qualified leases. The Q4 and S3 formulation blobs remain exactly
`59ceb9534dfd22e05ea69296f92abeb0511f14cf` and
`823b5b0cdc450f7c7f2f2861aefcf4dd2062b99e`, respectively.

Verification before the timing smoke comprised 227 focused tests and 76
adjacent load, assembly, and recovery regressions. All 303 passed. An
independent adversarial re-review found no remaining P0, P1, or P2 runtime
finding in the hardened paths.

A bounded, nonclassifying N=20/N=40 smoke then ran six fresh child processes
with three-way overlap, a 120-second per-child limit, a 300-second global
limit, one numerical-library thread per child, and a 24-GiB child-tree memory
limit. All children completed; the coordinator elapsed time was 23.858
seconds. The canonical smoke summary is 3,058 bytes with SHA-256
`EADD63EEA7CD1BA4DBC738B15CEBE522953ACF819A7DC653F06A1B88E30BEB4A`.

The registered conservative partial forecast lower bound is
683.3075 seconds, exceeding the 480-second acceptance budget. Consequently,
N=80/N=160 timing expansion and both formal qualification cycles were not
started. This smoke is explicitly
`NONCLASSIFYING_E4_PL_S3_COLD_PATH_TIMING_ONLY`; it creates no scientific
aggregate and leaves `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` in force.

The optimized runner also requires a new successor execution-authority freeze
before any formal use. The historical v2 authority is intentionally preserved;
it does not bind the optimized runner, and its batch-program raw-byte binding
is not portable under Windows CRLF checkout. A successor must bind an
LF-controlled executed batch-program path and pass authority-only validation
from a fresh Windows checkout.

## Required successor action

Before formal execution, choose and independently review one of these paths:

1. further optimize the bounded plate-record path until a conservative forecast
   proves both complete cycles fit the acceptance budget, then create and
   review a successor LF-stable execution-authority freeze;
2. preregister a smaller nonclassifying screening campaign that cannot
   authorize default activation.

The existing complete 252-record acceptance scope must not be silently
reported as executed by a smaller campaign.
