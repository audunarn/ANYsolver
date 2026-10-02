# Free sphere — coupled shared-driver development slice

Parent0def128d; full C0–C9 objective, science gates and prior failures remain.
Question: obtain physical mutual beam/free-body response without separate lagged
impact integration or inferred inertia. Reuse radial line work and shared Newmark
transactions/restart. Explicit mass, centre at declared sphere point and positive
isotropic centre inertia are required. Frictionless radial tractions are central;
spin advances exactly as exp(t[omega]x), with no torque or shape coupling. This
does not admit anisotropic gyroscopic rotation, eccentric centres or friction.

For beam displacement u and sphere offset c, radial potential depends on u-Ac,
where A is uniform nodal translation on contacting nodes (partition of unity).
If f,K are its beam residual/tangent, coupled contact blocks are
`[f;-A.T f]` and `[K,-K A;-A.T K,A.T K A]`. Structural work/mass remains separate;
three physical centre coordinates join the same constrained Newton/Newmark system.
The free body receives opposite physical force, not an independently applied load.
Retain exact complete relative Hermite curve/time distance bounds, endpoint gates,
bounded cutback/cancellation and explicit resource failures. V6 binds body inertia,
initial velocities, named ownership and the coupled restart coordinates.

Prospective focused checks: independent scalar/two-body response where feasible,
coupled virtual work/directional tangent <=1e-5 on a smooth branch, equal/opposite
force/wrench <=1e-6, independent line-force quadrature and centre impulse, total
linear/angular momentum with unconstrained translational directions, spin energy
and orientation, dynamic press/open, active split restart, changed inertia/state
rejection and cancellation/exception rollback. Independent geometry minima and
crossing tests cannot call the production bounds as their oracle. Numerical toy
response tolerances:1e-10m,1e-8m/s,1e-7N,1e-10J, restart1e-9. Preserve registered
physical gap settings and distinguish time/integration/enforcement errors.

Routine portable development exact selectors, JIT off/threads1,180s/953MiB;
one final isolated installed candidate when source checks close. Independent source
scrutiny targets central-force/spin assumptions, cross blocks, path and state.
No new general dynamics/engineering acceptance or release is asserted.

## Development decisions and retained discrepancies

v1 failed collection on an integration indentation defect. v2 had60passes/4fails:
two real dynamics hit the unchanged512 subdivision cap, and two cancellation tests
used a nonexistent import. v3 corrected the actual public-token cancellation tests.
Geometry correlation was strengthened with exact squared-distance Bernstein
controls; v4 retained59passes/3cap failures, including an independent cubic turning
fixture. Split direction then uses exact lower-bound gain rather than raw vector
variation. v5 passes that fixture and both coupled trajectories at unchanged
1e-10 resolution/512cap. This is a changed algorithmic candidate, not regrading
the original exhausted enclosures or increasing their budget.

v6 retained a B3 case failing its intended1e-5m nonuniform deformation check;
all normal momentum/impulse assertions passed. That E=1e3Pa toy was too stiff to
exercise the intended curve variation. A distinct E=10Pa dynamic fixture was
selected before v7, with the same mass, geometry, loads, step and criterion; it
passes. This changes an exploratory input and keeps the first failure intact,
not a scientific tolerance or previously frozen qualification. v8 passes the
independent closed line-potential energy refinement: dt=.00025/.000125s, positive
initial translational energy scale, improving defect and fine maximum <=1%.

Before checkpoint, exercise the separately exposed free-sphere nodal-history
profile on the same installed source: force ramp0/.004/.025s, active.014s V6 split,
independent two-body external force and polynomial nodal work. Preserve the same
1e-10m/1e-8m/s trajectory,1e-9restart and1e-12J work comparisons. This closes a
changed-branch coverage question without replaying unaffected installed checks.
