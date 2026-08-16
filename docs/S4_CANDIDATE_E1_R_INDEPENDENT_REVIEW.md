# Candidate E1-R independent review

## Verdict

`ACCEPT`

No P0 or P1 finding remains in the frozen Candidate E1-R packet.  The accepted
terminal is limited to
`PROVISIONAL_GO_CANDIDATE_E1_R_PLANAR_REGULARIZER_ONLY`.  It is not a
qualification of a physical rank-18 shell element, a production host, or a
modal/transient formulation.  The overall release terminal remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

## Bound review surface

The review used raw bytes, not rendered or normalized document content.

| File | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| `.gitattributes` | 1,502 | `1989E8C7412D004ADF6C4F819ED23AB4CDA5E932D7E7D0619D9C2B27122F1DDD` |
| `docs/agent_plans/S4_CANDIDATE_E1_ALLMAN_SESTRA_QUALIFICATION_PLAN.md` | 5,885 | `16093C1B1E95AAC790E5AC0F4A6D19927782A0D24194108367B77BCDB5CA6BBE` |
| `docs/reference_cases/s4_candidate_e1_baseline.json` | 2,622 | `EA7E81C38912F14CB89CFD98302B6A8478D878939F7CFC1E3A60439667A745C1` |
| `docs/reference_cases/s4_candidate_e1_environment.json` | 1,330 | `F2DB5FF809FE0ED35ABE398FBFCECD133F2E8C36E96D1AB5C79354784F7216DE` |
| `docs/reference_cases/s4_candidate_e1_source_registry.json` | 2,628 | `C25197408932746D04C0651D082D5435369CEF94CFAF03BD3A12F8521A24B375` |
| `docs/reference_cases/s4_candidate_e1_material_fixtures.json` | 737 | `F29886ED86AC83081E04D4A352D3F25BA304393DB5C0FA64A3BCF4338D4EFA07` |
| `docs/reference_cases/s4_candidate_e1_test_inventory.json` | 1,751 | `3290ACA0B30CD8C23A2508543DC8889D1F0795F38CF237AF7E826833E230EA16` |
| `docs/S4_CANDIDATE_E1_R_DERIVATION.md` | 3,867 | `37B4C31FE326414339EE1EB9E8052161FF572DB13FB457FFEA71AEBAAF5322B1` |
| `docs/reference_cases/s4_candidate_e1_r_identity.json` | 1,382 | `201E8B7C33F055BF6BCC17CE2EB3FFDB5502C438013EB33419868990FACABA5E` |
| `docs/reference_cases/s4_candidate_e1_r_cases.json` | 1,256 | `695FBD1A4F07806444B26E3350F436FF9055A0816968ECFE65F20567B3B71EA9` |
| `docs/reference_cases/s4_candidate_e1_r_oracle.py` | 44,176 | `C45CE53597F5DC5A90B051B7BC336D8BD114A92ACFB20F1BF03A47C2117FA02E` |
| `docs/reference_cases/s4_candidate_e1_r_contract.json` | 4,120 | `9F3F19DD7BE8868D98E7B487FDD488DB9A77ACA429F12FB9824261551B6F7A4C` |
| `docs/reference_cases/s4_candidate_e1_r_output.json` | 5,041 | `ED26CF65363AD97BFA57234EA6CC7C708D8E94B4D477AAC64F5C6BAFB44B749B` |
| `docs/reference_cases/s4_candidate_e1_status.json` | 2,230 | `D9DDF6EFF2BC2A8C261F988BE9A7598867588D7BF78A1D0398EFE041C3CCC22D` |
| `docs/S4_CANDIDATE_E1_QUALIFICATION_REPORT.md` | 5,586 | `72DCCDDA0374946FB41DD3A47967196E025EAB9157959D1472D2EE488A0A30AA` |
| `docs/reference_cases/s4_candidate_e1_a_contract.json` | 3,877 | `78ACB0EACC002B79C17A1E2C434FB890F64C7C178CA56493A7145F8E0EC5BFFA` |
| `docs/reference_cases/s4_candidate_e1_a_output.json` | 2,397 | `8022ECC3FB9D78637851EAF751044ABEE3C7E09D428160302450B726BD710788` |
| `tests/test_s4_candidate_e1_a_exact_rank.py` | 2,715 | `9D9FE91A1E77747215B9620D9CDFE0C13492BCE0F917696769E69B48847A7E6A` |
| `tests/test_s4_candidate_e1_a_qualification.py` | 5,671 | `B4E894462E1B3480EFB9A00BE8D92D374B145B36CFDA7AC4C834917084252529` |
| `tests/test_s4_candidate_e1_r_exact_regularizer.py` | 4,005 | `470F8734FE1E76BAAFD1F82289DE8BC48D9B1B8BD6350EABAB5EC0A0CA7C7318` |
| `tests/test_s4_candidate_e1_r_qualification.py` | 7,718 | `7253255EE7F28DCFE793ADE814640BDF94D14F8680B2AD55C5CD92393F132619` |

