# Prescribed plane translation — shared Newmark development slice

Parent `9ef78d5b`; original C0–C9 objective and all science gates retained.
Question: add physical prescribed-tool motion without another solver/state stack.
Use exact elastic classical B2/B3 plane profiles first; shell DAE/rotation and free
rigid inertia require their own mappings, not implicit admission by this slice.

Immutable named histories supply piecewise-affine translations in metres versus
physical seconds, starting at zero offset. Existing body `path_translation` stays
the static continuation contract and remains rejected here. Stop at every history
knot. Fixed normals/radii permit a tensor Bernstein relative curve/time enclosure:
subtract affine plane controls at temporal fractions 0,1/3,2/3,1. Endpoint force
evaluation uses the same represented plane points. Keep each pair's gap budget and
one aggregate split cap. Set candidate poses from immutable references, not by
incrementally moving a shared committed body. Restore temporary quadrature poses.

Tool work input on the represented path is `-integral F_rigid dot d(point)`;
contact body force is the physical reaction, not a shell material resultant.
Use bounded embedded Gauss integration, report its measured discrepancy separately,
and compare with an independent polynomial/root integral. The estimate is not a
certified continuum error bound. Keep regularization energy and time discretization
effects separate. Only accepted steps accumulate work; checkpoint schema 5 binds
histories/settings and carries each body's cumulative work/error. Old schemas and
fixed profiles remain byte-contract compatible.

Bounded checks: relative bounds versus independently computed polynomial extrema;
uniform beam/constant-speed tool versus scalar forced Newmark; per-tool forces and
work versus independent gap-polynomial integration, changing tool velocity knots,
opening/recontact, multiple bodies, active split restart, changed-history/settings
rejection, quadrature exhaustion/cancellation and pose restoration. Include one
deforming B3/translated-plane case after the scalar discriminator. Prospective toy
comparison tolerances: 1e-10 m,1e-8 m/s,1e-7 N,1e-10 J and original gap gates; no
engineering acceptance. Existing temporal/enforcement/scientific gates remain.

Routine checks use portable development exact targets/JIT off/threads1,180s/953MiB
and fresh output; one coherent installed artifact. Retain failures. Source-only
independent review scrutinizes the relative path, work sign, knots and restart.
Advance on agreement; otherwise one discriminating correction, no automatic cap
growth. Do not replay consumed runs or edit another checkout/owned guard.

## Targeted corrective candidate after first discriminator

The first pulse probe exceeded its unchanged work comparison tolerance despite
the zero-rule safeguard; retain that failure. Isolate temporal support before
sampling, using roots of real-end cubic gaps and the B3 spatial discriminant.
Initial partitions count against the existing work cap. Test both unsampled and
near-zero sampled pulses; do not infer a certified bound from floating roots.
The independent polynomial gap fixture also contained wrong cubic coefficients;
correct its derivation separately without changing the failed result or tolerance.
The source review's feasible sub-minimum knot remainder is corrected by distributing
remaining steps within dt/minimum_dt; impossible partitions reject in preflight.
Add a scalar moving-tool elastic energy balance with dt=1e-4/5e-5, same model/end
and a positive initial kinetic-energy scale: require improvement and finer defect
<=1%. This is a development discriminator, not general impact qualification.

## Time/restart corrections and their evidence

Source v6 retained two review counterexamples: an unreached future knot blocked
a legal truncated endpoint, and arithmetic roundoff rejected a feasible minimum
step. Source v8 retained the large-epoch nearest-knot override; v9 checks nearest
combined ownership and a distinct near-terminal landmark. Review then identified
decimal ceil preflight inconsistency (`.03`/`.025`, knots `.11`/`.17`). Admission
and redistribution now use the same explicit arithmetic roundoff allowance.

Installed v2 retained 96 passes/3 failures: strict tool endpoint iteration exposed
roundoff-sized final steps at split checkpoints. Terminal snapping now lands on
the requested endpoint without skipping a distinct later representable time.
Source v10 retained 17 passes/1 failure: split acceleration differed by
1.388e-9 m/s² under its unchanged 1e-9 comparison. New tool profiles reuse the
existing accumulated Newmark acceleration correction instead of subtracting
nearby positions and dividing by h²; v11 passes that discriminator. Existing
fixed/event profiles and all science/work/gap tolerances remain unchanged.
The installed v2 supervisor's Unicode log display also failed after retaining
the execution record; v3 sets UTF-8 child output. This is an evidence-display
correction, separate from the three solver failures.
