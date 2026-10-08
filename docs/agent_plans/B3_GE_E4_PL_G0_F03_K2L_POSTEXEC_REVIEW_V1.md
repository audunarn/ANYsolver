# Independent F03-K2L v1 postexecution audit

21 September 2026. Read-only independent review of the immutable
K2L v1 registration, raw inventory and supervisor attestation. The
reviewer did not modify files or rerun the consumed executor.

Sixteen direct registration, raw, log, source and predecessor identity
checks matched, including clean source commit
`6acd349daa69054bdbfb4b1ea5a7304fb46523aa`. The raw inventory
has 28 records, 26 ordered meshes and 78 ordered candidate rows, all
typed `RANK_DECOMPOSITION_CONSISTENT_NOT_F03_ACCEPTANCE`. The terminal
counts match; child exit 0, elapsed 113.97 s, sampled peak RSS
255,545,344 bytes, no external violation or read/supervisor error.
Stdout is empty. Stderr contains only Git-ignore permission warnings.

Each of the 78 stored full whitened singular spectra, multiplied back
by `u*√L0`, matches the independently retained K1 row singular spectrum
with maximum relative error `4.88e-15`. Re-SVD of all 78 serialized
projected shell maps reproduces their recorded spectra, with zero
rank/status/cutoff discrepancies and no near-cutoff flags. Maximum
native-null and shell-reconstruction residuals are `5.38e-16` and
`1.69e-15`. The native-only spectra cannot be independently reconstructed
from serialized K2L output without reassembling the original `C`;
their rank/cutoff identities and ambiguity flags were checked. This is
a stated limit of the independent audit, not an implied independent
assembly oracle.

The `d_shell` counts agree between Q4 and S3-V2D: P1-beam gives three
on every mesh; P1-shell-grid gives zero at `N_s/N_b<=.5`, three at 1,
15/27/51 for the ratio-2 three levels, 75 at ratio 4 and 171 at 8.
P0-shell-grid gives zero through ratio 1, then 12/24/48, 72 and 168.
At `N_b=8,N_s=1`, the three P1-beam restrictions act on only six free
shell coordinates and coincide with K2P's Q4 smooth shell energy
`2.65755e-34 J` (S3 `0.230 J`); P1-shell-grid has no remaining
shell restriction there and Q4 energy `14.515 J`. At the 8:1 reach,
P1-beam still gives three but Q4 shell energy is `12.079 J`.
P1-shell-grid gives 171 and energy `5.542 J`, with a smaller K2P
pointwise gap `0.00563` versus `0.06361` for P1-beam, but its raw
scaled KKT ratio is `6.19e-11`.

An additional independent read-only trace check establishes the exact
coarse Q4 mechanism. For `N_b=8,N_s=1`, let `P` be K2L's projected
shell map, `N` an orthonormal basis of its nullspace, and
`G(s)=diag(1,1,ℓ) T_shell(s)` in the dimensionless shell coordinate
`z_s=q_s/u*`. The reviewer recomputed `||G(.5)N||₂=1.144e-15`
(relative `2.27e-15`) for Q4, and values of order `1e-15` at
`s=0,.25,.5,.75,1`. S3-V2D instead has midpoint norm `0.170733`
(relative `.33587`); Q4/S3 at `N_s=2` have midpoint norms
`.339434/.370233`. Thus the shared `d_shell=3` count does not by
itself imply a vanishing trace.

For the Q4 `N_s=1` tensor trace, write the weighted free-node
displacements on either side of the sampled footprint as
`a=.46 u_lower+.54 u_middle` and
`b=.54 u_middle+.46 u_upper`. With
`h±(s)=1−|s±.2−.5|`, `m=h−+h+`, `d=h+−h−`, the fitted centroid is
`m(a+b)/4` and yaw is
`[.2d(a_y+b_y)+.23m(a_x−b_x)]/[4(.2²+.23²)]`.
The three independent projected rows impose
`a_x+b_x=a_y+b_y=a_x−b_x=0`. Consequently the fitted shell trace
vanishes **for every station**, not merely at the midpoint. Since the
shell has no direct load and its supported stiffness is SPD,
testing shell equilibrium with its own displacement gives
`q_sᵀK_s q_s=−λᵀC_s q_s=0`, hence `q_s=0` in exact arithmetic for
this linearized fixture. K2P's same case has symmetric physical Schur
(`skew_ke=7.38e-18`) and positive minimum/maximum eigen ratio
`1.7183e-5`; its uncoupled physical matrix contains supported `K_s`
as a principal block. K2P's tiny Q4 shell energy is the numerical
counterpart. This is a discrete algebraic explanation, not a continuum
locking theorem or full eccentric shell connection qualification.

**Adjudication:** K2L is complete as a bounded algebraic diagnosis.
The projected rows explain the **specific** coarse Q4 zero-shell-motion
result. The counts alone do not establish a locking conclusion across
meshes. Native signed saddle stability, independent
physical convergence and six-channel attachment remain unresolved.
No candidate is selected; F03/G0B stay open.
