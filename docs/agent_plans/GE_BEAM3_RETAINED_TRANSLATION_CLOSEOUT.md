# Private retained generalized translation-control closeout

Controller implementation: `fd42d3e84d82a3a65418fad5d3b29a7189caf371`.
Final comparison/test freeze: `12202be28f0c21ad11db14089213caed9f55cbb9`.
Final tree: `86d6ab0869888c13a214e25170496cb1e6f31946`.
Branch: `codex/ge-beam3-curved-moment-reference-v1`.

## Implemented scope

An additive private controller prescribes a physical nodal translation while
solving for its spatial dead-force load factor. The existing full retained
generalized element/section residual and spatial Jacobian are unchanged. The
controller solves a full bordered system, including internal cell rotations
and resultants. It requires equilibrium, compatibility, control and remaining
bordered correction to satisfy 1e-11. Load factor and displacement target are
distinct accepted-state fields under a new checkpoint schema.

Strong Context issuance, complete origin/history/reaction/work/recovery replay,
external checkpoint hashes, fixed accepted origins across rejected trials, and
pre/post callback guards remain mandatory. Direct force/control cross-schema
restart fails closed. The controller does not publish FEModel state or expose
a public selector. It does not provide arc length or establish postbuckling.

No existing source file changed: the source delta from Euler closeout b891c08
is only `_ge_beam3_retained_translation_control.py`. B2/B3/Q4/S3, defaults,
recovery laws, package metadata, dependencies and public routing are unchanged.

## Preserved first failure and correction

The original two-macrocell curved port failed the 1e-11 load-factor gate with
error 4.829318056565057e-10. That failed rehearsal remains immutable. Saved-state
diagnosis predicted -4.827535166001761e-10 from the comparison force state's
permitted residual; inverse compliance amplified its small displacement error.

Only test comparison preparation changed: two fixed-load Newton corrections
at the same material origin, followed by a stricter 1e-14 reference check before
measuring targets. The original accepted force capsule is unchanged; these
refined trial coordinates are explicitly unaccepted comparison data. All
original acceptance thresholds and the controller implementation are unchanged.
The final port errors are 1.5620837956475953e-13 in load factor and at most
3.895977319398773e-12 in the normalized mechanical-state comparison.

## Separate final inventories

- Smoke/schema/ownership/mutation/full-border algebra: 34 tests, zero science files.
- Straight analytical load/unload/reversal and restart: 2 tests, four science files.
- Curved coupled one/two-macrocell force ports: 2 tests, eight science files.
- Cancellation and failed-step rollback: 3 tests, three science files.
- Existing nodal-force regression: 22 tests, nineteen science files.
- Existing generalized ownership regression: 10 tests, zero science files.

All passed at the final freeze. All nineteen old nodal science files match the
bound `1bce83f` archive byte-for-byte. The corrected complete rehearsal spanned
56.036455 seconds; its longest child was 30.7439676 seconds (diagnostics only).

Two fresh-directory repeats of the new control gates followed the accepted
rehearsal. Each repeated the separate 34/2/2/3 inventories. Cycle A spanned
41.134953 seconds; B spanned 42.025153 seconds. Every science file matches the
rehearsal and the other cycle exactly. Their canonical aggregates are each
2,241 bytes, SHA-256
`421A76EF813CC61302E7A82A43D36B1A760B6D303ED8CF4FA9058E381066795C`.

Every child used one numerical thread, a 24-GiB process-tree memory bound,
600-second wall bound and 120-second CPU-inactivity protection. Peak overlap
was three; all process trees are empty. No consumed worker was retried. The
comparison correction used a new frozen source identity and fresh outputs.

## Preserved archive

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-translation-12202be-20260908`

- Manifest: 30,186 bytes, SHA-256
  `5A1D9EA53C434411DE6813D533841EEE3350FE867AEDE438D546C48409030A87`.
- Audit: 12,323 bytes, SHA-256
  `EB70425FB4E32D19DD1739DE097868B7A06DF4C52FB7B3266E605DD2598D9A68`.
- All 241 manifest entries verified. Initial failed and passing runs, bounded
  saved-state diagnosis, corrected rehearsal, repeats, logs, receipts and both
  source snapshots are preserved. Original temporary records remain intact.

Direct elevated access to sandbox-owned temporary files was denied before
archive creation. Publication used a copy-verified workspace mirror instead;
no permissions were broadened and no scientific process reran. The mirror and
editable handoff remain outside the frozen worktree under `.perf2-worktrees/`.

## Remaining qualification

This is `PRIVATE_RETAINED_TRANSLATION_GATES_PASSED`, not beam qualification.
Next gates are controlled nonlinear history and objective covariance, followed
by a separately frozen arc-length controller and real curved/post-limit cases
against independent references. The scalar fold test is not an engineering
postbuckling result. Controlled-state modal adapters remain to be implemented;
controlled capsules must never be cast into force-program evidence.

Full spatial postbuckling, practical scale, public FEModel/state integration,
installed opt-in packaging, full environment attestation, independent review
and objective eccentric/curved beam-shell connection qualification remain open.
Independent review is PENDING; full goal remains active and incomplete.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
