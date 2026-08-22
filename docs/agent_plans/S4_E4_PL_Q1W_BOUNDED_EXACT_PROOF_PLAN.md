# E4-PL-Q1W: Parallel Bounded Exact-Proof Adjudication

Q1W is a research-only successor to the frozen Q1V closeout at commit
`4fb39e8b86fe0673c2a766f60d6e7826f75ee33a`.  It never reruns either Q1V
registered implementation.  The two preserved, byte-identical Q1V reference
wrappers are historical inputs only.

Three preregistered Q0 rotation shards (`R90`, `R180`, `R270`) reconstruct the
frozen D4 maps and extract the corresponding exact recovery rows.  A separate
SymPy checker rebuilds the Q0 equation-7 frames, patch vectors, constitutive
resultants, and work identities.  The checker compares recovered quantities
against the correctly transported local components.  The earlier comparison
against unchanged base components is retained only as an incident diagnostic
and cannot classify Q1W.

All three producers run concurrently.  Each process is limited to 600 seconds,
24 GiB resident memory, and one numerical-library thread.  Every completed
proof is checked twice in parallel fresh processes.  No retry is automatic.
The canonical aggregate is emitted only after every launched process has a
terminal process status.

An exact nonzero correctly transported residual yields
`NO_GO_E4_PL_Q1W_EXACT_COUNTEREXAMPLE`.  Three exact-zero shards yield
`UNCLASSIFIED_E4_PL_Q1W_BOUNDED_EVIDENCE`; absence of a bounded counterexample
is not qualification.  Timeout, memory excess, malformed evidence, or checker
disagreement yields `BLOCKED_E4_PL_Q1W_PROOF_OR_REVIEW`.  Every result retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`; Q1B and production changes remain
unauthorized.

No path under `src/`, package metadata, workflows, public APIs, dependencies,
dispatch, serialization, recovery, or defaults may change in Q1W.
