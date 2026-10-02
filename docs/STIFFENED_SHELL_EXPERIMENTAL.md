# Experimental stiffened-shell workflows

`anysolver.stiffened_shell.create_analysis(definition=definition)` dispatches
the explicitly selected GE or physical B2 profile. Both remain experimental;
implemented behavior is distinct from programme qualification. Legacy selectors,
element mass kernels and package versions are unchanged.

## Accepted point actions and native consumer inputs

GE `solve_linear`, `solve`, `recover` and `restore` results now include immutable
`point_wrenches`, in definition order. Each `PointTransferWrench` identifies its
shell/beam node IDs, port positions (including their low parts), six-component
gap and global spatial `shell_action`/`beam_action`. These are the loads exerted
by the connection on each domain: minus the assembled connection resisting
residual (forces in N, moments in N m). Each moment is about its own port; include the lever arm when checking
balance about a common origin. Raw material-basis multipliers are not spatial
moments. Gap translations use the shell material frame; rotational gaps use the
joint's reference-relative logarithm convention (translations in m, rotations in rad).

Reference-linear records use the frozen reference constraint map and reference
positions, not a finite reinterpretation of the linear displacement. Finite
records use the same spatial pose evaluation as assembly. Their enclosing result
binds the accepted generation; recovery performs no new mechanical evaluations.
Rejection/cancellation preserve the accepted payload. Derived records are rebuilt
on restore and chart reset without changing checkpoint schemas. This verifies
recovery, not physical torque/drilling fidelity or the complete M1 milestone.

ANYfem can now store exact `ExperimentalGEPointPanel` or
`ExperimentalB2PointPanel` inputs in an ordinary `.anyfem` Project using
`AnalysisDefinition.experimental_point_panel(name, panel)` and the normal
`save_project`/`load_project` functions. The resulting analysis record's
`create_point_panel_analysis()` creates a fresh public solver owner.
`anyfem.solve.stiffened_shell_project.solve_point_panel(record)` executes the
stored reference-linear GE action set or ordered B2 cases/selected recovery.
GE has no batch callback; B2 preserves complete-case cancellation semantics.

These explicitly experimental records own a mesh-native definition. Project
geometry/load targets do not regenerate it; unrelated Project settings,
resource policies and output requests are rejected. Native input save/reopen
does not save an accepted solver checkpoint. Standalone experimental files,
legacy/default routes, ordinary native format version and qualification status
retain their meanings. BL5 uses a distinct experimental Project route; general consumer completion remains unfinished.

## Native physical-fibre reference-linear point panels

The existing GE owner admits native physical axial/biaxial-fibre sections at
their stress-free reference linearization, including generalized and physical
sections in the same point-connected Q4/S3 panel. It retains all 24 internal
coordinates per beam and uses the existing native residual/Hessian and physical
section derivative. No material law or legacy selector changes.

Run the installed headless example with `--beam-family physical_fibre` or
`--beam-family mixed`:

```text
python scripts/experimental_stiffened_ge_panel.py --beam-family mixed
```

This route supports linear solve, physical support reactions, owned coordinates,
checkpoint/restore and subsequent compatible loads with factorization reuse.
Capabilities report `EXPERIMENTAL_NOT_QUALIFIED`. The same point owner also
admits experimental finite physical-fibre and mixed-family histories with
elastic or isotropic DNVC-C208 J2 Q4/S3 shells. Native cell coordinates are retained; each trial uses
the same accepted material predecessor and acceptance is atomic. Accepted
station recovery supplies paired fibre strains, stresses and plastic increments
from the actual native material response. `beam_station_accumulated` reports
maximum fibre accumulation per physical-fibre station, and generalized
accumulation for generalized stations; these are different material measures.

The distinct binary native-material V7 checkpoint stores the last predecessor
and resulting history in model-defined order, preserving every high/low pair.
Restoration re-evaluates that increment and requires matching accepted history
before publishing state. This validates the endpoint and its last material
update, not the provenance of an entire loading path. Generalized-only formats
keep their existing contracts.

