# S4 Stage-M Candidate-B energetic derivation

Status: preregistered mechanics definition; no numerical outcome.

## 1. Authority and identity

This document defines the proof-only Stage-M Candidate B named
`mitc4_plus_hd_compatible_surface_v1`. It is governed by:

- `docs/S4_FULL_PRODUCTION_QUALIFICATION_PROGRAM.md`, raw SHA-256
  `17CB914002E362A5DB2B475981A46020C1F39E8BA5398B4A7BEC64C39EEEC4A7`;
- `docs/S4_STAGE_M_MECHANICS_SELECTION_PLAN.md`, raw SHA-256
  `4AE07F5954C9A2E6E6B002BEA24A9FC274B528D405EE6E5FCACE630893021E5B`;
  and
- the accepted source-boundary manifest
  `docs/reference_cases/s4_stage_m_source_manifest.json`, raw SHA-256
  `22B7B9D56DCC180CEE29F43AD4F31C69547A7C74CB212FD5B7D301909A8C0BE6`.

Candidate A remains `BLOCKED_PRIMARY_SOURCE_UNAVAILABLE`. Candidate B is
comparison evidence only and cannot resolve the overall Stage-M selection
while Candidate A remains blocked.

Candidate B is not the literal Ko-Zhang-Bathe 2025 MITC4+/D identity. The
published operator and its Eq. 21 remain immutable baseline evidence. This
candidate retains the physical Eq. 15-16 midsurface displacement enrichment
and literal Eqs. 24-25/Appendix B, but supersedes Eq. 21 only inside its own
strain-energy operator. The 2017 Eq. 27 comparison remains internal,
non-default, and unused.

The source formulas are visually bound to the preserved 2025 PDF at
`.perf2-worktrees/s4-improved-integration/tmp/pdfs/mitc4_d_2025.pdf`,
9,046,388 bytes, raw SHA-256
`89C10DE1FB13056EB967111C2DBB28FE2D18179090814141455F4E8901D919EA`.
Eqs. 15-16 define the drill-dependent midsurface displacement; Eqs. 17-19
derive its in-plane strain for indices `i,j=1,2`; Eq. 20 separately defines
the transverse-shear interpolation; Eq. 21 maps the assumed drill membrane
strain; and Eqs. 24-25 define the base MITC4+ membrane field.

## 2. Frozen Q4 and edge convention

Natural coordinates are `(r,s) in [-1,1]^2`. Corner order is

```text
0=(-1,-1), 1=(1,-1), 2=(1,1), 3=(-1,1).
```

Oriented edge order is bottom, right, top, left:

```text
I=0:(0,1), I=1:(1,2), I=2:(2,3), I=3:(3,0).
```

The Eq. 10 midside functions are

```text
h0 = (1-r^2)(1-s)/2,
h1 = (1-s^2)(1+r)/2,
h2 = (1-r^2)(1+s)/2,
h3 = (1-s^2)(1-r)/2.
```

Candidate B uses every exact derivative of those functions:

```text
h0,r = -r(1-s),       h0,s = -(1-r^2)/2,
h1,r =  (1-s^2)/2,    h1,s = -s(1+r),
h2,r = -r(1+s),       h2,s =  (1-r^2)/2,
h3,r = -(1-s^2)/2,    h3,s = -s(1-r).
```

The curl-marked Eq. 11 derivatives, in which the cross-edge derivatives are
zeroed, are forbidden in Candidate B. No Eq. 21 `J0/J` scale, fixed-center
tensor transform, or assumed drill-membrane row may enter this operator.

For element-center reciprocal in-plane vectors `m^r,m^s`, the accepted fixed
drill direction `V_D`, and the accepted edge coefficients `c_r^I,c_s^I`, set

```text
d_I = c_r^I m^r - c_s^I m^s,
L_I q = V_D . (theta_j - theta_i)
```

