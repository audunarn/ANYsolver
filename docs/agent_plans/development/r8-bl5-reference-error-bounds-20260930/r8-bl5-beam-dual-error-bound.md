# Beam auxiliary dual error: equilibrated-flux bound

**Disposition: the proposed sign and bound are correct**, provided the cell-rotation algebraic equations and the physical load integrals are exact, and E_h denotes the Galerkin energy. For an inexact numerical solution, use the lower functional below and retain any algebraic rotation residual. This certificate concerns the positive auxiliary reference inverse-action, not physical mechanics, candidate stability or qualification.

## Residual identity, including finite-width averaging

Let k=ell²/L, Abar=<A>_y, and J=<A^T A>_y. On the fixed cell partition,
\[
 h_B((U,\Theta),(V,\Psi))=
 \frac1L\int\{U\cdot V-U\cdot\bar A\Psi
       -\Theta\cdot\bar A^TV+\Theta\cdot(J+\ell^2I)\Psi
       +\ell^2U'\cdot V'\}\,ds .
\]
U and V are continuous H1 with zero root translation; Theta and Psi are constant per cell and free at the root. The right-hand side is
\[
 F(V,\Psi)=\int f\cdot V\,ds+\sum_jm_j\cdot\Psi_j .
\]
f is the declared piecewise-P0 physical force density; m_j is the exact integrated physical cell moment, without division by cell length.

For any continuous P1 U_h and cell-constant Theta_h define
\[
 C_j=\frac{h_j}{L}(J+\ell^2I),\qquad
 D_jU_h=\frac1L\int_{I_j}\bar A^TU_h\,ds,\qquad
 \delta_j=m_j-C_j\Theta_{h,j}+D_jU_h .
\]
Constant averaged arms are assumed here. The exact cell equation is delta_j=0. In particular use J, **not** Abar^T Abar: the finite-width covariance J-Abar^T Abar is positive semidefinite and belongs in C_j. It contributes no extra translation residual.

Set
\[
 r(s)=\frac{U_h(s)-\bar A\Theta_h(s)}L-f(s),\qquad
 \sigma(s)=-\int_s^Lr(t)\,dt .
\]
Then sigma'=r, sigma(L)=0, and sigma is continuous through all cell/load/primal interfaces. No root flux condition is imposed because V(0)=0. Integration by parts gives, with R=F-h_B(w_h,\cdot),
\[
 R(V,\Psi)=\int[\sigma-kU_h']\cdot V'\,ds
                  +\sum_j\delta_j\cdot\Psi_j .
\]
Thus the proposed sign is sigma MINUS k U_h'. Native/P1 derivative jumps are already represented by this identity: do not add separate jump terms. Continuity of sigma cancels interface terms, and sigma(L)=0 cancels the natural endpoint term. Point forces would require corresponding flux jumps and are outside the stated piecewise-volume-load scope.

## Guaranteed energy bracket

Let w_* solve the exact auxiliary Riesz problem. Positivity gives
\[
 h_B(V,\Psi)\ge k\|V'\|^2+
                       \sum_j\frac{\ell^2h_j}{L}|\Psi_j|^2.
\]
Consequently
\[
 \|w_*-w_h\|_{h_B}^2=\|R\|_{h_B^*}^2
 \le B=
 \frac L{\ell^2}\int|\sigma-kU_h'|^2\,ds
 +\sum_j\frac L{\ell^2h_j}|\delta_j|^2 .
\]
For exact cell equations the second term vanishes, giving precisely the proposed bound. Arm covariance only increases the nonnegative norm contributions; it cannot invalidate this derivative-based estimate.

Define directly from physical loads and the norm
\[
 E_-=2F(w_h)-h_B(w_h,w_h),\qquad E_*=\|F\|_{h_B^*}^2 .
\]
The exact identity E_*-E_-=||w_*-w_h||² implies
\[
 E_-\le E_*\le E_-+B .
\]
For an exact supported Galerkin solve, F(w_h)=h_B(w_h,w_h), so E_-=E_h and E_*-E_h is the Galerkin energy error. For a finite-precision solve, the 2F-h formula and the measured delta terms avoid assuming these identities hold numerically. When E_->0, B/(E_-+B) bounds the relative exact-energy gap. A small linear-solve residual by itself does not replace this reference-discretization certificate.

## Computable polynomial integral; no new mesh

Split integration at the union of existing P1 nodes, fixed Theta-cell endpoints and P0-force boundaries. On each subinterval [a,a+d], write
\[
 U_h(a+t)=u_0+u_1t,\quad
 r(t)=r_0+r_1t,\quad
 r_0=(u_0-\bar A\Theta_j)/L-f_0,\quad r_1=u_1/L .
\]
Starting from the right endpoint sigma(L)=0, integrate backward:
\[
 \sigma(a)=\sigma(a+d)-r_0d-\tfrac12r_1d^2 .
\]
The discrepancy is the vector quadratic
\[
 q(t)=a_0+b_0t+c_0t^2,\quad
 a_0=\sigma(a)-ku_1,\quad b_0=r_0,\quad c_0=r_1/2 .
\]
Its exact squared integral is
\[
 \int_0^d|q|^2dt=
 d|a_0|^2+d^2a_0\cdot b_0
 +\frac{d^3}{3}(|b_0|^2+2a_0\cdot c_0)
 +\frac{d^4}{2}b_0\cdot c_0+\frac{d^5}{5}|c_0|^2 .
\]
Equivalently, three-point Gauss integrates this quartic exactly with positive weights and avoids cancellation between expanded terms. Compute D_j U_h by exact P1 integration and m_j from the actual physical density/arm/couple formula, splitting at support boundaries. The flux uses the original f, not its projection onto P1 nodes.

Riesz U_h has units N, Theta_h N/m, f N/m, m_j N m, sigma and q N. Both B and E have units N². ell must be positive, h_j positive, and L positive. Floating-point accumulation, load integration, C/D assembly and evaluation error must be bounded or explicitly reported before calling the numerical interval rigorous; the mathematical estimator does not magically certify rounded arithmetic.

The certificate applies to each supplied action without another refinement. For an all-combination reference-Gram bound, exploit linearity to assemble the corresponding error quadratic (including flux and delta terms); selected-action certificates alone do not establish a Loewner bound for every multiplier. No mechanical/KKT, uniform-beta or F03 claim follows.
