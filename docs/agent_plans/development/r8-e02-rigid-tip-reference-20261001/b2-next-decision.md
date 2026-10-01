# B2 resolution obstruction — next bounded numerical decision

Separate Read-only reviewer inspected the retained scalar trace and actual
panel/batch source. No edits or numerical execution. The global8.326e-9 floor
estimate exceeds the existing1e-9 explicit-load cap; it establishes neither
accuracy nor inaccuracy of the returned solution. Do not rescale loads or tune
the unloaded stub to obtain admission.

Next discriminator: certify the failed candidate's compensated **unscaled**
stored-KKT residual against each active primal row's unchanged
`1e-9*abs(projected explicit load)` cap. Restrict this first investigation to
zero prescribed offsets and a pure unit-coordinate selector. Reduced entries,
projected load and restored coordinates then copy stored values without affine
cancellation. Preserve compatibility, finite/representability, physical
equilibrium and backend-failure checks independently.

Use the existing accurate sparse residual and bounded same-factor correction
facilities; do not create a new framework or substitute a global residual norm.
If the candidate fails, one correction must still satisfy every original cap.
No compensation pass establishes forward displacement/element rounding or E02
physical accuracy. A general affine/nonzero-offset extension is a separate
problem because `applied-Ku0` may already have erased the load.

Required rejection controls before a product fallback:

- Zero returned solution for nonzero1e-12 load: residual exceeds its1e-21 cap.
- Large and tiny loads where the tiny response is silently dropped: assess
  every explicitly loaded row, not the largest load or a global norm.
- Cancellation hiding a unit term in1e16+1-1e16, and the retained many-small-
  terms control in test_b2_f13_affine_batch_dev.py.
- Nonzero offsets or a non-selector T remain ineligible for this narrow route.
- Nonfinite/nonrepresentable products, failed compatibility and actual backend
  failure must remain numerical non-success.

Only a successful discriminator and counterexample checks justify implementing
the narrow rejection seam in the existing panel owner. This is a prospective
development decision, not acceptance of a fallback or altered tolerance.
