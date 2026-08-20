# E4-PL-Q1S: Frozen-Identity Implementation Completion

## Purpose and authority

This is the executable successor to the blocked Q1R implementation stage. It
does not change the Q1R formulation. It completes two independent dormant
research implementations, freezes an execution contract before mechanics,
and performs one fail-closed local qualification.

```text
study:
study_e4_pl_q1s.q1r_frozen_identity_implementation_completion_v1

dormant candidate:
candidate_e4_pl_q1s.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1

branch:
codex/s4-e4-pl-q1s-implementation-completion

exact parent:
46231c56d4c7d24000421fc3ba0f4800239e64bd

parent tree:
c04f7f784d25790da105ae321636a7cae288d53e
```

The supplied `S4_E4_PL_Q1S_IMPLEMENTATION_COMPLETION_PLAN.md` is background
design input: 23,611 raw bytes, SHA-256
`0FCD3C99B5ED8A85BB7E5FFEADF41E0F6136087A45255502178AF4BB8A0F48ED`.
This corrected plan controls where it differs from that attachment.

Q1R is closed at `BLOCKED_E4_PL_Q1R_IMPLEMENTATION_IDENTITY`. Its scientific
classification is `NOT_ESTABLISHED`; Q1B is not authorized. The production
terminal is `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`, and legacy
`ShellElement` remains the default.

## Immutable inheritance

Q1S binds all 16 paths in Q1R Commit 1
`97edc4265a7ce5ca9763f66875d1336e419bcef4`, tree
`e511c461b59162029eaf3e8ceb93f144d94bf910`, including the Q1R
preregistration-authority test. It also binds all five files in the exact Q1R
blocked-closeout commit above and the accepted E4 core authorities:

```text
docs/reference_cases/e4_core_cases.json
5435 bytes
FE08E59D9E01073E04251C52544EDF10C4CC86861EA8B98FC6CB1A645427FEF2

docs/reference_cases/e4_core_contract.json
2284 bytes
8768ABDC5D77B5FCC1643AF69920EFEB83F27DDFBDE17525F06EE2B53A5C1678
```

The inheritance manifest records raw bytes, SHA-256, Git blob, and a row-bound
source commit for every inherited row. Q1R terminal identifiers and its old test
inventory are immutable historical inputs, not Q1S identifiers or a runnable
Q1S inventory. The Q1S terminal table supplies an explicit semantic map and a
new finite inventory.

Before preregistration, the accepted E4 suite was rerun only in an exact
detached `97c3150c9ecd41cf42fc108e9ff476497154428c` worktree: 20 nodes passed
in 7.42 seconds. Its 1,795-byte canonical node list retains SHA-256
`1C29534F6568AA2FF072F5D776E9D10BD71DE85F51C7562827FC6A3F0234E10F`.
This inventory remains separate from every Q1S inventory.

The eight Q1R drafts remain
`NONAUTHORITATIVE_SUCCESSOR_SCAFFOLDING`. Their source identities and exact
source-to-destination mappings are preregistered. They may be copied only
after Q1S Commit 1. Their initial copies and final corrected forms are both
content-addressed. Q1R source drafts remain untracked and unchanged.

## Frozen mechanics identity

Q1S retains the Q1R/E4-0 identity without coefficient, space, quadrature,
case, tolerance, or transport changes:

- flat planar Q1 geometry with the WG2020 equation-7 numbered frame;
- WG2020/WG2004 `n=7`, `k=0`, MITC shear, and positive `2x2` quadrature;
- 14 stress/resultant and 21 independent-strain parameters;
- three perturbed-Lagrange multiplier parameters;
- `gamma_PL=G`, `epsilon_hg=10^-3`, and thickness `t=2/3`;
- centre-linear drill constraint with only the faulty `r*s` coefficient
  deleted;
- frame-dependent `T5`, `QD`, physical/drill projectors, `range(T5)` loads,
  and no direct drill moments; and
- the six registered rational geometries, their eight D4 numberings, and the
  `R_star/b_star` transform of the tapered-skew geometry.

The exact registered order is:

```text
Q0_SQUARE
Q1_AFFINE_SKEW
Q2_TRAPEZOID
Q3_TAPERED_SKEW
Q4_HOSTILE_ASYMMETRIC_1
Q5_HOSTILE_ASYMMETRIC_2
Q3_TAPERED_SKEW_RSTAR_TRANSLATED

E, R90, R180, R270, MR, MS, MD, MA
```

