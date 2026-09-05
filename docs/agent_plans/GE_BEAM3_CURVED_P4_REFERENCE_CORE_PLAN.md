# GE Beam3 curved P4 reference-core authority gate

## Purpose and boundary

P4 begins from the accepted straight standalone GE-B3 closeout at commit
`7aa359c18d1cf5db3dfb84d364afd9870e2da994`, followed only by the
checkout-neutral closeout-test correction at
`8ac156cbb7632f2442f904e3ab73d6a7eb867670`. The accepted straight candidate
remains `CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2`, its qualified formulation
remains `GE_BEAM3_DC_MIXED_K1_MACRO_V2`, and its exact public selector remains
`ge-beam3`.

This P4 tranche is deliberately smaller than a curved-beam mechanics tranche.
It freezes and tests only the authority, reference curve, material reference
frame, intrinsic strain, objectivity, and reversal maps needed by a later
curved mixed candidate. It reserves the private candidate identity
`CANDIDATE_GE_BEAM3_DC_MIXED_CURVED_Q2_MACRO_V1` and the future formulation
identity `GE_BEAM3_DC_MIXED_CURVED_Q2_MACRO_V1`; the latter is reserved, not
issued, and this tranche creates no public selector.

The study ID is
`study_ge_beam3.curved_mixed_q2_reference_core_v1`. The exact preregistration
commit subject is `docs: preregister GE Beam3 curved P4 reference core`.

The following accepted straight files are immutable in P4:

- `src/anysolver/ge_beam3_mixed_element.py`
- `src/anysolver/ge_beam3_mixed_state.py`
- `src/anysolver/ge_beam3_element.py`
- `src/anysolver/ge_beam3_state.py`

P4 may initially add only research authority, cases, schemas, an independently
checkable reference-geometry implementation, tests, and canonical evidence.
It must not change B2, B3, Q4, S3, any existing alias or default, package
metadata, version, dependency, workflow, factory, solver, state transaction,
load, mass, recovery, modal, buckling, or joint behavior.

## Authority discipline

The source ledger uses three classes:

- `P`: an equation printed in a hash-bound public primary source;
- `D`: an independent repository derivation that must be reviewed and tested;
- `B`: background that cannot define an indispensable candidate equation.

Humer--Steinbrecher--Pechstein supplies the printed mixed-beam and
reference-relative rotation framework. It does not print this repository's
three-external-node, two-half-cell quadratic-reference packaging, exact
regularity test, shortest-transport-plus-residual-roll material-frame
interpolation, reversal map, or state layout. Those items are class `D`.
Meier--Wall--Popp, Jelenić--Crisfield, the original
attached plan, and the older curved compatibility plan remain class `B`.
The Jelenić--Crisfield PDF has not been locally artifact-hashed and therefore
cannot be promoted from background in this tranche.

Two equation maps must be hash-bound before reference-core implementation.
Map A traces source statements into the proposed reference construction. Map B
reconstructs the same obligations from interpolation, frame covariance, and
work-conjugacy invariants. Independent review must establish that their common
claims agree and that no background-only statement fills a derivation gap.

## Reference curve

Use node order `[END_1, MID_VERTEX_2, END_3]` at natural coordinates
`[-1, 0, 1]` and the quadratic Lagrange curve

\[
r_0(\xi)=N_1X_1+N_2X_2+N_3X_3,
\quad
N_1=\tfrac12\xi(\xi-1),\quad
N_2=1-\xi^2,\quad
N_3=\tfrac12\xi(\xi+1).
\]

Its derivative is the affine vector

\[
d_0(\xi)=r_{0,\xi}=a+b\xi,
\quad
a=\tfrac12(X_3-X_1),\quad b=X_1-2X_2+X_3.
\]

Let `Lscale` be the maximum of the three pairwise nodal distances. Require
finite distinct geometry, positive `Lscale`, and

\[
\min_{[-1,1]}\|a+b\xi\|/L_{scale}>
\max(64\epsilon_{binary64},10^{-14}).
\]

Evaluate this minimum analytically at both endpoints and, when `b·b>0`, at
the clamped stationary point `-a·b/(b·b)`. Sampling alone is forbidden.
Define `J0=||d0||`, `t0=d0/J0`, and `d/ds0=J0^-1 d/dxi`.

A single quadratic curve through three points is planar even when embedded in
three dimensions. General spatial curvature is represented by a compatible
piecewise-quadratic chain, not by falsely describing one element as a helical
arc. Adjacent elements must share the same authoritative nodal material frame.

## Authoritative material reference frame

P4 accepts explicit proper nodal triads only. Each `R0_i` must be finite,
right-handed, orthonormal, and have first column aligned, to the registered
binary64 invariant tolerance, with `t0(xi_i)`. No global-axis heuristic,
Frenet frame, or automatic anisotropic roll inference is allowed.

Freeze reference-frame policy
`PIECEWISE_SHORTEST_TRANSPORT_LINEAR_ROLL_V1_INDEPENDENT_DERIVATION`. Construct its
rotation-minimizing base independently on each half interval `[-1,0]` and
`[0,1]`. Starting from the left nodal triad, transport its first axis to the
station tangent with the unique shortest proper rotation

