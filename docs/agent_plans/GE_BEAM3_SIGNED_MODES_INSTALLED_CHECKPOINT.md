# GE-B3 signed modes — installed-wheel checkpoint, 2026-09-07

Frozen candidate `2b0ee70beda6f12e81bb57aa95195c424364a23d`, tree
`f8a21473610c6e05abe92847f796c0ea80ff88b2`. This checkpoint adds only a package
correctness harness, evidence inventory, documentation and static tests.
No existing mechanics, state laws, defaults, dependencies or public routes change.

## Exact isolated artifact

The harness archives the committed candidate's source/package paths and builds
one private wheel. It binds 67 source modules: the prior 65-module reference,
state/control and modal graph plus the two signed-mode modules. Source identity
uses explicit UTF8/LF normalization. The isolated build deliberately converts
those copied source files to CRLF, verifying the existing Windows line-ending
policy; installed byte hashes and normalized source hashes are recorded
separately. No working-checkout source is substituted for the candidate archive.

A fresh virtual environment installs the wheel from the preserved offline
wheelhouse. The ten dependency artifacts are hash-checked; their historical
resource request is not invoked or reused. Both workers use isolated Python,
remove repository search paths, reject `docs`/`tests` imports and verify that
all imported ANYsolver modules originate from the installed target. Private
signed-mode functions/classes must remain absent from package-root exports.

Each subprocess has one numerical-library thread and a 180-second test safety
limit. A timeout kills that owned child process tree. Outputs are exclusive,
logs remain external and failed commands are not automatically retried.
No timeout or test failure occurred. Retained stderr contains only disabled
byte-compilation warnings and the known Git user-ignore permission warning;
no ACL or Git configuration was changed.

The private wheel is `anysolver-0.4.2-py3-none-any.whl`, 1,387,052 bytes:

`063937aa20e41960404c36cfef1e67c0946cb231732464ad85b4cfeba3f9a7ef`

This is a development artifact with unchanged source metadata, **not a release**.
It must never replace the published ANYsolver 0.4.2 artifact or be published
under that existing version. No tag, version change or publication is authorized.

## Installed checks

Five independently constructed small fixtures execute the actual installed
native force/state path and signed-mode adapter:

- One-macro L/h=1,000,000 compression, retaining both negative bending modes.
- One-macro L/h=1,000,000 tension.
- Two-element curved, coupled-section beam with shared traces and cell inertia.
- Curved elastic unloading after a genuine plastic history.
- Free curved beam with six near-zero rigid modes and a positive next mode.

The two straight cases use the preserved rational-coefficient, 80-digit
finite-shear discrete reference, embedded without importing research modules.
Static AST comparison verifies that both reference functions are unchanged.
This is same-author reference reconstruction, not independent review.
Moderate curved spectra are compared with the preserved dense loaded solver.
All cases check residuals, physical mass normalization, state preservation,
load-parameter mismatch rejection, private result scope and exact native replay.
The common record's `negative_count` counts values below -1e-11, distinguishing
instability from rigid-mode roundoff. Full signed eigenvalues are retained
unchanged in external diagnostics; no solver clipping is performed.

Both fresh processes use Python 3.13.9, NumPy 2.5.2 and SciPy 1.18.1. This is
distinct from the earlier source-test NumPy 2.4.3/SciPy 1.16.3 environment;
byte identity is asserted within the installed environment, not across runtimes.

The installed-wheel test passed in **61.63 seconds**. The two 17,834-byte result
records are identical, SHA-256:

`a46d38b7319ecfdeba21c1f63a8b7b28af73685807645315442fac3db047286c`

All ten diagnostic pairs (five states and five full pencils/mode sets) are also
byte-identical. The separate static suite passed 27 tests in 0.52 seconds:
seven new installed-checkpoint checks, eight signed-mode checks, seven prior
signed-spectrum checks and five prior installed-reference checks.

## Preservation and remaining scope

The 39-file, 3,552,060-byte archive includes the source zip, wheel, source map,
worker, receipt, stdout/stderr and both complete record sets. Every file was
verified by byte count and SHA-256 from the normal workspace context:

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-signed-modes-installed-20260907-063937aa20e4`

The canonical inventory is
`docs/reference_cases/ge_beam3_signed_modes_installed_evidence.json`.
Original temporary outputs and all historical archives remain; only verified
relay duplicates are removed. No formal resource request was consumed.

Independent review remains PENDING. This closes this private module's installed
correctness check, not full modal/buckling qualification. Multi-element
high-contrast curved/coupled validation, broader engineering and geometric-domain
coverage, general nonlinear section parity, performance/scalability and
objective beam-shell connections remain required before overall completion.
