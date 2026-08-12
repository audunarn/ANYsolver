# S4 A1/A2/A3 literal-formulation correction plan

## Authority and decision boundary

User authority is limited to the bounded stage accepted by the ANY ecosystem
boss on 2026-08-12:

1. **A1:** implement the literal 2025 Eq. (21) fixed-center-to-natural
   covariant drill-strain transformation;
2. **A2:** implement the literal 2025 Eqs. (24)-(25) membrane construction
   using the direct Appendix-B reciprocal-basis definitions;
3. **A3:** run the registered focused formulation gates, obtain independent
   formulation-audit acceptance, replay the unchanged content-addressed rank
   gate, and create a post-correction evidence packet.

This plan does not authorize a rank policy, gauge, penalty, stabilization,
constraint, contract relaxation, production activation, integration, shared
assembly edit, activity/deletion edit, handoff consumption, native-hybrid
merge, sibling-repository write, heavy suite, build, benchmark, profiler, or
qualification run. Options 1, 2A, 2B, and 3 in the accepted proposal remain
reserved for a later user decision.

## Registered baseline and source identity

- Repository: `C:\Github\ANYsolver`
- Isolated worktree: `C:\Github\ANYsolver\.perf2-worktrees\s4-reference-core`
- Branch: `codex/s4-reference-core`
- Git base: `cd4831c6352844be7853f2764ada4f72662ab15f`
- Accepted proposal SHA-256:
  `643D01EC94ACEFE4335CC3BEF9F97AE682D6940108491E0EE63E1EC7D8FF457D`
- Frozen pre-correction decoded source-bundle SHA-256:
  `0CA69CFFF1C79EA8892D4F89FDC6E7A72C93BBA7525A4EA2BF9A9DD323DA4577`
- Frozen qualification-contract SHA-256:
  `1591906DB90B83A7018E51D1C6CF35A545BCE28787ED3108713CDEECC51103F1`

The formulation modules are uncommitted files on this historical Git base.
Their authoritative pre-edit byte hashes are:

| File | SHA-256 |
|---|---|
| `docs/S4_IMPROVED_FORMULATION.md` | `DA874C2AC0ECCF2F595E39FC613AA6E456CC8CB8F7E7B25D6CB3389EF6599AB5` |
| `src/anysolver/shell_formulations/protocol.py` | `FC4C47D915CCAE5B2F8EA0F4D3768C0FF149AEA5197E30CD19610B508C114A9A` |
| `src/anysolver/shell_formulations/q4_common.py` | `DA543257685F1D4A869A9840B09A5B229ED27EA7D664C2A27B85CC2058DD08F3` |
| `src/anysolver/shell_formulations/mitc4_plus_d_reference.py` | `60EAEAB13208A3357CEF6BC36F1C2DD11E2D1865C55232CE073FACF67B09F550` |
| `src/anysolver/shell_formulations/mitc4_plus_d_scalar.py` | `804F973A8541060C523320487C466F10F2D387BE77ECFF99914DA9133EF8CB28` |
| `tests/test_s4_improved_reference.py` | `D77AEC9AB491D86D1EDAF747ABADD8ADA84B8A469EA7A2186C27AA92A2284E2A` |

No implementation file may change until this plan and the editing-agent plan
have been hashed, reported, and acknowledged by the boss.

## Exact write ownership

The sole formulation editor may modify only:

- `docs/S4_IMPROVED_FORMULATION.md`
- `src/anysolver/shell_formulations/protocol.py`
- `src/anysolver/shell_formulations/q4_common.py`
- `src/anysolver/shell_formulations/mitc4_plus_d_reference.py`
- `src/anysolver/shell_formulations/mitc4_plus_d_scalar.py`
- `tests/test_s4_eq21_eq25_reference.py` (new)

The coordinator alone may create the following evidence files after the
implementation interface freezes:

- `docs/S4_A1_A2_A3_COMPLETION_PACKET.md`
- `docs/reference_cases/s4_free_element_rank18_post_correction.json`
- `docs/reference_cases/s4_free_element_rank18_post_correction_output.txt`

The permanent gate `tests/test_s4_improved_reference.py` is read-only and must
remain byte-identical at SHA-256 `D77AEC9...84E2A`. The accepted Eq.25/Eq.27
oracle and rank-bundle artifacts in the integration worktree are read-only
inputs and must not be rewritten here.

## Explicit exclusions

Excluded from every edit in this stage:

- `src/anysolver/__init__.py` and every package export;
- `elements.py`, `fe_core.py`, `assembly.py`, `matrix_assembly.py`, nonlinear,
  recovery, session, cache, dispatch, serialization, and shared hot paths;
- all activity/deletion policy and the authoritative `ElementActivity` seam;
- handoff commit `931ed76943dc84fb9d01b26a5d6dd4c46af3d74a`;
- native-hybrid commits `1fd1c196518ac92b9dee920676f54c2d0cf58d26` and `7daa6e8`;
- every sibling repository and geometry document/live geometry API;
- the frozen 113-claim contract and all rank-policy choices.

## A1 equation-to-code contract

The implementation must retain the Eq. (17)-(19) drill tensor in the fixed
center contravariant basis, form its symmetric tensor components, and apply
the literal Eq. (21) double covariant transformation at every evaluation
point before adding the result to natural membrane rows. Tensor shear and
engineering shear conversion must occur exactly once at the documented API
boundary. Eq. (21) must not alter displacement interpolation or mass.

## A2 equation-to-code contract

The selected 2025 path must use the printed outer A-E tie ordering, internal
barred points, `lambda=j0/j(r,s,0)`, and complete `Q(r,s) R(r,s) S` map with
the direct Appendix-B reciprocal-basis definitions. Jacobian sign and tensor
shear conventions must fail closed and be tested. The 2017 Eq. (27) operator
may remain only as an explicitly named internal reference function used for
comparison; it may not be the default 2025 path, export, serialization value,
or fallback.

## A3 focused gates and definition of done

Focused, non-performance gates must cover:

- literal Eq. (21) component mapping against an independent tensor oracle;
- literal Eq. (24)-(25) columnwise equality against an independent QRS oracle;
- square, affine, skew, tapered, distorted, and valid warped mappings;
- center, 2x2 Gauss, and hostile interior points;
- outer/barred ties, direct Appendix-B basis, `lambda`, tensor/engineering
  shear, Jacobian sign, cyclic renumbering, anchored reversal, and arbitrary
  rigid rotation;
- membrane extension, in-plane shear, bending, transverse shear, paper patch,
  objectivity, symmetry, no significant negative stiffness mode, and scalar /
  generalized consumer consistency within the owned reference boundary;
- deterministic signatures and explicit distinction between 2017 comparison
  and selected 2025 behavior;
- zero production ANYgeometry imports, document parsing, or live geometry
  calls.

After independent audit acceptance, replay the unchanged gate from the
corrected owned modules. Preserve its exit and full diagnostics in the two
registered post-correction artifacts. The expected rank is not preselected;
do not xfail, relax, or modify the gate. Report any contradiction without
inventing policy.

Definition of done for this bounded stage:

1. source/doc changes remain inside the exact owned paths;
2. A1/A2 oracle and invariance gates pass;
3. an independent read-only formulation audit accepts;
4. unchanged-gate bytes are reverified before and after replay;
5. the machine-readable post-correction packet links source, papers,
   environment, commands, and observed diagnostics;
6. a clean atomic specialist commit is reported, but not integrated;
7. no heavy work runs without a new explicit performance lease.

