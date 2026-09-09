# P5 equilibrated reference flexibility — 2026-09-05

Author development successor to `30e396c4acdf57552efa45eba0b141f49d721991`.
This record neither changes nor supersedes accepted P3/P4 scientific evidence.
The P5 algebra, finite, and QR probes and their records remain unchanged.

## Equivalent reference calculation

The mixed reference potential on a half cell can be written in dual form:

`z.p + ell.m - (p-J^T m)^T F^-1 (p-J^T m)/2 - m^T H m/2`.

Here p is the force conjugate to z and m contains the two material endpoint
moments. Eliminating p and m recovers the existing P5 reduced potential.
Stationarity in the internal reference rotation requires
`-chord cross p + M_left - M_right = 0`.

Parameterize that equilibrium exactly by the six coordinates (p,t), with
`M_left=t` and `M_right=t-chord cross p`. Their external work is
`p.(du+chord cross theta_right) + t.(theta_right-theta_left)`.
Use a proper chord-aligned numerical basis E and let W map these six
coordinates to material endpoint moments. With `V=[E,0]-J^T W`, the
complementary flexibility is

`S = V^T F^-1 V + W^T H W`.

This is positive definite for the admitted reference problem. Diagonal
equilibration followed by Cholesky solves S; no diagonal regularization,
penalty, pseudoinverse, tolerance adjustment, spectral truncation or empirical
coefficient is introduced. The structural zero for the axial-force column
of `chord cross p` is retained explicitly. Numerical basis choice uses
existing material frame directions and does not redefine material roll.

The implementation retains the work-coordinate evaluation and solves the
six-dimensional flexibility. It does not assemble a dense nodal stiffness
for low-energy contractions. Forming that dense stiffness can reintroduce
the cancellation identified in the earlier checkpoint.

## Reference conditioning result and its limits

For the twelve previously inspected constant-spatial-moment cases (three
geometries, rho = 1, 100, 10000, 1000000), relative energy errors now range
from zero to 5.86e-16. All meet the unchanged 1e-11 check. At rho = 1000000:

| Geometry (height, shift, twist) | Relative energy error |
|---|---:|
| (0, 0, 0) | 0 |
| (0.4, 0, 0) | 1.58096e-16 |
| (0.6, 0.2, 0.15) | 4.38881e-16 |

The new test contains a separate 80-digit Decimal reconstruction of the
original primal stationary equations. It converts binary64 coordinates,
frames, displacements and F/H/J integrals exactly to Decimal, assembles
the local three-rotation Hessian and gradient, solves them by deterministic
Gaussian elimination, and evaluates the original potential. It imports
neither the flexibility factors nor a rounded assembled stiffness. All
twelve low-energy comparisons meet 1e-11. Coupled section comparisons at
rho = 1 and 1000000, at displacement amplitudes 1 and 1e-6, also meet it.

This is independent arithmetic and a separate algebraic reconstruction, not
independent authorship or independent physical/continuum evidence. Both
calculations share the same binary64 reference metric integrals. The check
does not qualify quadrature, curved engineering response, the domain of
geometries, finite-state mechanics, or the full slenderness range. No source
equation map or independent review is newly accepted here.

High-contrast moment recovery and energy covariance/reversal are checked.
Axial force on rounded nearly inextensional nodal data remains sensitive to
conditioning; it is not forced to zero and is not claimed qualified by an
energy check. Reference-only flexibility is not a finite geometric tangent.

## Separate finite-state failure found

An unchanged `CurvedFiniteProbe` was evaluated once at each of four stiffness
contrasts using helper `reference(0.6,0.2,0.15)`, the existing `perturbed(ref)`
positions/vertex frames, and section diag(rho^2,rho^2,rho^2,1,2,3).
Its existing defaults were retained: at most 25 Newton iterations, at most
12 backtracks, and absolute local residual tolerance 1e-11.

| rho | Outcome |
|---:|---|
| 1 | Solved in 2 iterations; residual 1.9116652705264414e-15 |
| 100 | Solved in 4 iterations; residual 1.2346235145344053e-12 |
| 10000 | `LocalStationarityError: local line search failed after 12 trials` |
| 1000000 | `LocalStationarityError: local line search failed after 12 trials` |

The entire four-case diagnostic command exited normally in about 2.3 seconds;
expected probe failures were explicitly reported, not converted into accepted
responses. No retry or higher iteration/tolerance override was attempted.
These are new author diagnostics, not reruns of a consumed formal request.

The finite failure mechanism is not yet fully established. Strong force
penalties and subtraction in the local strain are plausible conditioning
sources, but iteration traces and a separate formulation-equivalent check
are needed before making that attribution definitive. The new reference
algorithm does not fix this finite solver.

## Verification, preserved boundary, and next action

- New flexibility suite: 17 passed in 1.87 seconds.
- Existing algebra, finite and QR suites: 52 passed in 3.23 seconds.
- `git diff --check` passed before committing this checkpoint.
- No accepted source, existing probe/test, production element, default,
  dependency, public alias, package or workflow was edited.
- No resource request, formal execution, candidate freeze, independent
  scientific review, merge, release or publication was created.

New probe SHA-256:
`8A0C2D75EDDA2931F252FEC2C2BF96FD2D026FAAB0074F4933B8E82DFF067266`.

New `tests/test_ge_beam3_curved_p5_flexibility_probe.py` SHA-256:
`8340136F3134B63AD765D049B430E8F3313BBE774F0A98FE0405BDCFB921E72C`.

Next: diagnose finite local iteration accuracy and evaluate an equivalent
force/moment mixed solve with scaled equations if supported by that evidence.
Derive its finite SO(3) variations; do not assume the reference linear
moment-equilibrium parameterization is valid in the finite problem. Keep
bounded rejection and the same potential/tolerances. Do not start assembled
qualification until the local finite failure is understood and corrected.

The overall goal remains active and incomplete, including nonlinear sections
for straight/curved beams, curved engineering qualification, postbuckling,
mass/dynamics/restart, installed-wheel exposure and objective beam-shell
connections. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
