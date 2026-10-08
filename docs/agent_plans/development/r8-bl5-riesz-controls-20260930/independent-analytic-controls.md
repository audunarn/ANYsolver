# Independent auxiliary-Riesz analytic controls

Development oracle for the flat, straight, zero-reference-lift contract in docs/agent_plans/B3_GE_E4_PL_M2_TRACE_NORM_CONTRACT_DEV.md. These controls validate reference inverse-actions and physical pairing; they do not supply candidate beta floors, uniform stability, mechanical condensation, or qualification. No numerical execution is included.

## Normalization, units and boundaries

Keep the contract's beam factor \(1/L\), shell factor \(1/|\Omega|\), and fixed physical \(\ell>0\). Physical test translations have units m and rotations are dimensionless. A force functional has units N m. Consequently the **Riesz representer** translations below have units N, representer rotations N/m, and squared dual norms N²; representers are not physical displacement solutions.

The beam has \(U(0)=0\), \(U'(L)=0\), continuous U, and independently free constant \(\Theta_j\) on each \(I_j=[s_j,s_{j+1}]\), length \(h_j>0\). There is no root rotation condition on the retained cell field. A vector force density f has units N/m; an integrated cell moment \(m_j\) has units N m. Split quadrature at every halfcell boundary, including unequal/end cells. The partition remains fixed while enriching continuous U.

## 1. Zero-arm continuous translation controls

Set \(A=0\), all \(m_j=0\), and act in one Cartesian translation channel. Then \(\Theta_j=0\) and
\[
 -\ell^2 U''+U=L f,\qquad U(0)=0,\quad U'(L)=0.
\]
Let \(r=L/\ell\), and let p be a constant force-density amplitude (N/m).

**Constant density \(f(s)=p\):**
\[
 U(s)=Lp\left[1-\frac{\cosh((L-s)/\ell)}{\cosh r}\right],
 \qquad
 E=\|F\|_*^2=L^2p^2\left[1-\frac{\ell}{L}\tanh r\right].
\]

**Ramped density \(f(s)=ps/L\):**
\[
 U(s)=p\left[s-\ell\frac{\sinh(s/\ell)}{\cosh r}\right],
 \qquad
 E=L^2p^2\left[\frac13-\frac{\ell^2}{L^2}
                     +\frac{\ell^3}{L^3}\tanh r\right].
\]
In each case \(E=\int_0^L fU\,ds=h_B(U,0)\). Repeat in all three independent translation channels, including negative amplitudes. Use scaled hyperbolic formulas when r is large and series/high precision when cancellation makes the displayed norm formula poorly resolved; avoid treating analytic evaluation error as discretization error.

## 2. Zero-arm cell-moment control

Set f=0, A=0, and prescribe any integrated vectors \(m_j\), with different signs and unequal cell lengths:
\[
 U=0,\qquad \Theta_j=\frac{L}{\ell^2h_j}m_j,\qquad
 E=\sum_j\frac{L}{\ell^2h_j}|m_j|^2.
\]
For a constant moment density \(\tau_j\) (units N), \(m_j=h_j\tau_j\), so \(E=\sum_j Lh_j|\tau_j|^2/\ell^2\). This distinguishes an integrated moment from a density and detects a missing h or \(1/L\). It must be exact up to quadrature/linear-solve roundoff on the declared constant-cell rotation space, including the first cell.

## 3. Nonzero constant-arm manufactured coupled field

Choose a fixed nonzero spatial arm a (m), \(A=\operatorname{skew}(a)\), \(B=A^TA+\ell^2I\). A single-arm surface average is sufficient for this coupling control; it is not a replacement for a later finite-width average. Choose a vector \(u_0\) (N), and cellwise vectors \(t_j\) (N/m), with \(A t_j\ne0\) and \(A^Tu_0\ne0\). Alternating t signs and unequal cell lengths exercise local elimination.

Put \(g(s)=2s/L-(s/L)^2\), \(U_*(s)=u_0g(s)\), \(\Theta_{*,j}=t_j\), and
\[
 \bar g_j=\frac{L}{h_j}
 \left[\xi^2-\frac{\xi^3}{3}\right]_{\xi=s_j/L}^{s_{j+1}/L}.
\]
The independently manufactured physical actions are
\[
 f_j(s)=\frac1L\left[u_0\left(g(s)+\frac{2\ell^2}{L^2}\right)-A t_j\right],
 \qquad
 m_j=\frac{h_j}{L}\left[B t_j-A^Tu_0\bar g_j\right].
\]
These follow directly from integration by parts of the norm. U* is supported, its derivative vanishes at L and is continuous across all cells, so no endpoint/interface point forces are omitted; f may jump with t. The actions are inputs, not actions reconstructed with the assembled candidate matrix.

The exact dual norm is
\[
 E=\left(\frac8{15}+\frac{4\ell^2}{3L^2}\right)|u_0|^2
   -2\sum_j\frac{h_j}{L}\bar g_j\,u_0^TA t_j
   +\sum_j\frac{h_j}{L}t_j^TBt_j.
\]
It also equals \(\int f\cdot U_*\,ds+\sum_jm_j\cdot t_j\). Compare the full coupled solve and the independently implemented C/D/S inverse-action to these same fields and E. A P2 continuous translation space containing this quadratic, together with constant cell rotations and sufficient exact quadrature, reproduces it to solve roundoff. For a concrete sign check take \(a=a_0e_z,\ u_0=F_0e_x,\ t_j=T_je_y\): \(A t_j=-a_0T_je_x\), and \(m_{j,y}=(h_j/L)[(a_0^2+\ell^2)T_j+a_0F_0\bar g_j]\). Reversing a while keeping u0/t fixed changes both cross-action signs.

## 4. Supported five-field shell volume-action control

Take \(\Omega=(0,L)\times(-W/2,W/2)\), area \(A_\Omega=LW\), clamp all five physical fields at x=0, and use natural normal-gradient conditions on x=L and both y edges. Let p be a constant 3-vector volume-force density (N/m²), and q a constant 2-vector volume-director-couple density (N/m). Use the generalized functional
\[
 F_S(v,\eta)=\int_\Omega(p\cdot v+q\cdot\eta)\,d\Omega.
\]
With \(b(x)=1-\cosh((L-x)/\ell)/\cosh r\),
\[
 v_*=A_\Omega p\,b(x),\qquad
 \eta_*=\frac{A_\Omega}{\ell^2}q\,b(x),
 \qquad
 E_S=A_\Omega^2\left(|p|^2+\frac{|q|^2}{\ell^2}\right)
             \left[1-\frac{\ell}{L}\tanh r\right].
\]
All fields are y-uniform. A ramp \(p(x)=p_0x/L,\ q(x)=q_0x/L\) uses
\(b_r(x)=x/L-(\ell/L)\sinh(x/\ell)/\cosh r\) and replaces the last bracket by
\(1/3-\ell^2/L^2+\ell^3\tanh r/L^3\). Exercise each of the three translation and two director channels independently. If actions are instead declared on the physical top surface, first include its force-arm contribution in q with the declared spatial sign/frame.

This is a **volume functional**, not a line action at y=0. A line force \(\int_0^L t(x)\cdot v(x,0)\,dx\) has a delta-in-y source and generally a y-dependent Riesz representer. Replacing it by volume density t/W agrees only after restricting tests to y-uniform fields; it is not an oracle for the enriched shell line dual. A separate line-source Green/modal or converged independent reference control remains necessary before claiming that part of M is verified.

## Independent error checks and limits

- Compare fields, E from closed formulas, direct physical work, and norm energy. Use exact cell moments and adequate quadrature; assess quadrature and sparse-solve residuals separately from enrichment.
- For nested conforming Galerkin spaces with the same cell partition, boundary space and exact assembly, \(E_h=F(w_h)=h(w_h,w_h)\), \(E-E_h=\|w-w_h\|_h^2\ge0\). E_h is monotone increasing. Smooth zero-arm/P1 controls have H1 error \(O(h)\) and norm-value error \(O(h^2)\); exact P2 manufactured and pure-cell-moment controls have only numerical error. Changing the rotation partition changes the reference space and does not have this same-space monotonicity guarantee.
- Freeze a reference accuracy budget and normalized residual limits from these analytic controls and floating-point conditioning before candidate spectra. For shell-plus-beam independent actions, the exact squared dual is \(E_S+E_B\), with no cross-domain term. Keep both physical-domain signs even though quadratic norms are sign-even.
- Verify equivalent-unit and reciprocal multiplier-basis congruence using the contract's fixed \(\mu=(\lambda_t,\lambda_d/\ell)\), \(\lambda=Q\mu\). Preserve arms and force/moment units. These are controls of a positive auxiliary norm, not acceptance tests of the actual indefinite mechanical KKT.

No F03 authority is consumed or renewed by this oracle note. Candidate thresholds, supported physical line-functional verification, gauge/annihilator checks, and mechanical/transfer convergence remain open.
