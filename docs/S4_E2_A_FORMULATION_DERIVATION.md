# Candidate E2-A source and formulation identity derivation

## Gate result

The registered identity is
`candidate_e2_a.wg2020_n7_k0_displacement_allman_q4_kinematic_v1`.
The Wagner-Gruttmann Hu-Washizu core and the MITC4 shear field can be fixed,
but the displacement enrichment cannot.  The available primary sources fix
only a quadratic Allman/Cook edge construction driven by endpoint drill
**differences**.  That is the immutable E1-A hostile control and annihilates a
common drill.  A mean-drill/chord-spin term can be derived, but the conditions
registered for E2-A leave more than one non-equivalent displacement operator.

Consequently no `H(q)` is selected and the source gate closes with
`BLOCKED_E2_A_SOURCE_OR_FORMULATION_IDENTITY`, reason
`RANK_SUFFICIENT_DISPLACEMENT_ENRICHMENT_NONUNIQUE`.  No rank, stiffness,
mass, patch, or extension outcome is used to choose an interpolation.

## Frozen, non-ambiguous contract

The reference Q4 nodes and counter-clockwise edges are

```text
node       0          1          2          3
(r,s)   (-1,-1)    (+1,-1)    (+1,+1)    (-1,+1)
edge      0->1       1->2       2->3       3->0
```

The local frame is right-handed.  At the element center, `a1` is the
normalized first covariant vector, `a3` is the normalized cross product of
the first and second covariant vectors, and `a2=a3 cross a1`.  A degenerate
center Jacobian is inadmissible.  The node-major external order is
`[u1,u2,u3,theta1,theta2,theta3]` at each of four nodes.  The drill scalar is
`theta_D=theta dot a3`.

The generalized strain order is

```text
[epsilon_11, epsilon_22, 2 epsilon_12,
 kappa_11,   kappa_22,   2 kappa_12,
 gamma_1,    gamma_2]
```

and the work-conjugate resultant order is

```text
[N_11,N_22,N_12,M_11,M_22,M_12,Q_1,Q_2].
```

Thus the third membrane and curvature rows are engineering shear rows while
`N_12` and `M_12` are tensor-shear resultants.  This fixes the factor of two
exactly once at the strain interface.

The inherited Wagner-Gruttmann core uses `n=7`, `k=0`.  Its discontinuous
stress-resultant field has 14 parameters.  Its discontinuous independent
strain field has the 14 base parameters plus the first seven membrane
columns of the printed `M_eta^m` matrix:

```text
[xi,0,0]^T, [0,eta,0]^T, [0,0,xi]^T, [0,0,eta]^T,
[xi eta,0,0]^T, [0,xi eta,0]^T, [0,0,xi eta]^T.
```

No optional curvature column is retained.  Both local fields are eliminated
from the block system of Wagner-Gruttmann Eqs. (21)-(25) by exact local
Gaussian/Schur elimination when the registered mixed block is invertible.
They never become global degrees of freedom.  The positive surface rule is
the source rule `2 x 2` Gauss.

The MITC4 transverse-shear field is also fixed.  In the above natural order,

```text
gamma_r(r,s) = (1-s)/2 gamma_r(0,-1) + (1+s)/2 gamma_r(0,+1),
gamma_s(r,s) = (1-r)/2 gamma_s(-1,0) + (1+r)/2 gamma_s(+1,0).
```

These statements are primary-source inheritances.  They do not determine the
new in-plane displacement map.

## What the public Allman construction fixes

For an oriented physical edge `e=(i,j)`, let `L_e` be its length, `t_e` its
unit tangent, and `n_e=a3 cross t_e`.  The published quadratic
Allman/Cook construction fixes the fictitious midside displacement to

```text
u_mid^e - (u_i+u_j)/2 = (L_e/8) (theta_D_j-theta_D_i) n_e.
```

Lifting the four midpoint values with the standard serendipity edge functions
therefore factors every drill column through the cyclic difference operator.
It is exactly the E1-A field and sends `(1,1,1,1)` to zero.  Giving it a new
candidate name would not escape the accepted E1-A certificate.

The 2020 Hu-Washizu paper does not supply an all-node drill displacement map.
It uses five coordinates at ordinary nodes and six only at shell
intersections.  Its `n=7`, `k=0` equations consequently cannot choose a
rank-sufficient replacement for the difference-only edge field.  The 2004
core report states the same ordinary-node boundary explicitly.  The 1992
drilling article and the original Allman quadrilateral article were available
only as lawful metadata in this wave, not as complete equation-level sources.

## Necessary relative spin

A construction that distinguishes common drill from physical rigid spin must
use translations as well as rotations.  A chord-normal slope is not by itself
the required spin.  For a general affine displacement gradient `F=E+W`,

```text
n_e dot (u_j-u_i)/L_e = spin(W) + n_e dot E t_e.
```

Equating the nodal drill to that slope would therefore add strain-dependent
edge corrections and destroy affine membrane completeness.  A true-slope
cubic Hermite interpretation is an additional, non-Allman kinematic choice,
not a consequence of the selected sources.

An affine-exact relative variable can instead be built from the physical
center gradient.  Let `A=[X_,r X_,s]` and
`U=[u_,r^Q1 u_,s^Q1]` be the 3 by 2 geometry and bilinear-displacement
derivative matrices at the center.  With

