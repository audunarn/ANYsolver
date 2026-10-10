# BL5 centerline work and F03 norm contract — review draft

**Status:** mathematical proposal for independent mechanics review, not an
adopted F03 metric, multiplier selection, qualification, or execution authority.
Revision 8 Section 4.2 controls the physical BL5 law. Existing registrations,
tolerances, seven ratios, growing spaces, three refinement levels, physical
transfer checks and the unconsumed formal F03 run remain unchanged.

## Decision this contract must enable

Determine whether a candidate multiplier space resolves the declared
five-channel centerline bond without missing modes or locking. Distinguish
that question from positive observation of beam variables and from
well-posedness of the signed native mixed tangent. The next numerical test
may proceed only after the physical work map, positive test norm, dual norm,
normalization and counterexamples below receive independent review.

## Exact five-channel work and released motion

At material station `s` on the **fixed reference centerline** `Gamma0`, use
reference arclength `ds0` and the plan's shell top-surface point `p_s`,
physical director `d_s`, native beam pose `(r_b,R_b)`, and fixed reference
`a_b`, `nu`, `b_1`, `b_2`. Let `g=(c_t,c_d)` with three position components
and two director components as defined in Revision 8. The constraint work is

```text
b(q,lambda) = integral_Gamma0 [lambda_t · c_t(q)
                           + lambda_d · c_d(q)] ds0.
```

`c_t` is measured in metres, `c_d` is dimensionless; density coefficients
`lambda_t` have units N/m and `lambda_d` have units N. Thus `b` has units
N m. At any admissible linearization, `C_h v` is the integrated first
variation of these five gaps and `C_h^T lambda` is the coordinate-covector
force. Multipliers are densities per unit **reference** length; an integrated
P0 row dual is its reference-interval length times the density. Reference
correspondence and measure are compiled once, not updated with stretch.
Local gradients, curvature and recovery must use
the same representation and actual finite-rotation update.

For a declared positive length `ell`, define

```text
g# = (c_t, ell*c_d),       mu = (lambda_t, lambda_d/ell).
b = integral_Gamma0 mu · g# ds0.
```

All five components of `g#` are lengths and all components of `mu` are
forces per length. This is an invertible change of units, not a new law or a
sixth rotational constraint. `ell` must be frozen from reference geometry
and justified before quotient assessment; the earlier algebraic probe's
`0.2*line_length` is only a test value, not that choice.

The local release has an exact finite-motion witness at one material station.
Hold the shell fixed and rotate the whole beam by `Q` about the attachment
point `p_s` with axis
parallel to `d_s`. Then `r_b' = p_s + Q(r_b-p_s)`, `R_b'=Q R_b` and
`Q^T d_s=d_s`; both `c_t` and `c_d` remain zero if initially zero. The
beam-axis translation is essential when the arm is eccentric. Consequently
the five-row Jacobian annihilates this tangent motion and every five-row
multiplier does zero virtual work on it. For nonzero multipliers, test the
second variation along the **actual finite-motion path**; a raw additive-chart
Hessian quadratic form need not vanish without the path-acceleration term.
The existing local test covers the finite gap witness. It does not imply that
a finite attachment has a free global rigid mode or that the signed mixed
system is stable.

The centerline bridge at commit `82960b26` checks the virgin beam-side
five-row Jacobian at 22 compiled stations. Its six-pose *primal* observation
may include normal spin, but the multiplier work remains five-channel. A
finite-width observation is admissible only as a separately justified
auxiliary beam norm or a distinct distributing-footprint law. It cannot be
used as BL5 constraint work.

## Reuse the existing independent reference norm

The earlier [M2 physical trace reference norm](B3_GE_E4_PL_M2_TRACE_NORM_CONTRACT_DEV.md)
already defines supported shell/beam auxiliary kinematic spaces, the
force-equivalent five-channel density, physical arms, and an **independent**
multiplier dual `M_ref` from the shell and beam Riesz work functionals. Its
beam surface-width average is an *auxiliary norm convention*, not a BL5
finite-width bond. Do not replace `M_ref` with `C_h H_h^-1 C_h^T` on the same
candidate: that would normalize away a missing discrete interface mode.

The prior reference contract is scoped to a straight, flat, zero-native-lift
configuration, with explicit `ell`, width, support maps and half-cell
director partition. Its later `0.43` finite-family floor is tied to those
exact spaces, dimensions, inputs and certificate route. It is not transferable
to a changed native graph or multiplier policy by assertion, and the closed
certificate campaigns remain closed. The nonuniform-P1 scalar Neumann Gram
is a useful separate algebraic/unit control; it does not replace this
independently declared physical dual.

