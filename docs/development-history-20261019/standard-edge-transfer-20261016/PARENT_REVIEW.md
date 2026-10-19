# Parent review of initial product diff

R1: `_validated_shape_weights` checks finite entries but not finite reduction.
Finite huge mixed-sign weights can make numpy sum NaN after overflow, for which
`abs(weight_sum-1)>tol` is false. Require explicit finite weight_sum before POU
comparison, and a regression with finite entries whose sum overflows to NaN.
Reject before constructor/emission success; preserve finite negative weights.
This is a boundary validation repair within fixed contract, no extra physics.

Review so far: exact equation coefficients unchanged, missing referenced nodes
now fail through existing audit, aliasing preserved, protected assembly excluded.
Final tests/docs review follows handoff. Do not restart passed unchanged checks.

R2: Current wrench test sums nodal moments directly; those are about DIFFERENT
node origins. It does not demonstrate total moment about declared common origin.
Use physically matched xb=sum(Ni xi)+r, arbitrary nonzero common origin o, and
sum [mi+(xi-o) cross fi] from actual diagnostics. Compare applied beam wrench
M+(xb-o) cross F with internal sign. Keep per-node map test separately; separate
force/couple scales instead of dividing concatenated mixed units by FORCE_SCALE.
Virtual work should also contract actual master-equivalent diagnostics, not only
an analytic transported wrench; retain analytic oracle as independent third leg.

R3: test_mutable_weight_refresh_matches_cold_session_parity currently creates a
fresh transformation each time, no AnalysisSession is used. Add REAL reused
AnalysisSession constraint_plan versus cold AnalysisSession, with valid aliased
weight and offset updates and structure-key/cache invalidation assertions.
Existing generic session tests don't cover mutable coupling coefficients.

R4: New test named linear weights uses 3 masters at noncollinear positions with
arbitrary weights. Add/use actual 2-node linear edge shape weights at a stated
coordinate; current negative3-node quadratic weights are fine. Keep algebraic
fixtures explicitly named if retained. A positive shared-node mesh generation
control must show no coupling elements/slave constraints are installed (current
self-coupling rejection alone is negative coverage). Reuse existing simple
MeshConfig(use_shared_nodes=True) production path/finite fixture.

R1 reproducer confirmed locally: numpy finite array [1e308,1e308,-1e308,-1e308]*2
has sum NaN (under errstate overflow/invalid ignore). This passes current sum
comparison erroneously. Reject nonfinite reduction and test emission after
aliased mutation too.

R4 source clarification: mesh_gen.generate_stiffened_panel_mesh explicitly
REJECTS use_shared_nodes=True for eccentric stiffeners (lines650ff); do not
re-enable it and do not treat that refused option as a positive route. The
positive shared-node control should be the existing direct FEModel composition:
a standard shell panel (generate_simple_panel_mesh or hand-authored square),
then a standard BeamElement along the same shell edge node IDs, no coupling
element. Assert their edge DOF identity and zero MPC slaves via production audit/T.
This is the admitted coincident shared-node route, no new eccentric capability.
The suggestion to use that refused mesh flag is withdrawn on source evidence.
