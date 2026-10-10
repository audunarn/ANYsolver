# Lead disposition - Q4/Q4 monolithic supported-force bending

8 October2026. Implemented and verified against the bounded development
criteria; engineering acceptance and release remain false.
Four product files extend existing admission and fixed-supported-force work.
The ordinary force adapter, semismooth solver, original bilinear geometry,
shared fineQ1 supports and full24-coordinate derivatives are reused.
No second driver, changed default, pressure-mode removal or law tuning.
Ru=Rstruct-D(w/S).T*z and C=z-max(0,z-c*w/S) use moving-support quotient
derivatives; c=regularization*full_reference_support is constant and positive.
Inherited pressure_tolerance is an admission/restart setting, not the C gate.

Independent Fraction Q1 work agrees to 6.938893903907228e-17.
Hard-contact reference uses G_free*K_free^-1*G_free.T without a penalty term;
structuralK is explicitly reused. Finite six-mode detection is not mesh-uniform
pressure stability. Actual nonlinear/linear discrepancy
1.965417431654545e-06 is reported without a1e-6 parity claim.
Full-run C/Fref=1.2911771464110076e-12 and equilibrium/Fref=
9.416990668789461e-15 pass frozen1e-8/1e-6 gates. Both bodies genuinely
bend and rotate under the declared linearized-director physical skin map.
Physical and structural-coordinate wrench gates pass with separate1e-4N and
1e-4Nm scales; the small-rotation moment deficit is reported, not suppressed.
Independent exact authoritative binary-pose gap meets50um. Full u/z coupled
directional checks meet1e-5 at two perturbations, including cross blocks.

The frozen alternate regularization2000 versus1000 gives stored u/z differences
0.0m/0.0N.
This is fixture-scoped scale invariance. Fresh active restart differences are
0.0m/0.0N,
binding passing full SHAd048f6524d491acf5a235001a1062bce24955f73707b5c7d95cace13e7af853b.
Provenance/enforcement/content incompatibility, public precancel and unsupported
routes are refused. Rejected-iteration accepted-candidate commit trap and
declared model repr checks concern this elastic route and no accepted increment;
they do not qualify general hidden material-trial rollback. Legacy Q4/S3
monolithic and Q4/Q4 penalty checks and public installed CLI are retained.
Two failed safety attempts were test-only message/field mistakes; both remain.

Lead rehashed629payloads/3286private
imports with zero discrepancies. Passing testcase invocations=8.
Wheel SHA92f5da4ab8c3ff5da72b380d2a5fd95b63ec74eba400f11b888a5fab88261eec. Exact commands, inputs, effective runtime,
process wall, memory, failures and all outputs remain in
C:/ANYworkspaceWork/contact_q4_pair_monolithic_20261008.
Q4_PAIR_MONOLITHIC_DEV600: 148.24805949999427/600s used,
451.75194050000573remaining,60final reserve protected/unused; no active job.
Serial<=60s/job953MiB,JIToff/Numba1/pools1. No performance claim from this new
force fixture and no renewal/pooling of any earlier execution allowance.

Next connected development check: cyclic force-controlled Q4/Q4 bending,
press/open/recontact and fresh restart while open, using the same existing
zero-control path owner. This tests the new profile's release/history boundary
without a new production driver or an open-ended refinement campaign.
Spatial/reference pressure stability, finite rotations, broad geometry,
nonlinear state and the full C0-C9 engineering acceptance remain required.
