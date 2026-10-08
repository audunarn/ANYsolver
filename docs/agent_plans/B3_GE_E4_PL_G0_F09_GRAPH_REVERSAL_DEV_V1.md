# F09 coupled-section graph reversal development screen

27 September 2026. Bounded Level-A preparatory result on source base
`d1e1c14e28aa179e581af38e9fbc4b85da34fb83`. This is neither F09
acceptance nor a public B2 selection. Historical B2 source and evidence are
unchanged.

## Decision question and bounded experiment

The earlier single-member reversal check had no graph, while the generalized
elbow probe had no reversal. Does the two-member mixed-load graph retain the
same physical response when its second member connectivity is reversed and
its coupled six-channel stiffness is explicitly reoriented? Competing outcomes
are a correct frame transform, a graph scatter or local kinematics defect, or
an apparent agreement caused by insensitive loading. The experiment reverses
one member's node order while holding its physical y axis, geometry and global
tip loads fixed. It transforms the section tensor by the exact local-axis sign
map. A deliberately unchanged tensor is the negative control. The oracle is
an independent exact-rational cut-wrench section-compliance integral with
Simpson integration, which is exact for the quadratic energy density. Two
mixed terminal wrenches exercise axial, both shears, torsion and both moments.
The separate focused station test checks reversed pose, derivative pullback
and equal virtual work at five stations.

Source: `scripts/probe_b3_ge_e4_pl_g0_f09_graph_reversal.py`, SHA-256
`341d20087651535e85c978be01a68dc06612133be308998f7af1bf105493f119`.
Focused test: `tests/test_b2_f09_graph_reversal_probe.py`, SHA-256
`cd3aae445f90afea13213ec94994d21b85f3094c95f43970b31f726a0bc381ff`.
Raw `evaluate()` record: `B3_GE_E4_PL_G0_F09_GRAPH_REVERSAL_DEV_V1.json`.
Command: `python -B -c "import runpy,json; m=runpy.run_path('scripts/probe_b3_ge_e4_pl_g0_f09_graph_reversal.py'); r=m['evaluate'](); print(json.dumps(r,sort_keys=True))"`.
Environment: Windows 11, Python 3.14.2, NumPy 2.4.6, SciPy 1.17.1.
The command emitted the raw record to stdout; it was retained in the adjacent
JSON because this tool session denied ordinary process writes to the worktree.

## Result and next action

Both declared loads pass the diagnostic component/work and separate free
force/moment residual limits of `2e-12`. The two assembled matrices and tip
responses agree exactly at reported binary64 precision. The rational physical
work matches the sparse response to at most `4.44e-16` on the declared
unit-floor measure. Without the section transform, the assembled matrix
differs by `9.35%` of its largest entry and physical work differs by
`0.75%`/`0.16%`; the control demonstrates load sensitivity. Focused private
tests passed `2/2` in `0.68 s`. The five relevant private B2 suites,
including the new tests, passed `29/29` in `4.53 s` using the minimal package
path. This is a development result, not a timing measurement.

The next F09 action can specify explicit reversed generalized-section
provenance and preserve the same station pullback in the eventual attachment
contract. It still needs a physically admitted generalized-section family,
typed representability and conditioning, independent installed graph evidence
and the actual shell attachment. No mass, prestress, F12 or G1 result follows.
