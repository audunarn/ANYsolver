# S4 Stage-M mechanics selection plan

Status: source-gated implementation plan. No Candidate A equation edit is
authorized until the primary-source checkpoint in S0 is content-addressed and
independently accepted. An independently accepted manifest recording an
unavailable source may release Candidate B comparison work under S3, but can
never release Candidate A or an overall selection.

## 1. Frozen base and authority

This stage starts from commit
`bac7d393bf212760f5befca716bfdf7b218e73a7` (tree
`164f6ae5911b9df792dee6f16ad30b5529f2cb0c`) on branch
`codex/s4-full-production-qualification`. Its governing program is
`docs/S4_FULL_PRODUCTION_QUALIFICATION_PROGRAM.md`, raw SHA-256
`17CB914002E362A5DB2B475981A46020C1F39E8BA5398B4A7BEC64C39EEEC4A7`.
The governing formulas, thresholds, fixtures, activation order, and terminal
rules are inherited without relaxation.

The coordinator is sole editor. Odin audits mechanics and derivations,
Forsete audits the case/contract matrix, and Heimdall audits production-seam
claims; all three are read-only. User authority governs this task directly.

## 2. Exact owned paths

This plan is committed alone before scientific work. During S0, the
coordinator alone may add and commit only
`docs/reference_cases/s4_stage_m_source_manifest.json`. After that manifest is
independently accepted, the coordinator alone may add these remaining new
paths:

- `docs/S4_STAGE_M_CONSTRAINED_DERIVATION.md`;
- `docs/S4_STAGE_M_ENERGETIC_DERIVATION.md`;
- `docs/S4_STAGE_M_SELECTION_REPORT.md`;
- `docs/reference_cases/s4_stage_m_mechanics_cases.json`;
- `docs/reference_cases/s4_stage_m_dyadic_interval.py`;
- `docs/reference_cases/s4_stage_m_mechanics_oracle.py`;
- `docs/reference_cases/s4_stage_m_mechanics_output.json`;
- `docs/reference_cases/s4_stage_m_mechanics_contract.json`; and
- `tests/test_s4_stage_m_mechanics.py`.

No existing production source, package export, selector, serialization,
assembly, activity, constraint, recovery, nonlinear, buckling, batch, sibling
repository, workflow, or accepted S4 evidence path is owned. The untracked
`tmp/` tree, primary PDFs, rendered review pages, and qualification residue are
preserved and excluded from commits. There is no cleanup authority in this
stage.

## 3. S0 - primary-source checkpoint

Before implementing a Fox-Simo equation, obtain a lawful copy of D. D. Fox and
J. C. Simo, *A drill rotation formulation for geometrically exact shells*,
CMAME 98 (1992) 329-343, DOI
`10.1016/0045-7825(92)90002-2`. Do not bypass a paywall, CAPTCHA, access
control, or publisher safety page. The PDF stays untracked in the task-owned
`tmp/s4_stage_m_sources/` directory.

For an acquired source, the source manifest must bind the raw PDF SHA-256,
byte size, page count, title, authors, DOI, acquisition URL/provenance, and the
exact page/equation
locations used for the continuous constraint, multiplier functional,
linearization, regularization interpretation, and finite-element multiplier
space. Render and visually inspect every cited page. A manifest amendment must
also freeze the source-derived discrete interpolation and quadrature before
the first Candidate A mechanics run. Abstracts, snippets, secondary
descriptions, and model recollection are corroboration only and cannot satisfy
the acquired-source branch of S0.

If the source cannot be obtained, report
`BLOCKED_PRIMARY_SOURCE_UNAVAILABLE`; do not classify Candidate A and do not
select either candidate. After the unavailable-source manifest is independently
accepted, Candidate B may still be derived and evaluated as comparison
evidence, but a Candidate B pass cannot convert the blocked overall selection
to `GO`.
If an acquired, hash-bound, renderable source does not substantiate the
asserted continuous constraint, small-rotation limit, or multiplier variation,
report `NO_GO_CANDIDATE_A_SOURCE_MISMATCH`; do not fill the gap by analogy or
invention. That frozen source no-go may advance to S3.

## 4. S1 - basis-invariant linear stop gate

