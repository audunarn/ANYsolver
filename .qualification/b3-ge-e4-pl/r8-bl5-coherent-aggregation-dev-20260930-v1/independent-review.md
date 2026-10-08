# Independent BL5 aggregation development review

Date: 2026-09-30. Review performed by the independent bl5_consumer worker.
Disposition: clear for the bounded experimental implementation and retained development interpretation described below. No consequential source or artifact-binding defect was found. This is not F03, M2, accuracy, uniform stability, policy selection, or release acceptance.

## Source and installed evidence

The source extension admits every positive integer P0 multiplier_span dividing the native halfcell count, rejecting partial groups and preserving the previous span 1/2 meaning, descriptors and default. P1 restrictions are unchanged. The assembly and finite row integration retain density-integral aggregation; there is no macro-support-length division and no mechanical stiffness replacement. Existing descriptor-based identities distinguish different spans. The whole-trace free-rigid-mode guard now covers P0 span equal to the trace count, including the public finite solve and restore entry points before state creation/decode. The new zero-pattern regressions cover old span 2/new span 8, fixed/adaptive control and fresh-owner state/generation preservation. These changes do not assert that every admitted span is a physically acceptable policy.

I independently read the installed inventory, identity, runner and imports, hashed the retained wheel, and compared all 387 manifest modules between wheel ZIP, installed site, current worktree and source manifest: zero differences. The wheel SHA256 is:
5079b270ec58736fb22bf1bc618e5168c324e1850eabae4b9426f996e825f240.

The inventory contains 73 passes, zero failures/errors/skips: aggregation 18, BL5 finite 9, BL5 local 8 and L1 assembly 38. All 210 recorded ANYsolver imports resolve inside the declared installed site. Identity records both BLAS pools at one thread, Numba one thread and JIT disabled. The supervisor records exit 0, 59.0254182 s and 248913920 B peak process-tree RSS; pytest itself reports 55.644 s. Four fixture hashes agree with the frozen manifests.

The earlier failures remain failures: source V2 inventory has 18 cases, four fixture-construction failures and fourteen passes; the corrected zero-pattern source V3 selection has eight passes, ten deselections. Installed collection-failure-v1 retains exit 2 and the missing scripts._b3_e4_f03_native_fixture import error before numerical cases. This review does not convert those histories into passing executions or consume another execution.

## Frozen screen and refinement

Reviewed the frozen result.json, manifests, run_case.py and installed runners under r8-bl5-coherent-screen-v1 and r8-bl5-coherent-refinement-v1. Their executed script hashes respectively match:
c0b270d020fe2d9591dc2522ea16e8481512ba0cc56f001f37cdf7d63ca29221
9bd47696851110764486016f7d91f3de786818e87e4da88829dd76d5931f1fce.

Both bind the same wheel/site/module and fixture manifests. The refinement predecessor is byte-identical to the screen result and binds SHA256 9eacd9da983963cb203133ea301bfe6436ba4ccb5dec0f83a9265f79ac3cb751. Both results are explicitly COMPLETED_DEVELOPMENT_ONLY. Supervisor exits are zero; screen uses 5.1857283 s/161595392 B and refinement 33.5696293 s/248557568 B, within their recorded 600 s/8 GiB limits.

The complete c_lambda=1/2 rule is applied to all five channels without load-dependent changes: span=max(1,ceil(c_lambda*nbeam/nshell)), with divisibility and uniform projected geometry checks. Each support is a union of whole consecutive native halfcells, at least c_lambda shell-trace widths. The root shell column is clamped in all six nodal coordinates and beam node 101 is fixed in axes 0..4, leaving normal spin free; the transverse mesh is refined with the longitudinal mesh, preserving aspect 1.25.

