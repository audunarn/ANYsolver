# F03-K2L: native-image and shell-compatibility rank diagnosis

21 September 2026. **Preexecution design, not a registered result or F03
acceptance.** K2P's exact KKT has small weak residuals yet almost vanishing
Q4 shell response for P1-beam at `N_b=8,N_s=1`. Determine whether the
constraint rows force independent shell compatibility conditions that the
native beam variables cannot satisfy on their own. Do not infer physical
locking from rank alone; K2P's measured response remains separate evidence.

Use the same native retained B3 and physical Q4/S3-V2D shell fixture,
reference geometry, supports, integration partitions and 26 K1 meshes.
Compare P1-beam, P1-shell-grid and P0-shell-grid. The third space is a
lower-dimensional alternative identified by K1, not a selected law.
This is a **load-independent**, three-channel planar algebraic experiment.

For every assembled `C=[C_s C_b C_r]` (free shell, native physical beam,
native retained beam), construct the exact K0 coordinate scales `D_q`,
multiplier mass `M`, and whitened dimensionless map
`A=L_M^{-1} C D_q/(u*√L0)` with `L_M L_Mᵀ=M`,
`u*=f0L0/(Et)` and `L0=1 m`. The map before final division has units
`m^(3/2)` in the registered metre convention. Partition into `A_s`, `A_b` and
`A_r`. Use one frozen relative singular cutoff `τ=1e-10 σ_max(A)` for
all partitions of that same candidate. Report the complete singular
spectra and ranks of `A`, `[A_b A_r]` and `A_b` separately. The difference

```text
d_shell = rank(A) − rank([A_b A_r])
```

is the number of independent assembled shell restrictions left after
the native beam image is quotiented out, at this declared cutoff. Also
project `A_s` onto a left-null basis of `[A_b A_r]`, and verify its rank
and nonzero singular spectrum agree with `d_shell`. Report the projected
map, numerical range/null reconstruction and projector orthogonality
residuals, not just a scalar count. These check the SVD decomposition,
not the physical law. Mark a candidate **ambiguous** if any relevant
singular value lies within a factor ten of the cutoff, a discarded native
singular value exceeds `0.1τ`, projected rank differs from `d_shell`,
or numerical null/range reconstruction exceeds `1e-10`. Check mass
symmetry, definiteness and conditioning, reference/assembly quadrature,
coordinate scales and whitened-map finiteness. Preserve invalid candidates
with typed disposition. A fully dimensionally transformed m↔mm case,
including `ℓ`, `L0`, `u*` and all native scales, remains a **separate
uncompleted requirement** before any quantitative stability claim.
K2L records SI dimensionless singular spectra as a diagnostic and tests
rank sensitivity; it does not claim unit-independent stability. Do not remove rows,
regularize Krr, or substitute a dense production assembly.

Preregister the source/dependency graph, unchanged fixture and K1/K2P
evidence identities, exact mesh/candidate inventory, one-thread environment,
resources and single-use output path. A supervisor independently checks
26 ordered mesh records, 78 candidate rows, dimensions, rank identities,
finite spectra, process exit, raw/registration hashes and resource limits.
Independent pre- and postexecution reviews must inspect coordinate units,
whitening, singular threshold, rank sensitivity and connection to K2P's
observed work/trace responses. No repeated run consumes the same authority.

Even if a rank deficit explains the coarse P1-beam response, neither
`d_shell=0` nor full row rank proves a stable mortar interface. K2 still
requires a justified mesh-independent dual norm, full retained saddle
stability and independent resolved physical convergence. The six-channel
eccentric shell/beam attachment and all G0B/G1–G6 obligations remain open.
