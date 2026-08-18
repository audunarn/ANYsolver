# E4-PL-Q1A planar formulation identity

## Identity result

The equation-level source gate closes one, and only one, non-affine planar
continuation of the accepted E4-0 identity. The dormant research identity is

```text
candidate_e4_pl_q1.wg2020_n7_k0_surface_pl_planar_linear_iso_v1
```

This is not HW29, an Allman element, a production registration, or a claim of
mesh-uniform qualification. The construction combines the already accepted
WG2020/WG2004 five-parameter core with the already accepted scalar
perturbed-Lagrange drill completion. The sources fix the non-affine choices as
follows:

- WG2020 equations 7-18 and 21-23 fix the constant element frame, centre
  Jacobian transformations, `n=7`, `k=0` mixed spaces, centroid corrections,
  `j0/j` enrichment factor, block equations, and positive unshifted `2 x 2`
  rule.
- WG2004 equations 19-21 fix the two pairs of midside transverse-shear samples,
  their natural interpolation, and the pointwise inverse-Jacobian map.
- WT2011 equation 26.42 selects the linear expansion of the drilling constraint
  at the element centre. Equations 26.43-26.45 fix the geometry-dependent
  residual row; equations 26.46-26.47 fix the centre-basis transform and the
  three element-local multiplier coefficients.
- MITC9i equations 18-19 fix the shell-scalar, thickness-weighted PL
  normalization used by E4-0.

The alternatives listed in the source map - an L2 projection of the complete
rational curl, a fourth Gauss-value coefficient, and the rectangular
Hadamard residual row on an irregular element - are therefore different
identities and are not selected by rank or benchmark behavior.

The formulation identity and element-local algebra close, but the frozen
numbering-covariance screen below fails exactly on two asymmetric cases. The
Q1A terminal is therefore
`NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE`; none of the closed component results
below authorizes Q1B.

## Geometry, frame, and source core

Use the counter-clockwise natural nodes

```text
(-1,-1), (1,-1), (1,1), (-1,1)
```

and the WG constant right-handed element frame. The frozen planar cases are
already expressed in this common frame. For any admitted physical node set,
write the bilinear geometry as

```text
x = x0 + xr*r + xs*s + xrs*r*s,
y = y0 + yr*r + ys*s + yrs*r*s.
```

With the Cartesian-by-natural Jacobian

```text
J = [[x_,r, x_,s],
     [y_,r, y_,s]],
```

its determinant is exactly

```text
j(r,s) = jc + jr*r + js*s,
jc = xr*ys - xs*yr,
jr = xr*yrs - xrs*yr,
js = xrs*ys - xs*yrs.
```

The source centroid offsets are `r_bar=jr/(3*jc)` and
`s_bar=js/(3*jc)`. Stress and the first fourteen independent-strain columns
use the WG centre-Jacobian transformations and these offsets. The seven
`n=7` strain columns use

```text
(jc/j) * T_epsilon(Jc) * M7(r,s),
```

where `M7` is the first seven printed WG2020 membrane columns. No
pointwise-J replacement is made. The compatible membrane and curvature rows
use the isoparametric derivatives. The two natural MITC shear rows are sampled
at `(0,-1),(0,1)` and `(-1,0),(1,0)`, interpolated in the transverse natural
coordinate, and transformed at each station by `J^-T`. All `F`, `Gq`, and `H`
blocks use the same four positive Gauss stations and physical factor `j`.

This construction reduces byte-for-byte at matrix-value level to the accepted
E4-0 core on the unit square. The independent Q1A reference also obtains exact
core ranks

```text
rank(F)=14, rank(Gq)=14, rank(H)=21,
rank(D)=35, rank(K5)=14
```

on the square, affine skew parallelogram, trapezoid, and tapered-skew probe.

## Unique centre-linear drilling rows

For a Q1 scalar field use modal coefficients `[f0,fr,fs,frs]`. Define

```text
c = theta_D - (v_,x-u_,y)/2
  = theta_D + N/(2*j),
N = -x_,s*u_,r + x_,r*u_,s - y_,s*v_,r + y_,r*v_,s.
```

The source-selected centre linearization is

```text
c1 = c0 + r*cr + s*cs = P^T*C*q,  P=[1,r,s]^T,
c0 = d0 + N0/(2*jc),
cr = dr + (Nr*jc-N0*jr)/(2*jc^2),
cs = ds + (Ns*jc-N0*js)/(2*jc^2),
```

