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

## Required successor action

Before formal execution, choose and independently review one of these paths:

1. optimize the qualified cold-path guard under its existing non-renewable
   operation lease, then rerun guard mutation tests and bounded timing smoke;
2. preregister a smaller nonclassifying screening campaign that cannot
   authorize default activation.

The existing complete 252-record acceptance scope must not be silently
reported as executed by a smaller campaign.
