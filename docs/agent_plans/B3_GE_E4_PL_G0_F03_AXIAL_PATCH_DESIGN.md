# F03 bounded classical axial Schur decomposition

22 September 2026. This is a small, unregistered G0B development fixture,
not a replay of the consumed Nm128 case or a native B3-GE/E4-PL line law.
The saved Q4 Schur forms at Nm64/Nm128 have the same coarse-space action to
`1.61e-14` relative Frobenius error, while their minimum beta declines by
46.4%. Read-only post-hoc axial diagnostics are at
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-nm128-stability-axial-diagnostic-v1/report.json`
(SHA-256 `52c7c3f10d3322274d128652b79bcb58f70b4589a9fa20dcec0e5005b6e5de70`).
The first ten weak modes are axial to numerical precision. The lowest mode's
raw nodal DCT-I has 97.96% (Nm64) and 99.81% (Nm128) coefficient energy in
the upper half frequencies; DCT coefficient energy is only a descriptive
wavelength measure. For ten R-normalized Nm128 vectors, the sum of squared
R-projections onto nested Nm64 P1 is `0.0027059`, or a **mean 0.0271% per
mode**. The individual modes can rotate within their low-eigenvalue cluster.
These results are conditional on the saved classical operator and the
unproven numerical positive-energy certificate; they do not select a
multiplier or override the failed CST-CB condition.

The new bounded helper splits the supported classical primal energy into its
independent shell and beam blocks. With fixed physical scales and full weak
coupling, write `B=[Bs,Bb]`, `Kbar=diag(Ks,Kb)` and therefore
`S=Bs Ks^-1 Bs^T + Bb Kb^-1 Bb^T = Ss + Sb`. It checks the actual primal
cross block, side solve residuals, symmetry and axial generalized eigen
residual. Side actions are evaluated on the *same* normalized minimum axial
traction; side-alone minimum eigenvalues are reported with an eigenvalue
scale and unresolved-near-zero classification. A small negative value in a
near-null side is not a physical instability or a square-rootable beta. Tests
compare the sum with the existing bounded complete assembly for Q4 and
CST-CB, and compare each side's work for a common nested P1 traction at
Nm32 and Nm64. No global dense primal matrix is formed.

A side-action fraction at different Nm uses a different minimizing vector
and norm, and therefore cannot identify causal stiffness by itself. The
next bounded patch should hold beam trace or shell host fixed while varying
the other, use ratio-matched `(Ns,Ny,Nb)=(16,8,64)` and Nm16/32, and compare
common-traction side actions, subspaces and physical work. An unregistered
exploration on this ratio-matched patch saw Q4 beta `.32977→.26002` and
CST-CB `.31996→.25828` on Nm16→32, but these values are **exploratory** and
not frozen acceptance evidence. Prior native coarse-P1 and local-dual
physical screens already had adverse loaded gaps. The native signed
retained-yaw weak mode is distinct from this classical axial mode.

Supported energy has a separate element Gram/rigid-nullspace derivation and
sparse smallest-algebraic screen. Its positive numerical result is not an
arbitrary-matrix SPD certificate. Candidate P0, P1, or local-dual policies
still require a prospective physical floor and full G0B registration.
