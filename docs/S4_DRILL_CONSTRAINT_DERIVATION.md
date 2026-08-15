# S4 drill-constraint derivation

Status: proof-stage artifact for the separately named research identity
`mitc4_plus_d_published_2025_linear_spin_constrained_research_v1`.

This document does not activate a production formulation. It derives and
tests one parameter-free kinematic constraint against the literal corrected
MITC4+/D Eq. 21 and Eqs. 24--25 mechanics. The legacy production default and
the restricted improved-S4 fail-closed policy remain unchanged.

Registered inputs:

- governing plan SHA-256
  `90B5C4903EE6A9C06056F7E1F3AB21DAE0626C185A27627843A04BF289430E3A`;
- Tor editor plan SHA-256
  `8E969863806461124510E7C31D99A3244FCCF15DD67424517320EE819439AA90`;
- cases SHA-256
  `B4D663382302E971752F0757F6E869549A54234F485235E06DBEF74085860F38`.

## 1. Kinematic statement

Let `H_c` be the continuum displacement interpolation before the `/D`
enrichment. At the midsurface, with full covariant and reciprocal bases
`g_k,g^k`, define

```text
omega_c(q) = (1/2) sum_(k=r,s,zeta) g^k cross H_c,k q,
d(q)       = sum_i N_i (d_bar dot theta_i).
```

At each 2x2 surface station, the constraint residual is `d-omega_c.d_bar`.
The assembled constraint is the discrete quadrature-L2 Galerkin normal
equation

```text
C_raw = D_sample^T (D_sample-F_sample),
D_sample[eg] = sqrt(mu_eg) D_phys,eg S_q A_e,
F_sample[eg] = sqrt(mu_eg) F_phys,eg S_q A_e,
mu_eg = w_r w_s ||g_r cross g_s|| > 0.
```

Only surface measure enters this statement. Density, thickness, and positive
stiffness/mass activity do not weight `C_raw`; hard-deleted elements are
removed before assembly. The independent constraint rows `C_D` are the
projector-derived canonical orthonormal basis of `row(C_raw)`.

## 2. Objectivity

For an analytic infinitesimal rigid field
`u=c+Omega cross x_h`, the continuum derivatives are
`u_,k=Omega cross g_k`. The triple-product identity and reciprocal completeness
give

```text
(1/2) sum_k g^k cross (Omega cross g_k)
= (1/2) [3 Omega - sum_k (g^k dot Omega) g_k]
= Omega.
```

With nodal rotations `theta_i=Omega`, partition of unity gives
`d=Omega.d_bar`. Therefore `D-F` annihilates every analytic rigid motion,
including warped and varied-director geometry. The oracle checks this result
directly rather than assuming it.

## 3. Flat-element drill effect

For a flat element with uniform directors, a pure nodal drill field has no
base-continuum displacement contribution: `F q_drill=0`. Its sampled trace is
the bilinear Q4 field `sum_i N_i theta_di`. The 2x2 quadrature Gram matrix of
the four Q4 shapes is positive definite, so the pure-drill restriction of
`C_raw` has rank four.

Consequently this hypothesis removes the entire four-coordinate pure-drill
subspace: the exact zero-mass constant gauge `G`, the positive-mass
checkerboard `Z`, and two energetic edge-difference directions. It is not
"gauge removal" and does not change the free local stiffness rank. The exact
constraint reduction later gives a six-coordinate element representation,
but the unconstrained element remains the accepted rank-16/eight-null
mechanics.

## 4. Mixed-unit and quotient algebra

For retained topology length `ell`, the physical-to-analysis map is

```text
q_phys = S_q q_hat,
S_q = blockdiag(ell I_3,I_3) per declared node.
```

The weighted free operators remain the accepted ones:

```text
B_w = vstack sqrt(alpha w/W_B) B S_q,
H_w = vstack sqrt(rho beta w/W_H) H S_q/ell.
```

The proof partitions `N=ker(B_w)` into exact zero-mass
`G=N intersect ker(H_w)` and registered-metric complement `P`. Rigid motion is
handled as a quotient image: `R_N=R intersect N`,
`RQ=range(Pi_P Q_RN)`, and `Z=P-RQ`. After homogeneous rows `C` are applied,
it uses the constrained lift
`L_C=N_C intersect (R_N+G)` and
`RQ_C=range(Pi_P_C Q_L_C)`. No raw representative intersection substitutes
for either quotient.

Physical supports, MPCs, and declared work-conjugate coupling rows are scaled,
normalized with their affine right-hand sides, and combined with `C_D` before
feasibility or nullspace analysis. Exact reduction is congruence only:

```text
K_r=T^T K T,  M_r=T^T M T,
T=basis ker([C_D;C_phys]).
```

It introduces no energy, penalty, tuned threshold, hourglass term, or hidden
stabilization.

## 5. Frozen evidence boundary

