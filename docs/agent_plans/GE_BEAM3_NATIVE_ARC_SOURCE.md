# Explicit native translation-to-arc source

Base c8be153d27af07818e2dd291370a2ccced517663. Preserve existing beam/shell
mechanics, native tangent/parameter-column algorithms, defaults and unseeded
arc bytes. Add a private TranslationArcSource carrying the exact translation
programme, complete canonical checkpoint, external SHA-256 and explicit forward
trajectory sign. Handoff uses its latest accepted non-genesis state;
it cannot select or discard a later accepted source record.

The source and arc must have identical model, loads and history profile.
Seeded arcs require neutral old initial_sign=1; the explicit source control
sign determines follow/reverse orientation. Use the existing GENERAL predictor
with the metric-normalized last authenticated spatial displacement/rotation
increment and load-factor increment, rejecting a zero last increment. Rotation
differences are the actual spatial increments verified by the source codec,
not accumulated vectors interpreted as orientations. Then use the existing objective
frame-chord arc equations. Rotation coordinates remain spatial increments.

The source is decoded and fully validated; retain every genesis/source snapshot
and append new arc snapshots with consecutive material epochs. The arc records
remain separately indexed. A distinct TRANSLATION_SOURCE schema embeds the
exact source packet and binds its descriptor/hash in the arc programme.
Every checkpoint revalidates the source prefix, full combined chain, predictor,
arc constraint and signed loads. Reject combined source+planned arc history
above 65 snapshots before execution; keep 2/8-MiB explicit profiles and 60-second
validation/600-second process bounds. No validation cache or omitted history.

Unseeded source=None preserves existing descriptors, schemas and canonical
bytes. Source/programme mutation at a safe point must preserve the last
accepted arc capsule. Original input/source histories are not rewritten.
A handoff is not hot restart across formulations or a conversion of
translation rows to arc rows.
An incoming arc checkpoint's external hash must be checked before source replay.

Change only the new source module, native arc setup/descriptor branches,
arc checkpoint envelope, focused tests and this plan. Test both capacities:
analytic bar continuation/reversal, complete source-prefix equality, exact
resume, hash/type/profile/load/orientation/genesis/history-count rejection,
resealed embedded/descriptor/prefix/predictor/schema mutations, objective secant
covariance and zero-increment rejection, live-source
mutation and unseeded rejection. Separately test a curved plastic source with
combined line/couple loads, continued plastic history, physical recovery and
exact prefix restart. Re-run original local/safety/history-profile
inventories separately and compare old scientific bytes.

Run bounded rehearsal, freeze and two fresh-directory deterministic replicas.
No automatic retry. Preserve failures before any correction. Each child:
one numerical thread, 24 GiB tree memory, 600-second wall and 120-second
CPU-inactivity limits; at most three concurrent, 1800 seconds per wave.

This is implementation of an explicit continuation interface, not an actual
arch crossing or production qualification. Assess sixteen-macro source/replay
cost before an actual crossing; do not relax the validation deadline if it is
too expensive. Arc step adaptation, wider parity, mass/spectra, independent
review, installed integration and objective shell connections remain open.