## Trace-active inf-sup space; full mechanics stays separate

The actual BL5 local port has only nine beam columns: translations of its
two bracketing nodes and three rotations of its native half-cell. It has no
direct columns for nodal frame rotations or the 18 force-like retained
coordinates per member. The shell work likewise uses physical translation
and director variations, not an independent drilling restraint. Verify
these zero-column statements on each assembled candidate and chart; do not
infer them merely from variable names.

The present implementation supplies a source-level check for an *isolated*
BL5 row block: `NativeHalfCellPort.active_beam_slots()` returns the six
bracketing translation and three cell-rotation coordinates; reference
assembly scatters only the resulting 21 local slots; finite assembly reuses
those slots and applies its chart map only to shell rotations. Its current
fixed supports select individual coordinates, so they do not mix active and
inactive beam fields. This does not prove a future combined-attachment row
block or an affine support map has the same split. The actual assembled
formal candidate still needs its checked row/column identity before an F03
quotient.
The flat Q4 P0/discontinuous-P1 all-column physical-work checks pass 2/2.
The same independently derived station variation passes 4/4 new checks on
mixed Q4/S3 and all-S3 edge hosts. These checks reuse product quadrature and
multiplier interpolation, which remain separate checks. They do not establish
finite-chart, general-topology or support-map equivalence.

Therefore build the interface inf-sup `H_h` by **restricting the existing
supported `h_S+h_B` kinematic reference forms to the actual shell and beam
physical interpolation spaces**. Retain all supported bulk shell
translation/director fields, including off-line nodes; on the beam retain
continuous axis translations and independent half-cell directors. Only
algebraic resultants and native nodal-frame variables absent from BL5 work
may be omitted from this interface kinematic space. Use the declared
physical surface arms, reference boundary conditions, auxiliary width and
fixed `ell`. Its quadratic has squared-displacement units.

The flat Q4/S3 shell-side restriction now has a bounded implementation and
[source controls](../../.development/f03-mixed-shell-h1-20261008-v3/results.md).
At each flat +Z shell node the five auxiliary coordinates are `(u,eta)`;
the actual E4 rotation variation is `omega=(-eta_y,eta_x,0)`, so
`omega cross e_z=(eta_x,eta_y,0)`. The area-normalized Q4/S3 scalar form is
`M+ell² G`, used for each translation and multiplied by `ell²` for each
director component. Root coordinate-selection supports remove the mapped
fields, but direct zero BL5 work at off-line shell nodes does not permit
deleting them: the supported H1 Gram has nonzero on/off-line coupling.
This verifies a necessary flat shell restriction only. It does not specify
the complete beam-plus-shell operator, affine/curved supports, independent
dual, numerical floor or signed mechanical stability, and cannot consume
formal F03 authority or transfer the previous `0.43` floor.
The next bounded [actual-owner bridge](../../.development/f03-actual-primal-work-20261008-v3/results.md)
now combines that shell restriction with the original continuous-translation,
cell-director beam form. For flat straight zero-lift Q4, mixed Q4/S3 and
all-S3 fixtures with coordinate-selection supports, it takes the beam arm
from compiled BL5 stations and verifies the complete embedded `C E` virtual
work. It refuses omitted supported-free coordinates carrying work. This
bridge uses compiled owner ordering and full native half-cell coverage;
equivalent input reordering is checked by congruence rather than entrywise.
The [first failed order comparison](../../.development/f03-actual-primal-work-20261008-v2/results.md)
is preserved. This
closes the finite-fixture kinematic mapping question only; it does not supply
the independent multiplier dual or extend the contract to curved/affine maps.
The independently enriched reference dual `M_ref` stays independent of the
candidate trace and has squared-force units. With actual five-channel work
matrix `B_h`, the dimensionless positive assessment is

```text
B_h H_h^-1 B_h^T z = beta_h^2 M_ref z.
```

The [flat P0 actual-owner dual bridge](../../.development/f03-actual-mref-20261008-v2/results.md)
now integrates all physical force/couple-density basis actions independently
of candidate `C`, converts the two director multipliers by the frozen `ell`,
and verifies agreement with `-(C E)^T lambda` on Q4, mixed Q4/S3 and all-S3
owners. Its reference Riesz actions use separately refined Q4 shell and
continuous beam/cell-director spaces, with explicit root-only support
admission. The bounded 1/2/4 nested levels are positive but do not yet
provide a certified error majorant or candidate-independent acceptance floor.
This check is P0-only and cannot be silently used for P1 or dual spaces.

