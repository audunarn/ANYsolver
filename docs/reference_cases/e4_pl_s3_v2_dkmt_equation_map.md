# E4-PL S3 V2 flat DKMT equation map and repository derivation

## Authority and scope

This record maps the flat plate equations used by the Stage-1 S3 V2 candidate to
Andi Makarim Katili, Imam Jauhari Maknun, and Irwan Katili, *Theoretical
equivalence and numerical performance of T3-gamma-s and MITC3 plate finite
elements*, Structural Engineering and Mechanics 69(5), 527-536 (2019), DOI
`10.12989/sem.2019.69.5.527`. The public publisher file is bound in
`e4_pl_s3_v2_dkmt_source_ledger.json`.

The printed source is authority only for a flat, small-strain,
Reissner-Mindlin/DKMT plate with homogeneous isotropic elastic bending and
transverse shear rigidities. The source does not establish a curved shell,
finite-rotation or material-nonlinear tangent, consistent mass, arbitrary
anisotropic or membrane-bending-coupled generalized section, shell recovery,
drilling completion, or production activation. The shell embedding and PL
completion below are repository derivations (`D` authority), not claims about
the printed paper.

## Frozen conventions

Use a positively oriented flat element chart `(x,y,z)` and barycentric
coordinates

\[
  \lambda=1-\xi-\eta,\qquad N_1=\lambda,\quad N_2=\xi,\quad N_3=\eta.
\]

For the directed edges `(i,j,k)=(1,2,4),(2,3,5),(3,1,6)`, define

\[
 x_{ji}=x_j-x_i,\quad y_{ji}=y_j-y_i,\quad
 L_{ij}=\sqrt{x_{ji}^2+y_{ji}^2},\quad
 C_{ij}=x_{ji}/L_{ij},\quad S_{ij}=y_{ji}/L_{ij}.
\]

Thus `(C_k,S_k,L_k)` is `(C_12,S_12,L_12)`,
`(C_23,S_23,L_23)`, or `(C_31,S_31,L_31)` for `k=4,5,6`.
The edge tangent is `t_k=(C_k,S_k)` and the left in-plane normal is
`n_k=(-S_k,C_k)`. The projected rotations are

\[
 \beta_s=C_k\beta_x+S_k\beta_y,\qquad
 \beta_n=-S_k\beta_x+C_k\beta_y,
\]

and the engineering transverse shear convention is
`gamma_s=w_,s+beta_s`. Reversing an edge reverses both `t_k` and the scalar
components measured along it; this leaves the physical vector and assembled
work invariant. This orientation convention is part of the formulation.

The printed plate vector is ordered

\[
 u_n=(w_1,\beta_{x1},\beta_{y1},w_2,\beta_{x2},\beta_{y2},
      w_3,\beta_{x3},\beta_{y3})^T.
\]

## Printed equation map: Eqs. 12-16 and 20-41

### Side shear projection, Eqs. 12-16 (printed page 529, PDF page 3)

At each corner, the two adjacent directed side shear components are the
projections of the Cartesian shear vector. Solving the corresponding 2 by 2
systems gives

\[
 \gamma=(\gamma_x,\gamma_y)^T=B_{s\gamma}\gamma_{sn},\qquad
 \gamma_{sn}=(\gamma_{s12},\gamma_{s23},\gamma_{s31})^T.
\]

With

\[
 A_1=C_{12}S_{31}-C_{31}S_{12},\quad
 A_2=C_{23}S_{12}-C_{12}S_{23},\quad
 A_3=C_{31}S_{23}-C_{23}S_{31},
\]

the printed interpolation is

\[
B_{s\gamma}=\begin{bmatrix}
 S_{31}N_1/A_1-S_{23}N_2/A_2 &
 S_{12}N_2/A_2-S_{31}N_3/A_3 &
 S_{23}N_3/A_3-S_{12}N_1/A_1\\
 -(C_{31}N_1/A_1-C_{23}N_2/A_2) &
 -(C_{12}N_2/A_2-C_{31}N_3/A_3) &
 -(C_{23}N_3/A_3-C_{12}N_1/A_1)
\end{bmatrix}.
\]