Accepted `beam_fibre_energy` records contain paired stored material energy in
joules, previous hardening energy, last-increment dissipation, and the native
incremental material potential. The stored-energy/dissipation split uses the
unchanged fibre law at its actual converged station strains and saved predecessor.
It does not report cumulative dissipation, external work or total coupled-system
energy. Energy capture is opt-in at the private local operator; its default
response and legacy station-recovery payloads remain unchanged.

The distinct V8 native/shell-J2 checkpoint retains both shell and beam material
predecessors and resulting histories. S3 records are model-bound native blobs;
predecessor coordinates and anchors bind their constitutive chart. Restore
repeats the update and checks saved material/recovery consistency before one
publication. V7 and generalized-only formats keep their existing contracts.

Simultaneous active shell/fibre yielding still needs direct evidence; a shell-J2
definition with zero shell plastic accumulation does not establish it. Line
attachments and total-system energy remain unfinished. Strong full-section
yielding and small-load/pure-fibre S3 convergence failures remain development
findings; tolerances have not been relaxed. The passing partial-yield histories
do not qualify those cases or G3. A linear result does not predict yielding.

## Physical B2 numerical output admission

The physical section law is checked for exact positive definiteness of its
binary64 inputs. The former provisional normalized-pivot cutoff is replaced by
`B2_BOUNDED_OUTPUT_REPRESENTATION_V1` on the actual emitted tangent. It certifies
all six basic deformation energies to the existing 1e-8 work accuracy, and
separately bounds physical rigid wrench leakage (1e-9) and bounded rigid/cross
work (1e-8). Exact rational tests do not average the matrix with its transpose.
The operator's immutable `output_certificate` identifies this check;
`stiffened_shell.OutputRepresentationError` carries a failed certificate.
Overflow, underflow and insufficient subnormal precision still fail explicitly.

The reference right inverse fixes node one. Rigid fields use a centroid basis,
translations scaled by element length L and unit rotations. The force scale is
the maximum of the section translation diagonals and rotational diagonals/L²;
moment and energy scales are F*L. Rigid and cross bounds each apply to their
normalized finite-amplitude cube. They are not one total-energy bound or an
all-amplitude relative guarantee near a rigid kernel. Basic energies are checked
against the implemented law; independent physical work/force/station oracles
remain required. Local admission is not continuous-range qualification or
assembled graph stability; sparse solve/equilibrium checks remain separate.

The certified constant tangent is prepared once per immutable local operator.
Each evaluation returns an owned copy. No material law, historical B2 equation,
default selector or package version changes. Programme F09 acceptance remains
separate from this implemented numerical guard.

## Supported B2/Q4 reference-modal development route

The existing multi-Q4/multi-B2 point-panel owner now accepts a positive explicit
`density_kg_m3` on each `Q4PanelShell` and physical `MassMetadata` on each beam.
Missing mass remains valid for static use; the owner rejects a modal request
without complete mass. Density and inertia are never inferred from stiffness.

```python
from anysolver import stiffened_shell

analysis = stiffened_shell.create_analysis(definition=definition)
result = analysis.modes(stiffened_shell.B2ReferenceModesRequest(count=3))
if result.status == "ok":
    frequencies_hz = result.frequencies_hz
    mass_normalized_physical_vectors = result.physical_modes
else:
    failure = result.failure_reason
```

This initial route uses supported, conservative reference-linear models with
coordinate supports, including diagonally rescaled selectors. General affine
MPC columns are rejected. It returns checked finite candidate eigenpairs;
residuals and orthogonality do **not** certify spectral completeness or repeated
eigenspaces. Free-free modes, prestress, buckling, S3/GE modes and spectral
qualification remain open programme obligations.