with

```text
N0 = -xs*ur + xr*us - ys*vr + yr*vs,
Nr = -xrs*ur + xr*urs - yrs*vr + yr*vrs,
Ns = -xs*urs + xrs*us - ys*vrs + yrs*vs.
```

Thus `C` is a fixed `3 x 24` nodal operator. It is not a fit to the four Gauss
values. At positive `2 x 2` quadrature,

```text
M = sum_gp t*j_gp*P_gp*P_gp^T,
B = sum_gp t*j_gp*P_gp*P_gp^T*C = M*C.
```

`M` is positive definite because the weights and Jacobians are positive and
`[1,r,s]` is independent at the four stations. The scalar multiplier is stored
in the common orthonormal frame. The constant determinant introduced by the
WT centre-basis antisymmetric-tensor transformation is absorbed bijectively
into the three discontinuous element coefficients. This is a parameterization,
not a new geometry-dependent stiffness scale; `gamma_PL=G` remains unchanged.

## Geometry-dependent residual row

Let

```text
xi  = (-1, 1, 1,-1),
eta = (-1,-1, 1, 1),
h4  = ( 1,-1, 1,-1),
S1_i = x_i-x_center,
S2_i = y_i-y_center,
A = 4*jc.
```

The frozen WT gamma construction is

```text
b1 = ((eta*S2)*xi-(xi*S2)*eta)/(4*A),
b2 = (-(eta*S1)*xi+(xi*S1)*eta)/(4*A),
gamma = (h4-(h4*S1)*b1-(h4*S2)*b2)/4.
```

Here juxtaposition inside parentheses denotes a nodal dot product. Exactly,
`gamma*1=0` and `gamma*h4=1`. It reduces to `h4/4` on a
parallelogram. On both registered non-affine probes it is

```text
(3/14,-3/14,2/7,-2/7).
```

The residual energy is only

```text
Pi_hg = (1/1000)*G*t*A*(gamma*d)^2.
```

No physical displacement column and no physical-resultant recovery term is
introduced by this row.

## Covariance result and patch boundary

The preregistered D4 action is a signed permutation of `(r,s)` and the nodes.
The common component frame is unchanged for a proper action. For an improper
action the frozen right-handed-frame repair is `F=diag(1,-1)`, acting on
`(u,v)` and `(theta_x,theta_y)`, with `w` and `theta_D` multiplied by
`det(F)=-1`. No transformation is selected from an observed matrix result.

Exact source-local reassembly gives the following K5/K24 congruence counts:

```text
unit_square   8/8, orientation reversal PASS
affine_skew   4/8, orientation reversal FAIL
trapezoid     4/8, orientation reversal FAIL
tapered_skew  8/8, orientation reversal PASS
```

The failures are exact nonzero rational or `a+b*sqrt(3)` differences, not a
tolerance, rank, or conditioning result. Replacing the fixed-frame action by
a D4-dependent physical-frame reorientation can change the result; doing so
after observing the counts changes the frozen covariance contract and is not
an admissible repair in Q1A.

The separate proper global-frame check passes when the already local WG
operator is embedded into the rotated global frame. Origin shifts cancel from
every derivative and relative nodal coordinate. The metre/millimetre actions
at scales `1/1000` and `1000` pass with the dimensionally transformed material
and coordinate maps. These passing subgates do not override the D4 and
reversal failure.

For any affine physical membrane field

```text
u=a*x+b*y, v=c*x+d*y,
theta_D=(c-b)/2,
```

the complete physical curl is constant and `c1=0`; the gamma row also
annihilates constant drill. Rigid translations, the matched rigid spin,
constant extension, symmetric shear, and the registered general affine patch
are therefore exact numerical nulls on every frozen geometry. Pure bending
and transverse-shear coordinates have no `u`, `v`, or drill column in these
two numerical operators.

WG stationary fields alone recover physical `N/M/Q` and stresses. PL
multipliers, centre-linear mismatch, residual amplitude, and both numerical
energies are diagnostics. Total reactions may be projected and reported, but
their PL/hourglass projection is kept distinct from WG physical recovery.

The membrane-with-nonzero-spin, bending, transverse-shear, and combined
physical patch/recovery records all pass; the physical support projector and
reaction separation also pass. Nevertheless, the exact D4/reversal failure is
fatal under the governing terminal table. Continuous G1 geometry, refinement,
stability, locking, and Q1B execution are not authorized. Production remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
