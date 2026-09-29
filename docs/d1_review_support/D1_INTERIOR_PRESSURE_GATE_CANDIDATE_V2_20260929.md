# D1 interior pressure stability — proposed assessment specification

**29 September 2026. Status: draft for independent mechanics review; proposed
mesh family is not yet executable at all three levels.** This
document does not freeze a claim-bearing run, accept the current pressure
space, or regrade the retained cut-front failure. It sharpens the earlier
[review brief](D1_INTERIOR_PRESSURE_GATE_REVIEW_BRIEF_20260929.md) using the
working deformable-target fixture. The independent reviewer must check the
norm, source-motion subspace, physical work map and proposed criterion before
formal inputs are frozen.

## Intended claim and exclusion

The claim is only for the D1-interior planar, small-rotation Q4 source / S3
deformable target: complete source coverage by the target *surface union*,
no physical source-rim contact, no active pressure at a source node whose
physical normal motion is prescribed, positive reference support for every
included pressure hat, and the admitted material/geometry settings. Signed
linear combinations of all **interior** fine-Q1 source pressure hats are
tested; checking only the currently positive coefficients would miss nearby
active-set directions. Target material is five times the source modulus but
is deformable and contributes to the complete equilibrium and work map.

This finite family does not claim stability for arbitrary positive cuts,
prescribed-normal source boundaries, a target physical rim, warped Q4,
general finite rotations or every mesh sequence. The corrected
[two-hat positive-cut counterexample](d1_cut_front_two_hat_counterexample_20260929.md)
remains failed for the broader pressure pairing and belongs to D2.

## Proposed fixed family and pose

Use source `4×4`, `8×8`, `12×12` uniform Q4 grids on the same physical
`[0.1,1.1]² m` patch. A corrected candidate keeps the target at `4×4`
cells / 32 S3 faces with its lower physical edge at `y=−0.113 m`, upper
edge at `y=1.2 m`, and full left edge structurally clamped and
five-times source Young's modulus. Use the same source perimeter support,
`10⁻⁴` common reference slope, 0.05 m shell thickness, physical skins,
0.04 N compact physical bump load, two force increments, prescribed target
`x` anchoring, fine nodal Q1 pressure, monolithic enforcement, existing
integration controls and `5×10⁻⁵ m` independent gap budget. No force,
mesh, penalty or solver limit is tuned after observing a formal result.

The accepted `12×12/4×4` development pose used the earlier `y=−0.1 m`
target and demonstrates an analogous fixture, not this corrected family.
Preflight all three corrected fixtures for admission, nonzero *interior*
pressure, complete coverage and resource use. If any is inadmissible,
resolve the fixture before freezing the formal runs; do not silently
substitute another mesh.

A later read-only screen of that earlier accepted pose evaluated all 121
signed interior pressure modes with its saved active nodal forces. It found
`η=0.99999754`, `κ=221.80035` and `γcert=0.00450854` in 34.01 s/211 MB.
This supports feasibility of the provisional levels on **one old-geometry
pose only**. It neither checks current-pose energy equivalence nor executes
the corrected family. The first screen used zero trial pressure and therefore
misreported zero active modes; its `η` and `κ` were unchanged, and the corrected
screen confirms two active modes. A final profile-identity check used the
saved `overlap_local_dev` certificate setting and matched its reference
support; the measures did not change. [Current screen](d1_pressure_gate_saved12_screen_v3_20260929.json),
[resource](d1_pressure_gate_saved12_screen_v3_resource_20260929.json).

**Acceleration question for review, not an adopted gate:** Pressure-space
stability is a property of the constrained discrete gap/work operator at a
pose, not of the nonlinear iteration used to reach that pose. One possible
three-mesh check would transport one smooth, physically admissible
deformable-target press geometry to source `4×4/8×8/12×12` grids, using a
fixed physical interpolation rule and the same shifted target reference
mesh. It would evaluate the complete signed interior `B`, exact `M`,
constrained `Q` and structural-energy bound at those poses without three
expensive coupled solves. The actual accepted source4/source12 presses and
the exact-Q1 source8 analytical workflow would remain separate equilibrium
controls; the transported source8 pose would make **no** accepted-solve
claim. The reviewer should decide whether this construction supports the
intended pressure-space claim, what gap/coverage and current-pose checks it
needs, and whether an additional source8 coupled solution remains necessary.
Do not substitute a transported pose into the currently proposed accepted-
pose family or freeze it without that decision. This could avoid repeating
the source8 run that exhausted the routine cap while retaining the
three-mesh pressure-space calculation.

