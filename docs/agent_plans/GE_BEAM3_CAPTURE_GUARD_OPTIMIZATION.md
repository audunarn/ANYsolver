# Profile-directed guard work reduction, unchanged physics and encoding

Baseline profile source07b70515c1bcf05a88550171f5457979874ff769. Archive
ge-beam3-capture-profile-07b7051-20260909 has13entries; manifest1277bytes SHA
DE6229D7DF613F606CC88EC94321E4866205AAD5741E2A7F0327BCEAFCFFA80E.
Profile138925bytes SHADEDEB9929864E0D2FF7E6E2F2D3ECED9CFBA0AA18B276E0BAFF45D77BD256733.
The original N8 captured packet matched its preserved bytes. Instrumented
capture29.897365s; model identity9900calls/12.324456s; cell guard87728calls/
6.253315s including section guard;322297JSON dumps and87917JSON loads.
Cumulative times overlap and must not be summed as independent costs.

Keep every existing callback, section guard, compiled-data guard, complete
model/state check, cancellation check, deadline, canonical encoding and SHA.
Add an immutable captured cell-identity helper which reads policy, section
identity, complete station-capture bytes and identity on every call. Bind
fingerprint method identities. On changed bytes use the ORIGINAL canonical
fingerprint and never adopt a changed snapshot. This is not an object-only
cache; original canonical equivalences remain accepted through fallback.

Avoid one duplicate controlled-state serialization per modal callback: the
native ownership check compares its single current serialization against BOTH
the issued record's snapshot and the modal capture's immutable expected bytes.
Continue checking the complete model and section inertia at every callback.

Before using finer search results: mutation-test live capture bytes, section,
compiled station maps, policy, methods, captured authority, foreign objects,
and simultaneous state/owner-table tampering. Run existing cell, controller,
modal and retained-state regressions. Re-profile the same N8 checkpoint and
require identical packet bytes. Capture the actual preserved N24 .045 checkpoint
twice unprofiled into fresh processes and require both packets byte-identical
to historical data. Do not rerun controller solves for either comparison.

All child/wave/memory/thread/nativeContext limits remain unchanged; exclusive
external outputs and no automatic retry. Preserve failures and raw profiles.
These measurements are development evidence, not a statistically powered
performance qualification or scientific onset pass. No S3/Q4/B2/B3 mechanics,
defaults, tolerance, state schema, package or release changes. Full beam/joint
goal and independent review remain incomplete.
