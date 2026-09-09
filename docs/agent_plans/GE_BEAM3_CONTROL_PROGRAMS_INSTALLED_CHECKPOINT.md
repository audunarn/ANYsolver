# GE-B3 installed displacement and arc controls

This development-only package checkpoint binds source candidate
`f7c65a157bafc37ee9bd6cefbceff151710a1c62`, tree
`f159596e6789b803eb6da26b87d0ca833c05f108`. It changes no source module,
element mechanics, coefficient, tolerance, alias, default or old evidence.

## Isolated package check

The harness validates the preserved native, force, displacement, arc-geometry
and arc-program source bindings. It builds one private wheel from a source
snapshot, using the existing offline wheelhouse only after checking each
dependency's byte count and SHA-256. Historical resource request identities in
the wheelhouse record are not reused or treated as authority for this check.

The wheel is installed in a fresh external virtual environment. Two fresh
processes use isolated mode with repository paths removed. The standalone
fixture cannot import repository tests or research modules. Every loaded
ANYsolver module must originate under the installed package directory; each
bound installed source is checked after explicit UTF8/LF normalization.
Installed byte hashes are recorded separately, including CRLF differences.

Each process exercises a small curved beam with a coupled section and directed
hardening: displacement loading/unloading/reversal, three arc steps, split
restart, recovered load-parameter binding, and nonzero plastic history. Arc
restart uses the native preceding-origin and direction replay checks. Both
controls are cancelled immediately before and after commit, and their retained
capsules are restored. Resealed reaction mutation and duplicate JSON keys must
be rejected. This is package/state correctness, not independent mechanics proof.

The two canonical records and both accepted control capsules must be
byte-identical. No cross-runtime equality with earlier source-checkout results
is claimed: the offline wheelhouse has its own bound NumPy/SciPy versions.

Each subprocess has a 180-second timeout and one numerical-library thread.
The harness retains streamed stdout/stderr, terminates its child process tree
on timeout, and does not retry automatically. These small checks do not
constitute a performance test or a formal qualification wave. The package's
unchanged `0.4.2` metadata is private development metadata: this artifact must
not be uploaded as a replacement for a published wheel.

## Preserved harness incident

The first unfrozen test failed before equilibrium evaluation because its
fixture registered the section passed to the constructor rather than the
element-owned section. The production ownership guard rejected it. The
corrected fixture registers `element.core.section`. An additional harness
inspection corrected checkpoint hashing to hash raw capsule bytes rather
than passing bytes to the JSON-value hashing helper. Neither correction
changes the element, driver, material law, test targets or tolerances.

The failed script, wheel, source map and logs are preserved separately from
the corrected run. There is no fabricated failed-run canonical result. Exact
archive inventory, runtimes, hashes and accepted test results are recorded in
`docs/reference_cases/ge_beam3_control_programs_installed_evidence.json`.

## Completed verification and preservation

The corrected installed-wheel test passed in **143.29 seconds**. It verified
56 bound source modules in Python 3.13.9 with NumPy 2.5.2 and SciPy 1.18.1.
The two 14,307-byte result records are identical, SHA-256
`a30bf00d7be9485189cc41eb4968d2938c104f081618d12017e0675a5e486f69`.
The displacement capsules are 36,704 bytes each; arc capsules are 62,259 bytes
each. Both pairs are byte-identical, with their hashes bound in the receipt.

All 31 selected artifacts (3,056,574 bytes), including the failed first harness,
are preserved under:

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-control-programs-development-20260906-7e26dad29510`

Every archive byte count and SHA-256 was checked from the normal workspace
context after exclusive copying. Only verified relay duplicates and empty relay
directories were removed; original temporary outputs remain. The corrected
private wheel is 1,353,234 bytes, SHA-256
`7e26dad29510e282fdcbf6fa96d48ac7a2893e599a884cb0a8d7a722549f6415`.

Static evidence checks passed **26 tests in 0.61 seconds**, with separate
inventories: seven new installed-control checks, five arc-program checks,
four arc-geometry checks, five displacement checks and five prior installed
force-program checks. There was no mechanics rerun in this static suite.
Independent review remains pending; these are development tests only.

## Remaining programme

Next is bounded adaptive cutback with explicit accepted-step accounting and
transaction-safe restart. General section/load/constraint parity, loaded
modal and buckling, full straight/curved engineering qualification, independent
review, public integration and the objective beam-shell connection remain open.
This package checkpoint authorizes neither qualification nor activation,
version changes, publication or modification of existing B2/B3/Q4/S3 behavior.
