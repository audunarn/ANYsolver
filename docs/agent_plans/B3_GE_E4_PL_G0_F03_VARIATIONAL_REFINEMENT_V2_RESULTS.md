# F03 classical variational line: independent refinements do not yield a reference

21 September 2026. **All 96 preregistered exploratory cases completed and
passed the finite-model numerical checks; the provisional physical-response
screen failed. F03/G0B remain open, and G1 production integration is barred.**
This is a classical independent planar comparator, not a native B3-GE/E4-PL
six-channel eccentric coupling or a completed physical reference.

The inventory and criteria were frozen at integration commit
`1f123848af8f8c6527d186d4f334040ef33cc2e0` in
`B3_GE_E4_PL_G0_F03_VARIATIONAL_REFINEMENT_V2_REGISTRATION.md`. It reused
the exact v1 classical source; the supervisor checked the sealed v1 raw
hashes and all inherited source hashes before creating the exclusive root
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-variational-refinement-v2/`.
The raw SHA-256 identities are:

| File | SHA-256 |
|---|---|
| `manifest.json` | `b198e2e8fac60a21d52d123c40b18e4dfb35a49e701cb6dc14ab056e0be12214` |
| `preflight.json` | `8a6dc936d517a2fb060208d086d51a36c71d3efb93fc6989e2075491e8904d78` |
| `records.jsonl` | `4a2fc2d63a102f8738abf4958795c7b501fc7c64bd6b244cf0d80ffd137c68c3` |

The read-only adjudicator checks all 96 distinct ordered case identities,
the frozen source hashes, each child stdout against its embedded response,
empty stderr, and zero exit status. The preflight four/six-point coupling
quadrature maximum was `4.95e-16` relative. Minimum row-normalized Gram
ratio was `.01503`; maximum free equilibrium, x/y force balance, moment
balance, doubled-energy balance and normalized weak residual were
`4.91e-13`, `1.11e-13/7.43e-12`, `8.76e-13`, `5.27e-13` and `1.28e-15`,
respectively. Maximum interface work cancellation was `3.06e-13 J`;
force/moment load-resultant errors were each `1.17e-10` in their respective
units. Longest case was `3.014 s`; summed child wall time `185.472 s`;
maximum sampled child RSS `159,715,328 B`. These are recorded finite
algebraic and resource checks, not a physical-line stability proof.

Signed beam-tip translations at `(Ns,Ny,Nm,Nb)=(16,8,32,128)` are in µm.
For all relative comparisons the denominator is
`max(|a|,|b|,.01U)`, where `U=1e6/(210e9·.07) m`.

| Shell/load | P0 tip | P1 tip | P0/P1 difference | P0/P1 mortar 16→32 |
|---|---:|---:|---:|---:|
| Q4 smooth | +36.582 | +34.463 | 5.792% | 8.614% / 6.436% |
| Q4 sine | −9.764 | −9.972 | 2.087% | 3.919% / 2.183% |
| S3 smooth | +35.750 | +33.639 | 5.904% | 8.752% / 6.538% |
| S3 sine | −9.562 | −9.779 | 2.219% | 4.028% / 2.303% |

The fourth column exceeds the `1%` law screen in all four shell/load
groups; every terminal fixed-beam mortar comparison exceeds `1%`.
By contrast, the terminal 128→256 beam-subcell changes at fixed mortar
range from `.036%` to `.157%`. Beam-subcell convergence in this model
does not erase law or mortar sensitivity.

At fixed 128 beam subcells and mortar 16, the terminal joint shell
`32/16→64/32` tip changes range from `.282%` to `2.281%` across the
eight law/load/shell combinations, and separate crossed width/length
edges reach `2.722%`. Thus the joint shell change cannot be used to
claim independent convergence; several of the explicit crossed edges
also exceed `1%`.

The sampled scaled pointwise gap lower bound exceeds `.05U` in **50/96**
cases. At the finest fixed-beam mortar level, the smooth-load lower
bounds are `.211–.242U` for both shell types and both laws; the sine
values are `.018–.019U`. Even the smaller sampled values cannot certify
a continuous upper bound. Small assembled weak moments, rank and global
balance do not establish physical pointwise bonding or uniform inf-sup
stability. No case was silently substituted or rerun.

The preregistered physical warning screen is **failed**. Preserve the
raw run and its adverse trends. Do not select P0/P1 as the production
law or use a favorable coarse/station response as an independent
reference. The next G0B work must resolve the physical trace and
endpoint/root contract, derive a reachable-image local dual and stable
lifting, and obtain a genuinely converged continuous-gap and
matched-idealization response before comparing with native eccentric
torque/shear mechanics. The larger G0–G6/B2 programme is unchanged.

Independent pre-execution review checked the 96-case inventory, both
crossed shell-refinement tiers, inherited source-byte checks, threshold
definitions, and bounded supervisor before the registration commit.
Independent post-execution read-only review matched actual predecessor
and v2 hashes, source/import identities, 96 ordered stdout/record pairs,
preflight, numerical/resource limits, and each physical comparison. It
agreed with the failed physical-screen decision and found no raw-evidence
or mechanics-calculation discrepancy. The adjudicator was subsequently
tightened to assert the reviewed preflight and resource conditions;
rerunning this read-only adjudication did not execute or modify a case.
