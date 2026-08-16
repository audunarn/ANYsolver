# S4 Stage-M Candidate-A source and discretization addendum

Status: plan-only source amendment and proof program. It grants no production
implementation, activation, integration, push, publication, or cleanup.

## 1. Authority and immutable history

This addendum is subordinate to:

- `docs/S4_FULL_PRODUCTION_QUALIFICATION_PROGRAM.md`, raw SHA-256
  `17CB914002E362A5DB2B475981A46020C1F39E8BA5398B4A7BEC64C39EEEC4A7`;
- `docs/S4_STAGE_M_MECHANICS_SELECTION_PLAN.md`, raw SHA-256
  `4AE07F5954C9A2E6E6B002BEA24A9FC274B528D405EE6E5FCACE630893021E5B`;
- Stage-M closeout commit
  `9fe7baf5cc14f60f4bf695018becb35635cfa881`, tree
  `722cc366f129486c87ae609d672e7880873cffff`.

The accepted unavailable-source manifest
`docs/reference_cases/s4_stage_m_source_manifest.json`, raw SHA-256
`22B7B9D56DCC180CEE29F43AD4F31C69547A7C74CB212FD5B7D301909A8C0BE6`,
is immutable historical input to the completed Candidate-B execution. It must
not be edited, renamed, or rebound. The Candidate-B output remains raw SHA-256
`3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D`
and terminal `NO_GO_CANDIDATE_B`; no precision shard is rerun.

User authority is held by this task. No PERF lease or external approval is
required. Independent agents remain read-only auditors.

## 2. Acquired source boundary

The user supplied a lawful local copy of D. D. Fox and J. C. Simo,
*A drill rotation formulation for geometrically exact shells*, Computer
Methods in Applied Mechanics and Engineering 98 (1992) 329-343, DOI
`10.1016/0045-7825(92)90002-2`.

The frozen PDF identity is:

- raw SHA-256
  `A2075C06EB551FB317E09DF37E9BEFB6B525754A945EAC894F58F204CAB2D7D8`;
- 1,137,295 bytes;
- 15 unencrypted pages, PDF 1.7;
- original local path
  `C:/Users/AudunArnesenNyhus/Downloads/A drill rotation formulation for geometrically exact shells.pdf`;
- byte-identical, untracked task copy
  `tmp/s4_stage_m_sources/A drill rotation formulation for geometrically exact shells.pdf`.

All 15 pages were rendered at 120 dpi with Poppler 26.05.0 to the untracked
`tmp/pdfs/fox_simo_primary_source/` directory and visually inspected. The PDF
and renders are evidence only, must remain untracked, and are not authorized
for redistribution or cleanup.

The source substantiates the continuous scalar tangent-plane constraint,
modified-gradient polar rotation, mixed scalar-multiplier functional, first
variation, weak operator, and second variation/tangent. It does not specify a
finite-dimensional multiplier interpolation, quadrature rule, discrete
inf-sup pair, topology assembly, or a rank-two Q4 constraint.

The regularized and eliminated forms in Eqs. (49)-(50) and (55)-(56) are
context only. They do not authorize a penalty, stabilization, `C^T C` energy,
or an empirical parameter.

## 3. Exact owned paths and ordering

Commit this addendum alone first. After independent acceptance, the
coordinator may add and commit only the acquired-source record:

- `docs/reference_cases/s4_stage_m_fox_simo_source_acquisition_amendment.json`.

After that manifest is independently accepted, the coordinator may add only:

- `docs/S4_STAGE_M_CANDIDATE_A_DISCRETIZATION_DERIVATION.md`;
- `docs/S4_STAGE_M_CANDIDATE_A_DISCRETIZATION_REPORT.md`;
- `docs/reference_cases/s4_stage_m_candidate_a_discretization_cases.json`;
- `docs/reference_cases/s4_stage_m_candidate_a_discretization_oracle.py`;
- `docs/reference_cases/s4_stage_m_candidate_a_discretization_output.json`;
- `docs/reference_cases/s4_stage_m_candidate_a_discretization_contract.json`;
- `tests/test_s4_stage_m_candidate_a_discretization.py`.

Every generated or executed input must be content-addressed and independently
accepted before the first scientific run. No existing source, proof, output,
test, selector, export, serialization, assembly, activity, nonlinear,
buckling, recovery, batch, workflow, sibling repository, worktree, or ref is
owned. Existing `tmp/`, `.s4_stage_m_*`, pytest, PDF, render, and shard residue
is preserved and excluded.