The independent oracle uses standard Python plus pure-Python
`mpmath==1.3.0`, with decimal precisions 80, 160, and 320 and sensitivity
multipliers 0.25, 1, and 4. Target-rounded matrices are rank-revealed from a
doubled-precision Gram eigenproblem. All restrictions inherit their registered
parent scale. Projectors are canonicalized from projector columns, never from
arbitrary vectors in degenerate singular spaces.

The evidence catalog covers literal Eq. 21/Eq. 25 columns, numbering and
frame covariance, warped geometry, positive activity, hard deletion, orphan
coordinates, connected/disconnected/odd-cycle topologies, a noncoplanar rigid
fan, affine feasibility, physical work rows, exact rigid/patch fields, and
reduced symmetry/PSD/congruence. The noncoplanar fan does not qualify a general
production coupling API; its extra rotational relations are meaningful only
under the fixture's declared rigid-joint derivation.

## 6. Focused result

The registered 80-decimal focused square run passed all three sensitivity
multipliers:

| Quantity | Free | With `C_D` |
|---|---:|---:|
| `rank(B)` / `rank([B;C_D])` | 16 | 18 |
| `N` / `N_C` | 8 | 6 |
| `G` / `G_C` | 1 | 0 |
| `P` / `P_C` | 7 | 6 |
| `R_N` / `L_C` | 6 | 6 |
| `RQ` / `RQ_C` | 6 | 6 |
| `Z` / `Z_C` | 1 | 0 |
| pure-drill restriction rank | 4 | 4 constrained coordinates |

The constant drill remained exact zero stiffness and zero mass before the
constraint. The alternating drill remained exact zero stiffness with positive
mass. All six rigid motions, the four registered patch fields, scale/frame/
origin covariance, and reduced PSD/congruence passed the frozen calculus.

## 7. Full registered result

The first monolithic full-catalog execution reached its frozen 30-minute
caller deadline and exited 124 without a scientific packet. It was an
execution blocker only and did not change any fixture, precision, threshold,
equation, or classification. The accepted supersession evaluates the same
complete catalog in independent 80-, 160-, and 320-decimal precision shards,
then performs a non-scientific canonical merge. Two serial shard sets must
produce byte-identical merged packets under the same environment manifest.

The content-addressed result below is inserted only after that registered
sharded catalog and independent closeout complete.

<!-- FINAL_RESULT_BEGIN -->
Outcome: `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

The execution-only addendum SHA-256
`AD808C3F1FDC88D67565D2ED0A08259A2E51ACF20389467D6DD055866644B056`
authorized only the extended 320-decimal caller deadline. Under environment
manifest SHA-256
`7F721DC09C2D7242009E5EBE637C07F65E5DF77A9FC25D4FB08066189FB4C647`,
both independent serial shard sets produced byte-identical 1,434,454-byte
merged packets with SHA-256
`8005C6D285263E33FF7F6D4B5138D5FBE4EFAB6A95834C401F94AF044ACD9E1B`.
Their precision-shard SHA-256 values were:

| Decimal digits | Shard SHA-256 |
|---:|---|
| 80 | `321D9AE299B4D0BE5F1F5FA49F6F3B6DAA3E4CA8D1D46A766705EB715CEFABE9` |
| 160 | `ED3951413EA8E655B9DC521536F06F3F0F7F18CE82403B0184384CFCB69459CB` |
| 320 | `E5C375415FACBC181034A0EACE2872F3A1FE5208562EB742CD37B2A203173B09` |

The parameter-free constraint clears the square checkerboard mechanism, but
the fully materialized warped topology is categorically threshold-sensitive.
At 80 and 320 decimal digits, and at 160 digits with multipliers 1 and 4, its
drill-constrained quotient has `L_C=6`, `RQ_C=6`, and `Z_C=0`. At 160 digits
with the preregistered multiplier 0.25 it instead has `L_C=5`, `RQ_C=5`, and
`Z_C=1`: a positive-mass quotient mechanism remains. With the qualified
`warped_fixed_drill` support row, the same case is feasible but changes from
`L_C=5`, `RQ_C=5`, `Z_C=0` to `L_C=4`, `RQ_C=4`, `Z_C=1` at that precision
and multiplier.

Thus the required cross-precision/sensitivity stability and universal
positive-mass-mechanism closure do not hold. The candidate is not certified
for adapter planning, no mode is relabelled as gauge, and the production
restriction remains unchanged. No threshold, fixture, penalty, stabilization,
or stiffness term was altered in response.
<!-- FINAL_RESULT_END -->

## 8. Exclusions

Even a certified result authorizes only later planning for a linear dense-row
adapter. This stage provides no production selector or public spin API and
does not qualify nonlinear `/D`, geometric stiffness, buckling, recovery,
optimized batches, arbitrary shell/beam intersections, or a separately named
energetic rank-18 formulation.
