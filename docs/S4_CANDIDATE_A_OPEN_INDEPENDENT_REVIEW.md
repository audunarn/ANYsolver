# Candidate-A open qualification: independent review

## Decision

**ACCEPT.** The corrected candidate closes both registered exact necessary
screens, preserves the governing no-go and release terminals, and satisfies
the independent reproducibility and repository-scope gates.

This review binds baseline commit
`148ccb45ba79266d48dae1a84c4c500bdc1b4d85` (tree
`0a0809b2111c07098058fd43891729c6f9266b06`) to candidate commit
`b07a79bb79af32a6d456585a7c020cb2e13b2916` (tree
`8f31b373fd27d9d395dddc68f093090c02e7aaef`).

## Exact-screen findings

- A1 `candidate_a.d4.span_r_s`: the two exact constraint rows have rank 2;
  the eight accepted `ker(B)` witnesses have rank 8 and are annihilated
  exactly. Consequently `rank([B;C])=16` and `rank(BT)=14`. The terminal
  `PROVEN_FAIL_CANDIDATE_A1_FLAT_RANK` is exact and justified.
- A2 `candidate_a.d4.span_1_rs`: the same nonzero local `rs` multiplier on
  the four consistently oriented patch elements has squared norm 4, while
  its six-component admissible transpose action is exactly zero after the
  boundary clamp. Thus `beta=0` in the full unquotiented multiplier space,
  justifying `PROVEN_FAIL_CANDIDATE_A2_INF_SUP`.
- The aggregate terminal is `NO_GO_CANDIDATE_A_DISCRETE_PAIR`; the release
  terminal remains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`. Candidate B is
  preserved as `NO_GO_CANDIDATE_B`. The rank-four identity remains
  `mitc4_plus_d_published_2025_linear_spin_constrained_research_v1` with its
  existing no-production-release terminal.

## Provenance and reproducibility

The evidence graph is acyclic: frozen inputs feed the stdlib oracle, the
oracle identity feeds the contract, the contract identity feeds the output,
and the report binds those upstream objects. No artifact contains its own
hash. Canonical Git-LF identity is explicit; uniform LF and CRLF transports
normalize to the same named identity, while BOM, mixed newline, and lone-CR
transport remain blocking errors. All new Candidate-A-open paths are checked
out as LF.

Key identities are:

- A1 certificate:
  `2198458DCDC7EFB4684B5CC59ADAF6E9A0EECF381951CBDD21B286D6DB11097C`;
- A2 certificate:
  `68691E4F1F23E23ED7DF00C4210436BDD1A730ADB58ED3E755E15CC01ECC5F3B`;
- oracle:
  `7C3CE3821CE51FBA4689E437B4AB4AFD4CF1A3AA6638D1A800018E6B3FFCA682`;
- contract, 5,539 bytes:
  `7A9334964FB9A248EA1D44653C04E1F71731B3E605B053434CE7F252CCAB0D92`;
- canonical output, 2,644 bytes:
  `C42911E11BB1F1FA091F29FD0E3F5A3617310EF5F06C686E57C013171242B63C`;
- original ordered 64-node inventory:
  `7D71339F0621328AF54BC4BDFC04E3C7082EDA333B58E100C4C9550F0E9C85D9`.

Two separately spawned Python oracle processes emitted identical bytes and
both matched the committed canonical output. The focused command

```text
python -m pytest -p no:cacheprovider tests/test_s4_candidate_a_open_a1_rank.py tests/test_s4_candidate_a_open_a2_inf_sup.py tests/test_s4_candidate_a_open_qualification.py -q
```

completed with `11 passed in 3.97s`. Its wrapper also recollected the original
eight test files and matched all 64 ordered node IDs and the frozen digest.

## Repository extent and qualification meaning

Against the baseline, the candidate changes exactly 17 paths: only
`.gitattributes` is modified and 16 Candidate-A-open plan, evidence, report,
oracle, and test paths are added. `git diff --check` is clean. No production
source, public interface, selector, assembly, serialization, penalty,
stabilization, or `C^T C` path changes.

Finite-rotation, high-precision, performance, and production 24-DOF work were
correctly not run: both registered candidates already fail exact necessary
conditions. This ACCEPT decision closes the independent-review gate for the
no-go qualification packet; it does not qualify or activate an improved S4
production formulation.
