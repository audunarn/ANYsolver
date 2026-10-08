# F03 graph-scaled signed retained KKT: bounded v1 registration

22 September 2026. **Exploratory G0B necessity check, not F03 line-law acceptance.** Before execution freeze this registration, probe and supervisor at one clean integration commit and obtain independent mechanics/code review. The supervisor verifies the exact previous banded-v3 raw hashes and all inherited source bytes, source-root ANYsolver import, and the ten unique native Q4/S3-V2D meshes `(Nb,Ns)=(4,4),(8,8),(16,16),(8,1),(8,64)` for each topology. Evaluate both existing K4 and local-dual/P0 constraint rows, no row or element-law substitutions. Exclusive root: `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-signed-graph-v1`. One serial one-thread supervisor, 8 GiB sampled child RSS, 900 s/case, 7,200 s total, 1,200 dense KKT rows and 2,500 trace rows. Preserve every child failure and do not rerun a consumed identity.

The known v1 L2 multiplier normalization showed refinement decay. The mathematical shell-port bound and v3 banded check support a reachable-image broken-trace dual in the **straight planar** fixture, but neither tested the signed constrained operator. This diagnostic uses the actual supported native stiffness `A=D K D/W0`, actual rows `Cbar=C D/(U L0)`, and the fixed work/gap scales from the signed-v1 probe. No constitutive or attachment mechanics change is made. Partition supported physical `p` and native retained `r`; calculate `P=A_rr^{-1} A_rp`, `Ke=A_pp−A_pr P`, and `T=[[I,0],[P,I]]`. Verify positive `Ke`, invertible signed `A_rr`, and symmetry. The primal norm is the fixed diagnostic choice

```text
H0=T^T diag(Ke, |A_rr|) T,
G=(E D/U)^T R (E D/U),
H=H0+G.
```

`R` is the registered overlay L2/slope norm plus actual native yaw-jump terms. `G` may have a kernel; **do not invert it alone**. Its coefficient in `H` is exactly one under the frozen scales and must not be tuned after outcomes are seen. `|A_rr|` occurs only in the positive primal norm. The assembled KKT and Schur use the *signed* `A_rr`. Independently compare `G` with the predecessor graph assembly and check skew ≤`1e−10` and parity ≤`1e−10` before symmetrization. The supported physical shell ports, rooted native P1 translations and retained P0 yaw give `S=E Q/U`; for each native row functional `Fbar=F/L0`, set the multiplier Gram `N=(Fbar S)(S^T R S)^{-1}(Fbar S)^T`. Check the physical root identity, exact native/trace row parity, SPD `N`, and the numerical reachable-image ordering `N≼B=Cbar G^+ Cbar^T`. Repeat the graph pseudoinverse check at relative cutoffs `1e−12`, `1e−10` and `1e−8`; require discarded constraint action ≤`1e−8` and relative dual-matrix change ≤`1e−8` from the first cutoff. Record min/max generalized ratios and ranks. This equivalence concerns the reachable trace image, not ambient DG or a certified physical norm.

Report the eigenstructure and norms of the graph-scaled **signed** KKT

```text
[[H^(-1/2) A H^(-1/2), H^(-1/2) Cbar^T N^(-1/2)],
 [N^(-1/2) Cbar H^(-1/2), 0]]
```

including smallest and largest singular and signed eigenvalues, negative/near-zero inertia, positive constraint β and ceiling, and minimum absolute eigenvalue/negative-mode count of the signed multiplier Schur. Define near-zero inertia at `|λ|≤1e−10 max|λ|` in each matrix; also report minimum and maximum signed Schur eigenvalues. Compare its Schur formed from the complete `A` with the exact `p/r` expression `Cl Ke^{-1} Cl^T + Cr A_rr^{-1} Cr^T`, where `Cl=Cp−Cr P`. Report retained negative modes, `Ke`/`H` spectral floors, dimension/rank, operator bound, dual ratios, equation residual and resource use. Verify signed stiffness skew ≤`1e−10`, KKT/Schur skew ≤`1e−9`, scaled constraint parity ≤`1e−10`, full/condensed Schur parity ≤`1e−8`, graph discarded action ≤`1e−8`, dual ordering tolerance `1e−8`, actual equation residual ≤`1e−8`, positive norm spectra relative floors `1e−12`, and `||H^{-1/2} A H^{-1/2}||₂≤1+1e−8`. Record any failure and all numerical floors even when no floor threshold is prescribed. The supervisor verifies exactly both spaces, status, finite response data, dimensions, empty successful stderr and the registered root/cache before counting a child complete.

Adjudicate the complete ten-case inventory and signed spectra independently. A finite pass means the chosen graph-scaled **diagnostic** was internally consistent; it does not certify a mesh-uniform inf-sup constant or physical response. A declining floor is an adverse trend for this chosen normalization, not an asymptotic instability theorem. No accepted physical load reference, six-channel eccentric moment/shear transfer, production sparse KKT, or G0B/G1 acceptance follows. Preserve signed-v1, banded-v1/v2/v3 and all other historical evidence unchanged.
