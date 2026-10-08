# F03 Qp fixed-grid x-refinement pilot

23 September 2026. **Predeclared preparatory diagnostic, not a one-use
scientific registration.** The default-grid Q4/Q5/Q6 signed-band screen
failed its absolute-change condition. This pilot changes the reference
mesh systematically without changing the physical problem, acceptance
criteria, or any observed-output selection. Earlier failed records remain
immutable.

Let `X0` be the sorted default x coordinates returned by
`FinitePadQpTrace`, retaining their exact binary64 values. Define `X1` by
adding the arithmetic midpoint of every consecutive pair in `X0` whose
width is **strictly greater than 0.25**, then sorting. The quarter length
is fixed by the pre-existing beam-quarter observations: every new x cell
is at most one quarter of the beam length. This global geometric rule is
independent of the two failed band values. It inserts exactly `0`, `0.5`,
and `1`; it does not round the represented `±0.15000000000000002` or
`0.8500000000000001` pad-edge coordinates. Keep default y, pads, `J`,
supports, load, material, section, and all normalization scales. The
result has 12 x cells, 17 represented station intervals, and three
one-ulp intervals. Exact-rational crossing inspection found no displaced
interior event. Q4/Q5/Q6 have 1,974/3,068/4,402 free DOFs and Q6 has
4,526 total physical nodal coordinates.

Run Q4, Q5, and Q6 **all on X1**. Do not splice default-grid values into
this p sequence. Preserve raw source/environment identities, timing,
memory, quadrature, root-rank, energy/work, equilibrium and recovery
diagnostics. The holdout is the entire prior 49-component signed scalar
inventory: tip pose, shell/beam/total energy, external work, root
reactions, root/tip sections and atoms, complete line wrench, four
quarter bands, and four short endpoint bands. In particular retain
`[0.5,0.75]` and `[1/32,1/16]` Fy. Also compute adjacent complete H1-dual
functional distances, the unchanged `1%` normalized signed-component
criterion, and `|Q6-Q5| <= |Q5-Q4| + 1e-5*S` for every component. Check
48/64 piecewise full-wrench band work against the separate adjoint,
spatial balance, and Q6 X0→X1 sensitivity. Any failure stays failed.

This one spatial refinement can expose grid-sensitive p oscillation, but
cannot establish h-convergence. A later second h level and independent
adjudication would be required for a continuum-accuracy claim. Even a
passing classical reference cannot qualify the native B3-GE/E4-PL
interface by itself. G0B/F03 stays open and G1 barred.

Independent read-only mechanics review of this fixed pilot rule found no
preparatory objection. The reviewer did not edit or run the pilot.