The `A_i` must be nonzero. A degenerate or collinear triangle is outside the
supported domain.

### Linear side kinematics, Eqs. 20-23 (printed page 529, PDF page 3)

The mean engineering shear on directed side `i-j` is

\[
 \gamma_{sij}=\frac{w_j-w_i}{L_{ij}}+
 \frac12(C_{ij}\beta_{xi}+S_{ij}\beta_{yi}+
          C_{ij}\beta_{xj}+S_{ij}\beta_{yj}).
\]

For edge order `(12,23,31)`, write `gamma_sn=A_u u_n`, where

\[
A_u=\frac12\begin{bmatrix}
-2/L_{12}&C_{12}&S_{12}& 2/L_{12}&C_{12}&S_{12}&0&0&0\\
0&0&0&-2/L_{23}&C_{23}&S_{23}&2/L_{23}&C_{23}&S_{23}\\
2/L_{31}&C_{31}&S_{31}&0&0&0&-2/L_{31}&C_{31}&S_{31}
\end{bmatrix}.
\]

Equations 21-23 then give the unenhanced assumed field
`gamma=B_sgamma A_u u_n`.

### Incomplete quadratic rotations, Eqs. 24-31 (printed page 530, PDF page 4)

Normal rotation is linear on an edge. Tangential rotation is enriched by its
one hierarchical midside coordinate `Delta beta_s,k`:

\[
 \beta_s(s)=(1-s/L_k)\beta_{si}+(s/L_k)\beta_{sj}
 +4(s/L_k)(1-s/L_k)\Delta\beta_{s,k}.
\]

The three incomplete quadratic functions are

\[
 P_4=4\lambda\xi,\qquad P_5=4\xi\eta,\qquad P_6=4\lambda\eta.
\]

The two rotation fields are

\[
 \beta_x=\sum_{i=1}^3N_i\beta_{xi}+
         \sum_{k=4}^6P_k C_k\Delta\beta_{s,k},\qquad
 \beta_y=\sum_{i=1}^3N_i\beta_{yi}+
         \sum_{k=4}^6P_k S_k\Delta\beta_{s,k}.
\]

Using the engineering curvature convention

\[
 \chi=(\beta_{x,x},\beta_{y,y},\beta_{x,y}+\beta_{y,x})^T,
\]

write

\[
 \chi=B_{b\beta}u_n+B_{b\Delta\beta}\Delta\beta_{sn},
 \quad
 (B_{b\Delta\beta})_k=
 \begin{bmatrix}
 P_{k,x}C_k\\P_{k,y}S_k\\P_{k,y}C_k+P_{k,x}S_k
 \end{bmatrix}.
\]

Only the bending rows of `u_n` participate; the `w` entries in
`B_bbeta` are zero.

### DKMT shear factor and elimination, Eqs. 32-38 (printed pages 530-531,
PDF pages 4-5)

For a homogeneous isotropic plate of thickness `h`, Poisson ratio `nu`, and
shear correction `kappa`, the printed factor and side shear are

\[
 \phi_k=\frac{2h^2}{\kappa(1-\nu)L_k^2},\qquad
 \gamma_{s,k}=-\frac23\phi_k\Delta\beta_{s,k}.
\]

Combining this relation with the side kinematics gives

\[
 -\frac23(1+\phi_k)\Delta\beta_{s,k}=(A_u u_n)_k.
\]

Therefore

\[
 \Delta\beta_{sn}=A_\Delta^{-1}A_u u_n,
\]

where

\[
 A_\phi=-\frac23\operatorname{diag}(\phi_4,\phi_5,\phi_6),\qquad
 A_\Delta=-\frac23\operatorname{diag}(1+\phi_4,1+\phi_5,1+\phi_6).
\]

