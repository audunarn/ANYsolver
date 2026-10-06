# Native material BL5 arc continuation candidate

Status: IMPLEMENTED_BUT_UNVERIFIED source candidate; no execution authority. Neither
source tests, an installed artifact nor scientific acceptance have been established.
OpenAI owns this slice because Mistral/local availability is already exhausted.

## Early checkpoint

The existing tangent-plane corrector already assembles through the coupled finite
driver from the actual accepted shell/beam material predecessor. Its physical
metric includes nodal translations and physical shell/beam rotations; retained
coordinates remain equilibrium unknowns and are not additional metric terms.
The shared affine endpoint validator already recognizes native BL5 histories.
The obstruction is POINT-only arc admission, history serialization and checkpoint
identity dispatch, plus the explicit public native-BL5 arc refusal.

The candidate reuses these services: equilibrium is R(z, lambda)=0, and the frozen
physical tangent plane is n dot chord(z,z_previous)=radius. Predictor and corrector
use the existing bordered solve, free translation orientation, cutback bounds and
fixed accepted material predecessor. No constitutive equations, attachment laws,
tolerances, default controls or backend are changed.

Planned changes are a private native-material BL5 arc identity, full native beam
and Q4/S3 histories through the existing displacement payload layout, ordinary
nonadaptive affine-force or fixed-translation seed admission, atomic publication,
fresh restore and compatible accepted-prefix continuation. Existing POINT and
generalized BL5 arc identities must remain unchanged. Chart rebasing, staged or
external seeds, adaptive/event histories and branch/capacity qualification remain
outside this candidate. Tests and a public example will be supplied but not run.

Reserved decisions: root acceptance of this DEV route and any future execution
authority. No mechanical or public compatibility change is proposed.

## Implemented route

`continue_arc_length(actions, ArcLengthControl(...), steps=...)` remains the
existing experimental API. An explicit private admission helper requires the
constructed finite BL5 native-material domain and one of the two existing native
fibre material policies. A generic native-history flag does not admit arc solving.
The mixed policy retains its existing all-S3/mixed Q4-S3 J2 construction guards;
the earlier Q4 native material policy retains its own construction guards.

The checkpoint uses the existing `ANYSSARC1` outer framing, with distinct kinds
`finite_arc_native_fibre_bl5` and `finite_arc_native_fibre_bl5_mixed_shell` and
policies `B3_GE_NATIVE_FIBRE_BL5_TANGENT_PLANE_V1_DEV` and
`B3_GE_NATIVE_FIBRE_BL5_MIXED_SHELL_J2_TANGENT_PLANE_V1_DEV`. The mechanical inner
payload reuses the corresponding native displacement kind or S3 material codec.
It carries accepted and actual last-predecessor physical fibre/generalized
histories, Q4 layer states, S3 state blobs and S3 predecessor coordinates/anchors.
The distinct shell-chart policy is
`B3_GE_NATIVE_FIBRE_BL5_ARC_UNREBASED_SHELL_CHART_V1_DEV`. Existing native POINT V1/V2
and generalized coupled BL5 identities/readers remain unchanged.

Ordinary nonadaptive nodal dead-translation force endpoints and existing fixed
translation endpoints seed this controller. Shell anchors must be identity or
absent; chart events, trial event policies, adaptive schedules, staged programmes
and external load contexts are refused. Subsequent calls must preserve the
controller, metric and affine load direction of the saved accepted prefix.

Each trial uses the unchanged accepted shell/beam origins. Cutbacks do not advance
them. Decoded endpoints are replayed on an isolated owner with the common affine
validator; publication binds predecessor digest, physical poses, material origins
and applied load before the existing locked atomic commit. Cancellation and typed
selection failures propagate with the already accepted prefix intact. Successful
calls return `completed`; recovery and fresh restoration retain `accepted_prefix`.
Observers receive accepted prefixes. Full indefinite equilibrium still includes
cells, resultants and multipliers. Stored zero nodal-layout tail coordinates are
an existing representation invariant and are not a removal of retained mechanics.

## Explicit metric limitation

Root adopted the existing full-frame `PhysicalChordMetric` for this DEV candidate.
For a pure shell normal spin theta with unchanged position/director it measures
`2*w*(1-cos(theta))`, which is positive. It is objective under a common rigid
rotation, but it is not a position/director quotient or gauge-invariant distance.
No attachment stiffness is added by this metric. Retained variables/multipliers
are excluded from its seminorm while remaining in the full bordered equilibrium
solve. Radius measures the existing local frozen tangent-plane projection, not
an exact global arclength, mesh-independent step size or capacity indicator.
The local pi/2 chord-domain guard, scientific tolerances and controls are unchanged.

