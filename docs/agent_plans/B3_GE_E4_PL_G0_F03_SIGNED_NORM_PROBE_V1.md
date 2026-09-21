# F03 finite-mesh signed retained norm probe v1

21 September 2026. **Exploratory operator-adapted stability diagnostic,
not a G0B inf-sup proof.** Freeze six joint refinement cases
`Nb=Ns=4,8,16` and the reciprocal adverse reaches `Nb=8,Ns=1,64` for
each Q4 and S3-V2D, twelve meshes in total. Evaluate the existing K4
channel-adapted rows and the distinctly assembled local dual/P0 rows on
each mesh. All source-backed tests use one BLAS thread, the integration
worktree's ANYsolver import and an explicit ignored Numba cache. Keep raw
per-case rows including failures in a new exclusive directory. The bounded
dense diagnostic rejects assembled KKT dimensions above 1,200; it is not
a production assembly or performance benchmark.

With supported physical coordinates `p`, native retained coordinates `r`,
and exact symmetric tangent blocks, assume invertible local `Krr` and SPD
supported physical Schur block `Ke=Kpp−Kpr Krr⁻¹ Krp`. The congruence
`r̃=r+Krr⁻¹Krp p` gives `K=diag(Ke,Krr)` in `(p,r̃)` coordinates. Define
the finite-mesh primal norm with `diag(Ke,|Krr|)`, where absolute value
uses the signed eigenvalues **without** dropping negative retained modes.
Normalize coordinates by frozen displacement/retained scales and work
`W0=F0 L0 U*`, where `F0=1e6 N/m` is the force-density scale,
`L0=1 m` the attachment length, and `U*=F0 L0/(E·0.07 m)`.
The distinct yaw conversion length is `ell=.46 m`. Use exact multiplier
L2 Gram mass `M/L0` in scaled metre-gap channels (numerically `M` here).
The transformed constraint rows are
`Cl=Cp−Cr Krr⁻¹Krp` and `Cr`, so neither the retained trace nor its
induced multiplier effect disappears.

The whitened constraint singular floor measures the discrete inf-sup in
this norm. The signed Schur is `Cl Ke⁻¹ Clᵀ+Cr Krr⁻¹ Crᵀ`, which can
cancel even when the positive inf-sup is large. Also record the smallest
singular value of the fully norm-scaled signed KKT. Check `Ke`, `Krr`
inertia, exact local-block structure, symmetry and numerical finiteness.
Do not infer physical stability from a raw mixed-unit KKT spectrum.

This `H` is built from the operator itself; a healthy finite-mesh floor
does **not** prove uniform mechanical inf-sup. Qualification still requires
independent mesh-local energy/trace norms, a broken yaw-jump measure and
its dual, norm-equivalence and trace-continuity bounds over registered
refinements and ratios, physical response, and the full eccentric
six-channel formulation. Failure or decay is diagnostic; success is only
a necessary bounded screen. The prior K4 and local-dual results remain
unaltered whatever this probe finds.
