# Native GE-B3 linear solve integration: local resultant elimination

Start from clean `1200d6c1478c92e8737d53797830419a4ca7200c`, tree
`a868a5faa29615dd5e3db345f619b3010c36aa54`. Preserve all native nonlinear,
loaded-modal and independent continuum evidence. No historical path is rerun.

The native curved/physical-fibre element currently enters a bounded dense
retained system with 18 nodal coordinates, six physical cell rotations and
18 constitutive-resultant unknowns per macrocell. A production solver needs
a safe algebraic reduction before general sparse assembly/controller adoption.

For a supplied COMPLETE spatial residual Jacobian and homogeneous fixed
increment map, partition free geometry g and element-local resultants p:

    [ A  B ][dg] = [bg]
    [ D -C ][dp]   [bp]

Require each C positive definite and exactly symmetric, D=B-transpose, and
zero coupling of resultant blocks belonging to different elements. Then:

    (A + B C^-1 D) dg = bg + B C^-1 bp
    dp = C^-1 D dg - C^-1 bp

Use local Cholesky actions, not explicit inverses. Factor the reduced matrix
through ANYsolver's existing SciPy/SuperLU backend with GENERAL classification:
the complete spatial Jacobian need not be symmetric away from equilibrium.
Preserve all six physical cell rotations; do not statically eliminate inertia.
Reuse one factor for Newton and line-search right-hand sides. Reconstruct the
full increment and require componentwise backward error at most 1e-11 against
the complete supplied matrix. Do not regularize, symmetrize, clip or retry.

This first component is private and is not selected by existing controllers.
It does not change a mechanical operator, accepted state, history, recovery,
mass, tangent definition, public selector, legacy beam or shell default. It
does not yet remove the original dense assembly or its 256/512 coordinate
budget, and makes no general speed, locking or production-readiness claim.

Bounded tests compare recovered increments against direct full-system solves
at nonstationary straight/curved states, the preserved one/two/four-macro loaded
states, and a new trial from a preserved accepted plastic origin. Include
multiple RHS, factor reuse, deterministic serialization, fixed constraints,
mutated matrices/layouts and missing/invalid material blocks. No native load
path or eigensolve may run. A component test failure blocks controller adoption.

Use one thread, 24 GiB process-tree memory, 600-second test-process wall and
120-second activity limits. Each factorization/action also checks 60 seconds.
After a successful rehearsal, freeze the implementation and run two fresh
bounded test processes, preserving raw comparison packets and logs. Require
byte-identical scientific packets, not identical timings. No automatic retry.

Following successful parity, the next work is a separately bound controller
integration and full nonlinear transaction comparison, followed by sparse
assembly and public solver qualification. Algebraic reduction alone is not
completion of any of those gates or the full GE-B3 goal.
