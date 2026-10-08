# D1 interior pressure stability — proposed assessment specification

**29 September 2026. Status: revised development specification for independent
mechanics review; a corrected smooth-pose family passed exploratory checks,
but no claim-bearing result is frozen.** This
document does not freeze a claim-bearing run, accept the current pressure
space, or regrade the retained cut-front failure. It sharpens the earlier
[review brief](D1_INTERIOR_PRESSURE_GATE_REVIEW_BRIEF_20260929.md) using the
working deformable-target fixture and corrects the objections to [draft v2](D1_INTERIOR_PRESSURE_GATE_CANDIDATE_V2_20260929.md).
Independent review of the corrected finite operator, norm, transport and
criterion is required before formal inputs are frozen.

## Intended claim and exclusion

The claim is only for the D1-interior planar, small-rotation Q4 source / S3
deformable target: each source face with positive projected overlap is
wholly covered by the target *surface union* (a zero-overlap face is allowed),
no physical source-rim contact, no active pressure at a source node whose
physical normal motion is prescribed, positive reference support for every
included pressure hat, and the admitted material/geometry settings. Signed
linear combinations of all **interior** fine-Q1 source pressure hats are
tested; checking only the currently positive coefficients would miss nearby
active-set directions. Target material is five times the source modulus but
is deformable and contributes to the complete structural energy and
two-body contact work map.

This finite family does not claim stability for arbitrary positive cuts,
prescribed-normal source boundaries, a target physical rim, warped Q4,
general finite rotations or every mesh sequence. The corrected
[two-hat positive-cut counterexample](d1_cut_front_two_hat_counterexample_20260929.md)
remains failed for the broader pressure pairing and belongs to D2.

## Proposed fixed family and pose

Use source `4×4`, `8×8`, `12×12` uniform Q4 grids on the same physical
`[0.1,1.1]² m` patch. The candidate uses one kinematically admissible
deformable-target press pose sampled on these source grids by a fixed
physical formula. Each fixture has a `4×4` cell / 32 S3-face
target with lower physical edge `y=−0.113 m`, upper edge `y=1.2 m`, full
left edge structurally clamped, and five-times source Young's modulus.
Source perimeter support, `10⁻⁴` common reference slope, 0.05 m shell
thickness, physical skins, target `x` anchoring, fine nodal Q1 pressure and
the same integration controls apply at every level. This is a finite
operator check at declared poses, **not three accepted equilibrium solves**.

The proposed transport is one fixed smooth physical field sampled on each
mesh. With source coordinates `ξ=x−0.1`, `η=y−0.1`, set source `uz` in
metres to `−55×10⁻⁶ sin(πξ) sin(πη)` and all other source DOFs to zero.
With target coordinates `a=x/1.3`, `b=(y+0.113)/1.313`, set target
`uz` to `5×10⁻⁶ a sin(πb)` and all other target DOFs to zero. The target
left clamp and both target `ux` path anchors are exactly respected. The
target is structurally deformable, has nonzero displacement, and its
authoritative DOFs remain in the contact gap/work map. This is a declared
candidate pose, not an accepted nonlinear equilibrium.

The accepted `12×12/4×4` development pose used the earlier `y=−0.1 m`
target and demonstrates an analogous fixture, not this corrected family.
The earlier Q1 transport of that saved pose is **not** the proposed rule:
source4 had no interior compression and source8 raised a Q4 projected-
inversion error. Preserve that [failed preflight](d1_pressure_transport_preflight_20260929.json).
An initial 30 µm smooth bump removed the inversion on all three grids but
left all interior gaps open. The 55 µm amplitude above was selected from
that measured gap in development and fixed before the operator screens.
Preserve the [open-pose result](d1_pressure_analytic_preflight_20260929.json).
Preflight all three transported fixtures for admission, complete physical
coverage of every positively overlapping source face by the target union,
positive interior reference support,
smooth projection/clipping branches, correct directors and physical skins,
and meaningful interior contact at the declared pose. The latter means
an interior gap/contact load pattern relevant to the press, not a requirement
that a transported pose itself satisfy equilibrium. Check the full
constrained/path-controlled reference stiffness is symmetric positive
definite at every mesh. If any fixture is inadmissible, diagnose it in one
bounded corrective preflight before freezing; do not silently substitute
another mesh or infer success from a timeout.

The earlier **invalid** smooth pose used `a=(x−0.1)/1.2` and imposed a
nonzero `uz` on the target's clamped left edge `x=0`. The initial screen
checked path `ux` controls but missed that structural essential condition.
Its raw results are retained below solely as a diagnostic; they cannot
support a kinematically admissible pressure claim. The corrected runner
now checks the complete structural constraint transformation.

