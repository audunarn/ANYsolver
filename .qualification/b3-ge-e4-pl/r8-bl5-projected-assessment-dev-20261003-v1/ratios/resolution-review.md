# Projected all-five support-resolution design review

Read-only mathematical/source review. No numerical runs, workers, Git changes or scientific acceptance. Source scope: joint norm, rational external row helpers and controlling M2/Revision8 contracts.

## Exact proposed rule and admissible grids

Let N_s be shell trace intervals, N_h native beam halfcells, and b=N_B3/N_s the declared whole-member:shell count ratio. Then r=N_h/N_s=2b. Set H=4 max(1,r) halfcells per support, S=N_h/H supports, and physical support length L/S=4 max(L/N_h,L/N_s). This is four intervals of the coarser shell/native-halfcell trace. It is not four whole B3 members in general.

| Whole B3:shell | Halfcell:shell r | H | Shell intervals/support | S at N_s=16 |
|---|---:|---:|---:|---:|
| 1:8 | 1:4 | 4 | 16 | 1 |
| 1:4 | 1:2 | 4 | 8 | 2 |
| 1:2 | 1:1 | 4 | 4 | 4 |
| 1:1 | 2:1 | 8 | 4 | 4 |
| 2:1 | 4:1 | 16 | 4 | 4 |
| 4:1 | 8:1 | 32 | 4 | 4 |
| 8:1 | 16:1 | 64 | 4 | 4 |

Require exact integer counts: N_h even, integer H divisible by four, N_h divisible by H, common physical trace endpoints and all support endpoints on both grids. Across all seven ratios, N_s divisible by 16 supplies these conditions; the registered 16/32/64 grids do so. Smaller grids can fail even though their ratio is dyadic (N_s=8, whole1:8 gives only two halfcells, insufficient for H=4). Do not round H, shorten the last support or omit incomplete aggregation. At fixed ratio, doubling both meshes doubles S; this is a growing multiplier family, not fixed-rank refinement.

This reproduces current span8 at whole1:1. M2 trace norm contract 145–152 distinguishes whole and halfcell ratio conventions; retain all seven whole ratios, not merely the historical seven halfcell ratios. Revision8 343–353 requires mesh-based supports, complete aggregation and checks of gaps/transfer; 401–405 retains seven ratios and three growing levels.

## Geometric feasibility and native/external distinction

Every support is H/2 complete native B3 members and an integer number of shell intervals. Quarter stations at halfcell offsets H/4 and 3H/4 are distinct interior beam nodal stations, including B3 midpoint nodes when their indices are odd. For exact projected beam P1-hat action, rational helper weights at these stations are (h_h, +/- h_h/2): `r8_bl5_external_affine_reference_dev.py:107–145,215–229`. Their ten-coordinate dependent block remains algebraically invertible for the five physical channels and constant arm/frame. Hats at the first/last quarter do not leak into another support's selected columns (243–248). Endpoint hats and their full support integrals must remain included.

These are independent external nodal elimination stations. They do not identify native retained halfcell directors with nodal rotations, and do not eliminate native resultants. Native translations, cell directors and their actual coupling must retain their own maps/work pairing. Root at x=0 is not a dependent quarter station; all selected dependent coordinates must be free (220–221). The auxiliary product transfer still requires common translational root conditions, unconstrained retained cell directors, constant frames/arms and zero lift. Additional director clamps, differing roots, interior fixes or curved/nonzero-lift traces invalidate this reuse. Mechanical mixed equilibrium is a separate obligation.

The current aggregate_rows admission is deliberately frozen to three existing tuples (185–188); rational helpers are generic but an offratio wrapper needs explicit prospective admission. Do not broaden the old worker gate silently.

## Consequential mathematical limits and implementation discriminators

The rule is geometrically feasible, not proven stable or accurate. For H=4, the retained director gap pattern (1,-3,3,-1), constant over successive halfcells in one support, has zero constant and affine projected moments: its sums against (1,1,1,1) and (-3/4,-1/4,1/4,3/4) vanish. With zero nodal translations and a transverse retained-director perturbation, both director and fixed-arm translation weak actions vanish while pointwise director/surface gaps are nonzero. This is an explicit blind mode, not a claim of zero physical stiffness: actual mixed-kernel positivity and load-driven locking/transfer checks decide its consequence. At whole1:8 the first level has only one support/ten multipliers, so an attractive beta can coexist with seriously underresolved local action.

Current joint norm cannot be parameterized by changing constants alone:

* At `r8_bl5_projected_joint_norm_dev.py:54–55`, the H8 affine density mass 21/(64*S) must become (1-1/H^2)/(3*S), with constant mass 1/S. Fixed H8 scaling would give the wrong canonical L2 condition/floor offratio.
* Its member-to-cell-director mapping at 181 uses range(NX), valid only at whole1:1. Use actual N_h/2 members and validate all retained/free/fixed coordinates and all-column work.
* Its shell-null checker at 80–84 is specific to the current halfcell2:shell1 action. At r<=1 there is no nonzero complete halfcell P0 shell-action null mode with root fixed and tip free: for r<1 interior shell hats identify each halfcell value; at r=1 the free tip action fixes the last value, then interior adjacent sums recursively fix every preceding value. Thus reusing the current checker would produce a false diagnostic failure. Derive the actual complete action rank/nullspace; test a positive-reference null mode only when one exists, otherwise explicitly verify injectivity. Duplicate-column deficiency and basis/unit controls remain applicable. Do not relabel an arbitrary outside-projection mode as shell-null.

Fresh rational action, scalar positive Gram, independent reference error bound and floor must be registered before native beta. The product Fortin argument transfers under the stated physical/root hypotheses; its scalar constant and actual native work/norm do not transfer numerically. No coarse congruence/interlacing or old beta/floor qualification follows. Preserve 1e-3 reference error, 1e-10 inverse/eigen, 1e4 canonical L2 condition and 1e-6 arithmetic margin; retain actual mixed-kernel and physical/gap checks without complete-K SPD claims.

## One discriminating next fixture

Recommend whole1:2 on the existing L=1, width/sections/root supports and fixed Fy load: shell16x4, native eight B3 members/16 halfcells, H=4, four projected supports at the same 0,1/4,1/2,3/4,1 boundaries as current nested40. This is the smallest neighboring offratio that preserves the current physical multiplier-support inventory while halving the retained beam partition and reaching the other branch of the proposed resolution rule. It isolates the former Fy/rotation concern from additional support coarsening; the absolute smallest whole1:8 fixture changes support count from four to one and confounds those effects. Register its fresh independent scalar norm/floor first, then inspect actual full mixed kernel, retained response and weak versus pointwise director/surface gaps, density moments/ground balance and fixed-region transfer. This is one development discriminator, not authorization for the remaining ratios, levels, external gates or F03.