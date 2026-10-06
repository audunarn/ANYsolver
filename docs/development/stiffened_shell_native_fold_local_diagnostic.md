# Passive saved-g13 Q4 local diagnostic

Status: **implemented source candidate, UNRUN**. Neither model construction,
assembly, finite differences, collection, tests, build nor interpreter execution
has been performed for this slice. The consumed saved-prefix assessment and its
244.3197409 s verification remainder provide no authority for this discriminator.
The example's main entry refuses execution; a separately authorized supervisor
may call `diagnose_saved_g13(folder,on_evaluation=writer)` and save its detached
structured result. After every complete baseline/signed evaluation, and before
the next, the optional writer receives a separate owned plain capture payload
after complete public/byte preservation checks. Writer errors propagate while
the seam restores and the owner closes. The caller supplies durable storage;
this example creates no output files or archiving framework. A streamed
`COMPLETED_EVALUATION` remains part of a `PARTIAL` diagnostic, not a completed
assessment; only the final bounded result marks diagnostic completion.

## Question and bound

The previous assessment failed its unchanged 1e-6 relative directional and
plateau criterion at all three endpoints. Saved vectors localized 94–98% of the
squared discrepancy to shell transverse-force rows, but did not retain local
per-sign contributions. This discriminator captures those missing observations
at **g13 only**. It does not rerun the three-endpoint assessment or continuation.
It uses the reviewed assessor's exact checkpoint/JSON SHA bindings, public
restore, original supported mixed border, fixed h=(1e-5,1e-6), full unit-factor
load denominator and physical tip-z orientation. The case remains the 8x2 Q4
skin, 16 elements, 162 shell rows and 552 mixed rows with all retained variables
and native multipliers. Exactly one baseline and four actual trial assemblies,
and one border solve, are provided. No h sweep, retry, mesh or mechanics change.

## Passive source seam

The context replaces only three example-scoped aliases:

1. `_stiffened_shell_ge_finite_experimental.q4_algorithmic_response`;
2. `_stiffened_shell_q4_algorithmic_pullback.deformation`;
3. `_stiffened_shell_q4_algorithmic_pullback.spatial_response`.

The first wrapper admits only the fresh owner's model and sixteen known element
objects. The other wrappers observe only calls nested in that actual response.
Each element's accepted predecessor is checked against its same-owner origin
object on every call; captures retain that identity witness and its explicit
constitutive branch/margin limitation, without borrowed history objects.
No global tracing, evaluator replay or alternate map is used. Each wrapper
returns the **same original object**, including original material candidate and
payload. Arrays are copied before subsequent evaluations invalidate scratch.
Nested, foreign, asynchronous and replaced-alias calls are refused. This seam
requires **one synchronous fresh owner in an isolated process**, with no parallel
solver observations. It is private verification tooling, not a supported API or
a concurrency service. All three exact original callables restore in `finally`,
including cancellation and programming failures; unexpected errors propagate.

Original evaluator scratch and material-predecessor lifecycles remain ordinary.
Trial caches are not artificially restored, replaced or reused as acceptance
witnesses. Full accepted public recovery and byte-identical checkpoint are
checked after each evaluation and finally before closing the fresh owner.
Precancellation performs no assembly; postassembly cancellation still restores
the seam and closes the owner. No internal-state atomicity claim is made.

## Captured observations and units

Every actual evaluation retains its complete assembled residual and actual mixed
trial coordinates, plus owned per-element slots, input shell coordinates,
local deformation, differential, second differential, reference coordinates,
rotation anchors and numerical selection flags. It captures the actual local
force/tangent supplied to the spatial adapter and that adapter's returned
spatial residual/tangent, plus the Q4 response's actual returned residual/tangent.
`derived_work_covector=D.T*f` is explicitly a **diagnostic work transform** of
captured arrays, not an observed private intermediate or an extra evaluation.
The baseline actual mixed nonsymmetric sparse Jacobian, full supported tangent,
loads, reference scales and public accepted state accompany these observations.

Shell translation force rows are N, rotational spatial rows are N m. Shell
columns are additive translations in m and additive rotation chart coordinates
in radians; the spatial-row derivative still uses the actual additive columns.
Local corotated forces/covectors retain their original corresponding work units.
Native beam/cell rotations remain spatial-left, retained resultants and constraint
multipliers remain present. No conservative-Hessian equivalence is assumed.

