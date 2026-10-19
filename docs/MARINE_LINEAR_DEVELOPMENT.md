# Marine linear radiation-dynamics route (development)

Experimental development slice for the ANYmarine roadmap's first linear
two-body problem. Owner repository: `ANYsolver`. Governing contract:
`C:/ANYworkspaceWork/anymarine-evidence/solver-first-slice-contract.md`
(read 2026-10-08). Policy: `ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1`,
revision `2026-09-24.2` (Level A development evidence only).

This document describes the additive `anysolver.marine_linear` module, its
admission rules, its verification evidence and its limits. It is development
documentation, not a qualification claim.

## Scope boundary

`anysolver.marine_linear` solves only the fixed-equilibrium-frame linear
equation of motion with constant matrices, fixed time step and an explicit
causal radiation-memory convolution:

```text
(M_dry + A_inf) a + C v + K q + memory = F
memory_n = dt*(0.5*K_r[n] v_0 + sum(j=1..n-1, K_r[n-j] v_j)
               + 0.5*K_r[0] v_n),   n >= 1,   memory_0 = 0
```

- Newmark average acceleration, `beta = 1/4`, `gamma = 1/2`, fixed `dt`.
- `K` is the separately assembled linear hydrostatic plus mechanical link
  stiffness; no current load and no duplicated radiation force.
- `A_inf` is only the instantaneous (infinite-frequency) radiation added
  mass; the retardation kernel `K_r` carries the frequency-dependent part.
- Full cross-DOF dense matrices are retained (no diagonal reduction).
- No Capytaine, ANYhydro or Qt import; no shared structural integrator use.

Not in scope (refused by design, not merely undocumented): finite-rotation
(W4) mechanics, Morison loads, lines, contact, adaptive stepping, restart,
nonzero memory initialization, and any capability claim beyond the linear
fixed-grid route above. Tests of this module are development evidence, not
scientific qualification.

## Public API

`src/anysolver/marine_linear.py` exposes:

- `MarineLinearSpec` — frozen input dataclass: `labels`, `dt`, `times`,
  `forces`, `mass_dry`, `added_mass_infinite`, `damping`, `stiffness`,
  `radiation_kernel`, `kernel_times`, optional `initial_displacement`,
  `initial_velocity`.
- `solve_marine_linear(spec, *, cancel=None) -> MarineLinearResult`.
- `MarineLinearResult` — frozen, read-only-array result: accepted `times`,
  `displacements`/`velocities`/`accelerations` (q/v/a), external forces and
  the force decomposition (`dry_inertia_forces`, `added_inertia_forces`,
  `memory_forces`, `damping_forces`, `stiffness_forces`), equation residual,
  `balance_relative_max`, `n_steps`, `n_accepted`, `complete`, `cancelled`.
- `exponential_radiation_kernel(cr, decay, dt, count)` — deterministic
  builder for `K_r[k] = cr * exp(-decay*k*dt)` kernel stacks (a linear-scope
  convenience, not a hydrodynamic provider).
- `MarineLinearError`, `MarineLinearInputError`, `MarineLinearSolveError`.

## Step algorithm

With `q_pred = q_{n-1} + dt*v_{n-1} + dt^2*(1/2-beta)*a_{n-1}` and
`v_pred = v_{n-1} + dt*(1-gamma)*a_{n-1}`, each step solves

```text
[M + gamma*dt*(C + dt*K_r[0]/2) + beta*dt^2*K] a_n
    = F_n - memory_past_n - (C + dt*K_r[0]/2) v_pred - K q_pred
```

where `memory_past_n` is `memory_n` without the current-step term
`dt*0.5*K_r[0] v_n` (that term moves to the left side through
`v_n = v_pred + gamma*dt*a_n`). The effective matrix is factorized once
(dense LU); the total mass is factorized by Cholesky for the initial
acceleration `a_0 = (M_dry+A_inf)^{-1}(F_0 - C v_0 - K q_0)`.

Initialization: the radiation memory starts at rest at `t0`
(`memory_0 = 0`) even when `v_0 != 0`. A nonzero initial velocity is an
impulsive start whose pre-`t0` radiation history is not modeled; this is the
documented initialization convention, matching the augmented-ODE reference
`z(0) = 0`.

## Admission and validation

All checks fail closed with `MarineLinearInputError` naming the field, the
expected contract and the observed violation. No physics is adjusted to
pass a check and no eigenvalue is silently projected or clamped.

- Labels: non-empty, unique, non-empty strings; stored as a stable tuple.
- `dt`: finite and strictly positive; the time grid must satisfy
  `times[k] = times[0] + k*dt` and the kernel grid `kernel_times[k] = k*dt`
  within a documented small relative tolerance; the kernel must cover every
  lag needed by the requested steps.
- Shapes: matrices `(n, n)` per DOF count, kernel `(n_kernel, n, n)`,
  forces `(n_steps, n)`, `q0`/`v0` `(n,)`.
