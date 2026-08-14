# S4 restricted release status

## Release outcome

The corrected published 2025 MITC4+/D reference mechanics, geometry handoff,
nullspace proof, and qualification scaffold are retained in ANYsolver as
dormant, inspectable evidence. They are not a production formulation selector
or a runtime activation path. The existing `ShellElement` implementation and
its serialized behavior remain unchanged and remain the release default.

The descriptive research identity is
`mitc4_plus_d_published_2025_eq21_eq25_reference_v2`. The descriptive legacy
identity `anysolver.shell_element.legacy_s4` is not a new public or serialized
token.

## Accepted histories

The integration preserves history in this order:

1. main base `4db31b633d0f886fcb4ad82946a982eb6fadde0e`;
2. nullspace proof `cfaf9c7a6e51e1cc0c3113648f84835e917fca2a`;
3. geometry handoff `931ed76943dc84fb9d01b26a5d6dd4c46af3d74a`;
4. qualification scaffold `89ea46d8c1b1365b1d4a390ce6f34e2609c434f9`.

Activity delivery `1fd1c196518ac92b9dee920676f54c2d0cf58d26`
and its ledger follow-up `7daa6e8c61954cfc1bc4469457fef0db154d3375`
were already present on main and were not
reapplied. `ElementActivity` remains the sole activity policy owner, with
element-local pre-scatter scaling.

## Nullspace result and release interpretation

With positive quadrature and density weights, the gauge is
`G = ker(B_w) intersection ker(H_w)`. For the corrected flat square, the
accepted quotient analysis is:

| Quantity | Value |
| --- | ---: |
| `rank(B)` | 16 |
| `N` | 8 |
| `G` | 1 |
| `P` | 7 |
| `R` | 6 |
| `R_N` | 6 |
| `R_G` | 0 |
| `RQ = rank(Pi_P Q_RN)` | 6 |
| `Z = P - RQ` | 1 |

The constant drill direction is the exact zero-mass gauge in this case. The
checkerboard `Z` direction is strain-null but has positive mass. It is not a
gauge and this release neither removes nor constrains it. No gauge constraint,
penalty, hourglass term, tuned stabilization, invented stiffness, or hidden
representative substitution is added.

The categorical curved/warped partition is threshold-sensitive in the accepted
proof. Coupling and provenance are not end-to-end qualified. Nonlinear
mechanics, geometric stiffness, buckling, recovery, and optimized production
batches are also unqualified. Any of those conditions keeps improved-S4
production activation unavailable and fail-closed.

The ordered release-status reasons are:

| Code | Release meaning |
| --- | --- |
| `s4_improved.research_only` | The accepted mechanics remain research evidence. |
| `s4_improved.positive_mass_zero_stiffness_z` | The positive-mass `Z` mechanism is unresolved and is not gauge. |
| `s4_improved.threshold_sensitive_geometry` | The curved/warped categorical partition is not stable across the frozen sensitivity band. |
| `s4_improved.coupling_unqualified` | Production coupling is not qualified. |
| `s4_improved.nonlinear_unqualified` | Exact nonlinear mechanics are not qualified. |
| `s4_improved.geometric_stiffness_unqualified` | Geometric stiffness is not qualified. |
| `s4_improved.buckling_unqualified` | Buckling is not qualified. |
| `s4_improved.recovery_unqualified` | Production recovery is not qualified. |
| `s4_improved.optimized_batches_unqualified` | Optimized production batches are not qualified. |
| `s4_improved.provenance_unavailable_or_unqualified` | End-to-end geometry provenance is absent or unqualified. |

## Historical qualification wording

`S4_IMPROVED_FORMULATION.md`, the frozen 113-claim qualification contract, and
`run_s4_improved_qualification.py` preserve historical candidate obligations,
including rank-18/exact-six wording. Those obligations are not reported as passed.
For release interpretation they are superseded by the accepted
nullspace evidence in `S4_NULLSPACE_SEMANTICS_PROOF.md` and by the machine-
readable restricted contract.

`S4_REDUCED_RESEARCH.md` describes a separately named future energetic
rank-18 research direction. It is not the published 2025 formulation and is
not activated by this integration.

## Dormant boundary

The reference, scalar, director, provenance, quality, proof, comparison, and
qualification files remain directly inspectable. They are deliberately absent
from the root package exports, `ShellElement` construction, serialization,
assembly dispatch, activity maps, nonlinear solvers, recovery, and optimized
batch routing. Future activation requires a separately registered and verified
production task.

The authoritative machine-readable mirror is
`docs/reference_cases/s4_restricted_release_contract.json`.
