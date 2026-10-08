# Connected moving-front work integration — development pass

Explicit open-endpoint helper now integrates a stationary contact-appearance boundary.
The uncertainty strip has a conservative discrete-work enclosure; its midpoint is the
integral estimate and half-width adds to absolute work error. No recovered point history
is fabricated. Strict open endpoints make residual/tangent/storage zero, not accumulated
D/release. Present bound admits one captured released-origin segment/one stationary branch.

Penetration <= maximum chord norm times strip width plus arithmetic allowance; full-frame
objective-slip variation includes normal AND first-edge rotation. D<=C*(slip+2*n*C/kt),
release<=C^2/(2kt). Source review required denominator error subtraction/numerator padding;
implemented. Independent scalar tiny-pulse work is bounded (1focused pass).

Whole-angle branch proofs are bound to field/cell/segment/angular interval and reused in
per-angle root isolation. All new slabs consume the existing shared support budget.
Mixed4/8 directional quadrature estimates choose refinement direction. Initial wiring
applied the choice to support rather than quadrature; diagnostic identified this and
correction preserved the original support splitting rule. Failed cap runs retained.

Final connected test PASS: independent scalar32-step Coulomb law integrated by SciPy quad
through pulse-appearance xi=-.5; error <=max(1e-12J,1e-5relative), positive dissipation,
zero endpoint residual. Existing integrator tolerances/caps unchanged. Test70.46s,
pytest74.22s, runner75.6385s, sampled peak234139648bytes, limit953MiB/180s, JIT off.
No whole-route speed claim. Scalar reference values were asserted but not separately
exported; stdout/selection/runtime/resource evidence retained in raw.zip.

Still development: Gauss difference is an estimator, not rigorous smooth-region error.
Extreme-scale and nearly degenerate geometry controls remain before qualification.
No owner/restart admission, engineering acceptance or release. Actual saved second-load
patch has multiple segments and closed endpoints; this passed helper does not admit it.
Next extend physical event composition/derivatives for closed-ending histories and multi-
segment work accounting before attempting that full patch. Do not silently apply the
zero endpoint force/tangent argument outside strict open endpoints.
