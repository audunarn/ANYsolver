# Coupled physical-fibre cell conjugate — development successor

Parent `7b8daa273c29fdacba7253be94a9074964314ea5`.
Independent review PENDING. No public routing or qualification authority.

## Work map and simultaneous station problem

Retain the existing two half-cells, shared three-component axial/shear
coordinate `z_c`, station maps `V_j`, and linear endpoint moment maps `N_j`.
Let `x=[z_0,z_1,kappa_0,...,kappa_(Ns-1)]` and
`e_j=[V_j z_c; kappa_j]=S_j x`.
The station measure `w_j` is the frozen reference-arclength quadrature weight.

For 18 retained forces/moments `p=[a_0,a_1,m_00,m_01,m_10,m_11]`, define L by

`p^T L^T x = sum_c a_c^T z_c + sum_j w_j (N_j m_c)^T kappa_j`.

Using the complete native physical-fibre incremental potential W, the cell
complementary potential is

`Psi*(p;origin) = sup_x [p^T L^T x - sum_j w_j W(S_j x;origin_j)]`.

Fibre increments minimize their actual station material potential at each
trial x. All stations are coupled through the shared z coordinates. This is
not a set of independently prescribed station-force return maps.

Solve the convex stationarity system
`r=sum_j w_j S_j^T s_j-Lp=0` at fixed origin. Its current tangent is
`A=sum_j w_j S_j^T Ct_j S_j`. On a smooth, strictly positive branch,

`gradient(Psi*)=L^T x`, `Hessian(Psi*)=L^T A^-1 L`.

The station curvature equations enforce `m_j=N_j m_c`; the shared force
equations enforce `sum_(j in c) w_j V_j^T n_j=a_c`. The gradient's moment
entries are the weighted curvature moments, not unweighted station values.
The Fenchel identity `Psi*+sum w_j W_j=p^T gradient(Psi*)` checks load work.

## Numerical and state contract

Evaluate the native fibre potential in Decimal at 80 digits. The new evaluator
uses the captured physical fibre law and the same declared energy integral;
tests compare its physical station response with the existing section entry.
Use the full virgin elastic cell solve only as a starting predictor. Each
Newton step uses the actual algorithmic fibre tangent and a convex-potential
decrease check. A generic backtracking prototype failed the 10^12 contrast
case and is preserved. The successor line search partitions [0,1] at every
known affine fibre-strain yield/table-knot crossing, then minimizes the actual
piecewise-quadratic energy along that direction. Never replace the material
by its tangent in an elastic energy or relax its scientific tolerance.

Limits: 48 Newton updates, at most 4096 line partitions per update, a cooperative
60-second call bound and cancellation checkpoints throughout assembly and
linear algebra. The small development compiler accepts 4–32 stations, including
at least two distinct t coordinates per half-cell to resolve endpoint moment work, and at
most 32 fibres per station. No automatic restart, retry or regularization.
The retained 18 resultants are unchanged; internal numerical strain variables
are not new nodal DOFs. A nonpositive current tangent fails closed in this
strict-conjugate entry. It does not disqualify perfect plasticity generally:
the latter may require a set-valued constrained formulation rather than an
invertible smooth complementary map.

The origin is a cell-identity-bound immutable ordered tuple of station fibre
histories. Trial evaluation cannot publish it. Return proposed history,
physical fibre stress/elastic strain, paired station fields, paired potential,
gradient and Hessian; record smooth versus semismooth selection explicitly.
Numerical Decimal/paired-binary64 output is not an exact or interval proof.

This step establishes and tests the coupled constitutive cell. Global retained
beam integration, station transaction/restart binding, nonlinear assembled
loading/reversal and independent qualification remain required.
