# D1 interior pressure pairing — finite candidate specification

**29 September 2026. Development-informed proposal; not frozen or accepted.**
This replaces v3's proposed family. It retains the selected pressure law,
all historical failures and the goal's numerical criteria. A finite result
in a declared reference-energy norm does not imply stability for arbitrary
meshes, configurations or the current nonlinear Newton tangent.

## Family and actual work map

Use the accepted two-step 0.04 N development presses on 4×4, 6×6 and 12×12
uniform Q4 source meshes, each with the same 4×4-cell/32-S3 deformable target.
Source reference patch is [0.1,1.1]² m; the target lower edge is y=−0.1 m.
Perimeter source support, full target left clamp, fixed physical bump load,
common reference slope 10⁻⁴, thickness 0.05 m, source E=10⁵ Pa, ν=0.3,
target E multiplier 5, target ux path anchors, physical skins, fine Q1
pressure, monolithic enforcement and `overlap_local_dev` are unchanged.
These are actual accepted development states; every formal run still needs
prospective source/settings binding and the completed certificate correction.

The signed interior pressure space includes every physical interior Q1
node (9/25/121), regardless of current active count (2/1/2). Do not remove
small supported modes. Check reference support, complete target-union coverage,
physical boundary admission, constraints and path controls.

The registered algorithmic pairing is **B=diag(S) D(gbar) Q**, where S is
reference support. It is distinct from D(S gbar) by gbar DS at nonzero gaps.
Q maps interior source normal translations into authoritative coordinates,
including the reference normal's ux component; it lies in the complete
structural/path-control constraint space. Target coordinates remain in the
complete constrained energy and physical contact map. Q is a constructive
subspace, rather than the complete set of physical motions.

## Norm and finite inequality

M is the exact reference Q1 mass restricted to interior pressure nodes;
R=M⁻¹ᐟ² is its symmetric positive inverse root. K is the restriction of the
same positive reference structural energy to Q, while the **complete**
structural/path-controlled reference energy must independently pass symmetry
and Cholesky checks. Define A=R B R and L=R K R.

For every signed interior pressure coefficient vector, restricting the
admissible displacement supremum to Q gives the constructive lower bound
λmin(A L⁻¹ Aᵀ) ≥ σmin(A)²/λmax(L). Let η=σmin(A),
κ=λmax(L) hmin⁴/D and γ=η²/κ, with
D=E t³/[12(1−ν²)] and hmin the source cell width. The proposed finite levels
are η≥0.9 and κ≤2110. They were informed by development; they are not
retrospective qualification of the saved runs.

Independently verify M using tensor-product 1D mass integration, Q rank and
constraints, and the actual restricted dual minimum. Compare the algorithmic
map to independently clipped current-skin quadrature in centre, signed
checker and smallest-singular-vector directions at 10⁻⁷ and 3×10⁻⁷ m.
Hold smooth clipping/projection branches fixed. Use the existing 10⁻⁵
directional target; exact mass and support algebra checks use 10⁻¹¹ relative.
Report gbar DS separately and retain gap differences; map parity alone is
not a coupled equilibrium or physical penetration check.

## Development result and remaining check

| Source mesh | η | κ | Actual restricted γ | Maximum independent map error |
|---|---:|---:|---:|---:|
| 4×4 | 0.9999998113 | 1386.39610 | 0.00072129458 | 3.75×10⁻⁷ |
| 6×6 | 0.9999995281 | 767.92889 | 0.00130220395 | 7.79×10⁻⁷ |
| 12×12 | 0.9999975410 | 221.80035 | 0.00450855951 | 3.78×10⁻⁶ |

[4-mesh record](d1_pressure_saved4_independent_v4_20260929.json),
[6-mesh record](d1_pressure_saved6_independent_v4_20260929.json),
[12-mesh record](d1_pressure_saved12_independent_v4_20260929.json).
All complete reference energies were positive; mass errors were ≤5.82×10⁻¹⁶.
Runs took 15/22/55 s with peak process-tree memory ≤225 MB under 180 s/1 GB.
The helper subsequently gained explicit saved-pose constraint and parity
dispositions; retain these raw records with their earlier helper identity.
Early read-only scrutiny confirmed the finite proof and identified those
helper fixes. Human/scientific acceptance remains a separate obligation.

Before freezing, add one same-profile accepted opening/recontact cycle on a
representative mesh, with physical separation/zero open pressure, equilibrium,
complementarity, independent gaps, balance and deterministic restart. Evaluate
the full signed-space pressure screen at accepted recontact. Active-set changes
alone leave the geometric map intact; clipping/projection/support events need
one-sided or generalized independent map checks on the admitted sides.
Three full lifecycle repetitions are not required for this finite claim.

The representative 4/4 whole-clamp-edge cycle now completes all eight steps
in 232.78 s/376 MB. All eight independent physical-gap, equilibrium,
complementarity and contact-wrench checks pass locally; opening has zero
pressure. Recontact gives η=0.9999998300 and κ=1386.39610, positive complete
reference energy and independent map error below 10⁻⁵. The open checkpoint
continued to exactly equal saved displacement, pressure, wrench, gap and
generalized reaction. [Cycle](d1_pressure_family4_moving_edge_cycle_v4_20260929.json),
[independent checks](d1_pressure_family4_cycle_independent_v5_20260929.json),
[recontact screen](d1_pressure_family4_recontact_screen_v5_20260929.json),
[split comparison](d1_pressure_family4_split_compare_v6_20260929.json).
The corrected swept strategy now has restart revision `affine_union_outward_v1`;
unversioned checkpoints reject. The previous two-corner moving/fixed-edge
fixture failed and remains retained; this is a prospective fixture correction.
These are development results before final source/criterion freeze.

## Preserved exclusions and failures

The shifted-target 8×8 attempt and its single eight-inverse-update corrective
experiment both stopped at pair-197 projected inversion in the second force
step (602/680 s). That source change was reverted. The original-target 6×6
alternative completed both steps in 255 s/381 MB. This prospectively changes
an unfrozen intermediate mesh; it does not regrade an old result.
The invalid target-clamp field, open transports and corrected nonequilibrium
4/8/12 auxiliary screens remain in [v3](D1_INTERIOR_PRESSURE_GATE_CANDIDATE_V3_20260929.md).
The historical positive-cut pressure failure remains failed and belongs to D2.
Its different hmin prevents attributing a scaled numerical difference solely
to the cut. Preserve its exact mechanics and failure interpretation.

An independent same-normalization discriminator now uses the retained touching
θ=0.1/0.05/0.025 cases without a coupled replay. Full-reference normalized
overlap η is 8.1884e−4/1.1072e−4/1.4609e−5; the actual constrained-source
witness response is 8.7867e−4/1.1936e−4/1.5771e−5, compared with 1 at full
cover. All 15 historical pressure hats are retained, including six nonzero
witness coefficients; clamped source work is exactly zero. Distinguish 15
geometric hats from 12 admissible source motions. This demonstrates the
constructive metric's response to the retained cut loss; it does not prove
full-system instability from this subspace or compare γ across different
constraints and physical rims. [Independent algebra and input identities](d1_cut_eta_discriminator_20260929.json).

Freeze final inputs, source/environment, geometric tolerances, norm/scales,
references, uncertainty, repetition/resource budget and disposition before
claim-bearing execution. No run authority is renewed by this proposal.
