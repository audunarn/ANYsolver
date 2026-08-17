# E4-PL variational drill closure

## Result

The study identity
`study_e4_pl.wg2020_surface_reduced_perturbed_lagrange_v1` receives

```text
PROVISIONAL_GO_E4_PL_LINEAR_QUALIFICATION_PLAN
```

The result closes a dimensionally consistent flat-affine variational identity
and its fatal exact screens. It does not register `candidate_e4_pl`, reproduce
HW29, or authorize a production element.

## Frozen kinematics

Use reference coordinates `(r,s)` on `[-1,1]^2`, the counter-clockwise node
order `(-1,-1),(1,-1),(1,1),(-1,1)`, and one constant right-handed frame
`(a1,a2,n)`. The external vector is node-major

```text
q_i=[u,v,w,theta_x,theta_y,theta_D].
```

For an affine map

```text
[x,y]^T = a + J [r,s]^T,
J=[[x_r,x_s],[y_r,y_s]], detJ != 0,
```

write every Q1 field as

```text
f=f0+fr*r+fs*s+frs*r*s.
```

The registered linear drill measure is

```text
c = theta_D - (v_x-u_y)/2.
```

Direct use of `grad_x=J^-T grad_(r,s)` gives the complete coefficient
classification

```text
c0 = d0 + (-x_s ur + x_r us - y_s vr + y_r vs)/(2 detJ),
cr = dr + (x_r urs + y_r vrs)/(2 detJ),
cs = ds - (x_s urs + y_s vrs)/(2 detJ),
crs = drs.
```

The last coefficient has no translation column. E4-PL deletes exactly this
rotation-only `r*s` constraint coefficient and retains

```text
c1 = c0 + cr*r + cs*s = P^T C q,
P=[1,r,s]^T.
```

No other constraint coefficient is deleted. The residual drill coefficient
is controlled separately by

```text
gamma=(1,-1,1,-1)^T/4,
d_rs=gamma^T d.
```

## Surface reduction and dimensions

The multiplier `T_h=P^T tau` has stress units. Starting from the volume-form
source grammar and integrating the constant thickness produces

```text
Pi_PL = integral_A h [T_h c1 - T_h^2/(2G)] dA,
G = E/[2(1+nu)].
```

Both integrand terms have stress units and `h dA` has volume units, so the
result is energy. An equivalent resultant multiplier `That=h T_h` would
instead require

```text
integral_A [That c1 - That^2/(2 G h)] dA.
```

Using `G` under an unweighted area integral is dimensionally excluded.

The scalar normalization is source-explicit. MITC9i equations (18)--(19)
print the shell-scalar form

```text
h integral_A [T_h*c-T_h^2/(2*gamma)] dA
```

and its eliminated form `gamma*h/2 integral_A c^2 dA`. E4-PL freezes that
scalar convention with `gamma=G`. A factor inferred from a differently
normalized skew-tensor multiplier is not imported into this identity.

For an affine element, exact positive `2 x 2` Gauss integration gives

```text
M = integral_A h P P^T dA
  = h |detJ| diag(4,4/3,4/3),
B = integral_A h P (P^T C) dA
  = M C.
```

Since `h>0` and `detJ!=0`, `M` is symmetric positive definite.

The separate residual-mode energy is frozen before outcomes as

```text
Pi_hg = epsilon_hg G (h A) (gamma^T d)^2,
epsilon_hg=1/1000,
A=4|detJ|.
```

It has the same energy dimension. Its Hessian is
`2 epsilon_hg G h A H_hg^T H_hg`, where `H_hg q=gamma^T d`. It is rank one,
PSD, and has zero action on constant drill.

## One uncondensed functional

Let

```text
z=[sigma_hat_1,...,sigma_hat_14,
   epsilon_hat_1,...,epsilon_hat_21]
```

be the actual 35 source-ordered WG parameters. The open-core certificate
constructs

```text
D=[[0,F^T],[F,H]],
Q=[Gq^T,0],
p=T5^T q,
```

from WG2020 equations (11)--(23), the WG2004 linear MITC map, and the
registered isotropic resultant matrix. The complete local functional is

```text
Pi(q,z,tau) = 1/2 z^T D z + p^T Q z
            + tau^T B q
            - (1/(2G)) tau^T M tau
            + epsilon_hg G h A (H_hg q)^2
            - q^T f.
```

The internal ordering is `[z_1,...,z_35,tau_0,tau_r,tau_s]`. The drill terms
are part of the functional before differentiation; no matrix is appended
after core condensation. The hourglass row is denoted `H_hg` to distinguish
it from the WG strain block `H`. At the unstressed linear reference the block
equations are