For positive thickness, rigidity, shear correction, and edge lengths,
`A_delta` is nonsingular. Its inverse must be applied as the displayed solve;
an affine beta field, a lowest-order Nedelec shear substitute, or an MITC3
tying interpolation is not the same formulation.

### Enhanced curvature and shear, Eqs. 39-41 (printed page 531, PDF page 5)

After eliminating the hierarchical coordinates,

\[
 B_b=B_{b\beta}+B_{b\Delta\beta}A_\Delta^{-1}A_u,
 \qquad
 B_s=B_{s\gamma}A_\phi A_\Delta^{-1}A_u,
\]

with the positive diagonal ratio

\[
 A_\phi A_\Delta^{-1}=
 \operatorname{diag}\left(
 \frac{\phi_4}{1+\phi_4},
 \frac{\phi_5}{1+\phi_5},
 \frac{\phi_6}{1+\phi_6}\right).
\]

These are the implementation-defining DKMT operators for the supported flat
isotropic bending/shear subset.

The two kinematic limits follow without changing coefficients. As
`h/L_k -> 0`, `phi_k -> 0`, the shear ratio `phi_k/(1+phi_k) -> 0`, and the
remaining `Delta beta_s` curvature enhancement is the discrete-Kirchhoff thin
limit. As `h/L_k -> infinity`, `Delta beta_s -> 0`, the curvature becomes the
linear nodal-rotation field, and `phi_k/(1+phi_k) -> 1`, so the shear becomes
`B_sgamma A_u u_n`, the thick T3-gamma-s/MITC3 limit described by the source.
These are kinematic limits for the frozen homogeneous isotropic model, not a
claim about a state-dependent generalized section.

### Three-point Hammer rule (printed page 531, PDF page 5)

The source specifies three-point Hammer integration for both bending and shear
stiffness. The repository fixes the symmetric degree-two rule as

\[
 (\lambda,\xi,\eta)\in
 \{(2/3,1/6,1/6),(1/6,2/3,1/6),(1/6,1/6,2/3)\},
 \qquad w_g=A/3.
\]

The repository test proves the rule reproduces every barycentric monomial of
total degree at most two. Consequently it exactly integrates the quadratic
stiffness integrands produced by the linear `B_b` and `B_s` fields when the
isotropic section rigidities are constant. It is a fixed numerical rule, not
an exactness claim for variable, nonlinear, layered, or arbitrarily coupled
sections.

## Repository derivations (`D` authority)

### Rigidity form of the DKMT shear factor

For the strictly supported homogeneous isotropic section,

\[
 D=\frac{Eh^3}{12(1-\nu^2)},\qquad
 H=\kappa Gh=\frac{\kappa Eh}{2(1+\nu)}.
\]

Direct cancellation gives

\[
 \frac{12D}{HL_k^2}
 =\frac{2h^2}{\kappa(1-\nu)L_k^2}=\phi_k.
\]

This identity does not define `phi_k` for an arbitrary anisotropic shear
matrix, membrane-bending coupling, layered state-dependent tangent, or a
generalized section with no scalar `(D,H)` pair. Those cases remain blocked.

### CST membrane and 18-coordinate shell embedding

The candidate shell vector is

\[
 q=(u_1,v_1,w_1,\theta_{x1},\theta_{y1},\theta_{D1},\ldots,
    u_3,v_3,w_3,\theta_{x3},\theta_{y3},\theta_{D3})^T.
\]

For a flat triangle, `u=sum N_i u_i` and `v=sum N_i v_i`, so the engineering
membrane strain is the standard constant triangle field

\[
 \epsilon=(u_{,x},v_{,y},u_{,y}+v_{,x})^T=B_m q.
\]

An infinitesimal rotation vector changes the unit director `e_z` by
`theta cross e_z=(theta_y,-theta_x,0)`. Therefore the printed DKMT rotations
embed as

\[
 \beta_x=\theta_y,\qquad \beta_y=-\theta_x.
\]

