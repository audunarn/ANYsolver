# F03 Q6 preparatory signed-output screen

23 September 2026. **Unregistered diagnostic only.** This records the
next reference-level investigation after Q3/Q4/Q5 failed the draft 1%
signed-scalar screen. It does not amend any earlier failed result, create
a one-use authority, or clear F03/G0B.

The default-grid Q6 candidate has 3,410 physical shell coordinates,
3,286 free shell coordinates and eleven represented station intervals.
The bounded trace, energy, piecewise moment, signed recovery and precise
functional helpers were extended to Q6. In one preparatory serial run,
assembly took `87.03 s`, the scaled sparse solve `5.99 s`, and precise
functional conversion/norm `4.25 s`. The beam-order and load-order
discrepancies were `3.29e-14` and `2.09e-16`; scaled equilibrium and
root-compatibility defects were `4.67e-15` and `2.44e-15`. The Q6
functional norm was `612907.6789728493 N`. The direct-recovery and
independent nodal-coefficient defects were `1.88e-12` and `6.87e-15`
normalized. These are numerical preparation observations, not a full
mechanics or resource gate.

[Raw signed outputs for Q3–Q6](B3_GE_E4_PL_G0_F03_QP_HIGH_ORDER_SCALARS_P6_20260923.json)
retain tip pose, shell/beam/total energies, external work, three root
reactions, root/tip section resultants and atoms, complete line wrench,
quarter bands and four short endpoint bands. The original Q3–Q5 raw
record remains separately preserved.

For Q4→Q5 and Q5→Q6, all 49 compared scalar components in that inventory
are individually below the draft 1% normalized limit. The second
mandatory condition, however, fails on two signed force components:

| Quantity | Absolute Q5−Q4 change | Absolute Q6−Q5 change | Allowed increase floor |
|---|---:|---:|---:|
| Quarter band `[0.5,0.75]`, Fy | `103.106 N` | `202.258 N` | `10 N` |
| Near-root band `[1/32,1/16]`, Fy | `30.951 N` | `177.243 N` | `10 N` |

The rule requires the final absolute change not to exceed the preceding
one plus `1e-5*F0 = 10 N`; both rows exceed it. Small relative error on
each pair does not erase these failures. The first independent
[piecewise-density band integration](B3_GE_E4_PL_G0_F03_QP_BAND_INDEPENDENT_20260923.json)
compared **Fy** only: its third component is a line-angular integral,
whereas the adjoint reports physical origin `Mz`. The corrected
[full-wrench reconstruction](B3_GE_E4_PL_G0_F03_QP_BAND_WRENCH_INDEPENDENT_V2_20260923.json)
includes the station lever arm and represented pad geometry. At 48 and 64
points per interval, its `(Fx,Fy,Mz)` agrees across orders to at most
`5.9e-11` physical units and with the separate adjoint recovery to at
most `3.0e-8` physical units on these bands.
Neither failing band touches an endpoint atom. The third-quarter band
has substantial cancellation between its `[0.5,0.6]` and `[0.6,0.7]`
subinterval changes, while its Q5→Q6 change is mostly in `[0.7,0.75]`.
The near-root band lies wholly in the first station interval. These
observations support a real local p-refinement oscillation rather than
a band integration or endpoint-allocation bug.

The Q5→Q6 complete-functional
distance, default-grid spatial work, full area/resource run, systematic
Q6 operator tests, installed-artifact checks and formal independent
adjudication have not been performed. **Q4/Q5/Q6 cannot be registered
under the draft acceptance matrix.**

Next, use a predeclared, bounded, nested x-grid refinement at the physical
support and represented pad/cell transitions. Retain every signed band and
the unchanged 1% and absolute-change criteria. Determine whether the
two failures persist under that spatial refinement before deciding on a
new scientific registration. Do not drop either band, weaken its threshold,
or describe this screen as a pass. **F03/G0B remain open; G1 remains barred.**
