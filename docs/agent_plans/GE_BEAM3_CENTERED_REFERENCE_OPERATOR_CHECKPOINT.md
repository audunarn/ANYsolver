# Stable reference evaluation and stationary operator

## Development status

Base: `0fd9d3a27ad3c385d8d616f25ce5058841d89c5c`, tree
`7dd5eb31755e63f7cac983be46feeae112ca046c`.

This checkpoint implements and checks a stable reference evaluator and a local
stationary-operator successor. It **does not yet integrate them into the native
coordinate-state package**. Independent review and full beam qualification remain
pending. Existing B2/B3, P3 routing, Q4/S3, defaults, V1/V2 native packages, source
maps, wheel archives and all historical qualification evidence are unchanged.

New private source modules:

- `_ge_beam3_centered_reference.py`: `CenteredCurvedBeam3ReferenceGeometry` and
  split-coordinate station records.
- `_ge_beam3_centered_mixed.py`: `CenteredStationaryBeam`, explicitly adopting the
  new reference evaluator and a stable equivalent spatial-dead-load potential.

These are new source additions, not a no-`src/`-delta claim. There is no public
selector, version, dependency, release, tag, push or merge change.

## Finding and correction

For the exactly represented curve with nodes `(-1,0,0)`, `(0,0.5,0)`, `(1,0,0)`,
the preserved reference implementation evaluates shape derivatives against world
coordinates and computes the reference lift by subtracting two world positions.
A common translation of `2**40` produced maximum derivative error
`0.00014475283138885059` and lift error `0.00041659953205635245` in the checked
runtime. The input node differences remain exactly represented; these errors are
evaluation cancellation, not loss of the original geometry at input.

The successor uses the same quadratic curve and the unchanged independently
derived shortest-transport/linear-roll frame policy:

```
a = (X_right-X_left)/2
b = X_left-2*X_mid+X_right
r0(xi) = X_mid + xi*a + xi**2*b/2
r0'(xi) = a + xi*b
half_cell_lift(t) = t*(t-1)*b/2
```

Coefficient construction uses exact rational arithmetic on the supplied binary64
nodes, then stores two rounded components. Runtime geometry uses short compensated
sums and the analytical lift identity. Absolute positions have explicit high/low
components; the high-only `position()` is a rounded display value. `station()`
returns the pair and the evaluation ID. It does not silently return an old station
record that loses the retained component.

Frame interpolation and its analytic derivative reuse the preserved frame
functions through stable tangent evaluation. Regularity, frame tolerances, branch
limits, nodal tangent alignment and proper-frame admission are not weakened.
The regularity computation remains a binary64 evaluation of the analytical
minimum, not an outward interval proof or an all-floating-point-domain theorem.
Overflow/nonfinite and inadmissible geometry fail closed. Two-component storage
does not recover geometry already rounded away before it was supplied, nor does
it constitute arbitrary-precision geometry.

The new local operator retains the physical strain operator, directed-hardening
section law, local nonlinear solve, analytic variations, quadrature and convergence
limits from the preserved package. It constructs stations using the new frame,
Jacobian and analytical lift instead of cloning the old reference evaluator.

Spatial-dead-load work is evaluated using the identity

```
r_h-r0 = I(x-X) + (U-I)*half_cell_lift
```

rather than first multiplying large world positions by interpolation weights.
This preserves small displacement work and retains its analytic first and second
variations. No load coefficient, stabilization or physical operator is tuned.

## Checks and evidence

Final regression: **91 passed in 10.33 seconds**:

- 32 centered-reference checks against an independently written rational Lagrange
  polynomial, including planar/spatial curves, scale changes, exact translations,
  proper rigid frame re-expression, reversal, frame derivatives, midpoint traces,
  split station ownership and rejection of folds/near-singular geometry.
- 14 local-operator checks. Elastic and plastic stationary responses are
  byte-identical at shifts `0`, `2**20`, `2**30`, `2**40`, `-2**40`, with and
  without spatial dead loads. At the origin the new operator agrees with the
  preserved variational operator within the existing normalized tolerance.
- Two diagnostic/evidence checks, including two fresh processes with byte-identical
  canonical output and before/after source bindings.
- Sixteen preserved P4-reference checks, three V2 coordinate-checkpoint checks,
  three V1 package-checkpoint checks and 21 accepted P3 opt-in checks.

The independent tiny load-work reference is the length
`sqrt(2)+asinh(1)` of the planar parabolic curve. A common translation displacement
`2**-54` against a unit spatial line load retains the expected nonzero work even
with reference coordinates shifted by `2**40`. Integrated force, potential,
residual/tangent variations (`1e-7`) and tangent symmetry (`1e-11`) are checked.

Initial focused suites passed 28 geometry checks in 1.41 seconds and fourteen
operator checks in 3.13 seconds. The first combined suite passed 87 in 10.35
seconds. Adding explicit split-station coverage produced ninety passes and one
test-fixture failure: the selected dyadic station happened to need no low part.
The fixture was corrected to a non-dyadic station (`xi=0.3`), without changing
the evaluator or tolerance, before the final 91-check pass.

`ge_beam3_centered_reference_evidence.json` binds the old/new source files, preserved
package maps, five geometry records and two loaded material-branch records with
five identical translated-response hashes each. These are development records,
not formal qualification or independent-review acceptance. The source runtime is
the existing Python 3.13.9 / NumPy 2.4.3 / SciPy 1.16.3 environment. Cross-runtime
bitwise equality is not claimed. No package build, resource request, global lease,
large-mesh study or formal qualification wave ran in this checkpoint.

## Next gate: explicit native adoption

Do not simply pass the new reference object to an old consumer. The tests show
that the old local operator clones it into the old class and loses the evaluation
policy. That remains the preserved V1/V2 implementation, not successful adoption.

Prepare one bound native successor that does all of the following together:

1. Construct the centered reference from authoritative nodes/triads, retain its
   evaluation ID/fingerprint in core, driver, codec and restart identities, and
   reject an old evaluator rather than silently downgrading.
2. Use `CenteredStationaryBeam` for trial solve, accepted-origin replay and current
   augmented stiffness. Preserve the V2 total-displacement high/low state contract.
3. Update reference stiffness/mass factors and current retained-cell mass to use
   the same centered frame/Jacobian and analytical half-cell lift. Eliminate all
   world-position-subtraction lift calculations in those candidate paths. Do not
   introduce trace-rotation inertia, Guyan cell-spin reduction or new mass policy.
4. Update native physical recovery to use the same station schedule and analytical
   lift with the committed coordinate pair. Bind both position components and
   evaluation provenance. Keep physical resultants separate from numerical terms.
5. Preserve fail-closed unsupported routes. The local dead-load potential test
   does not by itself authorize a new native distributed-load, follower, modal,
   nonlinear dynamics or beam-shell coupling interface.
6. Run actual native one/two-element translated elastic/plastic solves, rigid-motion
   and work checks, shared-node assembly, control/cancellation, exact split restart,
   source/state mutations, reference/current modal checks and an isolated wheel.
   Use a successor identity; do not hot-restart V1/V2 states as though their
   reference-evaluation policy were unchanged.

This work corrects numerical evaluation of the existing physical field. It does
not establish full slenderness/locking, buckling/post-buckling, generalized material
parity, public routing or objective beam-shell connection qualification. Those
remain requirements of the active goal, along with independent review. Preserve
the historical unresolved 32-element evidence; any later heavy campaign requires
a fresh resource request and lease, with no consumed request reused.
