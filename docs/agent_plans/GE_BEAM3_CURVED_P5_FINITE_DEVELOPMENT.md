# P5 finite-mechanics development checkpoint

This is author development evidence on top of preparatory commit
`1432230440dbb8a81c86822af43bdaabe5afada5`. It is not an independently
reviewed candidate freeze or a formal qualification result. The independently
authored equation map/review required by the P5 plan is still pending.

## Implemented development probe

`docs/reference_cases/ge_beam3_curved_p5_finite_probe.py` implements the
proposed objective curved lift for a fixed SPD elastic 6-by-6 section. It
precomputes the reference force, compliance and coupling integrals, eliminates
12 material moment variables analytically, and solves six spatial relative
cell rotations. These are research functions outside the production package.

Both the residual and the full Hessian are derivatives of the same scalar
potential. The implementation propagates second derivatives using the
unchanged `_ge_beam3_mixed_ad.py` scalar/SO(3) kernel. This shared kernel is
declared explicitly: its reuse cannot be counted as an independent oracle.
No finite difference computes the implementation's residual or tangent.
Finite differences appear only in directional diagnostic tests.

The external chart is `x=x_base+du`, `Q=Exp(dtheta) Q_base` at each node.
The six internal rotations use spatial multiplicative updates. After solving
their equilibrium, the tangent is the Schur complement of the 24-variable
energy Hessian. At nonzero external increments, derivative comparisons keep
the same base chart. Differencing spatial residuals after silently changing
rotation charts is not an equivalent test of this symmetric Hessian.

The local solver has at most 25 Newton iterations and 12 backtracking trials
per iteration. It checks the local residual, finite derivatives and a positive
definite local Hessian at termination. Failure is explicit; there is no
fallback stiffness, automatic retry, accepted partial result or regularizing
diagonal. All evaluations are stateless. These numerical development settings
must be reviewed and frozen with the eventual candidate contract.

## Curved load work and recovery

For spatial dead distributed force `f` per reference arclength, the work is
the integral of `f dot (r_h-r0)`, with
`r_h=I_c x+U_c(r0-I_c X)`. The internal rotation contribution is retained in
the local equilibrium and its first and second variations. The implementation
precomputes the tensor `integral f tensor (r0-I_c X) ds0` as well as the nodal
load vectors. A test explicitly shows that omitting this tensor leaves a
nonzero local residual at the correct loaded solution.

Station recovery reconstructs material moments and obtains physical curvature
from the section compliance, `kappa=D^-1(m-B^T gamma)`. It does not report the
zero interior compatible curvature as bending recovery. Strains, six physical
resultants, current frames, spatial force and spatial moment are returned.
Recovery rejects a mismatched stationary configuration or corrupted moments.
These checks are preparatory consistency checks, not a restart fingerprint or
a nonlinear material transaction protocol.

## Verification actually performed

The new finite-probe suite passed 18 tests in 3.03 seconds. It covers:

- reference Hessian agreement with the separately assembled algebra probe;
- local stationarity and condensed symmetry;
- energy/residual and residual/tangent directional checks, including a
  nonzero external rotation chart;
- finite noncommuting bend/twist, with nodal rotation vectors of order one
  radian, and arbitrary superposed rigid motion;
- coupled-section reversal and reference-coordinate covariance;
- finite straight-limit energy, residual, tangent and moment agreement with
  the accepted P3 mixed solver;
- distributed-force work, total force and total moment balance, and the
  loaded condensed tangent;
- physical elastic station recovery and rejection of mismatched recovery;
- bounded failure, deterministic repeated evaluation, copied section inputs,
  caller-input preservation and rejection of invalid rotations/configurations.

The earlier 23 algebra-preparation tests remain separately recorded. The new
tests do not constitute a new formal P4 cycle, an independent P5 review, or a
curved engineering benchmark. Existing P3/P4 evidence is unchanged.

## Remaining work toward the complete goal

Independent derivation review remains required before candidate freeze.
Further development and qualification must cover integration accuracy and
slenderness with independent references; arches, rings and compatible spatial
chains; tension/compression and post-buckling; objective nonlinear section
trial/commit/discard for both straight and curved variants; mass, modal,
prestressed modal and buckling; full load/recovery/restart parity; isolated
installed-wheel exposure; and objective finite-rotation beam-shell connections,
including eccentric and curved attachments. The existing straight variant
accepts only a fixed linear generalized section; that limitation is not closed
by these elastic probes.

The branch remains `codex/ge-beam3-curved-p5-objective-lift-v1`, in worktree
`C:\Github\ANYsolver\.perf2-worktrees\ge-beam3-curved-p5-objective-lift-v1`.
No new resource request, scientific authorization, formal run, public selector,
default activation, merge or release is created by this checkpoint.