## Supplied but unrun verification

`tests/test_stiffened_shell_native_material_bl5_arc.py` supplies all-S3 and mixed
ordinary/fixed-translation seed workflows, exact fresh restoration and continued
checkpoint equality, actual named material recoveries and retained-state equality,
older Q4 native-material payload identity coverage, injected typed failure and
before-step/after-prefix/atomic-commit cancellation, malformed cross-policy/history
replay, changed-controller and unsupported seed refusals, and a local normal-spin
metric/objectivity regression. The numerical rejection test is explicitly injected
and does not establish a real nonlinear cutback or turning-point reference.
`examples/stiffened_shell_native_material_bl5_arc.py` supplies the public workflow.
It chooses equal positive weights explicitly; these are not inferred mass or a
scientific quadrature prescription.

No Python process, AST/compile/import, test, build, install or numerical check was
run for this slice. Source reading and scoped Git diff inspection are the only
verification evidence. Shared historical process accounting does not establish
remaining execution authority, and has not been renewed here. Future bounded
checks require explicit authority and should first execute these impact tests plus
the existing POINT arc/selection/chart and generalized coupled arc regressions.
Source/installed artifact binding, independent acceptance, different-family review,
physical mesh/unit/stability G4D obligations and scientific/release gates remain open.

## Final source handoff

The candidate is connected through the existing public controller, isolated
endpoint validation and atomic publication services. Source inspection found no
need for a new API, new mechanics or altered stored retained-coordinate invariant.
Root adopted the explicit full-frame metric limitation. The final tests use the
previously demonstrated mixed/biaxial/continuous-P1-coarse translation definition
for simultaneous physical-fibre/S3 positive history; other controls do not assume
simultaneous yielding. All material recovery records are compared recursively,
including arrays, high/low contents, station identities, frames and measures.
An unrun derivative test uses the driver's actual updates for physical and
retained coordinates and an actual assembled full bordered-system RHS. It is
planned regression evidence, not a measured tangent or cutback result.

Only source reads, source writes, native file hashes and scoped Git status/diff
inspections were performed. Scoped `git diff --check` found no whitespace issue.
No execution ledger was edited or execution authority consumed/renewed by a test
child. Sandbox status reported known protected-artifact visibility deletions;
none were restored or edited. Read-only HEAD was observed as
`4305f789cd017f9bb689d4aba73ff38b301cddcb` during final inspection; Git integration
remains with root. No sibling files or closed evidence were edited.

Remaining gates: execute the supplied tests and public example under new explicit
bounded authority; inspect failures and real material/retained-state evidence;
preserve historical POINT/generalized arc regression identities; verify a newly
built installed artifact; independently assess the complete candidate; and retain
all physical/scientific/release obligations. Zero test pass claims are made here.

## Source byte inventory

| Owned path | SHA256 |
| --- | --- |
| src/anysolver/_stiffened_shell_affine_endpoint.py | 5c8bf8f980fc440f63cb1ac5dca83de4d96cfcb0c5b675b8aa7a7cf2cabd50b5 |
| src/anysolver/_stiffened_shell_arc_control.py | 1046b50d8a8aa846856a7c21e3d2517410d43d8b6bf2cd64225835909ae39c22 |
| src/anysolver/_stiffened_shell_arc_trial.py | 3363e64fae192eea7f6e9c79b632258da2ffedef828a40a2d6716acb3195f17b |
| src/anysolver/_stiffened_shell_arc_checkpoint.py | 30d5fc11c18e115403e30a1333ff47d7b226286f1719513095111ce6b5e31083 |
| src/anysolver/_stiffened_shell_arc_publication.py | 40fd75ed8e5082af4db599a479a7f8e2e307f4b5eb594f6328819d8f8626a1fe |
| src/anysolver/_stiffened_shell_ge_experimental.py | fbc26f1c95f432928c423ebc3886d12f2d33e6f86b9229a28676cde07b2491b2 |
| tests/test_stiffened_shell_native_material_bl5_arc.py | 0fc2f4c4814d01db847140d5a1d6fffdbc397184468998b23c846f4317352c74 |
| examples/stiffened_shell_native_material_bl5_arc.py | 2e1e92a33b67fadfa531ea8e9603e7c11e5fdb7fd941161fb1c16bf68bb071ea |
