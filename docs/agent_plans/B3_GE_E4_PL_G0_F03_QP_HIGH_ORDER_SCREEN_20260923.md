# F03 Q3/Q4/Q5 preparatory high-order screen

23 September 2026. This is **unregistered exploratory work**, not a
scientific attempt, acceptance record, or authority to advance G1. It
continues the independent classical finite-pad reference after the proposed
Q1/Q2/Q3 complete-functional screen gave `6.279584%` and `1.114597%`
adjacent changes against a proposed 1% limit. The old failed Ritz attempts
remain unchanged.

The bounded Qp trace, piecewise pad-moment oracle, energy, signed beam
recovery, functional converter and Decimal one-ulp helper now admit `p=4,5`.
Their numerical inventory limits were raised only to the exact Q5 default
grid size: 2,392 physical nodal coordinates and 2,288 free shell coordinates.
No native B3-GE/E4-PL product workflow or material law changed. An
independent read-only mechanics review found no formula blocker for the
new degree and quadrature orders; it required route-wide and physical
checks before a scientific gate.

An unregistered serial default-grid Q3/Q4/Q5 solve followed by precise
functional recovery returned:

| Degree | Free shell coordinates | Functional norm (N) | Approximate assembly/solve/functional time (s) |
|---|---:|---:|---:|
| Q3 | 832 | 614250.3472649711 | 30.40 |
| Q4 | 1470 | 613319.2873853258 | 43.72 |
| Q5 | 2288 | 612963.5360841347 | 96.60 |

The complete-functional distance was `1804.3383263607025 N` or
`0.2937464%` for Q3→Q4, and `739.6035620365935 N` or `0.1205903%`
for Q4→Q5, normalized by the larger operand norm or 1000 N. Both are
below the proposed 1% physical limit, and the second is smaller. This
did **not** establish the other required signed scalar, reaction, energy,
spatial or band-wrench settling conditions.

A later unregistered signed-output screen preserved its raw Q3/Q4/Q5
values in [the scalar record](B3_GE_E4_PL_G0_F03_QP_HIGH_ORDER_SCALARS_20260923.json).
It found Q3→Q4 failures of the proposed 1% per-quantity rule: beam energy
`1.8199%`, root section resultant `1.5760%`, tip section resultant and tip
atom `2.0057%`, and the `[1/32,1/16]` band wrench `1.4880%`. The largest
Q4→Q5 error in those named families was `0.7783%`, and all checked
Q4→Q5 tip/energy/reaction/section/atom/line/quarter/endpoint-band
quantities were below 1%. This remains a preparatory screen; a complete
physical and absolute-change adjudication has not been made. **Q3/Q4/Q5
must not be registered as the passing sequence.** The natural successor
to investigate is Q4/Q5/Q6, subject to resource and mechanics checks.

Focused source checks performed after the bound change:

| Check | Result | Scope |
|---|---|---|
| Q1–Q5 trace and random piecewise oracle | 39 passed | Includes high-order rigid motion, root rank, derivative plateau, selected crossings and physical yaw. The first extension attempt failed 5 tests; diagnostics were saved at `C:/Users/AUDUNA~1/AppData/Local/Temp/f03-high-order-20260923.log`. A measured smaller finite-difference step and a condition-scaled floating comparison resolved those *numerical test* failures without changing product equations. |
| Qp beam recovery, functional conversion and precise one-ulp route | 44 passed | Includes Q4/Q5 signed work and coefficient/atom checks. |
| Q4/Q5 all-event one-sided direct density | 2 passed | All ten default-grid interior events, both sides. |
| Independent small-grid shell/beam energy and KKT solve | 4 passed in 150.40 s | Q2–Q5; random energy/work oracle, quadrature, scaled solver checks. |
| Finite-pad zero-field area load and atom checks | 5 passed in 74.47 s | Q1–Q5. |
| Spatial cell/boundary/jump/support work | 3 passed in 1141.81 s | Q1, Q4 and Q5 on one custom grid; checked p+5/p+7 x area-order load and signed work. The output lacks per-case timing, so no 900-second per-case conclusion follows. |

The expanded numerical tests use their original work/physics limits.
The high-order float parity test has an explicit roundoff allowance
`2 eps cond(V)` for its independent tensor-Vandermonde reconstruction;
the derivative check uses the measured finite-difference plateau at
`h=2.5e-6` for Q4/Q5. Neither changes a scientific acceptance tolerance.

Before registering any higher-order successor, freeze exact source and case identities,
exercise the complete default-grid physical output inventory and two
support liftings, measure per-case full-route time/RSS under a bounded
supervisor, retain raw output, verify the 1% signed-scalar and absolute-
change rules, check nested energy identities for the new pairs, and obtain
independent execution/mechanics review of the resulting protocol. The
current spatial route's repeated recovery cost is a performance concern.
**F03/G0B remain open; G1 remains barred.**
