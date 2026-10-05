# Native support certificate transition — development only

Base6ef1fa05; exact changed-source hashes and run resource records are in
`replay_zero_set_transition_results.json`. Raw logs, runtime settings, selection
and failure diagnostics are in `replay_zero_set_transition_raw.zip`.
All runs used the portable development runner, JIT off,180s/953MiB.

## Disposition

| Run | Actual result |
|---|---|
| Nearby target-plane origin |1failed/24passed; savedsecond still exhausts128. Discarded.|
| Structured unresolved-region diagnostics |Savedsecond remains non-success;240queries,128support,87proof panels.|
| Three-time derivative enclosure |1failed/23passed; savedsecond128support,33proof panels. Discarded.|
| Corrective temporal short-circuit |1failed,9.30s pytest;5.32s fixture,240queries,128support,49proof panels. Candidate stopped.|
| Diagnostic contract |First test fails due to wrong test attribute name; corrected1pass3.85s.|
| Zero-set certificate core |7pass3.27s; not wired into production geometry.|

Maximum sampled process memory across these runs was200724480bytes. The final
failed temporal run took10.747s process/195579904bytes. These are failed-work
measurements, not successful-solve acceleration evidence. No coupled rerun.

The target-origin and temporal implementations are retained in
`experimental_local_proof_origin.py`, `experimental_local_origin_test.py` and
`experimental_temporal_derivative_enclosure.py`; none is imported by production.
The nearby-origin review additionally identified rounding amplification under
large barycentric extrapolation. Exact-arithmetic equivalence alone did not
establish conservative binary64 bounds. Production support is restored to base.

## Architectural finding and new candidate

A permitted rotating point can have
g(t)=R[cos(2t−0.4)−0.7]: an extremum away from contact followed by one transverse
crossing. It is neither globally monotone nor strictly open/closed. Arbitrarily
small spatial rectangles need not resolve the old classifier's limitation.
This is a mathematical counterexample to completeness, not proof that the saved
second-load failure has that exact cause.

The new private certificate accepts a complete temporal cover in which every
slab either excludes zero by a strict gap enclosure or has a strict derivative
sign. All potentially zero-containing slabs must share that sign. Continuously
differentiable point gaps then have at most one zero. Turning points away from
zero are allowed; hidden pulses and unresolved tangencies fail. Each inspected
slab charges the same shared support budget. Analytic rotating-strip roots and
a tangent quadratic provide independent checks of the implication.

Read-only review by native_integral_review found no consequential core defect.
This is OpenAI source scrutiny, not cross-family or engineering acceptance.
Outstanding adapter obligations: whole-space/time conservative enclosures;
actual captured path and original-time derivatives; target area/orientation and
continuous differentiability; compensated coordinates/full rotating arm/moving
target; arithmetic allowances without the rejected origin-shift assumption.
Sampling alone cannot establish a slab enclosure.

## Next bounded slice

Implement and review the geometry adapter, verify analytic single/two-crossing
geometries and cap/invalid-geometry controls, then evaluate the savedsecond fixture
once under unchanged settings. Full history replay and quadrature error gates
remain independent requirements. No coupled retry before local success.
Second loading, restart equivalence, installed native verification and C5
acceptance remain open. Existing shell artifact/evidence remain unchanged.
