# E4-PL-Q1R numbered-frame identity

## Status and boundary

This document preregisters the plan-only `D` derivation for
`candidate_e4_pl_q1r.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1`.
It contains no assembled mechanics, observed rank, observed D4 count,
scientific output, agreement digest, selected scientific terminal, or Q1B
plan. The accepted Q1A mechanics remain nonclassifying history and are not
used in this derivation.

The only new formulation content is the explicit numbered-frame transport.
The retained predecessor is the WG2020/WG2004 Hu-Washizu Q4 identity with
`n=7`, `k=0`, source MITC shear, 35 physical-core local variables, three PL
multiplier variables, positive unshifted `2 x 2` Gauss quadrature,
`gamma_PL=G`, `epsilon_hg=10^-3`, and deletion of only the faulty equal-order
`r*s` PL coefficient.

## Natural convention and all eight actions

Let `xi=[r,s]^T`, with natural nodes

```text
1=(-1,-1), 2=(+1,-1), 3=(+1,+1), 4=(-1,+1).
```

For an operation `g`, `A_g` maps new coordinates to base coordinates,

```text
xi_0=A_g xi_g,
xi_{p_g(I)}=A_g xi_I,
X_I^(g)=X_{p_g(I)},
X^(g)(xi_g)=X(A_g xi_g).
```

The complete and exclusive table is:

| ID | `A_g` | `p_g` | `delta=det(A_g)` |
|---|---|---|---:|
| `E` | `[[1,0],[0,1]]` | `(1,2,3,4)` | +1 |
| `R90` | `[[0,-1],[1,0]]` | `(2,3,4,1)` | +1 |
| `R180` | `[[-1,0],[0,-1]]` | `(3,4,1,2)` | +1 |
| `R270` | `[[0,1],[-1,0]]` | `(4,1,2,3)` | +1 |
| `MR` | `[[1,0],[0,-1]]` | `(4,3,2,1)` | -1 |
| `MS` | `[[-1,0],[0,1]]` | `(2,1,4,3)` | -1 |
| `MD` | `[[0,1],[1,0]]` | `(1,4,3,2)` | -1 |
| `MA` | `[[0,-1],[-1,0]]` | `(3,2,1,4)` | -1 |

`E`, `R90`, `R180`, and `R270` are `D4+`; `MR`, `MS`, `MD`, and
`MA` are `D4-`. `MD`, tuple `(1,4,3,2)`, is the named complete orientation
reversal. There is no ninth reversal action and no active/passive convention
may be substituted.

Define the scalar node permutation by

```text
[P_g^(4)]_{I,J}=1 exactly when J=p_g(I)
```

and the node-only global permutation

```text
P_g=P_g^(4) tensor I_6,       q^(g)=P_g q.
```

The six Cartesian components at a node remain ordered
`[UX,UY,UZ,RX,RY,RZ]`. At Gauss points the correspondence is exactly
`xi_0=A_g xi_g`; the symmetric four-point set is permuted, never
reinterpreted.

## Source frame and admissibility

WG2020 equation 7 is reconstructed for every numbered geometry:

```text
dbar_1=X_3-X_1,                    dbar_2=X_2-X_4,
dhat_1=dbar_1/||dbar_1||,          dhat_2=dbar_2/||dbar_2||,
t_1=(dhat_1+dhat_2)/||dhat_1+dhat_2||,
t_2=(dhat_1-dhat_2)/||dhat_1-dhat_2||,
t_3=t_1 cross t_2,
T(X)=[t_1 t_2 t_3].
```

The numbered element is inadmissible if either diagonal has zero length or
if either normalized diagonal sum or difference has zero length. These are
exact predicates. No tolerance-selected fallback frame is allowed.

Put `a=dhat_1`, `b=dhat_2`. Direct substitution of each frozen permutation
gives:

| ID | `(a_g,b_g)` | `(t_1^g,t_2^g,t_3^g)` |
|---|---|---|
| `E` | `(a,b)` | `(t_1,t_2,t_3)` |
| `R90` | `(-b,a)` | `(t_2,-t_1,t_3)` |
| `R180` | `(-a,-b)` | `(-t_1,-t_2,t_3)` |
| `R270` | `(b,-a)` | `(-t_2,t_1,t_3)` |
| `MR` | `(b,a)` | `(t_1,-t_2,-t_3)` |
| `MS` | `(-b,-a)` | `(-t_1,t_2,-t_3)` |
| `MD` | `(a,-b)` | `(t_2,t_1,-t_3)` |
| `MA` | `(-a,b)` | `(-t_2,-t_1,-t_3)` |

