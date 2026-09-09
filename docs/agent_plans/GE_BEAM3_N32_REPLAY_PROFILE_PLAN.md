# Bounded N32 native enrollment/replay profile

Parent e7187248adbd9b5bbdb5470b1b823162fec02075. Four additive research paths:
this plan, ge_beam3_call_observer.py, ge_beam3_n32_replay_profile.py and
test_ge_beam3_call_observer.py. No src, mechanics, state or guard changes.

Run one uninstrumented control and one selected-call observed diagnostic, serially
in fresh external worker directories. Each creates the original positive seed
owner with targets (.0075,.010,.015), restores the preserved actual target-one
checkpoint and compares the complete checkpoint bytes. No owner.solve, Newton
advance, recovery override, target change, timer reset or formal qualification.

Use the immutable accepted seed chain and preserved branch archive manifest
586fa4cf92e5e12a1fb12c8334aafd41f79b9f245b62534b2bc1df9478808be5;
target-one checkpoint SHA-256
6d6d4790cff22761f2c04f0fcc9172630eebbf49f386f4b540047984e223b226.
Runtime source/environment guard must pass before mechanics imports and at end.

Selected-call wrappers invoke the original exactly once, forwarding all arguments,
return objects and exceptions; ExitStack restores them. Record nested inclusive
and exclusive wall/CPU times and call counts, separating enrollment and restore.
Retain original 120-second native context deadline. Measure enrollment, restore,
full-model identity validation, constraints, assembly, record and recovery. This
is a selected-call profile, not a complete call graph or a benchmark speed claim.
Observer overhead is visible through the control; timing differences are diagnostic.

The existing Windows Job supervisor supplies 600 seconds and 24GiB per tree,
one numerical thread, 120-second CPU inactivity and 1800-second full wave bounds.
No retry. On failure preserve receipts, logs and any profile emitted in finally;
do not fabricate absent checkpoints or complete diagnostics. Both terminal workers
and byte-identical checkpoint/state/completion outputs are required for a completed
diagnostic comparison. Raw timings stay external and are not scientific evidence.

Use the measurement to select a separately reviewed optimization, not to weaken
identity validation or scientific acceptance. All existing qualification evidence,
defaults, B2/B3/Q4/S3 and the full unfinished beam/coupling goal remain unchanged.
