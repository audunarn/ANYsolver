# F03 Nm128 supported energy/dual-norm stability preflight

22 September 2026. **Design before implementation and execution
registration.** This is a bounded classical planar diagnostic, not a
native B3-GE/E4-PL inf-sup proof or loaded physical-reference result.
The existing Nm128 admission patch `b39d6c1a` changes only private
diagnostic limits. Its 88 focused tests and beam-only row-Gram check
do not establish mechanical stability.

## Inventory and fixed normalization

Use exactly four cases on the same physical geometry, offsets, support
mask and P1 line: Q4 and CST-CB at `(Ns,Ny,Nb)=(128,64,512)` with Nm64
and Nm128. Assemble each actual supported shell+beam stiffness `Kff`
and full coupling `Cf=[−Cs,Cb]` from the same reference maps as the
loaded comparator. The P1 multiplier row counts are 195 and 387;
physical free coordinates remain 36,223, giving KKT dimensions 36,418
and 36,610. Verify all four offset hosts, beam/mortar ratio 8:1 and
4:1, and exact-rational as well as floating segmented overlays.

Let the existing fixed scales be `L0=1 m`, `F0=10^6 N`,
`U0=F0/(E t)`, `E0=F0 U0`, with rotational coordinates scaled by
`U0/L0`; `D` is the coordinate scale already used for the classical
KKT. The coupling matrix includes the same physical yaw length
`Lc=.46 m`. Form dimensionless operators

```
Kbar = D Kff D / E0
B    = Cf D / U0
S    = B Kbar^{-1} B^T.
```

`Kbar` is the supported elastic energy norm. For the multiplier norm,
assemble exact one-dimensional P1 mass `M` and derivative `H` on
`[0,1]` independently of the coupling quadrature. Solve
`H V = M V diag(mu)` with `V^T M V=I`; use
`R = M V diag((1+mu)^(-1/2)) V^T M`, repeated in the three
interleaved physical force/moment-length channels. `R` is the frozen
discrete H-minus-one-half dual norm with reference length `L0`;
record its eigenvalue range and normalization checks. Report the
generalized eigenvalues of `S x = lambda R x`, including
`beta_min=sqrt(lambda_min)`, `beta_max`, their ratio and both
Nm128/Nm64 changes. Also show an L2 mass-norm screen as a clearly
separate sensitivity, if feasible; it is not a substitute acceptance
norm.

## Numerical route and terminal checks

Keep global matrices sparse. Factor only the supported `Kbar` with the
existing general sparse-direct backend. Form `S` in bounded batches of
constraint right-hand sides. Dense operations are limited to the
at-most-387-dimensional interface Schur and P1 norm matrices; no
global dense matrix, inverse, nullspace or SVD is admitted. Check the
original `Kbar` symmetry and the supported energy operator; do not
silently symmetrize an inconsistent stiffness. Confirm supported
near-zero modes using a sparse inverse-action probe and record its
numerical limits. Neither the near-zero probe nor LU factorization
certifies positive definiteness: negative modes farther from zero
remain possible. A separately validated smallest-algebraic or inertia
check is required before calling the Schur values an inf-sup measure
in a positive energy norm.

Before source freeze, test the small assembled route against an
independent dense oracle and analytic P1 mass/derivative entries, and
verify that changing displacement units while preserving physical
scales leaves the dimensionless result unchanged. The four-case
registration must bind the exact source/dependency/thread identities,
input mesh and section definitions, row and matrix counts, backend,
norm construction, raw output files and a read-only adjudicator. Use
one-thread serial runs, no competing benchmark, 8 GiB RSS and 900 s
per case. The supervisor requires that reviewed registration before
launch and checks its source, command and resource identities. Its RSS
limit is enforced by 0.1-second sampling, not by a hard OS memory cap.
Preserve a failed or incomplete root without retry or
replacement.

Predeclare numerical gates: relative stiffness and Schur skew at most
`1e-10`; maximum norm-scaled factor solve residual at most `1e-9`;
generalized eigen residual at most `1e-8`; finite positive dual norm
and smallest Schur eigenvalue greater than both `1e-10` times its
largest eigenvalue and a heuristic residual screening margin. This
margin is not a bound on forward eigenvalue error and does not certify
positivity for an ill-conditioned stiffness. Verify
full rows with a separate norm-scaled sparse/bounded-local rank check.
Backend failure, negative/uncertain supported energy or generalized
minimum, exceeded resources, changed identity or a failed residual
stops the diagnostic before any loaded Nm128 solve.

A finite positive result with only the near-zero probe is a provisional
mesh-specific diagnostic, not certified positive-energy stability.
The beam-only Euclidean row-normalized singular ratios observed in an
unregistered prototype, about `.35` at Nm64 and `.15` at Nm128 for
both hosts, motivate this preflight but are not an acceptance floor.
An independently justified **physical** lower bound and refinement
trend criterion are still absent. Do not promote a multiplier policy
or launch the registered loaded extension merely because these
algebraic checks pass. Interpret the finite beta trend with independent
mechanics review; if no defensible floor/trend can be frozen, retain
`STABILITY_ADMISSION_UNRESOLVED` and revise F03 rather than relaxing
the evidence requirement.