The E0 authority was independently checked at commit
`87b639499187736c59d87bc4aa8e6bd7f819d28b` and tree
`c01fd5cab7b63325e6cb5b70000f4586d4788563`.  The production-qualification
base remains `a9b45ca95303bc4b30b893fbb0d7177f9c98db03`.

## Exact projector and scale audit

For an eligible element the frozen stiffness scale is

```text
Dmean = trace(K_theta_theta^mat)/12
cK    = 10^-8 Dmean
R4    = (4 cK/3) (I4 - 1 1^T/4).
```

`K_theta_theta^mat` is the condensed, physical, pre-regularizer material
rotational block.  Geometric stiffness, supports, constraints, MPCs, prior
artificial terms, and E1-R itself are excluded.  For `Dmean>0`, `R4` is
symmetric positive semidefinite, has diagonal `cK`, off-diagonal `-cK/3`,
rank three, zero row sums, and eigenvalues
`{0,4cK/3,4cK/3,4cK/3}`.  Its kernel is exactly the constant drill vector, so
there is no absolute drill-to-ground term.  Nonpositive `Dmean` is ineligible.

The 24-coordinate block is `J_n^T R4 J_n`, where `J_n` projects each nodal
rotation onto the exact common component normal.  The rational oracle checks
all eight D4 permutations, a 3-4-5 orthogonal frame rotation, and normal
reversal.  The reference case has `Dmean=4`, `cK=1/25000000`, rank three,
and the expected eigenspace at factors `{1/10,1,10}`.  The trace scale and
the embedded block are frame covariant.

## Component gauge, constraints, and activity

The local projector deliberately retains one constant-drill gauge.  After
activity and hard deletion, the component graph is rebuilt from elements with
positive effective regularizer scale.  Every positive scale preserves
connectivity; a zero scale deletes that graph edge.  The unscaled physical and
regularizer contributions are combined first and the activity factor is
applied once.  The exact hostile calculation distinguishes this from an
activity-squared implementation.

For each component, `Z` contains its constant-drill vector and `W` contains
the objective area-weighted covector with nodal weights
`w_i=sum_(e incident to i) A_e/4`.  If homogeneous support and eligible
pure-drill MPC rows are collected in `A`, a canonical exact basis `S` of
`ker(AZ)` identifies only the surviving gauges.  The added rows are

```text
H = S^T W^T.
```

Because `W^T Z` is the positive diagonal matrix of component areas,
`H Z S` is positive definite and removes exactly those surviving gauges.
The exact cases close unsupported components, one supported component, full
support, and a cross-component equality without redundant rows.  A unit 2 by
2 Q4 patch has scalar rank eight, the registered quarter-area weights sum to
four, and its one gauge raises the augmented rank to nine.  The activity
bridge has rank seven while positive and splits into two rank-six components
when its middle scale becomes zero.

## Eligibility and non-intrusion

Eligibility is fail-closed.  A component must be explicitly declared planar,
have exactly zero coplanarity triple products, nonzero consistently oriented
element normals, no host drill stiffness or physical/drill coupling, no
normal drill-moment transfer, and no mixed physical/drill MPC.  There is no
tolerance-triggered automatic activation.  The warped `1/1000` fixture is
rejected exactly, and normal reversal does not change the quadratic form.

For an eligible host the four required null identities are
`K0 Q=0`, `KG Q=0`, `Q^T f=0`, and `recovery Q=0`.  They give a block-diagonal
proof: E1-R changes only the gauge-reduced drill equations, while physical
static displacement, recovery, and the finite physical buckling spectrum are
unchanged.  The rational fixtures retain displacement `(2,3)`, recovery `8`,
and buckling factors `(2,3)` across all three decade sensitivities.  E1-R
contributes exactly zero geometric stiffness and no physical stress,
resultant, yield, fatigue, recovery, or load channel.