This yields 56 numbered cases, 224 ordered Gauss-point records, and 56 centre
records. Base patch, rigid, load, and support objects are constructed once in
the `E` source frame and transported node-only. They are never re-evaluated
as numerically identical local polynomials after renumbering.

### Actual 35-field Hu-Washizu core

The implementations use the inherited exact orders and operators, not a Gram
or identity-block surrogate. With centre-Jacobian source transforms, and with
`j0/j` applied only to the seven membrane enhancement modes,

```text
N_sigma:   8 x 14
N_epsilon: 8 x 21
B:         8 x 20
```

and

\[
F=-\int N_\epsilon^T N_\sigma\,dA,\qquad
H=\int N_\epsilon^T C N_\epsilon\,dA,\qquad
G_q=\int N_\sigma^T B\,dA.
\]

The actual stationary matrices are

\[
D_{35}=\begin{bmatrix}0&F^T\\F&H\end{bmatrix},\qquad
Q=\begin{bmatrix}G_q^T&0\end{bmatrix},\qquad
K_5=-QD_{35}^{-1}Q^T.
\]

The compatible fields use the frozen membrane, curvature, and MITC shear
operators. The independent strain and resultant fields are reconstructed at
every corresponding Gauss point from `N_epsilon` and `N_sigma`; raw local
parameter vectors are not recovery evidence.

### Exact PL and residual construction

For

\[
c=\theta_D-\tfrac12(v_{,x}-u_{,y}),
\]

freeze the analytically differentiated centre Taylor rows

\[
C=\begin{bmatrix}c(0,0)\\c_{,r}(0,0)\\c_{,s}(0,0)\end{bmatrix},
\qquad M=\int_A tP^TP\,dA,\quad P=[1,r,s],\quad B_{PL}=MC.
\]

A Gauss-point `L2` projection of the full rational curl is forbidden. The
uncondensed PL block is `-M/G`, its coupling is `B_PL`, and eliminating the
multiplier gives `G B_PL^T M^-1 B_PL`. The full local internal order is
stress-14, strain-21, multiplier-3.

The geometry-dependent residual row and its force/tangent are the exact
WT2011/Q1R construction. Numerical PL and residual quantities remain separate
from physical `N/M/Q`, stress, yield, fatigue, and code-check recovery.

### Numbering and global transport

For every frozen D4 action, with `delta=det(A_g)`, prove the equation-7 frame
theorem, Gauss correspondence, and exact work-conjugate maps:

\[
e_0=C_{eng}(A_g)e_g,\quad N_0=C_{res}(A_g)N_g,
\]
\[
k_0=\delta C_{eng}(A_g)k_g,\quad M_0=\delta C_{res}(A_g)M_g,
\]
\[
\gamma_0=\delta A_g\gamma_g,\quad Q_0=\delta A_gQ_g,
\]
\[
\lambda_0=\delta\operatorname{diag}(1,A_g)\lambda_g.
\]

Membrane, bending, shear, and PL work invariance is a separate exact gate.
Stiffness covariance cannot substitute for field reconstruction.

For the proper global transform, use the frozen

\[
G_R=I_4\otimes\operatorname{diag}(R_\star,R_\star)
\]

and prove all eight transformed numberings for the frame, `T5`, `QD`, both
projectors, stiffness, residual, load, supported solution, support reaction,
physical recovery, and separate numerical diagnostics. Translation by
`b_star` changes no translation-invariant quantity, and `P_g G_R=G_R P_g`.

### Recovery, support, and reactions

At all 224 stations reconstruct compatible strain, independent HW strain,
and independent `N/M/Q`; then reconstruct physical global tensors/vectors.
PL multiplier/constraint/compliance and residual-mode coordinate, energy,
residual, and tangent have separate numerical keys.

The unsupported element is used only for local rank and rigid-mode gates. The
sole supported solve is the frozen full physical zero projector probe:

\[
A_{bc}=T5^T,\qquad
\begin{bmatrix}K&A_{bc}^T\\A_{bc}&0\end{bmatrix}
\begin{bmatrix}q\\\mu\end{bmatrix}
=\begin{bmatrix}f\\0\end{bmatrix},\qquad f=T5p_f.
\]

