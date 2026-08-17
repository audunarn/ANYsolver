# E4 open Hu-Washizu core identity

## Result

The study identity
`study_e4_core.wg2020_n7_k0_full_integration_reference_v1` receives
`GO_E4_OPEN_CORE_IDENTITY` for the bounded E4-0 flat-affine linear study.
This is an identity result for the five-parameter physical core; it is not a
24-coordinate drilling formulation and it does not register a candidate.

The public Wagner-Gruttmann 2020 formulation closes the Hu-Washizu
functional, its first and second variations, the `n=7`, `k=0` mixed spaces,
positive `2 x 2` surface quadrature, and Gaussian elimination of the local
fields. Its equations (11)--(18) print the stress and independent-strain
interpolations, and equations (21)--(23) print the actual `F`, `G`, and `H`
blocks. The open 2004 report prints the compatible linear Q4/MITC strain map
and the isotropic resultant law used in the exact reference cases. Thus the
classification below uses the source-specific 14-stress/21-strain block, not
a generic 35-variable Schur example. Neither source supplies a drill
completion at every node.

## Frozen reference and coordinate split

Let `(a1,a2,n)` be one constant right-handed orthonormal frame on a flat
affine Q4. At every node the physical coordinate block is

```text
p_i = [u1,u2,u3,theta_1,theta_2]
```

and the external study block is

```text
q_i = [u1,u2,u3,theta_1,theta_2,theta_D].
```

The block-diagonal maps are

```text
T5_i = diag(I3,[a1 a2]) in R^(6 x 5),
QD_i = [0,0,0,n]^T       in R^(6 x 1),
T5    = diag(T5_1,...,T5_4),
QD    = diag(QD_1,...,QD_4).
```

Here the last notation means four columns with disjoint nodal support. Frame
orthonormality proves exactly

```text
T5^T T5 = I20,
QD^T QD = I4,
T5^T QD = 0,
T5 T5^T + QD QD^T = I24.
```

Thus every `q` has the unique decomposition

```text
q = T5 p + QD d,
p = T5^T q,
d = QD^T q.
```

The drill-free embedding of any physical residual, tangent, and load is

```text
r0(q) = T5 r5(T5^T q),
K0    = T5 K5 T5^T,
f0    = T5 f5.
```

Consequently `K0 QD=0`, `QD^T r0=0`, and `QD^T f0=0`. Direct nodal drill
moments are outside E4-0. Physical resultants are recovered from `p` and the
stationary WG internal fields only; changing `d` cannot change physical
`N/M/Q` or stress.

## Source-exact mixed operator

Let the source ordering be eight resultant/strain components

```text
[11,22,12, k11,k22,k12, 13,23],
```

with engineering `12` components. For `n=7`, `k=0`, WG2020 equations
(11)--(18) give fourteen stress parameters and twenty-one independent-strain
parameters. In the normalized affine square `x=r`, `y=s`, their polynomial
columns are, without a change of basis:

```text
N_sigma:
  I8,
  N11=s*a8, N22=r*a9,
  M11=s*a10, M22=r*a11,
  Q1=s*a12, Q2=r*a13;

N_epsilon:
  the same first fourteen columns,
  eps11=r*e14+r*s*e18,
  eps22=s*e15+r*s*e19,
  2eps12=r*e16+s*e17+r*s*e20.
```

The general affine form is fixed in `e4_core_cases.json` by the printed
WG2020 transformation `T(a,b)`: `T_sigma=T(2,1)`,
`T_epsilon=T(1,2)`, and the shear transformation is the affine Jacobian.
Because `n=7`, no quadratic column containing the shape factor `c` is used.

The open WG2004 linear equations give the compatible/MITC map `B`. On the
normalized square its polynomial coefficients are

