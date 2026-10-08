# F03 analytical trace-norm validation protocol

22 September 2026. This is a **pure auxiliary-norm study** following the
preserved endpoint-comparison v1 HOLD. No structural equilibrium, physical
state, native attachment, continuum inf-sup or G0B acceptance is part of it.
No 128-subdivision retry is permitted or needed by this protocol.

Use the full scalar H1 norm on the physical one-metre interval, with fixed
L0=1 m and free endpoints. The functional combines P1 line densities and
endpoint atoms. Its Riesz problem is `-u''+u=w`, with boundary conditions
`-u'(0)=alpha0` and `u'(1)=alpha1`.

On each cell of width h, w=a+b*x. Evaluate the exact cell solution using
positive Taylor series for `A(x)=cosh(x)-1`, `B(x)=sinh(x)-x`, their zeroth
and first moments, and the transfer

`uR=uL+h*vL+(uL-a)*A(h)+(vL-b)*B(h)`

`vR=vL+(uL-a)*sinh(h)+(vL-b)*A(h)`.

Twelve positive terms are fixed in the candidate. Report the local series
tail bound, but do not label it a certified bound on accumulated binary64
roundoff, the complete Gram, or its spectrum. Enforce the two boundary
derivatives by solving the scalar initial-value transfer. Integrate each
test density against that cell solution analytically and include both
endpoint evaluations.

An independently implemented oracle integrates
`G(s,t)=cosh(min(s,t))*cosh(1-max(s,t))/sinh(1)` using Decimal arithmetic
at exactly 70 digits. It splits every cell branch and the kernel diagonal;
disjoint-cell integrals separate, and same-cell integrals use two triangles.
Refine Gauss-Legendre roots in Decimal arithmetic. Freeze quadrature
orders **12 and 16**, rather than choosing them after comparisons.
Convert only final Gram entries to binary64 for the reported comparison.

Both constructions use the canonical enriched functional order: all P1
hats, root atom, tip atom. Normalize interior hats by h, boundary hats by
h/2, and atoms by 1. Derive the P1 and hybrid restrictions explicitly:
all hats for P1; interior hats and both atoms for hybrid. Do not average
the candidate Gram with its transpose, clip eigenvalues, add a diagonal,
or use structural stiffness to construct the norm.

## Fixed inventory and criteria

Evaluate Nm=4,8,16 with all three spaces: nine scalar Gram comparisons.
The 32/64 auxiliary FE Grams from the prior algorithm are also evaluated
for **descriptive error estimates**, with no new acceptance assigned to v1.

Require all of:

- Finite Gram entries and successful Cholesky factorization.
- Relative Frobenius skew at most `1e-12`.
- Candidate/reference relative Frobenius difference at most `1e-12`.
- Candidate/reference relative operator error at most `1e-9`.
- Decimal order-12/order-16 relative operator difference at most `1e-12`.
- Analytical endpoint and density partition identities within `1e-12`.

For reference Gram B=L L.T, define the relative operator error as
`norm(L^-1*(A-B)*L^-T,2)`. Evaluate it with triangular solves. It bounds
relative quadratic-form error and includes any candidate antisymmetry;
it does not silently select one triangle or repair the matrix. Report
condition numbers, all criteria, the FE approximation errors and the
truncation bound. Every mandatory scalar-space row must pass.

Freeze a clean source commit, Python/dependency/platform identities,
single-thread numerical pools, an exclusive evidence root and both source
algorithms before executing this registered study. The child receives
120 seconds and 512 MiB sampled RSS under an owned-process supervisor.
Write each completed Nm result and Gram archive exclusively before the
next Nm starts. Preserve failed or aborted results. Independent review
is required before execution and after the evidence is produced.

A pass validates only this auxiliary norm evaluator for the listed rows
and numerical domain. The original comparison remains
`UNRESOLVED_AUXILIARY_NORM`; any future use of its saved structural fields
requires a separately explicit source/state-bound analysis contract.
No structural solve or acceptance criterion is changed by this study.
