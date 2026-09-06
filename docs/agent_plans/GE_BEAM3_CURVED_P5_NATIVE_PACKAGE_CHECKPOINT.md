# P5 self-contained native package candidate

Parent `bc4a6dc30a3c2dd1254f4ee6adce4c8ff008ea06`, tree
`4834fc55b9763102cc8fdd88f092888d954efc91`.

## Outcome and qualification boundary

The native curved P5 candidate can now run from a built and installed ANYsolver
wheel without importing research files or using a source checkout. The internal
package is `anysolver._ge_beam3_p5`, with class `NativeP5BeamElement` and candidate
ID `CANDIDATE_GE_BEAM3_P5_NATIVE_PACKAGE_V1`. This is package integration, **not
qualification, public registration or a release**. The root package exports and
factory aliases remain unchanged; existing `ge-beam3` still refers to accepted P3.

The standalone and objective-joint goal remains incomplete. This checkpoint
does not authorize a public curved GE-B3 alias or erase any outstanding physics,
state-safety, engineering, parity or independent-review gate.

## Reproducible extraction rather than a new mechanics implementation

Seventeen internal package files contain only the required algebra, array
validation, section law, mixed stationary solve, compensated coordinates,
rotation-chart pullback, native element/state/codec, reference factors, retained
inertia and modal adapters. The extraction preserves the source equations,
coefficients, local solver budgets, tolerances and quadrature choices.

`ge_beam3_curved_p5_package_extract.py` is a standard-library-only, read-only
extractor/checker. It prints proposed files with `--emit` and verifies them with
`--check`; it does not write them, run mechanics or generate execution authority.
The source map binds parent Git-blob bytes/SHA-256, exact selected definitions,
import rewrites, class/identity renames, excluded obsolete bridge methods and all
generated file hashes. Original research implementations remain unchanged.

The old NativeMaterialSession driver and its obsolete core dispatch methods
are excluded. The installed candidate uses the actual native solver-owned state
protocol. Only the fixed typed-schema dataclasses/decoder needed by the native
checkpoint are extracted; no historical path runner, finalizer, resource manager
or filesystem restart publisher is brought into the runtime package.

Formulation/core/state/codec identities are successor identities. Numerical
responses must remain byte-identical, but research checkpoint identities must
not silently become packaged-candidate identities. Cross-identity state restore
is rejected. New packaged-candidate native checkpoint split continuation is
tested for exact equality with uninterrupted execution.

For shallow CI checkouts, missing source ancestry may use the canonical committed
source-map hashes only when Git explicitly reports a shallow repository. A missing
base in an ordinary local repository fails. Both paths are tested; this fallback
does not create new scientific authority.

## Source checks

The initial package-equivalence run had **11 passes and one failure in 17.11 s**.
The failure was in the new test helper: it used nonexistent `load_factor_end`
instead of the actual solver's `max_load_factor`. The helper was corrected to
use the established one-step half-load / resumed-two-step schedule. No mechanics,
history, tolerance or solver interface was changed to accommodate the test.

After correction and shallow-boundary checks, the combined source regression
passed **97 tests in 38.19 s**, with this inventory:

- `test_ge_beam3_curved_p5_package_candidate.py` (14 tests)
- `test_ge_beam3_curved_p5_native_committed_modal.py`
- `test_ge_beam3_curved_p5_native_modal.py`
- `test_ge_beam3_mixed_p3_optin.py`
- `test_nonlinear_state_cleanup.py`

Package/reference comparisons include elastic and active-plastic actual native
Newton responses, displacements, station histories, recovery, reference spectra,
current elastic spectra/operators and new-identity restart continuation. Compared
scientific arrays/records are byte-identical within the development runtime.
The directed hardening section remains the same single associative-flow test law,
not a new general fibre/J2 material implementation.

## Installed wheels and Windows source normalization

The global Python installation has editable repository paths even under `-I`.
The installed check therefore creates a **fresh virtual environment**, installs
the candidate and its hash-verified offline dependency wheels, uses isolated
Python in two fresh working directories, and rejects all `docs`/`tests` imports.
Every loaded ANYsolver module must originate inside the installed environment;
every internal P5 source file must match the bound source map. No research files
are shipped in the wheel.

The check runs actual native plastic Newton loading, exact split restart,
recovery, reference modes and current elastic-interior modes. The initial LF
installed test passed in **31.36 s**. A second test deliberately converted only
the disposable package build snapshot to CRLF; it passed in **31.38 s**. Each
test's two fresh processes produced byte-identical records. Six scientific hashes
(response, recovery, checkpoint, reference spectrum, current operator and current
spectrum) also match between the LF and CRLF builds.

Canonical source authority is explicitly `UTF8_LF`; actual installed byte counts
and SHA-256 values are recorded separately. This avoids confusing a Windows Git
checkout transform with a mechanics change, while still binding the exact wheel
and deployed files. `.gitattributes` is unchanged. Wheel archives themselves are
not asserted identical across separate builds.

The dependency graph is the preserved P3 offline wheelhouse (including NumPy
2.5.2/SciPy 1.18.1), verified before installation. Source tests use the existing
development runtime. There is no claim of bitwise equality across different
dependency versions or a new cross-version qualification campaign.

These are disposable development wheels retaining the repository's existing
`0.4.2` metadata. They are not replacement PyPI releases and must not be published
as such. No version, package dependency, root export or factory/default change
is made. No network installation, benchmark, formal qualification request,
resource lock, ledger entry, tag, push or merge is involved.

## Preserved evidence

Archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-native-package-development-20260906-e0d33c100ec2`

Twelve files (2,614,095 bytes) preserve both wheels, their source maps/check scripts,
both process results per build and receipts. Every copy was byte/hash verified.
The committed development-evidence JSON binds all twelve files and records the
explicit nonqualifying disposition.

Final CRLF wheel: 1,282,679 bytes, SHA-256
`e0d33c100ec23b90f8c701c18a72c219cdf31280f63c66c7665f5892e5b6b3c9`.
Final identical process records: 4,708 bytes each, SHA-256
`c9f99de36f66c3c6668dfa81f8f169cd282d3676e373c115bcae034cf191a1d3`.

The first archive copy encountered a Windows token/access mismatch reading
sandbox-owned pytest files; it created empty destination directories, not evidence.
The originals were preserved, copied through an explicitly bounded workspace relay,
then copied to still-absent archive files with fail-fast hash checks. No test was
rerun for this administrative issue. Only the verified duplicate relay files and
empty staging directories were removed; original temporary outputs and archive
remain intact.

## Next gate

Use this self-contained candidate, not an expanding chain of research imports,
for the remaining capability/engineering gates. Priorities remain native public
operator routing under explicit qualification authority, load-work/tangent parity,
fine-mesh compensated state representation, reviewed nonlinear section semantics,
straight/curved buckling/modal references and the separately qualified objective
beam-shell joint. Independent review and complete qualification are still required
before activation. All B2/B3/Q4/S3 mechanics and historical qualification evidence
remain unchanged.
