# E4 PL Q1D Ultrathin Conditioning Closure

Q1D is a bounded research successor to merged Q1C at `22c57838f64205716d5e9272328acc9d0f06289e`. It resolves only the `t/L=1e-6` numerical-conditioning uncertainty and makes no formulation or production change.

Three shards run concurrently: `FULL_BLOCK_LDL`, `DRILL_SCHUR`, and `ULTRATHIN_REFINEMENT`. Each reconstructs the affine strip from high-precision equations, uses 128/192/256-bit arithmetic, and is limited to 120 seconds, 8 GiB, and one numerical thread. The full solve uses 12-DOF cross-section blocks; the Schur shard verifies physical/drill equation parity; the refinement shard compares divisions 16 and 32 at `t/L=1e-5` and `1e-6`.

Two independent checker processes must produce byte-identical checks for every shard. Two complete cycles must produce byte-identical aggregates. Stability requires 192/256-bit response agreement within `1e-18`, scaled residual below `1e-24`, full/Schur response parity within `1e-18`, division-32 error below two percent, and response-ratio drift from `1e-5` to `1e-6` no greater than `5e-3`.

Terminal precedence is `BLOCKED_E4_PL_Q1D_PROOF_OR_REVIEW`, `NO_GO_E4_PL_Q1D_ULTRATHIN_LOCKING`, `NO_GO_E4_PL_Q1D_SOLVER_EQUIVALENCE`, `UNCLASSIFIED_E4_PL_Q1D_PRECISION`, then `UNCLASSIFIED_E4_PL_Q1D_ULTRATHIN_CONDITIONING_CLOSED_ONLY`.

Every result retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`. Q1D authorizes no Q1B integration, production, API/default, dependency, workflow, package, or `src/` change.
