# G3a independent review: formal confirmation blocked

Decision: **BLOCKED_G3A_IMPLEMENTATION_REVIEW**.

Reviewed candidate: `5a4a4ac6a6e6130153ad7e8eb32a482dacd06129`,
tree `afa9d6011d467fc16d361d525fd05587692a8a71`.
Frozen contract parent: `e78c1b667694b43141912c1d85f894de2b41a848`.

**No G3a formal cycle was launched, runner authorized or confirmation
certificate created.** This is an acceptance-coverage block, not a numerical
NO-GO or loss of previously accepted element qualification.

## Independent findings

The canonical five-key review is
`reference_cases/ge_beam3_g3a_implementation_review_v1.json`.

1. **G3A-IR-01: per-graph S15 coverage.** The frozen contract requires these
   checks for every native graph. Full stationary/Schur verification, including
   nonzero internal residual, currently covers N_BRANCH3 and N_BRACED5 only.
   N_RING4 and N_DISJOINT2 need the same check. Loaded physical covariance is
   checked only on N_BRACED5; explicit shared-Q/incident-triad checks cover only
   N_BRANCH3. Complete the missing graph-specific matrix.
2. **G3A-IR-02: rollback/token coverage.** Last-element preparation rollback
   currently covers N_BRACED5, while cancellation covers N_BRANCH3. Complete
   both checks for every native graph, with genuine accepted prefixes.
   Add the preregistered N_BRACED5 stale/foreign-issued-token cases, checking
   committed bytes, both generations, history, no active trial, authenticated
   checkpoint replay and subsequent continuation.

Both are verification nonconformances and block formal execution despite their
P2 labels. Passing the existing tests cannot replace absent frozen cases.

## Separate restart observation

A bounded read-only reproduction changed a valid virgin checkpoint's graph
policy to MIXED or supplied a nonempty unregistered adapter allowlist, and
resealed the external digest. Restore initialized all three native elements
before rejecting the serialized graph identity. No mixed element/adapter was
invoked; the original owner's checkpoint and state remained byte-identical,
with no trial. This is late validation of inert metadata, not demonstrated
unsupported-route acceptance or state corruption.

Move policy/schema/allowlist validation ahead of native initialization in the
successor and add an early-rejection regression. The review explicitly
distinguishes this recommendation from its two blocking findings.

The reproduction used one numerical thread and a 24-GiB process-tree job with
a 60-second child bound; it finished in 2.8855 seconds, peak 201711616 bytes,
exit 0 and zero active processes. Observations are preserved in the review and
reviewer tool transcript. No raw files were created or are claimed.

## Preserved evidence and verification

- G3a development: 58 passes remain valid for the tested inventory, not formal
  qualification. G1's 49 and G2's 54 regression passes remain separate.
- Five boundary checks passed again in the frozen candidate in 0.270 seconds.
- All six normalized development source bindings and all 39 durable archived
  files were reverified, including the three clean final process records.
- Archive: `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-g3a-development-20260910-e78c1b6`.
  Manifest SHA-256:
  `0177b98a1e1d423d15e3255c68f2173d4c892c4933184086b3a4b01cd6b0a64b`.
- The original candidate/worktree, existing evidence and all G1/G2/native
  element mechanics remain unchanged. This review branch adds two documents
  only. Main, Q4/S3, defaults, versions, other repositories and the unrelated
  ANYmesher compatibility plan are untouched. No push, merge or release.

## Recommended next gate

Create a scoped successor for the missing fixture/rollback/token regressions
and early restart-metadata preflight. Do not change element mechanics,
registered scales, perturbation steps or tolerances. Complete a bounded
rehearsal, freeze the correction, and obtain independent re-review.

Only after acceptance freeze and independently review the G3a formal runner,
exact inventories and evidence schema, then run two fresh-directory cycles
with the frozen 600-second child, 24-GiB/tree, one-thread, 120-second inactivity
and 1,800-second wave safeguards. G3b/G3c, G4 and G5 remain separate gates.
