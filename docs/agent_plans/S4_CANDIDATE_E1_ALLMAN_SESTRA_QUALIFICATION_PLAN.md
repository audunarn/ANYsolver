# Candidate E1 Allman and Sestra-pattern qualification plan

## Authority and separation

This proof-only successor starts from Candidate E0 commit
`87b639499187736c59d87bc4aa8e6bd7f819d28b`, whose parent is the immutable
production-qualification baseline `a9b45ca95303bc4b30b893fbb0d7177f9c98db03`.
It preserves E0 and every accepted A, B, C, and rank-four terminal.

Two mechanically and terminally independent candidates are registered:

* `candidate_e1.wg2020_n7_k0_independent_allman_q4_static_v1` (E1-A); and
* `candidate_e1.sestra_pattern_planar_gauge_regularizer_v1` (E1-R).

E1-R may not repair, alter, or be assembled with E1-A in this program.  A
combined formulation would require a new pre-outcome residual, rank, mass, and
recovery plan.  No production source, public API, serialization, selector,
export, dispatch, or default is owned here.

## E1-A necessary screen

The physical core is the Wagner-Gruttmann 2020 Hu-Washizu element with
`n=7`, `k=0`, and its 2 by 2 surface rule.  The independent all-node lift uses
exactly the four standard serendipity midside edge functions.  No interior
bubble is admitted.  On every consistently oriented edge `(i,j)`, the
two-node Hermite/Allman midpoint normalization is `L/8` times
`theta_D_j-theta_D_i`.  This is the complete minimal ansatz; an interior
coefficient or an outcome-selected scale is forbidden.

Before any stiffness or benchmark run, exact arithmetic must establish the
edge coefficient uniqueness, D4 and numbering covariance, vertex traces,
rigid invariance, and drill-column rank.  The 20-coordinate core contains six
rigid modes and therefore has rank at most 14.  The four drill columns factor
through the cyclic edge incidence matrix and have rank at most three, so the 24-coordinate rank is at
most 17 and E1-A stops with `NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY`.  No later
mechanics, DNV response, or buckling stage may run after that exact failure.

E1-A is not Sestra FQAS and is not represented as a reproduction of the
unavailable 1992 element.  If it survived the necessary screen, every
stiffness, consistent mass, load, recovery, geometric stiffness, and tangent
would have to follow from one enriched displacement/strain potential with no
independent drill inertia or stabilization.

## E1-R exact fallback

E1-R is a separately named numerical regularizer for an explicitly declared
planar component whose coplanarity and consistent orientation are proved
exactly.  It is eligible only when the host physical shell has zero drill
stiffness/coupling, transfers no applied drill moment, and does not already
contain another drill regularizer.

For a Q4, let `K_theta_theta^mat` be the 12 by 12 rotational block of the
condensed pre-regularizer physical material tangent in the component frame:

```text
Dmean = trace(K_theta_theta^mat)/12
cK    = 10^-8 Dmean
RK    = (4 cK/3) (I4 - 1 1^T/4).
```

Geometric stiffness, constraints, supports, MPCs, prior artificial terms, and
E1-R itself are excluded from `Dmean`.  `RK` acts only on rotations projected
onto the common component normal.  It must be symmetric positive semidefinite,
rank three for `Dmean>0`, have zero row sums, preserve constant drill exactly,
and be invariant under global-frame changes and normal reversal.

For each active connected planar component define nodal area weights
`w_i=sum_(e incident to i) A_e/4` and gauge functional
`sum_i w_i (theta_i dot n_C)=0`.  Components are rebuilt after deletion.  For
supports and MPCs, exact rank of their action on the complete component-gauge
basis determines the surviving gauge subspace.  Cross-component drill MPCs
that cannot be reduced without ambiguity fail closed.  Add only a basis for
the surviving gauges; never duplicate an already removed gauge.

The mass analogue is conditional:

```text
Mmean = trace(M_theta_theta^phys)/12
cM    = 10^-12 Mmean
RM    = (4 cM/3) (I4 - 1 1^T/4).
```

It may be applied only after an exact host audit proves a relative-drill mass
singularity.  A host already carrying positive drill rotary inertia is
ineligible.  E1-R produces no physical stress, resultant, yielding, fatigue,
recovery, load, or geometric stiffness, and no modal/transient claim is made.

## Evidence and terminals

The source registry binds the two local Sestra manuals by raw identity and
page map, but no copyrighted page, figure, screenshot, or copied passage is
committed.  The attached Candidate-E proposal is retained as superseded design
input; `k_D=sqrt(det(A_s0))` and `j_D=rho_A ell^2` are excluded.

The packet uses canonical UTF-8/LF JSON and standard-library exact oracles.
Each candidate has separate cases, contract, output, and terminal.  Both
oracles run twice in fresh processes and must emit byte-identical output.

The accepted pre-E1 matrix is verified in two tiers.  Its exact 94 ordered
nodes run only in an isolated checkout of E0 commit
`87b639499187736c59d87bc4aa8e6bd7f819d28b` and tree
`c01fd5cab7b63325e6cb5b70000f4586d4788563`, using the coordinator's
content-addressed pinned dependency roots.  E0's closeout tests deliberately
reject successor paths and therefore are never weakened or represented as a
live E1-branch suite.  The active E1 branch runs only the new E1 focused and
closeout tests, which revalidate every immutable E0 artifact and production
source identity.  Results from the two tiers are reported separately; their
counts are never added into a fictitious single-worktree pass.

Identity errors block before science.  A certified E1-A rank failure is
`NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY`.  E1-R passes only its limited fallback
scope as `PROVISIONAL_GO_CANDIDATE_E1_R_PLANAR_REGULARIZER_ONLY`; it cannot be
reported as a rank-18 physical element.  Missing evidence is `UNCLASSIFIED`
for the corresponding candidate.  Every outcome retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` and legacy `ShellElement` as default.
