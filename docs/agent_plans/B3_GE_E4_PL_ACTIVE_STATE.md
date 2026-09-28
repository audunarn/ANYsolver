# B3-GE / E4-PL / B2 active state

Updated 28 September 2026 under Revision 7 and
`ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1`. The complete earlier record
is preserved at commit `a52042d1`. The
[complete programme](B3_GE_E4_PL_B2_COMPLETE_PROGRAMME.md), frozen
registrations, historical failures, and versioned evidence retain authority.

## Decision and gates

Deliver the experimental multi-element GE and B2 workflows while resolving the
native six-channel line law and growing multiplier space. **G0B/F03 remain open;
G1 acceptance and production qualification are barred.** None of F01–F13 is
fully accepted. Formal F03 execution authority is unconsumed. A/B are development
spaces, not selected policy. The dirty factor-4 Fy fallback is outside this
slice; do not edit or run it by default.

## Delivered experimental behavior

- The sparse GE owner solves multi-Q4/S3/native-B3 point panels with retained
  variables, atomic elastic stepping, recovery, and restart. A replaceable L1
  operator works on a bounded matching line, not qualified nonmatching lines.
- The separate physical B2 profile batches 1/10/100 cases with selected
  recovery and eligible factorization reuse. Physical range, attachments,
  mass/prestress, and scale remain open; historical B2 is unchanged.
- ANYfem has a separate experimental save/reopen consumer. The installed
  solver/consumer milestone and review are in
  `.qualification/b3-ge-e4-pl/r7-combined-integration-dev-20260928-v1/`.

## Connection facts and uncertainty

A separate finite-support flat-Q4 shell-pose prototype has exact box-window
centroid/covariance weights, objective rigid-motion recovery, a bounded
endpoint-witness screen, and first variations through actual shell/native
updates. Seven focused patch checks pass, including six-channel work,
physical pure torque without drilling, vertical transfer with director
freedom, and positive physical-only compliance on one patch. Independent
read-only review found no bounded factory or derivative defect. This is a
line-indexed 2D
distributing-footprint candidate, not a selected bonded line or a uniform
physical-core work proof.

The unsmoothed zero-width L1 normal-spin law includes shell-line endpoint
point evaluations and is unbounded on the continuum shell H1 energy space.
The physical-width rail is a **separate finite connection law**: Q4 E4-PL does
not expose a unique finite interior physical director field. Virgin first-order
Q4 top/frame variations match the owner's shape gradients and Mindlin signs.
At 35/70 mm thickness, point pure Mx/My/Mz and mixed wrenches balance,
include the native beam arm, do no shell drilling work, and excite supported
physical Q4 compliance. Point yaw-slope evaluation remains unbounded on H1;
these local checks do not qualify a line law.

A bounded material rail assembles two Gauss stations per segment with
fixed reference arclength weights and finite-dimensional sampled six-component
densities. Constant yaw density cancels interior shared-node shell work. Pure
moment and mixed densities produce the declared integrated shell/native wrench,
zero resultant and drilling work, and supported physical-only shell compliance.
Same-parent gradients and Hessians follow the actual native update. A
finite P0/P1 six-channel density basis gives owned coefficients,
exact piecewise-polynomial L2 Gram, and coefficient-conjugate projected gaps.
Four-segment tests check shared-node work cancellation, independently derived
growing density Gram, and positive supported E4 physical-only compliance; they
do not establish growing-space stability.
The virgin joint covector now maps to a spatial force and shell-rail moment
including the eccentric lever arm. A four-station physical-wrench quadrature
Gram uses frozen force/length scales; station-map equality alone does not
prove whole-segment constancy. Twenty-four focused checks pass. Independent
read-only reviews found no bounded discrete measure, scatter, or basis algebra
defect. Gauss exactness
applies to density products, not generally to nonlinear density-gap work.
**Generic L2 densities have no point values.** This raw coordinate-density
Gram is distinct from the new physical quadrature Gram. Whole-segment map
constancy or bounded integration error, curved-line transport, growing-space
stability, and full physical assessment remain.

A bare native B3 broken-half-cell L2 screen at 4/8/16 half-cells produced
upper quotients 9.260/9.222/9.213 × 10⁻⁶ J⁻¹. This finite-grid diagnostic
neither proves a uniform trace bound nor selects A/B. Its raw evidence is in
`.qualification/b3-ge-e4-pl/r7-f03-native-broken-l2-dev-20260928-v3/`.
The actual virgin retained Jacobian matches independent half-cell difference,
shear and nodal/cell spin rows on the same three bounded meshes. Those rows
give a mesh-independent broken-pose L2 estimate conditional on a local
energy lower bound. For the affine-straight virgin **constant diagonal
generalized section**, the cell's constant-force and linear-moment compliance gives
exact local energy ratios 1, 2 and 6 against that canonical strain norm,
independent of affine element length. The assembled 4/8/16 checks reproduce
the closed form to about 1e-16 relative matrix error. Independent mechanics
review confirmed that derivation and its Loewner extension to constant coupled
SPD generalized sections; a bounded coupled-section check passes. Curved or
non-affine references, fibres and loaded plastic states remain outside it.
This does not close F03.
Exact coarse-to-fine action transport is not an energy isometry, and three
reference levels do not bound the unseen same-law compliance tail. Historical
F5/S4 comparisons cannot allocate the physical difference to this connection.
The [F03 draft](B3_GE_E4_PL_G0_F03_PROSPECTIVE_ASSESSMENT_DRAFT.md) records
those limits and the mathematical obstruction.

