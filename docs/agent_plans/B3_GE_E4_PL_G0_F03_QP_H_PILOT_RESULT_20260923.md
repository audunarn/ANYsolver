# F03 classical Qp nested-grid pilot result

23 September 2026. **Preparatory, unregistered evidence. F03/G0B remain
open and G1 remains barred.** This document does not replace the failed
Ritz attempts or qualify a native B3-GE/E4-PL attachment.

The prior default-grid Q6 result and the two prospectively defined x-grid
rules are recorded in the [X1 design](B3_GE_E4_PL_G0_F03_QP_NESTED_X_PILOT_20260923.md)
and [X2 design](B3_GE_E4_PL_G0_F03_QP_NESTED_X2_PILOT_20260923.md).
All three h levels use Q6, identical default y, four finite pads,
represented `J`, section, material, supports, and loading. X0, X1, X2
have respectively 3,286, 4,402 and 5,890 free coordinates. X1/X2
retain the exact binary64 X0 pad-edge coordinates. This is one fixed-Q6
spatial sequence; its values must not be mixed into a p sequence.

## Terminal decisions from the exploratory screens

The default-grid Q4/Q5/Q6 p screen failed the unchanged absolute-change
rule on quarter-3 Fy and near-root Fy. On X1, Q4/Q5/Q6 failed it on
quarter-2 origin Mz: `86794.89555 → 86794.03204 → 86805.43457 Nm`,
giving absolute changes `0.86350 → 11.40253 Nm`, above the permitted
`0.86350 + 4.6 Nm`. The [X1 adjudication](B3_GE_E4_PL_G0_F03_QP_NESTED_X_ADJUDICATION_20260923.json)
retains all 49 signed channels and the full-functional result. Its
functional differences `184.83746 → 31.24801 N` passed, but that cannot
erase the signed failure. The [separate cell-polynomial band check](B3_GE_E4_PL_G0_F03_QP_NESTED_X_BAND_ORACLE_20260923.json)
agrees with the X1 adjoint physical wrench. Independent mechanics review
found that cancellation of the force lever-arm and section-couple terms
made the Q4→Q5 moment change unusually small; the X1 failure is real.

The fixed-Q6 X0→X1→X2 h screen passes its **draft** criteria:

| Quantity | X0→X1 | X1→X2 | Draft decision |
|---|---:|---:|---|
| Largest normalized signed change among 49 components | `0.4462%` | `0.01032%` | Both below `1%` |
| Complete H1-dual functional distance | `141.22460 N` | `7.17886 N` | Both below `1%`; final smaller by more than `10 N` allowance |
| Quarter-2 origin Mz absolute change | `7.90988 Nm` | `5.07388 Nm` | Final within preceding change plus `4.6 Nm` |
| Quarter-3 Fy absolute change | `203.81309 N` | `11.35798 N` | Final within preceding change plus `10 N` |
| Near-root Fy absolute change | `198.68415 N` | `3.50323 N` | Final within preceding change plus `10 N` |

The [h adjudication](B3_GE_E4_PL_G0_F03_QP_NESTED_X2_ADJUDICATION_20260923.json)
retains every scalar, normalization, pairwise percentage and
absolute-change decision. The Q6 X0→X1
[sensitivity record](B3_GE_E4_PL_G0_F03_QP_NESTED_X_H_SENSITIVITY_20260923.json)
independently gave a `0.02304%` complete-functional change. A separate
[48/64 cell-polynomial full-wrench check](B3_GE_E4_PL_G0_F03_QP_NESTED_X2_BAND_ORACLE_20260923.json)
agrees with the adjoint to at most `1.2e-14` scaled over the three
previously vulnerable bands. Those bands are interior, so endpoint atoms
do not enter that check. The beam-root multiplier stored as `eta` has
physical reaction `−eta`; the sign convention does not change the
pairwise settling decision.

## Numerical preparation and resource observations

The bounded Q6 h-prolongation test passed work-conjugate pose mapping,
load/root/tip embedding and solved Ritz-energy identity. The X2 grid
preflight found 16 x cells, 25 station intervals, three one-ulp intervals,
5,890 free and 6,014 total physical nodal coordinates. Its area-rule
point inventory is `8,316 / 10,164 / 12,012` for x orders `9 / 11 / 13`
with y order `7`, within the 65,536-point preparation cap.

X2 completed numerical assembly and solve checks with a functional norm
of `612881.17152 N`. Its measured phase times were assembly `227.57 s`,
solve `21.78 s`, signed recovery `68.05 s`, and precise functional
`18.24 s` (about `335.64 s` combined). X1 Q4/Q5/Q6 phase times and
numerical values remain in the raw case files. These are single
preparatory observations, with no sampled peak RSS or complete-route
spatial/restart cost. They are **not** a performance qualification.

Raw state and outputs are preserved as [default Q6 state](B3_GE_E4_PL_G0_F03_QP_DEFAULT_Q6_STATE_20260923.npz),
[default signed Q3–Q6](B3_GE_E4_PL_G0_F03_QP_HIGH_ORDER_SCALARS_P6_20260923.json),
[X1 Q4](B3_GE_E4_PL_G0_F03_QP_NESTED_X_Q4_20260923.json),
[X1 Q5](B3_GE_E4_PL_G0_F03_QP_NESTED_X_Q5_20260923.json),
[X1 Q6](B3_GE_E4_PL_G0_F03_QP_NESTED_X_Q6_20260923.json), and
[X2 Q6](B3_GE_E4_PL_G0_F03_QP_NESTED_X2_Q6_20260923.json).
Failed initial high-order test diagnostics remain at
`C:/Users/AUDUNA~1/AppData/Local/Temp/f03-qp-p6-focused-20260923.log`;
the focused corrections were checked without changing any scientific
acceptance limit.

## Why no gate has closed

The exploratory cases were not run under a frozen clean source and
one-use supervisor. The h adjudicator binds the default saved state to
its multiplier and tip pose, but does not independently recompute every
stored X1/X2 signed output and functional from its saved state. Actual
X0→X1→X2 Ritz/load/root/tip embedding identities, all-eight-band
independent line and physical-wrench recovery with terminal atom
ownership, complete area/spatial/support lifting checks, sampled memory,
installed-artifact verification and registered per-case resource limits
are outstanding. The independent mechanics reviewer found no sign or
normalization blocker in the local h result, while identifying those
evidence gaps. The accepted classical reference would still not qualify
the native line multiplier, torque/drilling/shear, material or lifecycle
contracts required for G0/G1.

The next work is to close the preparatory state-binding, actual-case
h-identity, spatial and resource feasibility checks, then freeze an exact
candidate and obtain independent review of a one-use h registration.
Any formal run must rerun X0, X1 and X2 under that registration. Do not
reuse this exploratory pass as formal acceptance.
