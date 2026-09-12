# G3b entry-safety successor

Parent: `41108c29db77f3910c07f1643a3c7307f51bdad8`, tree
`035388767b1d15d39ef089ba555d37a35a164a12`.

Its two-cycle rehearsal completed with identical scientific evidence in every
lane. Rehearsal record: 260,737 bytes, SHA-256
`9199db052943e209c317619519d0f8ce5f3fc4ac530a942051d1f9817c2e4b1e`.
This is preserved REHEARSAL_ONLY evidence, not formal confirmation. A separate
bounded local check exposed an additional owner-entry safety defect, so this
passing rehearsal is not sufficient to accept that implementation.

## Reproduced finding

If the publication property throws before transaction bookkeeping completes,
the original owner acquired its lock outside the protected cleanup region.
The accepted bytes survived, but the lock remained held even after restoring
the property. A resumed checkpoint failed with 'mixed owner busy'. The isolated
M_Q4 probe completed in 3.918 seconds, zero remaining children, with raw logs in
`C:/Users/AUDUNA~1/AppData/Local/Temp/anysolver-g3b-entry-probe-pn0f3xlo`.
The probe and all previous records are retained; this is an author-run local
safety finding, not an independent review.

## Narrow correction and verification

Move all fallible bookkeeping into the try/finally region after acquisition.
Read rollback authority directly from the private publication registry, not
from an overridable property. Restore only successfully captured state and
always release the lexical lock. No element mechanics, recovery equations,
coefficients, tolerances, public routing or defaults change.

Add ten regressions: all five families with a raising publication view and a
forged publication view. Each preserves an accepted prefix and cached factor,
verifies lock release, restores the external dispatch, then requires fresh
restart and continued solves to match. Targeted lane: 10 passed in 9.70 seconds
(`anysolver-g3b-development-pqw4unar`). Complete correction lane: 180 passed in
118.64 seconds (`anysolver-g3b-development-2fe9_lyv`). Both bounded processes
exited successfully with zero remaining children.

Inventory V1 remains unchanged. Inventory V2 preserves the original ordered
170 correction cases and appends these ten, binding the actual passing stdout.
All seven other lane inventories remain unchanged and are reported separately.
Entry-case scientific records use the existing accepted/replayed-journal schema.

The source-only runtime fingerprint necessarily changes. The expected owner
packet is derived from the preserved 135,368-byte packet by substituting only
its five runtime fields:

- Old runtime: `a34ad4cc5fbec1515ee5e336e68903294d0d3bc28db118dacc3db5258b1862bf`.
- New runtime: `cae1aa34442449beded2bace6028e77d31b0dc51549fce8a2210d281953dc4b5`.
- Expected packet SHA-256: `acee4a3a6350a99fa830e2007ce664e6386afe86036d00d1e436a6f4ba6ca49f`.

This is a preregistered expected-fixture derivation, NOT manufactured evidence.
A real owner run produced exactly those bytes: 60 passed in 25.33 seconds,
`anysolver-g3b-development-4m8b3but`. Authority validation separately passed
62 tests in 18.63 seconds (`anysolver-g3b-development-ls60sxxz`), and runner
validation separately passed 21 tests in 0.40 seconds
(`anysolver-g3b-development-vt4wn7dn`). All three process records report success
and zero remaining children. All six historical family and transport packet
hashes remain unchanged. A new clean freeze, two fresh rehearsal cycles,
genuine independent review and two formal
cycles remain required before formal G3b acceptance. Old output directories
must never be resumed or reused.
