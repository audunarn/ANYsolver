# F03-K2 independent norm and full-retained saddle review

21 September 2026. Read-only independent mechanics review of the K2
conditional multiplier norm proposal against the actual native retained B3
fixture and K2P evidence. No K2 qualification was executed.

The proposed Neumann spectral dual mass for the three metre-valued planar
gaps can be defined by `e0=1/√L0`,
`en=√(2/L0)cos(nπs/L0)`, `wn=(1+n²π²)^(-1/2)` and
`H_ij=Σn wn (∫φ_i en ds)(∫φ_j en ds)`, with
`H_full=H_scalar⊗I3` in basis-major channel ordering. Every multiplier
coefficient then has units N/m; the yaw physical couple density is
`ℓ λ_z` N. A dimensionless conditional inf-sup square has the stated
`(f0/u*)` factor only with the explicit bilinear work normalization
`b(q,λ)=λᵀCq/W0`, `W0=f0 u* L0`, symmetric SPD `K_e`, and
`C_u=C_lᵀ`. The finite spectral truncation can be bracketed by
`0≼H−H_N≼w_(N+1) M`, subject to analytic basis projections, a
verified positive `H_N`, a frozen eigen-error tolerance and a hard
mode cap. This is at most a conditional physical-primal metric.

The needed uniform trace/norm equivalence is **not proved**. The native
beam yaw in the current fixture is cellwise retained and can jump at
half-cell knots. A jump has divergent `H^(1/2)` double-integral seminorm
`∫∫|v(s)-v(t)|²/|s-t|² ds dt`; a standard continuous H¹ trace theorem
for the shell does not control that full native gap. The four offset
sample lines on the shell also need nondegenerate pose-fit and uniform
trace bounds. Thus an apparent stabilized `H^(-1/2)` eigenfloor would
remain exploratory until the actual beam/shell trace topology and jump
control have a reviewed proof.

For the exact retained system, eliminating native coordinates produces
the signed multiplier block `−S_r`, `S_r=C_r K_rr^(-1) C_rᵀ`.
The multiplier Schur operator is `C_l K_e^(-1) C_lᵀ+S_r`, which can
cancel or be indefinite. A finite-mesh *algebraic* positive primal
metric can be formed in work-scaled coordinates `z=D_q^(-1)q`:

```text
d_r = z_r + Khat_rr^(-1) Khat_rp z_p
||q||² = [z_pᵀ Khat_e z_p + d_rᵀ |Khat_rr| d_r]/W0
```

Here `|Khat_rr|` is its spectral absolute value; this presumes symmetric,
nonsingular retained `Khat_rr` and SPD `Khat_e`. Test the full signed KKT
generalized spectrum and independent reduced congruence/inertia with
residual and inertia bracketing. This is not a mesh-independent physical
norm without uniform equivalence to a fixed continuum/graph norm.
Check a fully transformed m↔mm case before interpreting any dimensionless
spectra. No K2 threshold or production multiplier space is frozen.

The subsequent K2L native-image experiment only diagnoses whether
constraint rows impose additional shell compatibility combinations after
quotienting the beam image. It is not a substitute for either stability
proof, independent physical reference, or the six-channel F03 work.
