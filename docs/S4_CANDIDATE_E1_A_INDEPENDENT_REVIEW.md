# Candidate E1-A independent review

## Verdict

ACCEPT.  No P0 or P1 finding remains in the frozen Candidate E1-A packet.
This accepts the reproducibility and correctness of the exact NO-GO
certificate; it does not accept E1-A as a usable element.

The reviewed scientific terminal is
NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY with reason
COMMON_DRILL_NULL_RANK_AT_MOST_17.  The release terminal remains
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED and legacy ShellElement remains the
production default.

The authority is E0 commit 87b639499187736c59d87bc4aa8e6bd7f819d28b,
tree c01fd5cab7b63325e6cb5b70000f4586d4788563, with production qualification
base a9b45ca95303bc4b30b893fbb0d7177f9c98db03.  The branch name is
codex/s4-candidate-e1-allman-sestra-qualification.

## Frozen raw identities

The following raw byte counts and SHA-256 identities were independently
recomputed from the reviewed files.

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| .gitattributes | 1502 | 1989E8C7412D004ADF6C4F819ED23AB4CDA5E932D7E7D0619D9C2B27122F1DDD |
| docs/agent_plans/S4_CANDIDATE_E1_ALLMAN_SESTRA_QUALIFICATION_PLAN.md | 5885 | 16093C1B1E95AAC790E5AC0F4A6D19927782A0D24194108367B77BCDB5CA6BBE |
| docs/reference_cases/s4_candidate_e1_baseline.json | 2622 | EA7E81C38912F14CB89CFD98302B6A8478D878939F7CFC1E3A60439667A745C1 |
| docs/reference_cases/s4_candidate_e1_environment.json | 1330 | F2DB5FF809FE0ED35ABE398FBFCECD133F2E8C36E96D1AB5C79354784F7216DE |
| docs/reference_cases/s4_candidate_e1_source_registry.json | 2628 | C25197408932746D04C0651D082D5435369CEF94CFAF03BD3A12F8521A24B375 |
| docs/reference_cases/s4_candidate_e1_material_fixtures.json | 737 | F29886ED86AC83081E04D4A352D3F25BA304393DB5C0FA64A3BCF4338D4EFA07 |
| docs/reference_cases/s4_candidate_e1_test_inventory.json | 1751 | 3290ACA0B30CD8C23A2508543DC8889D1F0795F38CF237AF7E826833E230EA16 |
| docs/S4_CANDIDATE_E1_A_DERIVATION.md | 2666 | BF40E075122C5F53DD7335F3A6FF3649393B5E25B98490DC389CCF2619B747E2 |
| docs/reference_cases/s4_candidate_e1_a_identity.json | 802 | 1A5D7A2E174A1BF7903DD4B188F56D7BDF2F1BC53639D3BE14FFFA5C010110FE |
| docs/reference_cases/s4_candidate_e1_a_cases.json | 571 | F654F446ECDCED1F80FE86C092425D1AC95EA2F244FD0D20BEE80D52F95EE11A |
| docs/reference_cases/s4_candidate_e1_a_oracle.py | 22724 | DBD69B6A3128848A100F3F76BC21BF3885D041CA2B17CA9EAEF0949E60A2EBEB |
| docs/reference_cases/s4_candidate_e1_a_contract.json | 3877 | 78ACB0EACC002B79C17A1E2C434FB890F64C7C178CA56493A7145F8E0EC5BFFA |
| docs/reference_cases/s4_candidate_e1_a_output.json | 2397 | 8022ECC3FB9D78637851EAF751044ABEE3C7E09D428160302450B726BD710788 |
| docs/S4_CANDIDATE_E1_R_DERIVATION.md | 3867 | 37B4C31FE326414339EE1EB9E8052161FF572DB13FB457FFEA71AEBAAF5322B1 |
| docs/reference_cases/s4_candidate_e1_r_identity.json | 1382 | 201E8B7C33F055BF6BCC17CE2EB3FFDB5502C438013EB33419868990FACABA5E |
| docs/reference_cases/s4_candidate_e1_r_cases.json | 1256 | 695FBD1A4F07806444B26E3350F436FF9055A0816968ECFE65F20567B3B71EA9 |
| docs/reference_cases/s4_candidate_e1_r_oracle.py | 44176 | C45CE53597F5DC5A90B051B7BC336D8BD114A92ACFB20F1BF03A47C2117FA02E |
| docs/reference_cases/s4_candidate_e1_r_contract.json | 4120 | 9F3F19DD7BE8868D98E7B487FDD488DB9A77ACA429F12FB9824261551B6F7A4C |
| docs/reference_cases/s4_candidate_e1_r_output.json | 5041 | ED26CF65363AD97BFA57234EA6CC7C708D8E94B4D477AAC64F5C6BAFB44B749B |
| docs/reference_cases/s4_candidate_e1_status.json | 2230 | D9DDF6EFF2BC2A8C261F988BE9A7598867588D7BF78A1D0398EFE041C3CCC22D |
| docs/S4_CANDIDATE_E1_QUALIFICATION_REPORT.md | 5586 | 72DCCDDA0374946FB41DD3A47967196E025EAB9157959D1472D2EE488A0A30AA |
| tests/test_s4_candidate_e1_a_exact_rank.py | 2715 | 9D9FE91A1E77747215B9620D9CDFE0C13492BCE0F917696769E69B48847A7E6A |
| tests/test_s4_candidate_e1_a_qualification.py | 5671 | B4E894462E1B3480EFB9A00BE8D92D374B145B36CFDA7AC4C834917084252529 |
| tests/test_s4_candidate_e1_r_exact_regularizer.py | 4005 | 470F8734FE1E76BAAFD1F82289DE8BC48D9B1B8BD6350EABAB5EC0A0CA7C7318 |
| tests/test_s4_candidate_e1_r_qualification.py | 7718 | 7253255EE7F28DCFE793ADE814640BDF94D14F8680B2AD55C5CD92393F132619 |

