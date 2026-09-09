# P5 finite-configuration full-inertia development

Base: `2c7455a37170d5c7fdc7ac5d794f443a14a1819e`, tree
`b0d9c19897e0ed87dafb5f836f0724f1c5507eb5`. Research preparation only. Keep
all existing source, mechanics, kinetic probes, accepted evidence and defaults
unchanged. Add this derivation, a finite-inertia probe and small unit tests.

## Scope and source distinction

The existing reference full-inertia model retains cell spins dynamically and
eliminates only exactly zero-inertia vertex traces. Its kinetic field has rank
15 on one free 24-coordinate macro, not a full-rank 18-coordinate nodal mass.
The previous Guyan approximation and coarse modal discrepancies remain intact.

This step extends the *same lifted configuration* to instantaneous finite
velocities/accelerations and inertial forces; no independent interpolated
velocity, trace inertia, mass floor or static spin elimination is introduced.
The one-field kinetic principle and convective inertial term are background
theory from Sonneville–Géradin, DOI 10.1007/s11044-022-09867-4, publisher HTML
sections 2.1, 2.3.1 and 2.4.1, equations (3), (7), (11), (16)–(17), inspected
2026-09-06: https://link.springer.com/article/10.1007/s11044-022-09867-4 .
We are **not** implementing that paper's two-field interpolation or claiming
its published verification for P5. No PDF equation authority is substituted.
The following curved P5 specialization is a repository derivation; independently
authored reconstruction/review remains required before qualification.

## Frozen preparatory derivation

Within each half, d0=r0-I(X), d=U d0, r=I(x)+d, Q=U R0.
All velocities and accelerations supplied here are spatial, with
Udot=hat(omega) U and omegadot=alpha. Vertex rotations have no direct kinetic
field. Local spins remain independent dynamic coordinates, not static solves.

```
v = I(v_nodes) + omega cross d
a = I(a_nodes) + alpha cross d + omega cross (omega cross d)
V = [Q^T v, Q^T omega]
Vdot = [Q^T a - (Q^T omega) cross (Q^T v), Q^T alpha]
[p,h] = J V
f_body = (J Vdot)_linear + omega_body cross p
n_body = (J Vdot)_angular + omega_body cross h + v_body cross p
```

J is the same SPD, coupled 6x6 material section-inertia contract as the
reference research model. Physical-section admission beyond that contract
is not claimed. The virtual motion map B gives [delta r,eta_cell], with
nodal translation columns I, cell translation columns -hat(d), cell angular
columns identity, and zero columns for the nine vertex rotation traces.

```
T = integral V^T J V / 2 ds0
M = integral B^T diag(Q,Q) J diag(Q^T,Q^T) B ds0
F_inertia = integral B^T diag(Q,Q) [f_body,n_body] ds0
```

Integrate over reference arclength. The convective force is quadratic in
velocity; acceleration enters affinely through M. Derive velocity and spatial
cell-rotation configuration Jacobians by the product rule, not differencing
frames. For a configuration direction eta, delta d=eta cross d and
delta Q=hat(eta)Q; nodal-position derivatives of inertia vanish for this lift.
For a velocity direction, differentiate both centrifugal acceleration and all
momentum cross products. Expose these as separate derivative blocks; do not
claim an assembled time-step/Newton algorithm or a symmetric dynamic tangent.

## Checks and limits

Small, single-macro tests: reference full-mass agreement, kinetic energy and
generalized momentum, affine acceleration identity, exact zero trace rows,
nonzero gyroscopic/centrifugal forces, rigid-motion/frame/reversal covariance,
power and linear/angular momentum rates, and analytic configuration/velocity
Jacobian directional checks. Use the existing 1e-11 normalized identities and
1e-7 directional checks. Finite differences are test-only independent checks.
Use coupled sections and straight/curved/twisted configurations. No heavy
wave or new resource request is needed for these small correctness fixtures.

Input validation is fail-closed, arrays copied/read-only, nonfinite outputs
rejected. No plastic history is modified. Finite kinetic energy is frame
covariant under a constant rigid observer transform; it is not asserted
invariant under an accelerating observer or arbitrary added rigid velocity.

Next requirements: independently review this derivation, integrate retained
dynamic spins and zero-inertia trace constraints in a transactional implicit
time integrator, establish energy/momentum and step-refinement behavior,
prestressed modal equations, restart and material parity. This step cannot
close these requirements or authorize production selection.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

## Implemented result and handoff

Added `ge_beam3_curved_p5_finite_inertia_probe.py` with instantaneous kinetic
energy, 24x24 retained-coordinate mass, generalized and total spatial momenta,
inertial forces, velocity derivative and spatial configuration derivative.
All derivatives are analytic product rules. The acceleration derivative is
the returned mass. No finite-difference routine is used in the implementation.

The focused suite has 22 checks (straight and curved configurations with
material roll and coupled inertia). The targeted run including existing mass,
modal-chain and immutable onset-closeout suites passed **57 tests in 6.99 s**.
The generalized virtual-action test perturbs the physical configuration and
its compatible spatial angular velocity, integrates kinetic energy independently
over time, and compares the action variation with inertial virtual work. Its
arbitrary local/nodal variations are stronger than rigid-momentum checks alone;
the fixture demonstrably rejects omission of convective inertia. This remains
same-author development verification, not independent scientific qualification.

The same-order reference full mass agrees within 1e-11. Coupled-energy and
spatial momentum integration, constant-observer covariance, proper reversal,
affine acceleration response and quadratic-velocity identity pass at the
existing normalized scale. Velocity/configuration and time/action directional
checks pass at 1e-7. Repeat evaluations are byte-identical and do not mutate
inputs. No whole-campaign deterministic qualification is implied.

The full 24-coordinate mass remains rank 15, with nine exactly zero-inertia
vertex traces. This is distinct from the three-dimensional mass kernel after
the previous 18-coordinate Guyan reduction. Neither kernel is filled with
invented inertia. Dynamic local-spin condensation must include inertia and
time-step history, rather than reuse the static local equilibrium solve.

The pure kinetic operator accepts proper finite rotations without a logarithm
branch. A future combined mechanics/time-step interface must additionally apply
the existing elastic/material chart and state guards; this module does not
weaken them. No dynamic state/restart codec or time integrator exists here.

No resource request, heavy run, publication, production/default update or
historical evidence mutation occurred. The accepted onset snapshot remains
unchanged. Continue with a bounded retained-spin implicit transaction path and
independent equation review; do not advertise finite-rotation dynamics yet.
