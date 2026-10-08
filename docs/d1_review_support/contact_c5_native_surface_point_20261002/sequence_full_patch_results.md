# Saved full-patch event sequence — non-success preserved

First full-patch run: support128,560queries,78support panels,10.14s test call.
Endpoint-scope discriminator finds mixed open/closed endpoints but strictly negative
whole-segment derivative [-4.197127e-6,-2.336799e-7] in first unresolved rectangle.
New transverse cover therefore admits mixed endpoints only when all potential roots
share one orientation (at most one crossing per point). Opposite orientations still
require strictly open endpoints. Existing endpoint law remains authoritative.

Second full-patch run: support128,80queries,3support panels,1.43s test call. Temporal
refinement stalls on spatial uncertainty in an endpoint pressure-front guard strip.
Added existing derivative-width non-success rule: yield unresolved to spatial refinement
when spatial width dominates temporal width. This cannot admit contact or skip history.
Three focused tests pass: analytical pulse/tangency non-success, saved two-event local
rectangle, saved mixed-endpoint monotone rectangle. No final full-patch rerun yet.
Tangency test initially over-specified MemoryError; changed to accept explicit unresolved
or named cap exhaustion, never resolved. That test failure is retained in raw.zip.

No solved second load, restart equivalence, accepted speedup or acceptance claim.
Next run the saved full patch with this final candidate once, then derive event-front
spatial ownership if complete rectangular proof remains obstructed. Do not keep adding
arbitrary temporal/spatial tuning or increase caps. Closed-ending multiple-event point
history remains unimplemented. All raw resource/runtime/selection records retained.
