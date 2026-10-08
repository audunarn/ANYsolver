# F03 local dual/P0 planar screen: distinct span, adverse response

21 September 2026. **Four/four exploratory meshes and eight/eight physical
loads solved; no G0B/F03 acceptance or line-space selection.** The frozen
source is integration commit `c6e6633`. Complete JSONL and the manifest are
at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-local-dual-v1/`.
SHA-256: `manifest.json`
`f8644041e1438f622d8fa6a099b1bfff64c653eb9ec7305dbf1043df15fdffce`,
`results.jsonl`
`5005eed683788ec7892e79f51df808acf0ac7138d25d05de3ef5b3f9b18b6542`.
The manifest binds all six probe/helper hashes, Python 3.14.2, NumPy 2.4.6,
SciPy 1.17.1, Numba 0.65.1, an exclusive Numba cache path, and the
ANYsolver import from this integration worktree's `src` tree. The commit
identifies that imported product source; the manifest does not contain a
separate full-source-tree hash or an installed-wheel identity.

The candidate replaces K4's continuous P1 translation hats with locally
biorthogonal, discontinuous tests and retains P0 cell yaw. All four cases
have 24 constraint rows, native image rank 24, full row rank 24, and no
shell-only restrictions. K4 also has row rank 24. The combined row rank is
**26/40** for Q4 at shell counts 1/64 and **30/40** for S3-V2D. Thus the
assembled rows are not an invertible reweighting of K4 at the stated
`1e-10` relative singular-value cutoff; the last included singular value
is at least `1.77e6` times that cutoff. Exact beam nodal-moment pairing
differs from its diagonal analytical target by at most `2.78e-17`.
Newly assembled C/M and the unchanged physical trace-Gram quadrature
discrepancies are at most `1.37e-15`.

| Shell | `Ns` | Smooth shell energy, J | Smooth sampled gap / U* | Sine shell energy, J | Sine sampled gap / U* |
|---|---:|---:|---:|---:|---:|
| Q4 | 1 | 14.1283 | 0.36747 | 0.00207329 | 0.0044515 |
| Q4 | 64 | 21.4777 | 0.53342 | 1.25603 | 0.0632349 |
| S3-V2D | 1 | 14.1549 | 0.36642 | 0.0373488 | 0.0026272 |
| S3-V2D | 64 | 19.6232 | 0.49092 | 1.16261 | 0.0593756 |

The fixed displacement scale is `U*=1e6/(210e9*0.07)=6.80272e-5 m`.
The coarse Q4 sine shell energy is over 2,000 times K4's previously
observed `9.5197e-7 J`, but remains very different from the fine-shell
response. The smooth gap grows to about half U* as the shell alone is
refined, and the sine gap also grows. Nine beam-endpoint samples are only
a lower bound on the continuous maximum. They cannot certify a bonded
line's pointwise compatibility or traction-jump behavior.

All eight loads have small numerical residuals: maximum scaled free
equilibrium and normalized weak residual below `2.0e-13` and `2.7e-15`,
respectively; normalized support force/moment imbalance below `7.4e-13`
and `4.2e-13`; full/retained-condensed parity below `1.6e-11`. These
demonstrate accurate solution of this bounded signed KKT, not a stable
continuum connection. Maximum local row incidence reaches 109 on refined
Q4 because the physical four-sample footprint intersects more shell nodes;
production sparsity and memory are not established.

Independent pre-execution review found no mechanical assembly blocker and
required the failure-status correction made before commit. Independent
post-run review verified the source identities, complete cases, distinct
rank, pairing, quadrature, response and limitations without rerunning.

**Decision:** Do not promote this span to the registered F03 candidate or
G1. It changes K4's constraint kernel but does not resolve adverse
fixed-beam mesh sensitivity. The independently converged physical target,
signed retained inf-sup norm, continuous gap/traction bounds, reciprocal
and joint refinements, and six-channel eccentric mechanics remain open.
