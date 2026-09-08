# Generalized-section retained-cell integration development

Base: 912933630ad2bb94f77741794d5c8279e8c4fd50.
This additive private gate integrates the preserved six-resultant ellipsoidal
section with the existing centered two-cell work map. No existing physical-fibre,
beam, shell, solver, selector, qualification evidence or default is modified.

For retained p=(f_0,f_1,m_0L,m_0R,m_1L,m_1R), station moments are
m_j=(1-t_j)m_cL+t_j m_cR. Independent station forces n_j minimize
sum_j w_j W*(n_j,m_j;origin_j) subject to
sum_{j in c} w_j V_j^T n_j=f_c, V_j=R0_j^T/J_j.

Using Lagrangian F(n,m)-lambda.(Bn-f), stationarity requires
W*_{,n,j}=V_j lambda_c. Thus lambda supplies the shared cell generalized
translation strain. The conjugate gradient is lambda and the integrated
endpoint-weighted station curvatures. Differentiate the complete constrained
system to obtain its 18x18 compliance; no independent-station approximation.

The constrained Hessian equations are
[ F_nn, -B^T; B, 0 ] [dn;dlambda]
 = [ -F_nm dm; df ].
The lower gradient derivative is F_mn dn+F_mm dm. The reduced Hessian
must be positive definite. Origin is fixed for every local Newton/line-search
evaluation. H>0 remains explicit; no regularization or hidden material change.

Use bounded 80-digit Decimal algebra, 48 Newton updates, 32 line-search cuts,
60-second cell deadline, and 1e-28 scaled internal residual control. These are
numerical controls, not exact certificates. Preserve paired outputs and history.
The finite retained potential remains p.k(q)-Psi*(p;origin), with the frozen
analytic centered geometry and 42-coordinate first/second variations ported
unchanged into a separate generalized operator.

Independent audit reconstructs the opposite primal strain elimination from
the separately authored seven-equation section KKT return map. Check forces,
moments, shared strain, curvature, material history, work and full compliance.
Also check mutations, directional derivatives, straight/curved rigid objectivity,
native resultant recovery, station order coverage and deterministic serialization.
Add proper spatial re-expression of the cell and reference-state static
condensation for straight and curved fixtures: six analytical rigid columns
and a positive 12-dimensional complement. These are numerical reference checks,
not a complete exact-rank, finite-state, spectral or dynamic qualification.

Run bounded smoke then full rehearsal; freeze these five paths and run two
fresh-directory cycles. One thread, 24 GiB, 600-second child wall and 120-second
CPU inactivity, at most three children and 1,800 seconds per wave. No retries.
Preserve any failure before correction. Independent review remains PENDING.
No public API, full native solver-state integration, dynamics or qualification
authority is conferred. Continue with static condensation/global native history
integration, remaining solver/material parity, mass/spectra/engineering,
packaging and objective beam-shell joints.