The shell mass follows through-thickness velocity about the mid-surface and
has zero normal-spin inertia. Beam mass uses the admitted physical sectional
metadata and existing station-trace Ritz interpolation. Multipliers and any
retained zero-inertia primal coordinates remain algebraic. The sparse route
uses a negative-shift descriptor factorization and general inverse-product
eigensolve; no global dense inverse, nullspace or artificial mass is used.
Returned vectors, physical gaps, projected equilibrium, descriptor residuals
and physical-mass orthogonality are checked before publication. Numerical
failure or cancellation publishes no partial pairs and leaves static operation
available. Unclassified programming errors propagate.

The ANYfem experimental B2 `mass-v2` input format preserves explicit shell
density and beam mass metadata for this route. The historical static-v1 format
still rejects these fields rather than discarding them. Experimental input
persistence is distinct from ordinary native-project persistence, which remains
unfinished along with complete modal qualification.

Development evidence and exact installed identities are linked from the
[active state](agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md). This document does not
establish G0/G1, F07/F12 or G4B acceptance.

## Experimental GE shell-anchor reset

After an accepted finite point-coupled step, the same owner can reset its shell
rotation chart without advancing the physical load:

```python
accepted = analysis.recover()
rebased = analysis.rebase_rotations(expected_generation=accepted.generation)
saved = analysis.checkpoint()
resumed = stiffened_shell.create_analysis(definition=definition)
resumed.restore(saved)
```

The owned physical orientation is `Q = Exp(eta) @ A`; the event sets `A = Q`
and `eta = 0`. It preserves beam poses, native retained variables, material
histories and accepted load factors. The event advances the accepted generation
once. Stale predecessors, cancellation before publication and failed mechanical
checks leave the accepted prefix intact. This operation does not extend the
admitted element strain, distortion or relative-rotation domains.

Only fully free or fully fixed shell rotation triples are admitted for reset.
Partially fixed total-rotation components require transformed support equations
and are explicitly rejected. Line owners remain reference-linear. Native beam
rotations retain their existing physical storage; this is a shell-chart event.

After reset, `shell_frames` contains the physical matrices,
`shell_rotation_anchors` the immutable anchors, and `shell_chart_coordinates`
the local coordinates. `shell_displacement` retains translations and displays
principal rotation vectors; those vectors cannot reconstruct a loading history.
The historical Q4 adapter uses a total evaluation chart and rejects its pi branch.

Anchored checkpoints have a separate V6 identity, inner policy and physical-pose
witness. Restore checks mechanical consistency and continues without replay.
Unrebased checkpoints retain their previous contracts. This development slice
does not close F06, V18, G0B or broad chart/history qualification.

## Selected Q4 full algorithmic pullback

Q4 point panels can explicitly select a separate force-map policy:

```python
from dataclasses import replace
from anysolver import stiffened_shell

definition = replace(definition,
    q4_pullback_policy=stiffened_shell.Q4_ALGORITHMIC_PULLBACK_V1)
analysis = stiffened_shell.create_analysis(definition=definition)
```

This experimental policy uses the complete deformation pullback for the
unchanged local Q4 elastic or isotropic DNVC-C208 J2 update. Each trial uses
the same accepted material predecessor. The tangent includes deformation-map
curvature and the spatial-row/additive-chart transformation, including owned
rotation anchors. It is not a claim of a conservative plastic potential.
Reference-linear and finite evaluations use the selected map consistently.

The historical corotational policy remains the default. The selected policy
changes model identity; checkpoints from the two maps cannot be interchanged.
The existing anchor-envelope format is retained with that separate model
identity. Selection requires at least one Q4 element. It is admitted for point
panels, including mixed Q4/S3 panels, and elastic pure-Q4 BL5 line models with
generalized beam sections. S3's existing map is unchanged. Other line/material
combinations and all-S3 selection fail explicitly.

ANYfem persists this selection in the separate experimental v3 panel schema;
existing v1/v2 records retain their original selection and layout. These
experimental records are distinct from ordinary native-project persistence.
The policy does not qualify F05/F06 or broaden the shell strain/chart domain.

## Elastic S3 arithmetic with native fibre histories

