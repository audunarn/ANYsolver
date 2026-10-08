# F03 finite-pad joint refinement v1

22 September 2026. **UNRESOLVED_JOINT_REFINEMENT.** All six supervised
cases completed and passed numerical consistency checks. None of the six
family/topology refinement trends passed the registered physical screen.
The result keeps F03/G0B open; it supplies no production-space selection.

## Source, execution and evidence

Source: `707cb39d65ec17e8f4a3794d0f2e52eaa7712666` on the isolated
`codex/b3-ge-e4-pl-integration` branch. Main remains untouched. Evidence is
under `.qualification/b3-ge-e4-pl/f03-joint-refinement-v1/` in that worktree.
The frozen contract is `B3_GE_E4_PL_G0_F03_JOINT_REFINEMENT_PROTOCOL.md`.

| Artifact | SHA-256 |
|---|---|
| Registration | `42a9fcddee56232921edcaf7f7108e6093196003cd3c18f6de78a944c8263558` |
| Adjudication | `aa7848374fbe2664037794c129e918251bc9e67f6519537fea123790bdbef471` |
| Orchestration | `c2f9d61fbfc7b629690c5840b9f12cc1b396905bca0a1ffafc39de2a5685a421` |
| Completed artifact inventory | `8508091cf59573664e86e356dbd98277c2aa410b55be5ad1e6a357fa11f99322` |

Three mesh levels `(Ns,Ny,Nb,Nm)=(4,8,8,4),(8,16,16,8),(16,32,32,16)`
were assessed for Q4/CST-CB and P1/hybrid/enriched exact multiplier spaces.
The coarse/fine sets required12 fresh equilibria. The six middle states
were reconstructed from immutable endpoint-comparison snapshots without
equilibrium solves. Their complete state arrays and historical physical
observations reproduced exactly. Sparse Schur inverse actions remained
necessary for the newly selected analytic norm.

The same independently validated analytic H1-dual norm was used throughout,
with owned small Schur and Gram matrices saved for every family. This
does not revise endpoint-comparison v1's FE32/64 HOLD or rerun that study.

The serial run completed in296.838s; maximum child134.063s and maximum
sampled child RSS111.571MiB, within the900s/8GiB limits and2400s launch
cutoff. All five supervisor and child thread caps were1; child numerical
pool counts are recorded. These diagnostic times are not a performance
qualification or speedup claim. All six children exited0. Final
adjudication exited1 because the physical refinement screen is unresolved.
No case was retried, and no evidence was overwritten.

The implementation passed44 integrated focused checks before review
corrections, followed by25 affected checks after those corrections.
Independent pre-execution review found and closed two evidence/lifecycle
issues: stopping subsequent launches after cancellation, and binding
reported force coefficients to saved multipliers. Tests cover both.

Maximum numerical measures over the six cases were free residual4.88e-15,
scaled weak gap8.99e-16, balance1.70e-13, energy identity8.98e-14 and
structural inverse-action residual7.60e-12. Enriched energy ordering held
within every common mesh; all finite Schur spectra were positive. These
checks establish numerical consistency, not physical convergence.

## Physical outcome

Values below are on the finest level. Changes are middle-to-fine,
componentwise and normalized using the preregistered floors. The force
functional compares the entire density-plus-atom action in the same H1
dual norm, not raw coefficient vectors or a scalar force resultant.

| Topology / space | Tip uy (um) | Tip change | Energy (J) | Energy change | Gap RMS / motion | Force-functional change |
|---|---:|---:|---:|---:|---:|---:|
| Q4 / P1 | 36.56522 | 7.4695% | 17.14034 | 13.8368% | 4.4298% | 27.4950% |
| Q4 / hybrid | 27.07669 | 4.6940% | 10.36262 | 6.6534% | 1.0808% | 4.8010% |
| Q4 / enriched | 27.07788 | 4.7003% | 10.34718 | 7.5974% | 0.1599% | 4.6195% |
| CST-CB / P1 | 36.40517 | 6.8661% | 17.05272 | 13.3797% | 4.4415% | 27.7370% |
| CST-CB / hybrid | 26.91500 | 5.4209% | 10.26318 | 7.6291% | 1.0466% | 5.0880% |
| CST-CB / enriched | 26.91615 | 5.4208% | 10.24861 | 8.5142% | 0.1388% | 4.8949% |

