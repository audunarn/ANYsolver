# Partially supported S3 target: tangent development slice

The accepted 24-Q4 distributed pose is reused as a kinematically admissible
configuration after replacing the target's full clamp with a left-edge clamp
on S3 nodes 51 and 54. Target nodes 52 and 53 become free, raising the
reduced coordinate count from 98 to 110. This saved pose is **not shown to be
equilibrium** for the new support configuration.

The initial [development report](../../reports/general_contact_d1_free_target_tangent_dev_20260927.json)
(SHA256 `f7a4c9f22546a6b64c47de4fd9fcd173bc046968df5365a6ef38a8797056e370`)
perturbs uz at nodes 52 and 53 by equal weights. It compares a negative
one-sided force difference with the analytic assembled tangent, keeping the
saved 50 multipliers fixed. The contact-only action is isolated by subtracting
structural-only assemblies at the same poses. All 48 overlap-pair signatures,
pressure active masks, support masks and overlap signatures remain unchanged.
Coupled errors at h=1e−6 and 5e−7 m are 3.834e−7 and 1.917e−7;
mapped-contact errors are 3.847e−7 and 1.923e−7. The contact action is
704.30 N/m in the original combined-row norm.

Independent read-only review confirmed the support change, direction and
derivative signs, contact subtraction, fixed multipliers and trial discard.
The first report preceded the later instrumentation that reports force and
moment rows separately. Because forces and moments have different units,
the combined-row norm is development orientation only. A distinct direction
with separate force/moment checks is needed before a claim-bearing decision.
