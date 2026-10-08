# F03 saved-state variational attribution v1

22 September 2026. **3/3 diagnostic cases passed and independent review
accepted the evidence and bounded interpretation. G0B remains open.**
The earlier joint-refinement and auxiliary-norm HOLDs are unchanged.
This is a classical in-plane diagnostic, not native B3-GE/E4-PL
qualification, a continuum error estimate or a production-space selection.

## Registered scope and execution

Source: `f8f8e851e3ce24885005381d9b64873026baa314` on
`codex/b3-ge-e4-pl-integration`. Contract:
`B3_GE_E4_PL_G0_F03_VARIATIONAL_ATTRIBUTION_PROTOCOL.md`.
Raw root: `.qualification/b3-ge-e4-pl/f03-variational-attribution-v1`.
The command was:

```text
python scripts/b3_e4_f03_variational_attribution.py --run-all --root .qualification/b3-ge-e4-pl/f03-variational-attribution-v1
```

All five registered thread caps were one. Python 3.14.2, NumPy 2.4.6,
SciPy 1.17.1, Windows 11, and imported/source identities are preserved
in the registration. All three children and the runner exited zero.
Orchestration took 29.5034555 s; maximum sampled child RSS was
88,465,408 bytes (84.37 MiB). These are diagnostic resource observations,
not timing qualification or process-peak guarantees.

The run reused exact Q4 middle/fine physical states and fine multipliers
from the consumed joint-refinement registration. Mesh tuples
`(Ns,Ny,Nb,Nm)` were `(8,16,16,8)` and `(16,32,32,16)` for each of
P1, hybrid and enriched. Sparse operators were reassembled, but no
equilibrium, Schur or constitutive solve was performed. No CST nesting
was assumed. Exact parent hashes and copied states are bound in the
new registration and raw archives.

## Signed discrete identity

Let `v=P q_middle`, `e=v-q_fine` and
`r=K_fine q_fine+C_fine.T lambda_fine-f_fine`. The checked identity is

```text
Pi_fine(v)-Pi_fine(q_fine) = A_shell + A_beam + B + R
A_shell + A_beam = .5 e.T K_fine e
B = -lambda_fine.T C_fine e
R = e.T r
```

All entries below are joules. Signs are retained; the terms are not
percentages of a continuum error.

| Family | Shell distance | Beam distance | Constraint work B | Residual work R | Direct potential change |
|---|---:|---:|---:|---:|---:|
| P1 | 0.9606591780 | 2.7988239753 | -6.5120270742 | -5.347e-13 | -2.7525439208 |
| Hybrid | 0.7806078592 | 0.1063457881 | -0.1974904339 | 4.513e-14 | 0.6894632134 |
| Enriched | 0.7713632392 | 0.0147177141 | 0.0000329631 | 1.129e-13 | 0.7861139163 |

Enriched's change is predominantly shell energy distance between these
two discrete states, with small **net** constraint work. This does not
isolate the causal structural-discretization error or bound endpoint
reaction error or full incompatibility: cancellation is possible.
Hybrid retains appreciable negative constraint-work cancellation. P1's
constraint work dominates and reverses the sign of potential change.
These observations explain the signed identity only; none selects a
multiplier space or establishes continuum convergence.

## Checks and independent review

All frozen checks passed. Maximum normalized defects across the cases:

| Check | Observed maximum |
|---|---:|
| Matrix-action parity | 1.495e-16 |
| Exact support preservation | 0 |
| Scaled stiffness pullback | 5.603e-16 |
| Scaled load pullback | 1.388e-17 |
| Shell energy preservation | 2.492e-14 |
| Beam energy preservation | 5.223e-17 |
| Load-work preservation | 1.045e-16 |
| Signed identity defect | 3.232e-15 |
| Fine free equilibrium | 3.844e-15 |
| Fine compatibility | 7.584e-16 |
| Independent off-grid field parity | 1.993e-16 |
| Independent off-grid strain parity | 9.563e-15 |

Maximum absolute identity defect was `2.19825e-13 J`; maximum absolute
residual work was `5.34686e-13 J`. Integrated focused tests passed
20/20 before review; all 9 affected runner tests passed after adding
the exclusive private-child start marker. The evidence records their
separate logs rather than treating these as 29 distinct tests.

Independent reviewer `/root/finite_pad_axis_review` accepted the raw
identity and receipt chains, all 12 source hashes, four parent hashes,
exact parent-state parity, archive inventory/types/shapes/digests,
sparse P/K/C operators, actions and scalar recomputation. The reviewer
also checked fields and strains with independent closed-form off-grid
evaluation, byte-identical P/K/load across families and the expected
enriched/P1/hybrid row relations. Review used saved artifacts only;
no source assembly or solve was repeated. No correctness finding remains
in this diagnostic. Mechanical HOLDs remain in force.

## Evidence identities and next implementation

| Record | SHA-256 |
|---|---|
| Registration | `6aed8b9b92f44218d7d779754882e2831c6ee9c10289461e6625c705384d6500` |
| Adjudication | `58a4e2d35720d00d659fb7d006698b6a0905e69cc74eb8c6a3baa5dc082537aa` |
| Orchestration | `5076027799a69827ccb67a8c19e0c6e646cd6783946780bcc59a768ffb9fd5fc` |
| Execution provenance | `f58a23c98fc1ff4134b4d504a02a806c638a0367e9c881fad530b3679bd695c8` |
| Completed inventory | `582eeb5900678869a6c60d420b3daf021064e246afd9cf8100cccd010c72cf68` |

The inventory binds 23 completed files, including provenance. This
execution is consumed; preserve it without overwrite, rerun or relabel.

The continuous eliminated-primal derivation in
`B3_GE_E4_PL_G0_F03_CONTINUOUS_PRIMAL_REFERENCE.md` has separately passed
independent mechanics review. It proves the fixed rectangular pad map
and retains the exact three beam-root constraints, physical work and
reaction/endpoint-atom interpretation. At this result's execution no
primal reference had been implemented or run.

The next implementation is a bounded independent polynomial Ritz
reference, with independent pad moments, root constraints and reaction
recovery. Freeze and review its basis, quadrature, conditioning,
convergence and resource contract before scientific reference solves.
This must precede reference comparisons; it does not authorize automatic
mesh extension, weaker tolerances, native integration or family selection.
Mandatory external execution and native full-vector/shear/drilling
qualification remain separate outstanding requirements.
