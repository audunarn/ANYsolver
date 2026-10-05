# Main reconciliation — 1 October 2026

The user authorized the first coordinated integration step. Owned pending work
was saved at `0726662badddc6a7dbc59fe631d9a14ca72856c3`, preserving the original
development checkout and its foreign dirty F03 script. The script remains SHA256
`c908b1f3e4d9467deb3a96876126d5488cd040503cc6c6ec485b8aeaecef9481`.

Remote main was verified with `git ls-remote` at
`ef85882858533eb82086810c04eec58d18fe625a`. A history-preserving merge completed
without conflicts at `d31e09dca6b615d85758b5858485c83b4c24f984`, on
`codex/stiffened-main-reconcile-20261001`, in
`C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001`.
All six incoming solver modules match the pinned main exactly; no product repair
was needed. Main and the original branch were not merged with this candidate.

Installed solver wheel SHA256:
`a80d4a862b2155292baf385549d430baa22865056b5343ee8454cd8fa8a11435`.
The child processes verify all 391 source/wheel/site Python modules and actual
onsite imports. The consumer source remains
`f4bb5ed2eecc21c915a3b78519f84b1a773d0a61`; its new wheel is
`baed94eb40e85861d8af553a6e56e685550464f8d01f9b39f14dd2f1e7bc225e`.
Its 98 source/wheel/site modules are checked independently.

## Impact checks

| Check | Result |
|---|---|
| Main plane-stress, trusted guards, spectral preparation, S3 element/model checks | 280 passed, 6 skipped |
| GE footprints, V2 chart restart, staged material histories, finite stepping, supported/free-free modal checks | 141 passed |
| B2 physical batches, panel constraints, cancellation, selected recovery and factor reuse | 76 passed |
| Public V2 footprint chart/restart example | Passed |
| ANYfem installed consumer compatibility | 173 passed |
| Enabled-JIT cache and plane-stress checks | 13 passed |

Five skips in the first row are cache checks subsequently passed with JIT enabled; the remaining
skip explicitly concerns an absent base-critical API for that profile. No skipped
check is counted as a pass. There are 684 passing test executions across the
listed groups, including repeated plane-stress controls under both JIT settings;
this is not a unique-test count. These are bounded compatibility checks, not formal
F03 execution or aggregate acceptance. The preceding footprint artifact evidence
retains its original identity; this merge does not silently rebind it.

All numerical jobs are serialized with the contact task. Each process tree has
a 600-second and 8-GiB ceiling, with actual one-thread BLAS/Numba checks. JIT is
disabled except for the explicit cache checks. No performance improvement is
claimed. GE checks took 489.730 seconds, peak sampled tree RSS 213,221,376 bytes.

## Retained failures and limits

The first wheel build could not write pip's cache; the uncached build succeeded.
The first main-impact collection lacked the S3 helper script. The first B2
collection lacked its graph helper. The next B2/example run passed all 76 B2
checks and failed only because the example's sibling module was missing from the
installed test fixture. Adding those unchanged fixture dependencies enabled the
affected checks; no product equation, tolerance or test assertion changed.

Raw working evidence is under
`C:/Users/AUDUNA~1/AppData/Local/Temp/r8-main-reconcile-20261001-v1`.
Source manifests, imported paths, fixtures, execution logs, failed attempts and
JUnit inventories are retained. The adjacent raw archive and inventory preserve
the source snapshots, wheel artifacts, runners, fixtures and test outputs.
[Archive](raw-v1.zip) SHA256
`b10b37f787554bf529b7c960bbccee6fbc58c86c2caabbcd40384bae516802b3`;
[inventory](raw-v1-identity.json) binds 2,062 files, each reread from the archive
and checked against its SHA256.
Consumer checks used 278 onsite imports and took 188.377 seconds; enabled-JIT
checks passed with actual one-thread pools/Numba and took 12.545 seconds.
All owned numerical jobs are terminal; the slot was released to the contact task.

The contact owner is reconciling its separate branch. Its Newton initialization
conflict and trusted-cancellation integration correction are owned there. This
report makes no combined contact/stiffened capability claim. The final independent
footprint artifact assessment, explicit ANYfem V2 policy record and all broader
programme gates remain open. Wider feature development and release are outside
this first step.
