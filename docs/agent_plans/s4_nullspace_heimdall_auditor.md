# Heimdall — independent S4 nullspace-semantics audit plan

## Role and base

Heimdall is a read-only independent auditor for the proof stage based at
`f5cf8d925f47c816f5fe4857a83c5e38fd599570` in
`C:\Github\ANYsolver\.perf2-worktrees\s4-nullspace-semantics`.
Heimdall owns no file and must not edit, stage, commit, integrate, or authorize
a production rank policy.

## Independent audit duties

After the coordinator announces a content-hash freeze, Heimdall must:

1. rederive `ker(B_w)`, inherited-scale `ker(H_w Q_N_B)`, `G`, and the
   positive-mass quotient projector `Pi_P=Pi_N_B-Pi_G` without trusting
   Vidar's helper functions. Independently establish `R_N=R intersect N_B`
   with the symmetric augmented-basis primitive, form
   `Y_R=Pi_P Q_R_N`, verify
   `rank(Y_R)=dim(R_N)-dim(R_N intersect G)`, and audit
   `Pi_RQ=projector(range(Y_R))` and `Pi_Z=Pi_P-Pi_RQ`. Reject raw
   `R intersect P` and `Pi_P Pi_R Pi_P`. Use the frozen `S_q`, positive B/H
   row weights, and dimensionless registered metric;
2. independently check the exact `64*max(m,n)*eps64*sigma_max` SVD threshold,
   `(0.25,1,4)` sensitivity band, empty/zero conventions, preregistered
   inherited parent scale for every derived restriction, projector-derived
   basis procedure, the exact `4096*d*eps64` residual tolerance and frozen
   dimension/norm/zero-denominator/trace rules, residuals at every sensitivity
   multiplier without multiplying that residual tolerance, same-manifest
   repeated output hashes, and different-manifest
   numerical-only comparison semantics;
3. byte-audit the exact `.17g` JSON tokens, signed-zero normalization,
   symmetrized-projector/C-order little-endian `<f8` snapshot bytes, fixed v2
   SHA header, and sorted compact UTF-8/LF JSON procedure; independently
   reconstruct every exact environment-manifest field, recursive config
   filtering, six pre-import one-thread controls, NumPy RECORD hash, manifest
   runtime CPU dispatch, Python executable and NumPy/NumPy-libs binary inventory
   hashes, case-insensitive explicit numeric-runtime override rejection,
   complete recognized-prefix numeric-environment serialization, warm-loaded
   one-thread threadpoolctl BLAS backend/architecture/library binding,
   serialization/hash, and digest binding; require exact snapshot equality only
   for identical manifest digests and use residuals—not digests—across runtimes;
4. verify local element cases and analytic constant/checkerboard candidates;
5. independently assemble representative topology matrices from JSON and
   confirm connected/disconnected, bipartite/non-bipartite, orientation,
   activity/deletion results, including the frozen retained-node-universe
   deletion order and separately reported orphan-coordinate intersections;
6. verify supports, dependent/weighted affine MPCs, and abstract coupling
   matrices using independent rank/projector calculations; require RHS /
   homogeneous tangent separation and check `G_C` plus constrained
   `L_C=N_C intersect (R_N+G)`, `Pi_P_C`, `Pi_RQ_C`, and `Pi_Z_C` without
   conflating feasibility or local rank. Require the quotient-image rank to
   equal `dim(L_C)-dim(L_C intersect G_C)` and reject raw constrained rigid
   intersections;
7. independently inspect the hash-verified synthetic package loader and reject
   execution of real ANYsolver initializers or loading of sibling ANY modules;
   independently reproduce each accepted module hash from raw bytes by rejecting
   a UTF-8 BOM, strict UTF-8 decoding, CRLF-to-LF replacement, remaining-CR
   rejection, UTF-8/no-BOM re-encoding, and SHA-256; treat the recorded Windows
   raw-byte hashes only as checkout observations; verify the exact case-folded
   six-name allowlist, all-`anysolver.*` preflight/no-overwrite rule, and failure
   rollback to the exact pre-load module key order and object identities;
8. reject any conflation of true gauge, the positive-mass quotient, analytic
   rigid mode, non-rigid positive-mass mechanism, constrained rank, or local
   rank;
9. reject physical-production claims that are unsupported by derivation;
10. inspect exact path scope, imports, source/contract hashes, exclusions, and
   absence of penalty/stabilization/magic correction;
11. run only focused lightweight commands and remove guarded audit temporaries.
12. independently reproduce the two-dimensional quotient counterexample, the
    unit-square Rz/gauge coset and corrected `P=7,RQ=6,Z=1` split, augmented
    intersection commutativity/containment, and the preregistered
    `diag(1,delta)@[0,1]^T` restriction family for
    `delta in {0,2^-60,2^-40,1}` with ranks `(0,0,1,1)` at all three
    multipliers.

## Verdict standard

Return `ACCEPT` only if every numerical claim is reproducible, every theorem
is correctly scoped, every physical interpretation is labelled, and the
packet selects/applies no option. Findings must identify P0 scientific or
governance defects separately from P1 durability/completeness gaps. Any
positive-mass checkerboard vector described as mere gauge is an automatic P0
rejection.