The subsequent [P0 continuous-dual bracket](../../.development/f03-actual-mref-20261008-v3/results.md)
applies the existing modal-shell and equilibrated-beam majorants to every
force-equivalent density column of this root-supported fixture. It verifies
the registered `M_upper <= (1+1e-3) M` reference budget in binary64 and
encloses the three-level refined auxiliary dual. It still needs a
different-family mechanics review before formal use; neither the
historical floor nor multiplier-space acceptance follows from it.
The [exact-value report](../../.development/f03-actual-mref-20261008-v4/results.md)
records a `6.050952616809546e-05` relative bound for the small mixed
fixture. A separate [16×4 Q4/P0 actual-owner check](../../.development/f03-actual-mref-20261008-v6/results.md)
matches all 40 physical density rows of one registered scalar-family entry.
These observations support that entry's action identity, not transfer of
its family-wide `0.43` floor to mixed meshes or unverified ratios. Further
isolated refinement of the 4×1 comparator is not the next discriminator.
The [registered-entry norm check](../../.development/f03-actual-mref-20261008-v7/results.md)
also verifies the actual 16×4 Q4 shell Gram is congruent to the saved
tensor-product scalar shell Gram under the exact supported-node/field
permutation. This binds one entry's positive norm as well as its work map;
the full family and signed physical system remain separate obligations.
[V9](../../.development/f03-actual-mref-20261008-v9/results.md) also checks
the complete beam Gram and excludes a missing interior Q4 or overlapping S3
partition before the rectangular continuous dual is used. The original V8
syntax failure is preserved. A same-family read-only review supplied these
adversarial findings; it does not satisfy the required different-family review.

The historical [c2 native 21-case family](development/r8-bl5-native-stability-20260930/results.md)
already covers the seven native half-cell:shell-segment ratios at 16×4,
32×8 and 64×16 with the same `span=max(1,ceil(2*halfcells/nx))` P0 rule.
Its installed artifact and positive-quotient sources remain frozen. The
current [seven-ratio actual-owner bridge](development/r8-f03-actual-family-20261009/results.md)
tests work, norm and reference on 16×4 only; reuse of the historical
three-level values requires relevant source/reference identity reconciliation,
not a fresh positive-family campaign by default. The separate projected
whole-member 21-case series uses a different ratio convention and support
rule and cannot supply missing c2 entries. Neither historical series proves
the signed native KKT, physical transfer or this draft's adoption.

The later [seven-ratio development screen](development/r8-f03-actual-family-20261009/results.md)
checks this work/norm/reference construction at one 16×4 Q4 shell resolution
for native half-cell counts 2–128. All seven entries pass the unchanged
`1e-3` continuous-dual budget after prospectively fixing at most 2048 beam
auxiliary segments for this screen; the 128-half-cell entry uses 16 rather than
32 subdivisions to keep its original-matrix inverse residual below the
unchanged `1e-10` requirement. The 128/32 failure and intervening numerical
diagnostics remain preserved. This is one mesh level, not a family floor or
complete uniform-stability argument. The shell/beam norm constructors are
shared with the declared auxiliary model, so their parity is a coordinate
embedding check, not an independent mechanical validation. Different-family
review, three levels, physical transfer and signed-KKT checks remain open.

Use sparse positive solves, physical row-density conversion, a justified
multiplier quotient, and the registered floors/controls only for matching
identities. A block-diagonal positive extension on inactive native variables
leaves this inf-sup unchanged only when the supported space also splits into
active and inactive parts. If supports or the norm couple those parts, the
effective active norm is a Schur complement; zero direct `B_h` columns alone
do not justify deleting them. Such an extension must not be used to claim
physical stability. The **full signed retained
KKT**, including nodal frames, force-like coordinates, constraint curvature,
kernel behavior, locking and equilibrium, is assessed separately. No
stationary reduction or invented SPD mechanical tangent is implied.

The earlier full-native graph is not adopted for this prospective assessment.
The old `h_B` admits independent cell-constant directors in L2. A DG jump
penalty for alternating directors grows like `h^-2` relative to it. Removing
those rows retains finite-fixture ranks `51/78/150`, but a three-level check
of the physically scaled virgin compatibility-energy term still raises the
graph/reference ratio `3.878 -> 6.832 -> 18.647` at 4/8/16 half-cells,
while its no-jump trace/reference ratio is `1.0` on this witness. Thus the
full-native energy graph is **not adopted as the F03 primal norm**; rank alone
misled that route. The finite ratios are adverse comparability evidence,
not a proof that no uniform bound exists or that this is the only valid norm.
They establish no universal asymptotic rate or formulation failure. Preserve
[no-jump rank](../../.development/bl5-centerline-no-jump-20261008-v1/results.md)
and [weak-director comparison](../../.development/bl5-cell-director-norm-20261008-v1/results.md).