```text
[ K_hg       T5*Q   B^T  ] [dq  ]   [Rq  ]
[ Q^T*T5^T   D       0   ] [dz  ] = [Rz  ]
[ B           0     -M/G ] [dtau]   [Rtau].
```

The exact core certificate proves `rank(D)=35`; positivity of `G` and `M`
proves `rank(-M/G)=3`. Thus the actual combined local block is block diagonal
of rank 38. The two internal families do not couple to each other. Their
stationary values are

```text
z*(q)   = -D^-1 Q^T T5^T q,
tau*(q) = G M^-1 B q.
```

Substitution gives

```text
Pi_c(q) = 1/2 q^T K0 q
        + (G/2) q^T B^T M^-1 B q
        + epsilon_hg G h A (H_hg q)^2
        - q^T f,

K0  = -T5 Q D^-1 Q^T T5^T,
K_c = K0 + G B^T M^-1 B
          + 2 epsilon_hg G h A H_hg^T H_hg.
```

This proves stationary energy, residual, virtual-work, and symmetric-tangent
parity. The recovered `z*` alone produces physical shell resultants. `tau*`,
`c1`, `Hq`, PL energy, and hourglass energy are numerical drill diagnostics;
they are excluded from physical `N/M/Q`, stress, yield, fatigue, and code
checks.

## Exact rank and rigid states

The three retained rows have rank three. Restricted to the four pure nodal
drills, they are the first three rows of the Q1 Hadamard transform. The
hourglass row is its fourth row, so it is independent and the combined drill
map has rank four.

The open embedded core has rank fourteen and nullity ten: six physical rigid
vectors plus four drill coordinates. On this nullspace:

- pure common drill `g`, with `d=(1,1,1,1)`, has `C g=(1,0,0)` and is PL
  energetic;
- translation-only in-plane spin `s`, with `u=-y`, `v=x`, `d=0`, has
  `C s=(-1,0,0)` and is PL energetic;
- their matching rigid state `r=s+g` has `C r=0` and `H r=0` exactly;
- alternating drill `(1,-1,1,-1)` has `Cq=0` and `Hq=1`, so only the
  hourglass term controls it.

The remaining two nonconstant drill modes are controlled by `cr` and `cs`.
Thus the added form has rank four on the ten-dimensional core kernel and its
kernel there is exactly the six combined rigid motions. Therefore

```text
rank(K_c)=14+4=18,
nullity(K_c)=6.
```

All coefficients are positive for `E>0`, `h>0`, `-1<nu<0.5`, so the
condensed drill contribution is PSD and has no negative-energy mode.

## Patch and covariance closure

Affine constant membrane fields with drill equal to continuum spin give
`c1=0`; symmetric membrane strain has zero drill work. In particular,
`u=x,v=0,d=0` and `u=y/2,v=x/2,d=0` are exact nulls of both numerical terms.
Bending and transverse-shear patch coordinates do not enter `C` or `H`, so
the drill completion cannot change their source-core work. The six combined
rigid motions are exact nulls.

Translations of the origin leave derivatives and all four modal drill rows
unchanged. A proper frame rotation transforms displacement/rotation columns
orthogonally while preserving the scalar normal spin. D4 renumberings and
edge reversals act by permutation/sign changes on `P`, `C`, and `gamma`; `M`,
`B^T M^-1 B`, and `H^T H` transform by congruence. For a normal-reversing
orientation both `theta_D` and the oriented in-plane curl change sign, so the
energies remain invariant. The general affine formulas above prove the same
result for every rational or real nonsingular `J`, not only the square.

Uniform length/unit changes are carried by `J`, nodal translations, `h`, and
the area measure. Since `c` is dimensionless and the volume factor is explicit,
the energy has objective units and no hidden length or material parameter.

## Hostile controls and scope

This identity depends on the source-exact E4 open-core certificate. The
discarded generic `I35` Schur witness is nonclassifying and is not used by
E4-PL. This identity neither changes nor reinterprets the E1 common-drill failure,
Candidate A/C multiplier-kernel failures, or the E2-A nonunique displacement
bubbles. E4-PL is a different regularized variational identity. Decade changes
of `gamma_PL/G` and `epsilon_hg` remain diagnostic only; every registered
value is positive, so the fatal rank/nullspace classification is unchanged
and no value is tuned.

Distortion, locking, mesh-uniform behavior, generalized sections, finite
rotations, geometric stiffness, buckling, nonlinear response, mass, dynamics,
performance, and production integration remain for separately reviewed work.
The exact flat-affine screens therefore authorize only
`PROVISIONAL_GO_E4_PL_LINEAR_QUALIFICATION_PLAN`. Production remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