## 4. Source amendment result

The acquired-source manifest must distinguish literal statements from derived
results and freeze the exact article/PDF page map. It records:

- continuous source gate: `PASS_CONTINUOUS_CANDIDATE_A_SOURCE`;
- Candidate-A equation implementation: `false`;
- Candidate-A mechanics run: `false`;
- Candidate-A status:
  `BLOCKED_CANDIDATE_A_DISCRETIZATION_UNREGISTERED`;
- Candidate-B terminal: `NO_GO_CANDIDATE_B`;
- overall Stage-M status:
  `BLOCKED_CANDIDATE_A_DISCRETIZATION_UNREGISTERED`.

The small-rotation identity is a derived result, not a verbatim quotation. On
a flat orthonormal reference it is frozen as

```text
delta_c = u_1,2 - u_2,1 + 2 theta_3
        = 2 (theta_3 - omega_3),
omega_3 = (u_2,1 - u_1,2) / 2.
```

The source amendment cannot itself choose Q0, Q1, `{1,rs}`, `{r,s}`, a reduced
quadrature rule, or a topology-adaptive multiplier space.

It must also record that the source's extended configuration contains
`(phi,Q,lambda)` with `d=lambda Q t0`, whereas the current 24-coordinate Q4
uses a fixed scalar element thickness and has no independent `lambda` field.
The source does not authorize silently deleting that field, expanding the
production space, or treating the present nodal rotation interpolation as the
paper's continuum `SO(3)` field.

## 5. Pre-outcome discrete-pair classification

Before any Candidate-A equation edit or mechanics run, the derivation and
cases must first choose, from a pre-outcome physical derivation, either a
justified fixed-`lambda` specialization or an expanded `lambda_h` primal
space. An expanded primal space invalidates the current 24-coordinate rank
theorem and must stop for a separately registered governing amendment. A
fixed-`lambda` specialization must prove which source terms vanish or survive
and why its force, work, and tangent remain consistent.

Only after that primal-space checkpoint may the proof freeze a
source-independent, outcome-blind classification of the discrete constraint
pair. It must also freeze the finite-rotation `Q_h` interpolation/update,
positive-determinant polar branch, and relation between the paper's `Q` and
the program's candidate rotation field.

For the flat bilinear Q4 primal space, derive the linearized continuous
constraint exactly and materialize its `Q1 = span{1,r,s,rs}` coefficient map.
Classify every rank-two subspace admitted by this exact reference-cell
symmetry representation. In the ordered real coefficient basis
`b=[1,r,s,rs]`, use the coordinate generators

```text
R(r,s)=(-s,r),    S(r,s)=(r,-s),
(rho(g) f)(r,s)=f(g^-1(r,s)),
rho(R)=[[1,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,-1]],
rho(S)=diag(1,1,-1,-1),
M=diag(4,4/3,4/3,4/9).
```

Here `M_ij` is the exact unweighted `L2([-1,1]^2)` Gram matrix of `b`.
Enumerate rank-two projectors with exact algebra from

```text
P^2=P,  trace(P)=2,  P^T M=M P,
P rho(g)=rho(g) P for every g in D4.
```

The symbolic enumeration must prove exhaustiveness and must reproduce the two
invariant images `span{r,s}` and `span{1,rs}` before either is applied to a
mechanics operator. This enumeration is strictly `B`-blind. Only afterward
may the already frozen rank/rigid/energy theorem classify every enumerated
candidate using `B`. Do not choose or discard a space during enumeration
using the published-operator nullspace, Candidate-B output, desired G/Z
modes, a floating-point rank, or a downstream benchmark result.

At minimum, the cases and contract must bind:

- node, edge, orientation, director, and reference-coordinate conventions;
- the full D4 action on primal and multiplier coefficients;
- every symmetry-admissible rank-two subspace and its canonical projector;
- exact primary and sensitivity quadrature, measure, row scaling, and sign;
- affine/frame/origin/scale/cyclic/reversal covariance;
- element-to-global multiplier assembly for connected, disconnected,
  noncoplanar, warped, odd-cycle, supported, MPC, coupled, active, softened,
  hard-deleted, and orphaned topologies;
- exact support/MPC affine-feasibility separation;
- no penalty, stabilization, invented coefficient, or observed-result tuning.

