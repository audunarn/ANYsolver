# F03 double-segmented axial line-resolution extension V3

24 September 2026. Level-A development diagnostic only. No formal F03
execution authority was consumed. The mathematical operator, physical
geometry, beam and shell spaces, four-sample pose, load and support are
unchanged from V2. This source revision widens only the exploratory P1
line-interval admission from 512 to 1024.

The fixed case `(x degree 24, y degree 12, beam 512, P1 intervals 1024)`
completed with exit 0, sampled child RSS `1,635,545,088 B` (1.523 GiB)
and 58.90 s elapsed under the one-thread, 8 GiB sampled-RSS and 300 s
wall limits. The exact manifest, commands, source hashes, stdout/stderr,
parsed result and status are in
`B3_GE_E4_PL_F03_DOUBLE_SEGMENTED_XP24_YP12_B512_M1024_V3/`.
The manifest binds predecessor commit `181e0cdf` and exact source bytes;
changed reference/runner SHA-256 values are
`bbce242d673aa8efaff52b6a377af508da5372d46e84f9301d1ab020c0fdfc2b`
and `c577e8e8079536fca12567f36433f046bc09c2188dca512e8edc9acf0d88a9ab`.
Sampled RSS is not a hard memory peak or process-tree total.

| P1 intervals | Tip axial (m) | Beam energy (J) | Root axial (N) | Gap L2 (m) |
|---:|---:|---:|---:|---:|
| 256 | `-3.335459569e-7` | `0.000472403463` | `-8176.54` | `7.08400e-11` |
| 512 | `-3.337246847e-7` | `0.000468153489` | `-8210.01` | `1.46347e-11` |
| 1024 | `-3.337760691e-7` | `0.000466488339` | `-8219.46` | `3.96999e-12` |

The adjacent 512→1024 changes are **-0.356%** in beam energy,
**+0.115%** in root-force magnitude and **+0.0154%** in tip magnitude.
Shell energy changes +0.00986%. The algebraic residual ratio is
`1.61e-12`, work discrepancy `1.39e-12` relative, and assembled weak
row norm `1.25e-23`. These demonstrate finite-system consistency;
they do not prove mesh-independent physics or a stable multiplier family.
The lower physical gap and settling tip cannot replace force, work,
energy, signed-stability and refinement checks.

This supports retaining the double-segmented classical model as a useful
physical comparator candidate. It does not select an accepted target or a
native shell pose/multiplier space. Longitudinal, transverse and beam
resolution, matched Q4/CST convergence, full eccentric torque/shear, signed
KKT stability and required mesh ratios remain open. **F03/G0B remain open;
G1 is barred.**
