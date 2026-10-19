# Mistral PR35 planning checkpoint — inspection only

Configured Mistral Read worker completed 10 inspection turns with successful
source tool outcomes but no final handoff. No edits or numerical execution.
Original full stdout/stderr are MISTRAL_PR35_PLAN_REVIEW.*.txt in this folder.
User wants a bounded plan only; PR35 remains open, four other PRs are closed.

Confirmed input identities: main 8475718b9262e120607c9d3861923f9c79f13e55;
PR35 head 090e2c9756fd2d5e7f8378a6379b87b477b39fbe; initial fix a8428e0d.
Your early checkpoint proposed only canonical immutable-vector recognition,
the idempotent freeze change and new active shared-contract regression coverage.
All Q4 mass/recovery batching, cache-authority rewrites, warmup, verification
result caches and CI changes stay deferred.

Your source inspection found main lacks the old helper and still rebuilds
these arrays. You examined current freeze call sites, S3 component/recovery
plan and the current plan-validation signature. The last signature binds
mesh id, revisions, direct-state revision and material state, rather than
explicit vector identities. You had not demonstrated current cache invalidation
or current supported-route relevance. The absence of the old helper alone is
not a reproduced defect or a performance result. Don't infer an accepted
speedup or claim a cache miss without evidence.

Hand off now from these inspected facts. Recommend a bounded relevance gate
before coding, including a no-change/close option if current code already
avoids the old defect. Keep all execution prospective, with no solver import,
test or benchmark now. No more broad source investigation is needed for this
planning deliverable. State any exact call-site evidence and any remaining
uncertainty, a finite future check set, stop conditions and the deferred groups.
Preserve current immutable/mutable backing rules, dtype/shape/subclass behavior,
mutation/refusal/invalidation and scientific tolerances. No retired tests.