All 24 contract and status references to packet inputs, contracts, and outputs
match their current raw byte counts and hashes.  Every registered E1 JSON file
is canonical UTF-8/LF JSON with sorted keys, no duplicate keys, no BOM, no CR,
and one terminal LF.

The local technical-evidence identities also match the source registry:

| Evidence | Bytes | SHA-256 |
| --- | ---: | --- |
| Superseded Candidate-E proposal | 36288 | 4499DA192F97D9BF7D89C3A9A8B5A68E6201CA5E2350E30918583464BF0E98EA |
| Sestra 8.6 manual | 3937204 | 68E904E8E1B6800BC04FAA60299E17DEB29E3AB79B1823E09A7DD2F1C02FB1F3 |
| Installed current manual, self-identified as 11.0.0 | 4353645 | A7F0D3C4135B9ADC025229F3A91C1FB60E755F3CE3F176EA0EF4B6D7555A6334 |

The corrected registry treats the Sestra 8.6 material as technical evidence
for the pattern and FQAS boundary, not as normative source code.  No manual
page, image, figure, quotation, or PDF is committed.  E1-A is expressly an
independent Allman-type derivation, not Sestra FQAS and not a reproduction of
the unavailable GWW 1992 element.  The WG2020 n=7, k=0 core and its printed
rank record remain the registered primary-source inheritance.

## Exact derivation audit

On the reference square, the frozen serendipity S2 monomial basis is

    1, r, s, rs, r^2, r^2 s, s^2, r s^2.

For each target edge, matching the complete quadratic trace on all four edges
produces 12 rational equations for eight coefficients.  Exact elimination has
rank eight and gives one of the four standard midside functions

    h0=(1-r^2)(1-s)/2,     h1=(1-s^2)(1+r)/2,
    h2=(1-r^2)(1+s)/2,     h3=(1-s^2)(1-r)/2.

Thus each edge solve has nullity zero; the four independent coefficient
blocks determine all 32 coefficients.  Adding the Q2 monomial r^2 s^2 gives
rank eight for nine coefficients and nullity one.  That is exactly the
interior bubble ambiguity excluded by the preregistered minimal S2 space, so
no observed rank or benchmark is used to choose it.

Writing one edge midpoint contribution as L(a theta_i+b theta_j), common-spin
invariance and the frozen two-node normalization give

    a+b=0,
    -a+b=1/4,

hence uniquely a=-1/8 and b=1/8.  Every drill-driven edge amplitude therefore
contains the nodal factor L(theta_j-theta_i)/8.

For the cyclic edge order (0,1), (1,2), (2,3), (3,0), these four differences
are generated by

    D = [-1  1  0  0]
        [ 0 -1  1  0]
        [ 0  0 -1  1]
        [ 1  0  0 -1].

An exact 3 by 3 minor is nonzero, D times the all-ones vector is zero, and
therefore rank(D)=3 with kernel span{(1,1,1,1)}.  Geometry maps, tangent
directions, differentiation, material maps, and quadrature can only left
multiply this frozen nodal factor.  They cannot create a fourth independent
drill column.  The S2 edge set is closed under the eight D4 vertex
permutations, and the oracle verifies that every corresponding incidence
matrix has the same exact three-dimensional row space, including reversals.