Transport the identical boundary problem by
`A_bc^(g)=A_bc P_g^T` and `A_bc*=A_bc G_R^T`. Define the support reaction as
`r_support=A_bc^T mu`; require its solution, reaction, and virtual work to
transport exactly, and require `QD^T r_support=0` and
`Pi_D r_support=0`. Internal PL/hourglass drill residuals are not support
reactions, remain separate, and are not required to vanish.

### Exact rank, PSD, and equality calculus

Construct six analytical rigid columns `R` and prove exact rank six and
`K R=0`. Choose the quotient complement only from `R`, by the preregistered
lexicographic exact elimination; it may not depend on observed stiffness,
rank, or pivots. Certify the resulting 18-dimensional quotient by a fixed
outward LDL calculation. Report positive, negative, exact-zero, and unresolved
pivots. Eighteen positive directions alone do not prove PSD if any remainder
is negative or unresolved.

Structural covariance and mixed/condensed energy-work-residual-tangent
equalities pass only as algebraic exact zero. Dyadic intervals at 256, 512,
and 1024 bits may classify ordered positivity or certified nonzero values. A
nonzero-width band containing zero at 1024 bits is inconclusive; a certified
contradiction is the relevant NO-GO; unresolved required evidence is
UNCLASSIFIED. Float64 `1e-11` residuals are diagnostic only.

## Four immutable Git stages

The exhaustive allowlist contains 35 new paths and no existing-file change.
`.gitattributes` already supplies LF rules and is not modified.

### PLAN — 11 paths

```text
docs/agent_plans/S4_E4_PL_Q1S_IMPLEMENTATION_COMPLETION_PLAN.md
docs/reference_cases/e4_pl_q1s_plan_review.json
docs/reference_cases/e4_pl_q1s_baseline.json
docs/reference_cases/e4_pl_q1s_inheritance_manifest.json
docs/reference_cases/e4_pl_q1s_draft_preservation_manifest.json
docs/reference_cases/e4_pl_q1s_allowed_extent.json
docs/reference_cases/e4_pl_q1s_implementation_completeness.json
docs/reference_cases/e4_pl_q1s_authority_contract.json
docs/reference_cases/e4_pl_q1s_terminal_table.json
docs/reference_cases/e4_pl_q1s_test_inventory.json
tests/test_e4_pl_q1s_preregistration_authority.py
```

The plan review is canonical JSON with exact verdict
`ACCEPT_Q1S_PREREGISTRATION_NO_P0_P1`. Its `reviewed_inputs` must exactly bind
the path, raw byte count, and SHA-256 of the other ten PLAN paths; its
`reviewer_independence` must state that the reviewer authored only the review,
authored no reviewed input, and ran no mechanics. Before Commit 1, no implementation,
mechanics test, execution contract, output, agreement, observed mechanics
value, scientific terminal, or Q1B path may exist. Commit 1 has exact parent
the Q1R closeout, exact 11-path extent, and subject:

```text
docs: preregister E4 PL Q1S implementation completion
```

One plan-only correction and re-review is permitted.

### IMPLEMENTATION — 10 paths

```text
docs/reference_cases/e4_pl_q1s_reference.py
docs/reference_cases/e4_pl_q1s_oracle.py
docs/reference_cases/e4_pl_q1s_scientific_test_runner.py
docs/reference_cases/e4_pl_q1s_implementation_manifest.json
docs/reference_cases/e4_pl_q1s_implementation_review.json
tests/test_e4_pl_q1s_frame_and_fields.py
tests/test_e4_pl_q1s_local_algebra.py
tests/test_e4_pl_q1s_recovery.py
tests/test_e4_pl_q1s_global_supports.py
tests/test_e4_pl_q1s_terminal_and_agreement.py
```

The implementations are owned independently, share only committed JSON, do
not import one another or Q1A/Q1R mechanics, and remain standard-library
programs. Before freeze, only syntax, AST, schema, source-transcription, and
guard-negative tests may run. No registered case may assemble.

The new scientific runner performs its authority check before pytest
collection/import and invokes exactly these five nodes with no skip/xpass:

```text
tests/test_e4_pl_q1s_frame_and_fields.py::test_q1s_all_56_numbered_frames_and_field_work
tests/test_e4_pl_q1s_local_algebra.py::test_q1s_actual_38_field_condensation_rank_and_rigid_modes
tests/test_e4_pl_q1s_recovery.py::test_q1s_all_224_station_recovery_and_numerical_separation
tests/test_e4_pl_q1s_global_supports.py::test_q1s_global_transform_load_support_solution_and_reactions
tests/test_e4_pl_q1s_terminal_and_agreement.py::test_q1s_evidence_terminal_and_cross_implementation_contract
```

