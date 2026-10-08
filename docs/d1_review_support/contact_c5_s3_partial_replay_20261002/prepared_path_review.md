# Prepared S3 pressure path — development scrutiny, 2 October 2026

Scope: rational whole-path eligibility, exact P1 pressure moments, stage batching,
cache/resource accounting and query independence. No engineering acceptance.

The bounded Mistral Read review completed targeted reads but ended with HTTP 504,
without an assessment. Its retained log is
`C:/ANYworkspaceWork/contact-friction-prepared-path-review-20261002.log`.
OpenAI read-only reviewer `/root/prepared_path_scrutiny` supplied fallback scrutiny;
no tests or edits were performed by that reviewer.

## Finding

P2: `_stage_frames` retains a bounded snapshot of already cached frames but only
consults it for the prepared route. With ordinary cache capacity one, cached t2
and requested chunk (t1,t2), constructing t1 evicts t2. The implementation then
reconstructs t2 or incorrectly exhausts its construction budget despite retaining
t2 in the snapshot. Consult the snapshot for both routes and test this eviction
case. Fix deferred until the currently executing source-frozen integrated run
terminates; the frozen run must remain bound to its recorded source.

Disposition: fixed after the run terminated at its900-second limit. The ordinary
cap-one eviction regression and prepared/ordinary parity pass in
`contact-friction-replay-cache-profile-v2-20261002.log` (3passed15.93s, including
the saved residual cost discriminator). Frozen source snapshots are unchanged.

## Mathematical assessment and limits

The reviewer found the rational Bernstein conversion and source-normal projection
certificate consistent under the owner's conforming-disk assumption. The pressure
formula matches full-triangle P1 moments with unequal nodal gaps. Grouped event
processing preserves each material point's stage order.

Existing tests principally cover a stationary target and one replay segment;
moving/deforming targets and accumulated multisegment histories remain checks to
complete. Rational eligibility alone does not bound floating-point cancellation
when evaluating converted coefficients near degenerate geometry. These limits
remain open and do not confer broader admission.

## Follow-up: event partition reuse

The same Read reviewer found no actionable defect in skipping repeated entry
detection on partitioned substeps without fresh active anchors. The full segment
is partitioned before stages, every active/open interval is sampled, and fresh
anchors still call the original entry calculation. Ordinary endpoint calls retain
unconditional checking. Moving/straining-target multiframe parity compares all
returned states/outputs against unconditional substep checking. Four focused
checks passed11.79s; see partition_reuse_result.json and its retained raw paths.

Remaining numerical counterexamples: multiple pulses within one affine segment,
near-coincident roots and intervals whose midpoint rounds onto a boundary. The
shortcut relies on ordered exhaustive intervals and their representable samples.
No tests were run by the reviewer. This scrutiny neither resolves the integrated
timeout nor establishes acceptance.
