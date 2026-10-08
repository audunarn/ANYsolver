# D2 guided partial-foundation independent review — 30 September 2026

## Disposition

Scoped local development PASS for the nx79 and nx159 fixed-target partial-foundation cases, including the saved-data analytical enclosure. Independent source/evidence scrutiny found no remaining consequential ODE, fixture, load, support-row, reaction or enclosure blocker. Both cases pass all 14 retained development gates. Their enclosed force, integral L2 and global displacement errors satisfy the fixed 0.1% analytical target, and the finer L2 upper bound is below the coarser lower bound. This closes the analytical uncertainty question for this named development pair. No D2 scientific acceptance, installed qualification, application admission, release or radial regrade follows.

The reviewer read source and saved evidence and reconciled saved scalar/tree data and hashes. No numerical run, test, solver or replay was executed; this note is the only write. The kappa=1e7 radial target-response NONPASS and kappa=1e8 radial TIMEOUT remain unchanged. A later refinement would require its own prospective bounded authority, not renewal of an earlier run.

## Independent continuum equations and scope

With upward displacement `w`, downward load `q=0.5 Pa`, width 1 m and guided shear coefficient `D=1602.5641025641025 N/m`, the reference solves `-D w''-p+q=0`, `w(0)=0`, `w'(1)=0`. On `0<=s<=0.9 m`, `p=1e6 max(-(1e-4+w),0)` Pa; the remaining 0.1 m tail carries zero pressure. The ODE sign and units are consistent: `D w''`, p and q are Pa, and pressure integration times width is N. Source contact acts upward, target contact oppositely; the clamp action is `-B D w'(0)` upward.

The open quadratic and active hyperbolic fields satisfy front/cut displacement and slope matching. The nonsingular required-gap function is strictly increasing on the admitted front interval and brackets the unique front. Closed bin forces are clipped to the actual active covered domain, with stable negative-exponential ratios and 80-digit bin evaluation. The covered minimum gap occurs at the cut; negative uncovered-tail gap does not create represented pressure or establish collision with an unrepresented target.

`D2_GUIDED_PARTIAL_FOUNDATION_DERIVATION_20260930.md` and `d2_guided_partial_foundation_reference.py` correctly label this a pointwise continuum local-foundation comparator. Production uses finite-mesh nodal weak-gap averages. Their agreement under refinement is measured, not assumed; the ODE is not a discrete KKT or moving-geometry oracle.

The fixed-candidate selfcheck completed exit 0 in 0.281865 s / 38.801408 MB under 180 s / 1,073,741,824 bytes. The independent Decimal front discrepancy is approximately 4.906e-18 m. Front is 0.7564271912760346 m; contact/clamp reactions are 0.09903353861433664 / 0.40096646138566333 N, summing to 0.5 N. Maximum analytic ODE residual is 3.331e-16 Pa, independent five-point ODE relative error 8.101e-9 and bin quadrature discrepancy 2.082e-17 N. Covered/uncovered-tip gaps are -1.719410 / -3.279410 micrometres respectively, with zero uncovered pressure. These are development consistency checks, not a complete acceptance uncertainty certificate.

## Actual FE fixture and row preservation

Source geometry spans x=0.1..1.1 m and y=0.1..1.1 m at reference z=0.0401 m, with two node rows and 79 Q4 cells across x. In-plane coordinates and rotations are fixed; matching y-row normal coordinates are tied by explicit MPCs. Both left normal coordinates are fixed. Two fully fixed S3 target faces span x=0..1 m and y=0..1.4 m. Source bottom offset -0.025 m and target top offset +0.015 m yield the declared 100 micrometre physical clearance. The genuine target cut is at s=0.9 m, inside a source cell.

Consistent source loading gives each interior node -0.25/nx N and each endpoint node -0.125/nx N; both rows sum to -0.5 N. Pre-solve condensation through the actual tied-row basis matches the independently assembled `D/h` scalar stiffness with relative error 3.269024280e-15. Actual profile is `Q4_S3_PATCH_REFINED_PROJECTED_FINITE_PENALTY_STATIC_DEV_V0`; production equations/defaults remain unchanged.

All 160 source pressure modes are represented. Exactly 146 have positive support: both rows' indices i=0..72. Nodes 74–80 and 154–160 have genuinely zero support and exactly zero pressure; no positive hat or prescribed-node pressure row is discarded. Actual top/bottom row displacements are exactly equal. Q1 pressure integration averages the y-row hats and clips every bin to s<=0.9, so the empty tail integrity bin receives no pressure spill. The independent represented physical minimum is at actual covered nodes or the cut, valid for the saved tied-row, fixed-XY/rotation geometry.

## nx79 result reconciliation

The ordinary public solve completes two increments. Physical source/target contact forces are +0.09903461483495607 / -0.0990346148349561 N. Actual source clamp action is +0.40096538516492153 N, closing its -0.5 N applied load; fixed-target reaction is +0.0990346148349561 N. Complete guide moments and MPC/fixed reactions remain in both-body wrench reconstruction.

