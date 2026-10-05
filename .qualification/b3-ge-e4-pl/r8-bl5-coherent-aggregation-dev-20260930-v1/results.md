# Coherent BL5 aggregation and admission repair — development only

Parent source015b16a91994527830c6f9a23ca0217445b02bb8, plus the two bound
product files. Installed wheel
`5079b270ec58736fb22bf1bc618e5168c324e1850eabae4b9426f996e825f240` is
retained here; all387 modules match source/wheel/site. Package version0.4.7,
legacy defaults, span-one/two descriptors, element/material equations and
checkpoint formats remain unchanged. No main or publication action.

## Implementation and repaired finding

The existing P0 half-cell span now admits positive divisors of the complete
beam trace. Row grouping, density interpolation, integration partitions and
finite curvature use the same existing compiler. No implicit partial last
support or new basis is introduced. Span is already part of model/checkpoint
identity; new spans cannot restore a different span's state.

The known single-support rigid-mode guard now covers any whole-trace P0 support.
Independent review also found that finite solve omitted the linear guard:
zero/empty loads could accept stress-free equilibrium before factorization.
Finite entry and restore now reject that known unsupported layout before
constructing trial state or decoding a checkpoint. Fixed/adaptive negatives cover
oldspan2/newspan8, zero/empty loads and unchanged fresh accepted generation.

Source checks: V1 original10 pass; V2 expanded14 pass/4 fixture failures; the
helper incorrectly applied span8 to its provisional four-halfcell definition.
Corrected V3 eight zero-pattern cases pass, ten unrelated cases deselected.
Installed final candidate73/73 pass, no failures/skips,210 onsite imports,
effective BLAS/Numba1thread/JIT off. Coverage includes independent fine-row
aggregation, native K parity, finite same-parent work/curvature, restart identity,
partial/invalid supports, existing span1/2/P1 and nonuniform behavior, objectivity,
shear freedom, physical work, actual-update derivatives, rebase and lifecycle.

The first installed attempt failed collection because three definition-only
fixture modules were absent; raw inventory/log/identities are preserved.
Adding those copies did not change the wheel. Initial in-place build failed on
egg-info timestamp permission; the wheel was built from an isolated exact source
copy. A supervisor-path setup assertion was corrected before numerical execution.
No failed qualification or consumed authority is replaced by these repairs.

## Prospective physical decision and complete rules

Uniform aligned trace rule for every channel and load:

`span=max(1,ceil(c_lambda*n_beam_halfcells/n_shell_trace_segments))`.

Compare complete c_lambda1/2 alternatives. Verify uniform physical spacings,
`span*h_beam >= c_lambda*h_shell`, exact divisibility and complete support
membership/endpoints. This is runner-owned geometric validation; generic public
span admission does not validate a coherent geometric rule.

Small screen: shell8x2, beam4/16 halfcells, same L1m/W.2m/h.035m and square.1m
beam/axisz.0675 as the retained physical-transfer screen. All shell root nodes
are fixed6, beam root0..4 fixed, normal spin free. Loads Fy100N/Mx10Nm/Mz10Nm.
Both shell meshes retain aspect1.25. For beam4, c_lambda1/2 are the same span1
operator and explicitly alias one case. Beam16 uses spans2/4. Three compiled
owners complete nine distinct load routes, each with one eligible factorization.

Coarsening changes beam-finer Mz work17.46% and changes interior transfer
substantially. That result triggered two systematic two-direction refinements
with both unchanged policies, shell16x4/32x8 and beam32/64, not isolated axial
refinement. Four further owners complete twelve distinct routes. P0 row counts
grow40/80/160 for c_lambda1 and20/40/80 for c_lambda2; largest actual supported
mixed matrix order3041. All work maps, physical balances, finite values and
equilibrium/weak-constraint predicates pass. All native variables are retained.

| Relative c_lambda2 versus1 work difference | shell8 | shell16 | shell32 |
|---|---:|---:|---:|
| Fy | 1.61573% | 0.34609% | 0.08355% |
| Mx | 0.21290% | 0.05736% | 0.02233% |
| Mz | 17.45706% | 6.24400% | 1.84531% |

Pointwise gaps decrease. Integrated physical transfer differences generally
contract; individual quantities are not uniformly monotone. For example the
Fy interior Mz difference changes+42.60644,−0.13901,+0.83141Nm. Full station
wrenches, polynomial transfer moments and fixed physical region[.25,.75]
quantities remain visible. These are not point stresses or raw nodal splits.
Small gaps, contracting work differences or successful factorization do not
prove locking freedom, full mixed-system well-posedness or multiplier stability.

## Decision, norm contract and remaining work

Retain both complete policies for the full norm/ratio/physical assessment; neither
is selected. These three levels support resolving the reference norm next,
rather than another mesh. No fourth refinement follows this diagnostic.
The independently derived positive auxiliary Riesz contract uses continuous
axis translations and cellwise-constant retained directors with correct supports,
local moment/cross-coupling and an independently enriched reference dual norm.
It resolves the identified function-space/boundary obstruction, not numerical
acceptance. [Current derivation](../../../docs/agent_plans/B3_GE_E4_PL_M2_TRACE_NORM_CONTRACT_DEV.md)
still requires independent controls, gauge/work checks, convergence, numerical
floors and justified acceptance thresholds. Mechanical K is never replaced by
this positive norm operator or condensed through it.

Next: implement those independent Riesz controls, then assess the complete seven
ratios, growing spaces, actual mixed-system behavior and physical transfer.
Q4/S3, thickness, drilling response, physical external accuracy and all programme
requirements remain open. No beta, uniform stability, converged1% accuracy,
F03 execution, M2/G0B/G2 acceptance or release claim follows.

## Resources and evidence

Installed verification59.03s/sample peak248913920B; small screen5.19s/161595392B;
refinement33.57s/248557568B. Serial supervised600s/8GiB,1thread/JIT off.
Construction counts above are compiled mixed owners, not measured local element
construction counts. Profiling and speedup qualification were not performed.
Raw source failures, failed collection, setup/build logs, wheel, frozen runners,
inputs, imports, outputs and reviews are retained; no unmeasured speedup claim.
[Independent review](independent-review.md) is clear for this bounded development slice.
The independently derived [norm contract](trace-norm-contract.md) remains development-only; numerical controls and acceptance are open.
