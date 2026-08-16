# S4 Stage-M mechanics selection report

## Terminal decision

Stage M is closed without a selected production formulation.

- Candidate A: `BLOCKED_PRIMARY_SOURCE_UNAVAILABLE`.
- Candidate B: `NO_GO_CANDIDATE_B`.
- Overall Stage-M status: `BLOCKED_PRIMARY_SOURCE_UNAVAILABLE`.
- Candidate B may resolve the overall selection: `false`.

The legacy S4 formulation remains the production default. This result does not
authorize Stage P, a selector, activation, production edits, integration,
push, publication, or cleanup.

## Governing identities

The result is bound to these raw SHA-256 identities:

| Artifact | SHA-256 |
|---|---|
| Full-production qualification program | `17CB914002E362A5DB2B475981A46020C1F39E8BA5398B4A7BEC64C39EEEC4A7` |
| Stage-M mechanics selection plan | `4AE07F5954C9A2E6E6B002BEA24A9FC274B528D405EE6E5FCACE630893021E5B` |
| Primary-source manifest | `22B7B9D56DCC180CEE29F43AD4F31C69547A7C74CB212FD5B7D301909A8C0BE6` |
| Candidate-A constrained status | `577BD98FC5609629BC078B27719ED72985E4BA81536A7C6D76CBA687322D5488` |
| Candidate-B energetic derivation | `ACD03B67474BF35A06B2183830E3195843D4254DB17F04A5540724F42EC9F3A5` |
| Mechanics cases | `912E07377C174E1FE031EEBA98DD5E8406C9A294AF2B3032D9AB5B38F67C7B94` |
| Dyadic interval implementation | `05C086DB11548AA4B77A5B31A5171792E08C053F93682D5FBED2D16425C16CC3` |
| Mechanics oracle | `1B123591388AE73E83E3BA7082E82D0A579BE856669D461AA500BF41FE772D48` |
| Mechanics contract | `2FBB419F0C09D909F2B6A1D4FF77285EB078E8A6E7DB10286ECC47282D1F90DA` |
| Canonical mechanics output | `3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D` |

The canonical output is 5,824,196 bytes, canonical UTF-8/LF JSON, and records
environment digest
`E72CCC90B86C67528BDC6E186581C1FBE422F5243CD88581B2E15D613FD7E59F`.

## Deterministic execution evidence

Two independent serial precision sets were executed. Corresponding shard bytes
and the two merged packets are byte-identical.

| Precision | Bytes | SHA-256 |
|---:|---:|---|
| 80 | 892,218 | `986679725F248E282FBA91F0A8CD72BA170CA6781C8EEF73C9454A7E1923EC5F` |
| 160 | 1,086,218 | `74B824A14C4E4ACDF898FD11FC2FD7BCA09B7DA07B3BC94E8A11CDD817A834D1` |
| 320 | 1,468,552 | `2ABFFA6A1D3B62C6FD412383D313D9B3482D80903A231923F6D911D61F96C9A8` |

Each merged packet is 5,824,196 bytes with SHA-256
`3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D`.
The terminal completion manifest is 18,215 bytes with SHA-256
`8D72BB8A4A4EB95F06F1D55091CE7F83557934CFE6466DC15E3B8764182CD193`.

## Candidate-B result

The frozen terminal precedence records five exact `PROVEN_FAIL` gates:

1. `candidate_b.constitutive.coefficient_free`;
2. `candidate_b.square.rank_and_quotient`;
3. `candidate_b.square.checkerboard_coercivity`;
4. `candidate_b.square.common_drill_exact_g`; and
5. `candidate_b.square.reported_exact_g_reduction`.

The decisive exact rational/unisolvent certificate gives Candidate-B strain
rank 15 rather than the preregistered rank 17. It also records combined B/H
rank 23, pure-drill rank 3, rigid rank 6, and rigid-plus-common-gauge rank 7.
Although the numerical precision/rule/multiplier records classify the free
square as rank 17, the independently reconstructed runtime B operator does not
bind to the exact operator at any registered precision; the corresponding H
operator binding succeeds. This is an exact mechanics/implementation mismatch,
not permission to change a threshold, quadrature rule, coefficient, fixture,
or terminal classification.

The inherited execution ledger remains explicitly fail-closed: all 146
inherited-ID occurrences, 20 parameter rows, and 8 drill sample rows are
recorded individually as unresolved `BORDERLINE`, never as inferred or
hash-only passes. Those rows independently prevent a `GO`, while the five
certified failures determine the `NO_GO_CANDIDATE_B` terminal.

## Exclusions and preservation

The output records all prohibited changes as false: Candidate-A equation
implementation, gauge relabeling, invented material coefficients,
penalty/stabilization, production-source edits, a rank-18 claim, and
selector/activation. No production or sibling source was changed.

The precision shards, repeat merge, completion manifest, isolated mpmath
environments, temporary proof helpers, basetemps, and `tmp/` review residue
remain preserved outside the atomic Stage-M science commit. No cleanup is
authorized by this report.
