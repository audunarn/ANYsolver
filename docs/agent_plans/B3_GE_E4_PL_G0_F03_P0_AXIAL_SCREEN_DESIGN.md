# F03 classical P0 axial spectral screen: bounded development fixture

22 September 2026. This unregistered, source-local fixture adds the
finite-dimensional axial Schur diagnostic for the *existing classical*
small-strain P0 line operator. It neither repeats a closed loaded case nor
chooses a native B3-GE/E4-PL mortar space. No numerical trend, uniform
inf-sup, physical response, or gate acceptance is claimed here.

For a supported classical shell/beam reference, the previous element Gram
derivation gives positive primal energy under its stated connectivity and
supports. With `B=C D/U0` and `Kbar=D K D/E0`, the bounded implementation
forms the axial part of `S=B Kbar^-1 B^T`. It checks the unmodified symmetry
and per-column primal solve residual before roundoff symmetrization. This
code calls the separate sparse smallest-algebraic supported-energy screen
and rejects negative or inconclusive outcomes. A positive Lanczos screen
still does not independently certify arbitrary assembled primal SPD. Small
tests use an independent dense solve as an oracle.

The norm-only P0 construction supplies `Hlo <= Htrue <= Hhi` analytically
in the Loewner sense. If `S` is positive and the floating-point operations
accurately represent these forms, generalized Rayleigh quotients obey

```text
lambda_min(S,Hhi) <= lambda_min(S,Htrue) <= lambda_min(S,Hlo).
```

The code reports square roots of the endpoints, solver/eigen residuals and
matrix sizes. It also returns small matrices only when explicitly requested
by a test. The binary64 enclosure is not an interval-arithmetic certificate.
The P0 Gram and Schur are dense only on the bounded multiplier interface;
no global dense primal is assembled in the diagnostic route. The reference
length is 1 m; the diagonal physical scales match the earlier classical
P1 diagnostic. Comparing numbers against P1 requires stating that their
distinct discrete multiplier norms and spaces are different objects.

The fixture is limited to `Ns<=16, Ny<=16, Nb<=128, Nm<=64`. A prospective
experiment must freeze the exact source, cases, tolerances, and terminal
policy before generating evidence. Even a favorable classical P0 beta is
not enough to override the earlier loaded gap failures, native retained-yaw
jumps, lack of exact six-channel tangent, or missing physical line work.
