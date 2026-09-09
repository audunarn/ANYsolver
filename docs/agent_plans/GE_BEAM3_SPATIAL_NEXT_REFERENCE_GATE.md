# Separate continuum reference at the continued signed endpoints

Parent 5e3b9d37026a68e56b16320d145750c219a4c781. Bind the completed precise
continuation archive manifest
b7bcc4a9e513050a42b1542b081ba3c8ed22ff108044a6b5cdbb15586746cfac,
its exact signed checkpoint/recovery hashes and the original N20 +/-0.006
initializer records through their established hash-checking loader.

Create a successor wrapper for targets +/-0.0065; do not change the old continuum
case inventory or source. Frozen ge_beam3_spatial_continuum.py SHA-256
2f3c960cf0dfda2b62d2e3e0073533ee390e1c5e3af993758aa808f64401f1b9.
Reuse unchanged rod equations, material C, reference geometry/frames, physical
boundary conditions, segment force jump, sampling, energy integration and
non-collocation validation. Old N20 fields are Newton initial guesses only; the
new N24 fields do not define the ODE, a target response, or the expected solution.

BVP9: tolerance1e-9, boundary1e-11,4097node cap,60seconds and2000callbacks.
Require boundary error<=1e-11 and normalized differential/quaternion errors<=1e-8
at the two interior Gauss sites of every actual collocation interval. Verify
64/128point energy integration agrees relatively<=1e-8. No generic projection
or normalization is used to conceal a consistency failure.

Compare both actual continued endpoints:49nodes and192stations. Preserve the
four existing engineering definitions and2% limits: load, normalized nodal
displacement, resultant energy norm, and strain energy. Explicitly validate
station identities, maps, finite fields and positive measures. Save the complete
52-field piecewise cubic polynomial, not only a plotting grid, for later spatial
stability work. Verify values and derivatives round-trip byte-exactly. Frozen
binary64 reference is not an interval or multiprecision certificate.

Positive smoke first; if it passes, run negative and both signed replicas in
three concurrent fresh processes. Require same-sign comparison bytes identical.
Guard before scientific imports and again after computation; exclusive external
output; partial/failing diagnostic separate from accepted comparison; no automatic
retry. Each process one numerical thread,600seconds,24GiB; max3concurrent,
1800second wave and existing120second CPU inactivity watchdog. No mechanics rerun.

Tests cover complete polynomial roundtrip, domain/shape/nonfinite mutations,
registered target rejection, native input binding, exact192station coverage,
field/map mutations and absence of ANYsolver imports in the reference equations.
Independent author review remains pending. This establishes engineering reference
agreement at new endpoints only, not spatial stability, branch uniqueness, loading
from rest, broader qualification, public selection or beam-shell connections.
Existing B2/B3/S3/Q4 mechanics, defaults, APIs, packages and versions unchanged.
