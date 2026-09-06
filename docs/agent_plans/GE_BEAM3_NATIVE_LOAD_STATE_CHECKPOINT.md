# GE-B3 P5: parameter-bound native load state

## Status

Private development successor `CANDIDATE_GE_BEAM3_P5_NATIVE_LOAD_V4`, based on
`9173d83c0222deed07f4233ab756b9cc2d0f2faf`. Six new private source modules in
`anysolver._ge_beam3_p5_loads` add explicit line-load state to the shared native
assembly seam. Existing production files, generic solvers, B2/B3, Q4/S3,
qualified straight GE-B3 routing, coefficients, tolerances, defaults and
historical evidence remain unchanged. This adds source; it is not a no-src-delta
checkpoint. Independent review and production qualification remain pending.

The implemented scope is the actual native assembly, rotation/state transaction,
element-level typed restart and load-parameter column. The equilibrium tests use
a small test-only Newton/backtracking loop over the real shared assembly and
state store. They do **not** prove that `solve_static_nonlinear`, displacement or
arc-length drivers now schedule these loads. No parallel private production
solver or public selector was introduced.

## Native state and ownership

- The element owns a fixed finite spatial force per unit reference arclength.
  Its vector and `SPATIAL_DEAD_FORCE_PER_REFERENCE_ARCLENGTH_V1` policy are bound
  into the model fingerprint and descriptor. Changing the vector after model
  creation fails validation.
- Every local stationary solve receives an explicit scalar load parameter.
  The parameter is a required finite float, not an optional value that defaults
  to zero. Only virgin initialization explicitly supplies zero.
- Core, driver and codec IDs are V4. Every station-state record stores the load
  parameter. Commit, recovery and typed restart replay the original accepted
  material origins at that recorded parameter, not at the next increment or an
  inferred nodal force. Historical V3 states cannot hot-restart as V4.
- `LoadStateStore` extends the existing transaction store without changing it.
  `load_parameter_scope(p)` binds one parameter to the exact native trial token
  and owning thread object. No global or thread-local mutable load factor is
  used. Reads, commit, discard and replacement require matching ownership.
  Scope exceptions discard only a newly created unaccepted trial.
- Candidate insertion and final commit check the parameter before any accepted
  pointer swap, even if all candidate hashes have been recomputed. A restart
  store rejects element states with inconsistent parameters before attaching
  a native rotation history. Missing parameters, plain stores, unsupported
  batching and unscoped assembly fail closed.
- The owner is the retained `Thread` object, not a recyclable operating-system
  thread ID. Nested scopes cannot replace an active request, and detached or
  stale contexts cannot supply a load derivative.

The existing native store remains responsible for node-shared multiplicative
rotations, accepted-origin linkage, deep-owned trial material records and atomic
publication. The new store adds parameter authority to those checks; it does not
independently rotate nodes or advance material state during recovery.

## Work, residual and parameter column

The frozen centered variational core already includes full line work on both
nodal translations and internal cell rotations. The new native core now passes
the trial parameter into it. The returned assembly force is the derivative of
the material incremental potential **minus the parameterized line-load work**.
It therefore already contains the line-load contribution; adding another nodal
projection for that same pattern would double-count it.

The load-only automatic-differentiation evaluator is an exact AST extraction of
the previously checked research implementation. It has no research imports and
does not subtract two material potentials to recover a tiny load. The internal
parameter sensitivity is solved from the full stationary saddle block. The
resulting external derivative is transformed by the native Exp-chart Jacobian.
No finite-difference mechanics, regularization or tolerance adjustment is used.

`native_load_parameter_derivative` requires the live native material context and
rotation view. It verifies the candidate parameter, pose, epoch and previous
origins before returning the chart derivative. This provides the **net-force**
parameter derivative: future global residual/control equations must apply the
corresponding sign and add only separately declared nodal load patterns.

## Checks

The initial three native assembly/equilibrium checks passed in 5.49 seconds.
The expanded 18 checks passed in 24.74 seconds, then 22 including shared-node
large-offset paths passed in 61.35 seconds. Three load-column/extraction checks
passed in 3.12 seconds. A preliminary 104-check regression passed in 71.06
seconds before the additional ownership audit.

The ownership audit found a genuine new-store flaw: inherited discard and
replacement could still be called from another thread although reads and
commits already required ownership. Two focused tests failed in 2.21 seconds.
Both paths were restricted before final freeze, with four targeted ownership/
cancellation checks then passing in 2.35 seconds. The regression retains these
tests and verifies that failed foreign-thread attempts preserve the original
token and committed state. This is a development correction, not a reclassified
formal qualification result.

Final source regression: **106 passed in 70.55 seconds**:

- 28 new native load tests: actual assembly, load-bound commit/replay, force and
  moment balance, plastic loading/unloading/reversal, exact typed split restart,
  one/two-element models, shared rotation ownership, byte-identical `2^40`
  translations, state/hash/codec/direction mutations, cancellation, cross-thread
  misuse, native-chart parameter finite differences and exact zero-force
  equivalence to preserved V3.
- 29 prior load-work checks and three static load-evidence checks.
- 14 preserved centered local-operator checks and six centered-native evidence
  checks.
- 21 existing straight P3 opt-in checks and five generic state-cleanup checks.

Force/moment/invariant checks retain `1e-11`; parameter finite differences retain
`1e-7` and compare the same smooth material branch. Typed restart is tested in
fresh models/stores against uninterrupted histories. No claim is made about a
unique derivative at a nonsmooth yield transition.

Runtime: Python 3.13.9, NumPy 2.4.3, SciPy 1.16.3, one numerical-library thread.
These are small correctness checks, not performance tests or formal campaigns.
No resource request, ledger row, formal cycle, wheel build or publication ran.
The previous V3 wheel/archive remains preserved and does not contain this V4
successor.

The read-only source map binds six new and 40 preserved modules. The four shared
assembly/state protocol modules were also verified directly against the base
commit's Git blobs. Canonical evidence records the unfinished public driver,
solver checkpoint, installed-wheel, loaded-modal and qualification gates as
false/pending rather than counting this narrower assembly step as completion.

Post-evidence inspection: **six static checks passed in 0.16 seconds**. They
verify the source map, old-framework and new-source mutation detection,
development-only status and exact preservation of the codec's strict canonical,
duplicate-key and nonfinite parsing functions. No mechanics was rerun for this
inspection.

## Next gate

Integrate an explicit immutable load schedule with the global solver. Each
force-control evaluation, line-search candidate, cutback, reaction evaluation,
displacement-control evaluation and arc predictor/corrector must receive its
correct trial parameter. Restart must bind the accepted global path position to
the element's recorded parameter and load-program fingerprint. Reversal and
unloading cannot be inferred from a monotonically increasing stage index.

Use the already checked condensed chart parameter column in displacement and
arc equations. Keep nodal loads separate from the embedded line work. Do not
silently route current/prestressed modes or buckling through the unloaded V3
operator. Loaded current operators must replay and differentiate this same
accepted load potential. Broader loads/couples, nonlinear section parity,
installed packaging, engineering beam qualification, independent review and the
objective beam-shell connection remain open. No default or alias changes follow
from this checkpoint.
