# Native marine mechanics — development only

Public experimental APIs: `marine_rigid_v1`, `marine_link_v1`,
`marine_contributions_v1`, `marine_mechanical_v1`. MPL-2.0. Governing mechanics
and admission decisions: ANYmarine ADR012 and MECHANICS_LOAD_CONTRACT.md.
Existing structural and linear APIs remain unchanged.

`MarineMechanicalModel` declares ordered rigid bodies, finite attachment-frame
links, explicitly selected dry gravity, and developer contributions.
`solve_marine_mechanical(model, initial_states, run_spec, cancel, progress)`
integrates every body DOF together using fixed-step Newmark beta=.25/gamma=.5.
Dry and external total K/C/Ma derivatives enter the same Newton operator;
acceleration-dependent forces are included once. Production derivatives are
analytic. Principal-chart and relative-link rotation seams refuse admission.
Rechart after every accepted step preserves exact world pose/rates/acceleration.

Residual is external minus dry internal force. Force and moment residuals are
normalized independently by the declared SI unit floors, 1 N and 1 Nm, then
combined using `hypot`. Absolute tolerance is a dimensionless run specification.
Backtracking reduces Newton increments only. It never changes dt, stiffness,
physical properties or scientific acceptance criteria.

One `ContributionSet` owns history. Committed and trial values are recursively
immutable copies; numeric arrays have immutable backing storage. Only the exact
latest successful trial object may commit. Prepare while a step is active is
refused; `abort_step` explicitly discards it. Initial acceleration does not
advance time history. Provider failure, rejected trials, stale/forged commits,
transport failure and cancellation preserve the last committed inventory.
Transport receives immutable old/new chart descriptions. Physical histories
remain unchanged; chart histories require a declared transport callback.
Output and recharted states are validated before history commit. Cancellation
is polled within provider operations and after final-step progress reporting.

Results store authoritative WORLD position, rotation matrix, velocity and
acceleration for each stable body ID. Forces are WORLD wrenches about the
moving body origin: dry is positive internal, contribution forces are external.
Summing external minus dry reproduces the assembled physical residual.
Record fields are immutable and finite. `result_to_dict` exports the same
arrays; unmeasured log residuals are explicitly null. Failed/cancelled evidence
keeps its status and accepted-frame inventory, and is never a completed result.
Native model/spec serializers admit only their explicit versioned schemas;
arbitrary contribution/provider code cannot be loaded from JSON.

Development cases in `tests/test_marine_mechanical.py` fix all parameters before
execution: spherical free motion and gravity response, offset-CG nonspherical
momentum/energy conservation, two-body axial linear limit, and nonlinear framed
offset-link work/action balance. Each trajectory is dt=.001,100steps.
Gravity/spherical pose criteria are 1e-10 absolute SI/rotation-matrix entries;
free-body invariant drift<=1e-6 with SI unit floors; axial displacement error
<=1e-3 of its declared .1m amplitude; nonlinear force/moment balance<=1e-10 and
work derivative<=1e-8 with unit floors. Short protocol cases test added inertia,
immutable output, mid-trial/final cancellation, singular mass and failed chart
transport. This is implementation evidence, not the full scientific W4 gate.

Additional short cases in `test_marine_protocol_failures.py` cover step-2
singular/iteration failures, cancellation after chart transport, numerical
transport of a fixed WORLD vector through changing anchors, post-commit progress
exceptions, branch rejection with line search enabled/disabled, an injected
nonfinite initial Newton increment, and initial residual subtraction/norm overflow.
All ten cases passed in source and installed
modes. These are deliberate protocol/fault injections, not physical models.
Accepted records are checked against the configured residual tolerance and
failed/cancelled paths retain the correct accepted-frame/history inventory.
Nonfinite initialization and residual overflow report `nonfinite` with failed
partial evidence; rejection of the sole full Newton
candidate with line search disabled reports `branch_violation`. Failed evidence
from a progress exception may include the step already committed before that
callback. The norm uses fixed scales of1N and1Nm in a dimensionless L2 magnitude;
it does not apply a separate relative force/moment group normalization.
Narrow independent source assessments and the installed ANYmarine native CLI
check are recorded in `w4-integrator-*`/`w4-protocol-*` evidence. They do not
establish full W4 scientific acceptance or long-horizon rotation-drift bounds.

Do not run the complete old rigid-body test file under this slice's limits:
its legacy random oracle has32states. Selectors and process boundaries must
respect <=20numerical cases,<=12randomstates,<=4trajectories<=100steps/process,
one numerical process/thread and the existing cumulative execution budget.
No BEM, Morison, hydrodynamic/history source admission, lines, contact, HHT,
large-excursion potential-flow qualification or structural regression campaign
is established here. Physical-study authority remains separately pending.

ANYmarine's shared lazy services compile and execute this dry route headlessly.
They refuse configured hydrodynamic inputs instead of dropping them. Its native
job workflow now persists explicit link/initial-state configuration, executes
immutable snapshots through QProcess and admits validated matrix results with
their producing inputs. Source, installed public workflows and Windows desktop
replay passed the scoped development checks recorded in ANYmarine's TASK.md and
the native-job-verified evidence manifest. Scientific W4 and complete GUI/full
hydrodynamic acceptance remain separate obligations.

## Common mooring-node extension — 2026-10-09

The existing driver now appends three world translations per free line node
when `MarineMechanicalModel.mooring` is supplied. Body contributions keep their
original history/layout contract, while body and line matrices form one sparse
Newton operator. There is no second integrator or artificial node rotation mass.
Pass an exact immutable `initial_nodes` inventory; initial acceleration solves
the full body/node mass once. Accepted frames retain node arrays, tensions,
reactions, energies and component forces. Body recharting leaves world nodes
unchanged; line and body records commit after successful history transport.

The `marine_mechanical_mooring_v1` named model/result schema is distinct from
the unchanged body-only schema, preventing old consumers from erasing lines.
Cancellation and failure retain the previous accepted body/node/history set.
The new development cases contain at most four steps. They compare against
an independent linear Newmark system and check rotating fairleads, atomic
transport/cancellation, domain rejection and named persistence. Historical dry
test scopes and consumed budgets above remain evidence; the current prospective
driver pool is separate and does not renew them. These implementation checks
establish no W6 scientific acceptance. Line hydro/contact, coupled equilibrium,
ANYmarine workflow/replay and complete scientific gates still follow.