```text
G = A^T A,
A^+ = G^-1 A^T,
L = U A^+,
omega_c = axl((L-L^T)/2) dot a3,
eta = (theta_D_0+theta_D_1+theta_D_2+theta_D_3)/4-omega_c,
```

`axl(skew(v))=v` uses `skew(v) w=v cross w`.  In any right-handed
orthonormal tangent basis this is exactly
`omega_c=(F_21-F_12)/2` for `F=U_2 A_2^-1`.  It is not the natural-coordinate
curl unless `A_2` is the identity.

For a rigid in-plane rotation by `phi`, `omega_c=theta_D_i=phi` and
`eta=0`.  A pure common drill gives `eta=phi`; the same translation-only
rigid-spin field with zero nodal drill gives `eta=-phi`.  For every affine
membrane field with nodal drill equal to its physical spin, `eta=0`.  This is
the required kind of translation-rotation coupling that the difference-only
field lacks.  The sources do not prescribe how `eta` enters the displacement.

## Exact non-uniqueness certificate

On a nondegenerate affine element define the surface Jacobian and the
orientation-corrected cofactor map

```text
J_A = sqrt(det(G)),
chi = a3 dot (X_,r cross X_,s) / J_A in {-1,+1},
C_A = chi J_A A G^-1.
```

Here `X_,r` and `X_,s` are the two columns of `A`.  `C_A` is 3 by 2 and has
units of length.  In an oriented two-dimensional Cartesian representation it
is `chi |det(A_2)| A_2^-T`.  It maps a reference edge-normal covector to the
corresponding physical in-plane normal: for example,
`(A e_r) dot (C_A e_s)=0` and `(A e_s) dot (C_A e_r)=0`.

Let `u_A` denote the already fixed physical quadratic Allman/Cook difference
field.  The following dimensionless reference pseudovectors are D4 covariant:

```text
P_0(r,s) = [-s(1-s^2), r(1-r^2)]^T,
P_b(r,s) = [-s,r]^T (1-r^2)(1-s^2).
```

For every dimensionless scalar `alpha`, define the explicit family

```text
u_C(alpha) = sum_i N_i u_i + u_A + eta C_A [P_0 + alpha P_b].
```

Both pseudovectors vanish at all vertices.  `P_b` also vanishes on the
complete boundary, so every member has the same cubic mean-spin boundary
trace as `u_C(0)`, the same quadratic difference trace `u_A`, and unchanged
nodal translations.

The covariance is exact.  For a signed-permutation D4 map
`xi_old=Q xi_new`,

```text
A_new = A Q,                 C_A_new = C_A Q,
P(Q xi) = det(Q) Q P(xi),   eta_new = det(Q) eta.
```

Therefore
`eta_new C_A_new P(xi_new)=eta C_A P(xi_old)`, including reversals.
If the director alone is reversed while the surface parametrization is held
fixed, both `chi` and `eta` change sign and their product is unchanged.  Under
a proper global frame rotation `R`, `C_A` becomes `R C_A`, the physical
gradient becomes `R L R^T`, and the enrichment becomes `R u_C`.  An origin
shift changes none of `A`, `U`, `C_A`, or `eta`.  Under a uniform change of
length unit by `lambda`, `A`, `U`, and `C_A` scale by `lambda`, while `L` and
`eta` remain dimensionless, so the enriched displacement scales by
`lambda`.

For every affine membrane field `u=b+F X`, `U=F A` and the above physical
gradient recovers its tangential `F` exactly.  With nodal drill equal to the
in-plane spin, `eta=0` and the nodal drill differences in `u_A` vanish; the
ordinary Q1 field is therefore reproduced exactly.  The same holds for all
in-plane rigid motions.  Pure common drill and translation-only rigid spin
activate equal and opposite mean fields, while their matching combination
gives zero.  The fields at `alpha=0` and `alpha=1` have identical complete
boundary traces but different interior displacement gradients when `eta` is
nonzero.

This is not the only ambiguity.  Replacing the bubble by any independent
D4-invariant boundary-zero polynomial multiple produces another admissible
field, and no source selects the cubic mean-spin boundary trace or its
normalization in the first place.  Neither dimensional consistency, D4
covariance, numbering or reversal covariance, vertex interpolation, affine
completeness, rigid annihilation, the `2 x 2` rule, nor the mixed core
determines `alpha`.

Selecting `alpha`, deleting the interior mode, or choosing a normalization
because it improves rank or a benchmark would violate the pre-outcome
identity gate.  Hence no complete `H(q)` or `B=grad_s H` exists for this
registered candidate.

## Work map and extension consequence

The intended variational convention would be

```text
delta W_ext = integral(delta u_h dot p) dA
            + integral_boundary(delta u_h dot t) ds
            + sum_i delta theta_i dot m_i,
f_consistent = derivative(W_ext,q),
M_consistent = integral rho H^T H dV.
```

The same selected `H` would have to generate membrane strain, consistent
loads and mass, recovery, geometric stiffness, and the finite-rotation first
and second variations.  Because `H` is nonunique, those operators are also
nonunique.  A warped/curved lift and work-equivalent normal-moment map cannot
be reviewed without silently selecting one member of the family.  Extension
closure is therefore not reached; it is not classified as a mechanics
failure because the higher-precedence identity block stops the wave first.

E1-RH remains `DEFERRED_NOT_RUN`, all accepted E1 results remain immutable,
and production remains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
