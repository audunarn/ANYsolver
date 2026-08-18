# E4-PL-Q1R numbered-frame preregistration and local qualification

## Authority and purpose

Q1R starts exactly from blocked-closeout commit
`ad90068a7ee78c3390dfe1b651f28be035094f41`, tree
`e4cbb750ade5f2a160525e12b4c47afc5733a36a`, on branch
`codex/s4-e4-pl-q1r-numbered-frame`. The user-supplied plan is bound only as
background design input: 27,001 bytes, SHA-256
`3D8FE3ACF79B7C78B4B1D22E1DF40792B04603BAF88C99A390A0B499A97D27CA`.

The plan-only identity is
`study_e4_pl_q1r.wg2020_numbered_frame_transport_v1`. The caller-bound dormant
qualification identity is
`candidate_e4_pl_q1r.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1`.
It is `DORMANT_UNQUALIFIED`, is not a production registration, and may at most
authorize later preparation of a Q1B plan.

Q1A ended at `BLOCKED_E4_PL_Q1A_PLAN_AUTHORITY`. Its mechanics, D4 counts, and
agreement digest are nonclassifying history and cannot determine Q1R equations,
expected outcomes, tolerances, or terminals.

## Frozen formulation and transport

The physical element is unchanged from E4-0: WG2020/WG2004 Hu-Washizu Q4,
`n=7`, `k=0`, source MITC shear, 35 core variables, three PL multipliers,
positive unshifted 2x2 quadrature, `gamma_PL=G`, `epsilon_hg=1/1000`, and only
the faulty `r*s` PL coefficient deleted. External coordinates are node-major
`[UX,UY,UZ,RX,RY,RZ]`. Physical loads lie in `range(T5)`; direct drill moments
and drill support rows are excluded.

For each frozen D4 map, `xi_base=A_g*xi_new`, node `I` receives base node
`p_g(I)`, and `delta=det(A_g)`. Reconstruct the WG2020 equation-7 frame after
every renumbering and prove before mechanics

```text
T(X_g) = T(X_0) * diag(A_g,delta).
```

`MD=(1,4,3,2)` is the named complete orientation reversal; there is no ninth
action. The global 24-coordinate map permutes nodes only. Local fields use:

```text
epsilon_0 = A_g epsilon_g A_g^T       N_0 = A_g N_g A_g^T
kappa_0   = delta A_g kappa_g A_g^T  M_0 = delta A_g M_g A_g^T
gamma_0   = delta A_g gamma_g        Q_0 = delta A_g Q_g
lambda_0  = delta diag(1,A_g) lambda_g
```

Strain and curvature use engineering order `[11,22,2*12]`; conjugate
resultants use `[11,22,12]`. The frame contract also freezes Gauss-point
correspondence, `T5`, `QD`, physical/drill projectors, support/load transport,
PL work, multiplier compliance, numerical/physical reaction separation, and
proper global-frame covariance with `G_R=I4 tensor diag(R,R)`.

Use `t=2/3` for thickness and reserve `h_e` for mesh size. The only material is

```text
E=15, nu=1/4, G=6, k_s=5/6,
A=(32/3,8/3,4), D=(32/81,8/81,4/27), As=(10/3) I.
```

The centre and all four Gauss stations must have positive Jacobian.

## Frozen cases and classification

Apply all eight D4 operations to the four primary geometries and the two Q1A
hostile geometries listed in the canonical cases file. Apply the fixed rational
proper rotation and translation to the tapered-skew case. No case may be
replaced after preregistration and no Q1A expected result is imported.

Patch fields are frozen in source-local `(x,y)` coordinates:

```text
membrane: u=2x+y/3, v=-2x/5+4y/3, theta_D=-11/30
bending:  kappa=(2/5,-1/3,3/7)
shear:    gamma=(2/3,-1/4), theta_x=1/4, theta_y=2/3, w=0
combined: exact sum of membrane, bending, and shear
```