| Retained quantity | Result | Limit |
|---|---:|---:|
| Sampled displacement norm relative error | 5.727898e-5 | 0.02 |
| Integrated contact reaction relative error | 1.086798e-5 | 0.02 |
| Physical-bin L1/L2 relative error | 0.001571420 / 0.001231880 | 0.02 |
| Represented physical-gap lower bound | -1.722871e-6 m | >= -5e-5 m |
| Joint free equilibrium relative residual | 1.139936e-12 | 1e-6 |
| Maximum complete both-body wrench diagnostic | 8.060562e-13 | 1e-6 |
| Independent pressure-to-physical-force conversion | 1.473260e-10 | 1e-6 |

Nonnegative pressure, zero algorithmic multipliers, exact positive-support membership, y-row ties and the empty integrity bin also pass. Supervisor completed exit 0 in 118.5607846 s / 335.634432 MB under 180 s / 1,073,741,824 bytes. Resource/log/snapshot and raw result remain retained.

## Identity and analytical closure boundary

The executed coupled helper snapshot matches recorded SHA256 `f3a93eee11447d6a8f1b6abc199a61c47331b7d0a3f63b7fe2a059ef2bd91671`. Independent reference source is `ce407a6078eb76e01b552a6cb2353cf1b09bef847a1b2ccd5dc3adeb3c6373c1`; derivation is `f68c4c3f8b6103660d26a1afedd927d6ca9275a7c4f2077a2f19704373f43481`. All 433 recorded package source hashes match current production, with zero mismatches. This is source-checkout evidence, not a wheel claim.

- Reference selfcheck JSON: `fac5665f9875b23db30a64b7e924995d85f063ecb128e46c254593fc4fb6496d`.
- nx79 result JSON: `b0b1f10e52dc101eded53c855af49dc709bc92e596bc15745422fad796904fc6`.
- nx79 frozen inputs: `c4777f6354f3dfbe10cb34d3d0cc659cf98b4475ffca7e0229a06ca2f3438e68`.

The coupled helper correctly labels its 1001-point norm as sampled rather than exact continuum L2. Its raw analytic diagnostics remain recorded as unassessed; the separate saved-data enclosure below supplies the subsequent analytical disposition without rewriting those records or replaying a coupled solve. The nx159 evidence addresses discrete weak-gap refinement under the same physics/scales/gates and a separate prospective cap. It cannot establish arbitrary partial-boundary accuracy, uncovered-tip collision, moving stability or replace either radial failure.

## nx159 actual refinement

The separate prospective nx159 run completed two increments and all 14 development gates. Supervisor completed exit 0 in 214.8419627 s / 363.032576 MB under its newly declared 900 s / 4,000,000,000 byte cap; no earlier run was repeated. The constrained `D/h` operator error is 1.746019360e-15. The frozen package map is identical to nx79, and all 433 package and recorded helper/reference hashes match current files. Executed nx159 helper/snapshot SHA256 is `8d23e00fb622bd1e856c5d189545e330c5eaa24366cf23240fa1bf20b839ce3c`; the prior nx79 snapshot remains unchanged.

| Retained quantity | nx79 | nx159 |
|---|---:|---:|
| Sampled displacement norm relative error | 5.727898e-5 | 1.525513e-5 |
| Integrated contact reaction relative error | 1.086798e-5 | 6.884102e-6 |
| Physical-bin L1 relative error | 0.001571420 | 0.0003051625 |
| Physical-bin L2 relative error | 0.001231880 | 0.0002392805 |
| Represented gap lower bound (m) | -1.722871e-6 | -1.720428e-6 |
| Joint free equilibrium relative residual | 1.139936e-12 | 8.169588e-14 |
| Maximum full both-body wrench diagnostic | 8.060562e-13 | 5.194178e-13 |
| Independent physical-force conversion | 1.473260e-10 | 1.520772e-10 |

Sampled displacement error decreases by approximately 3.755 and physical-bin L1/L2 errors by approximately 5.149/5.148. This is meaningful information from the declared pair, not a proved general rate or monotonic mesh-family guarantee. All 320 pressure modes remain represented, exactly 290 positively supported; unsupported nodes 146–160 and 306–320 have exactly zero pressure. The empty integrity bin is exactly zero. Physical source/target forces are +0.09903422029524686 / -0.09903422029524689 N; actual source clamp +0.40096577970501246 N closes the -0.5 N load.

- nx159 result JSON: `c604268c746d4a425fd0223a22b8287ff2d2b234747b52202c720245184788c7`.
- nx159 frozen inputs: `23c507dc71bdbf2aacd642714491bac0bf039272d4301e4056ad23bf55490ad2`.

## Saved-pose enclosure: source and uncertainty review

