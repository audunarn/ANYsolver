# D1 fixed-structure x-pressure field discriminator — development evidence

The 32×8 independent scalar Q1 structure, load, clamp, near-rim y knots and
physical support were held fixed. The matching 32×8 and coarser 16×8
x-pressure bases both passed KKT, equilibrium, independent represented-gap
and active-work-rank checks (96/96 and 48/48 active columns). The matching
case reproduces the independent same-mesh Q1 field. This extends the earlier
[bin-only comparison](d1_fixed_structure_pressure_45b96736_20260928.md)
with exact common-refinement physical pressure integration.

| Coarser versus matching x-pressure basis | Difference |
|---|---:|
| Common 8×9 bin-force L2 | 0.5040% |
| Total reaction | 0.03567% |
| Pressure L2 over physical support `0≤y≤.9` | 7.7010% |
| Regular-area pressure L2 `0≤y≤.8` | 10.6289% |
| Rim pressure L2 `.8≤y≤.9` | 6.9061% |

The regular-area pressure change from x-pressure representation alone is
substantial on this fixed structure. For context, 16→32 structural/pressure
co-refinement changed that field 11.6182% in the same scalar model. These
nonlinear active-set comparisons are not additive and do not allocate a
precise causal fraction; their L2 denominators are the 32×8 matching field
and 16×8 co-refinement field, respectively. They show that rim alignment
alone cannot explain the regular-area x sensitivity. “Regular area” is a
y band and does not show whether variation is spread across x or concentrated
at the contact front. Both pressure spaces yield full active work
rank but that does not establish mesh-uniform stability or pointwise pressure
convergence at the contact front.

The [raw comparison](d1_x_pressure_field_06126ff8_20260928.json) binds
solver source `06126ff8`, probe/oracle/input hashes, KKT and rank diagnostics.
The [bounded run](d1_x_pressure_field_resource_06126ff8_20260928.json)
took 1.03 s and 80.44 MB peak process-tree memory under 180 s / 1 GB.
Three focused exact-integration comparison tests passed. No production
contact law or pressure basis changed.
Independent read-only scrutiny found no comparison or normalization issue
that changes this fixed-structure decision.

**Decision.** Retain fine nodal Q1 and pressure-space stability as a D1
gate. Use common physical bins for integrated-force accuracy while keeping
separate pressure-rank and partial-contact checks. Do not treat close bin
forces as a pressure-space qualification, nor launch an over-enriched
pressure solve without resolving its previously uncertified KKT result.
