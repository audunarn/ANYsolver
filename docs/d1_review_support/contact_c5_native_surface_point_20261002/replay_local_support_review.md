# Independent local-support review

OpenAI Read-only source scrutiny; no edits/runs or acceptance.

Found one defect: classifier bypassed half-cell rectangle validation on monotone/empty branches. Fixed with upfront cell/domain/finite-extent checks and negative tests.

Confirmed: closed bounds use min(-g)=-max(g) with absolute derivative bounds unchanged. Segment starts reconstruct original prefixes; no constitutive history reset. Unresolved support cannot enter accepted leaves. Coarse one-interval proofs fail conservatively to subdivision.

Scoped query skip is sound: strictly closed contradicts all-positive endpoints; open has no contact; monotone with positive endpoints stays open. Synchronous parent certificate controls both estimates; other points replay complete history.

Union is sound: every unresolved parent is replaced by complete children, and return requires empty pending stack. All-open requires all terminal children open. Proof and shared interval counters accumulate across the full integral without resetting per parent. Quadrature refinement remains independent. These implications do not establish rigorous Gauss error bounds or resolve all friction boundaries.
