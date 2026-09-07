# Loaded connected native restart development

Parent 709d457ce9bd603b42a523fe209f2dfaac4f9332, tree
1d81aca8dc41ebc30875d91ccef6781f8c3556d3. Preserve the frozen bb75ce3 codec,
native static adapter, mechanics and historical qualification. Add only this
plan and a new connected test file initially; no formulation, public selector or default changes.

Use two connected curved quadratic macrocells (five nodes, 30 external DOFs),
with an elastic doubly clamped case and a coupled physical-fibre plastic
cantilever. Use new fixed nodal-force patterns and the actual nonlinear solver,
not the separate retained-coordinate research controller. Run two increments,
encode/decode the whole supported model, continue a half-load prefix into a
fresh model, and require byte-identical final states and complete checkpoints.
Then unload from full to half load and preserve the accepted history chain.

Check all accepted snapshots for shared-node rotation identity, interface
action-reaction including external junction load, free residual, fixed-support
force and spatial-moment balance, physical field recovery without history
advancement, irreversible accumulated plastic history, and typed restart.
Resealed force-pattern/state-swap and changed-connectivity mutations must fail.
Driver tolerance 1e-12 and equilibrium/work gates 1e-11 remain unchanged.

Twelve test nodes: six for each supported model, with separate smoke/rehearsal
inventories. Each child has one numerical-library thread, 24 GiB, 600-second
wall and 120-second CPU-inactivity bounds, no automatic process retry. Preserve
every failure. Freeze after the complete rehearsal, run two fresh-directory
cycles and require byte-identical scientific packets. This is development
evidence, not independent full-workflow qualification or activation authority.

Inspect distributed-load routing separately. The preserved retained potential
has work on physical internal cell rotations; converting a line force only
into nodal forces would omit that work. Any actual-driver integration must bind
the load to internal equilibrium, tangent, state and replay through a separately
frozen successor. Do not silently route through legacy beam load mechanics.

The read-only load inspection confirmed an unsupported shell-pressure fallback:
unit pressure on one curved beam macrocell produced three nodal z forces
-0.006249999999999999 (norm 0.01082531754730548). Preserve this finding; it is
not beam load authority. Before freeze add a closed load-admission helper and
private-class branches at direct LoadCase vector and external tangent entry.
Admit only exact finite six-component nodal rows with zero moments. Reject
pressure, follower policy, unqualified nodal couples, raw element vectors,
gravity, activity/mass and unknown load fields before mechanics. All existing
element routes remain unchanged. This restriction is interim safety, not the
required finished beam's eventual load capability.

Use a separate 25-node load-admission inventory: six unsupported kinds through
direct vector, assembly, external tangent and actual solver entry, plus admitted
force/zero-tangent equality. Keep this inventory separate from the 12 connected
tests. After complete rehearsals freeze all seven implementation paths and verify
fresh deterministic cycles for each inventory. Distributed-load implementation
and work-conjugate nodal-couple routing remain the next required successor.

The first load-admission rehearsal passed 19 and failed six solver-entry cases:
the standard solver constructs initial stiffness before load-vector assembly.
Preserve this failure and move candidate-only load admission ahead of initial
state/stiffness evaluation, including constant and staged load cases. Do not
relax the before-mechanics requirement or alter existing formulation routing.
