# E4 PL Q1C Locking Diagnosis and Conditioning Repair

Q1C is a bounded research successor to the immutable Q1B closeout at commit `3df23199893eb136b2682c5190d1405b52dbdd58`. It does not alter Q1B evidence or production code.

The Q1B strip rows show thickness-independent spatial convergence through `t/L=1e-5`, while the `t/L=1e-6` sequence deteriorates as the supported matrix approaches binary64 resolution. Q1C separates spatial error, thickness sensitivity, and numerical conditioning before permitting any formulation change.

Three diagnostic shards run concurrently: `SPATIAL_DISCRETIZATION`, `THICKNESS_LOCKING`, and `CONDITIONING_SEPARATION`. Each is limited to 120 seconds, 8 GiB, and one numerical thread. Each checker runs twice and must produce byte-identical canonical output.

The repair candidate preserves the Q1B element matrices and equations but statically condenses the drill block before solving the five physical coordinates per node, then reconstructs the drill coordinates. Symmetric diagonal equilibration is mandatory for the condensed physical system. This is algebraically equivalent to the full supported equations and changes neither MITC tying, PL/hourglass operators, physical recovery, nor public APIs.

Acceptance retains the two-percent finest-mesh analytical error. Coarse meshes remain mandatory convergence evidence rather than locking contradictions. The thickness-spread gate is evaluated for the binary64-resolved range `1e-2` through `1e-5`; `1e-6` must either pass with a trustworthy conditioning certificate or remain explicitly unclassified.

Terminals, in precedence order:

1. `BLOCKED_E4_PL_Q1C_PROOF_OR_REVIEW`
2. `NO_GO_E4_PL_Q1C_LOCKING`
3. `NO_GO_E4_PL_Q1C_FORMULATION_REGRESSION`
4. `UNCLASSIFIED_E4_PL_Q1C_NUMERICAL_CONDITIONING`
5. `UNCLASSIFIED_E4_PL_Q1C_LOCKING_REPAIRED_ONLY`

Every result retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`. Q1C authorizes no production, API/default, dependency, workflow, or `src/` change.
