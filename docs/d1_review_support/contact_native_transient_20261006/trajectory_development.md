# Native trajectory controller - bounded development delivery

**6 October 2026. Implemented and selectively tested; C7 acceptance remains open.**

Public entry: `anysolver.ge_beam3_native_dynamics.solve_transient(analysis, config)`.
Example: `examples/native_contact_free_transient_dev.py`. Uses the existing native
SO3 midpoint/retained-inertia owner and `TransientConfig`; physical15 initial map,
atomic native origin preparation, disposable candidate accounting, complete controller/
native restart and work/momentum journals. Existing factories/profiles/equations/defaults
are unchanged. Scope remains one centered elastic generalized ellipsoid, free or
homogeneous full first-node clamp, admitted constant distributed loads; no contact.

## Evidence

- Installed workflow **3 PASS**: manual/two-step versus driver equality, full-grid split
  state/result/checkpoint equality, precommit cancellation and KeyboardInterrupt cleanup.
- Actual installed loaded clamped CLI: **1 accepted step**, completed at .001s.
- **545 package files and six metadata files** agree across source, held wheel and private
  installation.194 installed imports, errors0; JIT disabled, Numba1, observed pools1.
- Source analytic translation/SO3 and loaded controls passed before timeout. Saved free
  P/H defects4.46e-11/4.85e-11; clamped1.55e-8/6.61e-9 under separate .03N/.05Nm
  scales at .001s. Homogeneous support work0; constrained algebraic-frame couple retained.
- Source AST comparisons preserve31 original methods, factored native equations and
  original profile/default/factory nodes. Supporting independent source review is same
  model family, not engineering acceptance.

## Failures and limits

The full17-case new module did not finish. Source1 timed out after60.0649128s with
12PASS/2FAIL markers. Targeted loaded2 failed in2.4411633s because the example used
bareLinePattern. Its wrapper was corrected to existingDistributedPattern with identical
load values. The repaired subset timed out35.0687126s after3passing markers; remaining
cancellation/interruption checks passed installed. Full-suite PASS is not claimed.
Work dot-product is journal self-consistency; injected cutback is controller verification.
Precommit interruption tests do not cover the asynchronous postcommit publication window.
Existing finite-spin NONPASS, numerical gates and qualification boundaries are unchanged.
No complete C7/native impact/nonlinear energy-conservation/continuum accuracy or release claim.

## Identity and resources

Seven terminal jobs used **165.46361799992155/180s**, leaving14.536382000078447s
for this exact scope; no optional repeats. Peak observed170618880B under953MiB.
Private wheelSHA256 `1b90d1bd2f36614f5031b941ddfdbc54c29a73573eb64c316ec321b679fa47f7`.
Raw evidence: `C:/ANYworkspaceWork/contact_native_transient_20261006`, including final
manifest/worker handoff, exact executed snapshots and failed-fixture reconstruction,
job inputs/logs/resource/runtime/import records, root audits and source review.
[Current restart](../../../GENERAL_CONTACT_RESTART.md) gives ownership and all budgets.
