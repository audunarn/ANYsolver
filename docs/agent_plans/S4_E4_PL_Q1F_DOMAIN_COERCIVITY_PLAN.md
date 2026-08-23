# E4-PL-Q1F: Domain-Coercivity Reduction and Bounded Proof

## Purpose

Q1F addresses the sole unresolved Q1E question: a domain-wide coercivity certificate for the dormant numbered-frame planar-linear E4 candidate. Q1E closed at `UNCLASSIFIED_E4_PL_Q1E_DOMAIN_COERCIVITY` because finite assembled samples do not establish a continuous-domain lower bound. Q1F therefore preregisters a mathematical reduction and a later, separately authorized bounded proof campaign. It does not repeat Q1B--Q1E mechanics and does not authorize production use.

Study: `study_e4_pl_q1f.q1e_domain_coercivity_reduction_v1`

Candidate: `candidate_e4_pl_q1f.wg2020_g1_domain_coercivity_v1`

Branch: `codex/s4-e4-pl-q1f-domain-coercivity`

Base authority: merge commit `61195c18a704438b4b3cf66e6e93d7839723b0fb`, tree `1249c9e9280d626c11c7194c1f2f5b164e5d99b7`, containing the exact accepted Q1E closeout commit `e47bade554b23cbac3272d9453162a42e7e082ee` and its seven-path evidence packet.

## Frozen reduction

Every admissible bilinear quadrilateral is represented, modulo translation, proper rotation, and positive scale, by

\[
x=r+p s+u r s,\qquad y=q s+v r s,
\]

with \(p\in[-4,4]\), \(q\in[1/4,4]\), and \(u,v\in[-2,2]\). The parent coordinates satisfy \((r,s)\in[-1,1]^2\). The full domain additionally requires positive Jacobian determinant everywhere, minimum-to-maximum singular-value ratio at least \(1/4\) everywhere, and centre-relative Jacobian variation

\[
\sup_{(r,s)\in[-1,1]^2}\|J(0,0)^{-1}(J(r,s)-J(0,0))\|_2\leq 1/2.
\]

The Q1R material and quadrature identity is immutable. For the actual condensed 24-field element tangent \(K_e\), the candidate-independent Reissner--Mindlin/drill norm matrix \(H_e\), and the analytical 24-by-6 rigid matrix \(R_e\), Q1F must establish exactly

\[
K_eR_e=H_eR_e=0,\quad \operatorname{rank}R_e=6,
\]

construct the 24-by-18 basis \(Z_e\) by deterministic leftmost-pivot RREF of \(R_e^T\), and certify

\[
Z_e^T(K_e-10^{-6}H_e)Z_e\succeq0
\]

over the complete admissible parameter domain. Floating samples, finite registered geometry families, fitted tolerances, and outcome-selected bases cannot classify this obligation.

## Local-to-global theorem

Because both forms annihilate the same local rigid space, each assembled restriction may be reduced independently by its deterministic local rigid decomposition. Summing the certified local inequalities gives

\[
q^TK_hq\geq10^{-6}q^TH_hq
\]

with no mesh-dependent constant. On an edge-connected conforming component, equality of two distinct shared-edge nodes propagates the six local rigid parameters; hence the assembled nullspace is exactly the six analytical rigid motions per connected component. Consistent counter-clockwise connectivity and byte-identical shared child-edge coordinates are mandatory hypotheses.

Exact uniform parent-space one-to-four refinement must preserve the admissible-domain predicates after each child is returned to the same gauge, and it must preserve the same lower bound. This preservation is a proof obligation, not an empirical refinement check.

## Authority chain

The four successful stages have the exact extents and subjects frozen in `e4_pl_q1f_allowed_extent.json`:

1. `PLAN8` -- `docs: preregister E4 PL Q1F domain coercivity`
2. `IMPLEMENTATION10` -- `docs: freeze E4 PL Q1F coercivity proof tooling`
3. `CONTRACT3` -- `docs: authorize E4 PL Q1F bounded domain proof`
4. `OUTCOME8` -- `docs: close E4 PL Q1F domain coercivity`

Commit 1 is accepted only by a later independent canonical plan review with verdict `ACCEPT_Q1F_COERCIVITY_REDUCTION_NO_P0_P1`. This authoring step intentionally does not create that review. No domain proof, mechanics evaluation, or scientific output may run before the execution contract and its independent review are accepted.