Before formal F03, independently review the restriction of `h_B+h_S` to
actual Q4/S3 and native trace bases, including the full reference arm/lift,
support maps, off-line shell fields, boundary terms and any nullspace. The
older `0.43` finite-family floor is not transferred to changed spaces or
policies by assertion. The existing same-family numerical reviews are
supporting only; required different-family mechanics acceptance remains open.

### Analytically calibrated scalar method controls

The prospective quotient implementation has one exact negative and one
positive control independent of the BL5 element. On `[0,1]`, take the primal
space `H^1_0`, the seminorm `h(v,v)=int |v'|^2 dx`, continuous-P1 trial traces
with both ends fixed, and P0 density functions over `N` uniform cells of
length `a=1/N`, with even `N`. The work row is the exact cell integral
`b(v,lambda)=int lambda*v dx`. This deliberately supported scalar boundary
case is a numerical-method control, not the native root-supported owner.

For the **nonzero physical density** `lambda_i=(-1)^i`, adjacent cell
contributions cancel at every interior P1 hat: `B^T lambda=0`. The
independent continuous dual is positive. The primitive of `lambda` alternates
between zero and `a`. Because `-u''=lambda` and both endpoints are fixed,
`u'=mean(P)-P`, where `P(x)=int_0^x lambda`; its mean `a/2` minus the
primitive gives the Riesz derivative. Hence `||lambda||_(H^-1)^2=a^2/12`.
The quotient is exactly zero for this physically nonzero checkerboard,
rather than a duplicate-basis coefficient
nullity. Two-point cell quadrature independently reproduces the reference
dual in the [bounded scalar controls](../../tests/test_r8_bl5_scalar_checkerboard_control.py).

For the constant density `lambda_i=1`, the continuous dual is `1/12`, while
the P1 discrete dual is `(1-a^2)/12`; the quotient is `sqrt(1-a^2)` and
approaches one on refinement. The same controls verify this smooth benchmark
at `N=4,8,16` with sparse positive solves. [V1 and V2 receipts](development/r8-f03-scalar-checkerboard-20261009/results.md) preserve the
source-only checks and exact budget use. Neither result supplies a BL5
threshold, reference majorant, numerical floor, mixed-mesh stability or
signed-KKT acceptance. The scalar controls are necessary implementation
counterexamples after the actual physical `H_h` and `M_ref` receive review.

## Required counterexamples and separate acceptance checks

- A pure released normal spin about the eccentric attachment point must
  produce zero five-row work; an incorrect fixed beam-axis spin must not be
  used as its surrogate.
- The supported single-span-2 P0 fixture has a free native beam yaw and its
  owner correctly refuses a solve. A positive auxiliary graph norm observing
  that yaw cannot turn this refusal into a stability pass.
- A longitudinal gap invisible to a coarse multiplier space must be detected
  when that space is enriched; a physical deformation intentionally allowed
  by the continuous BL5 law must not be relabelled a discrete failure.
- Reject duplicate multiplier basis functions as a representation-integrity
  error: their coefficient difference represents zero physical density, so
  both work and the physical dual norm vanish. It is not a valid zero-beta
  witness. The analytic scalar checkerboard and smooth controls above now
  exercise this distinction for the method; an actual BL5 candidate must
  still be checked against the independently reviewed physical dual.
- Equivalent metre/millimetre and retained-basis transformations must keep
  physical work and the nondimensional quotient invariant, including actual
  recompiled section/support data rather than only an algebraic rescaling.
- Weak-direction inverse accuracy must be checked in addition to backward
  residual. The factored finite-fixture sample had `2.31e-6` forward error.
- Assess the signed constrained native KKT, kernel behavior, physical
  equilibrium/work, shear/drilling freedom, transfer, locking and convergence
  separately. A positive graph quotient or row rank alone is insufficient.

**Review outcome required:** accept a fully specified `H_h`, `M_h`, physical
scales, numerical floor and refinement criterion, or identify the obstructing
equation/counterexample. Until then, no further quotient or formal F03
assessment is justified; G0B/G1/M2 remain open.
