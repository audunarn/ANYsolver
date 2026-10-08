# F03 read-only case replay: bounded prerequisite result

23 September 2026. Complete-case adjudication and read-only replay now share
one saved-evidence computation. Exclusive adjudication writes the first case
receipt; replay recomputes the same predicates, work and physical observations
and compares them with the sealed receipt. Replay does not write to the case
directory and does not assemble, factor or solve equilibrium.

Replay requires the exact plan-archive SHA-256 from the validated
registration binding. It verifies bounded owned `plan.zip` bytes before and
after recomputation, reopens the semantic plan, and validates the sealed
receipt against saved evidence and independently reconstructed bindings. A
valid re-ZIP with unchanged plan payload but changed ZIP bytes is rejected.

Independent review found one provenance gap in the initial refactor and
verified its closure. The final focused suite passed **29 tests**;
`git diff --check` passed. No scientific case was registered or launched.
G0B remains open and G1 barred. Cross-case adjudication, the serial one-use
coordinator, registered execution and postexecution review remain open.