Fresh finite point owners containing physical-fibre beams and elastic S3 shells
use the existing compensated shell-translation map. This retains small
displacements independently of the reference-coordinate spacing and evaluates
the complete first and second variations of the same physical map. Q4, S3 J2,
generalized-only owners and the variational adapter's legacy default retain
their existing policies.

These histories have a distinct stable-S3 native-material V9 binary schema,
including its anchored variant. V9 uses the existing bounded binary framing;
it does not change constitutive history layout. Restoring V7 retains the
original translation arithmetic, validation criteria and checkpoint bytes.
Schema and model admission precede mechanical validation and publication.

The tested pure-fibre S3 elastic and partial-yield cases complete monotonic
loading and restart at unchanged tolerances. Fixed-step partial-yield unloading
exhausts backtracking in the retained diagnostic. Atomic rejection preserves
the accepted prefix. The optional controller below completes that same bounded
history with a midpoint; neither result qualifies full G3.

## Optional adaptive finite increments

```python
from anysolver.stiffened_shell import AdaptiveIncrementControl

control = AdaptiveIncrementControl(max_cutbacks=4, max_attempts=24)
result = analysis.solve(actions, targets=(.5, 1., .5),
                        increment_control=control)
```

The experimental point-owner controller halves an interval after typed Newton
iteration or backtrack exhaustion, starting each retry from the last accepted
state. It holds the reduced step until the requested target and then starts
the next interval. Every accepted midpoint appears in `accepted_factors`.
Physical equilibrium, compatibility and material checks remain unchanged.
Default fixed stepping is preserved. Backend, programming, memory, cancellation
and unclassified local failures propagate; they do not trigger these cutbacks.

`increment_attempts` records accepted and rejected factors, actual evaluation,
linear-solve and rejected-trial counts, and failure details. A cancelled pending
sequence recovers `status="accepted_prefix"`; reaching all requested targets
returns `status="completed"`. `AdaptiveIncrementExhausted` reports the incomplete
sequence and its failed work. An accepted prefix is not requested completion.

Finite GE `solve` also accepts optional `on_accepted(result)`. It runs
synchronously after each complete increment commit, including adaptive substeps.
The result and its nested arrays are detached from solver state; retaining it is
the caller's choice. `recover()` and `checkpoint()` inside the callback observe
that committed generation and controller cursor. Reentrant mutation is rejected.
The callback must not wait for another thread to mutate the same owner while the
enclosing solve holds its writer lock. Callback errors propagate unchanged and
never trigger numerical cutback; the committed prefix remains available.
Cancellation requested there takes effect at the next solver safe point and
does not undo a completed increment. Callbacks are not serialized in checkpoints;
pass the callback again when continuing a restored analysis. With no callback,
the solver retains no additional accepted-state history.

Distinct V10 checkpoints wrap the physical snapshot and durable controller state.
Resume with the same original targets, controls, Newton limits and load pattern.
An exhausted attempt budget is terminal for that pending sequence. Checkpoints
record work through their accepted boundary; exceptions can include additional
uncommitted rejected work. Restore validates dyadic decisions and the accepted
factor history before mechanical validation/publication. A rebase preserves the
pending plan and updates its charted physical snapshot. Prospective checkpoint
size is checked before commit; returned snapshots retain exact bytes. The
controller performs no mechanical history replay or topology recompilation.

The unchanged partial-yield S3 load/unload screen completes with a .75 midpoint
and matches a fixed solve at the identical accepted increments. The strong
full-section Q4 screen still exhausts four cutbacks after accepting .0625.
These are case-specific development results, not complete material or G3
qualification. Full limits, external validation and practical scale remain open.

## Experimental finite BL5 line

The separate BL5 position/top-surface director bond now admits elastic finite
force control on the existing persistent GE owner. Normal spin is released;
this does not alter six-row point semantics. Native retained half-cell poses,
fixed reference segmentation and the declared P0/P1 basis remain explicit.
No basis is selected or qualified by this implementation.

