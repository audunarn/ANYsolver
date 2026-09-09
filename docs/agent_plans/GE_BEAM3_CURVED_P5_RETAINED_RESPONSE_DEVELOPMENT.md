# P5 retained-coordinate elastic response — 2026-09-05

Author development successor to `7c1479987477edfa34168184996379f58a31beb2`.
Earlier probes and evidence are preserved. This is not a production element,
candidate freeze, independent review, or formal qualification result.

## Implemented response

`RetainedFiniteResponseProbe` now computes the external 18-component residual
and 18-by-18 condensed energy Hessian from the same potential as the local
current-chord-spin solve. It retains six internal tilt/spin parameters instead
of reconstructing strain from rounded local rotation matrices.

The external chart is `x=x_base+du`, `Q=Exp(dtheta) Q_base`. Local charts may
be rebuilt at a trial state, but external derivatives keep the caller's base
chart, including at nonzero increment. The shared Jet2 kernel differentiates
both the current chord length and its shortest transport from the local
anchor, along with the endpoint rotations and distributed-load work.

For chord increment h about d0, the length increment is evaluated as
`(2*d0.h+h.h)/(sqrt(ld0^2+2*d0.h+h.h)+ld0)`. This is exactly zero at the
anchor without subtracting nearly equal square roots. The transported unit
direction increment is `(h-axis*delta_length)/ld`; shortest transport uses
its cross product with the anchor axis. These are algebraic identities in
real arithmetic. No finite differences, derivative/value overrides, empirical
stiffness terms or altered section coefficients enter the implementation.

The local solve still checks absolute physical torque at 1e-11, with the
existing 25-iteration/12-backtrack limits. A full-chart/local agreement check
uses the existing 2e-11 cross-check bound. Only after these checks does the
method return a response. The original extreme coupled state still fails
explicitly and creates no response.

## Recovery and configuration binding

Recovery evaluates force strain from the retained chord coordinates and
material endpoint moments from H^-1(Jz+ell), then obtains physical curvature
through the elastic section compliance. It does not reconstruct force strain
by multiplying rounded U^T d and subtracting c. Both resultants and their
current spatial frames are returned.

The diagnostic response binds reference coordinates/frames, section, base
configuration, distributed load, integration order, retained parameters and
external increment with a SHA-256 configuration fingerprint. Recovery rejects
changed active inputs, parameters, increments or inconsistent rotations, and
rechecks stationarity. This hash is an integrity binding, not authentication
or an accepted canonical evidence/restart format. Unused response fields are
not certified by it. No persistent load-history state, trial/commit/discard,
serialization or hot-restart interface is supplied.

## Verification actually performed

- New focused suite: 13 passed in 4.23 seconds.
- Existing six P5 development suites: 95 passed in 5.55 seconds.
- The new suite compares the straight limit directly with the accepted P3
  potential/residual/tangent, and moderate curved responses/recovery with
  the original finite probe, including spatial dead distributed loads.
- Directional energy/residual and residual/tangent checks use 1e-7 in a
  fixed external chart, both at zero and nonzero increment.
- Superposed finite rigid motion, reference-coordinate covariance, reversal,
  loaded work, high-contrast response construction, recovery, deterministic
  repetition, state-binding mutation and explicit failure are tested.
- Force/moment balance checks at high contrast use the unchanged normalized
  1e-11 invariant tolerance. They do not substitute for small-mode accuracy.
- Additional reciprocal-amplitude coupled states remain additional cases,
  not replacements for the preserved amplitude-one extreme failure.

For a moderate curved diagnostic, differences from the earlier finite probe
were zero in potential, about 1.52e-14 normalized in residual, and 8.55e-16
normalized in tangent. Agreement between author implementations sharing the
derivative kernel is NOT independent scientific qualification.

## Explicit remaining dense-tangent conditioning failure

At the stress-free reference state, with section diag(1e12,1e12,1e12,1,2,3),
the same constant-spatial-moment diagnostic was contracted against the new
dense tangent. Expected energy remains sum(m^T H m)/2. Relative errors were:

| Geometry (height, shift, twist) | Dense tangent energy relative error |
|---|---:|
| (0, 0, 0) | 6.90294e-16 |
| (0.4, 0, 0) | 9.23533e-7 |
| (0.6, 0.2, 0.15) | 1.10004e-6 |

Thus the new retained response does NOT close high-contrast small-mode
accuracy. Passing a directional check normalized by a large stiffness norm
cannot establish accurate small bending-energy contractions. The earlier
reference-flexibility calculation remains the accurate energy diagnostic;
the current dense response must not be represented as equivalent in numerical
conditioning. No threshold or case has been changed to hide this issue.

## Provenance and next work

Probe SHA-256:
`1200C45D97C0A21FA617E4BDDBC8F9BC4B40D8B32599B62FA0DC3D524DF6B8D3`.

New test SHA-256:
`568EF2AB2948808D34D51E30D7196AC8ABABA120CE91BA4E4A273F2A0DAA6997`.

Next: implement and verify a factored/structured tangent application that
preserves small-mode accuracy, with separate high-precision comparisons for
energy and force action. Do not begin assembled thin-beam qualification on
the strength of the current dense tangent. Continue the admissible
equilibrium/cutback investigation of the original extreme coupled state.

Independent equation/source review, quadrature and engineering references,
nonlinear section history, mass/modal/buckling, restart, installed-wheel
qualification and objective beam-shell connections remain required. No
production source, existing B2/B3/Q4/S3 mechanics, defaults, package metadata
or workflow was changed. No formal request, run, merge or release was created.
The full goal remains active. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
