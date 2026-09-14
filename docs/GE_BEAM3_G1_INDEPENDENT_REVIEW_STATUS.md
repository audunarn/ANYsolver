# G1 independent review: blocked before formal confirmation

Independent review of candidate `635888afa6d5f0ed9523f10ed4339670276d61c3`
(tree `bf948f65e9133f2a7b7b481ef6c089ee2eccdc7a`) is complete.
Decision: **BLOCKED_G1_IMPLEMENTATION_REVIEW**. Two P1 state-safety findings
prevent acceptance. **No formal G1 cycle or confirmation certificate was run
or created.** This is an implementation-review block, not a mechanics NO-GO or
loss of previously accepted beam/shell qualification.

The independent reviewer `/root/g1_independent_review` did not author or edit
the implementation. The canonical five-key review preserves the findings,
source locations, reproduction instructions and process observations.

## Confirmed findings

1. **G1-IR-01, mutable free-DOF authority** (analysis line 68). Removing the
   last free DOF makes a tip moment disappear from the convergence test.
   The solve returns success at zero displacement and commits generation 1,
   reporting a reaction at an undeclared support. Its own checkpoint cannot
   replay. The operating free set is neither immutable nor checked against the
   frozen fixed-support set.
2. **G1-IR-02, post-callback publication gap** (analysis line 172). A cancellation
   callback can append an unsupported constraint after convergence evaluation.
   The solve still commits generation/history 1. A subsequent checkpoint
   rejects the modified graph, but accepted state has already advanced.

Both were reproduced in one bounded review-only worker: 2.73 seconds, one
numerical thread, a 24-GiB job limit, a 60-second deadline, 185,241,600-byte peak
tree usage and zero live processes at exit. This was not a formal mechanics
campaign. Output was captured in the reviewer's tool transcript; no external
raw diagnostic files were created or invented for this review.

The prior 27-test development runs remain preserved and accurately describe
what those tests exercised. They did not include these two failure cases.
Prior status/evidence files are not rewritten; this successor records why
development success does not confer formal acceptance.

## Required next step

Create a correction candidate from this preserved lineage, limited to:

- Binding the operative free-DOF selection to frozen support authority and
  rejecting mutation/replacement before state changes.
- Revalidating model, constraints, loads and DOF authority after user callbacks
  and protecting the final preparation/publication boundary.
- Regression tests for both reproductions, asserting unchanged committed state
  bytes, rotation/store generations and accepted history on rejection.

Then independently re-review that frozen candidate. Only an accepted review
with no state-safety findings permits the separately bound formal G1 runs.
Do not advance to G2 or relax scientific tolerances.

This review task changes documentation only. The frozen candidate, earlier
development packets, runtime source, defaults, main, qualified Q4/S3, legacy
beams and historical qualification remain unchanged. No merge or publication.