Run this gate before topology sweeps or nonlinear implementation. At the flat
four-node reference element, let `q in R^24`, let the literal published strain
operator be `B` with frozen `rank(B)=16`, let `R` be the six-column rigid basis
with `rank(R)=6` and `B R=0`, let `C` be the source-derived linear constraint
Jacobian with `rank(C)=p` and `C R=0`, and let `T` be any full-column basis of
`ker(C)`. Acceptance requires simultaneously:

```text
rank(B T) = rank(B) = 16,
T ker(B T) = range(R),
and exact work/energy equivalence on range(T).
```

Rank-nullity then gives the necessary invariant identity

```text
dim(T) - rank(B T) = 6,
(24 - p) - 16 = 6,
p = rank(C) = 2,
rank([B;C]) = rank(B) + p = 18.
```

Therefore any discrete constraint with effective rank other than two fails
Candidate A. In particular, a four-mode Q1 multiplier whose Jacobian has rank
four cannot be reduced after seeing results: it has `dim(T)=20`, so retaining
six null modes forces `rank(BT)=14` and deletes two published energetic
directions. No SVD-selected rows, `{1,rs}` or other hand-picked multiplier
subset, tuned quadrature, or topology-specific rank target is admissible.
Only a two-mode or topology-adaptive multiplier space derived independently
from the primary variational formulation and a preregistered inf-sup argument
may proceed.

The oracle must prove this theorem with exact rational matrices and again with
the registered interval/rank calculus. It must serialize `C`, `T`, every
removed subspace, `rank(C)`, `rank(BT)`, `ker(BT)`, rigid containment, and the
energy/work pullback; raw degenerate singular vectors are never evidence.

## 5. S2 - Candidate A certificate

Only after S0 and S1 pass, implement the separately named constrained
candidate from the source-derived modified midsurface deformation gradient,
polar rotation, independent shell rotation, and relative twist. Freeze the
finite-rotation branch, continuous multiplier space, discrete multiplier
pair, quadrature, and configuration derivatives before outcomes.

The independent oracle must certify:

- the small-rotation limit `theta_D-omega_p,D=0`;
- the linear KKT operator `[K C.T; C 0]` and, when reduced, exact
  `T.T K T`, `T.T M T`, loads, geometric stiffness, recovery, and state maps;
- the nonlinear KKT tangent including
  `sum(lambda_a Hessian(g_a))`, with no penalty or `C.T C` term;
- analytic rigid containment plus an exact or outward-rounded interval
  nonzero-minor certificate for every claimed rank;
- discrete inf-sup stability, frame/origin/scale/numbering covariance, and
  curved/intersection mesh convergence; and
- no loss of any positive-energy membrane, bending, shear, or published `/D`
  direction and no surviving positive-mass quotient mechanism.

Candidate A returns `GO_CANDIDATE_A` only if every governing case is stable at
all registered precision/sensitivity points. Any proven mechanical failure
returns `NO_GO_CANDIDATE_A` with a minimal counterexample. A numerical
borderline without exact/interval closure returns `UNCLASSIFIED_CANDIDATE_A`
and stops Candidate A; it is not permission to tune, classify, or select A.
Candidate B is still evaluated under S3, while the overall selection remains
`UNCLASSIFIED`.

## 6. S3 - Candidate B independent comparison

Candidate B is independently derived and evaluated against the same frozen
case matrix regardless of whether Candidate A passes, fails, is blocked, or is
unclassified. It is a separately named compatible `H_D` energy, not the
literal 2025 identity. Derive the full compatible strain of the Eq. 15-16
displacement enrichment while retaining literal Eqs. 24-25; the immutable
published Eq. 21 remains baseline evidence and is superseded only inside
Candidate B.

Use only the existing physical constitutive tensor. Do not introduce a drill,
Cosserat, couple-stress, thickness-, mesh-, shear-modulus-, or empirically
scaled coefficient. The exact zero-mass common-drill `G` may be removed only
by the already authorized explicit and reported exact reduction. Acceptance
requires exact rigid annihilation, coercivity on the positive-mass `Z`
quotient, no locking, correct thin/thick limits, energy/work equivalence, and
all governing precision/topology gates. The terminal values are
`GO_CANDIDATE_B`, `NO_GO_CANDIDATE_B`, or
`UNCLASSIFIED_CANDIDATE_B` under the same fail-closed rules. Final selection
still prefers Candidate A if and only if A passes every gate. Candidate B may
be selected only when A has a proven `NO_GO` and B passes every gate. A blocked
or unclassified A leaves the overall selection blocked or unclassified even if
B passes; B's result remains recorded comparison evidence.

