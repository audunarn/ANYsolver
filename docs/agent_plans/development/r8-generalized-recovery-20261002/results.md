# Cached generalized-beam material recovery — 2 October 2026

Status: IMPLEMENTED_NOT_QUALIFIED. Slice bases solver e78ae75e and ANYfem 481b4d1.
Public BL5 generalized-material and coupled-Q4 J2 results now expose native
station strain, resultants, physical frames, accepted plastic state and paired
energy densities. The actual evaluated material payload is cached against the
exact trial state and predecessor tuple, then formatted before publication.
Selected recovery returns detached arrays in requested element order without
another constitutive evaluation. Legacy routes lacking the required predecessor
contract return no such records. Physical-fibre recovery is unchanged.

Stored energy is endpoint elastic plus recoverable hardening energy (J/m).
Dissipation is the last accepted material increment from its fixed predecessor
(J/m); neither is cumulative or global energy. Native quadrature measures remain
reference arclength. Chart rebase preserves the accepted increment's records.
Snapshot restoration uses existing endpoint checks and saved accepted histories;
no schema, constitutive equation, acceptance tolerance or solver budget changed.

## Verification

Initial source run: 11 passed, 1 failed. Calling native paired-history validation
outside its 80-digit Decimal context rejected a valid yielded history. The helper
now establishes that existing context; no tolerance was relaxed. Failure retained.
Corrected focused source run: 12 passed in 29.78 s, supervised 30.77 s,
peak 177467392 bytes. Later rotated-frame and force-rebase tests are included in
the installed campaign below.

Installed solver: 19 passed in 255.42 s; supervised 257.42 s, peak 184446976 bytes.
Coverage includes field pairs/order/frames, mutation isolation, invalid material
payloads, the constitutive resultant identity, dissipation=Y*plastic_increment,
force/displacement restore, rebase preserving last-increment dissipation,
selected recovery with mechanics calls forbidden, stale predecessor rejection,
beam-generalized reversal, and the explicit -68um event-policy public endpoint.
No larger coupled physical path was executed.

Solver wheel SHA256:
`96e63373eeeb5d65c83797b0aa2987c264146dd620cfd9103fb358b70554079b`.
All 406 source/wheel/site modules match; 227 onsite imports, numerical pools at
one thread, JIT disabled. Jobs used the existing 600 s / 1 GiB bound.

Installed ANYfem: 2 passed in 75.45 s; supervised 77.60 s, peak 188723200 bytes.
Default and event-policy consumer workflows request generalized material records
after project roundtrip, cancellation, rebase and restored continuation. The
unchanged consumer product wheel was reused (tests changed), SHA256
`16e3d8634ecc0cdbc78c449066db448eddf312ead0f3119d45e9622ade57e754`.
Its 98 source/wheel/site modules still match against the new solver wheel.

Independent source review found no remaining blocker. It checked units, native
frame mapping, exact cache binding, publication order, force-rebase preservation
and restore semantics. Helper implementation and review had distinct owners.
OpenAI review does not establish cross-family scientific acceptance.

Archive `installed-public-v1.zip`, SHA256
`69c877de89d6b6714760ff443603ce0f83601755c81f6ad21179c39c4eea1329`.
Includes exact fixtures, source failure, corrected run, installed identities,
runners/logs, review and prior active note. Execution metadata is whitelisted;
inherited environment maps are excluded.

## Next scientific use and boundary

These records enable material-history assessment using actual accepted updates.
They do not prove global work balance, complete coupled reversal, full material
range or capacity. The historical coupled -500 N force-route failure and all
connection/F03, scale, external and release obligations remain open. Use the
records in one bounded unload/reload comparison before extending physical
amplitude; retain the existing tolerances, limits and failure evidence.
