# Independent review: F03 local scientific protocol v1 draft

23 September 2026. Reviewer `/root/signed_norm_review` reviewed the protocol
at corrected commit `363d325b`. **GO applies to runner implementation and
bounded lifecycle tests only. No scientific registration or execution is
authorized. G0B remains open and G1 remains barred.**

The initial draft at `6ce4e600` was NO-GO. It reused the system sparse budget
for potentially larger positivity factors, stated the raw rather than
condition-amplified backward-error gate, left component HOLD mapping
ambiguous, and did not completely freeze the replay schema and functional
comparison denominator.

The corrected draft passed review:

- System/certificate and positivity-factor validation have distinct exact
  budgets. The worst declared factor validator workspace recomputes to
  277,536,256 bytes.
- Candidate A requires `condition_2_upper <= 1e10` and
  `amplified_backward_upper <=1e-8`; raw backward error remains diagnostic.
- `HOLD` and `HOLD_UNRESOLVED` map to
  `UNRESOLVED_NUMERICAL_SCREEN`, distinct from explicit failure and physical
  settling outcomes.
- Nested and cross-family functional comparisons use
  `norm(diff)/max(norm(first),norm(second),1000 N)`.
- The solve-free replay inventory explicitly includes both physical/scaled
  operator descriptions, state/actions, positivity factors and maps, every
  indexed inverse block, ports, prolongations and saved recovery records.
- The five topology rows, nested chains, exact triplet/nnz/factor/inverse
  arithmetic, actual/represented balances and no-fallback policy remain
  internally consistent and honestly scoped.

Registration remains barred until the runner, supervisor, schemas and
solve-free adjudicator are implemented, tested and independently reviewed on
a clean committed source. No scientific case was assembled or solved during
this review.