Six analytical rigid fields include the matched nonzero drill rotation for
in-plane rigid spin. Analytical patch drill values are allowed; applied drill
moments and drill support prescriptions are not.

Categorical covariance requires structural/algebraic exact zero. Independent
standard-library dyadic outward intervals use 256, 512, then 1024 bits, with
square-root endpoints built by integer square root and denominator `2^p`.
Rank 18 requires six explicit rigid null vectors plus a certified positive
18-dimensional minor or LDL certificate. An interval that cannot separate a
required quantity by 1024 bits yields `UNCLASSIFIED`; float64 `1e-11` checks are
corroborating only.

## Four-commit authority chain

1. **Preregistration.** Create only plan/frame/contracts/cases/governance files
   and the non-mechanics authority test. Obtain independent verdict
   `ACCEPT_Q1R_PREREGISTRATION_NO_P0_P1`, then commit
   `docs: preregister E4 PL Q1R numbered-frame qualification`. No Q1R
   reference, oracle, science test, contract, output, outcome, or Q1B plan may
   exist before this commit.
2. **Implementation freeze.** Independently implement reference and oracle
   from committed contracts without importing, inspecting, or running Q1A
   mechanics. Add five frozen scientific test groups and an implementation
   manifest. Before freeze, run syntax/AST/schema checks only. Obtain an
   implementation review, then commit
   `docs: freeze E4 PL Q1R independent implementations`.
3. **Execution authority.** Emit a caller-bound contract that binds commits 1
   and 2, both trees, all input/implementation/test hashes, runtime, inventory,
   agreement schema, and terminal calculus. Obtain a contract review and
   commit `docs: authorize E4 PL Q1R scientific execution`. No registered case
   may run before this commit.
4. **Closeout.** Run reference twice and oracle twice in fresh processes.
   Require within-implementation byte identity and byte-identical cross-
   implementation certificate payloads. Commit separate raw outputs, combined
   agreement/output, report, scientific review, status, completion, and
   closeout test as `docs: close E4 PL Q1R local qualification`.

Permit at most one plan-only correction/re-review before commit 1 and at most
one static transcription correction/re-review before commit 2. Once registered
execution starts, no source, test, contract, tolerance, or implementation may
change; a defect blocks this run and requires a new successor identity.

## Verification and repository boundary

Run the accepted E4 20-node tier only in a detached worktree at `97c3150...`.
Verify Q1A through its exact commits, four blocked-closeout hashes, verdict,
and absence of contract/output/Q1B; never rerun Q1A mechanics as qualification
evidence. Keep historical, preregistration, and scientific inventories
separate and never publish a combined suite count.

The exhaustive stage-tagged allowlist is frozen before commit 1. No
`.gitattributes`, `src/`, `.github/`, package, workflow, API, selector,
serialization, export, assembly/solver dispatch, recovery implementation,
production test, or default may change. The six historical untracked evidence
roots remain untouched. No push, merge, publication, cleanup, or historical
rewrite is authorized.

## Terminal precedence

```text
BLOCKED_E4_PL_Q1R_BASELINE_MISMATCH
BLOCKED_E4_PL_Q1R_PLAN_AUTHORITY
BLOCKED_E4_PL_Q1R_FRAME_IDENTITY
NO_GO_E4_PL_Q1R_FRAME_IDENTITY
BLOCKED_E4_PL_Q1R_IMPLEMENTATION_IDENTITY
BLOCKED_E4_PL_Q1R_CONTRACT_OR_NONDETERMINISM
BLOCKED_E4_PL_Q1R_ORACLE_OR_REVIEW
NO_GO_E4_PL_Q1R_LOCAL_ALGEBRA
NO_GO_E4_PL_Q1R_PATCH_OR_COVARIANCE
UNCLASSIFIED_E4_PL_Q1R_LOCAL_PLANAR_IDENTITY
PROVISIONAL_GO_E4_PL_Q1R_Q1B_PLAN
```

Every outcome retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`; legacy
`ShellElement` remains the production default. A provisional GO authorizes
only later preparation of a separately preregistered Q1B plan.
