# Native event-sequence path routing — development, 2 October 2026

The explicit transverse_event_sequence selection now routes strictly signed endpoints
through complete event detection, released-ending replay, closed-ending replay, or
certified no-event persistence. A single schedule is reused for closed replay.
Initially active opening replay keeps its first window and releases before reclosure.
Exact-zero endpoints retain historical admission/rejection. Other activation policies,
historical sphere behavior and public defaults are unchanged.

Definition identity is NATIVE_S3_OPEN_CLOSED_EVENT_SEQUENCE_POINT_DEV_V2. New initial
checkpoint roundtrip passes; a constructed exact V1-definition checkpoint is rejected.
This is definition safety, not a coupled accepted-load restart qualification. Released
endpoint replay from initially active state carries its own V2 result profile.

## Evidence

- Three routing/identity checks passed: 4.68s pytest.
- One saved second-load closed point (.79, pi+.013) replayed through the history field:
  3.89s pytest; endpoint gap -0.0007044226760777762m, zero cumulative friction dissipation.
  Its final branch is persistence, not multiple recontact. No equilibrium claim.
- New initially active three-event opening replay and existing independent two-event
  scalar work passed. Single-release parity initially failed because its reference
  rotation .8 was outside the old global monotonicity certificate. Failure retained.
- Reference-admitted .3 rotation parity passed: 3.62s pytest, numerical comparison
  1e-12 relative/1e-14 absolute for discrete work. No mechanical gate was relaxed.
- Reviewed persistence history guard and changed result profile: two checks passed,
  3.90s pytest. Released history at an initially closed persistent point now rejects.

Eight distinct focused checks passed over these slices (one rerun after profile change).
All runs: JIT off,180s/953MiB portable development runner. Full successful/failed logs,
runtime, selection and sampled resources: event_sequence_routing_raw.zip. Final source
hashes/resources: event_sequence_routing_source.json.

Owned OpenAI reviewer closed_sequence_review found the persistence/history inconsistency;
fixed with a matching-partner guard and negative test. No further confirmed errors in
opening-window composition or shared cap. Read-only review, no numerical execution;
not independent engineering acceptance or cross-family assessment.

## Remaining integration

Moving-front aggregate helper still only accepts one released-origin segment and open
captured endpoints. Closed material replay does not extend its zero-force strip proof.
Next question: can stationary uncertainty strips be certified open locally while the
rest of a panel carries ordinary closed contact, instead of rejecting the whole panel?
Use the existing manufactured pulse with axial variation plus a closed neighboring region
as a bounded discriminator. Derive force/work error handling before omitting any strip;
retain budgets and do not replay the saved fullpatch yet. Multi-segment cumulative work,
closed-strip tangent bounds, native second load and split restart remain incomplete.