The implemented uniform midpoint-cell Lipschitz route is mathematically consistent. FE nodal slopes bound its piecewise linear interpolant. From the ODE and nonnegative pressure, `w'(s)=[-q(L-s)+integral_s^Ls p]/D`, with `0<=Fcontact<=qL`; hence `Lref<=2qL/D` is a safe global bound. Front/cut continuity suffices despite curvature jumps. In each cell, evaluation-error and Lipschitz-radius allowances give lower/upper absolute-error bounds. Positive squared sums bound the error integral and reference-square integral; with a strictly positive denominator lower bound, their ratios enclose the true L2 norm. Maximum cell error upper bounds give a global Linfinity enclosure. This avoids calling the previous sampled norm exact.

The preliminary proposed 1e-12 m floating reference allowance was replaced before execution. The actual assessor evaluates every reference midpoint in Decimal80 at a fixed one-million-cell partition. The fixed-domain proof bounds its few dozen arithmetic/exponential operations; it does not infer a rounding certificate from agreement with double precision. The root starts in [0.7,0.8] m and changes endpoints only on signs resolved beyond a 1e-60 m function guard. Its resulting bracket is retained and must resolve 1e-20 m. Positive derivative and front-sensitivity bounds, plus binary conversion below 2e-19 m, support the 1e-18 m point allowance. Closed-force sensitivity below 2 N/m supports the separate 1e-15 N force allowance. These are fixed-parameter bounds, not guarantees for arbitrary materials, loads or fronts.

The saved equal-row FE interpolants satisfy the admitted displacement/slope limits. A 1e-14 m coordinate/interpolation allowance, outward slope increments and enlarged cell radii cover the actual nx79/nx159 arithmetic. Positive-sum endpoints explicitly use `y/(1+gamma)` and `y/(1-gamma)` followed by outward `nextafter`; square-root/ratio endpoints receive additional 32-epsilon allowance and outward rounding. This correction addresses the prospective sum-proof clarification. The actual reported positive reference-square lower bound is greater than zero. The tip value supplies a lower bound on the reference supremum for the global displacement ratio; no unique-tip-maximum assumption is required. No NumPy exponential error assumption or solver/contact kernel call remains in the assessment.

## Saved-data analytical result and identities

The one saved-data process completed exit 0 in 60.0167788 s / 119.549952 MB under 180 s / 1,073,741,824 bytes. Assessor time is 57.1448928 s. Both source cases remain complete with their original physical, pressure, work and reaction gates. The assessor consumes their authentic saved displacements and certificate forces; no new mechanical state is solved or committed.

| Enclosed relative quantity | nx79 | nx159 | Fixed target |
|---|---:|---:|---:|
| Integral L2 lower bound | 5.269397e-5 | 1.077882e-5 | — |
| Integral L2 upper bound | 6.201478e-5 | 2.017927e-5 | <= 0.001 |
| Global displacement upper bound | 1.594264e-4 | 4.848089e-5 | <= 0.001 |
| Integrated reaction upper bound | 1.086723e-5 | 6.883334e-6 | <= 0.001 |

Both meshes pass all three numerical upper-bound comparisons. In particular, nx159 upper 2.017926926e-5 is below nx79 lower 5.269396660e-5, so improvement follows from disjoint integral-norm enclosures rather than sampled norms alone. Previously measured physical-bin errors improve as recorded above. The reference-square integral is enclosed by [6.359187116e-9, 6.359279255e-9] m3. Each retained front bracket has width below 1e-20 m and contains the same fixed-case front. The package/physics maps match across both saved cases, and all 433 package hashes still match current production with zero mismatches.

Frozen/result common metadata and both saved-input hashes reconcile exactly. Actual helper and executed snapshot have SHA256 `788976baa384cc481ea1025a67ef4f1a3d0315cdc8fb4b3a8abdd4a402a80747`; the reviewed enclosure derivation is `d8fc561eb8801cac229b7387aa55d43ecb446a435201fea173e62c15b9a65199`. The effective process records Python 3.14.2, Decimal precision 80 and ROUND_HALF_EVEN. Read-only independent scrutiny reconciled numeric intervals, gates, snapshots, inputs and resource evidence; it did not execute the assessor or repeat a solve.

- Enclosure result JSON: `c38d11ba23548902ca2288f000da8e0ba2f0504f769f8e4349c8ec7e279e6c2b`.
- Enclosure frozen inputs: `e77a010dc60ae672a321918ab316fef9160e0c06025e41bca3cb330dfce94ab4`.
- Enclosure resource JSON: `f3787fbbc0e5e8fc17444b84ac51a3761f9a5dd9cf5626e1d922b1ef6ce571f5`.

Disposition is analytical development PASS for the named guided, fixed-target, partial-foundation pair only. Raw `accepted=false` and `released=false` remain correct. This evidence neither qualifies general moving supports or arbitrary partial boundaries nor repairs the retained radial NONPASS/TIMEOUT. Any later method/profile acceptance or installed boundary is a separate obligation.