Thus the small tip movement seen in attachment-only refinement was not
overall convergence. Joint structural refinement still changes response
materially. Enriched passes the final gap screen; hybrid narrowly fails
its RMS requirement, and P1 fails by a larger margin. All spaces retain
unsettled signed reaction, energy or force-distribution channels.

Finest root `(Fy,Mz)` values, in `(kN,kNm)`, are Q4 P1
`(-707.230,-9.937)`, hybrid `(-774.691,-171.638)`, enriched
`(-774.843,-171.632)`; CST-CB P1 `(-708.479,-9.913)`, hybrid
`(-776.256,-172.345)`, enriched `(-776.385,-172.342)`. The large P1
moment difference cannot be hidden by similar global balance or a
decreasing gap. P1/hybrid and P1/enriched complete-functional differences
remain about68.5–68.7% on the finest grid.

Hybrid/enriched complete-functional differences are much smaller,
0.6915% for Q4 and0.6709% for CST-CB, but their total force and moment
over the fixed terminal band `[31/32,1]` differ by roughly10.1–10.6%.
Their band comparisons therefore fail even though their tip responses
nearly coincide. No family is removed from the registered decision.

Finest Q4/CST-CB total energy differs by less than1% and tip uy by less
than0.6%; nevertheless every topology comparison fails. P1's near-root
band moment differs4.73%; hybrid/enriched beam energy differs3.90/4.11%
and the near-root band moment differs1.27/1.30%. Total quantities cannot
replace the split energy and fixed-distance transfer checks.

The finite beta sequences for hybrid/enriched rise from approximately
0.456–0.463 to0.490–0.491; P1 decreases from0.657–0.663 to0.545–0.546.
No nonpositive finite mode appeared. This is not a continuum stability
proof and does not explain away the unresolved physical channels.

## Review and next action

Independent post-execution review **accepted evidence integrity and retained
HOLD on mechanics**. It verified18 source hashes, six supervisor receipts,
18 physical state pairs and partials,18 Schur/Gram pairs, every saved
eigenvalue, exact middle-level parity, closed-form band/quarter recovery,
all functional differences and all trend/cross-comparison predicates.
Saved Grams matched the previously validated norm archives. No structural
or norm constructor was rerun. The completed inventory binds89 evidence
files, including the execution and independent-review provenance record.

Preserve the failed trend screen and all earlier HOLD records. Do not
automatically add another uniform refinement or promote an endpoint space.

The independently recommended next step is a separately registered
**saved-state variational attribution**. For the nested Q4 middle/fine
physical spaces, verify exact prolongation v=P qmiddle and let e=v-qfine.
Check the potential-energy identity

    Pi_f(v)-Pi_f(qfine) = .5 e.T K_f e - lambda_f.T C_f e + e.T r_f.

Separate shell/beam energy-distance terms, constraint-mismatch work and
residual work. Check coarse energy/load preservation under prolongation;
retain any quadrature discrepancy explicitly. This requires assembly and
saved-state matrix actions, not equilibrium solves. Do not claim nesting
for CST-CB or transfer Q4 conclusions to it without a separate proof.

In parallel with that derivation, establish an independent **continuous
primal reference** for the exact finite-pad law. Formally eliminate the
beam trace b=A us in the energy:

    Pi(us) = .5 a_s(us,us) + .5 a_b(A us,A us) - l_b(A us).

Retain the existing shell supports and only the beam-root trace constraint
A us(0)=0; add neither a slope clamp nor an absolute tip support. Prove the
admissible trace/energy domain, variational equivalence and physical work/
reaction recovery before implementing an independent higher-order/Ritz
evaluator with independently integrated pads. This would remove the
discrete multiplier-space choice from the reference, but is not yet an
implemented or executed physical oracle. It does not replace the mandatory
external comparisons. New scientific executions need their own frozen
registration and review. Native full-vector, shear/drilling and the other
G0 foundations remain mandatory before G1.