## 7. Exact/interval oracle contract

Inputs use tagged rational, signed power-of-two, and explicitly defined
radical records; binary floats are forbidden in scientific fixtures. The
dyadic interval implementation uses outward-rounded endpoints and records the
precision, rounding mode, dependency manifest, and every certified minor.
Exact integer/rational results are preferred. No interval is narrowed using a
binary64 or previously observed result.

The binary64 comparison uses the governing `eps64`, thresholds, residuals,
projector rules, and `0.25/1/4` multipliers. Independent 80/160/320-decimal
calculations and exact/interval certificates must agree categorically. Same-
environment output bytes are canonical UTF-8/LF JSON and repeat byte-for-byte;
cross-runtime claims use the frozen numerical equivalence gates.

The inherited mechanics-ID union is copied exactly from these frozen inputs:

| Inventory | Raw SHA-256 |
|---|---|
| `tests/test_s4_eq21_eq25_reference.py` | `E5112C7BF98A5C1F8F3FB28D2331B76B9B872F073372D0E7045AA59E70703B36` |
| `docs/reference_cases/s4_nullspace_semantics_cases.json` | `223C0E1A1F03D30AA5EFBB13E8ECD8F64E5F7F0865E6F11274577D15C6691ABF` |
| `tests/test_s4_nullspace_semantics_proof.py` | `B6E23E5C1D1F90702464487707345E14D0A2A65B87D18D0076EB546064B789F3` |
| `docs/reference_cases/s4_drill_constraint_cases.json` | `B4D663382302E971752F0757F6E869549A54234F485235E06DBEF74085860F38` |
| `tests/test_s4_drill_constraint_derivation.py` | `63B36AFEA4AC7C082F5BF46FB1E0A7EAA5D30ACD6E8F1D2172139E62741B7B80` |
| `tests/test_s4_geometry_handoff.py` | `942BCAF44FCA897A231F0685EF6466BCC1ED1716C017C644677606C58AEE3250` |
| `tests/test_s4_restricted_integration.py` | `15EE81C022CCAC1BF425308479F01978C355CA002A460C334C9921DFC8E94C30` |
| `tests/test_s4_restricted_activity.py` | `AAEDCA8FE1AB61552A4566BACF73855FCEF0F49CE20501901E2D3CDCCA8068B4` |
| `docs/reference_cases/s4_restricted_release_contract.json` | `08950098FD43473DCAEFA6C3ABFE35C95AA45441D1D677288FB4CEF6949227CD` |
| `tests/test_s4_improved_qualification.py` | `B77C7A854A3C8A5780600DE983F95831DD500B0271EEFF7260399E53FC313053` |

The new mechanics contract must enumerate the exact union of every case/test
ID in those inputs, preserving each ID byte-for-byte. No drop, rename, umbrella
ID, wildcard replacement, or outcome rewrite is permitted. Candidate-specific
IDs are appended after that inherited union. This freezes Eq. 21, Eqs. 24-25,
nullspace, drill-constraint, rigid, patch, topology, support/MPC, coupling,
activity/deletion, and covariance evidence without discretionary filtering.

## 8. Focused verification and commit gates

Before a scientific run, independently verify the child-plan, source-manifest,
case, and oracle hashes and the exact owned extent. Then run, serially:

1. source-manifest/schema and closed-input-grammar tests;
2. the exact rank-two necessity theorem and hostile rank-one/rank-three/rank-
   four counterexamples;
3. Candidate A flat/warped/curved/topology and interval certificates;
4. Candidate B gates against the identical frozen matrix in every run;
5. the unchanged accepted Eq. 21/Eq. 25, nullspace, drill-constraint, and
   restricted-integration focused tests; and
6. deterministic output replay plus `git diff --check` and exact-path checks.

Every terminal mechanics packet receives independent Odin/Forsete/Heimdall
review before staging. Commit plans separately from science. Commit the final
selection packet atomically only after review. A Stage-M `GO` authorizes a new
content-addressed Stage-P plan; it does not authorize production edits,
activation, integration, push, publication, or cleanup by itself.
