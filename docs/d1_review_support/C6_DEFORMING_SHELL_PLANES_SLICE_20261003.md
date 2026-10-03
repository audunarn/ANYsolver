# Deforming shell and shared event-front slice — 3 October 2026

**Disposition:** development, implemented/source/installed-tested. No engineering
acceptance, release or application admission. Candidate parent `13ff3156`;
[exact changed-source hashes/environment/commands](contact_c6_deforming_shell_planes_20261003/source.json),
[retained raw 56-record archive](contact_c6_deforming_shell_planes_20261003/raw.zip).

## Mechanical discriminator

Four planar Q4 strips use constant manufactured MPCs (w=a+bx), other coordinates
zero. Independent integration of the admitted MITC shear, von Karman membrane and
consistent physical inertia gives M=diag(0.05,0.05/12) and
U=801.282051282b²+686.813186813b⁴. Local b=0.08/−0.13 checks resolve the quartic
force/tangent. Actual pressure-hat integration gives outer weighted x=5/12.
One Q4 fails the 5 µm physical-gap activation preflight; four strips pass.
No unsuitable coarse whole route was launched or regularization softened.

The asymmetric impact exercises both wall reactions sequentially. Its independent
two-mode Newmark oracle uses no production contact, structural or geometry calls.
It verifies equations at the actual accepted grid, not independently correct
event times or continuous accuracy. Full q/v/a reconstruction also verifies MPCs.

## Bounded failures and selected correction

1. Initial dt20 µs run exhausted the unchanged 128-stage event budget at
   t=0.00137304384 s (44.25 s / 191,709,184 bytes).
2. One halving discriminator at10 µs failed at the same event neighborhood,
   t=0.00137343815 s (44.88 s / 197,107,712 bytes). Smaller steps alone did not fix it.
3. Source inspection identified per-row endpoint bisection repeating full-vector
   equilibrations. A new explicit batched-front candidate shares those evaluations.
   A 12-row linear-family test exhausts the old64-query limit; the new candidate
   resolves its earliest root within40 queries at the same limit.
4. The candidate completed the route and matched work/response, then failed an
   additional simultaneous-contact assertion. Actual asymmetric motion makes
   contacts sequential. Retain that failed result. The prospectively scoped
   deforming fixture now requires both named wall contacts, with no change to
   mechanics, tolerances or caps. Prior simultaneous evidence is not replaced.

The default per-row route remains selected for existing callers. New controls
require the multiple-Q4 plane-event profile; true selection and algorithm revision
are restart-bound. No switch occurs inside a failed increment. All required-row
brackets, initial phases, omitted crossings and both stopping tolerances are
preserved. Hidden nonlinear endpoint reentry still requires the caller's full
reequilibrated path checks; this is no conservative nonlinear-family certificate.

## Verification actually performed

59 scoped pass outcomes: two local structural/contact checks; 50 affected helper
checks (46 old, four new); five small control/restart-identity checks; one repaired
whole-route work/response test; one active split-restart/algorithm-change rejection.
No full suite replay. All runs recorded JIT off, NumBa and BLAS one thread, actual
owned source imports, terminal180 s / 953 MiB resource status.

Read-only same-family scrutiny independently derived the structural reduction,
checked the fixture and front equations, and requested full-coordinate reconstruction
and narrow control/restart tests, which pass. It found no concrete source defect.
This is supporting scrutiny, not an independent engineering acceptance decision.

190 saved states, 12 reported events, zero cutbacks, 228 endpoint requests and890
stage evaluations. Maximum independent q/v/a discrepancies2.18e-16 (m/slope),
2.54e-12 (m/s,slope/s),3.45e-7 (m/s²,slope/s²); maximum modal force/moment residual
2.55e-10 on this unit-square fixture. Body force/moment errors2.56e-10 N/4.70e-11 Nm.
Maximum energy defect6.06e-7 relative. Independent represented physical minima
lower−0.508410943 µm, upper−2.127221672 µm, within5 µm; reported-bound discrepancy
4.17e-19 m. Tiny impact membrane energy does not establish its accuracy.

Repaired complete test58.44 s /183,926,784 bytes; active split-restart test17.66 s /
182,759,424 bytes, including runner overhead. Source/isolated installed example
matches205 imported hashes/all numerical fields. WheelSHA
`a34c45632767800cc83877ef705dc65ee433732b7e164bb219c96f9d9e9c21b2`.
Source51.00 s /161,550,336 bytes; installed50.74 s /162,250,752 bytes. These are
single runs; failure-to-completion is measured progress, not a twofold speed claim.

## Remaining boundary / next action

Only exact elastic guided planar-reference Q4/fixed planes and supplied-float
represented paths are covered. No temporal/spatial convergence, unrestricted
deformation, nonlinear membrane impact accuracy, descriptor/free-body/friction,
plastic multiple pairs, deformable-target impact or broad D5 acceptance. Next
reuse the verified static shell-pair contributor in a bounded dynamic pairing,
fixing both-body work, physical mass, geometry/path admission and restart identity
before expansion. No cap growth or further dt campaign without a discriminating gap.