for oriented edge `I=(i,j)`. The physical Eq. 15-16 enrichment and its full
surface derivatives are

```text
H_D(r,s)   = sum_I h_I(r,s)   d_I L_I,
H_D,r(r,s) = sum_I h_I,r(r,s) d_I L_I,
H_D,s(r,s) = sum_I h_I,s(r,s) d_I L_I.
```

These are `3 x 24` operators. Their signs and edge orientation are fixed by
the displayed equations; an implementation must also reproduce the accepted
`_drill_displacement_enrichment` values before its Candidate-B strain results
are considered.

## 3. Compatible surface strain and exact composition

Let `a_r=X_,r(r,s,0)` and `a_s=X_,s(r,s,0)` be the reference midsurface
covariant vectors at the evaluation point. Candidate B adds only the symmetric
in-surface gradient of `H_D`:

```text
B_D[rr] = a_r^T H_D,r,
B_D[ss] = a_s^T H_D,s,
B_D[rs] = (a_r^T H_D,s + a_s^T H_D,r)/2.
```

The three rows are tensor strain. The accepted covariant-to-local conversion
performs the engineering-shear factor exactly once after the complete
five-row operator is formed.

Let `B_raw(H_c;r,s,zeta)` be the displacement-compatible continuum operator
without `H_D`, `B_mid(H_c;r,s)` its first three rows at `zeta=0`,
`B_25(H_c;r,s)` the literal Eqs. 24-25 field whose tying samples exclude
`H_D`, and `B_20(H_c;r,s,zeta)` the literal Eq. 20 MITC4 transverse shear.
The Candidate-B covariant operator is exactly

```text
B_B[:3] = B_raw[:3] + B_25 - B_mid + B_D,
B_B[3:] = B_20.
```

`B_D` is added after Eq. 25 tying. It replaces Eq. 21; it is not accumulated
with Eq. 21. The transverse-shear rows contain no direct derivative of `H_D`.
This surface-only choice is forced by the registered Candidate-B scope and by
the source separation between in-plane Eqs. 17-19 and shear Eq. 20. Adding
`g_zeta . H_D,r/s` would define a third, director- and warp-dependent shear
formulation and is outside this stage.

The existing full covariant-to-local transform is retained. On an oblique
warped basis it may project the declared surface tensor into local components;
that geometric projection is reported and is not manually suppressed.

## 4. Potential, residual, tangent, and mass

At every integration point, let `C` be the existing physical five-component
constitutive tensor. The Candidate-B element potential is one total potential:

```text
Pi_B(q) = (1/2) sum_qp w_qp (B_B q)^T C (B_B q) - q^T f.
```

The sum includes the complete `(B_base+B_D)^T C (B_base+B_D)` expression and
both cross terms. It is forbidden to add a separate `B_D^T C B_D` stiffness
to the published matrix. Such a split would not be the Hessian of the declared
total strain energy.

For either registered quadrature rule, every natural quadrature weight is
strictly positive and the physical volume weight is

```text
w_qp = w_r w_s w_zeta det([g_r g_s g_zeta]) > 0.
```

Define the global element strain-evaluation operator and physical
displacement/mass operator by

```text
mathcal_B_B = vstack_qp B_B(r_qp,s_qp,zeta_qp),
mathcal_H_B = vstack_qp sqrt(rho_qp w_qp) H_B(r_qp,s_qp,zeta_qp).
```

Multiplying rows of `mathcal_B_B` by positive `sqrt(w_qp)` or by an invertible
square root of the pointwise SPD constitutive tensor does not change its
kernel. Therefore, for strictly positive weights and pointwise SPD `C`,

```text
ker(K_B) = ker(mathcal_B_B),
rank(K_B) = rank(mathcal_B_B),
N = ker(mathcal_B_B),
G = N intersection ker(mathcal_H_B).
```