The implementation review is canonical JSON with exact verdict
`ACCEPT_Q1S_IMPLEMENTATION_FREEZE_NO_P0_P1`. One static correction and
re-review is permitted. Commit 2 has exact 10-path extent and subject:

```text
docs: freeze E4 PL Q1S independent implementations
```

After Commit 2, implementation and test sources are immutable.

### CONTRACT — exactly 3 paths

```text
docs/reference_cases/e4_pl_q1s_execution_contract.json
docs/reference_cases/e4_pl_q1s_contract_review.json
tests/test_e4_pl_q1s_contract.py
```

The caller-bound contract binds Commit 1 and Commit 2, all plan and
implementation hashes, runtime, five-node inventory, terminal table, common
payload schema, agreement schema, three runners, required exact review
verdicts, and output absences. It does not predict its own commit. The review
is canonical JSON with exact verdict
`ACCEPT_Q1S_EXECUTION_CONTRACT_NO_P0_P1`. One contract correction/re-review is
permitted. Commit 3 has exact three-path extent and subject:

```text
docs: authorize E4 PL Q1S scientific execution
```

No registered mechanics may run before Commit 3.

### External authority and registered execution

After Commit 3, the coordinator exclusively creates one canonical authority
record with mode `xb` in a caller-owned `tempfile.mkdtemp` directory outside
all Git worktrees. It contains no timestamp or outcome. It binds program IDs,
Commit-3 commit/tree, contract hash, plan/implementation/contract review
hashes, exact verdicts, and runner inventory. Every runner requires
`--authority-record PATH --authority-sha256 SHA256 --contract PATH
--contract-sha256 SHA256 --runner-id ID`; it rejects symlinks, path escape,
wrong or extra keys, wrong hashes, dirty tracked/index state, wrong HEAD/tree,
wrong exact three-path Commit-3 diff, unlisted runner/node, and outcome files
present in the Commit-3 tree.

Reference run 1/2 and oracle run 1/2 write to fresh paths in an external run
directory. Within-implementation raw bytes must match. The normalized
implementation-independent certificate payload bytes must match across
implementations. Implementation-specific interval traces remain outside that
payload. Only after these checks are one raw file per implementation,
agreement, and combined output promoted to the worktree. The guarded runner
then executes the exact five-node inventory once and records a canonical test
result. After the first registered process begins there are zero corrections
to implementation, tests, contract, tolerances, cases, or runners.

### OUTCOME — 11 paths

```text
docs/reference_cases/e4_pl_q1s_reference_raw.json
docs/reference_cases/e4_pl_q1s_oracle_raw.json
docs/reference_cases/e4_pl_q1s_agreement.json
docs/reference_cases/e4_pl_q1s_output.json
docs/reference_cases/e4_pl_q1s_status.json
docs/reference_cases/e4_pl_q1s_execution_authority.json
docs/reference_cases/e4_pl_q1s_scientific_test_result.json
docs/E4_PL_Q1S_LOCAL_QUALIFICATION.md
docs/reference_cases/e4_pl_q1s_scientific_review.json
docs/E4_PL_Q1S_COMPLETION.md
tests/test_e4_pl_q1s_closeout.py
```

The authority-record copy is byte-identical to the external record. The
scientific review is canonical JSON with exact verdict
`ACCEPT_Q1S_SCIENTIFIC_REVIEW_NO_P0_P1`. Commit 4 has exact 11-path extent and
subject:

```text
docs: close E4 PL Q1S local qualification
```

The closeout test is static after Commit 4 and validates all four ancestries,
canonical transport, the hash DAG, exact extent, terminal precedence, and the
production boundary. It never reruns mechanics.

### Preregistered blocked-closeout routes

Every authority terminal has a content-addressed exit even when the normal
four-commit chain cannot advance. No new path is added. Define:

```text
BLOCKED5 =
  docs/reference_cases/e4_pl_q1s_status.json
  docs/E4_PL_Q1S_LOCAL_QUALIFICATION.md
  docs/reference_cases/e4_pl_q1s_scientific_review.json
  docs/E4_PL_Q1S_COMPLETION.md
  tests/test_e4_pl_q1s_closeout.py

POST_AUTHORITY_BLOCKED6 =
  BLOCKED5
  + docs/reference_cases/e4_pl_q1s_execution_authority.json
```

