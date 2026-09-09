# P5 explicit 32-element lateral-onset successor

Parent `ef7964287245829b0112ae81179d314c5c2f00cb`, tree
`9a65ace10f68b8f57d1ac0794d8d190c67327ea0`. Freeze exactly the nine paths
listed in the new onset32 runner's `ALLOWED` inventory: five shared research
extent/validation paths, the new runner, two new test files and this plan.
The completed 4/8/16 research wave, all source equations and all production
mechanics/defaults remain preserved.

## Why one more explicit refinement

The consumed 4/8/16 wave demonstrated decreasing sampled onset-load error
(approximately 15.18%, 4.78%, 1.29%) and onset-drop error (20.41%, 7.67%,
2.16%). The remaining location error justifies a single finer mesh. It does
not justify arbitrary mesh growth or modification of an operator or tolerance.
The 16-element uncertainty bracket remains visible rather than being replaced
by an exact-root claim.

Execute **one new 32-element worker**, never the old workers. The prior
aggregate is immutable background: 5,160 bytes, SHA-256
`DBA974AA285EF1F25073FE3B539EEABDB6DC8627D96AFFAE6ABBCF1F8E62ED58`, at
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-onset-20260906-4e2f54a71be94bb1ad3a0b5df77dad05\aggregate.json`.
Its original dispositions and comparisons are copied as explicitly historical,
not recomputed or reclassified as successor evidence.

## Explicit extent, unchanged calculations

The research assembly gains the named `ARCH_ONSET32` profile. Its default
remains `SMALL8`; the existing `REFINEMENT16` profile remains bounded at 16.
Generic/unregistered `REFINEMENT32`, sizes above 32 and implicit promotion
remain rejected. The new profile supports at most 32 connected quadratic
elements. This case has exactly 65 nodes, 390 external coordinates, 378 free
coordinates after the two full end clamps, and 512 material stations.

The arch constructor, sampled-inertia inspector and onset probe require
explicit selection of the new profile for enlarged inputs. The default
inspector still rejects more than 33 nodes/186 free coordinates; the new
profile admits at most 65 nodes/378 free coordinates. Polar/axial reflection,
span scaling, eigensystem checks, the backward-error uncertainty formula and
cross-block coupling correction are identical. The old raw validator gains
explicit profile/schema arguments, with its old defaults unchanged.

No element residual/tangent, interpolation, section law, stationary solve,
assembly scatter, load work, material transaction, recovery or replay method
changes. Tests compare all assembly methods against the exact parent AST and
the constructor after its extent guard/maximum selection. The count extension
does not change reference coordinate/triad construction; nested nodes and
frames match exactly.

The scientific case remains the same parabolic arch (height 0.1, span 2,
fully clamped ends), six-component section diagonal
`[1000,400,400,0.02,0.01,0.02]`, eight-point rule on each half element,
elastic history, full spatial displacement-control equilibrium at `1e-11`.
The fixed thirteen-point drop grid `0,0.005,...,0.060`, maximum sixteen
bisections, `1e-7` width stop and unresolved-midpoint stop are unchanged.
There are at most 29 states; each has at most sixteen Newton correctors and
8,192 total mixed evaluations. Every bisection uses its saved accepted
positive endpoint; no mode is removed, no retry/cutback or interval extension
is performed. The whole conservative Hessian is inspected, not the controller
Schur matrix. A symmetric unstable state does not imply successful selection
of a post-bifurcation branch.

## Frozen inputs and independent-check boundary

Require clean ANYfileIO at commit
`b48ba51c7b79e6d64b3f99c1fb131b9b602e7e1d`, tree
`29cb248a8d320607e21424c68625c4af6a949da1`, and the same Python 3.13.9
executable plus complete non-bytecode NumPy 2.4.3/SciPy 1.16.3 file inventory
record, canonical digest
`2CD226A5CF78C9CC833DCBAF7E4CD0C8EAB92DD8566AF69412E13D346DC298F4`.
The previously frozen environment function validates these files before
numerical imports and at finalization. No dependencies are installed or changed.

Require both preserved knot-resolved continuum endpoint packets under
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-lateral-knot-20260906-e10841364c644b29b60f7c057c20a41e`:

- Stride 1: 29,126 bytes, SHA-256
  `64C47952DACD030D81EC3A631744179C300C33052551E1EBE5C16A9E191019FC`.
- Stride 2: 29,139 bytes, SHA-256
  `A7917C813953D181DF20748C5E54179E0F84597585650B641FBD46B90E8F073C`.

The successor compares both references with its newly measured drop/load
endpoints, retaining relative errors as diagnostics. It does not solve the
continuum again, select a favorable stride, introduce a new accuracy threshold
or upgrade any prior evidence. Endpoint load values are not a rigorous load
enclosure or proof of monotonicity within the bracket.

The coordinator recomputes raw physical constraints and full/even/odd spectra,
validates station/history/budget counts, accepted origin epochs, strict
canonical JSON, file inventories and every raw byte/hash binding, and replays
the deterministic search against raw samples. This is integrity/spectral
validation, not independently authored element mechanics or an independent
scientific review. Those remain necessary for production qualification.

## One-use execution controls

After the clean exact-path freeze, generate one fresh resource request for
the new coordinator's exact emitted command and a fresh external output path.
Obtain the resource administrator's APPROVED row, acquire that exact ID, run
the stored command once and release in `finally` only after the whole tree
is terminal. Neither prior consumed ID can be reused. The new runner requires
exactly one approval and no terminal row until finalization and creates its
own permanent exclusive request claim.

One child uses one numerical-library thread, 24 GiB maximum complete-tree
memory, a 600-second envelope and 300-second CPU/checkpoint inactivity bound.
The coordinator has an 890-second watchdog, within a 900-second wave ceiling.
The existing Windows Job containment, early termination timer and tree drain
remain unchanged. Global resource serialization still applies. No automatic
retry, hidden worker, old case execution or new parallel campaign is allowed.

Preserve progress, PID/start data, stdout/stderr, process resource records,
full raw trials and all uncertainties externally. A failed process, violated
authority or malformed evidence stops the run, retains a blocked diagnostic
and creates no canonical aggregate. No historical file is removed.

Only after the single child exits and validates, exclusively publish
`RESEARCH_ONSET32_DIAGNOSTICS_COMPLETE`. Keep the actual search disposition,
uncertain signs and historical comparisons visible. Always retain
`production_qualified=false`, `accuracy_qualified=false`,
`first_critical_point_proven=false` and `historical_recomputed=false`.
Resource accounting success is not scientific qualification.

## Pre-freeze tests and preservation

The new extent suite passed **13 tests in 3.92 seconds**; the runner suite
passed **24 tests in 0.41 seconds**. Tests cover explicit 32 construction
(without a 32-element response), rejection of larger/default-profile inputs,
synthetic 65-node spectral maps, unchanged small matrix uncertainty, nested
geometry, parent-AST calculation identity, count/history/hash mutations,
exact authority/lease guards, one-child failure preservation, deterministic
serialization and nonqualifying historical comparison handling.

Before extension, a three-state two-element smoke had canonical result
1,240 bytes, SHA-256
`357C80EDE0C6345FF32216CF3CFB749D2C39D7A760EEF3CD84AE699862FD89EF`.
Both old and new profiles reproduce that exact result and all three raw
byte/hash identities after extension. This is a small compatibility check,
not a 32-element solve or qualification certificate.

The final focused regression passed **242 tests in 37.24 seconds**, including
the new suites and unchanged assembly, restart, prior onset/refinement and
short real Windows containment tests. These are bounded small correctness
tests; no 32-element nonlinear state has run before this authority freeze.
Confirm `git diff --check`, the exact nine research paths and zero `src/`
delta at commit. Record actual request/process/evidence identities in a
separate documentary closeout after execution.

No push, merge, release, activation, production mechanics/default change or
S3/Q4 qualification change is authorized. Broad nonlinear material parity,
physical mass/dynamics, production restart/interfaces, independent review,
packaging and objective beam-shell connections remain open.

NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