Physical left-port derivatives include multiplier curvature and rotational
gauge corrections. Only shell increment columns pass through their additive
charts. Returned `beam_shell_line_work` contains owned integer index maps,
station gaps, multiplier densities and integrated spatial gradients. These
are endpoint forces/couples and native cell couples; raw multiplier coefficients
are not display moments. Station gaps differ from accepted integrated weak rows.

Finite BL5 uses distinct V11 binary checkpoint identities (including anchored
states), preserving old point and reference-linear records. The optional V10
adaptive envelope can wrap V11. Unloading/reloading, cancellation, actual rebase,
restoration and continuation preserve accepted-prefix semantics. Only typed
candidate director/trace-chart failures backtrack; unclassified errors propagate.
Shell J2, physical-fibre lines, generalized plastic BL5 response, L1 finite
analysis and qualified bonded-line claims remain excluded. Broader programme
material/attachment requirements remain unfinished.

With explicit `Q4_ALGORITHMIC_PULLBACK_V1`, elastic pure-Q4 BL5 models also admit
`StagedDeadLoadProgramme` translation forces. Run:

```text
python examples/stiffened_shell_bl5_staged.py
```

This public-API example uses three Q4 shells and two native B3 elements with
nonmatching segmentation, signed force stages, accepted-prefix cancellation,
rotation rebasing and identical restored continuation. It reports experimental
status and numerical equilibrium/compatibility, not physical accuracy. The
historical Q4 policy remains unchanged and does not admit staged line loading.
Distributed forces/couples, shell pressure and material histories on lines are
outside this example's admitted scope. ANYfem now preserves explicit BL5 inputs and staged programmes in a distinct
experimental native Project route, with cancellation/checkpoint continuation
checks. Full consumer and physical qualification remain open.

The same explicit objective-Q4 BL5 owner now accepts `GEBeamDistributedLoad`
and `GEBeamDistributedProgramme`. These use the existing native beam quadrature,
including retained half-cell work, with fixed spatial force/couple densities per
reference arclength. Spatial couples are nonconservative. For example, using the
model from `examples/stiffened_shell_bl5_staged.py`:

```python
owner = stiffened_shell.create_analysis(definition=model)
try:
    load = stiffened_shell.GEBeamDistributedLoad(owner.preflight()["identity"], (
        stiffened_shell.GEBeamLineAction(1, (0., 0., 100.), (2., 3., 0.)),
        stiffened_shell.GEBeamLineAction(2, (0., 0., 100.), (2., 3., 0.)),
    ))
    result = owner.solve(load, targets=(.5, 1.))
finally:
    owner.close()
```

Both P0 and coarse continuous-P1 line cases pass signed force/couple programmes,
physical wrench balance, cancellation, rejected-trial preservation, chart restart
and continued stepping. A mixed point/BL5 layout also passes. These are bounded
integration checks, not acceptance of arbitrary layouts or BL5 physical accuracy.
Historical Q4, L1 and footprint distributed-load admission remain unchanged.
ANYfem BL5 distributed-load persistence is not yet implemented. Zero-load relative
assessment and all outstanding scientific obligations remain unchanged.

Run `scripts/experimental_stiffened_ge_bl5_history.py` with an installed
development wheel for a3-Q4/2-B3, nonmatching3:4 elastic history and byte-exact
restart/continue. Physical torque/shear reference, interface stability, ratios,
scale and G2/F03 acceptance remain open.

For a reference-linear strip with explicitly restrained beam termination, run
`scripts/experimental_stiffened_ge_bl5_reference_panel.py` through an installed
development wheel. It fixes the shell root and the beam nodal root translations
and x/y rotations, leaving normal spin free. Two Fy/Mx cases share one eligible
factorization and restore byte-exact snapshots. The reported shell and beam
reactions are separate **ground** reactions, summed about the reference origin;
they are not a concentrated beam-to-shell endpoint attachment. Removing those
beam supports defines a different physical support problem. The example does
not qualify retained-section endpoint enforcement or select a line basis.

