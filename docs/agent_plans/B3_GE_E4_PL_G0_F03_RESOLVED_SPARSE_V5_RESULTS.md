# F03 independent comparator v5: larger meshes still unresolved

21 September 2026. **Sixteen/sixteen exploratory cases completed; the
registered comparator-resolution criteria fail; F03/G0B remain open.**
Frozen source/registration commit `9c75a2b`; exclusive raw root
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-resolved-sparse-v5/`.
SHA-256: `manifest.json`
`73cfbaa752cc52cb0b36b7d6aafb43e8138858e152f7cd879ac38a51e52d2f6c`,
`preflight.json`
`7fe27f9e1624b832f2b23e192133e75901807de72d9428c97ae48df1427c1ddf`,
and `records.jsonl`
`e80825b19e5622aae33084268bdce1b6e188f79f23e0adf30b224d258ba31064`.
The four current script hashes matched the manifest; the prior v4 manifest,
records and reference-source hashes matched their frozen identities.
The run used serial one-thread child solves with a 24 GiB sampled child
RSS limit and 1,800 s per-case/7,200 s total limits. Maximum sampled
child RSS was 491,159,552 B; summed case wall time was 78.20 s. This
sampled RSS is not a hard peak or whole-process-tree limit.

The eight small sparse/dense preflight cases had identical numerical
matrix `nnz` and multiplier counts; the largest station-pose and gap-extrema
difference was `6.78e-21` m/rad, and the largest normalized work/energy/
moment difference was `2.21e-16`. More importantly, all four new n64
joint cases directly match the immutable v4 records: tip differences zero,
maximum station difference `6.78e-21`, largest normalized selected scalar
difference `1.42e-16`, and maximum gap-estimate difference `2.97e-21`.
Therefore the 64→96→128 trend joins the same *discrete classical
finite-station comparator*, with sparse trace storage rather than changed
mechanics.

| Shell/load | Tip at joint 64 → 96 → 128 (m) | Tip change 96→128 | Nine-station physical change | Shell energy change | Beam energy change | Physical-scaled maximum gap / tip at 128 |
|---|---|---:|---:|---:|---:|---:|
| Q4 smooth | 3.11584e-5 → 3.20765e-5 → 3.16326e-5 | 1.403% | 2.217% | 1.791% | 11.258% | 3.075% |
| Q4 sine | -9.97867e-6 → -9.98409e-6 → -9.98375e-6 | .0035% | .692% | .485% | 8.466% | .661% |
| S3-V2D smooth | 3.09895e-5 → 3.18225e-5 → 3.17413e-5 | .256% | .390% | .334% | 1.859% | 2.246% |
| S3-V2D sine | -9.97286e-6 → -9.98531e-6 → -9.98074e-6 | .046% | .179% | .204% | 1.270% | .540% |

All percentages use the preregistered denominators. Station translation
and yaw use a .46 m rotational conversion; the maximum discrete-field
gap uses the numerical polynomial-extrema estimate. This is not a
certified bound on the continuous loaded beam field. The Q4 smooth tip
crosses from increasing to decreasing at 128, and the smooth gap ratio
rises again from 96 to 128 for both shell types. A visually close sine
tip does not establish convergence of the smooth response or beam energy.

The smooth crossed controls isolate unresolved width dependence: at
`(Ns,Ny,Nb)=(128,64,128)` relative to `(128,128,128)`, tip changes are
1.032% Q4 and 1.622% S3, both above the 1% criterion. Holding the beam
at 64 instead changes tips .262% Q4 and .429% S3. All cases satisfied
finite algebraic equilibrium and work checks; the largest reported
equilibrium residual was below `8e-13` and work discrepancy below
`1.1e-12`; the largest station constraint was `8.81e-20`.
Maximum absolute force and moment imbalance were `8.25e-7 N` and
`5.89e-7 Nm`, respectively, on the declared million-newton load scale.
Tiny assembled station residuals therefore do not cure
off-station gaps or mesh dependence.

No extrapolated target is adopted. This runner compares a conventional
Timoshenko beam and classical plane-stress Q4/CST under finite-station
ties; it differs from native retained B3, E4-PL and the required exact
weak line law. Its homogeneous interior beam trace omits the distributed
load's particular field. Further refinement alone cannot resolve those
idealization differences. A physical F03 target needs a documented
matched model and converged independent response, continuous-gap/work
audit and the local signed trace stability proof. G1 integration remains
barred by the G0B foundation.
