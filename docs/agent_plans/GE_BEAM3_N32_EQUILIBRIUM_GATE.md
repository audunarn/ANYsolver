# N32 same-problem equilibrium prerequisite for modal mesh convergence

Parent f7335e75ea0c2e373a8be875f51c9d77461cd5ee. Eight-path extent:
src/anysolver/_ge_beam3_refinement_capacity.py,
src/anysolver/_ge_beam3_native_generalized_program.py,
src/anysolver/_ge_beam3_retained_generalized_state.py,
src/anysolver/_ge_beam3_elastic_seed_modal.py,
docs/reference_cases/ge_beam3_n32_controlled_case.py,
docs/reference_cases/ge_beam3_n32_equilibrium.py,
tests/test_ge_beam3_n32_refinement_capacity.py, and this plan.

## Capacity, not mechanics

Private explicit context n32_refinement_capacity permits at most32 elements,
1280 full retained coordinates and640 factor coordinates while active. Outside
the scope the existing24/1024/512 limits are unchanged. The nodal512 limit remains
unchanged, as do condensed driver limits. Nested scopes reject and exception exit
restores defaults. Fresh contexts do not inherit active capacity. Enlarged model
guards reject use outside the scope. No new public selector or model default.

Only three existing size checks consult the scoped limits. No potential,
residual/tangent, section, state/recovery laws, source equation, tolerance,
quadrature, frame convention, loading rule or time/iteration bound changes.
The old research N24 model and all historical scientific files remain unchanged.
No runtime monkeypatching, replacement imports or rewritten historical packets.

N32 geometry is the same parabolic reference x in[-1,1], y=.1(1-x^2), z=0,
65 quadratic nodes,32 elements, exact same physical nodal triads, 4Gauss per half,
coupled generalized elastic section diag(1000,400,400,.02,.01,.02), and explicit
GE_BEAM3_RETAINED_GEOMETRIC_WORK_DECIMAL80_V1 arithmetic policy.
The element/section constructors and all coefficients are unchanged.
Clamped ends1/65; quarterspan node17 z displacement +/-0.0065; only spatial dead
vertical force at crown node33. There is no external lateral force.
Retained Newton dimension1158; future modal dimension582, physical381,
algebraic189. This wave does not run modal analysis or modify spectral limits.

## New equilibrium, never relabelled history

Bind the saved continuum endpoint comparison/polynomial inputs through the
existing manifest6e4ee30363656257d27db2fc5ace7ff24b76472b17050e6481af6d72ffe82ff6
and exact positive/negative member hashes in ge_beam3_spatial_ritz_worker.
The continuum polynomial and load initialize a genuinely new native equilibrium
calculation. They do NOT define native residuals or acceptance.

Interpolate positions and nodal frames from the full piecewise polynomial.
Each cell rotation guess is current midpoint frame times reference midpoint
frame transpose. Guess reference-global force coefficients using U^T n and
material endpoint moments using R0(node)^T U^T m, choosing the cell's one-sided
segment at the crown force jump. Set supported endpoints exactly to native
reference positions/frames; zero low-position initial parts. These guesses have
no accepted state authority. Native Newton solves every free nodal/internal and
resultant coordinate using virgin station histories; no material history imported.

Reuse the existing trial-only elastic_control and solve_guess methods, their full
bordered Newton and line search, 24 iterations/8 backtracks and1e-11 equilibrium,
compatibility and correction criteria. No solver reseeding, mode removal, force
adjustment beyond its solved continuation multiplier, or automatic retry.
Require global force/moment balance <=1e-11, unchanged state during native recovery,
all256 stations virgin, actual control value and complete state descriptor.
Save the initial guess separately and bind its continuum provenance.

This prerequisite emits a converged research equilibrium only:
accepted_history_issued=false, old_chain_relabelled=false,
physical_loading_path_from_rest=false, modal_comparison_passed=false,
production_qualified=false. A later exact seed-enrollment/replay gate must issue
new owner state before native modal capture. No N24 capsule is transplanted.

## Tests and bounded wave

Test scoped/restored/nonnested capacity, malformed sizes, fresh-context isolation,
full native N32 model/support audit, post-scope rejection, old model hash equality,
one-sided source sampling, actual bound +/- continuum guesses, proper native
frames/shapes, exact clamps, and preservation of virgin inputs.
Run the existing lightweight capacity tests, excluding its two historical
mechanics runs. Do not combine inventories or claim those omitted runs passed.

Freeze clean source before positive smoke. If smoke succeeds, run negative and
both replicas in three fresh processes. Require same-sign equilibrium bytes
identical and all four trees terminal before aggregate. No reference BVP, N24
equilibrium or eigenanalysis is run. No automatic retry after a consumed failure.

One numerical thread each; max3 concurrent;600s and24GiB per process tree;
1800s wave; existing120s physical-context deadline and CPU-inactivity bound
unchanged. Progress at source, virgin context, every assembly/correction and
completion. Preserve initial guesses, stderr and any failure records externally.
Incomplete/failed worker data never becomes accepted canonical equilibrium.

This gate cannot cure the N24 modal comparison failure or qualify the beam.
After successful new seed issuance, a separately frozen spectral capacity/map
successor may compare all six N32 modes to the existing resolved reference under
the unchanged2%/0.95 gates. If the prerequisite fails, preserve it and diagnose;
do not silently extend limits or tune mechanics. No B2/B3/S3/Q4/default/version,
publication or activation change. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
