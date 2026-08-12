# S4 improved formulation: full 2 x 2 MITC4+/D

## Status and scope

This document is the notation and sign contract for the corrected scalar
reference candidate for `S4_improved`. It is not production activation or a
rank-policy decision. The element mechanics are the full-integration
published 2025 MITC4+/D element: the
improved MITC4+ assumed membrane field, classical MITC4 transverse-shear
field, and the physical `/D` drilling construction are one formulation. There
is no drilling penalty, hourglass coefficient, reduced-integration switch, or
fallback to legacy shell theory.

The equations are mapped from these primary sources:

1. Y. Ko, K.-J. Bathe, and X. Zhang, "Continuum mechanics-based shell
   elements with six degrees of freedom at each node - the MITC4/D and
   MITC4+/D elements," *Computers & Structures* 308 (2025) 107622,
   [doi:10.1016/j.compstruc.2024.107622](https://doi.org/10.1016/j.compstruc.2024.107622).
   This is the authority for the common drilling direction, midside
   enrichment, Eq. (21) drill-tensor transform, and the Eqs. (24)-(25)
   membrane field.
2. Y. Ko, P.-S. Lee, and K.-J. Bathe, "A new MITC4+ shell element,"
   *Computers & Structures* 182 (2017) 404-418,
   [doi:10.1016/j.compstruc.2016.11.004](https://doi.org/10.1016/j.compstruc.2016.11.004).
   Its Eq. (27) is retained only as an explicitly named non-default comparison
   operator. It is not the selected published-2025 MITC4+/D membrane field.
3. Y. Ko, P.-S. Lee, and K.-J. Bathe, "The MITC4+ shell element in
   geometric nonlinear analysis," *Computers & Structures* 185 (2017) 1-14,
   [doi:10.1016/j.compstruc.2017.01.015](https://doi.org/10.1016/j.compstruc.2017.01.015).
   This is the authority for total-Lagrangian Green-Lagrange strains,
   consistent first and second variations, and finite director rotations.

The reference implementation covered by this document supplies exact scalar
linear operators and a finite-difference oracle boundary. Production
finite-rotation state updates, material integration, geometric stiffness, and
batched kernels consume the same operators but are integrated in their
separately owned modules.

## Coordinates, numbering, and degrees of freedom

ANYsolver accepts a conventional counter-clockwise Q4 node order with natural
corners

```text
node       0          1          2          3
(r,s)   (-1,-1)    (+1,-1)    (+1,+1)    (-1,+1)
```

The papers number the same cycle starting at the opposite corner:

```text
paper node      1          2          3          4
ANYsolver       2          3          0          1
(r,s)        (+1,+1)    (-1,+1)    (-1,-1)    (+1,-1)
```

This is a cyclic permutation only. All paper edge orientations and equation
signs are preserved by traversing ANYsolver edges `0->1->2->3->0`.

The element vector has 24 entries and is node-major:

```text
q_i = [u_x, u_y, u_z, theta_x, theta_y, theta_z]_i
q_e = [q_0, q_1, q_2, q_3]
```

`r` and `s` are midsurface natural coordinates. `zeta in [-1,1]` is the
natural thickness coordinate (the papers use `t` or `xi`). Physical time is
never denoted by `zeta`. `X_i`, `a_i`, and `Vn_i` are the reference corner
position, positive thickness, and unit reference director. Directors are
element-corner numeric input; they are not queried from source geometry in an
element operation.

The bilinear shape functions are

```text
N_i(r,s) = (1 + r_i r)(1 + s_i s)/4,
r_i = [-1,+1,+1,-1],  s_i = [-1,-1,+1,+1].
```

## Continuum geometry and displacement

Following Ko-Bathe-Zhang (2025), Eqs. (1)-(4), the reference continuum is

```text
X(r,s,zeta) = sum_i N_i X_i
            + zeta/2 sum_i a_i N_i Vn_i,

u(r,s,zeta) = sum_i N_i u_i
            + zeta/2 sum_i a_i N_i (theta_i x Vn_i)
            + u_D(r,s).
```

`u_D` is the physical midsurface enrichment described below. It is included
in inertia as well as strain. The three reference covariant bases are
`g_r=X_,r`, `g_s=X_,s`, and `g_zeta=X_,zeta`. The linear covariant tensor
components are

```text
e_ij = 1/2 (g_i . u_,j + g_j . u_,i).
```

No center-flat geometry replaces this continuum. The center plane is used
only to define distortion measures and a common drilling direction.

At the midsurface, the characteristic vectors are

```text
x_r = 1/4 sum_i r_i X_i,
x_s = 1/4 sum_i s_i X_i,
x_d = 1/4 sum_i r_i s_i X_i,
X_,r = x_r + s x_d,
X_,s = x_s + r x_d.
```

The reciprocal center-plane vectors `m^r,m^s` satisfy

```text
m^alpha . x_beta = delta^alpha_beta,
m^alpha . V_D = 0.
```

## Physical `/D` drilling construction

### Common direction and rotation split

The common drill direction is the normal to the unique center plane
(Ko-Bathe-Zhang 2025, Eq. 5):

```text
V_D = (x_r x x_s) / ||x_r x x_s||.
```

Every corner drill scalar is measured about this same direction,

```text
theta_i^D = theta_i . V_D,
theta_i^D-vector = theta_i^D V_D,
theta_i^S = theta_i - theta_i^D-vector.
```

Using one direction is essential for rigid-motion and cyclic-numbering
invariance on warped elements. A changing corner normal is not substituted.
The total vector `theta_i` remains in the continuum director term, so curved
shell bending caused by a common-direction rotation is retained.

### Fictitious midside displacement

There is one fictitious node on each oriented edge `I=(i,j=i+1 mod 4)`.
Let `L_I` be its chord length, `ell` its edge coordinate, and
`Delta theta_I^D = theta_j^D-theta_i^D`. The Allman/Cook interpolation adopted
by Ko-Bathe-Zhang (2025), Eq. (12), gives the midside normal displacement

```text
u_n^I(ell) = 4 ell/L_I (1-ell/L_I) theta_n^I,
theta_n^I = L_I/8 Delta theta_I^D.
```

With `x_m^I=(X_i-X_j)/8`, edge-midpoint covariant vectors `x_r^I,x_s^I`,
and

```text
c_r^I = x_m^I . (-x_r^I x V_D),
c_s^I = x_m^I . ( x_s^I x V_D),
```

the continuous midsurface enrichment is (2025 Eqs. 15-16)

```text
u_D = m^r sum_I h_I c_r^I Delta theta_I^D
    - m^s sum_I h_I c_s^I Delta theta_I^D.
```

`h_I` is the standard quadratic midside function, equal to one at the edge
midpoint. This displacement interpolation is used by the consistent mass.

### Assumed drill-membrane derivatives

For strain, the paper's curl-marked interpolation (2025 Eq. 11) retains only
the derivative tangent to each edge: `h_,r` on the bottom/top edges and
`h_,s` on the right/left edges. It avoids raising the required surface
quadrature order and passes the patch tests. With
`J=det[g_r,g_s,g_zeta]_(r,s,0)` and `J0=J(0,0,0)`, Eqs. (18)-(19) first form
fixed-center tensor components (denoted by a tilde here). Each edge contributes

```text
e_rr~^D += (J0/J) h_,r c_r Delta theta^D,
e_ss~^D -= (J0/J) h_,s c_s Delta theta^D,
e_rs~^D += (J0/(2J)) (h_,s c_r - h_,r c_s) Delta theta^D.
```

These components are not added directly to the natural membrane rows. Let
`gbar^r=m^r`, `gbar^s=m^s`, and

```text
A_ik = g_i . gbar^k
     = [[1+s c_r, s c_s],
        [r c_r,   1+r c_s]].
```

The literal double covariant transformation in Eq. (21) is

```text
e_ij^D = A_ik A_jl e_kl~^D.
```

For tensor component vectors `[e_rr,e_ss,e_rs]`, its code matrix is

```text
T(A) = [[a^2, b^2, 2ab],
        [c^2, d^2, 2cd],
        [ac,  bd,  ad+bc]],  A=[[a,b],[c,d]].
```

Tensor shear remains tensor shear through this transform. Conversion to local
engineering shear occurs once, at the local-strain API boundary. This is
Ko-Bathe-Zhang (2025), Eqs. (17)-(21), written edge-wise. It is a
physical membrane strain, not a constraint or penalty. A constant global
rotation has `Delta theta_I^D=0` and therefore produces no drill strain.

## Complete MITC4+ assumed membrane field

Only the midsurface displacement-based membrane contribution is replaced.
The continuum bending terms remain displacement based. Define the five tying
components in the outer A-E order printed in Ko-Bathe-Zhang (2025), Eq. (25):

```text
A: e_rr^m( 0,+1)    B: e_rr^m( 0,-1)
C: e_ss^m(+1, 0)    D: e_ss^m(-1, 0)
E: e_rs^m( 0, 0)
```

The in-plane distortion scalars and denominator are

```text
c_r = x_d . m^r,
c_s = x_d . m^s,
d   = c_r^2 + c_s^2 - 1.
```

The selected valid convex-map branch requires `d<0`; a non-negative or
numerically vanishing `d` is rejected. Define the Eq. (25c) coefficients

```text
a_A = c_r(c_r-1)/(2d),  a_B = c_r(c_r+1)/(2d),
a_C = c_s(c_s-1)/(2d),  a_D = c_s(c_s+1)/(2d),
a_E = 2c_r c_s/d.
```

Let `g=1/sqrt(3)` and use the direct Appendix-B.1 reciprocal-basis products
at the barred points `Abar=(0,g)`, `Bbar=(0,-g)`, `Cbar=(g,0)`, and
`Dbar=(-g,0)`:

```text
A_r=x_r.g^r|Abar, A_s=x_r.g^s|Abar,
B_r=x_r.g^r|Bbar, B_s=x_r.g^s|Bbar,
C_r=x_s.g^r|Cbar, C_s=x_s.g^s|Cbar,
D_r=x_s.g^r|Dbar, D_s=x_s.g^s|Dbar.

n1=(A_r^2-B_r^2)/2, n2=(A_s^2-B_s^2)/2,
n3=(A_r^2+B_r^2)/2, n4=(A_r A_s+B_r B_s)/2,
n5=(A_r A_s-B_r B_s)/2,

m1=(C_s^2-D_s^2)/2, m2=(C_r^2-D_r^2)/2,
m3=(C_s^2+D_s^2)/2, m4=(C_r C_s+D_r D_s)/2,
m5=(C_r C_s-D_r D_s)/2.
```

The Jacobian ratio is `lambda(r,s)=J0/J(r,s,0)`. The selected final tensor
operator is literal Eq. (25):

```text
[e_rr~, e_ss~, e_rs~]^T
  = Q(r,s) R(r,s) S [e_rr^A,e_rr^B,e_ss^C,e_ss^D,e_rs^E]^T,

Q = [[(1+c_r s)^2, (c_s s)^2, 2 c_s s(1+c_r s)],
     [(c_r r)^2, (1+c_s r)^2, 2 c_r r(1+c_s r)],
     [c_r r(1+c_r s), c_s s(1+c_s r),
      c_r c_s r s+(1+c_r s)(1+c_s r)]],

R = lambda *
    [[1/lambda+sqrt(3)n1 s, sqrt(3)n2 s, 2sqrt(3)n5 s,
      n3 s, n4 s, n1 s/sqrt(3)],
     [sqrt(3)m2 r, 1/lambda+sqrt(3)m1 r, 2sqrt(3)m5 r,
      m4 r, m3 r, m1 r/sqrt(3)],
     [0, 0, 1/lambda, 0, 0, 0]],

S = [[1/2-a_A, 1/2-a_B, -a_C, -a_D, -a_E],
     [-a_A, -a_B, 1/2-a_C, 1/2-a_D, -a_E],
     [0, 0, 0, 0, 1],
     [1/2, -1/2, 0, 0, 0],
     [0, 0, 1/2, -1/2, 0],
     [a_A, a_B, a_C, a_D, a_E]].
```

The reciprocal products above are evaluated from the direct Appendix-B.1
definitions: each `g^r,g^s` is a row of the full three-dimensional reciprocal
to `[g_r,g_s,g_zeta]` at its barred midsurface point. This deliberately keeps
the interpolated thickness basis in warped/director-varying cases. The
simplifying Appendix-B.2 identities are not substituted.
The separately named 2017 Eq. (27) helper remains only for comparison tests;
it is not called by the selected 2025 path and is never a fallback.

The total in-plane covariant strain is therefore

```text
e_ij = e_ij^(MITC4+ membrane) + e_ij^D
     + zeta e_ij^b1 + zeta^2 e_ij^b2,  i,j in {r,s}.
```

## MITC4 transverse shear

The covariant transverse shear is tied at the classical edge midpoints
(Ko-Bathe-Zhang 2025, Eq. 20):

```text
e_rzeta~ = 1/2(1+s)e_rzeta(0,+1)
          +1/2(1-s)e_rzeta(0,-1),

e_szeta~ = 1/2(1+r)e_szeta(+1,0)
          +1/2(1-r)e_szeta(-1,0).
```

The tying values use the same continuum displacement/director interpolation.
No full-displacement shear, one-point shear integration, or empirical shear
factor is substituted.

## Local frame and engineering component order

At an integration point, the shell-aligned frame follows Ko-Lee-Bathe (2017
nonlinear paper), Eq. (17):

```text
L3 = g_zeta/||g_zeta||,
L1 = (g_s x L3)/||g_s x L3||,
L2 = L3 x L1.
```

Let `g^r,g^s,g^zeta` be the reciprocal covariant bases. Tensor components
transform as

```text
e_local_ij = e_cov_kl (L_i . g^k)(L_j . g^l).
```

The stable local operator orders are

```text
strain:    [eps_11, eps_22, gamma_12, gamma_13, gamma_23]
stress:    [sig_11, sig_22, tau_12,   tau_13,   tau_23]
```

where engineering shear `gamma_ij=2 eps_ij` is used. Positive director side
is `+zeta`; positive curvature produces increasing positive-side strain.
Reversing element orientation and all corner directors is an upstream model
construction operation, never an in-kernel correction.

## Surface and thickness quadrature

The permanent formulation uses the four tensor-product surface points

```text
(r,s) = (+/-1/sqrt(3), +/-1/sqrt(3)),  weight = 1.
```

The continuum scalar oracle uses two thickness points
`zeta=+/-1/sqrt(3)`, also with unit weight. The volume measure is
`det[g_r,g_s,g_zeta] dr ds dzeta`. Reference construction rejects a
non-finite, zero, or reversed determinant. No absolute determinant silently
repairs an inverted element.

## Generalized section convention

The stable generalized operators are

```text
epsilon0 = B_m q_e = [eps_11, eps_22, gamma_12],
kappa    = B_b q_e = [kappa_11, kappa_22, kappa_12],
gamma    = B_s q_e = [gamma_13, gamma_23].
```

`B_m` and `B_s` are evaluated at the midsurface. `B_b` is the coefficient of
physical distance along `L3`; it is obtained from the odd-in-`zeta` continuum
in-plane field divided by `||g_zeta||`. This retains the reference director
kinematics and fixes the curvature sign above.

For section matrices `A,B,D,As`, resultants are

```text
[N] = [A  B ] [epsilon0],
[M]   [B' D ] [kappa  ],
 Q  = As gamma.
```

The scalar stiffness integrand is explicitly

```text
B_m' A B_m + B_m' B B_b + B_b' B' B_m
+ B_b' D B_b + B_s' As B_s.
```

Thus a supplied nonsymmetric coupling matrix is not silently symmetrized:
the upper-right block is `B` and the lower-left block is `B.T`.
Generalized sections are resultants-only unless separate layer data exist.

## Linear stiffness, residual, and tangent

For a homogeneous plane-stress constitutive matrix `C` in the five-component
local order,

```text
K_e = integral_V B' C B dV.
```

For a generalized section, the surface expression above is used. Conservative
inputs produce a symmetric matrix. The exact scalar linear residual and
tangent are

```text
r_e(q_e) = K_e q_e,
dr_e/dq_e = K_e.
```

Finite differences are used only to check this derivative. The free element
must have exactly six rigid modes and no extra zero or negative elastic mode.

## Consistent mass

The mass uses the same continuum displacement, including the midsurface `/D`
enrichment:

```text
M_e = integral_V rho H' H dV,
u(r,s,zeta) = H(r,s,zeta) q_e.
```

It therefore includes translational inertia, rotary inertia from the
director interpolation, and the physical inertia of the drilling-driven edge
displacement. No artificial diagonal drilling mass is added.

## Total-Lagrangian finite rotations and analytical tangent

The nonlinear production path follows Ko-Lee-Bathe (2017 nonlinear paper):

```text
E_ij = 1/2 (g_i^current . g_j^current
           -g_i^reference . g_j^reference),
```

with the same MITC4+ membrane and MITC4 shear projections applied consistently
to both Green-Lagrange strains and their increments (paper Eqs. 7-23). The
internal force and tangent are the first and second variations of the same
discrete strain energy (paper Eqs. 24-25). Director triads are updated by a
proper finite rotation; the paper gives a quaternion update in Eq. (26).

For `/D`, the 2025 paper states that the linear drill-membrane operator is used
with total drill rotation accumulated about the instantaneous common
direction `V_D`. This defines the nonlinear extension but does not authorize a
numerical production tangent. The nonlinear owner must differentiate the
current common direction, rotation projection, assumed membrane coefficients,
and drill enrichment in the residual. Until that exact variation is present,
only the documented scalar linear operator is qualified.

## Geometric stiffness and recovery

Geometric stiffness is the stress-weighted second variation from the same
total-Lagrangian kinematics, not a legacy or center-flat substitute. In the
notation of Ko-Lee-Bathe (2017 nonlinear paper),

```text
K_t = integral B' C B dV + integral S_ij N_ij dV.
```

Recovery evaluates the same assumed membrane, drill-membrane, bending, and
shear fields used in assembly. Covariant fields are transformed into the same
local frame before forming `N/M/Q`, top/bottom stresses, or global tensors.

## Source geometry and sign boundary

Source geometry may provide validated corner coordinates, per-element-corner
directors, face-use orientation, and provenance during preprocessing. The
reference object contains only immutable numeric arrays and compact indices.
No geometry document is parsed and no live geometry API is called by reference
construction, stiffness, residual, tangent, mass, or recovery.

The positive normal/director, positive pressure side, material axes, and
top/bottom labels must already agree when the FE model is built. Geometry
schema migration and face-use correction remain upstream responsibilities.

## Deterministic validity checks

Reference construction fails closed on:

- wrong array shapes or non-finite values;
- non-positive thickness;
- non-unit or mutually reversed corner directors;
- a singular center plane or reciprocal basis;
- a non-negative or near-zero MITC4+ distortion denominator `d`;
- a non-positive continuum Jacobian at any reference quadrature point.

Tolerances scale with element dimensions, Jacobians, and machine precision;
geometry heal/merge tolerances are not reused. Immutable numeric inputs and
the formulation identifier form a deterministic reference signature.

## Qualification obligations

The reference operators remain candidates pending tests for partition of unity,
derivative sums, interpolation, reciprocal bases, rigid translation and
rotation, cyclic numbering, symmetry, the unchanged six-mode/rank gate, no negative mode,
membrane/bending/shear patch fields, warped valid Q4s, exact mass resultants,
and finite-difference residual/tangent agreement. Batch kernels must match
these arrays and scalar results; they must not rederive a different theory.
