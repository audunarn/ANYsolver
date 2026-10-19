# Fixed-fairlead staged mooring equilibrium (development)

`anysolver.marine_equilibrium` is an optional marine public module, API
`marine_fixed_fairlead_equilibrium_v1`. It uses the existing sparse
`MooringLineAssembler` and preserves its tension-only, reference weight/volume,
steady-current and compliant frictionless contact laws. It adds no mass,
compression, artificial stiffness, radiation history or Qt dependency.

## Suspended initializer

`elastic_catenary(first, last, L0, EA, w, material_coordinates)` solves the
homogeneous continuum problem. Coordinates are WORLD/z-up and SI; `w` is
net downward force per reference metre, `(mass_per_length-rho*area)*g`.
Positive and negative wet weight are admitted. Let horizontal force be `H>0`,
the first vertical component `V`, and material arclength `s`. Then

```
T(s) = hypot(H, V+w*s)
dx/ds = H/T(s) + H/EA
dz/ds = (V+w*s)/T(s) + (V+w*s)/EA
```

Two terminal-separation equations determine H/V. Both returned terminal forces
act on their supports, with sum `(0,0,-w*L0)`. Rationalized differences retain
the correct inclined, taut near-neutral-weight limit. The weightless branch
requires a taut cable: a slack weightless continuum has no unique equilibrium.
Vertical/coincident horizontal terminals require an explicit nodal guess.
Shooting is bounded (default200 evaluations); failed geometry closure is a typed
refusal, not an alternative approximate curve.

`initialize_mooring_catenaries(assembler, fixed_body_states)` instead shoots the
actual discrete polygon. Each segment chord is
`L0_j*(unit_tension_j+tension_vector_j/EA)`. Its vertical force uses the
segment reference midpoint, so differences between adjacent tensions balance
the actual half-segment lumped nodal weights. Segment lengths may vary; EA,
mass/length and displaced area must be homogeneous within each line. General
heterogeneous lines can use explicit stationary `MooringNodeState` guesses.
Fixed anchors and finite-rotation material fairleads retain their public maps.
No endpoint coordinates are duplicated. Initializers can be rejected by the
public wetting/floor/segment admission.

MoorPy is an optional independent future reference, not a runtime dependency.
Its [model description](https://moorpy.readthedocs.io/en/latest/structure.html)
also uses homogeneous wet weight and EA in a quasi-static catenary line. This
slice did not run MoorPy or qualify a comparison against it.

## Staged solve and audit

`solve_mooring_equilibrium(model, fixed_body_states, initial_nodes=None,
spec=MooringStaticSpec(...), cancel=None)` fixes all body poses and solves only
free nodal translations. Body and node velocities/accelerations must be zero.
Active waves are refused: static equilibrium cannot freeze an arbitrary wave
phase into a steady load. Downward z-up gravity is required.

1. Ramp gravity and buoyancy together through the specified net-weight
   fractions (default.25/.5/.75/1), with no current or contact.
2. With full weight, ramp the declared steady-current velocities through those
   fractions. The public environment and drag law are re-evaluated at each
   trial node position; current forces are not duplicated or prescribed once.
3. Activate the original contact law at full weight/current.
4. Re-evaluate the original, full model and audit residual, decomposition,
   tension and admissibility before returning `converged`.

The residual is `-force` and `K=-d(force)/dq`, so the Newton correction solves
`K*delta=force`. Node weight is position independent: scaling net weight leaves
the nodal tangent unchanged. Sparse direct Newton handles ordinary states;
compatible singular slack mechanisms use bounded least-norm Newton on the
same unmodified tangent. An inconsistent linearized force balance is refused.
Residual-decreasing admissible line search accepts trial positions. No unique
equilibrium or stability claim follows from balancing a neutral mechanism.
`least_norm_steps` records these steps in each accepted stage.

Force criterion is prospective and explicit:
`max(abs(free_node_force)) <= force_atol + force_rtol*force_scale`.
`force_atol` and `force_scale` are N; normalized residual divides by the positive
user-selected scale. Defaults are development solver controls, not W6 tolerance.
Iterations and line searches have explicit limits. A successful result retains
immutable stage nodes and an immutable final audit, including real compliant
penetration, anchor reactions and fixed-body forces in the assembler's
generalized chart coordinates (not relabelled WORLD wrenches).

Failures and cancellation expose only completed stage states, never the latest
unconverged trial. Before any completed stage, `nodes` is None. Input models,
states, velocities, environments and contact laws remain unchanged. Cancellation
is checked before initialization, each nonlinear iteration/search and final
audit; a single bounded sparse factorization/shoot evaluation is not preempted.

## Remaining scope

This is line-only statics with fixed fairleads. It does not establish coupled
body/link equilibrium, BEM equilibrium-geometry binding, partial wetting,
touchdown/friction qualification, contact nonpenetration, W6 1%/2% gates or
dynamic mesh/time refinement. Contact remains compliant and may penetrate.
Line hydrodynamic trials outside the public fluid domain fail rather than being
clamped: combined hydro/contact below that domain remains an admission issue.
Static workers/Qt jobs and coupled body continuation are subsequent integration.