The bounded proof must use independent producer/checker responsibilities, exact or certified outward arithmetic, deterministic subdivision, complete leaf coverage, and reproducible canonical evidence. An uncovered admissible box is inconclusive, not a pass. A certified negative direction is a scientific no-go. An authority, identity, review, or determinism defect is blocked evidence rather than a mechanics classification.

## Terminal precedence

First match wins:

1. `BLOCKED_E4_PL_Q1F_AUTHORITY_OR_REVIEW`
2. `BLOCKED_E4_PL_Q1F_REDUCTION_IDENTITY`
3. `BLOCKED_E4_PL_Q1F_PROOF_OR_NONDETERMINISM`
4. `NO_GO_E4_PL_Q1F_DOMAIN_COERCIVITY`
5. `UNCLASSIFIED_E4_PL_Q1F_INTERVAL_COVERAGE`
6. `PROVISIONAL_GO_E4_PL_Q1F_Q1B_INTEGRATION_PLAN`

The provisional terminal authorizes only a separate reviewed Q1B integration plan. Every outcome retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`; legacy `ShellElement` remains the default. Q1F makes no change to `src/`, public APIs, packages, selectors, serialization, dispatch, recovery, workflows, dependencies, defaults, or `.gitattributes`.

## Sole preregistration correction

The initial packet did not bind an executable mechanics identity or fully specify the gauge, child maps, norm, and interval proof grammar. The sole permitted plan correction closes those gaps before review. No mechanics has been executed.

The neutral mechanics inventory is content-addressed to the unchanged Q1V reference and the accepted Q1Y3 checker, contract, and bounded result. Q1F implementations must independently reproduce the frozen shape, Jacobian, physical-gradient, corrected MITC tying, source-field, 35-core-plus-3-PL stationary assembly, Schur, PL, hourglass, rigid-field, and leftmost-RREF formula inventory. Only arithmetic backend and gauge-domain input may differ. Normalized-AST or formula equivalence must be established without importing one implementation into the other.

Node order is \((-1,-1),(1,-1),(1,1),(-1,1)\), and every node-major vector is ordered `[u,v,w,theta_r,theta_s,theta_n]`. The bilinear coefficient representation is

\[
F(r,s)=a_0+a_1r+a_2s+a_3rs.
\]

With \(e_1=a_1/|a_1|\), \(e_2\) its unique proper quarter-turn, and scale \(\ell=|a_1|>0\), the exact forward gauge is

\[
p={a_2\cdot e_1\over\ell},\quad q={\det(a_1,a_2)\over\ell^2},\quad
u={a_3\cdot e_1\over\ell},\quad v={\det(a_1,a_3)\over\ell^2}.
\]

The inverse nodes and the exact congruence identities for \(K,H,R\) are frozen in the reduction contract. Reflections are forbidden, and \(q>0\) selects the unique proper orientation.

For a uniform child with \(r=r_0+\rho/2\), \(s=s_0+\sigma/2\), \(r_0,s_0\in\{-1/2,1/2\}\), define

\[
A=a_1+s_0a_3,\quad B=a_2+r_0a_3,\quad C=a_3.
\]

Its regauged parameters are

\[
p'={A\cdot B\over A\cdot A},\quad q'={\det(A,B)\over A\cdot A},\quad
u'={A\cdot C\over2A\cdot A},\quad v'={\det(A,C)\over2A\cdot A}.
\]

The child-domain, positive-orientation, byte-identical shared-edge, centre-variation, and inherited-bound statements are all proof obligations.

The bounded proof grammar uses reduced rational endpoints `[numerator,denominator]`, three equal-width root bands in `p`, and exact interval records. Internal boxes split the widest normalized coordinate, with ties resolved lexicographically `p,q,u,v`. Every leaf is exactly `EXCLUDED`, `POSITIVE`, `NEGATIVE`, or `UNRESOLVED`. A partition DAG must cover each root with disjoint interiors and matching faces. Positive leaves require exact identities, positive-definite interval LDL for \(Z^THZ\), and positive-semidefinite interval LDL for \(Z^T(K-10^{-6}H)Z\). Two independent checker replicas must emit byte-identical canonical checks. Any disagreement blocks; an admissible negative witness is `NO_GO`; any unresolved required leaf is `UNCLASSIFIED`.
