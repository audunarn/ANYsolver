# M2 physical trace reference norm — development contract

This independent derivation supplies the missing reference function space and boundary convention for the R8 §4.5 BL5 numerical contract. It defines a positive **auxiliary kinematic norm**, not a mechanical stiffness. It does not establish uniform inf-sup stability, a numerical acceptance floor, physical convergence, or F03 qualification.

## Scope and physical fields

The initial scope is a straight beam beside a flat shell, with fixed reference frames and **zero native reference lift**. Section eccentricity and the physical bottom/top surface arms remain present. Let the beam axis be \(s\in[0,L]\), use a fixed physical length \(\ell>0\), and declare the surface-width average \(\langle\cdot\rangle_y\) before implementation. \(\ell\), integration normalizations, and frames are reference inputs; they must not be calibrated from candidate singular values.

The beam reference space consists of a continuous axis translation \(U\in H^1(0,L;\mathbb R^3)\), with \(U(0)=0\) for the matched translational root support, and an independent spatial rotation \(\Theta_j\in\mathbb R^3\) constant on each declared halfcell \(I_j\). The retained cell rotation is free at the root: a supported nodal rotation is not a boundary value of this field. Other supported boundaries must be mapped to these physical fields explicitly; an unsupported axis endpoint has the natural auxiliary Riesz boundary condition.

Write \(A(s,y)=\operatorname{skew}(a(s,y))\). The beam surface translation is \(U-A\Theta_j\), and its scaled rotational trace is \(\ell\Theta_j\). The arm \(a\) is measured from the axis to the physical surface in the common spatial frame. A future nonzero-lift extension must include the reference lift in this arm and in work pullback. Variable lifts also change derivative terms; they require a separately justified norm equivalence and are outside this initial contract.

The shell reference has five physical fields: midsurface translation \(v\in\mathbb R^3\) and tangential director variation \(\eta\in\mathbb R^2\), continuously enriched over the flat shell. Its surface translation includes the top-surface arm acting on the director variation. The shell normal-spin/drilling variable is absent. This five-field trace must not be replaced by the nodal six-row point law, the L1 six-channel triad law, or the B2 finite-vertex law.

For coefficient calculations use the force-equivalent density
\(\mu=(\lambda_t,\lambda_d/\ell)\) and
\(Q=\operatorname{diag}(1,1,1,\ell,\ell)\), so \(\lambda=Q\mu\).
The pairing remains \(\mu^TQ^TCq\); director gaps are scaled by the fixed
physical length, not a mesh length. Build the reference dual for this same
pairing. Reciprocal basis rescaling and equivalent units must transform both
the pairing and norm by congruence. Never compare raw mixed-unit singular values.

## Positive auxiliary Riesz operators

Define the beam squared norm

\[
 h_B(U,\Theta)=\frac1L\sum_j\int_{I_j}
 \left(\left\langle|U-A\Theta_j|^2\right\rangle_y
       +\ell^2|\Theta_j|^2+\ell^2|U'|^2\right)\,ds.
\]

This is positive on the declared space. It uses a continuous translation, not independent broken-H1 translations. With all factors of \(1/L\) retained, set

\[
 C_j=\frac1L\int_{I_j}(\langle A^TA\rangle_y+\ell^2I)\,ds,
 \qquad D_jU=\frac1L\int_{I_j}\langle A\rangle_y^T U\,ds,
\]

and \(\langle U,A_UU\rangle=L^{-1}\int(|U|^2+\ell^2|U'|^2)ds\). Thus
\(h_B=\langle U,A_UU\rangle-2\sum_j\Theta_j^TD_jU+\sum_j\Theta_j^TC_j\Theta_j\).
Each \(C_j\) is SPD. The supported Schur operator

\[
 S=A_U-\sum_jD_j^*C_j^{-1}D_j
\]

is also positive. It is a supported reaction-diffusion operator **with cellwise finite-rank integral corrections**, not an uncoupled scalar Green operator.

For the independently derived beam work functional
\(F_B(U,\Theta)=\langle f,U\rangle+\sum_jm_j^T\Theta_j\), retain the integrated cell moments \(m_j\): physical force-arm moments, reference-lift pullback where applicable, and direct director couples, with their signs and frames. The Riesz solution obeys

\[
 \Theta_j=C_j^{-1}(m_j+D_jU),\qquad
 SU=\phi,\qquad \phi=f+\sum_jD_j^*C_j^{-1}m_j,
\]

so that

\[
 \|F_B\|_{h_B^*}^2
 =\sum_jm_j^TC_j^{-1}m_j+\langle\phi,S^{-1}\phi\rangle.
\]

The local term is the dual of the **integrated moment on a cell-constant rotation**. Substituting a pointwise moment-density L2 term changes the function space. Force/director cancellation may remove a cell moment, but a surviving force functional remains in the continuous-H1 contribution. Elimination here is static elimination in a positive norm; it is not condensation, stabilization, or an SPD replacement of the actual indefinite mechanical operator.

A declared shell auxiliary norm can use the supported five-field H1 Riesz form

\[
 h_S(v,\eta)=\frac1{|\Omega|}\int_\Omega
 (|v|^2+\ell^2|\eta|^2+\ell^2|\nabla v|^2+\ell^4|\nabla\eta|^2)\,d\Omega.
\]

Impose the actual mapped translation/director support conditions; do not impose drilling conditions on this space. Assemble the physical top-surface work, including its arm, independently of candidate constraint rows. These normalizations make both primal norms have squared-displacement units; work is in N m, giving squared-force units for their duals.

## Independent multiplier reference and remaining obligations

For a BL5 multiplier field \(\lambda\), derive the two signed physical domain functionals \(F_{S,\lambda}\) and \(F_{B,\lambda}\). Define the reference dual by

\[
 \lambda^TM\lambda
 =\|F_{S,\lambda}\|_{h_S^*}^2+\|F_{B,\lambda}\|_{h_B^*}^2.
\]

Use independently enriched shell and continuous beam translation spaces with analytic 1D Riesz controls and converged auxiliary inverse-actions. Preserve the stated cell-constant rotation partition. Sparse SPD solves of the coupled auxiliary norm are acceptable; explicit dense inverses are unnecessary. The candidate native trace is subsequently restricted into this independently declared reference space. Defining \(M=B_hH_h^{-1}B_h^T\) on the same candidate fields would normalize away the candidate's loss of stability and is not this contract.

Before a beta claim, verify physical work/units/frames, positive reference norms and M on the declared multiplier quotient, inverse-action accuracy, and enrichment error. Any gauge or annihilator must be identified physically and checked through \(BZ=0\); small eigenvalues must not be discarded to improve beta. With the bulk shell norm, off-line physical shell fields remain in H; they are not trace-null gauges. Native nodal rotations and algebraic retained forces that are absent from this kinematic norm still remain in the actual mechanical KKT. Freeze independent good/bad controls, reference length/weights, numerical residual tolerances, absolute admissibility floors, and permitted deterioration before inspecting candidate trends. Controls must exercise force, director, eccentric coupling, cancellation, and supported boundaries.

Actual indefinite KKT residuals, physical kernel stability, locking, transfer/work convergence, and coherent growing P0 aggregation remain separate obligations. This derivation resolves the specified boundary/function-space obstruction; it supplies no numerical uniform-acceptance or qualification conclusion.