\[
P(p,q)=I+\widehat{p\times q}
       +\widehat{p\times q}^{,2}/(1+p\cdot q).
\]

Determine the residual signed roll needed to reach the right nodal triad and
interpolate that roll linearly in the half-cell natural coordinate. The two
half constructions must reproduce all three authoritative nodal triads and
meet exactly at node 2. Require the tangent turn and the residual roll on each
half to remain strictly below `0.9*pi`; otherwise return a typed
refinement/frame diagnostic. The restriction is local, so deep arches and
rings are represented by multiple admitted elements.

The construction must provide analytic first derivatives needed for

\[
\kappa_0=\operatorname{axl}(R_0^T R_{0,s_0}).
\]

Numerical differentiation is permitted only in an independent diagnostic
checker and may not define canonical values.

Closed loops require explicit compatible seam frames (or a separately frozen
holonomy policy) at the mesh level. P4 does not silently distribute closure
twist.

## Required identities

At the reference state `r=r0` and `Q=R0`, the future curved strain definitions
must give exact zero:

\[
\gamma=Q^T r_{,s_0}-R_0^T r_{0,s_0}=0,
\qquad
\kappa=\operatorname{axl}(Q^TQ_{,s_0})-\kappa_0=0.
\]

The reference-core gate checks only these kinematic identities; it does not
authorize a curved discrete potential, residual, tangent, condensation, or
section update.

For a common rigid transformation `X_i'=G X_i+c` and `R0_i'=G R0_i`, require
`r0'=G r0+c`, `R0'=G R0`, invariant `J0`, and invariant material components of
`kappa0`.

Connectivity reversal uses `1<->3`, node 2 fixed, `xi_rev=-xi`, and
`S=diag(-1,1,-1)`. The reversed nodal frames are `R0_rev_i=R0_perm_i S`, which
reverses the tangent while preserving the physical second material direction.
Require

\[
r_{0,rev}(\xi)=r_0(-\xi),\quad
R_{0,rev}(\xi)=R_0(-\xi)S,\quad
J_{0,rev}(\xi)=J_0(-\xi),\quad
\kappa_{0,rev}(\xi)=(-S)\kappa_0(-\xi).
\]

The exact-midpoint collinear, common-triad case must reduce to the P3 straight
reference curve and constant frame without changing or re-entering the P3
implementation.

Freeze `max(64*epsilon_binary64,1e-14)` for the scale-normalized reference
regularity gate, `1e-11` for normalized SO(3), tangent, objectivity, reversal,
and zero-reference-strain invariants, and `1e-12` for independently
reconstructed frame agreement. These are reference-core tolerances only and do
not authorize or alter a mechanics tolerance.

## Fatal reference-core gate

Preregister straight-limit, shallow/deep planar arc, asymmetric planar curve,
translated/rotated/scaled copies, initially twisted curve, two-element spatial
chain, reversal, near-fold rejection, tangent-cutoff rejection, roll-cutoff
rejection, and explicit ring-seam mismatch cases. Mutation tests must cover
every node, triad, interpolation coefficient, tangent sign, roll sign, half
ordering, reversal map, source hash, and bound artifact hash.

An independently authored checker must reconstruct the quadratic interpolation,
analytic regularity minimum, proper-frame conditions, station frames,
reference curvature, objectivity,
reversal, continuity, zero intrinsic strains, and straight limit without
importing the production reference module or accepted straight mechanics.

Run smoke cases before a formal wave. Run two fresh-directory deterministic
reference-core cycles only after the frozen candidate passes rehearsal, and
require byte-identical canonical scientific aggregates. Each child uses one
numerical-library thread, at most 24 GiB, and at most 600 seconds; at most three
children run concurrently and a whole wave is capped at 1,800 seconds. Use a
frozen inactivity threshold no longer than 300 seconds, terminate the complete
process tree on a resource or inactivity breach, preserve partial logs outside
canonical evidence, retry nothing automatically, and never reuse an authority
request.

Terminal precedence is:

1. `BLOCKED_GE_BEAM3_P4_BASELINE_OR_AUTHORITY`
2. `BLOCKED_GE_BEAM3_P4_REFERENCE_PROCESS_OR_EVIDENCE`
3. `NO_GO_GE_BEAM3_P4_REFERENCE_REGULARITY`
4. `NO_GO_GE_BEAM3_P4_REFERENCE_FRAME_IDENTITY`
5. `NO_GO_GE_BEAM3_P4_REFERENCE_REVERSAL_OR_OBJECTIVITY`
6. `PROVISIONAL_GO_GE_BEAM3_P4_PRIVATE_CURVED_REFERENCE_CORE`

The successful terminal authorizes only a separately frozen private curved
mixed-mechanics tranche. It does not authorize curved energy, residual,
tangent, sections, loads, mass, recovery, modal, buckling, dynamics, public
selection, ecosystem exposure, beam-shell coupling, default activation,
versioning, tagging, publication, or any change to accepted straight GE-B3,
B2/B3, Q4, or S3 behavior.
