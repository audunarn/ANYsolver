# P5 nonlinear section potential and station history — 2026-09-05

Author research successor to `62cbcb1cc95fb5134a9d4dfe03903bbabc19e14e`.
This prepares a nonlinear section/mixed-density protocol. It is not production
material behaviour, a fibre/J2 model, an integrated nonlinear beam or independent
qualification. Existing beam/shell mechanics and evidence are unchanged.

## Declared constitutive test law

The complete SPD 6x6 elasticity C and all six strain/resultant components are
retained. A supplied material-coordinate direction a defines plastic strain
`z*a`; p is accumulated absolute plastic increment. The direction is not
normalized, inferred from global axes or substituted for an isotropic yield
surface. Its scale and units are part of the explicitly supplied test law.

For frozen origin `(z0,p0)`, the incremental potential is the minimum over dz of

```
0.5*(e-(z0+dz)*a)^T C (e-(z0+dz)*a)
  + 0.5*H*((p0+abs(dz))^2-p0^2) + y0*abs(dz).
```

Here y0>0 and H>0. This gives an associative single-direction yield condition
`abs(a^T stress) <= y0+H*p`. The full-strain return increment is

```
d = a^T C (e-z0*a)
dlambda = max(0,(abs(d)-(y0+H*p0))/(a^T C a+H))
z = z0 + sign(d)*dlambda
p = p0 + dlambda
```

Stress is `C*(e-z*a)`. On a plastic branch its consistent tangent is
`C-(C*a)*(C*a)^T/(a^T C a+H)`; on an elastic branch it is C. Stored elastic/
hardening energy and nonnegative yield dissipation are recorded separately.
The branch tangent at exactly the yield transition is not a unique classical
second derivative; tests of smooth derivatives stay away from that transition.

H>0 makes the declared law strictly convex. Perfect plasticity, softening,
arbitrary flow surfaces and general fibre yielding are not admitted by this
probe. Failure of finite/SPD constitutive reductions raises an error; no
regularization, tangent clipping or coefficient tuning is applied. This
restricted test law exercises the protocol and does not narrow the full goal.

## Correct mixed density

The P5 mechanics require prescribed axial/shear strain gamma and moment m,
not prescribed complete strain. The partial Legendre density is
`min_kappa(phi([gamma;kappa];origin)-m^T kappa)`.

Writing C in blocks A/B/D and S=A-B*D^-1*B^T, the scalar plastic drive at
fixed gamma and m is

```
d_mixed = a_gamma^T*(S*(gamma-z0*a_gamma)+B*D^-1*m) + a_kappa^T*m
metric_mixed = a_gamma^T*S*a_gamma
```

The return increment therefore has denominator `metric_mixed+H`, not the
full-strain denominator. Recover curvature as

```
kappa = z*a_kappa + D^-1*(m-B^T*(gamma-z*a_gamma)).
```

For a pure bending plastic direction, `a_gamma=0`; hardening still makes
moment-controlled return well-defined. This case is tested explicitly.

The mixed gradient is `[N;-kappa]`. With the full consistent branch tangent
partitioned into Aalg/Balg/Dalg, the mixed Hessian is

```
[ Aalg-Balg*Dalg^-1*Balg^T,  Balg*Dalg^-1 ]
[ Dalg^-1*Balg^T,           -Dalg^-1     ].
```

The test cases have three positive and three negative eigenvalues, as required
by this partial transform of a strictly convex potential. Recovered strains
are checked by a separate full-strain return; moments, plastic history and
tangents agree at 1e-11. Directional potential/gradient checks use 1e-7.
This is not substitution of a plastic tangent into the frozen elastic F/H/J
formulas. Those formulas and the existing elastic probes are not modified.

## Station ownership and accepted-origin replay

`SectionStationProbe` owns one committed history and one pending trial.
Trials do not mutate committed state. Discard, stale/foreign/repeat commit,
mutated response arrays and invalid trials are checked. A canonical response
digest detects accidental mutation; commit recomputes from the current origin
and stores its own copy. This is not an adversarial in-process security boundary.

An accepted increment retains both its accepted strain and its *original*
history. Final-state replay recomputes from that origin. Evaluating the same
strain from the new committed history is a new trial, and may correctly have
an elastic unloading tangent instead. Confusing those operations loses the
accepted plastic algorithmic tangent even if stress is unchanged.

The explicit replay test uses axial C=4, H=0.5 and y0=0.125 at strain 0.5.
The accepted loading tangent is 4/9; a new same-strain elastic trial has tangent
4. Accepted-origin replay preserves the former while returning the same
accepted stress/history. Discarding the new trial does not alter the replay.

The station tests also exercise plastic loading, elastic unloading and reversal,
monotone accumulated plastic magnitude and nonnegative yield dissipation.
Material-frame re-expression and connectivity reversal transform the supplied
C/a/strain/resultants together; the scalar histories and work are invariant.

No persistence format or hot-restart interface is implemented here. Persisting
the constitutive model identity, station ownership and accepted origin, plus
atomic commit across all stations after global convergence, remains necessary.
This turn does not authorize replaying qualified Q4/S3 with a changed protocol.

## Tests and boundaries

- New focused suite: **16 passed in 1.46 seconds**.
- Existing thirteen P5 suites: **205 passed in 19.23 seconds**.
- Checks include potential derivatives, consistent tangents, an exact-rational
  scalar-return comparison, yield/dissipation, mixed return and Legendre
  minimization, pure-bending flow, covariance/reversal, station isolation,
  accepted-origin replay, mutation, invalid data and commit/discard semantics.
- Probe SHA-256:
  `CA0B1BAC5CEE2723AB0F3324AC0E1209B72B2B80527A680741963FD2DDB9F251`.
- Test SHA-256:
  `8D51FEFF72018655FD708AEAE1241DEED55B32901D886CB1581491F163A2384D`.

The constitutive potential and equations here are repository derivations and
same-author checks, not independently authored source/review authority. Only
this record, a research module and its tests are added. No production source,
API, existing B2/B3/Q4/S3, defaults, recovery, package metadata, dependencies,
workflows or accepted evidence was changed. No formal resource request,
qualification run, merge, release or activation was performed.

## Next work toward the unchanged goal

Couple the nonlinear mixed density and station-owned origins into the finite
beam's local rotation/moment equations, with analytic variations, consistent
Schur tangent, physical recovery and all-station transactional safety. Then
verify actual nonlinear beam loading/unloading and restart histories.
The present module alone does not provide those capabilities.

The extreme finite coupled equilibrium failure, dynamic policy/integration,
general nonlinear section adapters, curved/slender domain qualification,
prestress/buckling/postbuckling, independent review, installed-wheel exposure
and objective eccentric/curved beam-shell connections also remain open.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
