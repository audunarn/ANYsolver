# Arithmetic benchmark setup incident

Frozen `e84cf586cfa0dd346708e91e32005d541cbc25ee` was invoked once at
2026-09-07T13:59:35.6541947Z and exited 1 at 13:59:37.8741803Z.
External evidence remains in `ge-beam3-inertia-benchmark-20260907-v1`
under the existing ANYrelease root; transcript is
`ge-beam3-inertia-e84cf58-transcript.txt`. No benchmark aggregate exists.

The harness supplied a zero-argument checkpoint to `_reduce`, which calls
it with a stage string. It failed before inertia measurements, with
`TypeError: worker.<locals>.check() takes 0 positional arguments but 1 was given`.
This is a harness signature defect, not an arithmetic or mechanics failure.
The correction accepts both callback forms while preserving the deadline;
a regression checks stage-bearing calls and expiry. No failed output is
deleted or reclassified. A successor freeze must use a new external directory.