Development preflight on 29 September at the original `y=−0.1 m` target
selected interior nodes `(12,13)` on source `4×4` and `(40)` on source
`8×8`, with independent gaps `−45.12` and `−26.20 µm`. The original
`4×4` coupled route completed in 83.88 s/355 MB, selecting the same two
nodes with no rim pressure and gap `−45.11 µm`; it differs from the
small-motion oracle force by `2.49×10⁻⁵` relative. The original `8×8`
coupled route rejected an exact clipping-boundary vertex; the existing
artificial-edge tie rule also rejected. The target/source Cartesian grids
have an exact diagonal coincidence at source `x+y=1.2 m`. Shifting the
target lower edge to `−0.113 m` preserves one interior oracle active node
and predicts gap `−26.15 µm`, but the shifted coupled route hit its
180 s/1 GB *routine* time limit without a mechanics result. This timeout
neither passes nor fails the contact method. **None of the three corrected
fixtures is yet a frozen assessment result, and the corrected family must
be preflighted after mechanics review before registration.** [Original
source4 comparison](d1_pressure_family_source4_coupled_compare_20260929.json),
[original source8 rejection](d1_pressure_family_source8_coupled_preflight_20260929.json),
[shifted source8 oracle](d1_pressure_family_shifted_source8_oracle_20260929.json),
[bounded shifted timeout](d1_pressure_family_shifted_source8_coupled_20260929_resource.json).

## Pressure and structural measures

Let `I` contain every source pressure node strictly interior to the physical
source perimeter. Let `M` be the exact reference-area Q1 mass matrix on the
whole source patch, restricted to `I`. Check positive definiteness and
reference support independently. Let `T` be the exact structural constraint
transformation for the accepted pose; path controls restrict variations
further. Construct `Q` with one admissible motion per node in `I`, moving
that node along its **physical reference normal** in authoritative
structural coordinates. Check `Q` is full rank, satisfies every structural
constraint and has zero variation of each path control. Its source `ux`
component cannot be omitted solely because the common slope is small.

From the production weighted-gap derivative at the accepted pose, including
the moving projection, target deformation, shell director and reference
support conventions, form

```
B = diag(S_I) D(gbar_I) Q
K = Qᵀ Kstruct Q
A = M⁻¹ᐟ² B M⁻¹ᐟ²
L = M⁻¹ᐟ² K M⁻¹ᐟ²
η = σmin(A)
κ = λmax(L) hmin⁴/D,   D = Et³/[12(1−ν²)]
γcert = η²/κ
```

`Kstruct` is proposed as the contact-free symmetric **reference** elastic
energy operator of the admitted small-rotation formulation. The resulting
inequality is exact in that declared reference-energy norm; it is not by
itself a bound on the possibly nonsymmetric current Newton tangent. Review
must determine whether a measured or derived current-pose norm-equivalence
check is needed for the intended nonlinear claim, and define that check
before formal execution. `hmin` is the minimum physical source-cell width, measured in
the same configuration used by the analytical stiffness bound. Use the
same mass, force and length units on every mesh. For each signed pressure
vector, restriction to `range(Q)` proves the complete constrained
structural-energy dual value is at least `γcert` after this normalization.
This *constructive lower bound* avoids treating a finite Gram rank as an
inf-sup certificate.

The provisional proposed gate is `η ≥ 0.9`, `κ ≤ 2110`, hence
`γcert ≥ 0.81/2110 ≈ 3.84×10⁻⁴` on all three accepted press poses. The
work threshold permits at most 10% loss from the ideal full-cover `B=M`;
the stiffness threshold permits a separately verified nonlinear margin
above the 2100 analytical planar-affine Q4 source-normal bound. **Review
must decide whether that margin is valid.** The earlier corrected
positive-cut control has `γ ≈ 1.58×10⁻⁴` under the same stated norm and
scale; retain it as an excluded-family negative discriminator, without
rerunning or regrading its historical qualification.

## Independent checks and acceptance use

At each mesh and final press pose, check source and target force/moment
balance, complementarity, integration error and independent physical gap
under the existing D1 tolerances. Confirm the exact reference mass and
`Q` mapping by independent element virtual work. Compare representative
pressure directions, including the computed smallest singular vector,
against an independently evaluated physical-skin virtual-work derivative;
use the `10⁻⁵` smooth-branch directional tolerance over a useful step
interval. Record branch decisions and quadrature subdivisions. A branch
change requires a one-sided/generalized check or a different smooth pose.

Record `η`, `κ`, `γcert`, the actual restricted dual minimum, the smallest
mode, physical pressure support, active nodes, forces, moments and gap on
each grid. A passing finite family supports **only this registered D1
profile and family**. Opening/recontact and restart use their existing
separate lifecycle cases; an open pose with zero pressure cannot establish
pressure stability. Representative 2% spatial response and 0.1%
analytical/code verification remain separate gates.

Before formal execution, freeze the actual source commit, environment,
fixture files, controls, length/force/moment scales, independent reference,
error tolerances and resource caps. Preserve all formal failures. Independent
assessment must explicitly address whether the `D/hmin⁴` scaling and the
source-only constructive bound support the intended pressure-space claim,
given the admitted shear and bending energy and deformable target. A
negative review returns this candidate to development; it cannot be fixed
by choosing a weaker threshold after seeing the formal result.
