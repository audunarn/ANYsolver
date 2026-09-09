# P5 opt-in local force-accuracy development contract

Parent: `c831a0c49c0e3134d16b754e81b256aa0f13e4c9`, tree
`2b411474da8b7c557a632b764f3fdc624839f445`.
Scope: the research nonlinear mixed probe, one new small test file and this
document only. No assembly, controller, canonical runner, production source,
section law, quadrature, coefficient, interface or default changes.

## Motivation and limits of the evidence

The preserved local witness accepts an internal residual of approximately
4e-12 while its nodal-force difference from a more accurate stationary state
is approximately 4.30e-10. This demonstrates that the existing absolute
internal stopping check alone does not bound condensed force error. It does
not establish the cause of the archived control32 failure.

This development introduces an optional research `LocalForceAccuracy` value
to the local `solve` method. The default is `None`: historical calculations,
result schemas, budgets, state replay and byte-bound small fixtures keep
their former path. Existing assembly code does not supply this option.

## Explicit estimated-error criterion

Let `i` be the 18 internal variables and `e` the 18 nodal variables. At the
current internal iterate and fixed nodal state, compute

`delta_i = -solve(H_ii, r_i)` and `eta_e = H_ei delta_i`.

Convert nodal moments in `eta_e` to force units with the supplied physical
`rotation_length`, then take the Euclidean norm and divide by `force_scale`.
The length must be positive and finite. `force_scale` must be finite and at
least one, consistent with the existing assembly's external-force scaling.
The requested normalized error limit must be finite, positive and at most
1e-11. Boolean, string, nonfinite and relaxed inputs are rejected.

This is a **first-order estimate**, not an interval enclosure or mathematical
error bound. It can miss nonlinear remainder and cannot certify rounding
error in the underlying residual evaluation. Its adequacy must be checked
against actual force changes and assembly behavior before qualification.

Accept only when both the unchanged `||r_i||_infinity <= 1e-11` check and the
estimated external-error check pass. Use the maximum of the two normalized
quantities as the opt-in line-search merit. No residual component is clipped,
zeroed or replaced by a Schur-corrected estimate. Return the actual evaluated
potential, residual, Schur tangent, internal state and station responses.

The 25-correction, 64-evaluation and 12-backtrack bounds remain unchanged.
Singular/nonfinite accuracy estimates fail closed; no fallback to the old
acceptance criterion, tolerance relaxation, retry or automatic cutback is
introduced. All station origins remain fixed throughout the local solve.
The negative moment-block and positive rotation-Schur checks still precede
return. A failed local solve cannot commit material or assembly state.

## Small validation and required next work

Tests cover:

- refinement of the preserved manufactured inaccurate internal state;
- actual returned force and station replay, not a surrogate residual;
- coupled elastic and active directed-plastic response on straight/curved
  members, fixed origins and bounded failures;
- spatial covariance and physical scaling of the estimator;
- common-chart energy/residual/tangent directional agreement;
- deterministic opt-in output and default/explicit-None agreement;
- invalid limits, singular systems and nonfinite diagnostics;
- unchanged historical small-case hashes and controller/history regressions.

Passing these tests is development evidence only. The directed-hardening
section does not establish general fibre/J2 parity, and an unchanged legacy
path does not establish opt-in assembly transaction qualification.

Validation before this freeze: **133 tests passed in 33.67 seconds** across
the new accuracy tests, preserved weakness reproducer, mixed operator,
observation/diagnostic, extent, displacement controller, assembly history
and history-path suites. These are small unit/regression fixtures, not a
32-element equilibrium run. The historical raw small-fixture hashes passed.
An initial test-collection import mistake was corrected before this run.
`git diff --check` passed; the exact extent is three research/test paths.

Before an assembly comparison, freeze a separate aggregate local-error
budget and bind its length/force scaling to the global physical residual.
For example, the triangle inequality permits summing per-element estimated
contributions, but these remain estimates rather than rigorous bounds.
Validate opt-in commit/replay and estimator monitoring on small assemblies.
Do not tune a budget against the control32 outcome or silently change a
historical constructor/state schema. If rounding prevents the requested
accuracy, preserve a typed failure and investigate evaluation precision.

Any resource-heavy comparison needs a fresh bounded request and explicit
administrator approval after its clean freeze. The prior consumed requests
are not reused. Resource terminal reporting for control32 remains pending
the already requested communication permission. No resource wave is run
by this contract, and no prior evidence or ledger record is overwritten.

Production qualification, full spatial/material/mass/dynamics/restart parity,
independent review, packaging and objective beam-shell joints remain open.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
