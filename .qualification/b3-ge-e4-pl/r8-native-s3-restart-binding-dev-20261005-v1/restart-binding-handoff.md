# S3 restart binding and stale rebase test — 5 October 2026

Source parent `888be00b`. Only product-test edit:
`tests/test_stiffened_shell_native_s3_displacement.py`. No solver, fixture,
checkpoint format, tolerance or physics changes. No contact/sibling/Git actions.

The exact six common-CI failure selectors reproduced locally before edits as
4 S3 arc passes and 2 elastic-S3 failures (28.94 s; supervisor 31.25 s).
The latter expected chart rebasing to be prohibited, but the public controller
already admits and advertises native displacement chart events. The repaired
tests verify unchanged load, physical frames and native histories, generation,
dual-owner and reopened checkpoint identity, stale-generation rejection and
continued parity. Both affected cases pass (11.40 s; supervisor 13.78 s).
The supporting review delta additionally requires continuing the fresh owner
restored from the rebased checkpoint to the same target. It now matches both
live rebased owners' final state and checkpoint exactly. Rebase-v3 passes both
affected cases in 12.63 s (supervisor 15.41 s, sampled peak 185835520 bytes,
numeric/unresolved maximum one). V2 evidence remains preserved; no product
change or dependency screen was performed for this delta.

The four common-CI arc failures are at `seed()` restoring the existing
`tests/data/native_s3_fibre_history/unloaded-v1.bin`, before new continuation.
The exact log shows NumPy 2.5.3/SciPy 1.18.1, whereas the local successful restore
uses NumPy 2.4.6/SciPy 1.17.1. The decoded archived accepted element 1 local
coordinate 2 is `5.082197683525802e-21`; CI recomputes `6.77626358e-21`.
The earlier approximation of the truncated printed saved coordinate as
`6.082...e-21` was incorrect and is superseded by the decoded raw value.
The original log's pytest state representation truncates the saved vector;
its `committed_constitutive_u` excerpt contains `[-3.375....082197683525802e-21`.
That representation does not identify the missing leading digit. The exact
saved value above comes from the unchanged checkpoint payload, not that excerpt.
Dependency/backend arithmetic is a supported hypothesis, not a reproduced
actual-CI cause; owner layout, translation-policy and archive association remain
subject to the exact existing restore guards.

The bounded fixed-coordinate diagnostic changes only the largest Davenport
quaternion eigenvalue by one representable ULP in each direction. All eight
accepted/predecessor local vectors change; maximum absolute coordinate delta
is `5.421010862427522e-20`. Eigenpair relative residual stays at or below
`2.808666638682284e-16`. The physical archived checkpoint remains byte-exact
(`bf25a2c7e16172cfbf40df921809371eba28db8ae8f7ada232d655addc4461d5`).
This demonstrates exact-binding arithmetic sensitivity without asserting the
diagnostic perturbation is the actual CI implementation. Raw values and runtime
identity are in `eigenvalue-witness-v1.json`; supervisor completed in 2.43 s.

The initial default-sandbox exact-backend setup could not start: no locally built
NumPy/SciPy wheels were cached, and the bounded no-retry download could not find
NumPy 2.5.3. This does not establish that the released version is absent: the
attempt ran with restricted network and default sandbox permissions, and its
effective pip index policy must be considered. `ci-package-attempt-v1.json`
records the exact command, requested PyPI index, timeout/retry settings,
`PIP_NO_INDEX` and proxy-presence settings without exposing credentials.
`ci-package-availability-v1.log` preserves the output. There was
no global installation or substitute-backend experiment.

Root subsequently obtained the exact wheels through authorized network access
and installed an isolated task-local site. Numba 0.68.0/llvmlite 0.50.0 were
needed because the existing global Numba 0.65.1 rejects NumPy above 2.4.
Backend-ci-v1 stopped before pytest: the restricted context could not read the
new package site and the version/path assertions caught fallback global imports.
That startup failure is preserved.

