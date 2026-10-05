# F03 independent variational line pilot: response remains law dependent

21 September 2026. **All 32 registered exploratory cases completed;
the physical-response screen is adverse. F03/G0B remain open.** Source
and registration were frozen at
`0003a91639c8622f4fc1790277a0dcded961c733`. The exclusive raw root is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-variational-line-v1/`.
SHA-256: `manifest.json`
`3895a90ec6e94dc92b9c3738a8fc880fca20f56c51dd182b58664446660e0483`;
`preflight.json`
`8a6dc936d517a2fb060208d086d51a36c71d3efb93fc6989e2075491e8904d78`;
`records.jsonl`
`e4925757567209706512f0aeec5ce234871eafdd1b669822b4b049bdf6511204`.
The five source hashes and isolated-worktree import paths matched the
manifest. All 32 records are distinct, ordered, exit-zero, with saved
stdout matching each embedded response and empty stderr.

This independent *classical* plane-stress Q4/CST and conventional
Timoshenko trial includes the declared elastic section constants,
the same four-sample shell pose and signed loads, and a variational
line action on the same beam trial field as the load. Weak P0/P1 tests
are integrated over the reference overlay. Two station-tie controls
respectively include/exclude the line's root endpoint. They are
different finite models, not interchangeable physical references.
The exact-static homogeneous beam subcells still omit particular
responses to the applied distributed load and line traction at finite
resolution; refining the conforming subcells must resolve that error.

The independent four-versus-six-point coupling assembly differed by
at most `4.95e−16` relative. All registered numerical screens passed:
minimum normalized row-Gram rank ratio `.00403`; maximum free-equilibrium
relative error `5.19e−14`, x/y support imbalance `1.39e−14/9.45e−14`,
moment imbalance `1.70e−14`, doubled-energy work discrepancy `1.46e−14`,
line-action work cancellation `8.88e−14 J`, and normalized assembled
weak/station residual `3.98e−16`. Maximum signed-load resultant errors
were `2.18e−11 N` and `5.82e−11 Nm`. Maximum sampled child RSS was
137,375,744 B; longest case 2.033 s, summed case time 59.918 s.
These balances establish a consistently assembled finite model, not
physical trace conformity or multiplier stability.

At `(Ns,Ny,Nm,beam subcells)=(8,4,8,4)`, beam tip translation in µm:

| Shell/load | Weak P0 | Weak P1 | Stations including root | Stations excluding root |
|---|---:|---:|---:|---:|
| Q4 smooth | +43.509 | +38.373 | +25.257 | +47.753 |
| S3 smooth | +41.455 | +36.550 | +23.859 | +45.466 |
| Q4 sine | −8.089 | −9.184 | −9.347 | −7.850 |
| S3 sine | −7.618 | −8.705 | −8.900 | −7.437 |

For all four shell/load combinations at this mesh, the P0/P1 tip spread
is `11.8–12.5%` relative to the larger magnitude, exceeding the
preregistered `5%` warning. Including versus excluding the root station
changes smooth tip by `22.496 µm` Q4 and `21.608 µm` S3. It would be
incorrect to ascribe a station/weak difference solely to quadrature.

At fixed shell/mortar resolution, beam subcells `1→4` change smooth
weak-law tips by `23–30%` and signed-load magnitudes by `6.4–16.7%`.
With four beam subcells, shell `(Ns,Ny)=8/4→16/8` changes smooth tips
by `3.3–7.0%` and sine magnitudes by `3.1–7.8%`. The line test space
was held at eight cells in this latter control, so it cannot establish
joint mortar convergence.

The sampled physically scaled pointwise gap exceeds the registered
`.05 U` warning in **26/32** cases, including every P0 case and every
smooth P1 case; P0 spans `.071–.733 U`. Sine P1 gaps `.026–.038 U` are
smaller, but its tip still changes materially with test space, beam
subcells, and shell mesh. These maxima are sampled **lower bounds**, not
certified continuous maxima. Very small assembled weak moments and
excellent global balance do not make a bonded physical line.

Independent pre-execution review checked source, quadrature, signs,
root policy, normalizations and the supervisor before source freeze.
Independent post-run review matched hashes, all raw case outputs,
resources, numerical criteria and response trends; it found no raw
correctness issue. The separate local-norm experiment likewise found
an ambient/physical-image mismatch. Together they preclude selecting
P0, P1, a finite station tie, K4 or the earlier local-dual native space
as an accepted physical line law from current evidence.

**Next:** derive a physical interface test and reachable-trace norm with
stable lifting, and obtain a resolved reference through independent
beam, shell length/width and mortar refinements. Freeze the root/bond
endpoint meaning, continuous-gap assessment and section/shear mapping.
Only then compare against the native retained B3/E4-PL six-channel
eccentric, torque and transverse-shear response. This classical planar
pilot is not a G0B pass or permission to start G1 production coupling.
