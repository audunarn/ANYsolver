# P5 compensated-coordinate assembly and transactions

Parent `1580ae3aa28a8097ce1e313030c72a9a85c8270b`, tree
`d69370b2a8d82eeceb1140dd2756819c85a0380f`.
Four added research paths: this note, compensated_assembly,
compensated_control, and compensated_assembly tests. No existing source,
scientific record, coefficient, tolerance or default changes.

## Explicit successor state

CompensatedAssemblyHistoryProbe retains the existing connected graph, section
origins, node rotation convention, scatter, physical residual normalization,
local station schedule and 1e-12 total estimated local-force budget. Local
evaluation explicitly uses the frozen CompensatedMixedBeamProbe.

CompensatedState and CompensatedTrial add normalized position_low arrays and
the exact `GE_BEAM3_P5_COMPENSATED_COORDINATES_V1` schema. Each element response
binds its mapped low parts and
`GE_BEAM3_P5_COMPENSATED_ASSEMBLY_FORCE_ACCURACY_V1`. These fields enter the
existing complete dataclass digests. No old checkpoint is implicitly upgraded
and missing schemas fail closed. They are numerical representation fields,
not new nodal DOFs or an activation of a public formulation.

Every additive nodal correction advances both coordinate parts. Physical
clamps retain their reference high coordinates and zero low parts. The new
displacement controller is separate from the historical controller; it sets
the prescribed target high part exactly and its low part to zero. The
constraint predictor subtracts both parts of the existing coordinate.
Both force and displacement paths use the existing spatial derivative,
including its rotational chart correction, for the Newton linearization.

Both solvers retain the global 1e-11 equilibrium limit, at most 16 updates,
10 backtracks, 256 mixed evaluations per element per trial, and the 0.9*pi
rotation-increment bound. No retry, adaptive tolerance or clipping is added.

## Atomic commit and reconstruction

Each trial uses fixed current committed material origins. Before publication,
validate complete trial identity, exact coordinate schema and pair normalization,
clamps, material origins, local policy/estimates, and element/trial low-part
agreement. Independently re-evaluate each local mixed potential at its accepted
local rotations/moments, reconstruct the Schur tangent and physical station
responses, and compare the complete response digest. Then apply the unchanged
global physical residual gate. A final-element failure prevents the entire
commit. Only after all checks does one checkpoint tuple assignment publish
positions, low parts, rotations, forces, histories and the accepted trial.

Accepted replay checks that committed high/low coordinates, rotations, forces,
schema and epoch match the accepted trial before reconstructing every element.
The controller additionally checks that the public trial agrees with its staged
assembly and exact prescribed coordinate before committing that assembly.
Copied inputs/exports and explicit ownership prevent cross-instance trials or
mutating failure sinks from changing the checkpoint.

Failure snapshots have the distinct
`GE_BEAM3_P5_COMPENSATED_FAILED_LAST_EVALUATION_V1` schema and include high/low
coordinates and coordinate identity. They remain detached, uncommitted last-
successful-evaluation diagnostics, possibly rejected candidates. No successful
evaluation means no fabricated snapshot. Candidate checkpoints additionally
report position_low_change_max so low-part activity is observable even when
high coordinates are unchanged. Observation/snapshot sinks cannot confer
commit authority or change the numerical result.

## Tests and boundaries

Small two-element tests cover plastic loading/unloading, discard, fresh replay,
deterministic serialization bytes, sub-ulp nodal corrections, prescribed targets,
interface force/moment balance including low-part lever arms, and assembled
energy/spatial-tangent directional agreement. Rehashed mutations cover schemas,
trial/element low parts, clamp values, local policy, material origins and missing
fields. Tests also inject a last-element replay failure, exhausted evaluation
budget, failed observation sink, cross-instance/legacy checkpoints, and staged
controller disagreement. Failures leave the previous checkpoint untouched.

Canonical serialization here means deterministic diagnostic dataclass bytes;
no external restart loader or production migration API is supplied. Generic
arc length, modal/mass, dynamics, full material parity and objective shell joints
are not qualified by these checks.

After the clean implementation freeze and full small rehearsal, prepare a
separate two-state 32-element comparison runner. It must bind all historical
failures, accept only the new coordinate schemas, validate low-part records,
retain the existing 600-second child / 24-GiB process-tree / 890-second outer
safeguards, and obtain a fresh resource request and administrator approval.
Do not rerun consumed requests or launch the larger onset sweep before that
comparison passes. All outcomes retain
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

## Development result

The six-file focused regression passed: 100 tests in 30.97 seconds, including
20 new compensated-assembly tests. An earlier negative test exposed an
unwrapped ValueError for an invalid committed coordinate expansion; this was
corrected to the explicit AssemblyTransactionError without relaxing any
validation. `git diff --check` passed. No 32-element mechanics, heavy resource
request, archived-worker rerun, production integration or qualification run
was performed in this implementation step.
