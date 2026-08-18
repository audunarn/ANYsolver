# E4-PL-Q1R independent preregistration review

## Verdict

`ACCEPT_Q1R_PREREGISTRATION_NO_P0_P1`

The plan-only packet is accepted for the first Q1R preregistration commit. This
verdict accepts only the numbered-frame identity, caller-bound inputs,
governance barriers, and repository boundary. It does not accept or authorize
an implementation, mechanics execution, scientific result, Q1B plan, or
production change.

Any byte change to a reviewed plan-stage artifact after this review invalidates
the verdict and requires `BLOCKED_E4_PL_Q1R_PLAN_AUTHORITY` unless a newly
reviewed successor packet is established.

## Review authority and method

- Review date: 2026-08-18.
- Branch: `codex/s4-e4-pl-q1r-numbered-frame`.
- Exact base commit: `ad90068a7ee78c3390dfe1b651f28be035094f41`.
- Exact base tree: `e4cbb750ade5f2a160525e12b4c47afc5733a36a`.
- Base parent: `0435fae39d02e6f3c946deba0b74f29522f90137`.
- Method: independent read-only authority, derivation, contract, case,
  tolerance, terminal, stage-DAG, and repository-boundary audit, except for
  creation of this review file.
- No Q1R reference implementation, oracle, scientific test, contract,
  scientific output, outcome, agreement digest, status, or Q1B plan existed or
  was executed during review.

The bound user design input is 27,001 bytes with SHA-256
`3D8FE3ACF79B7C78B4B1D22E1DF40792B04603BAF88C99A390A0B499A97D27CA`.
The governing packet correctly treats it as background design input rather
than a mechanics source.

## Content-addressed packet

All sizes are raw bytes and all hashes are SHA-256 over the raw file bytes.

| Path | Bytes | SHA-256 |
|---|---:|---|
| `docs/agent_plans/S4_E4_PL_Q1R_NUMBERED_FRAME_PLAN.md` | 7,203 | `A095EE95ABB3F62B42ABBBED077C74AE72F2B1EAA479DDBB241C321EF12722AD` |
| `docs/E4_PL_Q1R_FRAME_IDENTITY.md` | 10,857 | `60110EAE11EA8AFB6A08A89FEAC0F133AFBEBD8C2FC7948E5F1D91C361EF107A` |
| `docs/reference_cases/e4_pl_q1r_baseline.json` | 2,992 | `C5233265F1FDEFC0CCACA3B5D7A0002265D7C753527B08C38A4D56BDDFEB61FB` |
| `docs/reference_cases/e4_pl_q1r_environment.json` | 1,321 | `F629495E7E2A70FCBF2AF45FFD1CDB27DCE349334A1325FA83979ECE7C9278D7` |
| `docs/reference_cases/e4_pl_q1r_allowed_extent.json` | 3,073 | `F9C838D3432165FFC30158BF88B54C6C53FC3A52371CC534E08B9E265EED5052` |
| `docs/reference_cases/e4_pl_q1r_source_map.json` | 5,126 | `9412055CAF626D38313ACCD837C2A28EE150616EA57D27251DED97E54FA4BE3D` |
| `docs/reference_cases/e4_pl_q1r_frame_contract.json` | 6,522 | `AEE24E6CBA4F8093ABD948FB0A45372206BF4FB815385906D78C669E031284E5` |
| `docs/reference_cases/e4_pl_q1r_geometry_contract.json` | 2,293 | `712D81150A002DAB7C9AD52494DEBD1BA532E6475754CF43B9AA536D0AFF885E` |
| `docs/reference_cases/e4_pl_q1r_material_contract.json` | 1,698 | `98264E9466B9AE4E8D6A0841F39F75242572974E23F05F180FC646F2C2DFE8A4` |
| `docs/reference_cases/e4_pl_q1r_support_contract.json` | 1,727 | `51556AD2CE6730582CE94D602687B22991DC205DA6D1E0B9EEABC4F086F509EF` |
| `docs/reference_cases/e4_pl_q1r_cases.json` | 4,830 | `B439043B069982788A95489EFC26297E7095F8E94B9DEB924B9C7179077FE034` |
| `docs/reference_cases/e4_pl_q1r_tolerances.json` | 1,882 | `7A8A6BE902E97E4EBBF0558180DA70C4AEDC10C221AA54223612498B6621D9C6` |
| `docs/reference_cases/e4_pl_q1r_terminal_table.json` | 3,044 | `CDEA948B03C89511E6D65F598E7BF8E9F4C54B30848727C7520D040A5F2D7FDC` |
| `docs/reference_cases/e4_pl_q1r_test_inventory.json` | 1,421 | `92EDC3219B80D1D4AB63E535630925A25A6B293CD7E0586077E87EFF9537C136` |
| `tests/test_e4_pl_q1r_preregistration_authority.py` | 14,484 | `EC9CBA0F1537164377876786DF96DC2E17E20995DD670059201774DEA62EBFE8` |