The WG core has 20 ordinary coordinates and contains six physical rigid
modes, so its operator rank is at most 14.  Appending four drill coordinates
through a map that factors through D can add at most three directions:

    rank(E1-A) <= 14 + 3 = 17,
    nullity(E1-A) >= 24 - 17 = 7.

The common-drill vector is not one of the six physical rigid modes.  If its
zero nodal translations equalled a physical rigid motion, then
a+omega cross X_i would vanish at all four nondegenerate nodes.  Differences
along two nonparallel edges force omega=0 and then a=0, while the common-drill
vector still has unit nodal normal rotation.  The exact 24 by 7 column audit
accordingly has rank seven.

The missing direction is inherited by both operations that might otherwise
appear to hide it.  If an enriched displacement or strain map is H=T D, then
H times the common vector is exactly zero and any consistent Gram mass
H-transpose rho H has a zero common-drill row and column.  In the mixed
operator, the common vector gives both Kqq g=0 and Kyq g=0.  Consequently the
Schur complement

    Kcond = Kqq - Kqy Kyy^-1 Kyq

also satisfies Kcond g=0.  If the local mixed block is not invertible, exact
condensation fails rather than restoring rank.  The oracle records these as
zero-factor consequences, not tolerance-sensitive singular values.

E1-A therefore cannot meet rank 18 with exactly six rigid modes.  The result
is independent of material, thickness, quadrature, distortion benchmark,
mass scaling, or solver tolerance.  Stopping before DNV response, thin-limit
stability, recovery, geometric-stiffness, and buckling execution is the
required fail-closed action, and the output records all such E1-A stages as
not run after the exact rank screen.

## E1-A and E1-R separation

E1-A and E1-R have distinct identities, cases, contracts, outputs, reasons,
and terminals.  E1-A forbids the regularizer, penalty, stabilization,
independent drill inertia, interior bubbles, and outcome-selected
coefficients.  Its output states that E1-R was neither combined nor used.

E1-R is registered only as a planar gauge regularizer.  Its identity forbids
combination with E1-A, and its output makes no physical rank-18 claim.  The
combined status says combined_candidate=false,
e1_r_changes_e1_a_terminal=false, and
residual_rank_or_mass_combination_authorized=false.  The separate provisional
E1-R fallback result therefore cannot repair or modify E1-A's exact NO-GO.
Any combination requires a new preregistered residual-rank, mass, and recovery
plan.

The excluded full-scale hypotheses k_D=sqrt(det(A_s0)) and
j_D=rho_A ell^2 remain absent, as do an absolute drill-to-ground diagonal and
any new public material parameter.  The reporting boundary remains
compatible with DNV analysis workflows, not DNV-approved.

## Reproducibility and tests

The review confirmed the required two-tier evidence without combining test
counts:

* The detached, clean E0 checkout at the exact commit and tree above ran its
  ordered 94-node immutable suite: 94 passed in 125.02 seconds in the
  independent run.  The coordinator report separately records the same 94
  nodes passing in 113.45 seconds.
* The active E1 focused A/R suite was rerun against the frozen bytes: 15
  passed in 0.90 seconds.  The coordinator report records 15 passed in 0.89
  seconds.

The split is necessary because the accepted E0 closeout intentionally rejects
successor paths.  The packet correctly describes the 94-node E0 result as an
isolated-baseline result and the 15-node result as the active focused suite.

Direct fresh-process execution was also repeated twice for each oracle.  Both
E1-A runs exited zero, emitted no stderr, and matched output hash
8022ECC3FB9D78637851EAF751044ABEE3C7E09D428160302450B726BD710788 byte
for byte.  Both E1-R runs did the same for hash
ED26CF65363AD97BFA57234EA6CC7C708D8E94B4D477AAC64F5C6BAFB44B749B.
The emitted contracts match their stored bytes.  Wrong contract identities,
duplicate-key JSON, baseline drift, and output non-overwrite behavior are
covered by the fail-closed tests, with baseline and contract failures kept in
their distinct terminal classes.

## Production and allowed-path audit

Before adding this registered review path, the only tracked worktree change
was the LF-only .gitattributes extension and the index was clean.  All E1
files were new paths admitted by the A and R contracts.  Existing untracked
qualification roots were preserved separately.  The five content-addressed
production sources match their accepted canonical-LF identities, and no
production path appears in either contract's allowed extent.

There is no production source, public API, export, serialization, selector,
dispatch, activation, or default change.  There is no push, publication,
cleanup, or authorization to combine E1-A and E1-R.  The only accepted E1-A
conclusion is the exact rank-deficiency NO-GO stated above.
