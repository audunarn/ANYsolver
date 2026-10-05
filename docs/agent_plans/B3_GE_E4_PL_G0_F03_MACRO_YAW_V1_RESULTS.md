# F03 two-cell yaw moment probe: distinct span, no physical cure

21 September 2026. **Ten/ten bounded exploratory cases completed; the
two-cell yaw moment candidate is not selected and F03/G0B remain open.**
The frozen source and preregistered contract are at `b1d3f1e6186e3fccaafce8d4d3ac2c5ab0abb4e6`.
The exclusive raw root is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-macro-yaw-v1/`.
SHA-256: `manifest.json`
`92d1d95d850714b2d091b2cf52f9be70a8e27bcc5d09bb905b488821d9604e00`,
`results.jsonl`
`856c39273fce1cda2b3e5a2797919a9884802026f580a9bce06c9dc4ee6e54d6`.
The one-time runner exited zero. All ten Q4/S3-V2D cases and both smooth
and signed-sine load solves for both spaces completed. These are local
planar small-model calculations, not an installed production workflow.
Independent post-run read-only review verified the frozen source and all
eight helper hashes against the manifest, both raw artifact hashes,
all ten distinct successful rows, and all forty load solves.

The new two-cell yaw constant/linear tests preserve K4's translation
rows and the number of yaw rows. The analytical cell pairing and exact
test mass pass their absolute checks, and the macro candidate has full
assembled and native-image row rank in all cases. Stacking the new and
K4 constraints adds 2–8 independent rows across the inventory. It is
therefore a genuinely different assembled physical constraint span,
not simply invertible reweighting of K4. The maximum two-versus-four
Gauss relative errors are `1.09e-15` for yaw assembly and `1.26e-15`
for its mass; the independent direct multiplier–gap versus assembled
yaw work discrepancy is at most `2.30e-15`. This checks the local
assembly and quadrature, not convergence of the line law.
The analytical pairing and mass maximum absolute errors were
`5.55e-17` and `1.11e-16`.

| Shell | Joint native/shell refinement | New signed KKT floor | New smooth nine-station maximum gap / displacement scale |
|---|---|---:|---:|
| Q4 | 4/4 → 8/8 → 16/16 | .26402 → .11328 → .03467 | .52942 → .47255 → .36190 |
| S3-V2D | 4/4 → 8/8 → 16/16 | .26329 → .11332 → .03465 | .48836 → .43976 → .34110 |

The K4 signed floors on the same Q4 joint series are `.26536`, `.11349`,
`.03467`; its smooth gaps are `.52503`, `.47099`, `.36165`.
The new candidate does **not** arrest the beam-refinement decline in the
signed normalized KKT floor. Its positive constraint floors and signed
Schur minima are essentially unchanged to the reported precision.
This finite signed floor is norm dependent and cannot alone establish
loss of physical stability.

At fixed native beam eight cells and fine shell 64 cells, smooth gap
remains `.47588` of displacement scale for Q4 (K4 `.47427`) and `.44187`
for S3-V2D (K4 `.44056`). The nine-station maximum is a sampled lower
bound, not a continuous gap bound. The signed-sine gap falls slightly:
Q4 `.06333` K4 to `.06267` macro, S3-V2D `.05991` to `.05938`; this
limited difference cannot offset the persistent smooth gap. On those
fine-shell cases the active shell energy changes by about +0.13% under
smooth load and +0.4% under sine. Across all 40 load/space solves,
maximum normalized force/moment balance is `7.13e-13`/`4.02e-13`,
scaled free equilibrium `2.73e-13`, weak residual `4.72e-14`, and
full-versus-condensed signed solution difference `3.06e-11`. Physical
applied/support wrenches, free residuals, nine station traces, and
energies are retained in each raw record.

The algebraic falsification succeeded: the span really changed while
keeping native rank and accurate work. The candidate did not show a
convincing physical or signed-norm improvement on the registered
adverse cases. Do not select or integrate it as the production exact
line multiplier. An independently converged compatible physical target,
a mesh-local dual norm and stability bound, the full mesh-ratio inventory,
eccentric six-channel mechanics, torque/drilling/shear and external
references remain prerequisites for G0B. The independent post-run review
agreed that this is a consistently assembled, distinct span without a
useful physical or signed-stability improvement.