This sign map is applied before the printed `B_b` and `B_s`; it must not be
changed by copying legacy TRI3 or S3 V1 strain operators. The CST membrane,
the DKMT bending/shear block, and the PL block are assembled as separate
variational contributions in the common 18-coordinate vector.

### Barycentric PL completion and drill scale

Let

\[
 \omega=\frac12(v_{,x}-u_{,y}),\qquad (Cq)_i=\theta_{D,i}-\omega,
\]

and use the exact barycentric mass matrix

\[
 M=\frac{A}{12}\begin{bmatrix}2&1&1\\1&2&1\\1&1&2\end{bmatrix}.
\]

The uncondensed multiplier blocks are

\[
 K_{q\tau}=C^TM,\qquad K_{\tau q}=MC,\qquad
 K_{\tau\tau}=-M/k_D.
\]

Because `M` is positive definite for `A>0` and `k_D>0`, exact Schur
elimination gives

\[
 -K_{q\tau}K_{\tau\tau}^{-1}K_{\tau q}=k_D C^TMC.
\]

For the isotropic membrane matrix

\[
 A=\begin{bmatrix}a&b&0\\b&a&0\\0&0&g\end{bmatrix},\quad
 a=Eh/(1-\nu^2),\ b=\nu a,\ g=Eh/[2(1+\nu)],
\]

with

\[
 P=\begin{bmatrix}1&0\\-1&0\\0&1\end{bmatrix},\qquad
 G=\operatorname{diag}(2,1/2),
\]

the generalized eigenvalues of `(P^TAP,G)` are both `2g`. Hence
`k_D=0.5 lambda_min(P^TAP,G)=g=A_66>0`. PL forces and energy are numerical
completion diagnostics and are excluded from physical section resultants.

### Direct variational resultants and work

For the supported uncoupled isotropic elastic section, define the raw station
resultants directly from the variational energy:

\[
 N=A\epsilon,\qquad M_b=D_b\chi,\qquad Q=H_s\gamma,
\]

so

\[
 \delta W_{int}=\int_A
 (N^T\delta\epsilon+M_b^T\delta\chi+Q^T\delta\gamma)\,dA.
\]

This is `SHELL_VARIATIONAL_RESULTANTS_V1`. It is not smoothed or extrapolated
recovery and it contains no PL force. A separate recovery identity is required
before any recovered/visualization values can be qualified.

For a dead transverse pressure `p_z` measured along the fixed physical
director, consistent load work is

\[
 \delta W_{ext}=\int_A p_z\sum_iN_i\delta w_i\,dA.
\]

For uniform pressure this gives `f_wi=p_z A/3` at all three nodes; the Hammer
rule also integrates the consistent load exactly for an affine `p_z` because
`N_i p_z` has degree at most two. Connectivity reordering permutes these loads
and does not change the pressure sign. Follower pressure, distributed couples,
offset loads, and nonlinear load tangents are outside the Stage-1 scope.

### D3 numbering transport and flat director polarity

For any of the six node permutations `pi`, let `Pi_pi` permute complete
six-coordinate nodal blocks and let `q^(pi)=Pi_pi q`. Reconstructing the same
physical fields from permuted barycentric coordinates yields

\[
 K^{(\pi)}=\Pi_\pi K\Pi_\pi^T,
 \quad f^{(\pi)}=\Pi_\pi f,
 \quad (q^{(\pi)})^TK^{(\pi)}q^{(\pi)}=q^TKq.
\]

Connectivity reordering does not reverse the physical director. Odd
permutations therefore change the signed chart orientation but not director
authority; the chart/frame transformation and engineering components must be
transported together.

An explicit physical director reversal is a different operation. In the
strictly supported flat, symmetric, isotropic, zero-offset section it is
handled by reversing the thickness coordinate and applying the corresponding
local component transform; the symmetric stiffness and variational work are
unchanged. Layer order, offsets, membrane-bending coupling, top/bottom
recovery, curved pseudocurvature, and history-bearing polarity reversal are not
covered by this derivation and remain blocked.

