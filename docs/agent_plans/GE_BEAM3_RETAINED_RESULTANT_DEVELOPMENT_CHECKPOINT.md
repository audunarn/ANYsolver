# GE-B3 retained-resultant nonlinear development checkpoint

Status: **research progress, not qualification**. Independent review: **PENDING**.
Base: `4671d37ff3bd5bea6ab3d6c1a10d3506fbcbc039`, tree
`948f7d20e12340dc2a2436e5a7d4249f2db83680`.

## Failure diagnosis

The genuine two-macro V5 force tests use the unchanged curved geometry,
coupled section, tip load `(0.05,-0.001,0)`, and targets `(0.5,1)`.
L/h=100 passed. L/h=10000 failed its local line search and L/h=1000000
exhausted its local evaluation budget. Neither failure committed a target.
Their tests, local systems, last accepted capsules and logs are preserved.

The captured 18-coordinate internal linear systems were audited with
60/90-digit Decimal arithmetic. Improved linear solves alone do not remove
the local external-force-error estimate. Last captured evaluations are trials,
not necessarily the best accepted local iterate.

A separate first-step audit retained the common kinematic factor chain through
high-precision assembly and solution. Differences from the actual condensed
global step were 2.8034e-12, 4.2297e-8 and **0.01779587** at the three
slenderness values. The more accurate step still fails the local solve in
both high-slenderness cases. Thus global condensation accuracy and local
stationarity both require attention; changing only the global factorization
is insufficient. The L/h=100 audit intentionally stops after one global
iteration and is not a rerun of its complete qualification gate.

## Derived research alternative

The public mixed-beam background remains Humer--Steinbrecher--Pechstein,
[Mixed Finite Elements for Geometrically Exact Beams using Discontinuous
Rotations and Discrete Curvature](https://arxiv.org/abs/2605.04573), as already
bound by the P5 source programme. That paper introduces an independent
moment field through a partial Legendre transformation. The following
additional transformation is a **same-author discrete algebraic derivation**,
not a claim that the paper publishes or independently verifies this prototype.

For the existing integrated elastic cell functional, collect six common-cell
strain coordinates z and twelve endpoint moment coordinates m:

    Phi(z,m) = 1/2 z^T A z + z^T B m - 1/2 m^T S m.
    a = A z + B m.
    Psi*(a,m) = 1/2 (a-Bm)^T A^-1 (a-Bm) + 1/2 m^T S m.
    Pi(q,U,a,m) = a^T z(q,U) + m^T ell(q,U) - Psi*(a,m).

A, B and S are integrated from the same section Hessians, reference frames
and quadrature as V5. No new assumed-force interpolation, coefficient, strain
field or tolerance is introduced. Eliminating a recovers Phi+m^T ell.
The prototype verifies that elimination numerically at the potential,
uncondensed residual and Hessian, including a coupled section. It also checks
analytic first/second variations in a nonzero increment chart.

There are still 18 external nodal coordinates. This experimental retained
system has 6 cell-rotation coordinates, 6 independent cell-force coordinates
and 12 endpoint moment coordinates per macroelement. The two-macro solve
retains 78 coordinates before six root constraints. It uses the saddle
residual and analytic Hessian, rather than first solving local stationarity
and subtracting two dense Schur complements. Forces are independent unknowns;
they are not recovered by multiplying a very large section stiffness by a
rounded geometric strain difference.

This is **virgin elastic-interior research only**, not the finished element.
No native state is committed. Nonlinear section branches, distributed work,
unsupported supports and large rotation-chart increments fail closed. It
does not yet provide a native restart, physical recovery, load parity, mass
integration, arc length, production batching or independently reviewed API.
The module is not imported by production routing; it imports existing private
kinematic helpers for an equivalence experiment, so it is not an independent
mechanics checker.

## New evidence

All three retained-force specimens completed both targets in **three Newton
iterations per target**, with equilibrium and compatibility norms below
3e-14. L/h=100 tip displacement agrees with the previously successful V5
controller to about 3e-14 absolute in the observed components. This is not a
continuum/reference accuracy claim. Rotated geometry, loads, nodal/cell frames
and force/moment variables pass 1e-11 covariance checks at L/h=100 and 1e6.

Separate inventories, not a combined gate count:

- Original native force diagnostic: 1 passed, 2 genuine failures.
- Captured local linear audit: 4 passed.
- First-step audit: 4 passed (the recorded nonlinear trial failures remain).
- Initial local Legendre check: 4 passed.
- Initial retained-force check: 3 passed.
- Development smoke: 14 passed.
- Final research suite A: 19 passed, 8.407 seconds.
- Final research suite B: 19 passed, 8.369 seconds.

The final suites have **14 byte-identical JSON pairs**. Timings are diagnostics,
not a performance claim. These small correctness checks used one numerical
thread and consumed no resource request. The probe has a 120-second
cooperative bound, 12 Newton iterations per target and eight halvings; it is
not a formal process-tree watchdog. No formal authority or consumed request
was reused. A formal wave still requires the registered external runner.

## Preservation and next work

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-resultant-development-20260907-4bd7a55b75e7`.
Its 119 content files total 1,751,985 bytes. The additional archive manifest
is 39,102 bytes, SHA-256
`94d770281586812f7c84cea148035012ca9e4b728b7f38bfddefd7c0b28bf2b0`.
Every external content file was verified by byte count and SHA-256 in the
ordinary workspace context. Original temporary evidence remains. Preliminary
smoke reports are exploratory, not separately frozen authority; the final
source snapshot binds the two final suites.

Next: derive and independently review retained-resultant state/recovery and
complementary nonlinear sections; qualify rollback/restart and integration
with the native controller. Extend the bounded funnel to reversal/objectivity,
more geometries, finite bending, compression and continuation before broad
qualification. Full curved/slender convergence, modal/buckling integration,
nonlinear/fibre parity and objective eccentric/curved beam-shell joints remain
open. The earlier installed-wheel modal success is preserved, but does not
qualify this retained-resultant experiment.

Only new research, tests and checkpoint files are added. No existing tracked
file, B2/B3, accepted straight beam, Q4/S3 mechanics, default, alias, package,
workflow, dependency or production state layout changes. No push, release or
activation is authorized by this checkpoint.
