# G2 independent implementation review: formal confirmation blocked

Review subject: `3e89a5e30ba86103bad6c236356d700229d2820f`, tree
`b945ddcb02ed5d17ada718ec69424027195b7055`.
Preserved development handoff: `a474a91e126e6904f613f305deb2e1a1427d02de`.

Decision: **BLOCKED_G2_IMPLEMENTATION_REVIEW**.
**No formal G2 cycle was launched and no confirmation certificate was created.**
This is an implementation/state-safety and acceptance-coverage block, not a
reclassification of accepted G1 or existing beam/shell qualification.

## Confirmed state-safety defect

The inherited `ElasticAnalysis.solve` can be invoked on a `ConstrainedAnalysis`
owner and bypass the G2 multiplier equations. The G2 guard accepts the owner,
allowing the G1 solver to publish a G1-shaped journal into the G2 state store.
With a nonzero prescribed translation, the bounded independent reproduction
committed zero displacement despite a constraint residual of `0.001`. Both
virgin and already accepted owners advanced their generations; the resulting
G2 checkpoint failed its own restart history-schema validation.

This directly violates the frozen contract's prohibition on using the inherited
G1 zero-support solve on a G2 owner. The reviewer did not modify source files.
The reproduction finished in approximately 2.95 seconds, exit code zero, with
zero surviving processes. Its observations are retained in the canonical review
and reviewer tool transcript; no nonexistent raw files are claimed.

## Acceptance coverage

The independent review also identifies gaps in the prescribed-frame work,
nonzero-multiplier constraint-curvature and covariance checks. Several S11/S14
assertions omit `rtol`, so NumPy's default `1e-7` does not enforce the frozen
normalized `1e-11` acceptance criterion. These are acceptance-test gaps, not
proof that the corresponding mechanics results are incorrect.

The existing two 35-test G2 development runs and separate 49-test G1 regression
remain preserved. Their six bound input hashes and 26 archived output files
were verified during this review task. Passing those inventories did not cover
the inherited-solve bypass and cannot substitute for formal G2 confirmation.
The detailed independent five-key review is in
`reference_cases/ge_beam3_g2_implementation_review_v1.json`.

## Recommended next gate

Create a scoped successor that rejects inherited/base-class solve dispatch
before any trial or accepted-state change. Add virgin and accepted-prefix
regressions checking constraint satisfaction, committed bytes, both generation
counters, journal identity and valid checkpoint replay after rejection.
Complete the independently identified work/tangent/transport tests and enforce
the frozen normalized tolerance explicitly, without relaxing it.

Independently re-review the frozen correction and its confirmation protocol.
Only after acceptance run two bounded, fresh-directory formal G2 cycles. Do not
relabel development packets or proceed to G3 on this blocked implementation.

This task adds review documentation only. Frozen G2 source, tests, contract,
development evidence and worktree remain unchanged. Main, qualified Q4/S3,
legacy beams, defaults and versions are unchanged. No push, merge or release.
