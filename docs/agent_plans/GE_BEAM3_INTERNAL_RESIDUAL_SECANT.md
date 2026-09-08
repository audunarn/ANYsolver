# Bounded internal residual-secant globalization

Base: 7ceb34184f4ef1250329f38cb4ce72c811381923. Preserve the failed prestress
freeze eecf162 and its external archive; never reclassify or retry that freeze.
This successor changes only numerical globalization in the private generalized
stationary solver. No constitutive law, geometry, load, tangent, quadrature,
mechanical coefficient, acceptance tolerance, shell or legacy beam changes.

Keep all nine existing halving trials and their acceptance calculations.
Only after all nine fail, use their last residual and the base residual,
preconditioned by the same Newton factor. Minimize the squared norm of the
affine residual segment. Require a strictly interior positive fraction.
Normalize both residuals by one common magnitude before dot products.
No damping floor, fitted constant or analytic plastic fixture seed.

The proposal is evaluated at the next already-budgeted outer iteration.
Before acceptance or publication, require the same actual residual decrease
or unchanged 1e-11 equilibrium criterion. Otherwise fail closed. Retain 24
updates, nine backtracks per update, the final evaluation, the 60-second
internal boundary and cancellation checks. No additional evaluation budget.
No caller state is committed by the internal solver.

Separate bounded rehearsal inventories:
- Secant unit/safety: 14 tests, including actual unchanged plastic input,
  scale invariance, inadmissible proposals and committed-origin protection.
- Existing local spectral prestress: three tests, unchanged.
- Existing native current-rest modal: 17 local and one engineering test,
  recorded separately; compare their science byte-for-byte to archive 281b53b.
- Existing generalized static: test_ge_beam3_native_generalized.py (whole file).
- Existing generalized restart: roundtrip_native_recovery and
  actual_continuation_unload_and_failed_step for its three registered fixture
  families. Keep these six tests as a separate inventory.

Only after these pass may N1/N2/N4/N8 prestress rehearsal resume under this
new freeze. Only after the full rehearsal passes may two fresh deterministic
cycles run. A failed invocation is never automatically retried.
Every worker: one numerical thread, 24 GiB tree, 600 seconds, 120 seconds CPU
inactivity; at most three workers and 1800 seconds per wave. Fresh exclusive
outputs, complete process-tree cleanup and immutable failure diagnostics.

Independent review remains PENDING. This is not production qualification.
Any failure blocks expansion; no public selector/default change.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
