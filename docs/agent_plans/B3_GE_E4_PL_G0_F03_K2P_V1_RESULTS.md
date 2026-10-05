# F03-K2P v1 fixed-load physical KKT diagnostic

21 September 2026. **Completed diagnostic, not F03/G0 acceptance.** This
records the immutable one-shot evidence rooted at
`C:\Github\ANYsolver\.qualification\b3-ge-e4-pl\f03-k2p-v1`.
The frozen source is `0e248a02363653fd9efa9c9ad9137d007a6dc66e` on
`codex/b3-ge-e4-pl-integration`; accepted main remains separate. The
registration, raw inventory, supervisor attestation and child logs remain at
the evidence root. The runner used source ANYsolver 0.4.7 from the isolated
checkout; installed distribution metadata is 0.4.6. This is a source-level
mechanics diagnostic, not an installed-package qualification.

## Inventory and numerical disposition

The supervisor attested exact completion: 28 JSONL records (start, 26
meshes, terminal), 52 candidate matrices and 104 load responses, exit 0,
no resource violation. Elapsed time was 94.94 s and sampled peak child RSS
350,711,808 bytes. The attestation's registration and raw SHA-256 values
match the files independently read for this report.

All 52 candidate matrices had two load results. Fifty-one candidate rows
were `TWO_LOAD_LOCAL_DIAGNOSTIC_NOT_F03_ACCEPTANCE`; one was
`TWO_LOAD_INVENTORY_WITH_PARITY_OPEN`. Among loads, 103 were local numerical
diagnostics and one was parity-open: Q4, eight beam half-cells, `N_s=64`,
P1-shell-grid, smooth load. Its normalized sparse/condensed
forward-solution difference was `1.097982078e-10`, exceeding the frozen
`1e-10` parity threshold. It remains open, despite small backward residuals.

The worst eight-versus-twelve-point reduced sine load difference was
`1.695e-15`; the worst full native smooth load difference was `1.631e-15`
under the registered work scales. The maximum scaled free equilibrium was
`1.411e-13`, weak residual `4.699e-14`, assembled constrained-work
quadrature discrepancy `2.050e-15`, force balance `3.132e-13` and moment
balance `2.599e-13`. These show numerical assembly and global balance for
the linearized cases, not physical interface convergence. The full scaled
KKT singular ratio ranged from `6.187e-11` to `1.138e-5`; its decline
with refinement must not be called uniform multiplier stability.

## Physical trends that remain unresolved

The largest normalized pointwise trace gap was `0.1267` for P1-beam and
`0.9164` for P1-shell-grid. At fixed eight beam half-cells, Q4 smooth load,
the shell-grid parameter `N_s` increasing from 32 to 64 gave (the panel
has `2N_s` physical x intervals over `[-0.5,1.5]`):

| Basis | Maximum gap / u* at 32 → 64 | Scaled KKT singular ratio at 32 → 64 |
|---|---:|---:|
| P1-beam | 0.0631 → 0.0636 | 2.19e-7 → 1.10e-7 |
| P1-shell-grid | 0.0102 → 0.00563 | 7.14e-10 → 6.19e-11 |

The S3-V2D analogue is 0.0538 → 0.0541 for P1-beam and 0.00955 →
0.00437 for P1-shell-grid. Thus a beam-grid basis may leave a pointwise
gap plateau under shell-only refinement, whereas the shell-grid basis can
reduce gaps while the raw scaled KKT system becomes increasingly ill
conditioned. At matching 1:1 beam/shell grids the two bases represent the
same trace space and give the same response; this is not independent
corroboration. The three-level displacement histories vary with mesh and
neither basis has an independent resolved physical reference in this study.

The independent review identified a stronger adverse case at the 1:8
ratio-reach end: Q4 `N_b=8,N_s=1`, P1-beam smooth and sine responses have
shell energy of only approximately `2.66e-34` and `1.61e-34 J`, with
near-zero shell station motion, while multiplier densities reach
approximately `3.71e7 N/m` and the supports carry the load. The S3-V2D
counterpart is similarly near-clamped. This is evidence of possible
overconstraint/locking despite full row rank and tiny equilibrium residual;
the reciprocal reach has only one mesh level, so its convergence cannot be
inferred. The reviewer also found decreasing conditional physical-only
Schur floors on all twelve three-level topology/ratio/space sequences.
These observations bar a space selection on the current metrics.

The K2P run did not calculate the conditional `H^-1/2` interface norm or
the full retained inf-sup constant. Its planar in-plane trace is not the
six-channel eccentric shell/beam law. Individual support-node reactions,
nonlinear objectivity, drilling/shear/torque transfer, plasticity and
coupled ownership remain outside this diagnostic. No multiplier space is
selected. G0B and F03 remain open; G1 through G6 do not advance from K2P.

## Next mechanics decision

Derive and freeze the trace and dual norms for the actual shell/beam
coordinate spaces, then compare the candidate multiplier spaces under a
uniform norm-scaled stability criterion with the exact retained block.
Separately establish a resolved physical reference and gap/response
convergence for fixed continuum loads. A candidate that passes only weak
equilibrium or only raw KKT nonsingularity cannot be promoted. Extend the
accepted foundational result to finite pose, eccentric torque and
transverse-shear preservation before production line coupling.

Independent postexecution adjudication found the source and evidence hashes,
all record counts, signed sine load and global balances consistent; it
identified the adverse 1:8 response and conditional Schur trends above.
The separate review record preserves its calculations and exact scope.
