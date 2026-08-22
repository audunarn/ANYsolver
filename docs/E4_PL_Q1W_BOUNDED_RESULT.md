# E4-PL-Q1W bounded exact-proof result

Q1W replaced the abandoned exhaustive oracle rerun with three concurrent,
bounded Q0/D4 proof shards.  All three producers completed; every proof was
checked twice in fresh SymPy processes, and each checker pair was byte
identical.

The correctly transported strain, curvature, shear, resultant, frame, patch,
Gauss-correspondence, and work residuals were exact zero for `R90`, `R180`,
and `R270`.  The nonzero residuals behind Q1V's 49 transported-case failures
occur only when numbered local components are incorrectly compared with
unchanged base-frame components.  Q1W therefore establishes no mechanics
counterexample and closes conservatively as
`UNCLASSIFIED_E4_PL_Q1W_BOUNDED_EVIDENCE`.

The final producer wave took at most 168 ms per shard; checker replicas took at
most 1,530 ms and approximately 61 MB resident memory.  Five focused tests
passed in 15.98 seconds.  No Q1V executable was rerun, and no production,
package, workflow, dependency, public API, recovery, dispatch, serialization,
or default path changed.

The external canonical aggregate is 3,790 bytes with SHA-256
`BE6D90C692B8C9D3CB0FB36742B37474E9A69F03BDECD90633C72E16FFBFA2A3`.
Q1B execution remains unauthorized and production retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