The screen has four policy assignments, three actual owners and nine unique Fy/Mx/Mz solves. The beam-coarser trace (8 shell segments/4 halfcells) aliases c1/c2 at span 1 and 20 rows, correctly referencing owner/case 0 without inventing another solve. The beam-finer trace (8/16) uses spans 2/4 and 40/20 rows. Refinement uses shell meshes 16x4 and 32x8 with 32/64 halfcells, four owners and twelve unique solves; c1/c2 rows grow 80/40 then 160/80. Each owner reuses one factorization for its three declared loads. This is growing interface dimension, not one fixed global support. These two reciprocal ratio screens are not the full seven-ratio envelope.

## Physical transfer and interpretation

The diagnostic manual physical exerted-load pullback is checked against minus the local gap-work gradient and minus C.T times lambda, retaining surface/section arms, frame transport, director couples and the root moment arm. Its sign is connection load exerted on the domain, not the resisting covector. Ground wrench comes from the native supported residual/reaction result and is balanced against the declared applied wrench; it is not an external raw-nodeReaction claim.

Across all 21 unique retained routes I independently recomputed polynomial moments (orders 0,1,2), the physical x in [0.25,0.75] region wrench and translation/director gap maxima from raw station records: zero discrepancy with stored summaries. The region endpoints align with all admitted partitions, avoiding a changing physical observation region. The maximum ground-wrench difference from the declared opposing applied wrench is 3.067e-10 in its respective force/moment components. Saved free-equilibrium, weak-constraint and local-pullback checks satisfy their unchanged predicates. Physical force and moment components retain different units; I have not inferred a mixed-unit Euclidean norm or beta from these records.

For the fixed beam-finer ratio, c2/c1 relative applied-work differences over shell 8/16/32 are:
- Fy: 1.615729%, 0.346086%, 0.083554%.
- Mx: 0.212904%, 0.057365%, 0.022327%.
- Mz: 17.457061%, 6.244000%, 1.845309%.

Fixed-region transfer discrepancies contract overall, but individual components are not all monotone and some change sign. For example the Fy region Mx difference is about 3.3955, 0.00429, 0.06550 Nm; its Mz difference is about 42.6064, -0.1390, 0.8314 Nm. Pointwise first-variation gap maxima decrease on these three levels for each policy/load, but they do not supply a selection criterion or imply an exact finite-gap statement. These results support resolving the independent norm/control envelope next, without a fourth mesh or another tuning loop. They do not prove an asymptotic limit, quantify external accuracy, or choose c1/c2.

## Bounded norm-contract consistency review

Also read docs/agent_plans/B3_GE_E4_PL_M2_TRACE_NORM_CONTRACT_DEV.md, SHA256 4712d808715d9a21c7a4875f95b8e99acdc24b1951e1678d3215f647ecb6cdc0.

The algebra is consistent with surface translation U-skew(a)Theta, continuous supported H1 translation and independent cell-constant spatial rotation. The C_j/D_j block completion gives the stated positive auxiliary Schur operator and integrated-moment dual term; this is elimination within a kinematic norm, not condensation or replacement of actual mechanical K. The beam root translation boundary and free retained cell rotation are distinguished correctly. The shell norm retains the five physical translation/director fields and actual mapped supports, excludes drilling, and keeps bulk off-line physical fields rather than calling them gauges.

The force-equivalent mu, lambda=Q mu and Q-transformed pairing correctly require congruence of the reference dual under basis/unit changes. Raw mixed-unit singular values remain inadmissible. The independent reference functional is not constructed from the same candidate B_h/H_h in a way that normalizes away candidate instability. Reference surface-width averaging, fixed length/weights, enrichment/inverse-action accuracy, quotient positivity and physically justified nullspaces, independent good/bad controls, numerical tolerances and admissibility/deterioration thresholds remain explicitly open. This review checks internal consistency of the development derivation; it supplies neither a numerical beta claim nor a uniform discrete inf-sup proof.

No numerical jobs, additional mesh, source edits, downloads or unrelated historical audit were performed for this review. Only this review file was written. General M2/F03 and accuracy/qualification obligations remain open.

