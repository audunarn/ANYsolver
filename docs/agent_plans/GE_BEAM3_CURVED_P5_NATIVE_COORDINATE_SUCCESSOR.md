# Native P5 coordinate precision: diagnosed; correction not yet integrated

## Preserved baseline

The self-contained internal candidate remains frozen at
`cdf71995570b3d1aaeda44b7ed046c04528ae6b8`, tree
`60df248efdaab5579260dcb0b318ed1b05d76c3f`. Its seventeen extracted package files,
source map, installed-wheel archive and previous development evidence are unchanged.
No source, section law, coefficient, tolerance, public selector, existing beam/shell
mechanics, package metadata or default is changed by this diagnostic checkpoint.

This is development evidence, not a new formal qualification certificate, review,
authorization or reclassification. In particular, it does not reinterpret the
preserved 32-element unresolved-sign evidence or prove the cause of that outcome.

## Finding

The native driver owns the total displacement but evaluates the stationary
response using rounded `X + u` positions. `StationaryCore._solve` passes zero low
parts to the existing compensated local operator. Its accepted-origin replay does
the same; therefore successful replay alone cannot detect the lost displacement.
The current-state modal reconstruction also supplies zero low parts. Native
physical-position recovery currently publishes only the high coordinates.

The new diagnostic uses one straight length-2 beam, identity frames, `C=I`,
elastic axial loading below the declared yield threshold, and the exact field
`u_x(x)=epsilon*x`. Its independent rational reference is `N=epsilon`, nodal force
`(-epsilon,0,epsilon)`, and potential `epsilon**2`. No numerical reference solve,
generic simplification, tuned coefficient or absolute-tolerance escape is used.

Three actual native-assembly witnesses are frozen:

- `epsilon=2**-20`: the displacement is representable in the high coordinates;
  the native and compensated responses agree.
- `epsilon=2**-54`: both nonzero nodal displacements disappear in rounded `X+u`;
  native force and energy are zero despite nonzero exact reference values.
- `epsilon=-2**-55`: the same loss occurs in compression.

For the two sub-ULP cases the native relative force error is one. Supplying the
low parts to the **unchanged** compensated local solver recovers axial forces,
strain, resultants and potential within the existing normalized `1e-11` criterion,
here normalized by the nonzero analytical reference rather than by `max(1, norm)`.
The observed relative force error is about `1.2e-16` in this runtime. This is not a
claim that the tiny manufactured loads are themselves an engineering benchmark.

The helper independently checks the two-part sum against exact `Fraction` values
of the supplied binary64 inputs, rejects a mismatched native high pose, nonfinite
inputs, wrong shapes/types and overflow, and owns its output arrays. It is a
diagnostic helper, not yet a production/native state implementation.

Each trial is discarded in `finally`. The accepted material snapshot and both
material/rotation generations are unchanged. The first test attempt correctly
rejected reading a lazy trial payload after discard; the diagnostic now captures
its hash while its token is live. No mechanics change was made for that harness
error. Two fresh-process diagnostic executions must produce identical canonical
records within a fixed runtime. Cross-dependency-version bitwise equality is not
claimed.

## Validation at this checkpoint

The final small correctness suite passed **28 tests in 24.18 seconds**: eleven
coordinate-diagnostic checks, fourteen native-package checks and three preserved
package-checkpoint checks. This includes two byte-identical diagnostic runs in
fresh child-process directories, exact rational ratio serialization, hash-bound
package extraction, and checks of the existing external wheel archive. It does
not rerun installed-wheel builds or any formal mechanics/performance campaign.
The earlier initial diagnostic attempt had six passing checks and two setup
errors from stale trial-token access; those were corrected in the harness as
described above. A subsequent focused run passed all eight then-existing checks.

The stored rational numerators/denominators are JSON integers, including those
larger than `2**53`; they must never be round-tripped through binary64-only JSON
number handling. The static evidence test enforces their exact types and values.

## Next implementation gate: one bound coordinate-state successor

Create a reviewed successor mapping from the preserved package, with new candidate,
core-state, driver-state and codec identities. Do not edit old evidence or silently
reinterpret V1 checkpoints. Do not hot-restart a V1 package checkpoint into the
coordinate-state successor. Reuse unchanged physical operators and source authority;
the intended correction is representation and consistent propagation, not a new
section law, quadrature, stabilization or dynamic reduction.

The complete correction must cover all of the following together:

1. Derive normalized high/low current coordinates from authoritative reference
   coordinates and total translational displacement, not from subtracting rounded
   poses. Require exact high-pose agreement with the live native trial view.
2. Bind the coordinate policy and both parts into the state hash. Validate their
   relation to the total displacement independently; reject resealed mutations.
   Initialization, trial, commit, discard, cutback and cancellation must preserve
   ownership and accepted-state atomicity.
3. Pass the same pair to the local stationary solve and accepted-origin replay.
   A force-only patch is insufficient. Retain the analytic residual/tangent and
   fixed-origin plastic transaction semantics without changing tolerances.
4. Extend the typed canonical codec and model/restart fingerprints. Test exact
   continuous versus split continuation, fresh-process restart, rejected malformed
   records, changed lows, changed policy and mismatched total displacement.
5. Recover station positions without silently dropping lows: publish authoritative
   split physical positions plus a documented rounded display position. Keep
   physical strains/resultants sourced from the recovered stationary response.
6. Use the same position authority in accepted-state augmented stiffness and current
   mass evaluation, equilibrium and mode provenance. Audit load work and inertia
   for coordinate-sensitive sums; fail closed on any route not updated. Merely
   changing the current Hessian's low-parts argument is not complete parity.
7. Audit the reference geometry's direct polynomial sums for large common
   translations separately. This axial diagnostic does not establish large-offset
   reference-frame accuracy; do not fold an unreviewed geometry correction into
   the state patch or claim arbitrary-translation coverage from these cases.

Acceptance requires the exact rational coordinate tests, the three witnesses,
positive and negative increments, coupled curved elastic/plastic states, actual
native Newton/control/cancellation tests, replay/restart/recovery, current/reference
operator tests, deterministic serialization, and a fresh isolated installed wheel.
Retain exact equality against V1 when all low parts are zero; where they are nonzero,
use independent invariants and reference checks rather than demanding equality to
the defective rounding. Add hash/state/codec mutations and no-silent-route tests.

Normal small correctness tests may run under the existing workspace policy. No
32-element study, performance test or other heavy campaign is authorized by this
checkpoint; any such run needs a new clean freeze, request ID and resource lease.
Keep the existing child/wave ceilings for later formal work. No consumed request
is reused and no historical test wave is rerun automatically.

Public integration, general nonlinear material parity, modal/buckling engineering
qualification and objective beam-shell joints remain incomplete. This checkpoint
does not authorize activation, publishing, tags, merging or changes to Q4/S3.