If symmetry and invariance do not determine one admissible pair, all frozen
candidates are evaluated against the same matrix and the result remains
unselected unless a preregistered, physics-derived decision rule separates
them. Numerical convenience or targeting the known common-drill/checkerboard
modes is not a selection rule.

## 6. Mandatory exact and interval gates

Let `B` be the immutable published linear operator with `rank(B)=16`, `R` the
six-column rigid basis, `C` a candidate discrete constraint with `rank(C)=p`,
and `T` a full-column basis of `ker(C)`. Each candidate must establish, with
exact rational/radical algebra or outward interval certificates:

```text
rank(R) = 6,
B R = 0,
C R = 0,
rank(C) = 2,
rank(B T) = rank(B) = 16,
T ker(B T) = range(R),
rank([B; C]) = 18.
```

It must also establish a uniform discrete inf-sup lower bound under the frozen
mesh/refinement families, no loss of a positive-energy membrane, bending,
shear, or drill direction, exact force/work/energy and mass pullback, and
configuration-consistent nonlinear constraint/tangent objectivity. A
borderline, precision-sensitive, fixture-sensitive, or quadrature-sensitive
claim is `UNCLASSIFIED`, never a pass.

The oracle must run all registered candidates and all registered cases even
after a failure. No threshold, basis, quadrature, case, or classification may
change after the first scientific result.

## 7. Terminal calculus

- Invalid identity, grammar, source binding, or execution environment:
  `BLOCKED_INPUT_IDENTITY` or `BLOCKED_CONTRACT_VIOLATION`.
- An expanded `lambda_h` primal choice:
  `BLOCKED_CANDIDATE_A_EXPANDED_PRIMAL_AMENDMENT_REQUIRED`; no 24-coordinate
  theorem or pair run is allowed.
- A fixed-`lambda` specialization or `Q_h`/positive-polar mapping with a
  certified inconsistency: respectively
  `NO_GO_CANDIDATE_A_FIXED_LAMBDA_SPECIALIZATION` or
  `NO_GO_CANDIDATE_A_ROTATION_MAPPING`.
- A fixed-`lambda` specialization or `Q_h`/polar mapping with incomplete,
  borderline, or non-interval-closed evidence: respectively
  `UNCLASSIFIED_CANDIDATE_A_FIXED_LAMBDA_SPECIALIZATION` or
  `UNCLASSIFIED_CANDIDATE_A_ROTATION_MAPPING`.

Only a closed fixed-`lambda` and rotation checkpoint reaches pair
classification. Each preregistered pair then has exactly one categorical
result:

- `PROVEN_FAIL` if any mandatory exact or outward-interval gate proves a
  violation, including a late inf-sup, topology, objectivity, variational, or
  energy failure;
- `PASS` only if every mandatory gate closes;
- `UNCLASSIFIED` otherwise, including any missing, borderline,
  precision-sensitive, fixture-sensitive, or execution-error result.

Unless a source/physics-derived selector and its exact precedence were frozen
before the first run, aggregate the complete pair catalog as follows:

- every pair `PROVEN_FAIL`:
  `NO_GO_CANDIDATE_A_DISCRETE_PAIR`;
- exactly one pair `PASS` and every other pair `PROVEN_FAIL`:
  `GO_CANDIDATE_A_DISCRETE_PAIR`;
- every other mixture, including one `PASS` plus any `UNCLASSIFIED`, multiple
  `PASS`, or no `PASS` plus any `UNCLASSIFIED`:
  `UNCLASSIFIED_CANDIDATE_A_DISCRETE_PAIR`.

If a source/physics-derived selector is preregistered, the contract must state
before execution whether only its selected pair governs or whether the full
catalog aggregation above still governs. An outcome-derived selector is
forbidden.

A discrete-pair GO authorizes only a separately content-addressed Candidate-A
proof/implementation plan. It does not authorize production source edits,
selector exposure, integration, push, publication, or improved-S4 activation.
Candidate B remains a preserved NO_GO comparison and is never rerun here.

## 8. Verification and closeout

The source-manifest stage requires strict JSON parsing, raw identity checks,
PDF hash/size/page verification, all-page render inventory, exact equation map,
old-manifest/output immutability, `git diff --check`, exact staged-path checks,
and independent source/mechanics/scope acceptance.

The later discrete proof requires two deterministic independent executions,
canonical byte-identical output, the complete frozen case ledger, no skips or
xfails, and independent mechanics/matrix/seam closeout. Preserve all evidence.
There is no cleanup authority.