The invalid smooth pose passed the geometry preflight on all three
meshes. It had 1, 9 and 26 negative-gap interior nodes; minimum gaps were
`−6.71`, `−14.24` and `−15.77 µm`. The minimum interior reference supports
are positive, both target path controls are zero and current/reference
overlap areas are approximately `1 m²`. [Geometry preflight](d1_pressure_analytic_press_preflight_20260929.json).
The invalid-pose operator screen checked full constrained/path-controlled
reference SPD. Its diagnostic results were:

| Source grid | Interior modes | Full energy dimension | η | κ | γcert |
|---|---:|---:|---:|---:|---:|
| 4×4 | 9 | 228 | 0.999999997 | 1386.396 | 0.0007213 |
| 8×8 | 49 | 492 | 0.999999985 | 469.295 | 0.0021309 |
| 12×12 | 121 | 916 | 0.999999961 | 221.800 | 0.0045086 |

The invalid screens met the *draft* η/κ levels under the routine caps, with
9.29/23.17/32.40 seconds and peak memory 184/213/211 MB respectively.
These operator screens alone do not establish independent work-map parity
or formal acceptance. They evaluated zero trial nodal forces, so the
reported active-pressure count is zero on each mesh despite the negative
gaps. They assess the geometric pairing at deliberately non-equilibrated
poses; they do **not** assess a converged active-set tangent or a coupled
press at those three meshes. Independent review must decide whether these
screens plus the separate accepted-solve controls suffice for the stated
finite operator claim and D1 pressure disposition.
[4×4](d1_pressure_analytic4_20260929.json),
[8×8](d1_pressure_analytic8_20260929.json),
[12×12](d1_pressure_analytic12_20260929.json).

A separate independent current-skin quadrature screen on the invalid source4 pose evaluated
2,368 points without calling the production contact kernel. Its reference
support differs by at most `4.55×10⁻¹⁴` relative and normalized gaps by
`8.01×10⁻¹³ m`. For center-normal, signed-checker and smallest-singular
source motions, the `S·D(gbar)` relative L2 differences are
`1.52×10⁻⁸`, `1.60×10⁻⁸` and `1.21×10⁻⁸`. The measured
`gbar·DS` contribution is below `1×10⁻¹⁴ m²` for these three motions
in this fully covered fixture; this does not erase the distinction on
other geometries. [Independent source4 screen](d1_pressure_analytic4_independent_20260929.json).

**Corrected development screens.** Replacing the target coordinate with
`a=x/1.3` makes the pose satisfy the complete structural constraint
transformation to at most `6.8×10⁻²¹ m` in the recorded coordinate norm.
All three corrected geometries were admitted by the same current-pose
coverage and integration route; each retains a nonzero target displacement
and interior compression geometry. The pressure calculations and independent
current-skin work comparisons are:

| Source grid | Negative-gap interior nodes | η | κ | Largest of three algorithmic work errors |
|---|---:|---:|---:|---:|
| 4×4 | 1 | 0.999999997 | 1386.396 | 1.60×10⁻⁸ |
| 8×8 | 10 | 0.999999985 | 469.295 | 2.92×10⁻⁸ |
| 12×12 | 26 | 0.999999961 | 221.800 | 5.73×10⁻⁸ |

The independent support differences are at most `7.42×10⁻¹⁴`
relative over these runs. The checks used one `±10⁻⁷ m` perturbation step
per direction and completed in 11.86/30.96/55.13 seconds with peak process
memory 185/208/217 MB. The full SPD, positive mass and path-control
checks also passed. The corrected screens still use zero trial nodal
forces and do not establish accepted KKT states or a nonlinear tangent
bound. They remain auxiliary development evidence. [Corrected 4×4](d1_pressure_analytic4_corrected_20260929.json),
[8×8](d1_pressure_analytic8_corrected_20260929.json),
[12×12](d1_pressure_analytic12_corrected_20260929.json).

Preliminary independent review confirms the finite matrix inequality
for the declared SPD reference norm, and rejects using these unequilibrated
poses as the sole three-mesh D1 press stability evidence. Accepted same-family
press states or a quantitative pose/branch transfer bound remain necessary
for that broader disposition. The negative cut-front control has a different
`hmin`; its numerical γ separation cannot be attributed to the cut alone.

A later read-only screen of that earlier accepted pose evaluated all 121
signed interior pressure modes with its saved active nodal forces. It found
`η=0.99999754`, `κ=221.80035` and `γcert=0.00450854` in 34.01 s/211 MB.
This supports feasibility of the provisional levels on **one old-geometry
pose only**. A later full-space check found its 916-dimensional complete
constrained/path-controlled reference stiffness symmetric to `1.23×10⁻¹⁸`
relative and Cholesky positive, with minimum pivot `0.6902`; the pressure
measures did not change. It does not execute the transported family or
establish a current-Newton-tangent bound. The first screen used zero trial pressure and therefore
misreported zero active modes; its `η` and `κ` were unchanged, and the corrected
screen confirms two active modes. A final profile-identity check used the
saved `overlap_local_dev` certificate setting and matched its reference
support; the measures did not change. [Current screen](d1_pressure_gate_saved12_screen_v3_20260929.json),
[resource](d1_pressure_gate_saved12_screen_v3_resource_20260929.json),
[full-space SPD screen](d1_pressure_full_spd_saved12_20260929.json).