`P`, `R_N`, `R_G`, `RQ`, and `Z` then use the inherited registered-metric
projector and quotient-image definitions. A nonpositive or nonfinite Jacobian,
quadrature weight, density, or a nonfinite/non-SPD constitutive tensor fails
closed before a rank, PSD, or coercivity claim. Zero density is allowed only
in a separately declared massless fixture and cannot support a `G`/positive-
mass classification.

For linear material data,

```text
r_B(q) = K_B q - f,
K_B = sum_qp w_qp B_B^T C B_B.
```

The proof oracle must differentiate the displayed potential independently and
show that these are its first and second variations. Symmetry, positive
semidefiniteness, virtual work, constitutive scaling, and exact rigid
annihilation are mandatory.

The physical displacement interpolation remains

```text
H_B = H_c + H_D,
M_B = sum_qp rho w_qp H_B^T H_B.
```

There is no stiffness-derived inertia, drill-inertia coefficient, or lumped
substitute. Equal common-drill rotations give `H_D q=0`, so the exact
zero-mass gauge remains zero mass. The former checkerboard `Z` direction must
retain positive physical mass and acquire positive physical strain energy.

For generalized `A/B/D/As` sections, recompute the Candidate-B midsurface
operator `B_m` from `B_25+B_D`, retain the existing odd-in-`zeta` bending
operator `B_b`, and retain the direct Eq. 20 shear tying while applying the
same full covariant-to-local midsurface transform. The energy is exactly

```text
1/2 integral_A [
    e_m^T A e_m
  + e_m^T B kappa
  + kappa^T B^T e_m
  + kappa^T D kappa
  + gamma^T As gamma
] dA.
```

`H_D` belongs to generalized midsurface `H0` and mass-per-area. It does not
enter the through-thickness rotary `H1` or rotary-inertia-per-area term. An
asymmetric mass first moment is unsupported by the current section schema and
must fail closed rather than be inferred.

## 5. Frozen quadrature

No adaptive or per-case quadrature choice is permitted.

The primary Candidate-B continuum rule is tensor-product `G3 x G3 x G2`:

```text
G2 nodes   = {-1/sqrt(3), +1/sqrt(3)},
G2 weights = {1, 1},

G3 nodes   = {-sqrt(3/5), 0, +sqrt(3/5)},
G3 weights = {5/9, 8/9, 5/9}.
```

The same primary rule integrates the total stiffness energy and consistent
mass. Three surface points per direction are the minimum Gauss rule exact for
the affine-element Candidate-B contribution: the full enrichment derivatives
reach degree two and their quadratic energy reaches degree four.

The mandatory sensitivity rule is tensor-product `G4 x G4 x G3`. Its surface
nodes and weights are

```text
x_inner = sqrt((3 - 2 sqrt(6/5))/7),
x_outer = sqrt((3 + 2 sqrt(6/5))/7),
w_inner = (18 + sqrt(30))/36,
w_outer = (18 - sqrt(30))/36,
```

with both signs for each node. The thickness `G3` rule is the one above.
Generalized-section energy uses `G3 x G3` primarily and `G4 x G4` for
sensitivity.

Both rules independently execute every categorical and physical gate. Any
rank, nullspace, coercivity, sign, locking, patch, or convergence
classification drift is `UNCLASSIFIED_CANDIDATE_B`; neither rule may be
selected after seeing results. The literal base without Eq. 21 is also
reported under both rules so that quadrature effects cannot be attributed to
`H_D` mechanics.

## 6. Exact flat-element theorem and frozen expectation

For a flat, affine element with uniform director, restrict the nodal rotations
to four scalar drill coordinates. The cyclic oriented edge-difference map has
rank three and its kernel is the constant drill.

