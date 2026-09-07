# Actual force-control Newton integration for native line work

Successor of preserved clean d2f13d02008d48c29576092bc95b9a0a07526e6e.
This is a private bounded development gate, not independent qualification or
public exposure. No old beam/shell kernel, load potential, static condensation,
material law, qualification record, alias or default is changed.

## Exact extent

- `src/anysolver/_ge_beam3_native_line_program.py`: owned model/load program,
  constant plus proportional effective reference-line forces, exclusive nested
  scopes, deterministic assembly observations, and real force-control solver call.
- `src/anysolver/nonlinear_static.py`: candidate-only dispatch at four force-Newton
  assembly sites (including line-search trials/re-evaluation) and reaction recovery.
  Every original assembler argument is forwarded. Other element types retain
  the original assembler. Other control paths are not enabled for this candidate.
- `tests/test_ge_beam3_native_line_program.py`: actual straight/curved elastic and
  curved plastic two-increment solves, explicit line search, elastic constant
  plus proportional loading, independent load-work observation, accepted net
  equilibrium, reaction/force balance, origins, failure rollback, preflight and
  mid-assembly authority mutations including resealed patterns.
- This plan.

The frozen line-load scope and element are imported unchanged. Effective line
work acts on both nodal and internal cell coordinates; only the nodal portion
is supplied as the ordinary external LoadCase. The existing load-aware Schur
tangent is used unchanged. Zero force rows are omitted. Program signatures and
per-assembly effective signatures remain bound even if a pattern is resealed.

Only supported, homogeneous, standalone models (at most 16 elements/512 DOFs),
one layer, up to 16 increments and 24 Newton iterations are admitted by this
private entry point. No arbitrary initial state, staged path, MPC, activity,
mass, nonzero prescribed support, partial rotational support, nodal couple or
restart policy is added. Constant loading is applied from virgin state in the
same solve, not represented as previously committed plastic prehistory.

## Execution and preservation

Keep inventories separate: development smoke, expanded rehearsal, hardened
rehearsal, existing nodal-native regression, Q4 ownership regression, frozen
new-gate cycle A, frozen new-gate cycle B. One numerical thread/child, 24 GiB
process-tree memory, 600-second wall and 120-second CPU-inactivity supervision.
No automatic retry. At most three concurrent task children. Frozen A/B must
run from the same clean commit and configured runtime and produce byte-identical
scientific JSON packets; XML, timing and raw logs remain diagnostics.

Archive every run and exact runner command with per-file bytes/SHA-256, retaining
any failed output. Record independent review as PENDING unless actually obtained.
This gate cannot authorize a selector, general section parity, dynamics, release
or default changes. Next: load-bound typed restart/recovery and connected cases,
then the remaining complete beam and objective beam-shell programme.