The authorized local-access escalation for backend-ci-v2 verified NumPy 2.5.3,
SciPy 1.18.1, Numba 0.68.0 and llvmlite 0.50.0 from the isolated absolute site,
plus exact tested source/fixture hashes before pytest. All six original failure
selectors pass (31.84 s; supervisor 34.08 s, sampled peak 185712640 bytes,
numeric/unresolved maximum one). Wheel hashes, actual imports and effective
runtime are in `backend-ci-binding-v2.json` and `ci-effective-runtime-v2.json`.
Dependency versions alone therefore do not reproduce the CI failure on this
CPU/profile. CPU/BLAS dispatch, CI execution profile, previous test context or
actual CI source differences remained hypotheses at that stage.
No global environment, solver binding or immutable fixture changed.

The final authorized fixed-coordinate CPU-dispatch discriminator confirms both
isolated CI BLAS pools actually use Haswell. It decodes framing only and
evaluates the same eight accepted/predecessor coordinate sets, without history
restore/assembly, eigensolver perturbation, source/fixture edits or a core sweep.
All eight fail the unchanged exact saved/unforced-reference association predicate.
Maximum coordinate delta is `8.131516293641283e-20`; eigenpair relative residual
is at most `1.404333319145526e-16` and work residual `6.661332087714381e-16`.
Accepted element 1 coordinate 2 becomes `6.776263578034403e-21`, matching CI's
reported recomputed value. This demonstrates a real dispatch-sensitive route to
the archive association failure; CI's actual effective architecture remains
unmeasured. `haswell-runtime-v1.json`, `haswell-result-v1.json` and binding record
exact imports, source/fixture identity and raw values. Supervisor completed in
1.85 s, sampled peak 160571392 bytes and one numerical thread. All numerical
work stopped after this result; no binding/portability policy was changed.

The existing contracts are separate and both remain intact:

- `_restore_native_s3_histories` recomputes `d(q, anchors)` and binds the saved
  committed displacement and constitutive displacement exactly to that value.
- `_require_native_s3_replay` requires the full serialized accepted state to
  reproduce exactly from its saved predecessor and current physical endpoint.

The S3 state includes local committed total/constitutive vectors, material
history, stresses/strains, model identity and state-integrity hash. The outer
snapshot separately includes physical q, shell/predecessor anchors, predecessor
q and its own payload checksum. It contains no independent physical-input to
local-deformation association witness. Echoing the saved local vector would
bypass that association; it would also leave full same-predecessor replay
exposed to newly recomputed deformation. No such change is proposed as a fix.

Root's decision after the final discriminator preserves the legacy exact
archive contract. No dependency pin, relaxed guard, regenerated fixture or
forced production CPU setting is adopted. A forward repair must separate exact
archive identity from numerical mechanical consistency and define an explicit
compatibility identity and error budget for review before adoption. Existing
scientific criteria and execution authority remain unchanged.

Reserved forward choices, requiring that explicit contract decision:

1. Preserve the legacy exact archive contract and use the actual failing CI
   execution profile/source identity to discriminate arithmetic from a state
   defect. Local testing of the exact dependency versions now passes, so that
   comparison cannot establish the remaining CI failure's cause by itself.
2. Prospectively specify a portable numerical-consistency contract separately
   from exact archive identity, including the physical/local association and
   same-predecessor response requirements. This needs an explicit scientific/
   compatibility decision; an arbitrary rounding or tolerance edit is inadequate.
3. A future physical-input/local-state binding witness could preserve exact
   provenance in a new format, but requires a format/compatibility decision and
   cannot retroactively validate legacy associations or replace physical replay.

All jobs obeyed 600 s/2 GiB process-tree limits, one affinity, numerical pools
one and JIT disabled; effective settings are recorded. Raw reproduction failure,
successful two-test repair, JUnit, source bindings and eigensolver diagnostic
remain in this directory. No numerical job is active. Installed verification and
independent acceptance belong to root; no portability/qualification claim.
