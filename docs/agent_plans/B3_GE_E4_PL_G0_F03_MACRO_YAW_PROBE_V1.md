# G0 F03 registered two-cell yaw moment candidate v1

21 September 2026. This is a bounded **falsification** of a genuinely
different local multiplier span, not a production law or F03/G0B pass.
Source `scripts/probe_b3_ge_e4_pl_g0_f03_macro_yaw_v1.py` plus its eight
named helper scripts must be committed and independently reviewed before
one execution. Exclusive raw root:
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-macro-yaw-v1/`.
Record actual hashes, imported ANYsolver path, dependencies, one BLAS
thread, separate writable Numba cache and the 1,200-row dense KKT cap.

The ten Q4/S3 planar cases are the previous trace-dual inventory:
`(Nb,Ns)=(4,4),(8,8),(16,16),(8,1),(8,64)` for each shell.
Native beam half-cell count is even. Compare the new space with K4 in
each case, under the same smooth and signed sine fixed continuum load.
All displacement/gap quantities use the same frozen reference shell
trace and native retained beam, rather than a changed element law.

Keep K4's native-grid translation tests. For each two-cell macro interval
centered at `s_c`, let the native half-cell length be `h=1/Nb` and use
two yaw tests, zero outside: `psi_0=1` and
`psi_1=2(s-s_c)/h`. Both are integrated on the fixed shell/beam overlay,
with exact work `integral psi_i(s) c_yaw(s) ds` and multipliers. A pair
of native cellwise-constant yaw traces has local test pairing
`h [[1,1],[-1,1]]`, full rank, and yaw mass
`diag(2h,8h/3)`. Four- and two-point Gauss rules on each split interval
should agree within `1e-11` relative; the analytic pairing/mass within
`2e-14` absolute. This local construction has the **same row count** as
K4, not an extra penalty or automatic removal of a constraint.

Use a non-equilibrium scaled trial field and a nonzero macro yaw multiplier
field to compare direct `integral lambda_yaw(s) c_yaw(s) ds` against
`lambda_yaw^T C_yaw q`, with relative discrepancy at most `1e-11`.
The source must fail the case when either quadrature discrepancy or this
work discrepancy exceeds its registered threshold.

This is more than invertible reweighting of K4 on the whole physical
trace. For a shell yaw `A+B(s-s_c)`, the difference of adjacent P0 yaw
rows is `B h²`, whereas `psi_1` produces `(4/3)B h²`. On a native
cellwise-constant yaw image, both row pairs span the same image. Verify
the actual assembled candidate has full row rank and full native-image
rank, and that the stacked `[C_K4; C_macro]` rank exceeds K4 by at least
one on every registered mesh; otherwise this proposed distinctness fails
and no physical improvement may be attributed to a new span. Record row
incidence and exact mass/force work. A clean finite assembly still does
not establish mesh-local inf-sup or uniform rank.

For each load, compare actual shell energy, nine native/shell station
motions and gap, support force/moment, weak residual, and full-versus-
condensed signed solution parity with K4 on the same mesh. The first
adverse checks are Q4/S3 `Nb=8,Ns=1` under both loads for locking and
`Nb=8,Ns=64` for persistent pointwise gaps. Treat the nine-station
maximum as a lower bound, never a certified continuous maximum. Recompute
both spaces' positive constraint floor and full signed KKT floor with
the earlier restricted broken-trace dual; check the three joint levels
and both fixed-beam reaches. A higher positive floor or a smaller gap in
one case alone cannot select this mortar.

The source must preserve all ten rows and typed numerical failures, with
no retry under the same evidence identity. Candidate selection remains
blocked by independent converged physical response, a mesh-local
trace/dual norm, all physical mesh ratios, eccentric six-channel work,
torque/drilling/shear, material/lifecycle and external comparisons.
Both loads for both spaces must solve; any typed numerical failure is a
failed case and nonzero run exit, with the failed record retained. Record
applied and support wrenches and maximum free residual with each result.
