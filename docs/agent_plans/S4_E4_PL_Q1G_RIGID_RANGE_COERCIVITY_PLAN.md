# E4-PL-Q1G: Rigid-Range Repair and Bounded Domain Coercivity

## Authority

Q1G is a research-only successor of merged Q1F closeout `c9d75eaed17e658e84879085a01ecca823dd32cd`.  It preserves Q1F's rejected plan, blocked closeout, and eight premature drafts without promoting or executing those drafts.

Study: `study_e4_pl_q1g.q1f_rigid_range_repair_and_domain_coercivity_v1`

Candidate: `candidate_e4_pl_q1g.wg2020_g1_domain_coercivity_v1`

Production remains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`; Q1B execution and integration remain unauthorized.

## Corrected rigid theorem

For `X_raw = a0 + ell R2 X_gauge`, let `A = T_Q S_scale`, `G = A R_gauge`, and order rigid parameters as `(t_x,t_y,t_z,omega_x,omega_y,omega_z)`.  The exact parameter map `C(a0,R2,ell)` is defined by

```
t_raw_xy     = ell R2 t_gauge_xy - omega_z J a0
t_raw_z      = ell t_gauge_z - (R2 omega_gauge_xy)^T (-J) a0
omega_raw_xy = R2 omega_gauge_xy
omega_raw_z  = omega_gauge_z
```

The producer and checker must independently prove `G = R_raw C`, `det(C)=ell^3>0`, and therefore `R_raw = G C^-1` and `range(R_raw)=range(G)`.  No quotient or kernel claim may depend on equality of the original six columns.

## Bounded evidence

Three deterministic parameter shards run concurrently.  Each producer process is limited to 480 seconds, 24 GiB, and one numerical-library thread.  Every proof is checked by two fresh checker processes.  The complete cycle is limited to 600 seconds and is never retried automatically.

Q1G certifies the corrected rigid-range theorem now.  Domain coercivity is classified only when the executable K/H reduction covers every admissible leaf.  Missing K/H coverage is `UNCLASSIFIED_E4_PL_Q1G_DOMAIN_COVERAGE`, never a provisional GO.

Terminal precedence is:

1. `BLOCKED_E4_PL_Q1G_AUTHORITY_OR_REVIEW`
2. `BLOCKED_E4_PL_Q1G_REDUCTION_IDENTITY`
3. `BLOCKED_E4_PL_Q1G_PROOF_OR_NONDETERMINISM`
4. `NO_GO_E4_PL_Q1G_DOMAIN_COERCIVITY`
5. `UNCLASSIFIED_E4_PL_Q1G_DOMAIN_COVERAGE`
6. `PROVISIONAL_GO_E4_PL_Q1G_DOMAIN_COERCIVITY_CLOSED`

A provisional result authorizes only preparation of a separate Q1H re-adjudication plan.

## Boundaries

No file under `src/`, package metadata, workflows, dependencies, public APIs, serialization, recovery, or defaults may change.  Canonical evidence contains only identifiers, counts, booleans, hashes, and enums; matrices and rational witnesses remain diagnostic proof records.
