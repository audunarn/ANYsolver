# Generalized virgin-factor slenderness diagnosis

Base 1ab903d88405aa30bf4e58cbc29e892bf24e226a, tree
0a44db5b2a7574c9b820e186119a2dd04cc7b5a0. Three research-only paths:
this plan, ge_beam3_generalized_virgin_chain.py,
test_ge_beam3_generalized_slenderness_diagnostic.py. No production edits.

## Purpose and algebra

The accepted development modal-group gate does not cover extreme contrast.
The current generalized-material path expands a dense moment-Schur matrix.
At a virgin state its 42-coordinate Hessian has blocks [[0,J.T],[J,-S]]
on 24 nodal-plus-cell coordinates and 18 generalized resultants. Require
zero residual, exactly zero geometric block, symmetry and positive S before
forming L=chol(S)^(-1). The reference energy is ||L J q||^2/2. Retain L,J
separately when auditing supplied binary64 inputs. Do not substitute a virgin
tangent at a loaded/plastic state. This audit does not reconstruct independent
mechanics: it diagnoses rounding after native Hessian construction.

Use the existing standard-library Decimal chain audit at 80 and 100 digits,
with exact float conversion, full physical coordinate map, shared algebraic
trace elimination and physical kinetic factor. Require audit eigenvalues
to agree to 1e-40 normalized by max(1,abs(root)), and positive clamped roots.
This is precision convergence, not certified intervals or independent review.

## Frozen specimens

One macroelement, nodes at t=-1,0,1; straight or y=.2(1-t*t). Physical frame
columns tangent, global z, tangent cross global z. Both original coordinates
and common proper rotation Exp([.4,-.3,.2]) are evaluated.
Slenderness parameters rho=100,10000,1000000; nominal length2, h=2/rho.
EA=3*rho^2. Define D=diag(sqrt([EA,EA/3,EA/3.5,2,1,1.5])),
B=I with B03=.02,B15=.03, and elastic C=(B D).T(B D).
Generalized ellipsoid section uses metric I, yield1e6, hardening1; virgin
elastic only. Physical section inertia is diag(2,2,2,5h^2/12,3h^2/12,2h^2/12).
This is a frozen nominal slenderness/coupling diagnosis, not a rectangular
isotropic material specification. Clamp node1, retain physical cell inertia,
and eliminate exactly the remaining six massless nodal rotation traces.
Kinetic quadrature is24, native stationary quadrature4, both unchanged.

Record raw Hessian high/low, compliance, factor chain, kinetic factor,
80/100-digit spectra, current native pencil and returned roots or typed
rejection. Compare first six sorted squared frequencies at1e-11 relative to
max(1,abs(reference)); record genuine failures, never clip eigenvalues.
Any native failure or discrepancy is an observation, not a passed engineering
gate. State must remain byte unchanged. Unexpected exceptions/timeouts fail
the process. No altered coefficients, mass floors or threshold relaxation.

## Execution and decision

Local inventory: seven boundary/decomposition tests, seven scientific files.
Then three parallel rho inventories, one test each, four specimen observations
and one diagnosis; raw record count depends on whether native preparation
or eigen solving rejects. Every omission must be explained by its observation.
These are one-shot nonclassifying diagnostics, not deterministic qualification
cycles. No repeat or historical request reuse is authorized by this plan.

Use clean frozen HEAD, one numerical thread, 24 GiB process tree,600 seconds
per child,120-second CPU inactivity; at most three concurrent and1800 seconds
per wave. Decimal audit additionally retains its120-second invocation and
100-Jacobi-sweep bounds. Preserve all terminal/partial outputs externally.

Success means DIAGNOSTIC_OBSERVATIONS_COMPLETE only. Interpret observations
before designing any corrected numerical path or broad slenderness gate.
Historical accepted/failed gates and the full production goal remain intact.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED; independent review PENDING.
