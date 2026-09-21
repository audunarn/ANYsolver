# F03-D1 preexecution source review

21 September 2026. Independent read-only review by the F03 KKT mechanics
auditor, before source freeze or execution. The auditor compared the fourteen
reused K0 source hashes to the immutable v2 registration; all matched at
review time. The D1 combined probe reproduces v2's native retained-cell yaw,
two physical shell rails, stations, `h=0.001` step, scaling and work
multiplier. The beam-only direction is additional. The six P1-shell cases
include the five v2 parity exceptions and one full-rank small control.

The auditor confirmed the full sparse/dense KKT and signed retained-block
elimination formulas and the separation of D1 completion from F03/G0
acceptance. Three preexecution corrections were requested and made:

1. Validate exact station, direction, step and parity schemas in the
   supervisor, rather than only their record counts.
2. State a common adjacent step pair across directions and stations for
   a mesh plateau, and across both mesh sizes for a topology plateau.
3. Report out-of-plane translation and rotation derivatives in their
   respective units.

A local `ast.parse` subsequently caught an unmatched parenthesis in the
new supervisor expression. The nested expression was replaced by
`derivative_inventory_ok`. The auditor re-reviewed that helper and its use,
then independently parsed both corrected scripts successfully. This syntax
fault was caught **before any run**; no registration or evidence was
consumed. The auditor found no remaining source-level blocker within this
bounded review. It is not a review of future D1 numerical results or full
mechanical qualification. The final committed hashes and execution identity
must still match the registration exactly.