The independent blocked-closeout review uses exact verdict
`ACCEPT_Q1S_BLOCKED_CLOSEOUT_NO_P0_P1` and accepts only terminal precedence,
evidence disposition, and repository boundary. It does not promote rejected
implementation or scientific evidence.

The alternative commits are exact:

- baseline, inheritance, plan-authority, or pre-execution frame-identity
  block: parent Q1R closeout; `PLAN11 union BLOCKED5` (16 paths); subject
  `docs: close E4 PL Q1S plan-authority block`;
- implementation-identity block: parent accepted Commit 1;
  `IMPLEMENTATION10 union BLOCKED5` (15 paths); subject
  `docs: close E4 PL Q1S implementation-identity block`;
- contract-authority block: parent accepted Commit 2;
  `CONTRACT3 union BLOCKED5` (8 paths); subject
  `docs: close E4 PL Q1S contract-authority block`;
- post-Commit-3 contract, nondeterminism, oracle, or review block:
  `POST_AUTHORITY_BLOCKED6`; subject
  `docs: close E4 PL Q1S evidence-or-review block`;
- scientific NO-GO, UNCLASSIFIED, or provisional GO: the full `OUTCOME11`
  with subject `docs: close E4 PL Q1S local qualification`.

In a blocked subset, unpromoted raw runs, agreement, combined output, and
scientific-test result remain outside Git and are recorded only as incident
hashes in status when relevant. No absent file is fabricated. The closeout
test validates the selected route against terminal precedence.

## Review and agent independence

The coordinator alone changes stages and creates commits/authority records.
Reference and oracle have separate owners. Each plan, implementation,
contract, and scientific reviewer is independent of that gate's authors and
executor; no reviewer self-approves. Reviewers write only their single review
record. The coordinator may use at most two implementation agents at once and
reviewers sequentially; no recursive spawning is allowed.

## Terminal precedence

First match wins:

```text
1  BLOCKED_E4_PL_Q1S_BASELINE_MISMATCH
2  BLOCKED_E4_PL_Q1S_INHERITANCE_MISMATCH
3  BLOCKED_E4_PL_Q1S_PLAN_AUTHORITY
4  BLOCKED_E4_PL_Q1S_FRAME_IDENTITY
5  NO_GO_E4_PL_Q1S_FRAME_IDENTITY
6  BLOCKED_E4_PL_Q1S_IMPLEMENTATION_IDENTITY
7  BLOCKED_E4_PL_Q1S_CONTRACT_OR_NONDETERMINISM
8  BLOCKED_E4_PL_Q1S_ORACLE_OR_REVIEW
9  NO_GO_E4_PL_Q1S_LOCAL_ALGEBRA
10 NO_GO_E4_PL_Q1S_PATCH_OR_COVARIANCE
11 UNCLASSIFIED_E4_PL_Q1S_LOCAL_PLANAR_IDENTITY
12 PROVISIONAL_GO_E4_PL_Q1S_Q1B_PLAN
```

Source/frame absence or ambiguity is blocked; an exact source-frame
contradiction is scientific NO-GO. Certified negative/extra local modes,
nonzero rigid action, internal singularity, or mixed/condensed contradiction
maps to local-algebra NO-GO. Certified field/work, patch, recovery, D4,
global-transform, load, support, KKT, reaction, or numerical-separation
contradiction maps to patch/covariance NO-GO. Unresolved required evidence at
1024 bits maps to UNCLASSIFIED. Authority, implementation, contract,
determinism, or review defects remain BLOCKED.

A provisional GO authorizes only later preparation of a separately reviewed
Q1B plan. It does not re-establish DNV material qualification and does not
authorize Q1B execution, assembled stability, locking, nonlinear mechanics,
dynamics, buckling, coupling, or production use.

Every terminal retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`; legacy
`ShellElement` remains the default.

The sole plan-only correction cycle was used before preregistration to add
row-bound inherited source commits, exact review-content binding, and these
blocked-closeout routes. Later plan corrections are forbidden; the permitted
implementation and contract correction cycles remain unused at Commit 1.

## Repository boundary

There are no changes to `.gitattributes`, `src/`, `.github/`, package metadata,
workflows, public APIs, selectors, serialization, exports, assembly/solver
dispatch, production recovery/tests, or defaults. No PDF or copyrighted page
is committed. No push, merge, publication, cleanup, historical rewrite, or
Q1B path is authorized.
