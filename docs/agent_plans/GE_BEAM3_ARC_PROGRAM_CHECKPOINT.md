# GE-B3 native objective arc-program development

Private successor of `4f32c356d6c162d4d04aeeaf91c659ba48640103`.
The new `_ge_beam3_arc_program` module connects the verified frame-chord
geometry to the native beam assembly, load derivative, rotations and material
transactions. It changes no existing source file, mechanics, coefficient,
tolerance, selector, default or prior qualification/incident record.

## Predictor/corrector

The predictor uses the full border `[K, R_p; (M previous)^T]`; its direction is
normalized in the explicit metric and oriented consistently with the preceding
direction. A singular border fails; there is no stabilization, spatial-mode
deletion, automatic branch switching or assumed positive global stiffness.
The corrector uses the actual native residual/tangent, its parameter column and
the frame-chord hyperplane row in the same native increment chart.

Metric scales, initial load sign, positive step sequence and update/backtracking
bounds are explicit program inputs. The metric is isotropic within each spatial
translation/rotation triplet, normalized by the model node count. It is not a
mass matrix or stiffness regularizer. Unrepresentable metric weights and a wholly
zero declared load pattern fail before beam assembly. The native standalone
model/support restrictions remain; general joints and MPCs are not enabled.

Each predictor is based on the accepted origin. All correction and backtracking
trials use its unchanged material histories and solver-owned multiplicative
rotations. The hyperplane uses actual translation and Exp-coordinate increments,
not world-position subtraction or a linear accumulated-rotation constraint.
The native line work is already in the residual and is not counted again.

This stage has explicit fixed steps, no automatic retries or cutbacks, a
cooperative 600-second deadline, and bounded Newton/backtracking loops. Formal
execution still requires the separately authorized process-tree/memory runner.
Ordinary sparse factorization cannot be interrupted by a cooperative callback.

## Restart and atomic acceptance

The complete canonical capsule is staged before commit. It contains the model
and program identities, explicit metric, accepted parameter, shared global
coordinates, physical imbalance, continuation direction, ordered records,
current typed element states and the complete preceding accepted origin.

Restore validates canonical keys/types, hashes, size/depth, supports, exact
reaction replay and accepted equilibrium. Current and previous element states
are independently replayed from their saved algorithmic origins. Their epochs,
parameters and material-history linkage must match. Nodal rotations must obey
the actual native multiplicative update from the saved origin, not a reconstructed
accumulated rotation vector.

The last frame-chord equation is recomputed. Its predictor is recomputed through
the actual native assembly and parameter derivative at the saved origin, and
must match exactly. The origin's orientation is linked to the preceding path
record (or initial signed direction). Invalid capsules cannot silently choose a
different orientation, metric or physical history. This is an operational
restart guarantee with last-step replay, not a complete independently certified
mechanical replay of every earlier path point.

Cancellation before commit, staging failure, exhausted iteration bounds and
failed correctors retain the preceding accepted capsule. Cancellation after
commit retains the newly accepted capsule. Observer changes to bound inputs fail
validation. Unaccepted native/material trials are discarded.

## Development observations

Initial 19 checks passed in 27.87 seconds. Expanded 30 checks passed in
86.72 seconds. They cover a full-border singular-stiffness algebra witness,
elastic equivalence at the solved force parameter, plastic split restart,
origin/direction/metric/record mutations, both sides of commit cancellation,
staging failure, deadline/iteration bounds and strict JSON rejection.

The native two-element arch uses the same small specimen as the displacement
stage, with all spatial free DOFs retained. Eight steps of `0.02` produced load
parameters approximately `0.018615, 0.032645, 0.035666, 0.032939, 0.028178,
0.022737, 0.017427, 0.013149`, with 3--6 corrector updates per step. The sampled
branch continues past its sampled maximum into decreasing load. The final
capsule successfully replays its saved origin, predictor and arc equation.

This is not an exact critical-point location, bifurcation classification,
stability/PSD proof, continuum accuracy result or engineering post-buckling
qualification. Earlier formal arch/onset studies remain unchanged. Independent
review remains pending; this driver is not root-exported or publicly registered.

## Final verification and preservation

The combined source regression passed **201 tests in 293.57 seconds**. Its
eleven test-file inventories are listed separately in the canonical development
record. The new arc inventory has 32 tests, including proper coordinate-frame
covariance with coupled section properties and mutation of the metric program.
Python 3.13.9, NumPy 2.4.3 and SciPy 1.16.3 used one numerical-library thread.
These are development correctness checks, not timing acceptance or a formal
resource campaign.

The eight-step arch checkpoint, status and complete progress trace are
byte-identical between two fresh pytest processes. Six files, **204,522 bytes**,
are permanently archived under:

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-arc-program-development-20260906-edab037cfc2c`

Every archived file was exclusively copied and checked against its recorded
byte count and SHA-256 from the normal workspace context. Only verified relay
duplicates and empty relay directories were removed. Original temporary output
and all earlier archives remain. Each accepted arc capsule is 82,113 bytes,
SHA-256 `d61ceb10fc0571a860caf2cf62aaabe7415d12d73134e08e616d881421ff7df8`.

No installed-wheel execution of the displacement/arc successor has run. Earlier
force-driver wheel evidence does not qualify these later modules. No formal
request, independent review, publication or public activation occurred here.

## Remaining programme

Next: bounded adaptive cutback with explicit accepted-step accounting, and
installed-wheel checks for the new displacement and arc drivers. Broader
section/load/constraint parity, loaded modal/buckling, independent review,
straight/curved engineering qualification and the objective beam-shell
connection remain part of the active goal. No release or activation is
authorized by these development observations.