The normalizations in each row are exact because the operation only signs or
swaps the two unit diagonals. Define

```text
Ahat_g=diag(A_g,delta).
```

The table proves, for all eight actions and every admissible element,

```text
T(X^(g))=T(X) Ahat_g,
H_g:=T(X)^T T(X^(g))=Ahat_g.
```

Since `A_g^T A_g=I_2` and `delta^2=1`, `Ahat_g` is orthogonal. Its
determinant is `det(A_g)*delta=1`, so `H_g` belongs to `SO(3)` even for
`D4-`. A parameter reflection is therefore a proper three-dimensional frame
rotation whose third column reverses. An additional `diag(1,-1)` repair would
contradict the source reconstruction and is forbidden. The action is
geometry-independent although `T(X)` itself is geometry-dependent.

For a proper global rotation `R` and a translation `b`, equation 7 also gives

```text
T(R X+b)=R T(X),
```

because differences remove `b`, Euclidean normalization commutes with `R`,
and `R a cross R b=R(a cross b)` for `det(R)=+1`.

## Local physical and drilling coordinates

Let `T_12=[t_1 t_2]` and define the per-node embeddings

```text
B_5(T) = block_diag(T,T_12) in R^(6x5),
b_D(T) = [0,0,0,t_3^T]^T in R^6.
```

The frame-dependent element maps are

```text
T5(X)=I_4 tensor B_5(T(X)) in R^(24x20),
QD(X)=I_4 tensor b_D(T(X)) in R^(24x4).
```

They satisfy exactly

```text
T5^T T5=I_20,       QD^T QD=I_4,       T5^T QD=0,
Pi_5=T5 T5^T,       Pi_D=QD QD^T,       Pi_5+Pi_D=I_24.
```

Thus `Pi_5` and `Pi_D` are respectively the physical and numerical-drill
projectors. With

```text
L_g=block_diag(Ahat_g^T,A_g^T) in R^(5x5),
L_g^(20)=P_g^(4) tensor L_g,
D_g^(4)=delta P_g^(4),
```

the source-frame theorem gives

```text
T5(X^(g)) L_g^(20)=P_g T5(X),
QD(X^(g)) D_g^(4)=P_g QD(X).
```

Consequently

```text
Pi_5^(g)=P_g Pi_5 P_g^T,       Pi_D^(g)=P_g Pi_D P_g^T,
theta_D^(g)=delta P_g^(4) theta_D.
```

A registered physical load is constructed only as `f=T5 p_f`. It obeys
`QD^T f=0` and transports as

```text
p_f^(g)=L_g^(20) p_f,
f^(g)=P_g f=T5(X^(g)) p_f^(g).
```

Direct normal drill moments are outside the candidate.

## Work-conjugate field transport

At corresponding points, ordinary three-dimensional local vector components
obey `a_0=H_g a_g`. The registered two-dimensional shell pseudo-field maps
are frozen separately by their source definitions. With `delta=det(A_g)`,

```text
epsilon_0=A_g epsilon_g A_g^T,     N_0=A_g N_g A_g^T,
kappa_0=delta A_g kappa_g A_g^T,   M_0=delta A_g M_g A_g^T,
gamma_0=delta A_g gamma_g,         Q_0=delta A_g Q_g.
```

Membrane strain and curvature use engineering vectors
`[11,22,2*12]`; membrane resultant and bending moment use conjugate vectors
`[11,22,12]`. If `A_g=[[a,b],[c,d]]`, their explicit extraction maps are

```text
C_eng(A) = [[a^2,b^2,a*b],
            [c^2,d^2,c*d],
            [2*a*c,2*b*d,a*d+b*c]],

C_res(A) = [[a^2,b^2,2*a*b],
            [c^2,d^2,2*c*d],
            [a*c,b*d,a*d+b*c]].
```

Hence `e_0=C_eng(A_g)e_g`, `n_0=C_res(A_g)n_g`, and both curvature
and moment maps acquire the same factor `delta`. Shear strain and shear
resultant both use `delta A_g`. Orthogonality and `delta^2=1` prove

```text
n_0^T e_0=n_g^T e_g,
m_0^T k_0=m_g^T k_g,
Q_0^T gamma_0=Q_g^T gamma_g.
```

The independent Hu-Washizu membrane, curvature, and transverse-shear strain
fields use the same strain-side maps; their independent stress-resultant
fields use the conjugate resultant-side maps. Comparisons reconstruct fields
at corresponding points before transport. Raw mixed parameter vectors are
not observables and have no preregistered direct comparison.

