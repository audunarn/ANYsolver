# Independent bounded review

Reviewer: /root/b2_point_acceptance_gap; read-only, no numerical runs or edits.
Implementers: root (solver/recovery/tests), bl5_consumer (ANYfem records/adapter/tests).
Root separately reviewed the consumer work. This is a complete development-slice
review, not formal acceptance of a foundation or aggregate milestone.

Initial finding: linear cancellation safe point preceded the new O(points)
reference recovery loop. A cancellation during that loop could still publish.
Correction: final publish safe point after capture; regression cancels during
capture and checks identical accepted result and checkpoint. Closure confirmed.

Requested low-position regression was added. Its initial tuple multiplier input
failed strict binary64 admission. Reviewer initially endorsed its mathematics
but missed that API detail; the installed failure and correction are retained.
Final array-input test passes and retains the subspacing lever-arm couple/lows.

Final source review: correct minus-spatial-residual signs, reference C mapping,
current spatial rows before chart pullback, point-first row ordering, frozen model
IDs, owned immutable tuples, same-state identity guard, no extra evaluation during
recovery, and correct regeneration on restore/rebase. Accepted payloads are not
replaced by rejected trial caches. No remaining actionable source finding.

Consumer review: exact selector pair, strict schema/status/source, public consumer
decoding, deep detachment, save/create revalidation and explicit absence of Project
geometry regeneration. Defaults remain legacy. Inputs-only native persistence
does not imply accepted-state persistence or ordinary job execution integration.

Artifact closure independently confirmed: V1 XML171 cases (170pass/1fail), V2
XML1/1 selector equal to the V1 failure. Union171 distinct passing IDs; no all-green
V1 claim. Source maps and wheel maps match; sole fixture change tuple->np.array.
387/98 modules match source/wheel/site; effective threads1/JIT off. Failure and
resource outputs preserved. No torque/drilling fidelity or M1/M3/F13 acceptance.