The four-node preregistration inventory is 440 canonical UTF-8/LF bytes with
SHA-256 `67C7DDAC227F010672592B50600B31FBB6B103791A63405BFD6D6BA200A267E9`.
The independent review rerun passed all four authority nodes. The accepted E4
20-node tier remains separately bound to commit `97c3150c9ecd41cf42fc108e9ff476497154428c`,
tree `9ea7e81a17c246e41b3fdfc236200d9dbf3e2b60`, and is not combined with
the Q1R inventory.

## Findings

### Authority and historical boundary

The exact Q1A blocked closeout, first abort-preservation commit, four blocked
artifact hashes, and verdict `ACCEPT_BLOCKED_CLOSEOUT_NO_P0_P1` are preserved.
Q1A mechanics, D4 counts, and agreement data remain nonclassifying and are not
used as Q1R expected outcomes. The two overlapping asymmetric geometries are
included solely because of the explicit user request; their old Q1A outcomes
are expressly prohibited as input, prediction, or classification evidence.

The plan-only study and dormant qualification identities are distinct. The
candidate is `DORMANT_UNQUALIFIED`, is not registered in production, and may
not authorize Q1B except through the sole provisional Q1R terminal.

### Numbered frame and work maps

The eight D4 matrices, node permutations, determinant classes, and named `MD`
complete reversal are internally consistent with the convention
`xi_0=A_g xi_g`. Direct substitution into the WG2020 equation-7 diagonal frame
proves

```text
T(X^(g)) = T(X) diag(A_g,det(A_g)).
```

The lifted action is proper in three dimensions for all eight operations. No
independent reflected-frame repair remains selectable.

The packet also closes the node-only global permutation, proper global-frame
map, engineering-strain/resultant extraction, curvature and shear
pseudo-field signs, work conjugacy, multiplier coefficient transport,
`T5`/`QD` embeddings, projectors, physical load space, supports, reactions,
and numerical/physical recovery boundary.

WT2011 equations 26.44--26.45 are now frozen at equation level for the
geometry-dependent residual row, including `S1`, `S2`, `j_c`, `A`, `b1`,
`b2`, `gamma`, its energy, and the rule to reconstruct the row independently
for every numbered geometry. This removes the remaining implementation choice.

### Cases, arithmetic, and terminals

The six rational base geometries, all eight operations, rational proper global
rotation and translation, six rigid fields, membrane/bending/shear/combined
patches, physical load, support probes, and the single exact isotropic material
tuple are fixed before mechanics. Thickness is consistently `t=2/3`; `h_e`
is reserved for mesh size. The material matrices and patch identities are
dimensionally and algebraically consistent.

Categorical equality is structural or algebraic exact zero. Rank, PSD,
Jacobian positivity, and nonzero contradictions require exact or outward
dyadic certificates at 256, 512, and 1024 bits. Float64 has no classification
authority, and unresolved bounds fail closed to `UNCLASSIFIED`.

Terminal precedence distinguishes baseline, plan, source-frame,
implementation, contract/determinism, oracle/review, scientific no-go,
inconclusive, and provisional-plan outcomes. Every terminal retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

### Stage DAG and repository extent

The exhaustive allowlist separates `PLAN`, `IMPLEMENTATION`, `CONTRACT`, and
`OUTCOME` paths. Stage access is not inferred from worktree file presence. The
authority test instead requires exact commit subjects and parent chain, exact
stage-only `diff-tree` extents, and byte immutability of every earlier stage
through later commits, index, and worktree. All untracked paths outside the six
preserved roots must belong to the active committed stage.

At review time only the 15 preregistration inputs and this review path were
present. There was no reference, oracle, implementation manifest, scientific
test, contract, output, status, Q1B plan, or production change. `git diff
--check` was clean, the index was empty, and no `.gitattributes`, `src/`,
package, workflow, API, selector, serialization, dispatch, recovery,
production-test, export, or default path changed.

The sole plan-only correction cycle was used before this verdict to close the
exact residual row, hostile-case provenance, and commit-stage immutability
checks. No mechanics was executed during that cycle. A briefly spawned
unauthorized read-only child was interrupted before returning content or
changing files; none of its work entered this packet.

## Final disposition

No P0 or P1 finding remains. The packet may be committed exactly once as
`docs: preregister E4 PL Q1R numbered-frame qualification`. That commit must
contain exactly all 16 `PLAN` paths and have `ad90068a7ee78c3390dfe1b651f28be035094f41`
as its parent. Only after that exact commit may independent implementation work
begin. Scientific mechanics remains forbidden until the later implementation-
freeze and execution-authority commits both exist and pass their own reviews.