Pressure-space pairing can be checked at an admissible, declared pose
without solving nonlinear equilibrium at every mesh. The transported
source8 pose makes **no** accepted-solve claim. The actual accepted
source4/source12 presses and exact-Q1 source8 analytical workflow remain
separate equilibrium/code controls, with their different geometries and
claims stated explicitly. A new source8 coupled solve is not required for
this finite operator check. It may be required by a distinct response or
mesh-convergence gate, which this specification does not waive.

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
transformation for the transported pose; path controls restrict variations
further. Construct `Q` with one admissible motion per node in `I`, moving
that node along its **physical reference normal** in authoritative
structural coordinates. Check `Q` is full rank, satisfies every structural
constraint and has zero variation of each path control. Its source `ux`
component cannot be omitted solely because the common slope is small.

From the production weighted-gap derivative at the transported pose, including
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

`B` is the *algorithmic* nodal-force/constraint pairing at fixed nodal
force `z`: production uses `diag(S) D(gbar)` in its force map. It is
distinct from the derivative of a fixed-pressure work functional:
`D(S gbar) = diag(S) D(gbar) + diag(gbar) D(S)`. At a nonzero gap the last
term can matter. Neither this test nor its independent derivative check
may silently substitute the latter map. If a physical fixed-pressure work
claim is needed, quantify and assess that difference separately.

`Kstruct` is the contact-free symmetric **reference** elastic energy
operator of the admitted small-rotation formulation on the complete
structurally constrained and path-controlled space. Check its symmetry
and positive definiteness at every candidate pose. The inequality is
exact in that declared reference-energy norm; it is not a bound on the
possibly nonsymmetric current Newton tangent. No nonlinear tangent-norm
equivalence is claimed here. `hmin` is the minimum physical source-cell width, measured in
the same configuration used by the analytical stiffness bound. Use the
same mass, force and length units on every mesh. For each signed pressure
vector, restriction to `range(Q)` proves the complete constrained
structural-energy dual value is at least `γcert` after this normalization.
This *constructive lower bound* avoids treating a finite Gram rank as an
inf-sup certificate.

The provisional finite-family criterion is `η ≥ 0.9`, `κ ≤ 2110`, hence
`γcert ≥ 0.81/2110 ≈ 3.84×10⁻⁴` on all three transported poses. The
pairing threshold permits at most 10% loss from the ideal full-cover `B=M`
in the stated mass normalization. The `2100` analytical bound applies
only under its planar-affine source-normal assumptions; `2110` is a
prospective finite-family level, **not** a measured nonlinear tangent
margin or universal stability constant. Independent review must assess
the selected finite criterion before freeze. The earlier corrected
positive-cut control has `γ ≈ 1.58×10⁻⁴` under its own stated norm and
`hmin`; retain the corrected cut series as an excluded-family negative
discriminator, without attributing its numeric separation to the cut alone or
rerunning or regrading its historical qualification.

## Independent checks and acceptance use

At each transported mesh, check kinematic constraints and path-control
variations, full-union coverage, geometry/branch validity, reference support,
integration error and independent physical gap. Do not demand equilibrium
or complementarity from a transported pose. Confirm the exact reference
mass and `Q` mapping by independent element virtual work. Compare
representative signed pressure directions, including the computed smallest
singular vector, against an independently evaluated *algorithmic*
`S·D(gbar)` physical-skin map; use the `10⁻⁵` smooth-branch directional
tolerance over a useful step interval. Measure `gbar·DS` separately when
nonzero-gap rows make it consequential. Record branch decisions and
quadrature subdivisions. A branch change requires a one-sided/generalized
check or a different smooth pose. Coupled accepted presses retain separate
force/moment balance, complementarity, integration and independent-gap
gates under the existing D1 tolerances.

Record `η`, `κ`, `γcert`, the actual restricted dual minimum, the smallest
mode, physical pressure support, candidate active nodes, gap and branch
identity on each transported grid. Report forces and moments only for
the separate equilibrium controls. A passing finite family supports
**only this registered D1 profile and family in its stated reference norm**.
Opening/recontact and restart use their existing
separate lifecycle cases; an open pose with zero pressure cannot establish
pressure stability. Representative 2% spatial response and 0.1%
analytical/code verification remain separate gates.

Before formal execution, freeze the actual source commit, environment,
fixture files, controls, length/force/moment scales, independent reference,
error tolerances and resource caps. Preserve all formal failures. Independent
assessment must explicitly address whether the `D/hmin⁴` scaling,
full-space SPD requirement, transported poses and source-motion constructive
bound support the intended finite pressure-space claim,
given the admitted shear and bending energy and deformable target. A
negative review returns this candidate to development; it cannot be fixed
by choosing a weaker threshold after seeing the formal result.