Each nondegenerate `d_I` is nonzero, and `h_I=1` while the other three midside
functions vanish at edge midpoint `I`. Consequently `H_D` is injective on the
three-dimensional edge-difference quotient. If its compatible surface
symmetric-gradient polynomial field vanished, `H_D q` would be an in-plane
rigid field. Every `h_I` vanishes at all four corners, so that rigid field must
be identically zero; hence every edge difference vanishes. The map from the
four pure-drill coordinates to the complete compatible strain polynomial field
therefore has exact rank three. Both registered positive-weight evaluation
stacks must reproduce that same rank; it is never inferred from the rank of a
single `3 x 4` point sample.

The preregistered flat expectation for `mathcal_B_B` (equivalently `K_B` under
the positive/SPD assumptions above) before gauge reduction is

```text
rank(mathcal_B_B)=rank(K_B)=17,
N=7, G=1, P=6,
R=6, R_N=6, R_G=0, RQ=6, Z=0.
```

The constant drill remains the only exact zero-mass gauge. Candidate B must
never be reported as an unconstrained rank-18 element.

The only permitted reduction removes the exact, reported one-dimensional
`G`. It has 23 retained coordinates, stiffness rank 17, and six rigid null
modes. The reduction must preserve and report exact lifts for mass, load,
state, recovery, energy, and virtual work; it is not a penalty, stabilization,
or hidden rank policy.

## 7. Preregistered gates and terminal meaning

Before any Candidate-B numerical outcome, the mechanics contract and oracle
must enforce all of the following:

1. exact symbolic equality of `B_D` to the displayed compatible surface
   gradient at corners, edge midpoints, center, primary Gauss points, and
   off-center tagged-rational points;
2. byte- and value-level immutability of the Eq. 25 base, bending field, and
   Eq. 20 shear field; the incremental `H_D`/`B_D` contribution to rows 4-5 is
   exactly zero and the final rows equal literal `B_20`;
3. Eq. 21 activation count zero inside Candidate B and exactly one `H_D`
   contribution;
4. the same `H_D` in strain provenance and mass, with `H_D G=0` and
   `B_D G=0` exactly;
5. no material coefficient beyond the existing physical constitutive tensor,
   and no penalty, `C^T C`, Cosserat, couple-stress, mesh, thickness,
   shear-modulus, or empirical scale;
6. symmetry, PSD, first/second variation, virtual work, rigid, frame, origin,
   scale, cyclic, and reversal covariance;
7. exact or outward-interval pure-drill rank three, full rank 17, and the
   displayed quotient tuple at every frozen precision and sensitivity point;
8. positive lower-bound coercivity of the inherited checkerboard quotient
   relative to its positive physical mass, without an absolute tuned floor;
9. exact-G-only reduction and full work/energy/mass/load/state lift
   equivalence;
10. membrane, bending, transverse-shear, distorted, warped, curved,
    noncoplanar, topology, support/MPC, coupling, activity/deletion, orphan,
    thin/thick, and refinement gates inherited without relaxation; and
11. identical categorical results under both frozen quadrature rules.

The scientific terminal is `GO_CANDIDATE_B` only when every inherited and
Candidate-B gate executes and passes. Any exact or interval-certified failure
is `NO_GO_CANDIDATE_B`. Missing evidence, execution error, nonfinite data,
unclosed interval, borderline decision, or uncured precision/multiplier/
quadrature drift is `UNCLASSIFIED_CANDIDATE_B`. No threshold, quadrature,
fixture, coefficient, or interpretation may be altered after an outcome.

Regardless of Candidate B's terminal result, the overall Stage-M state remains
`BLOCKED_PRIMARY_SOURCE_UNAVAILABLE` until Candidate A's primary-source gate is
lawfully resolved by a new content-addressed manifest amendment.

## 8. Scope boundary

This document authorizes only the registered proof artifacts. It does not
authorize production reference types, selectors, serialization, assembly,
activity, nonlinear mechanics, geometric stiffness, recovery, restart,
compiled batches, cache changes, exports, activation, integration, push,
publication, or cleanup. Those remain Stage-P work after an overall Stage-M
selection.
