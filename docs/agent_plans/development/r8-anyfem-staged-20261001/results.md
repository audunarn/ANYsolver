# Installed staged consumer slice — 1 October2026

**Implemented and installed-tested: ordinary ANYfem point-panel inputs preserve
an explicit staged translation programme and dispatch it through the existing
public GE facade.** Independent complete review finds no consequential consumer
defect. This is experimental behavior; no aggregate/material/load qualification
or release follows.

ANYfem branch codex/experimental-ge-panel-consumer, commit
`0f0981ded564519ed04f36e607afd7261d50b369`; parent6226230. Four owned files only:
consumer, Project adapter, focused metadata tests and existing consumer documentation.
Wheel SHA `92daa6370ca019a10de07779ac37238cf34be2bb4180752617d722344859dd75`.
Solver product9057067d uses the unchanged wheel
`0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c` retained in
[the product record](../r8-staged-load-20261001/results.md).

The separate staged-v4 envelope nests the existing point-panel v1/v2/v3 input
and the public owned programme descriptor. It preserves future endpoints and
identity; ambiguous legacy actions alongside a programme fail explicitly.
Save/reopen is structural validation and ownership, with no mechanical assembly.
Actual model identity is checked when the existing public owner is created;
the solver validates all endpoint nodes/scopes before trials. Persistence is
not a promise that every stored path converges or every material combination
is qualified.

Staged Project execution requires explicit programme-position targets and
forwards finite controls, cancellation and accepted-state observers. Legacy GE
reference-linear execution and B2 case batches retain their routes. Input files
do not embed, decode or replace accepted-state checkpoints; checkpoint/restore
continues through the existing opaque owner operation. Default selectors and
native .anyfem format version remain unchanged.

## Execution and applicable inventory

- Source metadata/dispatch checks:13 current cases; no mechanical assembly,
  with explicit public owner stubs/forbidden constructors. Original runs and
  the two changed-test reruns remain preserved.
- Installed V1: wheel build failed before tests because pip's shared cache was
  unwritable. Preserved log; V2 uses no shared cache with identical product source.
- Installed V2:51 cases,50 pass and one retained S3 numerical failure. The passes
  comprise13 metadata checks,36 existing Project/legacy/B2 checks and one real
  Q4 staged Project→save/reopen→solve→checkpoint/restore→continue workflow.
- Installed V3:only the affected S3 workflow runs, using the exact previously
  passed [F06 staged mechanical history](../r8-f06-staged-transport-20261001/results.md)
  instead of the newly chosen small-load history. It passes the same public
  consumer operations, eight accepted positions and direct restarted continuation.
  No solver tolerance, iteration/backtrack budget or product source changes.

The applicable scoped inventory is50 unchanged V2 passes plus one V3 S3 route,
**51 passes with the earlier failure still visible**. V2 is not an all-green run,
and V3 does not resolve or qualify its S3 small-load history. Exact manifests
bind388 solver and98 consumer module bytes to current source/wheel/site;
unchanged metadata/Project/common fixtures and wheel hashes justify reuse.
Product imports resolve to the installed site:275 V2/274 V3. One effective
BLAS/Numba thread and JIT disabled are verified in the target processes.

Q4 uses the historical pullback and two-stage small loads; S3 reuses the frozen
1MN beam load followed by the−/+375kN shell pair, unchanged eight positions and
default adaptation/20 Newton/12 backtrack limits. The new consumer route checks
public programme identity, applied force, equilibrium/compatibility, stage cursor,
physical poses/cell state/reactions and restarted accepted path. It does not
repeat or replace chart-reset qualification.

V2:20.744512s, sampled process-tree peak239456256B. V3:76.438799s,
217997312B under600s/8GiB. These are execution observations, not speedup claims.
Full commands, identities, exact fixtures, JUnit, raw Project files/checkpoints,
failures and wheel are bound by [manifest](manifest.json).
[Independent complete review](r8-anyfem-staged-complete-review.md), SHA
`f8aaab30f1f4b72ffdc7f1c0554fe8f76cc0c6e3d15510eee00f9842d5781cd9`.

Remaining: the original S3 small-load backtrack failure, broader staged material
histories/unloading/zero-force completion, moments/followers/line programmes,
consumer/API breadth, platforms and complete programme acceptance. Typed numerical
failure remains visible and is never represented as a completed result.
