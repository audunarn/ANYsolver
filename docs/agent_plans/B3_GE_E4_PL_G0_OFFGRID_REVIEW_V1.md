# Independent F03-P-v4 off-grid evidence review

Reviewed read-only on 21 September 2026 at integration HEAD
`d831fd889cf06db8641a3751150224bf81d77c5d`. This review covers the
bounded, preparatory shell-only screen registered in
`B3_GE_E4_PL_G0_REGISTRATION.md`; it is not a full F03 or G0B acceptance.
No runner was executed during this review.

## Reviewed identities

| Input | SHA-256 |
| --- | --- |
| `scripts/probe_b3_ge_e4_pl_g0_physical_line_offgrid.py` | `01ecd1804ba2e5b555fb06a0c12d2e82fb73e1aad06bf04f7981bd351cac9fa9` |
| `scripts/probe_b3_ge_e4_pl_g0_physical_line.py` | `ea36eb4450b854382f3888510aa819cf46332290a68bc19d43620f8e0443f88c` |
| `src/anysolver/_ge_beam3_variational_shell.py` | `958cbf00f62e8af87724f909b793fa24391e02e3a0a2a5d5d62f05e9f1168320` |
| `src/anysolver/_ge_beam3_mixed_ad.py` | `c71cea89056ccb671d37d3169085844b7012e7fa8b7d78545dfc45fadaec105b` |
| `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f03-physical-line-offgrid-v1.log` | `db9bde0fc43e913263a732202dd399722fc6673ec7cb4906e500d44e2780d2f1` |

All five hashes were recomputed and matched the registered/handoff values.
The provided handoff reports Python exit code 0. The log itself is one JSON
output line (61,645 bytes), without a launcher, exit-code, or observed
environment record; the exit and actual execution settings cannot be
independently established from that artifact. Preserve this log and bind an
existing separate launch/exit record if available. Otherwise label those
facts as reported rather than independently evidenced.

## Evidence and disposition

The JSON reports exactly six cases: Q4 and S3-V2D at `n=4,8,16`. Each row
contains the complete applied-load, displacement and support-reaction vectors
of lengths 50, 162 or 578 as appropriate, plus compliance, twice the strain
energy, matrix `nnz`, unique host count and diagonal split count. All vectors
are finite; prescribed outer displacements and interior support reactions are
zero. Recomputed vector force sums, moments and `f.u` agree with the recorded
scalars to rounding precision.

The reference gradient difference is zero and its unit reference moment is
`-1`. Across the six rows, midpoint-versus-four-point-Gauss relative
load-vector error is at most `4.005e-16`; applied force norm at most
`2.453e-16`; applied moment is `-0.8` and support moment `+0.8` within the
registered `1e-8` limits. Support force balance is at most `9.115e-16`,
**absolute** free-equilibrium residual at most `1.584e-15`, and relative
work error at most `3.583e-16`. Compliance is finite and positive in
`[2.729e-11, 3.713e-11]`. S3 cases report 8, 12 and 26 diagonal splits.
Thus all registered numerical predicates pass for this exact shell-only
screen. The analytic gradient sign and S3 `xi=eta` split agree with the
imported host-weight convention. Work equality and support balance use the
same assembled stiffness and solved displacement and are algebraic checks,
not independent constitutive or line-multiplier oracles.

**Disposition: F03-P-v4 preparatory off-grid diagnostic PASS on the recorded
source and six results. F03 and G0B remain OPEN.** The result establishes
neither a multiplier-space choice nor torque/shear transfer, full constrained
system mechanics, mixed external validation, or product qualification.
