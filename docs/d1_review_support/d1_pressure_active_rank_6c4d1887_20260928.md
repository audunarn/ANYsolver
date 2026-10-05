# D1 fixed-structure enriched pressure: active work-rank discriminator

This is a bounded development analysis of the **independent scalar oracle**,
not a production mortar qualification. The 32×8 structural mesh has 288 free
scalar displacement coordinates. The x and y pressure enrichments have 585
and 528 positively supported modes, respectively, so their complete
pressure-to-structure maps cannot have full row rank. This fact alone does not
establish a problem on a smaller active set.

The [explicit scaled-QP attempt](d1_pressure_enrichment_qp_b_6c4d1887_20260928.json)
returned exploratory bin fields, but its complementarity products were
3.01×10⁻¹⁰ and 2.28×10⁻¹¹ Pa·m, versus 6.37×10⁻¹⁸ Pa·m for the matched
32×8 oracle. Its bin shifts are **not** qualified pressure-resolution results.
Warm active-set polishing subsequently failed with a singular x active block
and a cycling y active set. The [failed polish record](d1_pressure_enrichment_qp_c_6c4d1887_20260928.json)
retains those outcomes.

The single [algebraic replay](d1_pressure_active_rank_6c4d1887_20260928.json)
reconstructs exactly the saved QP bin fields and active counts, then forms the
support-scaled, unit-column active cross-mass work map on the same 288 free
structural coordinates. Under both 10⁻¹⁰ and 10⁻¹² relative singular-value
thresholds:

| Replayed approximate active set | Active modes | Work-map rank | Smallest relative singular value | One half-feasible null-vector effect on 8×9 bins |
|---|---:|---:|---:|---:|
| x-enriched 64×8 | 177 | 97 | 2.33×10⁻¹⁸ | 0.0010% |
| rim-knot y-enriched 32×16 | 156 | 96 | 6.06×10⁻¹⁸ | 0.505% |

The selected null directions change structural work only at numerical
roundoff, while keeping the replayed approximate pressures nonnegative at
half the limiting feasible step. This demonstrates that those approximate
active maps cannot identify a unique physical bin field from structural work;
the y case has a materially visible null direction. The x value is one sampled
null direction, not an upper bound on its possible bin effect. Independent
read-only review found no defect in the cross-mass rank or null-bin arithmetic.
The active sets came from
an **uncertified** QP iterate, so this is not a proof of nonunique certified
KKT solutions or of instability in the production matched fine-Q1 space.

**Decision:** Do not use these fixed-structure over-enrichments to claim a
pressure-resolution pass or fail for D1. Retain the original matched fine-Q1
candidate and its independent geometry, KKT, gap and refinement gates. The
next pressure-space qualification route needs an admissible structural and
pressure pairing or another reference that controls active work rank, rather
than further tuning of this over-enriched scalar oracle.