The current legacy `ShellElement` is not an eligible host.  Its frozen source
contains existing drilling stabilization and assigns positive rotary inertia
to all three nodal rotation axes.  The output therefore applies neither the
E1-R stiffness nor its mass pattern to the legacy element.

## Conditional mass boundary

The separately gated mass rule is

```text
Mmean = trace(M_theta_theta^phys)/12
cM    = 10^-12 Mmean
RM    = (4 cM/3) (I4 - 1 1^T/4).
```

It may be used only after the exact pre-audit `Mphys Q=0`.  The registered
massless-drill fixture has `Mmean=2`, `cM=1/500000000000`, rank three, and
preserves the constant gauge.  It changes neither translational mass nor any
reported physical mass property.  A host with existing drill rotary inertia,
including the current legacy shell, is ineligible.  This is only a conditional
matrix-pattern certificate; it carries no modal or transient qualification.

## Candidate separation and source boundary

E1-R was neither combined with nor used to rescue E1-A.  The E1-A terminal
remains `NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY`, its common-drill mode is not
relabelled as an E1-R result, and E1-R makes no rank-18 claim.  A combined
candidate requires a separately preregistered residual, rank, mass, and
recovery program.

The two installed manuals were checked locally against the registered raw
identities:

| Evidence | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| Sestra 8.6 manual | 3,937,204 | `68E904E8E1B6800BC04FAA60299E17DEB29E3AB79B1823E09A7DD2F1C02FB1F3` |
| Current installed manual, self-identified 11.0.0 | 4,353,645 | `A7F0D3C4135B9ADC025229F3A91C1FB60E755F3CE3F176EA0EF4B6D7555A6334` |

They are copyrighted technical evidence and corroboration only.  The packet
commits no manual page, image, figure, quotation, or PDF; `git ls-files
'*.pdf'` is empty.  The Q4 projector, component gauge, and mass normalization
are independently derived or frozen ANYsolver rules, not a Sestra binary or
FQAS reproduction.  The superseded `k_D=sqrt(det(As0))`,
`j_D=rho_A ell^2`, and absolute-ground proposals remain excluded.

The material fixture binds 17 existing DNV-RP-C208-backed rows across S235,
S275, S355, S420, and S460 with no new public field.  RP-C208 remains a
recommended practice, not a class rule or a July-2025 RU-SHIP material table.
July 2025 is only the registered project rule edition.  The permitted claim is
“compatible with DNV analysis workflows,” never DNV approval.

## Reproducibility and test audit

The two required test tiers were kept separate:

1. In a clean LF-materialized checkout of the exact E0 commit and tree, using
   the five registered absolute pinned dependency roots and recorded runtime
   variables, the reviewer reran the exact ordered 94-node inventory:
   `94 passed in 120.34s`.
2. On the active E1 packet, the two E1-A and two E1-R test files ran as a
   separate focused suite: `15 passed in 0.89s`.

The R oracle was also executed twice after the final source-role rebinding.
Both processes returned empty stderr and the same 5,041 output bytes, exactly
matching raw SHA-256
`ED26CF65363AD97BFA57234EA6CC7C708D8E94B4D477AAC64F5C6BAFB44B749B`.
The contract/output tests distinguish baseline drift from caller-contract
failure and enforce canonical UTF-8/LF JSON.

The index diff is empty.  The only tracked worktree diff is the LF transport
addition in `.gitattributes`; all E1 evidence paths are within the contract's
allowlist.  No production path is allowlisted or changed, and the oracle
revalidates the frozen canonical identities of the five production sources.
There is no API, serialization, selector, export, dispatch, default, push,
publication, cleanup, or activation authorization.

## Findings and conclusion

P0 findings: none.  P1 findings: none.  No lower-priority defect was found
within the declared proof-only scope.

The exact projector, objective component gauge, activity/deletion semantics,
eligibility barrier, conditional mass rule, and static/buckling non-intrusion
certificate support
`PROVISIONAL_GO_CANDIDATE_E1_R_PLANAR_REGULARIZER_ONLY`.  The qualification
does not make the current legacy host eligible, does not alter E1-A, and does
not change the production terminal.