### General flat-flexure rank proof

Assume a nondegenerate triangle, positive bending and shear rigidities, and
`phi_k>0`. All three Hammer weights are positive. If flexural strain energy is
zero, the bending and shear strains vanish at every Hammer point. Both fields
are at most linear, and the three Hammer points are noncollinear, so both
fields vanish identically over the triangle.

If `B_sgamma y=0` identically, evaluation at each vertex gives the two
adjacent directed edge projections of `y`. The two edge directions at a
nondegenerate vertex are linearly independent; hence every component of `y`
is zero. Thus `B_sgamma` is unisolvent for the three side values. Apply this to

\[
 y=\operatorname{diag}(\phi_k/(1+\phi_k))A_u u_n.
\]

The diagonal is strictly positive, so zero shear implies `A_u u_n=0`.
Consequently `Delta beta_sn=A_delta^{-1}A_u u_n=0`. The enhanced curvature
then reduces to the symmetric gradient of the affine nodal rotation field.
Zero curvature therefore gives the planar infinitesimal-rigid form
`beta=c+a(-y,x)`, rather than immediately making `beta` constant. Substituting
this form into the three oriented edge equations `A_u u_n=0` and summing them
around the `(12,23,31)` loop cancels the nodal `w` differences and the constant
part of `beta`. The remaining rotational circulation is a nonzero multiple of
the signed triangle area times `a`. Nondegeneracy therefore forces `a=0`, so
`beta` is constant. Each row of `A_u u_n=0` now states

\[
 w_j-w_i=-\beta\mathbin{\cdot}(x_j-x_i,y_j-y_i).
\]

Therefore `w_i=c-beta dot (x_i,y_i)`. The flexural nullspace consists of only
the transverse translation and the two rigid rotations: dimension 3, rank 6
in the nine DKMT plate coordinates. This proof is shape-independent over the
entire nondegenerate flat-triangle domain; it replaces a brute-force rank scan.
It does not supply a quantitative lower coercivity bound as triangle quality
approaches the admission boundary, which remains a separately bounded gate.

For the membrane CST block, positive membrane rigidity and a nondegenerate
triangle give rank 3 in six in-plane coordinates, with only two translations
and one in-plane rigid rotation in its kernel. Since the membrane and flexural
coordinate sets are independent, the physical 15-coordinate CST plus DKMT
operator has rank 9 and exactly six rigid null modes. Embedding it in the 18
external coordinates adds three free drill coordinates, so its rank is 9 and
its nullity is 9.

The PL constraint matrix has full row rank because its three drill-coordinate
columns contain the 3 by 3 identity. Its positive Schur completion removes the
three nonphysical drill modes while retaining the six rigid modes, giving the
final 18-coordinate rank 12 and nullity 6. Finally, congruence through the
negative-definite multiplier block gives

\[
 \operatorname{inertia}
 \begin{bmatrix}K_{physical}&C^TM\\MC&-M/k_D\end{bmatrix}
 =(12\text{ positive},3\text{ negative},6\text{ zero}),
\]

so the full 21-variable PL saddle matrix has rank 15. These rank and inertia
claims apply only to the strict supported section and geometry scope above.

## Supported Stage-1 result

This map closes equation authority only for an opt-in flat-linear candidate
with:

- a nondegenerate flat triangle and a fixed physical director;
- small strain and small rotation;
- a homogeneous isotropic elastic, uncoupled, symmetric, zero-offset section;
- CST membrane, the printed Eqs. 12-16 and 20-41 DKMT bending/shear core, the
  fixed three-point Hammer rule, and the independently derived PL completion;
- direct variational raw resultants only; and
- consistent dead transverse pressure work only;
- exact D3 block-permutation transport in the restricted flat scope.

It does not close curved, dynamic, nonlinear, arbitrary generalized-section,
qualified recovery, mixed-mesh, performance, serialization/restart, ecosystem,
or default-activation gates.
