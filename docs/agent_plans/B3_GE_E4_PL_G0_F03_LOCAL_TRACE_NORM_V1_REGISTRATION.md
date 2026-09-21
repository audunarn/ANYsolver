# F03 mesh-local broken trace norm: bounded diagnostic registration

21 September 2026. Status: **registered for exploratory execution only**.
F03/G0B are open. Freeze the script and runner before executing the
exclusive evidence run; the adjudication must name their committed hashes.
Do not treat a finite positive floor as a uniform stability proof or as a
physical line-law selection.

This diagnostic addresses a specific missing prerequisite in
`B3_GE_E4_PL_G0_F03_NEXT_REFERENCE_CONTRACT.md`. On each actual beam/shell
overlay interval, represent the three scaled physical gap channels by
independent one-sided endpoint values. The yaw channel is multiplied by
the fixed physical length `ELL=.46 m`. With interval length `h` and
reference length `L0=1 m`, assemble the exact local affine-field Riesz
form `h/(6L0)*[[2,1],[1,2]] + L0/h*[[1,-1],[-1,1]]` per channel.
At every native beam-cell boundary, add `L0/h_b` times the *yaw* jump
square. This defines a sparse positive definite `R` on an ambient broken
endpoint space. The one-sided physical trace map is `E` and each K4 or
local-dual test integrates against endpoint interpolation to form `F`.
Check `C=F E` and `G=Eᵀ R E` against the independently existing
assemblies. The mesh-local **norm definition and Riesz assembly** do not
make `R⁻¹` sparse; compute the test dual `A=F R⁻¹ Fᵀ` by sparse solves.

For bounded verification, compare against the earlier physical-image
dual `B=C G⁺ Cᵀ` using the existing explicit dense oracle and
`1e-12`, `1e-10`, and `1e-8` relative graph eigenvalue cutoffs, with
`1e-10` the primary reporting value. Record the retained eigenvalue gap,
rank, kernel action, and generalized ratios for each cutoff. Normalize
both consistently with the fixed physical scales. Check `0≼B≼A` and the generalized
eigenvalues of `(A,B)`. A large/growing maximum `A/B` shows that
ambient trace modes are not a uniform proxy for the physically reachable
trace image. Report a positive-norm coupling floor, signed Schur minimum,
and full signed KKT minimum separately. The signed native retained block
is preserved; its negative modes are not averaged or removed.

Inventory: Q4 and S3-V2D; joint `Nb/Ns=4/4,8/8,16/16`, plus crossed
`8/1,8/64`, ten cases total. Pre-execution smoke ran Q4 4/4 and S3
8/8 to check source mechanics and exposed maximum ambient/image ratios
about `124` and `674`, respectively. Those smoke values are disclosed
up front, are not gate results, and prevent interpreting a larger
ambient floor as improved physical stability.

Registered numerical checks: scaled `C=FE` and `G=EᵀRE` residuals
`≤1e-10`; affine midpoint residual `≤1e-10`; all `Nb−1` native jumps;
constraint action on dropped graph modes `≤1e-8` at all three cutoffs;
full-rank test dual with a minimum/maximum eigenvalue ratio above `1e-10`;
and lower eigenvalue of `A−B ≥−1e-9 λmax(A)` within roundoff.
Record the minimum/maximum generalized `A/B` and signed measures
without passing a uniformity claim from ten finite cases. Consecutive
joint-doubling increases above `2×` in `max(A/B)` are an explicit adverse
screen, not a criterion that passing would qualify F03. Any material
cutoff sensitivity leaves the comparison unresolved. The historical
fixed-side reaches are separate from an asymptotic proof.

The one-time runner uses an exclusive evidence root, serial child cases,
one BLAS/Numba thread, sampled child RSS limit 24 GiB, 1,800 s per case,
7,200 s total, 0.5 s sampling, source hashes, a revision and import path,
per-case stdout/stderr, and flushed JSONL records. Sampled RSS is not a
hard peak or process-tree memory limit. Preserve failures and incomplete
runs; do not reuse or overwrite the root. Before execution require a
read-only independent mechanics review of this definition, source, and
case inventory. Afterwards verify source hashes, all records, numerical
checks and resource outcomes independently.

Success here would establish only a bounded, reproducible local-norm
diagnostic. F03 still needs an independently converged physically matched
loaded response, a justified uniform trace/image comparison or different
norm, six-channel torque/shear connection checks, and a derived line test
span that passes physical response and stability across the full ratios.
No G1 product integration follows from this diagnostic alone.