```text
membrane:
  u_r+u_rs*s,
  v_s+v_rs*r,
  u_s+u_rs*r+v_r+v_rs*s;

bending:
  theta_y,r+theta_y,rs*s,
 -(theta_x,s+theta_x,rs*r),
  theta_y,s+theta_y,rs*r-theta_x,r-theta_x,rs*s;

tied shear:
  w_r+theta_y,0+s*(w_rs+theta_y,s),
  w_s-theta_x,0+r*(w_rs-theta_x,r).
```

The exact isotropic reference uses `E=5/2`, `nu=1/4`, `h=1`, hence `G=1`,
and

```text
C = diag(h*Cm, h^3*Cm/12, (5/6)*G*h*I2),
Cm=[[8/3,2/3,0],[2/3,8/3,0],[0,0,1]].
```

With positive `2 x 2` integration, define exactly as WG2020 equations
(21)--(23)

```text
F = -integral N_epsilon^T N_sigma dA,       (21 x 14)
Gq=  integral N_sigma^T B dA,               (14 x 20)
H =  integral N_epsilon^T C N_epsilon dA,   (21 x 21)
D = [[0,F^T],[F,H]],                         (35 x 35)
Q = [Gq^T,0],                                (20 x 35).
```

At the unstressed linear reference `K_g=0`, so Gaussian elimination gives

```text
K5 = -Q D^-1 Q^T = Gq^T S Gq,
S  = -(D^-1)_(stress,stress).
```

This is the actual registered core block. It replaces the earlier generic
`H=I35` algebra witness, which is nonclassifying and no longer appears in the
case packet.

## Exact invertibility, rank, and parity certificate

Independent rational assembly on the normalized square gives

```text
rank(F)=14, rank(H)=21, rank(Gq)=14, rank(D)=35.
```

The exact LDL pivots of `S` are

```text
2/3, 5/8, 1/4, 1/18, 5/96, 1/48, 5/24,
5/24, 15/8, 15/8, 1/6, 1/6, 5/8, 5/8.
```

They are all positive. Therefore `S` is positive definite and `K5` is PSD of
rank fourteen. The compact rational-array hashes for `F`, `Gq`, `H`, `D`,
`S`, and `K5` are frozen in the exact case packet. The nodal-to-modal
Hadamard map then proves that `ker(K5)` is exactly the six recorded rigid
vectors; there is no seventh physical mode. The second rational affine case
is assembled from the same printed transformations and has the same exact
ranks. Since every affine transformation used above is nonsingular, this is
also a change-of-basis proof for the registered nonsingular affine family.

It follows from the isometry of `T5` that

```text
rank(K0) = rank(K5) = 14,
ker(K0)  = T5 ker(K5) direct-sum range(QD),
dim ker(K0) = 6 + 4 = 10.
```

The four added null directions are coordinate drill directions, not physical
rigid motions.

For stationary local fields `z=[sigma_hat,epsilon_hat]`, the source equations
are

```text
D z + Q^T p = rhs_z,
z*(p)=D^-1(rhs_z-Q^T p).
```

Substitution into the same quadratic functional yields `K5` above. Hence the
uncondensed and condensed energy, residual, virtual work, and tangent agree
at stationarity, and recovery uses the same `z*(p)`. This is exact Schur
parity for the source block, not a separately chosen stiffness.

## Boundary and terminal

The GO is limited to a flat affine Q4, a constant frame, homogeneous
positive-definite isotropic material, `n=7`, `k=0`, source MITC shear, and
positive `2 x 2` integration. Mass, finite rotations, geometric stiffness,
warped geometry, nonlinear response, and buckling are not inferred.

The published WG2020 numerical eigenvalue example is retained only as
corroboration; it is not used to classify the core. The coordinate split,
source-exact rank and invertibility certificate, Schur identity, load-work
boundary, and recovery boundary close every prerequisite needed by the
bounded WS and PL screens. The terminal is therefore:

```text
GO_E4_OPEN_CORE_IDENTITY
```

Production remains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