The assembled derivative is measured at fixed actual load against `J*t`; `p`
is the declared full unit-factor dead-load column. Mechanical differences and
plateau use `||D difference||_free / ||D p||_free` and the unchanged 1e-6 criterion.
Constraint witnesses keep their original row-reference scaling. Endpoint and
border limits remain 1e-8 equilibrium and 1e-9 compatibility/control. The local
records also compare actual local-coordinate changes with the captured
deformation differential, and actual returned-force changes with each actual
returned tangent. They do not substitute local coordinates for native mechanics.

## Cancellation bounds and meaning

Q4 returned-force contributions are summed by global shell row. The report
retains sum magnitudes and a conditional **Q4-only** summation and central
subtraction/division bound: gamma_n=n*u/(1-n*u), u=eps/2; each signed row's bound
is gamma_n times an outward upper bound on the sum of absolute returned
contributions, then divided by 2h. A separate `2u/(1-4u)` times the absolute
computed central derivative bounds its subtraction/division rounding. This is
`gamma_2/(1-gamma_2)`, expressed through the computed result, rather than the
insufficient `2u/(1-u)` factor. Each positive bound addition, multiplication or
division is moved outward with `nextafter(value,+inf)`. Exact zero is retained;
subnormal, overflow and positive-operation underflow domains are refused.
Absolute fsum magnitudes are inflated outward by division through `1-u` for
their own final rounding. With at most sixteen terms, n*u and 1-n*u are exact
binary64 operands; gamma division and all subsequent bound arithmetic round up.
These conditional bounds apply to already returned floats, not exact mechanics.

The model is Windows IEEE754 binary64 with ordinary half-even final rounding;
[math.fsum documentation](https://docs.python.org/3.14/library/math.html#math.fsum)
describes the assumptions and possible least-significant-bit double rounding on
some non-Windows builds. No unrestricted exact-sum claim is made. The outward
step uses [numpy.nextafter](https://numpy.org/doc/stable/reference/generated/numpy.nextafter.html).
Reported normalized aggregate bound witnesses use ordinary floating-point norm
arithmetic and are explicitly **not interval bounds**; the outward row-wise
vectors are the conditional upper bounds.

They do **not** bound local deformation, constitutive calculation, spatial
pullback, baseline tangent multiplication or non-Q4 contributions. Those
arithmetic bounds remain UNESTABLISHED. If returned local contributions already
disagree beyond the conditional summation allowance, global Q4 summation alone
cannot explain that discrepancy under those assumptions; local force arithmetic
and a smaller directional-operator defect remain competing explanations. No
arithmetic bound is used to relax or replace the registered criterion.

`assembled_minus_Q4_reconstruction_remainder` is the assembled fixed-load
FD-minus-combined-J*t difference minus the separately reconstructed Q4
FD-minus-elementwise-J*t difference. It includes Q4 scatter/reconstruction and
combined-J versus elementwise tangent-product arithmetic rounding. It can be
nonzero even in a pure-Q4 case and is **not attributed to non-Q4 mechanics**.
The source control includes an explicit binary64 pure-Q4 distributivity
counterexample. The remainder supplies no operator-defect or component proof.

The result stays `INCONCLUSIVE_LOCAL_Q4_DIAGNOSTIC`. It proves neither an operator
defect nor its absence, nor elastic yield branch/margin, a simple or first fold,
continuity, stability or capacity. G4D, external/reference/refinement and F03
remain open. Frozen runtime/candidate provenance and any execution resource
record belong to the future supervisor. Historical evidence remains untouched.

The source tests cover owned observations, exact original return identity,
material predecessor forwarding, alias restoration after original exceptions,
pre/post cancellation, ordinary scratch lifecycle, nested/foreign/tampered seams,
wrong-case and public-entry refusal, full public/byte preservation and owner
closure, and separation of conditional assembly bounds from unresolved local
discrepancies. Exact Fraction controls cover positive outward operations,
cancellation and central envelopes; subnormal/underflow domains are refused.
Callback mutation/failure controls cover detached retained witnesses, partial
labels, actual baseline delivery, seam restoration and fresh-owner closure.
All controls are **UNRUN**; no source-only pass is claimed.
