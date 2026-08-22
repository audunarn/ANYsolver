# E4-PL-Q1X: Bounded Transport Closure

Q1X is a research-only successor to Q1W. It expands the correctly transported
comparison from the three square rotations to seven registered geometry groups
and all eight D4 operations, without rerunning Q1V or performing full local
stationary analysis.

One producer process per geometry constructs the base `E` field once, transports
the registered nodal patch vectors by the frozen permutation, and emits exact
frame, field-map, patch, four-station recovery, resultant, work, and residual
evidence. Producers run in batches of at most three. Every geometry proof is
then checked twice in fresh independent SymPy processes, with replica pairs
running together and total checker concurrency capped at four.

Each child has a 600-second wall limit, a 24-GiB resident-memory limit, and one
numerical-library thread. Outputs are exclusive; incomplete outputs are removed
without touching historical evidence. The aggregate is emitted only after all
seven producers and fourteen checkers reach a terminal process state.

The independent checker does not import producer mechanics. It uses
`QQ.algebraic_field` domain equality only: no floating point, `evalf`, generic
`simplify`, tolerances, or interval containment. The frozen primitive-field
table makes repeated exact checking bounded and deterministic.

An independently verified exact transported residual yields
`NO_GO_E4_PL_Q1X_EXACT_TRANSPORT_COUNTEREXAMPLE`. Exact closure of all 56 cases
and 224 stations yields `UNCLASSIFIED_E4_PL_Q1X_TRANSPORT_CLOSED_ONLY` because
Q1X does not establish rank, PSD, stationary condensation, full local
qualification, or Q1B authorization. Process failure, resource breach,
malformed evidence, or checker disagreement yields
`BLOCKED_E4_PL_Q1X_PROOF_OR_REVIEW`.

No path under `src/`, package metadata, workflows, public APIs, dependencies,
dispatch, recovery, serialization, or defaults may change. Every result retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
