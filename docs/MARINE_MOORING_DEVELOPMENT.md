# Sparse mooring mechanics — development contract

`anysolver.marine_mooring` owns a stateless line assembler. The common
`marine_mechanical` Newmark driver now integrates its body/node equations.
This development route does not establish W6 acceptance.
Line hydrodynamics, contact, catenary equilibrium and project/replay integration
remain required plan work.

The coordinate inventory contains six chart coordinates per rigid body followed
by three translations per free node. Anchors and rigid-body fairleads have no
additional coordinates. Bodies retain their public `RigidBody6D` mechanics;
fairlead velocity, acceleration and force pullback use its public point Jacobian.
Free-node states are immutable arrays. Segment/node indices are compiled once.
Distinct lines cannot share free nodes in this initial contract.

For segment displacement d, length l, direction n=d/l and length rate r,
elastic tension is E A max(l-L0,0)/L0. The viscous coefficient is c on the
stretched branch and zero on the slack branch. Total tension is
max(elastic+c r,0). Segment endpoint forces are +T n and -T n. This clipped
law carries no compression; axial damping force is (T-elastic)n. Its dissipation
(T-elastic)r is nonnegative, including the closing branch that clips to zero.
At branch boundaries the assembler supplies the inactive tangent, not a unique
classical derivative. A solver must account for that nonsmooth constitutive law.

Each segment contributes half its reference mass mu L0 and reference displaced
volume A L0 to each endpoint. Net submerged weight is (mu-rho A)L0 g,
distributed the same way. Mass and volume do not vary with axial stretch. No
artificial rotational mass is assigned to a node. Endpoint inertia includes
the geometric acceleration supplied by the rigid-body point map. Fixed anchors
carry their lumped weight through reported support reactions.

The generalized force is external line force minus line inertia. Returned
K=-dF/dq, C=-dF/dv and M=-dF/da. Node columns and acceleration derivatives
are analytic sparse blocks, including their pullback to bodies. Attached body
rotation columns additionally use central differences of the public point
Jacobian, velocity and acceleration with maximum angular step 2e-6 rad
(angular-rate step 2e-6 rad/s), retaining
follower and geometric acceleration terms. Constitutive forces and segment
lengths are never differentiated through those probes. This approximation is explicit; matrices are not forcibly
symmetrized. It requires further integration/convergence evidence before
scientific acceptance. Analytic segment blocks use the branch selected at the
base state for body and node columns even close to a slack/taut or
tension-clipping switch. At a submerged base state on the waterline, kinematic
probes extend the smooth point maps; public emerged states still
fail. This is a wet-side derivative, not a partial-wetting model.
Rotation probes shrink to one quarter of the remaining principal-chart seam
clearance. Results record each attached body's effective rotation/rate steps.
If that step is at or below 64 machine epsilons times max(1,|theta|), tangent
assembly fails with `MooringLineError` requesting recharting. Force-only evaluation
can still succeed there. No invalid chart probe or silent one-sided derivative
is supplied.

Only fully submerged straight segments are admitted (every endpoint at or below
the still-water level). Any emerged endpoint, collapsed segment, invalid numeric
input, unknown body, missing node or duplicate node ownership is refused.
Nonfinite support forces, tangents or energy from finite-but-overflowing inputs
are also refused. Inputs
are immutable. Result arrays and sparse matrices are fresh and may be changed
by a consumer without affecting subsequent evaluations. Elastic, damping,
weight and inertia diagnostics sum to the assembled force.

Development checks cover independently calculated straight-line blocks,
potential gradients, finite-rotation body/node derivatives, virtual work,
force/moment balance, dissipativity, branch/refusal paths and three-line sparse
inventory. The assembler tests contain no dynamic trajectory or qualification
campaign. Separate `test_marine_mooring_driver.py` development cases exercise
up to four steps of the common coupled driver, including independent linear
Newmark, finite-rotation rechart and atomic body/node/history failure checks.

Optional `MarineMechanicalModel.mooring` binds exact ordered bodies. Pass
`initial_nodes=MooringNodeState(...)` to `solve_marine_mechanical`. The body
contribution owner retains its body sublayout; line forces/matrices extend that
layout in the same sparse Newton solve. Initial acceleration includes line mass
once. Nodes remain world translations and commit only after body history
transport and cancellation checks. Frames store authoritative node arrays,
tensions, reactions, line energy and force diagnostics.

Body-only model/result schemas remain `marine_mechanical_v1`. Line-bearing
models/results use `marine_mechanical_mooring_v1`; exact named line transport
refuses unknown fields/code and prevents an old parser from dropping line data.
ANYmarine project/worker/GUI replay integration is still pending.
