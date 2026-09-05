# P5 current-chord spin and bounded failure — 2026-09-05

Author research successor to `13b2b409bc8052257efe53603b070882a06b8d1b`.
Prior implementations and evidence remain unchanged. No qualification,
candidate freeze, production integration, resource request or formal run.

## What the coupled trace established

The previous chord-chart experiment was traced at the preserved extreme
case: reference(0.6,0.2,0.15), original perturbed positions and frames, and
section `scaling @ section() @ scaling`, scaling=diag(1e6,1e6,1e6,1,1,1).
It made 221 local evaluations within its existing 25-iteration/12-backtrack
bounds and failed by iteration exhaustion. Best physical residual was
1.4748259056452582e7, not a near-tolerance roundoff residual. The initial
Hessian had two negative eigenvalues of about -1.42e8 and -8.57e7; the best
iterate retained a negative eigenvalue of about -2.69e4.

Therefore the earlier uncoupled roundoff diagnosis cannot simply be assigned
to this coupled case. The coordinate map itself mixes spin with the force
strain when the transverse tilt is nonzero, creating strong off-diagonal
Newton terms away from equilibrium.

## Equivalent current-chord spin

The new `CurrentChordSpinProbe` changes only the order of the local factors:

`U = D Exp(phi e1) Exp(beta_y e2 + beta_z e3) B^T`.

Because the first axis of D is the current chord, the axial spin preserves
that chord exactly. Force strain is independent of phi for arbitrary F,
including anisotropy; moment coupling, endpoint logarithms, load work and
the scalar potential remain intact. A dedicated component-algebra test
checks exactly zero force-component spin gradient/Hessian. Its temporary
moment-component ablation is only a unit test, never a solved or qualifying
mechanical model.

For the extreme case, the initial Hessian in these coordinates is positive
definite (smallest eigenvalue about 9.58), but that alone does not establish
an admissible stable solution. An intermediate disposable diagnostic without
the new chart bound took spin steps of many turns. Endpoint principal-log
checks can accept such endpoints after wrapping, despite the step crossing
the chart boundary. No such result was formally accepted or published.

The committed successor rejects axial spin at or beyond +/-pi before
evaluation. The separate existing 0.9*pi endpoint relative-rotation guard
remains unchanged. This is an explicit local-coordinate restriction, not a
claim that these two angle bounds are equivalent. A multi-turn step cannot
silently reappear as an admissible endpoint. Failed searches still return
an exception, with no accepted partial state.

## Bounded profile of the unresolved extreme case

Nine spin values from -2.5 to 2.5 radians were inspected, with at most eight
transverse Newton updates per value. Both spin derivatives remained negative
at these sampled values:

- First cell: approximately -1405.52 to -1304.00.
- Second cell: approximately -20141.08 to -18239.99.

The transverse residuals in this binary64 diagnostic were of order 1e-5,
not accepted stationary solutions. These samples suggest persistent driving
toward the chart boundary, but DO NOT prove the absence of an interior
stationary point or exclude the case from qualification. No tolerance,
section coupling, coefficients, or earlier failure classification changed.
The original extreme case remains an explicit bounded rejection in the new
unit suite, not a passed scientific case.

## Additional coupled deformation states

To distinguish all high-contrast sections from this particular prescribed
state, additional tests scale both translations and nodal rotation vectors
by amplitude=1/rho, while retaining the full coupled section at contrast rho.
This is a declared additional test family, not a replacement for the original
amplitude-one case and not a production amplitude admission rule.

| rho | Amplitude | Iterations | Physical residual infinity norm |
|---:|---:|---:|---:|
| 1 | 1 | 3 | 5.890727558246974e-15 |
| 100 | 0.01 | 2 | 3.526073390958962e-13 |
| 10000 | 0.0001 | 2 | 5.419376332575705e-13 |
| 1000000 | 0.000001 | 4 | 2.698909503365527e-12 |

All meet the unchanged absolute physical residual bound of 1e-11, with
positive local Hessians. This demonstrates local solutions for additional
coupled states; it does not establish the full section/admissibility domain,
locking performance or the validity of rejecting the original extreme state.

## Tests and boundary

- New focused suite: 14 passed in 2.29 seconds.
- Existing five P5 suites: 81 passed in 4.67 seconds.
- Tests cover coupled states, exact force/spin separation, same-potential
  value/physical torque, analytic directional derivatives, distributed-load
  work, superposed rigid motion, reference-coordinate covariance, reversal,
  principal-spin guard, original-case rejection and input preservation.
- The test that expects rejection proves failure safety, not qualification.
- Probe SHA-256:
  `75209EA7938513846E8BC5DF5AB71BFC014BDB892C80D950B0D9B71B9E5C2D3D`.
- Test SHA-256:
  `F889CC39BCAC5E606750408F2BA62F85335A1B5E3AE6D251C50BFF48AE89C0C6`.

The shared derivative kernel and author reconstruction are not independent
scientific review. The class is still a local research solve, not external
residual/tangent, recovery, state/restart, mass, factory or package support.
Existing B2/B3, Q4, S3, defaults and accepted P3/P4 evidence are unchanged.

## Next work toward the full goal

Determine the admissible equilibrium/load-cutback behaviour of the original
coupled extreme state with a separately checked continuation or domain
analysis. A sampled derivative sign is insufficient to declare it outside
the admissible formulation. Do not relax the tolerance or remove that case.

Also derive external variations and recovery from the retained current-chord
coordinates for successful states. Reconstructing only rounded U and calling
the old finite evaluator discards the numerical benefit. Full load-history
state, curved engineering qualification, dynamics/buckling, installed-wheel
exposure and objective beam-shell joints remain required.

The overall goal remains active and incomplete.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
