# B2 free reference modes — development result, 4 October 2026

The existing public B2 mixed reference-modal owner now has an explicit
`B2_FREE_FREE_MODAL_ONLY_V1` boundary policy. It returns six checked physical
rigid fields and selected finite flexible pairs for the bounded connected Q4,
mixed Q4/S3 and all-S3 point-coupled controls. This is experimental implementation
evidence, not F07/F12/G4B acceptance or complete modal/nullity qualification.

Source parent: `111aab68a55332de623e2bff76434483be8613f3`, branch
`codex/stiffened-main-reconcile-20261001`. Final changed module bytes and wheel
are bound in [installed-final/binding.json](installed-final/binding.json). The unreleased
0.4.7 wheel SHA256 is
`dea651b918e92871ffc017c6a435dd1f265d22e86f9a307d00d12ebd4abfa27b`.
Tests: free-file SHA256
`6a88e8d66b3f75c57a8e3b0c86e512c56f7d2f3b8d189aa5be4e40abd1e9fbb1`,
mixed-file SHA256
`520601798a9526f11c8f3e72f2e9ba73de946639a2f6ebceeafefdf311b18754`.

## Mechanical and lifecycle contract

`B2MixedReferenceModalDefinition.boundary_policy=None` preserves the historical
supported route, eager static factor and result contract. Explicit free policy
requires identity transformation, zero prescribed offset, connected incidence,
declared physical mass and the existing virgin inertia policy. It admits only
`modes` and `close`; static and body-load operations fail before numerical work.
Footprints, prestress and unsupported inertia remain rejected.

Canonical fields use common translations and rotations about the shell-node
centroid. Actual assembled K/C must annihilate them within existing tolerances
before projection. A bounded 6x6 kinetic Gram provides normalization. The sparse
negative-shift descriptor retains zero multiplier mass and massless primal
coordinates. Congruence-coordinate projection acts before the mass action and
after the shifted solve. No dense production nullspace, inverse, mass floor or
invented inertia is introduced. Recovered finite pairs retain actual physical
equation/constraint checks and rigid/flexible mass-orthogonality checks.

The near-zero flexible screen is a roundoff-resolution guard, not a certified
eigenvalue bound or proof of exactly six mechanisms. Connected incidence alone
does not prove that nullity. No complete spectrum, repeated-space envelope,
physical/external accuracy, line-law or drilling qualification is claimed.

## Checks actually executed

- Source supported/mixed controls: **52 passed**, portable `_8m1vp3b/P01`.
- Initial new free controls: **19 passed, 1 failed**, portable `6ajqund2/P01`.
  The failure was a test expecting ValueError from the historical closed-owner
  API, which raises `ExperimentalB2Q4PanelError`. Corrected the test expectation;
  product behavior was preserved. Failed runtime/resource/selection records
  remain in `source-initial-free-failed/`.
- Final new free/affected footprint controls: **44 passed**, portable
  `wywxaw_k/P01`; exact command/log in `installed/source-final.log`.
- Installed coherent candidate: **96 passed** across the four affected modal
  files. [Installed command and resource record](installed-final/resource.json),
  [log](installed-final/installed.log), [runtime](installed-final/runtime.json).

The independent bounded homogeneous dense descriptor pencil uses separate
assembly/mass oracles. Controls cover Q4/mixed/all-S3 flexible pairs and kinetic
subspaces; six canonical rigid fields; physical K/C and kinetic Gram; actual
frame, translation, triangle-reversal and equivalent-unit behavior; unchanged
operators; no construction factorization; static/empty-batch rejection;
cancellation/numerical/programming failures; corrupted rigid operators; and an
extra positive-inertia mechanism not hidden by projection. Dense computations
are restricted to the 54-DOF oracle fixture, not production assembly.

Python 3.14, JIT off, plugin autoload off, two observed BLAS pools and Numba each
at one thread. Installed runtime confirms **236 imported ANYsolver modules**
all came from the candidate site. Changed product modules match source, wheel
and site byte-for-byte. Source runs used the repository portable development
runner, normal conftest included. Installed run used an isolated pytest config
without source pythonpath; disposable supervisor/checker are retained.
All numerical jobs were serial and terminal, ceiling 180s/2GiB. Installed run
sampled peak 195440640 bytes and 11.684 seconds including startup; source final
193028096 bytes and 9.959 seconds. These are resource observations, not a speedup.

## Review and remaining work

Supporting non-implementing OpenAI review examines the complete source and
oracle slice in [review.md](review.md). It does not satisfy the required
different-family scientific acceptance. No publication, merge, version/default
change, F03 authority consumption or external comparison was performed.

Next independent delivery: expose this explicit policy/result through the
existing ANYfem B2 modal consumer and persistence contract, preserving old
supported records. Current consumer still rejects free-free. M2/F03/G0 remains
open: actual 8:1 kernel/beta, growing-space stability and regional/physical
accuracy need their own defensible resolution; this slice does not bypass them.

Final byte hygiene: two product files were normalized to the original HEAD LF,
removing a whole-file line-ending diff. Parsed AST equality is recorded in
[line-endings.json](line-endings.json). Source and supporting review apply by
this exact semantic equality; final installed96 checks bind the new artifact.
The initial assertion failure and redundant intermediate-v2 execution are
preserved, not described as mechanics failures or development savings.
Initial installed records/review source hashes remain unchanged for their
original identities; installed-final supplies the delivered artifact binding.
