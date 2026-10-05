# Prospective BL5 reference stability criterion: control argument

This is an independent approximation argument before native beta inspection. It uses the declared positive beam/shell reference norms, physical density/work map, and P0 aggregation. It supplies an exact negative scalar control and a sufficient aligned one-dimensional Fortin construction. It does not prove full BL5 stability or set empirical beta/slope tolerances. No execution authority is consumed.

## Spaces and the one-interval obstruction

Take a uniform primal partition of [0,L] into N intervals of length h=L/N. Let V be continuous H1 translations with u(0)=0 and let V_h be continuous P1 with the same root condition. The natural endpoint is a Riesz-operator condition, not an essential u'(L)=0 condition on this trial space. Use
\[
 \|u\|_V^2=L^{-1}\int_0^L(u^2+\ell^2u'^2)\,ds,
\]
with fixed physical ell. P0 densities pair by the integrals of u on their supports.

For one density support per primal interval, a constant-amplitude alternating density has zero interior nodal loads: each is h(lambda_{i-1}+lambda_i)/2. Only the free endpoint remains visible. This algebra alone is not a full product-domain instability proof.

There is, however, an exact independent obstruction to a uniform mean-preserving beam Fortin map. Choose a continuous u which is zero at every primal node and is a triangular bubble of height (-1)^j in interval j. Its cell mean is (-1)^j/2. Any P1 function v with these means and v_0=0 is uniquely determined by v_j+v_{j+1}=(-1)^j, hence
\[
 v_j=(-1)^{j-1}j,\quad
 \|u\|_V^2=\frac13+\frac{4\ell^2}{h^2},\quad
 \|v\|_V^2=\frac{N^2+2}{9}
             +\frac{\ell^2(4N^2-1)}{3h^2}.
\]
The projection norm therefore grows at least like N/sqrt(3). If M is the exact continuous scalar dual norm on these N densities, the relative scalar inf-sup constant satisfies
\[
 \beta_{\rm scalar}\le
 \sqrt{\frac{1/3+4\ell^2/h^2}
 {(N^2+2)/9+\ell^2(4N^2-1)/(3h^2)}}\sim\frac{\sqrt3}{N}.
\]
Indeed, the unique mean-preserving projection identifies the continuous dual as the adjoint extension of the discrete dual, so beta=1/||projection||. This provides a prescribed bad-control mechanism without fitting any candidate spectrum. The triangle is an H1 test field, not a mechanical deformation oracle. The full shell-plus-beam coupling can still be rescued by the other domain.

## At least two aligned intervals: explicit Fortin map

Let every P0 support I_j be a union of m_j>=2 consecutive primal intervals, length H_j=m_j h. For each support choose a P1 tent b_j zero at its endpoints, with height one at a middle interior primal node. For a uniform mesh its peak lies between H_j/3 and 2H_j/3, and
\[
 \int_{I_j}b_j=H_j/2,\quad
 \|b_j\|_{L^2}^2=H_j/3,\quad
 \|b'_j\|_{L^2}^2\le(9/2)/H_j.
\]
Let I_h u be the ordinary 1D nodal interpolant. Define
\[
 \Pi u=I_hu+\sum_j\alpha_j b_j,\qquad
 \alpha_j=\frac{2}{H_j}\int_{I_j}(u-I_hu)\,ds.
\]
Then Pi preserves every support mean, preserves the root condition, and is the identity on V_h. Disjoint support interiors prevent correction overlap. From interval Poincare and the derivative-average identity,
\[
 \|(I_hu)'\|\le\|u'\|,\quad
 \|u-I_hu\|_{I_j}\le(h/\pi)\|u'\|_{I_j},\quad
 |\alpha_j|\le\frac{2h}{\pi\sqrt{H_j}}\|u'\|_{I_j}.
\]
Consequently, with gamma=max_j h/H_j<=1/2,
\[
 \|(\Pi u)'\|\le(1+k_d)\|u'\|,
 \quad k_d=\frac{2\sqrt{9/2}}{\pi}\gamma,
\]
\[
 \|\Pi u\|\le\|u\|+k_0h\|u'\|,
 \quad k_0=\frac{1+2/\sqrt3}{\pi}.
\]
A valid explicit V-norm bound is
\[
 C_U=\left\|\begin{pmatrix}
 1&k_0h/\ell\\0&1+k_d
 \end{pmatrix}\right\|_2.
\]
Replacing h by the predeclared maximum initial h gives a refinement-uniform conservative bound. These are H1 stability and an L2 estimate on H1 inputs; point interpolation is not claimed bounded on unrestricted L2. Nonuniform intervals require a declared shape-regularity/peak-distance bound and corresponding constants. A terminal support with only one primal interval does not satisfy this construction.

For comparison, a direct tent test gives an H1/L2 density bound
\[
 \sup_{v_h}\frac{\int\lambda v_h}{\|v_h\|_V}
 \ge \frac{\sqrt L}{2\sqrt{1/3+(9/2)\ell^2/H_{\min}^2}}
       \|\lambda\|_{L^2}.
\]
This floor decreases with H_min. It does not justify a mesh-independent absolute floor in an H1/L2 normalization. The Fortin bound instead gives beta>=1/C_U relative to the **independent exact continuous dual M**, for this scalar problem.

## Extension to the declared beam norm and aggregation policy

For flat constant frames/arms, P0 force-density work depends on translation support means. Retained cell rotations have the same cell-constant space in reference and candidate; use the identity on Theta. Their integrated moments, including direct couples and force-arm contributions, remain exactly paired. Thus the translation Fortin map preserves all beam physical multiplier work when its support hypothesis holds.

Let rho=max_surface |a|/ell, including the declared finite-width arms, and K=max(2,1+2rho²). The physical beam norm and the uncoupled translation-H1 plus rotation-L2 norm satisfy
\[
 K^{-1}h_0\le h_B\le K h_0.
\]
This follows from both U=(U-A Theta)+A Theta and the reverse decomposition; the gradient term is unchanged. Therefore C_B<=K max(C_U,1) is a sufficient, conservative beam Fortin constant. It is fixed by geometry/norm parameters, not observed beta. Positive Theta_z stays in the norm even when the centerline BL5 law annihilates it.

For span=max(1,ceil(c_lambda N_B/N_S)), h_B=L/N_B and h_S=L/N_S, the support length H=span h_B is at least c_lambda h_S. Apply the interval-count test separately on both physical primal traces at each of the declared seven ratios:

- On the beam, the count is span. The sufficient beam hypothesis requires span>=2.
- On the shell line, H/h_S>=2 for c2, but length alone does not establish alignment or a bulk-shell Fortin bound. c1 can leave exactly one shell interval. Verify endpoints are shell primal nodes, actual intervals contained, complete coverage and the final support; do not infer these from the ceil formula.
- For beam-coarse ratios, even c2 can have span=1 while covering at least two shell intervals. The beam-alone sufficient argument then fails; the shell may supply the missing control. A policy must cover all ratios through proven domain control, not declare c2 stable from its label.

Native span divisibility/coverage requirements and the real support inventory remain in force. Means refer to physical line length; multiplier coefficient scaling Q and basis rescaling preserve the conclusion only by consistent congruence.

## Exact missing full-product inequality and justified criterion

Let H=H_B+H_S and let M=M_B+M_S be the independent physical dual sum. A full Fortin proof requires maps into the actual supported native physical fields satisfying, for every multiplier,
\[
 F_{D,\lambda}(\Pi_Dw)=F_{D,\lambda}(w),\qquad
 \|\Pi_Dw\|_{H_D}\le C_D\|w\|_{H_D},\quad D=B,S.
\]
Then the dimensionless product beta is at least 1/max(C_B,C_S), on the verified physical multiplier quotient. This is the lower floor the argument would justify; it concerns the positive reference norm, not the actual indefinite mechanical KKT.

The missing shell assertion is a bounded five-field map from the supported **bulk H1 shell** into native Q4 fields, preserving the physical P0 **line** work including top-arm/director moments. A one-dimensional nodal proof is insufficient: bulk H1 has an H1/2 line trace and no bounded point-evaluation interpolation. Interior trace tents need a stable bulk lifting/local correction estimate in this norm and exact root/support handling.

Alternatively, beam control alone would suffice if independently proven
\[
 M_S\preceq\kappa M_B
\]
uniformly for the declared densities, ratios, width and supports. It would give beta>=1/[C_B sqrt(1+kappa)]. No such comparison is supplied here, especially in ratios where span=1. A shell-only control would need the reciprocal comparison. Sampled load energies cannot establish either Loewner inequality for all multiplier combinations.

In fact, beam dominance cannot be assumed uniformly for the declared bulk-shell norm. Consider a centerline normal-force channel, with no direct couple and no force-arm moment, on the supported flat rectangle. For the independent sine density sin(kx), k=(m+1/2)pi/L, put alpha=sqrt(1+ell²k²)/ell. The Neumann-y line-source Green value is coth(alpha W/2)/(2ell² alpha), and the exact shell/beam squared-dual ratio is
\[
 \frac{M_S}{M_B}=\frac{W\alpha}{2}\coth(W\alpha/2).
\]
It grows like W|k|/2: the shell line dual has H^{-1/2} frequency scaling while the continuous beam force dual has H^{-1} scaling. This normal-force subcase also decouples from Theta for a symmetric finite-width beam norm with its centerline arm parallel to n. Increasingly resolved P0 representations inherit the comparison obstruction. Thus a fixed beam-only floor cannot establish the full-product floor through a mesh-uniform kappa; the supported shell line Fortin/lifting inequality is consequential, not optional bookkeeping.

The strongest currently justified prospective criteria are: reproduce the exact one-interval bad control; verify the explicit aligned two-interval Fortin identities/constants on independent controls; verify width/arm/work/quotient conventions; and require the missing shell Fortin or uniform dual-comparison inequality before assigning a full BL5 absolute floor. Enriched reference M also needs a certified accuracy bound for all combinations (not only selected action increments), or its discretization can overstate beta. No arbitrary p-slope or acceptance tolerance follows from this argument.
