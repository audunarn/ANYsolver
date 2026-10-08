# G0 F03 trace-image dual norm probe v1: registered exploratory screen

21 September 2026. This registration precedes execution. It does not
select a mortar space, accept F03/G0B, or qualify a product route.

## Exact question and finite model

For the ten planar Q4/S3-V2D cases registered in
`probe_b3_ge_e4_pl_g0_f03_signed_norm_v1.py` (joint native-beam/shell
counts 4/4, 8/8, 16/16 and fixed native count eight with shell counts
one and 64), compare the existing K4 and local-discontinuous-dual row
spaces in the **dual of the discrete broken physical gap trace**.

The source is `scripts/probe_b3_ge_e4_pl_g0_f03_trace_dual_v1.py` and
its seven named helper scripts. The bounded native fixture and shell
trace have fixed supports, E=210 GPa, thickness .07 m, attachment
length 1 m, force-density scale 1 MN/m, and yaw-to-position length .46 m.
The source hashes, imported ANYsolver path and dependency versions are
recorded in the run manifest. One BLAS thread and at most 1,200 dense
KKT rows are allowed. The exclusive output root is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-trace-dual-v1/`.
NUMBA_CACHE_DIR is a separate writable cache, not part of numerical
evidence. Do not overwrite or append to the run root after execution.

Let `S_q` be the existing physical coordinate scales, `u0` their
displacement scale, and `G` the graph of the position/yaw-converted
gap's L2 and slope terms, plus native retained-yaw jumps, integrated on
the exact reference overlay. In scaled coordinates,
`G_s=S_q G S_q/u0²`. For each candidate constraint matrix `C`, let
`C_s=C S_q/(u0 L0)`. With eigenpairs of `G_s`, construct
`R_lambda=C_s G_s^+ C_s^T` on the trace image. This is a **global,
mesh-dependent discrete diagnostic**, not a local production multiplier
mass or a proof of norm equivalence. Reject the primary result if C_s
does not annihilate discarded graph modes to relative Frobenius 1e-8 or
if R_lambda is not positive definite to relative eigenvalue 1e-10.
Do not silently remove constraint rows.

The primary pseudoinverse drops graph eigenvalues at relative 1e-12.
Also report 1e-10 and 1e-8 cutoffs, each with rank, kernel-annihilation
residual and extreme dual Gram eigenvalues. Recompute the positive
constraint, signed-Schur, and full signed-KKT floors for each admissible
cutoff; mark a variant inadmissible if the kernel or dual-rank check fails.
An eigenvalue cutoff on the graph corresponds to a square-root cutoff
on its trace factor. Strong cutoff sensitivity invalidates any robust
interpretation of a floor. The relative Frobenius kernel check is a
finite numerical diagnostic, not a rowwise or uniform proof.

Retain the signed native block exactly. In the scaled p/r factorization,
`K=T^T diag(K_e,K_rr) T`, use the positive primal metric
`H=T^T diag(K_e,abs(K_rr)) T`, with no made-up positive K_rr. Transform
the constraints through that factorization, then whiten them with
`R_lambda^(-1/2)`; report both the positive constraint singular floor
and the minimum singular value of the full signed, normalized KKT.
The signed Schur eigenvalues are additional diagnostics. A non-descent
of either floor over three mesh levels is not by itself proof of
uniform stability, and an L2 row mass is not substituted for this dual.

## Decision and preservation

An invalid graph, non-annihilated kernel, deficient dual Gram, indefinite
physical `K_e`, near-zero native `K_rr`, nonfinite factorization or
resource-limit failure is a recorded exploratory failure, not a passing
case. Preserve every case row and raw output. The one-time execution is
reviewed independently before and after running, and its source must be
committed before execution. Do not change the source to rescue a consumed
run; a genuine correction receives a versioned registration and root.

Even all ten finite results cannot accept F03. Selection still needs a
derived mesh-local norm and uniform evidence, mode and physical work
checks, independently converged eccentric response, and six-channel
pose/torque verification under the parent G0 contract. The earlier
local-dual physical-response failure remains adverse evidence.
