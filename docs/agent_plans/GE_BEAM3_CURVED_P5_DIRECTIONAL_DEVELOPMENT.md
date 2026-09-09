# P5 compensated directional tangent action — 2026-09-05

Author development successor to `03e092c892ce870940802779bacf9296a1e8ec1b`.
Prior probes and failure records are preserved. This record creates no
candidate freeze, formal execution, independent qualification or production API.

## Structured directional evaluation

`DirectionalResponseProbe` seeds a requested external direction into the
analytic scalar-potential graph BEFORE condensation and dense nodal assembly.
The same retained chord/spin potential and analytic frame derivatives are
used. With external direction v and internal coordinates a, it obtains

`K v = H_qv - H_qa H_aa^-1 H_av`,

`v^T K v = H_vv - H_va H_aa^-1 H_av`.

The implementation evaluates the 18 physical external seeds, one directional
seed, and six internal seeds together. This is a structured directional
evaluation, not a precomputed factorization, finite-difference tangent or
spectral correction. Directional seeds enter the potential, rather than
being contracted with a rounded dense K afterward.

## Why energy agreement was insufficient

The first directional diagnostic restored the high-contrast reference
bending energies but still differed from an 80-digit reconstruction in
force action by about 1.40e-5 and 3.68e-5 on the two curved geometries.
Ordinary binary64 chord-direction products can cancel after their rounding
remainders have been lost. Multiplication by axial stiffness of order 1e12
then makes the lost terms visible in forces.

The successor expands `(x_R-x_L).(v_R-v_L)` into products of the original
binary64 nodal inputs. It uses FMA to retain each product's rounding remainder
and `math.fsum` to accumulate those products. The identical constant-coefficient
linear expression is evaluated for value, gradient and Hessian. No derivative
is overridden, force is not forced to zero, and no stiffness/tolerance change
is introduced. In particular, the exact-real interpretation of rounded nodal
input data can contain a small axial force even for a manufactured mode that
was intended to be inextensional; the method must reproduce it, not erase it.

This arithmetic currently uses `math.fma` on the inspected Python 3.13.9
research runtime. Windows NumPy longdouble has the same epsilon as binary64
on this machine; it would not provide extra precision. Compatibility and
performance on other production runtimes are NOT established by this probe.
Nonfinite products and condensed actions are rejected.

## Conditional high-precision verification

The test reconstructs the ORIGINAL primal reference stationary equations at
80 Decimal digits, using exact conversions of the supplied binary64 nodal
coordinates, frames, section metric integrals and direction. It solves the
three internal rotations per half and computes energy and nodal force/moment
action. It does not import a rounded assembled stiffness or the new
directional seed calculation. It shares reference metric inputs and author
provenance: this is alternative arithmetic/algebra, NOT independently authored
formulation or quadrature evidence.

For section diag(1e12,1e12,1e12,1,2,3) and the preserved constant-spatial-moment
directions, compensated results versus that reconstruction were:

| Geometry (height, shift, twist) | Absolute energy error | Force-action norm error |
|---|---:|---:|
| (0, 0, 0) | 0 | 9.60680e-16 |
| (0.4, 0, 0) | 0 | 1.95750e-15 |
| (0.6, 0.2, 0.15) | 3.33067e-16 | 2.37467e-15 |

The suite also checks all three geometries at rho=1,100,10000,1000000;
arbitrary coupled-section reference directions at rho=1 and 1000000; and a
rotated/translated high-contrast reference with its rounded transformed input
direction. Energy and force action meet the unchanged 1e-11 checks.

These checks close the specific measured reference-mode discrepancy for this
method and test set. They do not establish all-geometry conditioning or full
finite-state/assembled slenderness qualification.

## Other verification and limits

- New focused suite: 20 passed in 3.02 seconds.
- Existing seven P5 suites: 108 passed in 8.08 seconds.
- Finite-state actions agree with same-chart residual directional checks at
  1e-7, including a nonzero external chart and distributed loads.
- Moderate-state action linearity, reciprocity, zero direction, state and
  rotation binding, finite seed validation, deterministic repetition and
  rejection of a deliberately corrupted local solve are tested.
- The retained extreme coupled state remains unresolved. No test or domain
  requirement was removed or reclassified by this work.
- The old dense tangent and its recorded small-energy failures remain intact.
  Calling a dense contraction does not gain the new method's accuracy.
- The shared Jet2 kernel remains NOT an independent oracle.

Probe SHA-256:
`20145C117312127DFBFBDCE767D5C76EABEA2CCFB092174075F2E811891731A4`.

Test SHA-256:
`67979859CE7F1B3DB862F99DCD444C54ADB8AD4AE3A95185436342A4209A005E`.

## Next steps and preserved boundary

Verify small assembled reference solves with the structured action, suitable
scaling/preconditioning, and a separate high-precision check. Do not claim
that small local action errors alone prove assembled response accuracy or
locking freedom. Any heavy or performance run still requires the workspace
resource policy; this checkpoint used only small unit diagnostics.

Finite-state high-contrast accuracy, the extreme coupled equilibrium/cutback
case, independent source/derivation review, integration accuracy, engineering
convergence, nonlinear section trial/commit/restart, mass/modal/buckling,
installed-wheel exposure and objective beam-shell joints remain outstanding.

No existing production source, B2/B3/Q4/S3 mechanics, defaults, package,
dependency or workflow was changed. No resource request, formal run, merge,
release or activation was created. The complete goal remains active.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
