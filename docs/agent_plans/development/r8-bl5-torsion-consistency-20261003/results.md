# Native affine director consistency decision — 3 October 2026

**Withhold the unmodified growing affine director rule on a demonstrated
consistency defect.** Keep the native retained physical trace and continuous
connection law experimental. Neither span8 nor a replacement space is accepted.

Independent equation review derived the virgin uncoupled torsion cell potential:

\[
\Pi_c=M_L(\psi-\theta_L)+M_R(\theta_R-\psi)
-h(M_L^2+M_LM_R+M_R^2)/(6GJ).
\]

The native half-cell rotation is independent and constant. A compatible
continuum twist theta=kappa*x is represented naturally by midpoint rotations.
Its mean director gap is zero, but its affine support moment is
`-kappa*H^2/(6*m^2)`. Enforcing both moments requires excess beam energy:

\[
E/E_{continuum}=1+1/(m^2-1).
\]

## Actual-operator discriminator

[Saved-operator patch](../../../../scripts/r8_bl5_saved_torsion_patch_dev.py)
uses the existing fine32x8 virgin K/C matrices at eight and sixteen supports.
No owner reconstruction, external solve, loaded solve or refinement was run.
Prescribed shell translations/directors and beam nodal rotations represent
compatible torsion including the 0.0675 m offset; root supports remain satisfied.
Only retained cell Rx and torsional moment variables are solved, using the
actual general indefinite block. Energy is the beam's stationary mixed torsion
potential, not a norm assigned to the full mixed matrix. An independently
eliminated scalar law checks the energy. All five channels' complete constraints
are checked after enforcing both director moments.

| Half-cells per support | Actual energy / continuum | Predicted | Excess |
|---|---:|---:|---:|
| 8 | 1.015873015873016 | 64/63 | 1.5873% |
| 4 | 1.066666666666664 | 16/15 | 6.6667% |

Natural midpoint rotations/uniform torsion moments and affine-gap identity pass.
Restricted mixed equilibrium <=1.003e-13, complete constraint gap <=1.483e-21.
Both cases have the same raw affine gap -4.0690104e-9 because half-cell size
is fixed. Persistence of relative energy error with fixed m as raw gaps shrink
follows analytically from the verified formula; no refinement sequence was run.
This explains why small residuals cannot select the affine rule; it does not
allocate the complete loaded comparison error or prove continuous-law failure,
full-system locking, uniform stability or engineering accuracy.

Run terminal exit0, 0.537 s, sampled peak 62812160 bytes, effective native pools
one. [Raw result](raw/result.json) binds both previously preserved input/operator
files by SHA256. Seven-file archive manifest SHA256
`3158b31d567f508af602fab853df8220a46d693d0bdf0c3c1ceefa9ef33bdfd8`.
No protected history or formal F03 authority was consumed.

Next decision: independently scrutinize one complete five-channel discrete
correction that uses half-cell averages of the affine multiplier density.
It must retain the native gap/work map, have its own explicit identity and pass
consistency, physical work, derivatives and growing-space checks. No automatic
loaded campaign, selective channel tuning or production selection follows.