- All input values finite; non-finite input is refused.
- Physical matrices symmetric within a small relative tolerance and used
  as given (no symmetrization).
- Total mass `M_dry + A_inf` must be positive definite: the documented
  numeric check is a Cholesky factorization; failure is an admission
  failure. Singular total mass fails admission.
- The effective Newmark matrix must be factorizable; a singular effective
  matrix is refused. A non-finite state produced during integration raises
  `MarineLinearSolveError` naming the step and time.

Reference frames and mass division: all matrices are constant coefficients
in the common equilibrium frame of the linearized model (SI units).
`mass_dry` is the structural (dry) inertia matrix; `added_mass_infinite`
is the instantaneous radiation added mass `A_inf`. They are kept separate
in the API and in the result force decomposition.

## Cancellation contract

`cancel` accepts a callable returning a truthy value, or an
`anysolver.control.CancellationToken` (duck-typed via `is_cancelled`).
It is polled at accepted-step boundaries only, after each accepted step.
Chosen API: cancellation returns normally — never an exception — with a
result whose `cancelled` is `True` and `complete` is `False`, and whose
arrays contain exactly the accepted history (at least the initial state at
`t0`, which is always computed). A cancelled run is never reported as a
successful complete run. Caller arrays are never mutated; result arrays
are fresh copies marked read-only.

## Development checkpoint (final status)

Implemented and verified against the assigned development criteria. New
files only: `src/anysolver/marine_linear.py`,
`tests/test_marine_linear.py`, `scripts/marine_linear_demo.py` and this
document. No existing file, root `__init__`, shared integrator or sibling
repository was touched. No blocker remains within this slice's scope.

## Verification evidence

Focused source development run (2026-10-08, repo `.venv`, Python 3.13.9,
numpy 2.4.3, scipy 1.16.3), executed through the portable runner and
bounded/recorded by the parent `run_check.py` helper:

```text
C:/ANYworkspaceWork/anymarine-evidence/runtime/Scripts/python.exe
  C:/ANYworkspaceWork/anymarine-evidence/run_check.py
  --out C:/ANYworkspaceWork/anymarine-evidence/solver-marine-linear-dev-02
  --cwd C:/Github/ANYsolver --timeout 120 --
  C:/Github/ANYsolver/.venv/Scripts/python.exe scripts/run_portable_ci.py
  --development tests/test_marine_linear.py tests/test_fe_solver_dynamics.py
  --timeout-seconds 120 --memory-limit-mib 1024
```

- Outcome: 35 passed, 0 failed, 0 skipped (31 marine linear development
  tests plus the 4 existing linear dynamics tests in
  `tests/test_fe_solver_dynamics.py`), exit code 0.
- Resources: process wall 12.2 s (limit 120 s), peak sampled process-tree
  RSS 184 MiB (limit 1024 MiB), one numerical thread, JIT off, plugin
  autoload off; runner runtime record reports no source-checkout import
  escapes and `anysolver.marine_linear` loaded from this checkout.
- Evidence: `C:/ANYworkspaceWork/anymarine-evidence/solver-marine-linear-dev-02/`
  (`result.json`, `stdout.log`, `worker-record/selection.json`,
  `worker-record/runtime.json`, `worker-record/resource.json`). The
  earlier equivalent run is preserved at `solver-marine-linear-dev-01`.
- Demo: `scripts/marine_linear_demo.py` executed with exit 0 in 2.5 s;
  evidence at `C:/ANYworkspaceWork/anymarine-evidence/solver-marine-linear-demo-01/`.

Test content (development evidence, not qualification): analytic
no-memory oscillator and step-load SDOF solutions; temporal convergence
(second order observed) and full off-diagonal 4-DOF response against the
augmented-ODE `scipy.solve_ivp` reference with nonzero initial velocity;
free-decay work/energy balance; harmonic steady-state identification
against the independent frequency-domain `A(omega)`/`B(omega)` reference;
result contract, force decomposition and balance; input immutability and
read-only results; 20 parametrized admission refusal cases (shapes,
non-finite, asymmetry, grid mismatch, short kernel, non-positive-definite
and singular total mass); cancellation at accepted-step boundaries
(callable, immediate, `CancellationToken` property and mid-run token) with
prefix-exact incomplete history; kernel builder values and refusals.

Author test passes are development evidence only. Scientific acceptance,
RAO/mesh/step studies and the Capytaine demonstrator remain separate gates.

## Limitations

- Fixed step, fixed grid; no adaptivity, no restart, no checkpointing.
- Constant equilibrium-frame matrices only; no finite rotation, no
  re-linearization, no mesh or frequency data consumed.
- Memory initialized at rest at `t0`; impulsive starts are not modeled in
  the radiation history.
- Dense 4-DOF-scale prototype; no sparse assembly (deliberate, per the
  first-slice contract).
- Development evidence only: no RAO, mesh/step study, Capytaine comparison
  or independent scientific acceptance is claimed by this module.
