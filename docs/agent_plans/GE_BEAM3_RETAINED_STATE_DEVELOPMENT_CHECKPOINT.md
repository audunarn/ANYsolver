# GE-B3 retained-resultant state/recovery checkpoint

Status: **private elastic development progress; qualification incomplete**.
Independent review: **PENDING**. No public selector, activation or release.

Base: `176b506011dc18f11bed30fe97533bc9699c1308`, tree
`6d65ed2c410550d8dd8e16e143430d6703c0afd8`.

## Implementation

The accepted-for-development retained-resultant research operator is ported
into a private package module without changing its geometric potential or
compliance construction. Byte equality against the preserved prototype is
checked at nonzero increment charts. The new return arrays own immutable
byte-backed storage. The prior failed V5 force evidence is unchanged.

New candidate: `CANDIDATE_GE_BEAM3_RETAINED_ELASTIC_V1`.
State schema: `GE_BEAM3_RETAINED_ELASTIC_ACCEPTED_STATE_V1`.

The standalone private controller retains nodal positions as normalized
high/low pairs, nodal rotation matrices, cell rotations and all cell-force/
endpoint-moment unknowns. It captures the model, section/reference identities,
supports and complete force schedule. It still uses the existing private V5
containers for geometry and section input; it does not replace the public
beam class or integrate with the central analysis dispatcher.

Trials are separately owned. A complete model-bound canonical capsule is
staged only after equilibrium and compatibility are both at most 1e-11.
The accepted state and capsule have one publication point. Cancellation or
failure before that point retains the preceding accepted state. Cancellation
after publication retains the newly accepted state. Model mutation is checked
before publication. No material history is committed to historical V5 stores.

Restart rejects duplicate/nonfinite/noncanonical JSON, wrong array types,
improper rotations, non-normalized coordinates, violated supports, incorrect
schedule/cursor/records, wrong formulation and changed model identity.
Reaction and recovery-bound evidence is recomputed: simply rehashing a forged
capsule is not sufficient. Historical V5 capsules cannot hot-restart this
candidate. Resuming a paused schedule is not a retry of a formal request.

Physical station recovery uses complementary strain fields and retained
moment variables. It reports engineering strains/resultants and reference/
current frames with formulation provenance. It does not invent fibre stresses
or plastic history. Compatibility with the geometric fields remains an
explicit equilibrium gate rather than a post-hoc overwrite of force unknowns.

## Evidence

Separate inventories:

- Initial state/restart suite: 24 passed, 10.764 seconds.
- Initial recovery/objectivity suite: 4 passed, 3.684 seconds.
- Final suite A: 36 passed, 14.459 seconds.
- Final suite B: 36 passed, 14.469 seconds.

All **nine JSON output pairs** from the final suites are byte-identical.
These are small correctness tests with one numerical-library thread, not a
performance or formal resource gate. Timings are diagnostics only. Runtime:
Python 3.13.9, NumPy 2.4.3, SciPy 1.16.3. No cross-runtime equality claim.

The native private controller reproduces the earlier prototype state exactly
at curved L/h=100, 10000 and 1000000. A separate L/h=1000000 schedule uses
parameters `(1,2,4,8,16,8,0,-4,0)` and tip-force pattern `(0.05,-0.001,0)`.
It loads, unloads, reverses and returns to the virgin configuration within
the tested tolerance. At parameter 16 its tip displacement is approximately
`(0.02716,0.08235,0.04623)`, exceeding 0.05 in magnitude. Uninterrupted and
restarted continuations have identical final capsules.

Additional tests cover thirteen rehashed checkpoint corruptions, invalid
JSON, foreign schedules, immutable arrays, exhausted Newton limits,
cancellation at four precommit stages and immediately after commit,
publication exceptions, model mutation, legacy-state rejection, and input
ownership. This is tested elastic state safety, not nonlinear history parity.

Recovery checks integrate station forces and curvature back to the retained
dual variables, verify the supplied coupled section law, and compare section
energy with complementary work. The largest observed force-integral error
is 4.6469e-12 at high slenderness, below the unchanged 1e-11 gate. This result
does not establish a general recovery error bound.

Objectivity tests hold the reference geometry fixed and superpose rotation
vector `(2.6,0.8,-0.3)` and translation `(1000,-2000,3000)` on the finite
current state. Potential, kinematic variables, residual, tangent and recovered
fields satisfy the registered 1e-11 checks at L/h=100 and 1000000. This is
stronger than re-expressing both the reference and current geometry together,
but remains a finite set of tests rather than an independent proof.

## Preservation and boundaries

External archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-state-development-20260907-f9933ac3804c`.
Its 36 content files total **316,240 bytes**. The additional manifest is
**11,331 bytes**, SHA-256
`862ae603a1a4a7f61d9f2743d0c86083477122de2ce0ce471725c09e252edcec`.
Each external file was verified by byte count and SHA-256 from the ordinary
workspace context. Original temporary test outputs remain; only verified
relay duplicates may be removed. Preliminary smoke reports are not separate
frozen authority. The source snapshot binds the two final suites.

The private controller admits at most 256 retained coordinates, bounded
Newton/backtracking counts and a 120-second cooperative deadline. It does
not provide a hard process-tree or memory watchdog. Formal execution still
requires the registered external runner/resource controls; no resource
request or ledger was consumed or changed in this work.

Three private source modules are added. No existing tracked file, B2/B3,
accepted straight beam, qualified Q4/S3 mechanics, defaults, aliases,
dependencies, package versions or workflows are changed. No wheel is built,
published or substituted by this checkpoint.

## Remaining programme

Next is a source-derived complementary nonlinear-section/state formulation,
including objective trial/commit/discard and fibre-section parity. The
retained candidate remains virgin elastic-interior only. Broader geometries,
slender/continuum convergence, finite loads and load tangents, displacement/
arc-length continuation and postbuckling, mass/modal/buckling integration,
scalable assembly, package isolation and independent review remain open.
Objective eccentric/curved beam-shell connections remain part of the full
goal. Nothing here authorizes public integration or complete qualification.
