# C2 development profile: distributed classical B3/B3 contact

`CLASSICAL_B3_B3_ROUND_TUBE_DISTRIBUTED_PAIR_STATIC_DEV_V0` is an opt-in
frictionless penalty profile for two separate classical B3 cells with declared
round centreline-tube radii. It uses each actual quadratic deformed curve and
the half-weighted sum of both directional reference-line potentials. It maps
forces and the smooth-branch tangent to both beams' authoritative translational
DOFs. It does not derive beam rotation couples from a centreline tube; the
swept-round material-surface profile needed for friction is separate.

The B3 target projection considers all real cubic stationary roots and both
physical endpoints. Competing spatially distinct closest points fail
explicitly. Contact activation and endpoint-projection changes are cut before
8/16-point adaptive line integration. The paired physical-gap certificate
uses quadratic Bézier hull bounds with an explicit spatial cell/depth budget.
The swept check combines these bounds with a conservative relative-velocity
hull, so a clear-start/clear-end through-crossing is rejected. A candidate or
quadrature budget failure reports non-success; no pair is silently dropped.

Use `examples/general_contact_round_b3_pair.py`. Supply a separate
`line_stiffness`, `gap_tolerance`, line integration tolerance and B3 pair gap
accuracy/cell/depth controls. This profile currently admits one elastic,
concentric, straight-reference B3 cell per surface, no shared material nodes,
no endpoint caps, von Karman static analysis and force or displacement control.
Restart binds the pair and numerical settings. B2/B3 mixed pairs and multi-cell
B3 chains are not yet admitted.

Focused tests cover exact parallel-line work, independent curved-line scalar
integration, smooth-branch finite differences, force/moment balance, role
exchange, endpoint and competing projection minima, exhaustive small-grid gap
comparison, through-crossing, coupled displacement control and restart.
`c2-b3-pair-focused-final2.txt` records 10 passing tests after the final
open-state fast path. An affected group including the existing B2 pair and
warped-Q4 route passed 18/18 after those refinements
(`c2-b3-pair-affected-final2.txt`).

The example's explicit 15 mm gap budget is a **development** setting for
100 mm combined radius, far looser than the programme's prospective 0.05 mm
benchmark based on either beam's 50 mm radius. The early unsegmented integration hit its declared
limit near contact activation (`c2-b3-pair-static-local2.txt`); endpoint
projection switching then hit a tangent-integration limit
(`c2-b3-pair-static-local4.txt`). Those failures drove the current cuts and
remain recorded. This profile is implemented and locally tested, not
independently accepted. Exact multi-minimum branch transitions, general
boundary/end ownership, interval-search completeness,
mesh/regularization refinement and scale evidence
remain C2 gates.

The registered narrow-double-pocket case currently measures about
`1.9431e-9 J` in one direction versus `3.8863e-9 J` from independent scalar
integration. It is retained as a strict expected failure in
`test_general_contact_b3_pair_potential.py`. Do not use this development
profile to qualify curved configurations until the missing interval is
handled without failing the coupled static path.

The wheel built from source `40e977a81b4fba3b0d151d993e0db3881f599ecf`
was installed into an isolated target without dependencies or index access.
The installed example produced the same reported forces, gap, counters and
checkpoint version (`c2-b3-pair-example-installed-40e977a8.txt`). This is an
installed-package smoke check, not publication or engineering acceptance.
