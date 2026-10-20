# Slice 1 owner checkpoint — 2026-10-20 (early, turn ~8)

## Concrete findings

- Registered preyield case (fixture `tests/test_nonlinear_beam_shell_slice3_continuation.py`):
  force control, canonical S355 curve scale 1.0 (`dnv_c208_steel_curve("S355", 0.012)`),
  L=1, W=0.24, t=0.012, shell 2x1, e=+0.04 z, beam section 10x40 mm with
  fiber_plasticity, -2000 N uz per shell-tip node (2 tip nodes), num_steps=6,
  max_iterations=30, tolerance=1e-8, corotational. The fixture proves this load is
  pre-yield: alpha_max == 0 and displacements match a true-elastic material exactly.
- Direct coupling = 3 beam nodes / 2 beam elements, all `CoupledBeamShellElement`;
  interpolated = 4 beam nodes / 3 beam elements with genuinely interpolated
  mid-span `InterpolatedBeamShellMPCElement` masters (deterministic IDs, no
  coordinate search).
- Public API sufficient for the example: `FEModel`, `BoundaryCondition`, `LoadCase`,
  `create_shell_element`, `CoupledBeamShellElement`,
  `InterpolatedBeamShellMPCElement`, `solve_static_nonlinear`,
  `CancellationToken`, `SolveCancelled` (top level); `BeamElement`
  (`anysolver.elements`), `dnv_c208_steel_curve`/`DNVC208MaterialCurve`
  (`anysolver.material_curves`). No private solver imports needed.
- Completion truth: `result.status == "completed"`, `result.stop_reason`
  (info), `result.load_factor` (achieved), probe uz from
  `result.displacements[dofs[2]]`, accepted increments = `len(result.steps)`;
  solver already writes `result.info["constraint_postcheck"]`
  (status passed/failed, max_relative_residual, relative_tolerance) with the
  correct rotating-MPC linear-displacement mapping.
- Cancellation: `solve_static_nonlinear(..., cancellation_token=...)` raises
  `SolveCancelled`; accepted increments are observable publicly through
  `progress_callback` events (`event_type == "nonlinear_static_step"`,
  metadata carries load_factor). No result object exists on cancel, so the
  JSON must report null achieved/probe fields when no increment was accepted.
- Harness: `run_slice.py 1` reuses gate-closure harness (allowance 1800 s,
  reserve 300 s, preflight, JIT off, one numerical thread). Regression commands
  (pytest/run_portable_ci.py) may use --timeout up to 600; other commands 120.
  `run_portable_ci.py` CLI confirmed: `--development TEST... --workers N --jit
  off|on --timeout-seconds N --memory-limit-mib N`; RUNNER_TEMP selects its
  durable output parent.

## Intended edit

1. `examples/beam_shell_coupling.py` (new): standalone public-API example.
   `build_model(coupling)` -> case object (model, load, probe node id);
   `run(...)` -> truthful JSON payload dict (status, stop_reason,
   requested_load_factor=1.0, achieved_load_factor, probe_displacement,
   accepted_increments, constraint_postcheck, completed = status completed AND
   |achieved-requested| <= 1e-8 AND postcheck passed); `main(argv)` CLI with
   `--coupling direct|interpolated` (default interpolated), optional
   `--output PATH`, JSON on stdout, exit 0 ONLY on completed, SolveCancelled ->
   non-completion JSON (accepted increments from progress events, empty history
   safe), other exceptions keep tracebacks.
2. `tests/test_beam_shell_workflow.py` (new): structure checks for both
   couplings; actual public solve completion for both couplings (status, load
   factor, 6 accepted increments, postcheck passed, completed flag, probe uz);
   independent true-elastic control (test-local public construction) matching
   the default-coupling probe displacement; cancellation tests (0 accepted and
   >=1 accepted) asserting non-completion JSON and no success claim; CLI main()
   JSON/exit-code tests in-process (runpy + capsys).
3. `docs/BEAM_SHELL_CONNECTION.md`: correct the stale "no completed plastic
   case" claim to the demonstrated default-route -11/60 m S355 case with
   restart; keep original -0.20 m, director -1/6 m and analytical accuracy open;
   add a short "Reading a displacement-control result" note
   (steps[-1].control_value, .converged meaning, manual continuation route).
4. `CHANGELOG.md`: Unreleased entries for the example/CLI and the doc
   correction; no default/tolerance/material change.

## Remaining work / blockers

Implement 1-4, then ONE verification pass via
`run_slice.py 1 --name ... --timeout 600 --hash-input examples/beam_shell_coupling.py
--hash-input tests/test_beam_shell_workflow.py -- .venv/Scripts/python.exe
scripts/run_portable_ci.py --development tests/test_beam_shell_workflow.py
tests/test_beam_shell_connection_options.py --workers 1 --jit off
--timeout-seconds 580 --memory-limit-mib 953` with RUNNER_TEMP set to
slice1/portable-runs; at most one diagnosed repair pass; optional 120 s CLI
smoke; handoff. No blockers. No solver/test-harness edits, no sweeps.