## Next discriminating action

The physical-only Q4 block **does not uniformly control growing P0 yaw
density work on the tested longitudinal-only refinement family**. That
family holds two transverse cells fixed while longitudinal cells shrink;
the rectangles become increasingly anisotropic. Independent review derived
a mode:
nodal lateral pattern (1,-1,1) has zero mean shear on each cell but nonzero
mean over the fixed central rail strip. Alternating longitudinal amplitude h
and matching P0 yaw density give constant work 0.25 while physical energy
quarters for h=.25,.125,.0625. The actual E4 operator reproduces energies
6.579e9, 1.645e9, 4.112e8 J; drilling load and virgin gap are zero. The
negative executable check and raw logs are in
`.qualification/b3-ge-e4-pl/r7-f03-growing-rail-dev-20260928-v1/`.
PL numerical completion can penalize in-plane curl but is not physical shear;
the drill-only hourglass term does no work on this mode. Positive compliance
on one fixed grid did not establish a uniform bound.
The targeted twice-long P0 yaw support also retains this anisotropic family: on 4/8 fine
cells, physical energy 8.224e8/2.056e8 J and work 0.125. Thus a fixed
two-cell macro P0 support does not by itself cure continuity on that family.
Independent mechanics review confirmed the asymptotic witness and
its narrow implication. Its raw log is beside the first counterexample.
Even constant yaw density has a free-end witness: localizing the same
lateral pattern to the last shell cell keeps work 0.5 and fixed density
norm while physical energy halves at each refinement (5.263e10,
2.632e10, 1.316e10 J at h=.25,.125,.0625). Independent review confirms
the endpoint derivation. The executable check and raw log are retained
with the other negative cases.

The previous decision to abandon P0 yaw for all refinements was too broad.
The previous provisional classical comparison paired longitudinal and
transverse refinement; native F03 candidate meshes have not yet been pinned.
The anisotropic witness does not decide the paired family's outcome. The current box-window
prototype proves only bounded kinematics and first work variations; it is
an unselected alternative, not a replacement bonded-line law.

**Paired-refinement result:** The bounded 8/16/32 longitudinal by 2/4/8
transverse Q4 screen kept the rail-cell aspect ratio at 1.25 and the same
fixed physical strip, supports and density actions. The macro-P0 witness's
normalized work was 6.595e-6, 0.862e-6 and 0.795e-6; the constant
endpoint witness's was 4.663e-6, 0.431e-6 and 0.281e-6. The reported
quotient is the numerical work divided by the square root of q^T K_phys q
and the L2 density norm; no unit conversion was applied. Neither
shows the anisotropic divergence. The strip average of the alternating
transverse field is bounded by its two partial end cells and falls with
transverse cell width; q^T K_phys q is constant for this macro field and
increases for the endpoint field on these grids. This is a constructed-mode
screen, not a whole-space bound, mixed-system result or F03 acceptance.
The executable and raw output are in
`.qualification/b3-ge-e4-pl/r7-f03-paired-refinement-dev-20260928-v1/`.

**Next decision:** Retain the rail as a candidate for prospective paired
family while checking the complete supported physical-core L2 work upper
quotient or deriving an equivalent whole-space bound. If that fails, identify
the responsible mode and correct the law or norm before F03 scoring. If it
holds, proceed to native mixed stability and matched physical torque/shear
transfer. Neither result silently removes increasingly anisotropic Q4 meshes
from the admitted domain; that scope requires an explicit scientific decision.
Do not silently restrict the admitted domain to shape-regular cells: the
programme has no explicit aspect-ratio ceiling, and any new admission rule
needs its own scientific review.
F03 formal assessment stays barred. The seven ratios, growing spaces, three
refinements, physical transfer, locking, shear, drilling, and mixed-system
checks remain mandatory. No automatic axial sweep or new external reference
is justified without a discriminating hypothesis.

## Execution boundary

At most three workers and one heavy numerical job at a time. New diagnostics:
100,000 rows, 600 seconds/run, eight numerical threads, 8 GiB process-tree
memory; verify effective settings. Historical one-use authorities are not
replayed. Preserve raw failures and exact scientific criteria. G0–G6,
V01–V28, B01–B18, external comparisons, scale, independent reviews,
consumers, and one authorized coordinated release remain mandatory.
