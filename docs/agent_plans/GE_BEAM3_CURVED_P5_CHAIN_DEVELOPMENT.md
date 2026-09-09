# P5 small assembled reference-chain checks — 2026-09-05

Author development successor to `1281d568983c164665b77f2d741b426b59c3f942`.
Earlier code, failures and P3/P4 evidence remain unchanged. These are tiny
linear reference-state diagnostics, not assembled engineering qualification.

## Scope and assembly

`ReferenceChainProbe` supports only one or two conforming three-node macro
elements, with the first node clamped in all six DOFs. It checks shared
reference node/frame identity. The two-element test subdivides the existing
height-0.4 curved reference into four half cells, five nodes and 30 external
DOFs. The tip load contains all three forces and three moments:
`[0.2,-0.3,0.1,0.03,0.02,-0.04]`.

The dense reference tangent is used as a preconditioner, not as the final
force operator. Iterative refinement recomputes reactions/residuals using
the selected structured action, with at most 12 corrections and the unchanged
normalized residual bound of 1e-11. A failed solve raises an exception and
returns no accepted partial solution. This iteration is not a retry of an
external resource request; no resource request or formal run was created.

## Retained displacement expansion

The solver keeps each displacement as a high and low binary64 part, using
error-free two-sum updates. These are two numerical parts of the same DOF,
not additional physical unknowns. The action consumes both parts; collapsing
them into one array before force evaluation loses the benefit.

Observed uncoupled two-element results, section
diag(rho^2,rho^2,rho^2,1,2,3), using the directional backend:

| rho | Corrections | Retained free residual infinity norm | Collapsed residual |
|---:|---:|---:|---:|
| 1 | 1 | 3.19744e-14 | 3.19744e-14 |
| 10000 | 2 | 9.04628e-15 | 1.78388e-9 |
| 1000000 | 3 | 4.86488e-15 | 9.20152e-6 |

At the highest contrast, the norm of the retained low part was approximately
4.28e-17. Discarding it causes a significant equilibrium error despite an
apparently unchanged displayed displacement. Production state/serialization
and nonlinear geometry updates do not yet preserve this representation.

## Coupled case and explicit precise backend

The complete coupled section `scaling @ section() @ scaling`, with
scaling=diag(1e6,1e6,1e6,1,1,1), initially failed the same chain test using
the directional backend. Free residual norms fell from 0.3 to 1.15e-4,
7.14e-9 and then fluctuated around 1.42e-11 to 4.34e-11 before the existing
12-correction bound was exhausted. The initial focused run was three tests
passed and one failed. No tolerance or case was changed to hide that result.

The same coupled test now explicitly selects `decimal-flexibility`.
`PreciseReferenceAction` compiles each half-cell's six equilibrated force and
moment coordinates at 80 Decimal digits. With the original binary64 F/H/J
metrics and exact conversion of nodal inputs, it builds
`S = V^T F^-1 V + W^T H W` and applies the dual reference equations directly.
It does not form dense nodal stiffness. Both displacement parts are combined
inside the high-precision context before evaluation.

Backend selection is explicit (`directional` or `decimal-flexibility`).
There is no automatic fallback or retry after failure. The original
directional-only coupled failure remains part of this diagnostic history.
The high-precision backend improves linear algebra after metric construction;
it does not improve quadrature accuracy, extend the finite-state chart, or
change section coefficients. A fixed Decimal context makes it independent
of caller precision/rounding settings.

## Separate assembled cross-check

The test reconstructs the original primal reference blocks independently
of either action implementation, retaining six internal rotations per macro
element. For two elements, it assembles 42 variables, clamps six, and solves
the remaining 36-variable system at 80 digits. It compares displacement,
reactions and external work, not merely a solver residual.

All uncoupled contrasts above and the complete high-contrast coupled section
meet the unchanged 1e-11 comparison checks with their explicitly selected
backends. Global force and moment balance are checked separately. The dual
backend is also compared directly with the original primal local equations.

This is a separately reconstructed algebra/arithmetic check by the same
author, sharing binary64 geometry/frame metric inputs. It is NOT independent
authorship, an independent continuum reference, a quadrature proof or a
domain-wide qualification result. No new symmetric coercivity, locking,
finite-state or nonlinear material claim follows from this small solve.

## Tests and provenance

- New focused suite: 11 passed in 2.54 seconds.
- Existing eight P5 development suites: 128 passed in 9.57 seconds.
- Tests cover assembly, full coupled section, forward displacement, reaction
  and work comparison, global balance, low-part retention, bounded failure,
  invalid input, shared-frame rejection, deterministic repetition, explicit
  backend selection and Decimal-context independence.
- Chain probe SHA-256:
  `7943962291ABFD763B63C3D3A8AEAA5417B6C95E09306420FE7D0D3989A0D1B3`.
- Precise reference action SHA-256:
  `674BFBF9309160630A2FAF200F8758476D4F1A5036C62E217FF99827833546C2`.
- New test SHA-256:
  `A2644F8B429FB10B700B8BD1D96F75C739AECAB6FC8165DDC1E6A62B1D9ABDDA`.

## Remaining programme

The next mechanics work must connect accurate reference assembly to physical
engineering/reference-convergence checks and reference mass/modal behaviour.
Precision/storage requirements must be carried into any eventual solver,
recovery and restart contract; returning only the collapsed displacement is
not an adequate high-contrast integration path.

The extreme finite coupled equilibrium/cutback case remains unresolved.
Independent source/equation review, finite-state high-contrast checks,
nonlinear section trial/commit/discard, geometric/material load histories,
postbuckling, mass/modal/prestress/buckling, installed-wheel qualification and
objective beam-shell joints remain required. No production code, existing
B2/B3/Q4/S3 mechanics, defaults, dependencies, workflows or package metadata
was changed. No formal execution, merge, release or activation was created.
The complete goal remains active. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
