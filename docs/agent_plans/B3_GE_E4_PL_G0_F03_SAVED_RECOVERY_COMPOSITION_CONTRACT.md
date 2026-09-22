# Saved recovery composition contract

22 September 2026. This bounded contract composes the already reviewed sparse
numerical, saved-interface, saved-work and saved-norm components. It introduces
no new mechanics, equilibrium solve, scientific case or qualification claim.
G0B remains open and G1 remains barred.

The composition accepts one canonical float64 `q,eta` pair. It owns those bytes
once and derives the exact recovery Fractions from them; callers cannot supply a
second exact state. Before component evaluation it owns and validates every
sparse matrix, numerical vector and saved record, checks common dimensions,
grid degree/partitions, nested inventories and a conservative aggregate budget.

The four components remain independent authorities for their declared checks:

1. Re-run sparse numerical equilibrium and its state binder from raw owned
   matrices and vectors; never accept a cached result.
2. Re-run saved-interface recovery from the exact values derived from the owned
   float64 state.
3. Re-run saved support/work checks from that same exact state.
4. Run saved norm verification only on the exact owned saved functional returned
   by the interface result. No caller-provided Functional is accepted.

The three existing deterministic recovery calls are retained and reported:
one in the interface component and two in the work/support component. Removing
them would weaken the existing independent factory rebind and is outside this
batch. The composition performs zero equilibrium solves or factorizations and
exactly two norm observations.

Every returned identity is independently recomputed. Cross-binding covers all
sparse numerical operands, numerical `q,eta`, the interface grid/state and
saved record, the work grid/state/saved record, exact recovery q/eta/cuts, and
the interface-functional-to-norm identity. Domain-specific hashes are not
compared with one another and a passing component status cannot waive a failed
identity.

Status precedence is:

1. `COMPOSITION_FAILED` for any saved-component failure or cross-binding
   failure.
2. `HOLD_NUMERICAL` for the sparse numerical component's `HOLD`.
3. `HOLD_UNRESOLVED` for a retained certified-enclosure or norm-resolution
   hold.
4. `COMPONENT_CHECKS_PASSED` only when all four component checks and every
   cross-binding pass.

Unexpected, programming and preflight errors propagate. The result never uses
`PASSED`, `ADMITTED`, or a scientific/G0 status. It returns an immutable scope,
status/reasons, canonical snapshot and saved identities, component statuses,
cross-bindings, bounded diagnostics and the nested component evidence.

Required focused checks cover the all-pass manufactured route, aggregate and
malformed preflight before any component starts, ownership against hostile
caller mutation, coherent q/eta identity changes, every saved identity, exact
functional flow into the norm verifier, status precedence, unresolved holds,
programming-error propagation, and the fixed counts of three recovery calls,
two norm observations and zero solves/factorizations.
