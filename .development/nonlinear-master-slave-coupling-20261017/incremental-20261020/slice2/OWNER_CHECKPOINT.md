# Slice 2 owner checkpoint (early, turn ~10 of 80)

## Findings (no repeat of slice1 investigation)

- Registered plastic case confirmed in `tests/test_nonlinear_beam_shell_slice3_continuation.py`:
  displacement control on the tip probe node (id 5) `uz`, full target `-11/60 m`
  in 11 increments, prefix `-0.10 m` in 6 increments, resume 5 increments,
  max 40 iterations, tolerance 1e-8, same geometry/material/-2000 N tip load as
  the example fixture. Existing comparison tolerances: u/lambda rtol 1e-6,
  material rtol 1e-6 / atol 1e-9 (`_assert_states_allclose`), oracle residual
  <= 1e-7, wrench balance <= 1e-6 * applied.
- Public checkpoint APIs confirmed: `solve_static_nonlinear(..., restart_checkpoint=bytes)`
  (accepts bytes via `load_nonlinear_checkpoint`), `emit_restart_checkpoint=True`,
  `result.restart_checkpoint_bytes()` (canonical JSON). Failed-terminal restart
  refusal is the existing `ValueError("restart checkpoint does not end at a
  continuable completed static target")` at nonlinear_static.py:6116ff. No new
  format/API needed; no source edit planned.
- DC progress events publish `type`, `load_factor`, `control_value`,
  `max_equivalent_plastic_strain` (nonlinear_static.py:4909ff); force events
  publish `type`/`load_factor` (8454ff). Force route polls cancellation each
  Newton iteration (7453) - unchanged, existing actual-cancellation test stays.
- Harness: `run_slice.py 2` wrapper, portable batch flags confirmed with
  actual spacing: `--workers 1 --jit off --timeout-seconds 580
  --memory-limit-mib 953`, `RUNNER_TEMP` selects the portable run parent.

## Intended edit

1. `examples/beam_shell_coupling.py` (owned): add registered plastic DC case
   `run_plastic()` + CLI `--case preyield|plastic` (default preyield, existing
   force `run()`/default untouched), `--stage full|prefix` (default full),
   `--restart PATH`, `--checkpoint-out PATH`. Checkpoint written via
   `result.restart_checkpoint_bytes()` only on completed target; incompatible
   flag combinations rejected clearly before any solve; failed-terminal
   restart refusal reported truthfully with nonzero exit.
2. NEW `tests/test_beam_shell_checkpoint_workflow.py`: per coupling
   (direct/interpolated) full, prefix, resume through the CLI in separate
   processes; full-vs-resumed displacement/load-factor/material-history
   comparison at the existing continuation tolerances from checkpoint bytes
   loaded through the public serializer; nonzero plasticity; target error
   <= 1e-8; independent copied-H reduced residual <= 1e-7 and wrench balance
   <= 1e-6 via the original continuation module oracle; flag-refusal checks;
   failed-terminal restart refusal; actual cancellation input-purity
   (checkpoint file bytes unchanged, same checkpoint still delivers fresh
   resume) using public `event['type']` mapping.
3. `docs/BEAM_SHELL_CONNECTION.md`, `CHANGELOG.md`: document the
   completed-prefix checkpoint workflow and refusals.

## Remaining

Implement 1-3, one initial portable verification via `run_slice.py 2`, at most
one diagnosed repair pass, terminal HANDOFF.md. Budget 1800 s incl. 300 s
protected final reserve; per-CLI child timeout 120 s; whole test < 580 s.

## Blockers

None. Unrelated untracked `docs/contact-incremental-20261020/NEXT_SLICE_PLAN.md`
untouched. No solver source change anticipated; if the checkpoint integration
repair boundary in nonlinear_static.py/nonlinear_restart.py is concretely
required it will be narrowly diagnosed first.
