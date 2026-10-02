# Distributed BL5 consumer integration — 2 October 2026

ANYfem local commit 330cb22 with solver 58286d90. Separate strict distributed-load
and distributed-programme envelopes nest the unchanged objective-Q4 BL5 v2 input.
Public descriptors are copied through canonical serialization, remain exclusive
of nodal actions/programmes, and keep their model identity. Project reference-
linear dispatch now uses the selected load; programmes require explicit targets.
Model-mismatch failure closes the newly created owner. Old v1/v2 meanings persist.

17 focused source consumer / installed solver checks passed in 36.583 s, sampled
peak tree 197246976 bytes. 53 installed checks passed in 36.556 s, peak 203399168
bytes. Coverage includes fixed-load resultants, standalone and native Project
round-trip, strict nesting/identity/exclusivity negatives, ownership and cleanup,
signed force/couple stages, cancellation, chart rebase, disk checkpoint restore,
exact continuation and affected existing point/BL5 Project formats. No failures
occurred in these campaigns. These are verification costs, not speedup claims.

ANYfem wheel SHA256:
`091b5d747d5376a275c5d0d03cfbafd0251c9b3b82a292a53ef2ff01dc66b786`.
Solver wheel SHA256:
`dd8ce52c2ab4ce072f4e4540f89e6fa5deb4600ed3511b2a1669de62f954cc74`.
All 98 consumer and 398 solver source/wheel/site modules match byte-for-byte.
All 284 imported solver/consumer modules came from the isolated site. Windows,
Python 3.14.2; actual BLAS pools and Numba 1 thread, JIT disabled. Version 0.4.1/0.4.7
unchanged. Each supervised numerical run uses 600 s / 1 GiB, with no competing run.

Independent OpenAI Read review found no consequential format, dispatch, ownership
or cleanup issue. This is not a different-family or physical mechanics acceptance.
Root inspected scope/diff and executed source/installed verification.

[evidence-v1.zip](evidence-v1.zip) SHA256
`4cbd3d672675eefcdadcae86d96bda0b7c14bb4c55e125d49c0b0e66c526f0d3`.
[evidence-v1.json](evidence-v1.json) binds 22 entries, including runner, exact test
fixtures, raw output, safe execution fields, dependencies/imports and module
identities. No full environment copied. Archived prepare/run scripts reproduce
no-index builds and isolated installed execution under the existing supervisor.

No new solver mechanics or qualification claim. Full physical BL5 reference,
materials/S3/topology, pressure-policy, scale, platform and complete-release
obligations remain open. No push or publication.