Reference-linear GE solves perform one compensated-residual correction using
their own cached sparse factorization before the unchanged equilibrium and
constraint checks. The existing optional second correction remains bounded.
`reference_linear_refinements` counts this work, including rejected or cancelled
work. Nonlinear solves and restored snapshot arrays retain their existing
contracts. The extra backsolve and residual evaluation have a cost; this change
does not establish large-model performance or uniform multiplier stability.

The experimental single-Q4 B2 point owner uses the same scale-aware physical
equilibrium and bounded affine-work projection as the multi-Q4 panel owner.
Tiny nonzero force/moment loads cannot be accepted through a fixed unit floor;
unrepresentable projected work fails explicitly. Submitted panel batch case IDs
and load references are fixed before completion callbacks; changing an original
load array is still detected by its bounded value fingerprint. These integrity
checks do not establish F10/F11/F13 or full M3 acceptance.

Closing the B2 point-panel owner from its `on_case` completion callback stops
the batch before another case begins and returns the complete selected prefix
with `status="cancelled"` and an explicit closure reason. If every submitted
case has already completed, the batch returns `status="completed"`. Counts
are copied before the callback, so neither the operation nor a propagated
callback-error traceback retains the closed factor. The closed owner rejects
further solves.
Combining closure with token cancellation preserves the same complete prefix.
Callback programming and memory errors still propagate unchanged. This is a
callback-boundary contract, not concurrent thread-safe owner closure.

The physical B2 graph also checks affine applied work before solving, using the
same cancellation-aware projection as the panel. A nonzero work component that
cannot be represented, including one erased by congruence scaling, returns a
numerical failure rather than a plausible zero response.

Panel batch results include `displacement_envelopes` and
`affine_reaction_envelopes` for each selected DOF. Each immutable record gives
signed `minimum`/`maximum` values and their governing case IDs; exact ties retain
the first submitted case. Units follow the selected translation or rotation
coordinate. Cancelled or failed results describe only fully completed cases;
an empty prefix has empty envelopes. These summaries do not add member-resultant
envelopes or an envelope-only storage mode. ANYfem returns the same solver result.

The finite GE point owner also accepts an experimental
`stiffened_shell.StagedDeadLoadProgramme(model_identity, endpoints)` in the
existing `solve(actions, targets, ...)` call. Use the identity from `preflight()`.
Each endpoint is a tuple of absolute spatial translation-force `NodalAction`s;
the initial force is zero and successive endpoints are joined continuously.
Programme positions run from zero to the number of endpoints. Requested targets
must move forward and include every crossed integer stage boundary. For example,
targets `(0.5, 1.0, 1.5, 2.0)` first ramp to endpoint1 and then change direction
toward endpoint2. Endpoint forces are cumulative loads, not stage increments.
Moments, follower loads and line owners are excluded from this initial policy.

Results expose `load_position`, `load_stage_cursor`, `load_stage_fraction`,
`load_programme_identity`, `load_programme_complete` and the owned
`applied_dead_load` vector. Existing `load_factor`, accepted factors and controller
attempt factors carry programme positions in this mode; they are not force
amplitudes. Completion of requested targets is separate from completion of the
whole programme. Equilibrium uses the current absolute force, while total path
work cannot be inferred from final force times final displacement.

The whole immutable programme, including future endpoints, is restart-bound.
A new outer envelope and augmented inner identity prevent admission of a stripped
programme checkpoint as a legacy proportional-load checkpoint. Progress, force,
physical state, material histories and controller commit together; callbacks read
that accepted prefix. Chart rebasing preserves programme position and force.
Legacy proportional patterns and checkpoint identities remain unchanged. Changing
mode or a future endpoint after acceptance fails. A zero-force endpoint is
representable, but the existing strict zero-load equilibrium check may prevent
finite numerical completion after unloading; no residual floor is introduced.
This capability remains experimental and does not itself close F06 or qualify
the broader load programme.
