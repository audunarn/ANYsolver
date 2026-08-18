# E4-PL-Q1A independent preregistration plan review

## Verdict

`REJECT_NOT_ACCEPTED` (`REJECT_P1`)

The Q1A packet is not accepted for preregistration. The sole correction cycle is exhausted. Two priority-one defects remain: the D4 frame action is not source-closed, and the preregistration barrier was breached by executing science and writing observed outcomes into governing inputs before an accepted plan-only review and the first preregistration commit.

The terminal required by precedence is:

`BLOCKED_E4_PL_Q1A_PLAN_AUTHORITY`

No Q1B program is authorized. Production remains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`, and legacy `ShellElement` remains the default.

## Review authority and scope

- Review date: 2026-08-18
- Branch: `codex/s4-e4-pl-planar-linear-qualification`
- Required base/HEAD: `97c3150c9ecd41cf42fc108e9ff476497154428c`
- Required base tree: `9ea7e81a17c246e41b3fdfc236200d9dbf3e2b60`
- Review mode: independent, read-only audit of the frozen correction-cycle packet, except for creation of this review record.
- The reviewer did not invoke or emit caller-bound scientific output and did not modify production, package, workflow, API, selector, dispatch, serialization, recovery, or test paths.
- Copyrighted source material was inspected only as technical evidence. No source page, figure, table, screenshot, or copied passage is committed.

The audit covered authority, attachment and historical hashes, source identity and uniqueness, plan/cases/thresholds/allowed extent, research/oracle independence, geometry/material/support contracts, production-path exclusion, and the two-commit preregistration barrier.

## Content-addressed packet reviewed

All sizes are raw bytes and all digests are SHA-256 over raw file bytes.

| Path | Bytes | SHA-256 |
|---|---:|---|
| `docs/agent_plans/S4_E4_PL_PLANAR_LINEAR_QUALIFICATION_PLAN.md` | 4,806 | `851C586738CE8AF0A06BEFB7359D703F154CA82F71F479E506F58730DBD19283` |
| `docs/E4_PL_Q1A_LOCAL_ALGEBRA.md` | 5,550 | `6F619F9FB3E2548031EF019F65B1589E0C13592D4ED8C0037CD96EDD7AE58ED0` |
| `docs/E4_PL_Q1A_PLANAR_IDENTITY.md` | 8,165 | `2C993148EE561F5A95325BD69B2483226E7B77E7EAF5528CCA2C5719070D446D` |
| `docs/reference_cases/e4_pl_q1a_allowed_extent.json` | 1,632 | `9613C2B25508712116C4F0839320AC48D47EF24199493DDFFA087DD802A393EF` |
| `docs/reference_cases/e4_pl_q1a_baseline.json` | 1,562 | `9E399706B7C9CDE04299D0FF3E0DC0E07F48AC93260446A84438E8456BF345AC` |
| `docs/reference_cases/e4_pl_q1a_cases.json` | 2,489 | `6054927B7E02EDBFDB88C4DED25E4D2E1F1533D43992296669903F516F26CF88` |
| `docs/reference_cases/e4_pl_q1a_environment.json` | 720 | `828CCFEF31C2ABE865A7F623F910D698DA98C68305B2CFA47CA98755468511EA` |
| `docs/reference_cases/e4_pl_q1a_geometry_contract.json` | 873 | `AD5FDEA0B45295C7F48EEAE5EEA91FF9031BD5FFD01786ADA399726D3485AF1E` |
| `docs/reference_cases/e4_pl_q1a_material_contract.json` | 946 | `5115FDB79F4968D6777A7B3D908220CE753EE3D9A4E0E1402A759658475F70C4` |
| `docs/reference_cases/e4_pl_q1a_oracle.py` | 77,867 | `6BDBE8B00B5EFEF1865E3F0180BBF7D2A41BD7798CBBE5CC498F816CB1F771C8` |
| `docs/reference_cases/e4_pl_q1a_reference.py` | 52,348 | `C146DDE4BFDAE54125CB2530E55EAF8CB3A1A155E3668428C9EEF5E238AB0AB7` |
| `docs/reference_cases/e4_pl_q1a_source_map.json` | 5,244 | `343D5B415042F5DF12871E650E3EF86D6A61A1E08375AF19CCEAC25FE4E0B248` |
| `docs/reference_cases/e4_pl_q1a_support_contract.json` | 447 | `45A532E0C12DD9689E9932212F8BA5DE58463655137302FE1DE448EEDB06C878` |
| `docs/reference_cases/e4_pl_q1a_terminal_table.json` | 603 | `3918A551FFC1E8EAEC8A386DA24788DF6BF82A43A6636123F1C6E7614859E70D` |
| `docs/reference_cases/e4_pl_q1a_test_inventory.json` | 1,548 | `E05CD96EFA3EBE203A3629A64E8CEF23AC53195043A39CFE99E8546BD7489CCD` |
| `docs/reference_cases/e4_pl_q1a_tolerances.json` | 471 | `4D490C1B964A2A794C5D8F3F37D040022464BAF4492E5190A57401E142F86783` |
| `tests/test_e4_pl_q1a_authority.py` | 9,991 | `A6251869BE4051A01C5CD4D52BCBD0018DAA806E1F59B3F66348520C878B75ED` |
| `tests/test_e4_pl_q1a_exact.py` | 15,788 | `8952E7210C2B65A064D26CBCCCE3F2F394E0AD5DBAF73A818BA7B035470EBAE4` |

The eight-node preregistration inventory is 759 canonical UTF-8/LF bytes with SHA-256 `50A1602EA53058F128107D853CD97E94175CD231C51F0F786DF2DBA03CD3EB4F`.

### Bound external and historical authority

| Authority | Bytes | SHA-256 or identity |
|---|---:|---|
| Attached design input `S4_E4_PL_PLANAR_LINEAR_QUALIFICATION_PLAN_MAIN_97C3150.md` | 26,423 | `91CFD5305896AE4DAA5875BB55B70B3EE9D140F8E14165DBFD5904E6BA6D43BD` |
| `docs/agent_plans/S4_E4_PL_LINEAR_QUALIFICATION_PLAN.md` | 4,670 | `912322A8158255F17DDA44A3BB8FD59EFF1FC3B6B1E9D6BBB22B4E49A72BD193` |
| `docs/E4_INDEPENDENT_REVIEW.md` | 13,311 | `E3E9C529C2912CD0983941158AB615C9FE4D0903EEAFDF780E6762EB14B222B7` |
| `docs/reference_cases/e4_status.json` | 4,427 | `4D72F7974FAFD2D3D738AB5B7F8FA962C82BCF9629F6C5A911A49D6CE3BE7EF1` |
| `docs/reference_cases/s4_candidate_e1_material_fixtures.json` | 737 | `F29886ED86AC83081E04D4A352D3F25BA304393DB5C0FA64A3BCF4338D4EFA07` |
| `docs/reference_cases/s4_candidate_e0_dnv_material_fixtures.json` | 2,135 | `A16024C81522FB783841CC790C11772A10C8D0D936F9E678BE1CA981FD3DD016` |
| ANYmaterial commit | — | `4626887667f4c251479d26f321b9e73b046a2783` |
| ANYmaterial tree | — | `0d40fe67ea5e0b52f11a47aeb467d6993b205a2b` |

### Bound primary/background source files

| Source record | Bytes | SHA-256 |
|---|---:|---|
| WG2020 | 3,267,230 | `DB68AD45455999D47D6152E736D7277F28AC1C0D85063790B15FE4089293A712` |
| WG2004 | 878,871 | `8EBDBA969BB3E2A34288EA3B5D52014C68C0E30FD2A9B36B1F92EB3073AEE7A0` |
| Wiśniewski–Turska 2011 | 310,978 | `E6AFAADE32B33D710D3C038635FE2AD2729E32FB952C5EC6706E68A93A3B1860` |
| MITC9i reference | 1,302,612 | `5C66A76D39682F71C13208E71AFFA585FD3CD1E284185360B825572DC8BA048B` |

## Priority-one findings

### P1-A — D4 frame action is not source-closed

The correction-cycle implementations apply the D4 transformations in a fixed common frame for proper operations and use an improper `diag(1,-1)` action for reflected cases. The governing plan and geometry contract do not preregister that map or uniquely derive it from the cited source-skew construction.

The WG2020 frame construction is geometry- and numbering-dependent: its centre frame is obtained from the numbered element diagonals. Under proper D4 renumberings, reconstructing that source frame can rotate or swap the local axes. A fixed-common-frame action and a source-recomputed frame action are therefore distinct, source-consistent candidates unless their equivalence is proved under a frozen transport convention. The packet supplies no such proof or unique selection.

Consequently, the observed D4 covariance result cannot classify `NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE`. The formulation identity remains unclosed at the authority barrier. A successor must freeze, before execution, the numbered-frame reconstruction, component transport, multiplier transport, reversal action, and comparison frame, then prove that this choice is the unique consequence of the cited equations and the frozen work map.

### P1-B — Scientific execution breached the preregistration barrier

The governing program required a content-addressed plan-only review before scientific-oracle execution and before the first preregistration commit. During the sole correction cycle, the research implementation and independent oracle were executed and their observed D4 pass/fail counts, agreement digest, and proposed NO-GO classification were written into materials that are themselves preregistration inputs, including cases, source-map, and derivation records.

This is retrospective specification: an accepted preregistration packet cannot be reconstructed after observing its scientific outcome. The later review cannot cure the ordering violation, and the exhausted correction allowance prevents another authority-preserving cycle.

## Disposition of correction-cycle science

The correction cycle repaired the eight earlier implementation gaps involving covariance coverage, physical patches, material fixtures, support semantics, terminal mapping, semantic governance validation, independent cross-comparison, and the authority-test expectation. Those repairs do not cure P1-A or P1-B.

All correction-cycle scientific results are designated:

`NONCLASSIFYING_CORRECTION_CYCLE_EVIDENCE`

This includes:

- the research/oracle agreement digest `E2AB0103721712E610D203BA4A2649BBE86E8FDC4B8061BA8A9FBF8056C73BF5`;
- the reported 7/7 passing pre-output tests with the caller-bound test deferred;
- the observed D4 operation counts and any proposed `NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE` result; and
- all other mechanical, algebraic, covariance, patch, material, support, or recovery observations produced in that correction cycle.

These records may be retained for audit and for designing a new preregistered study. They cannot classify the frozen Q1A candidate, authorize Q1B, or support production activation.

## Final review disposition

The packet is unsafe to preregister and receives no ACCEPT. With the sole correction cycle exhausted, precedence is `BLOCKED_E4_PL_Q1A_PLAN_AUTHORITY`, not a scientific source, mechanics, patch, covariance, material, recovery, or Q1B terminal.

Further work requires a separately preregistered successor that source-closes the D4 frame action before any scientific execution and restores the plan-only-review/first-commit barrier. No production change, merge, push, publication, or cleanup is authorized by this review.
