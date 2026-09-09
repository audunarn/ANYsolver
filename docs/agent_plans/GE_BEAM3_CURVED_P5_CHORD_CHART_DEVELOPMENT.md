# P5 retained chord-coordinate local solve — 2026-09-05

Development successor to `d68bc795224eb9edb44148a145c69e8fecdd513c`.
All earlier probes, their recorded failures, P3/P4 evidence, and production
mechanics remain unchanged. This is not a candidate freeze or qualification.

## Trace of the original finite solve

The unchanged original probe was instrumented through a disposable subclass
that recorded each local functional evaluation. The geometry was
`reference(0.6,0.2,0.15)`, section diag(1e12,1e12,1e12,1,2,3), and vertex
frames came from the existing `perturbed(ref)` helper. Two states were used:

- Original perturbed positions: 27 local evaluations before the bounded
  line-search failure. The best infinity-norm residual was
  5.112479490876343e-5; the corresponding Newton increment norm was
  2.5859643818075574e-8 radians.
- Positions constructed to preserve each chord length by rotations
  (0.12,-0.08,0.06) and (-0.06,0.1,0.08): 29 evaluations before bounded
  line-search failure. Best residual 3.6385424539764344e-5; Newton increment
  3.7081423456562885e-17 radians.

The latter trace supports a numerical representation/roundoff limitation:
the proposed update cannot reliably be retained in an order-one rotation
matrix. It does not prove that every high-contrast failure has that cause.
No timeout, tolerance override, automatic retry, or partial accepted response
was used. These were tiny development diagnostics, not formal resource runs.

## Equivalent local chart

The new research class `ChordChartLocalProbe` retains two transverse tilt
coordinates beta_y/beta_z and one axial spin phi for each half. B aligns
with the reference chord, and D aligns with the current chord using bounded
shortest transport from the original initial rotation. It represents

`U = D Exp([0,beta_y,beta_z]) Exp([phi,0,0]) B^T`.

With beta squared equal to beta_y squared plus beta_z squared, evaluate
`U^T d-c` from its exact chord identity instead of multiplying rounded
order-one matrices and subtracting nearly equal chord vectors:

`z_tilt = [delta_length - ld*cosc(beta)*beta_squared,
           -ld*sinc(beta)*beta_z, ld*sinc(beta)*beta_y]`.

Rotate this vector by the inverse axial spin and express it in B.
Here sinc and cosc use the unchanged shared analytic SO(3) derivative kernel.
The length difference uses `(d-c).(d+c)/(ld+lc)`. The original F/H/J
potential, endpoint logarithms, coupled section and internal distributed-load
work are retained. No numerical frame differentiation is introduced.

The exact chart-to-spatial virtual-rotation map is obtained from the analytic
matrix derivatives `axl(dU U^T)`. Convergence is checked on physical torque,
not merely a small chart gradient: the same absolute 1e-11 bound is used.
Newton systems use diagonal congruence scaling, with no stiffness alteration.
The limits remain 25 iterations and 12 backtracks. An inadmissible or failed
state raises an exception; no pseudo-inverse, regularization or fallback.

Authoritative local state consists of retained parameters plus chart data,
not just reconstructed U matrices. Discarding those parameters would discard
the small correction this calculation is designed to preserve.

## Results and remaining counterexample

For the original perturbed positions with uncoupled section
diag(rho^2,rho^2,rho^2,1,2,3), all four local solves now pass:

| rho | Iterations | Physical residual infinity norm |
|---:|---:|---:|
| 1 | 3 | 6.5630580346758225e-15 |
| 100 | 2 | 9.778732712303861e-13 |
| 10000 | 2 | 8.186910735451374e-13 |
| 1000000 | 2 | 8.152914982091672e-13 |

The two chord-length-preserving cases at rho=10000 and 1000000 also pass
the unchanged 1e-11 check in the new suite. Moderate coupled section and
distributed-load solutions agree with the original probe. Finite potential
and physical torque agree at nonstationary moderate states; first/second
directional checks pass at 1e-7 in a fixed chart. Superposed rigid motion,
reference-coordinate covariance, and reversal are tested separately.

Full coupled-section coverage is NOT closed. A separate diagnostic used
`C = scaling @ section() @ scaling`, scaling=diag(rho,rho,rho,1,1,1):

- rho=100: solved in four iterations, residual 2.4705164167865234e-13.
- rho=1000000: explicit `LocalStationarityError: chart iteration budget exhausted`.

Both commands were bounded and executed once for this diagnostic. No extra
iterations or relaxed tolerance were applied. The high-contrast coupled case
remains a required development failure, not an excluded qualification case.

## Verification and limits

- New local-chart suite: 12 passed in 2.62 seconds.
- Existing algebra/finite/QR/flexibility suites: 69 passed in 3.51 seconds.
- Implementation SHA-256:
  `07C2BAEF74DB633734F27A74297B4F0F01313DC474A4BA36D20A7ECBE4AA547C`.
- New test SHA-256:
  `9D070ACCD7FDAC3B01AA390DCAA5D29C88019383182EB82F6823BE70631433ED`.

The shared derivative kernel is NOT an independent oracle. No independent
high-precision finite solution or scientific review is accepted by this note.
This class supplies local equilibrium only: no external residual/tangent,
physical recovery, persistent state/restart, load-history sections, mass,
modal/buckling, factory or installed-wheel interface. It must not be wired
into a production element as if those obligations had been met.

Next: inspect the remaining coupled/anisotropic high-contrast failure without
shrinking section coverage. Investigate force-equilibrated coordinates or
an equivalent scaled force/moment mixed system as indicated by that trace.
After the local solve works across the intended section family, derive
external variations of the retained chart and recovery/state transport;
simply passing reconstructed U to the earlier evaluator is insufficient.

All work remains research-only and local. No formal request, freeze, run,
merge, release or activation was created. The full goal remains active,
including curved/straight nonlinear sections, engineering qualification,
postbuckling, dynamics/restart and objective beam-shell joints.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