## PL pseudoscalar and multiplier transport

Let

```text
ell(r,s)=[1,r,s]^T,
S_g=diag(1,A_g).
```

Then `ell(A_g xi)=S_g ell(xi)`. The drill constraint `c` and its
work-conjugate scalar multiplier `T_h` are oriented pseudoscalars:

```text
c_0(A_g xi)=delta c_g(xi),
T_0(A_g xi)=delta T_g(xi).
```

Writing `T_h=lambda^T ell`, coefficient equality gives exactly

```text
lambda_0=delta S_g lambda_g.
```

If `M_h=integral t ell ell^T dA`, then

```text
M_0=S_g M_g S_g^T,
lambda_0^T M_0 lambda_0=lambda_g^T M_g lambda_g.
```

At corresponding physical points the two signs cancel in `T_h c`, while
`T_h^2` is unchanged. The positive physical area measure and thickness are
unchanged. Therefore both

```text
integral_A t T_h c dA
integral_A t T_h^2/(2G) dA
```

are invariant. Raw multiplier coefficients may never be compared without
`delta S_g`.

For the separate residual mode, freeze WT2011 equations 26.44--26.45 rather
than a geometry-independent Hadamard row. In the current numbered source
frame define the four-vectors

```text
xi  =(-1,+1,+1,-1)^T,
eta =(-1,-1,+1,+1)^T,
h4  =(+1,-1,+1,-1)^T,
S1_i=x_i-x_c,                  S2_i=y_i-y_c,
x_c=x(0,0),                    y_c=y(0,0),
j_c=det(J_map(0,0)),           A=4*j_c,
b1=((eta^T S2)*xi-(xi^T S2)*eta)/(4*A),
b2=(-(eta^T S1)*xi+(xi^T S1)*eta)/(4*A),
gamma=(h4-(h4^T S1)*b1-(h4^T S2)*b2)/4.
```

All dots above are exact four-vector contractions and `j_c>0` is a registered
geometry precondition. The residual coordinate and energy are

```text
d_hg=gamma^T theta_D,
Pi_hg=epsilon_hg*G*t*A*d_hg^2.
```

The entire construction, including `S1`, `S2`, `j_c`, `A`, `b1`, `b2`, and
`gamma`, is recomputed from every numbered geometry in its reconstructed
source frame. A base gamma row is never reused and no sign is repaired by
inspection. Only transported global residual-mode energy, residual, and
tangent are compared. A raw gamma vector or signed scalar residual coordinate
is non-authoritative unless a separate signed transport is preregistered
before execution.

## Global frame, origin, recovery, and supports

For `R in SO(3)`, define

```text
G_R=I_4 tensor block_diag(R,R).
```

Under `X*=R X+b`, `q*=G_R q`, the required identities are

```text
T5*=G_R T5,                    QD*=G_R QD,
Pi_5*=G_R Pi_5 G_R^T,          Pi_D*=G_R Pi_D G_R^T,
K*=G_R K G_R^T,                r*=G_R r,
f*=G_R f,                      reaction*=G_R reaction.
```

Local physical recovery is unchanged when geometry and fields rotate
together; its global tensor/vector reconstruction rotates with `R`. Under
numbering, the authoritative condensed comparisons are

```text
P_g^T K^(g) P_g=K,
P_g^T r^(g)=r,
P_g^T f^(g)=f,
```

followed by the registered field transports above. PL multipliers and the
residual mode are numerical diagnostics and remain excluded from physical
`N/M/Q`, stress, yield, fatigue, and code recovery.

A support row matrix `A_bc` is physical only when

```text
A_bc QD=0,
```

equivalently when it factors through `T5^T`. It may constrain translations
and the two tangent rotations. The physically same supports transport as
`A_bc^(g)=A_bc P_g^T` and `A_bc*=A_bc G_R^T`; their reactions then obey the
same global covariance. Prescribed drill rows, prescribed nonzero drill
rotations, and direct drill reactions are excluded.

## Frozen preregistration boundary

The six rational base geometries, the exact `R_star` transform, patch fields,
physical load, material resultants, support grammar, interval policy, and
terminal precedence are frozen in the companion canonical JSON contracts.
Positive numbered-frame Jacobians are required at the centre and all four
Gauss stations. No tolerance may create a frame, change an orientation, or
turn an inconclusive radical bound into an equality.

This derivation is complete only as a preregistration identity. It neither
classifies Q1R nor authorizes mechanics execution, Q1B, or production use.
Every later outcome retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`, and the
legacy `ShellElement` remains the default.
